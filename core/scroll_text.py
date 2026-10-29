"""Server-owned continuous text track, bounded PNG tiles and shared frame compositor."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import threading
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw

RECT = dict(x=119, y=1325, width=842, height=256)
FRAME_BOTTOM = RECT['y'] + RECT['height']
PAD, TILE_HEIGHT = 18, 512
STYLE_VERSION = 'elegant-scroll-adjustable-2'


def build_track(text, credit, settings, workspace):
    from core.renderer import get_font, wrap_text
    draw = ImageDraw.Draw(Image.new('L', (1, 1)))
    sizes = dict(quote=settings['scroll_quote_size'],credit=round(settings['scroll_quote_size']*.625))
    fonts = {'quote': get_font('seguisb.ttf', sizes['quote'], workspace),
             'credit': get_font('segoeui.ttf', sizes['credit'], workspace)}
    outline = {key:settings['scroll_'+key] for key in
               ('outline_enabled','outline_color','outline_width','outline_blur','outline_opacity')}
    halo = outline['outline_width'] + math.ceil(outline['outline_blur']*3) + 2 if outline['outline_enabled'] and outline['outline_opacity']>0 else 0
    metrics = {}
    for kind,font in fonts.items():
        # Shared baseline bounds cover stacked Vietnamese accents and descending glyphs.
        box = font.getbbox('ẮẤỄỠỸẬỴgjpq',anchor='ls')
        ink_height = box[3]-box[1]
        pitch = math.ceil(max(sizes[kind]*1.125,ink_height+sizes[kind]*.12))
        metrics[kind] = dict(height=pitch,baseline=-box[1]+(pitch-ink_height)//2)
    top_pad = max(12,settings['scroll_fade_top'],halo)
    bottom_pad = max(12,settings['scroll_fade_bottom'],halo)
    rect = RECT.copy()
    rect['height'] = settings['scroll_lines']*metrics['quote']['height']+top_pad+bottom_pad
    rect['y'] = FRAME_BOTTOM-rect['height']
    if rect['y'] < 180:
        raise ValueError('Khung chữ quá cao. Hãy giảm cỡ chữ hoặc số dòng.')
    max_width = rect['width']-2*max(16,halo+4)
    lines, y = [], top_pad
    def append_line(text,kind):
        nonlocal y
        metric = metrics[kind]
        lines.append(dict(text=text,kind=kind,y=y,height=metric['height'],baseline=y+metric['baseline']))
        y += metric['height']
    # Preserve explicit Enter boundaries and empty paragraphs without turning them into scenes.
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            y += math.ceil(metrics['quote']['height']/2)
            continue
        for line in wrap_text(paragraph, fonts['quote'], max_width, draw):
            append_line(line,'quote')
    if credit:
        y += max(6,round(sizes['quote']*.2))
        for paragraph in credit.splitlines():
            for line in wrap_text(paragraph, fonts['credit'], max_width, draw):
                append_line(line,'credit')
    content_height = y + bottom_pad
    distance = max(0, content_height - rect['height'])
    words = len((text + ' ' + credit).split())
    seconds = max(float(settings['duration']), words / (2.5 * settings['scroll_speed']) + (4 if distance else .8), 6 if distance else 4)
    duration = math.ceil(seconds * 30) / 30
    track = dict(style_version=STYLE_VERSION, rect=rect, lines=lines,font_sizes=sizes,
                 outline=outline,halo=halo,quote_line_height=metrics['quote']['height'],visible_lines=settings['scroll_lines'],
                 content_height=content_height, distance=distance,
                 scroll_start=2., scroll_end=duration - 2., duration=duration,
                 fade_seconds=.2,edge_fade_top=settings['scroll_fade_top'],edge_fade_bottom=settings['scroll_fade_bottom'],tile_height=TILE_HEIGHT)
    # Static short content sits on the same lower edge as the full four-line window.
    track['initial_offset'] = min(0, content_height - rect['height'])
    asset_data = {k:track[k] for k in ('style_version','rect','lines','content_height','tile_height',
                                     'font_sizes','outline','halo','edge_fade_top','edge_fade_bottom')}
    track['asset_key'] = hashlib.sha256(json.dumps(asset_data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:32]
    track['tiles'] = [dict(index=i, y=y, height=min(TILE_HEIGHT, content_height-y))
                      for i,y in enumerate(range(0, content_height, TILE_HEIGHT))]
    return track


def scroll_offset(track, seconds):
    if not track['distance']:
        return track['initial_offset']
    progress = max(0., min(1., (seconds-track['scroll_start']) / (track['scroll_end']-track['scroll_start'])))
    # Integer pixels give identical crop positions in Pillow, canvas and encoded video.
    return track['initial_offset'] + math.floor(track['distance'] * progress + .5)


def frame_alpha(track, seconds):
    return max(0., min(1., seconds/track['fade_seconds'], (track['duration']-seconds)/track['fade_seconds']))


def tile_path(track, index, workspace):
    tile = track['tiles'][index]
    folder = Path(workspace)/'.cache'/'scroll_text'/track['asset_key']
    folder.mkdir(parents=True, exist_ok=True)
    target = folder/f'{index}.png'
    if target.is_file():
        return target
    from core.renderer import get_font, paint_outlined_text
    bleed = max(8,track['halo']+2)
    image = Image.new('RGBA', (track['rect']['width'], tile['height']+2*bleed))
    for kind, name in [('quote','seguisb.ttf'), ('credit','segoeui.ttf')]:
        font = get_font(name,track['font_sizes'][kind],workspace)
        ratio = track['font_sizes'][kind]/track['font_sizes']['quote']
        style = {**track['outline'],'outline_width':round(track['outline']['outline_width']*ratio),
                 'outline_blur':track['outline']['outline_blur']*ratio}
        entries = []
        pen = ImageDraw.Draw(image)
        for line in track['lines']:
            if line['kind'] != kind or line['y']+line['height']+bleed < tile['y'] or line['y']-bleed >= tile['y']+tile['height']:
                continue
            # Shared baseline, including Vietnamese marks; never align individual ink tops.
            x = (image.width-pen.textlength(line['text'], font=font))/2
            entries.append((x,line['baseline']-tile['y']+bleed,line['text']))
        image = paint_outlined_text(image, entries, font, (255,250,239,255), style, anchor='ls')
    image = image.crop((0,bleed,image.width,bleed+tile['height']))
    import uuid
    tmp = folder/(uuid.uuid4().hex+'.png')
    try:
        image.save(tmp)
        tmp.replace(target)
    finally:
        tmp.unlink(missing_ok=True)
    return target


@lru_cache(maxsize=32)
def _read_tile(path):
    with Image.open(path) as image:
        return image.convert('RGBA')


@lru_cache(maxsize=8)
def edge_mask(width=842,height=256,top=PAD,bottom=None):
    bottom = top if bottom is None else bottom
    mask = Image.new('L', (width, height))
    draw = ImageDraw.Draw(mask)
    for y in range(height):
        alpha = round(255*min(1.,y/top if top else 1.,(height-1-y)/bottom if bottom else 1.))
        draw.line((0,y,width-1,y), fill=alpha)
    return mask


def scroll_frame(track, seconds, workspace):
    rect = track['rect']
    image = Image.new('RGBA', (rect['width'], rect['height']))
    offset = scroll_offset(track, seconds)
    for tile in track['tiles']:
        y = tile['y']-offset
        if y >= image.height or y+tile['height'] <= 0:
            continue
        picture = _read_tile(str(tile_path(track,tile['index'],workspace)))
        image.alpha_composite(picture, (0,y))
    alpha = ImageChops.multiply(image.getchannel('A'),edge_mask(rect['width'],rect['height'],track['edge_fade_top'],track['edge_fade_bottom']))
    fade = frame_alpha(track,seconds)
    if fade < 1:
        alpha = alpha.point([round(i*fade) for i in range(256)])
    image.putalpha(alpha)
    return image


def write_scroll_video(track, path, workspace, scale=1., progress=None):
    """Stream only the small viewport to a lossless alpha movie; memory is bounded."""
    from core.media import tool_path
    width,height = (max(2,round(track['rect'][k]*scale)) for k in ('width','height'))
    with tempfile.TemporaryFile() as log:
        cmd = [tool_path('ffmpeg'),'-y','-v','error','-f','rawvideo','-pixel_format','rgba',
               '-video_size',f'{width}x{height}','-framerate','30','-i','pipe:0','-an',
               '-threads','2','-c:v','qtrle',str(path)]
        process = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        timer = threading.Timer(3600,process.kill);timer.daemon=True;timer.start()
        try:
            frames = round(track['duration']*30)
            for frame in range(frames):
                image = scroll_frame(track,frame/30,workspace)
                if scale != 1:
                    image = image.resize((width,height),Image.Resampling.LANCZOS)
                process.stdin.write(image.tobytes())
                if progress and frame%90==0:
                    progress(int(56+8*frame/frames),'Đang chuẩn bị chữ cuộn…')
            process.stdin.close()
            if process.wait(timeout=60):
                log.seek(0)
                raise RuntimeError('Không dựng được lớp chữ cuộn: '+log.read().decode('utf-8',errors='replace')[-2000:])
        except Exception:
            process.kill();process.wait()
            raise
        finally:
            timer.cancel()
