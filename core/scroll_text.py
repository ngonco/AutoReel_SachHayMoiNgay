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
PAD, TILE_HEIGHT = 18, 512
STYLE_VERSION = 'elegant-scroll-1'


def build_track(text, credit, settings, workspace):
    from core.renderer import get_font, wrap_text
    draw = ImageDraw.Draw(Image.new('L', (1, 1)))
    fonts = {'quote': get_font('seguisb.ttf', 48, workspace),
             'credit': get_font('segoeui.ttf', 30, workspace)}
    lines, y = [], PAD
    # Preserve explicit Enter boundaries and empty paragraphs without turning them into scenes.
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            y += 28
            continue
        for line in wrap_text(paragraph, fonts['quote'], RECT['width'] - 32, draw):
            lines.append(dict(text=line, kind='quote', y=y, height=54))
            y += 54
    if credit:
        y += 10
        for paragraph in credit.splitlines():
            for line in wrap_text(paragraph, fonts['credit'], RECT['width'] - 32, draw):
                lines.append(dict(text=line, kind='credit', y=y, height=40))
                y += 40
    content_height = y + PAD
    distance = max(0, content_height - RECT['height'])
    words = len((text + ' ' + credit).split())
    seconds = max(float(settings['duration']), words / (2.5 * settings['scroll_speed']) + (4 if distance else .8), 6 if distance else 4)
    duration = math.ceil(seconds * 30) / 30
    track = dict(style_version=STYLE_VERSION, rect=RECT.copy(), lines=lines,
                 content_height=content_height, distance=distance,
                 scroll_start=2., scroll_end=duration - 2., duration=duration,
                 fade_seconds=.2, edge_fade=PAD, tile_height=TILE_HEIGHT)
    # Static short content sits on the same lower edge as the full four-line window.
    track['initial_offset'] = min(0, content_height - RECT['height'])
    asset_data = {k: track[k] for k in ('style_version', 'rect', 'lines', 'content_height', 'tile_height', 'edge_fade')}
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
    bleed = 24
    image = Image.new('RGBA', (track['rect']['width'], tile['height']+2*bleed))
    style = dict(outline_enabled=True, outline_color='#101018', outline_width=2,
                 outline_blur=3, outline_opacity=.85)
    for kind, name, size in [('quote','seguisb.ttf',48), ('credit','segoeui.ttf',30)]:
        font = get_font(name, size, workspace)
        entries = []
        pen = ImageDraw.Draw(image)
        for line in track['lines']:
            if line['kind'] != kind or line['y']+line['height']+12 < tile['y']-bleed or line['y']-12 >= tile['y']+tile['height']+bleed:
                continue
            # Shared baseline, including Vietnamese marks; never align individual ink tops.
            x = (image.width-pen.textlength(line['text'], font=font))/2
            entries.append((x, line['y'] + (42 if kind=='quote' else 29) - tile['y']+bleed, line['text']))
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
def edge_mask(width=842, height=256, band=PAD):
    mask = Image.new('L', (width, height))
    draw = ImageDraw.Draw(mask)
    for y in range(height):
        alpha = round(255*min(1., y/band, (height-1-y)/band))
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
    alpha = ImageChops.multiply(image.getchannel('A'), edge_mask(rect['width'],rect['height'],track['edge_fade']))
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
