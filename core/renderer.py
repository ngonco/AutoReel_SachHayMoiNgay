"""One Pillow layout and one FFmpeg pipeline for stills, preview and Full HD."""
import math
import os
from pathlib import Path
import tempfile
import time
import unicodedata
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageColor
from core.media import resource_path, tool_path, run_media
from core.settings import normalize_settings
from core.paginator import boundary_penalty

W, H = 1080, 1920
PREVIEW_SIZE = (360, 640)
SAFE_BOTTOM = int(H * .86)


def get_font(font_name, size, workspace_dir=None):
    paths = ([Path(workspace_dir) / 'assets' / 'fonts' / font_name] if workspace_dir else [])
    paths += [resource_path('assets', 'fonts', font_name), Path('C:/Windows/Fonts') / font_name]
    for p in paths:
        if p.is_file():
            return ImageFont.truetype(str(p), int(size))
    raise ValueError('Thiếu font ' + font_name + '. Hãy khôi phục assets/fonts.')


def wrap_text(text, font, max_width, draw):
    # Break only over-wide tokens into character chunks before balancing real word lines.
    words = []
    for word in text.split():
        if draw.textlength(word, font=font) <= max_width:
            words.append(word)
            continue
        chunk = ''
        for char in word:
            if chunk and draw.textlength(chunk + char, font=font) > max_width:
                words.append(chunk)
                chunk = ''
            chunk += char
        if chunk:
            words.append(chunk)
    n = len(words)
    costs, previous = [0.] + [float('inf')] * n, {}
    for end in range(1, n + 1):
        for start in range(end - 1, -1, -1):
            line = ' '.join(words[start:end])
            width = draw.textlength(line, font=font)
            if width > max_width:
                break
            # Similar widths, few lines, no orphan tail, and intact Vietnamese phrases.
            cost = 35 + 90 * ((max_width - width) / max_width) ** 2
            cost += boundary_penalty(words, end) * 2
            if end == n and start:
                if end - start == 1:
                    cost += 450
                elif end - start == 2 and width < max_width * .40:
                    cost += 240
            if costs[start] + cost < costs[end]:
                costs[end], previous[end] = costs[start] + cost, start
    lines, cursor = [], n
    while cursor:
        start = previous[cursor]
        lines.append(' '.join(words[start:cursor]))
        cursor = start
    lines.reverse()
    return lines


def layout_overlay(quote_text, credit_text, theme_index=0, pos_mode='bottom', vertical_offset=0,
                   quote_size=68, credit_size=20, autofit=True, workspace_dir=None, **unused):
    draw = ImageDraw.Draw(Image.new('RGBA', (W, H)))
    quote_text = unicodedata.normalize('NFC', quote_text or '')
    credit_text = unicodedata.normalize('NFC', credit_text or '')
    qsize, csize = int(quote_size), int(credit_size)
    while True:
        qfont = get_font('segoeuib.ttf' if theme_index == 3 else 'timesbd.ttf', qsize, workspace_dir)
        cfont = get_font('segoeui.ttf', csize, workspace_dir)
        lines = wrap_text(quote_text, qfont, 768, draw)
        credits = wrap_text(credit_text, cfont, 768, draw)
        # Shared baseline bounds: diacritics must not shift each line's letter bodies.
        qboxes = [draw.textbbox((0, 0), s, font=qfont, anchor='ls') for s in lines]
        cboxes = [draw.textbbox((0, 0), s, font=cfont, anchor='ls') for s in credits]
        qtop = min((box[1] for box in qboxes), default=-qsize)
        ctop = min((box[1] for box in cboxes), default=-csize)
        qheight = max((box[3] for box in qboxes), default=0) - qtop
        cheight = max((box[3] for box in cboxes), default=0) - ctop
        qline, cline = math.ceil(qheight + qsize * .28), math.ceil(cheight + csize * .35)
        qh = len(lines) * qline
        ch = len(credits) * cline
        height = 48 + 32 + qh + (40 + ch if credits else 0) + 40
        if height > SAFE_BOTTOM - 180 and qsize > 28:
            qsize -= 2
            continue
        if autofit and len(lines) > 4 and qsize > 48:
            qsize -= 2
            continue
        break
    if height > SAFE_BOTTOM - 180:
        raise ValueError('Nội dung quá dài để hiển thị an toàn. Hãy bật tự động chia cảnh hoặc rút ngắn nguồn.')
    preferred = 260 if pos_mode == 'top' else (960 - height / 2 if pos_mode == 'center' else 1180)
    top = int(max(180, min(SAFE_BOTTOM - height, preferred + vertical_offset)))
    return dict(lines=lines, credits=credits, qfont=qfont, cfont=cfont, qline=qline, cline=cline,
                top=top, bottom=top + height, height=height, quote_y=top + 80,
                credit_y=top + 80 + qh + 40, quote_size=qsize,
                quote_baseline=top + 80 - qtop, credit_baseline=top + 80 + qh + 40 - ctop)


def soft_outline(mask, style):
    """Colored outer halo: dilate glyph alpha, feather, then exclude the sharp glyph itself."""
    layer = Image.new('RGBA', mask.size)
    bounds = mask.getbbox()
    width, blur = int(style['outline_width']), float(style['outline_blur'])
    if not bounds or not style['outline_enabled'] or style['outline_opacity'] <= 0 or (width == 0 and blur == 0):
        return layer
    pad = width + math.ceil(blur * 3) + 2
    box = (max(0, bounds[0] - pad), max(0, bounds[1] - pad),
           min(mask.width, bounds[2] + pad), min(mask.height, bounds[3] + pad))
    ink = mask.crop(box)
    expanded = ink.filter(ImageFilter.MaxFilter(width * 2 + 1)) if width else ink
    feathered = expanded.filter(ImageFilter.GaussianBlur(blur)) if blur else expanded
    alpha = ImageChops.subtract(feathered, ink).point([round(i * style['outline_opacity']) for i in range(256)])
    color = '#101018' if style['outline_color'] == 'auto' else style['outline_color']
    colored = Image.new('RGBA', ink.size, ImageColor.getrgb(color) + (0,))
    colored.putalpha(alpha)
    layer.paste(colored, box[:2])
    return layer


def paint_outlined_text(image, entries, font, fill, style, anchor='lt'):
    mask = Image.new('L', image.size)
    pen = ImageDraw.Draw(mask)
    for x, y, text in entries:
        pen.text((x, y), text, font=font, anchor=anchor, fill=255)
    image = Image.alpha_composite(image, soft_outline(mask, style))
    ink = Image.new('RGBA', image.size, fill)
    ink.putalpha(mask if fill[3] == 255 else mask.point([round(i * fill[3] / 255) for i in range(256)]))
    return Image.alpha_composite(image, ink)


def render_overlay(quote_text, credit_text='Thanh Vị Sách Hay Mỗi Ngày', header_text='', theme_index=0,
                   pos_mode='bottom', vertical_offset=0, quote_size=68, credit_size=20,
                   shade=.70, autofit=True, workspace_dir=None, outline_enabled=True,
                   outline_color='auto', outline_width=4, outline_blur=8, outline_opacity=.85):
    style = normalize_settings(dict(outline_enabled=outline_enabled, outline_color=outline_color,
                                    outline_width=outline_width, outline_blur=outline_blur, outline_opacity=outline_opacity))
    if style['outline_color'] == 'auto':
        style['outline_color'] = '#fff8e9' if theme_index == 4 else '#101018'
    layout = layout_overlay(quote_text, credit_text, theme_index, pos_mode, vertical_offset, quote_size, credit_size, autofit, workspace_dir)
    im = Image.new('RGBA', (W, H))
    draw = ImageDraw.Draw(im)
    top, bottom = layout['top'], layout['bottom']
    centered = theme_index in (1, 4)
    paper = theme_index == 4
    gold = (233, 199, 143, 255)
    if theme_index in (2, 4):
        shadow = Image.new('RGBA', (W, H))
        ImageDraw.Draw(shadow).rounded_rectangle((86, top + 8, 958, bottom + 8), 28, fill=(0, 0, 0, 115))
        im = Image.alpha_composite(im, shadow.filter(ImageFilter.GaussianBlur(12)))
        draw = ImageDraw.Draw(im)
        draw.rounded_rectangle((82, top, 954, bottom), 26,
                               fill=(255, 247, 229, 250) if paper else (20, 25, 28, int(205 + 45 * shade)),
                               outline=(180, 151, 106, 200), width=2)
        if not paper:
            draw.rounded_rectangle((94, top + 12, 942, bottom - 12), 18, outline=(180, 151, 106, 65), width=1)
    else:
        # Continuous soft scrim reaches the footer without a hard bottom seam.
        for y in range(max(0, top - 220), H if pos_mode == 'bottom' else min(H, bottom + 220)):
            distance = max(top - y, y - bottom, 0)
            factor = max(0., 1 - distance / 220)
            alpha = int((65 + 165 * shade) * factor)
            draw.line((0, y, W, y), fill=(6, 16, 23, alpha))
    accent = (165, 124, 76, 255) if paper else gold
    ornament_y = top + 43
    if centered:
        draw.line((447, ornament_y, 493, ornament_y), fill=accent, width=2)
        draw.polygon([(518, ornament_y - 6), (524, ornament_y), (518, ornament_y + 6), (512, ornament_y)], fill=accent)
        draw.line((543, ornament_y, 589, ornament_y), fill=accent, width=2)
    elif theme_index == 3:
        draw.rounded_rectangle((110, top + 48, 116, bottom - 40), 3, fill=gold)
    else:
        draw.line((134, ornament_y, 194, ornament_y), fill=gold, width=2)
        draw.ellipse((206, ornament_y - 3, 212, ornament_y + 3), fill=gold)
    color = (64, 55, 43, 255) if paper else ((255, 251, 242, 255) if theme_index in (1, 3) else (250, 230, 191, 255))
    y = layout['quote_baseline']
    entries = []
    for line in layout['lines']:
        width = draw.textlength(line, font=layout['qfont'])
        x = (1036 - width) / 2 if centered else 134
        entries.append((x, y, line))
        y += layout['qline']
    im = paint_outlined_text(im, entries, layout['qfont'], color, style, anchor='ls')
    draw = ImageDraw.Draw(im)
    if layout['credits']:
        y = layout['credit_baseline']
        line_start = 438 if centered else 134
        draw.line((line_start, layout['credit_y'] - 20, line_start + 160, layout['credit_y'] - 20), fill=accent, width=1)
        entries = []
        for line in layout['credits']:
            x = (1036 - draw.textlength(line, font=layout['cfont'])) / 2 if centered else 134
            entries.append((x, y, line))
            y += layout['cline']
        # Keep the smaller source text legible without an oversized halo.
        ratio = min(1., credit_size / layout['quote_size'])
        credit_style = {**style, 'outline_width': round(style['outline_width'] * ratio),
                        'outline_blur': style['outline_blur'] * ratio}
        im = paint_outlined_text(im, entries, layout['cfont'], (111, 83, 49, 255) if paper else (238, 220, 187, 255), credit_style, anchor='ls')
    return im


def overlay_key(plan, scene):
    import hashlib, json
    if plan.get('text_track'):
        return hashlib.sha256(json.dumps(dict(version=plan['version'],track=plan['text_track']),sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:32]
    keys = ('credit','theme_index','vertical_offset','quote_size','credit_size','shade','autofit',
            'outline_enabled','outline_color','outline_width','outline_blur','outline_opacity')
    return hashlib.sha256(json.dumps(dict(version=plan['version'],text=scene['text'],pos=scene['resolved_pos'],
                                          settings={k:plan['settings'][k] for k in keys}),sort_keys=True,
                                     ensure_ascii=False).encode('utf-8')).hexdigest()[:32]


def scene_overlay(plan, scene, workspace_dir):
    if plan.get('text_track'):
        from core.scroll_text import scroll_frame
        image = Image.new('RGBA',(W,H))
        track = plan['text_track']
        image.alpha_composite(scroll_frame(track,scene['text_start']+.21,workspace_dir), (track['rect']['x'],track['rect']['y']))
        return image
    s = plan['settings']
    return render_overlay(scene['text'], s['credit'], theme_index=s['theme_index'], pos_mode=scene['resolved_pos'],
                          vertical_offset=s['vertical_offset'], quote_size=s['quote_size'], credit_size=s['credit_size'],
                          shade=s['shade'], autofit=s['autofit'], workspace_dir=workspace_dir,
                          **{k: s[k] for k in ('outline_enabled', 'outline_color', 'outline_width', 'outline_blur', 'outline_opacity')})


def _execute(cmd):
    result = run_media(cmd, stdout=-3, stderr=-1, timeout=3600)
    if result.returncode:
        raise RuntimeError('FFmpeg không dựng được video: ' + result.stderr.decode('utf-8', errors='replace')[-3500:])


def render_plan(plan, output_path, workspace_dir, preview=False, progress_callback=None):
    from core.planner import load_plan
    # Reject stale files even if a plan was queued before a source edit.
    plan = load_plan(plan['plan_id'], workspace_dir)
    start = time.time()
    width, height = PREVIEW_SIZE if preview else (W, H)
    direct_preview = preview and len(plan['scenes']) <= 4
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_name(output_path.stem + '.partial.mp4')
    ffmpeg = tool_path('ffmpeg')
    settings = plan['settings']
    scrolling = bool(plan.get('text_track'))
    try:
        with tempfile.TemporaryDirectory(prefix='reel_render_') as tmp:
            clips, overlays = [], []
            for i, scene in enumerate(plan['scenes']):
                if progress_callback:
                    progress_callback(int(5 + 55 * i / len(plan['scenes'])), f'Đang chuẩn bị cảnh {i + 1}/{len(plan["scenes"])}')
                duration = scene['end'] - scene['start']
                target = str(Path(tmp) / f'background_{i}.mp4')
                # Decode before trimming for accurate MOV timestamps, then slow only when needed.
                vf = (f'trim=start={scene["source_start"]}:end={scene["source_end"]},'
                      f'setpts=(PTS-STARTPTS)/{scene["speed"]},scale={width}:{height}:force_original_aspect_ratio=increase,'
                      f'crop={width}:{height},setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=0.2,trim=duration={duration},format=yuv420p')
                if not direct_preview:
                    _execute([ffmpeg, '-y', '-v', 'error', '-threads', '2', '-i', scene['video_path'], '-an', '-vf', vf,
                              '-threads', '2', '-c:v', 'libx264', '-preset', 'ultrafast' if preview else 'veryfast',
                              '-crf', '24' if preview else '18', '-t', str(duration), target])
                clips.append(scene['video_path'] if direct_preview else target)
                if not scrolling:
                    overlay = Path(tmp) / f'overlay_{i}.png'
                    picture = scene_overlay(plan, scene, workspace_dir)
                    if preview:
                        picture = picture.resize((width, height), Image.Resampling.LANCZOS)
                    picture.save(overlay)
                    overlays.append(str(overlay))
            if scrolling:
                from core.scroll_text import write_scroll_video
                overlay = Path(tmp)/'scroll.mov'
                write_scroll_video(plan['text_track'],overlay,workspace_dir,width/W,progress_callback)
                overlays.append(str(overlay))
            if progress_callback:
                progress_callback(65, 'Đang ghép cảnh, chữ và nhạc…')
            cmd = [ffmpeg, '-y', '-v', 'error', '-filter_complex_threads', '1']
            for index, clip in enumerate(clips):
                cmd += ['-threads', '2']
                if direct_preview:
                    scene = plan['scenes'][index]
                    cmd += ['-ss', str(scene['source_start']), '-t', str(scene['source_end'] - scene['source_start'])]
                cmd += ['-i', clip]
            for overlay in overlays:
                cmd += (['-threads','2','-i',overlay] if scrolling else ['-loop', '1', '-framerate', '30', '-i', overlay])
            music = plan.get('music')
            has_music = bool(music and settings['music_volume'] > 0)
            if has_music:
                cmd += ['-stream_loop', '-1', '-i', music['path']]
            parts = []
            for i, scene in enumerate(plan['scenes']):
                normalize = ''
                if direct_preview:
                    normalize = (f'setpts=(PTS-STARTPTS)/{scene["speed"]},'
                                 f'scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},'
                                 f'setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=0.2,'
                                 f'trim=duration={scene["end"] - scene["start"]},')
                parts.append(f'[{i}:v]{normalize}settb=AVTB,setpts=PTS-STARTPTS,format=yuv444p,fps=30[b{i}]')
            last = 'b0'
            for i in range(1, len(clips)):
                nxt = f'cross{i}'
                parts.append(f'[{last}][b{i}]xfade=transition=fade:duration=0.4:offset={plan["scenes"][i]["start"]}[{nxt}]')
                last = nxt
            if scrolling:
                rect = plan['text_track']['rect']
                x, y = round(rect['x']*width/W), round(rect['y']*height/H)
                parts.append(f'[{last}][{len(clips)}:v]overlay={x}:{y}:format=yuv444:eof_action=pass[scrolltext]')
                last = 'scrolltext'
            for i, scene in enumerate([] if scrolling else plan['scenes']):
                st, et = scene['text_start'], scene['text_end']
                parts.append(f'[{len(clips) + i}:v]format=rgba,fade=t=in:st={st}:d=0.2:alpha=1,fade=t=out:st={et - .2}:d=0.2:alpha=1[o{i}]')
                nxt = f'letter{i}'
                parts.append(f'[{last}][o{i}]overlay=0:0:eof_action=pass:enable=\'gte(t,{st})*lt(t,{et})\'[{nxt}]')
                last = nxt
            if has_music:
                parts.append(f'[{len(clips) + len(overlays)}:a]asetpts=PTS-STARTPTS,volume={settings["music_volume"]},afade=t=in:st=0:d=0.6,afade=t=out:st={max(0, plan["duration"] - 1.2)}:d=1.2[a]')
            cmd += ['-filter_complex', ';'.join(parts), '-map', f'[{last}]']
            cmd += ['-map', '[a]', '-c:a', 'aac', '-b:a', '96k' if preview else '192k'] if has_music else ['-an']
            cmd += ['-threads', '2', '-c:v', 'libx264', '-preset', 'ultrafast' if preview else 'veryfast', '-crf', '26' if preview else '19',
                    '-pix_fmt', 'yuv420p', '-r', '30', '-t', str(plan['duration']), '-movflags', '+faststart', str(partial)]
            _execute(cmd)
        partial.replace(output_path)
    finally:
        if partial.exists():
            partial.unlink()
    if progress_callback:
        progress_callback(100, 'Đã hoàn tất.')
    return dict(success=True, output_path=str(output_path), duration=plan['duration'], slides_count=len(plan['scenes']),
                resolved_pos=plan['scenes'][0]['resolved_pos'], elapsed=round(time.time() - start, 2),
                size_bytes=output_path.stat().st_size, plan_id=plan['plan_id'], error=None)


def render_reel_video(background_video_path, quote_text, credit_text='Thanh Vị Sách Hay Mỗi Ngày',
                      theme_index=0, pos_mode='auto', vertical_offset=0, quote_size=68, credit_size=20,
                      shade=.70, duration=12., auto_paginate=True, music_path=None, music_volume=.85,
                      video_volume=0., output_path=None, workspace_dir=None, progress_callback=None, autofit=True,
                      outline_enabled=True, outline_color='auto', outline_width=4, outline_blur=8, outline_opacity=.85):
    from core.planner import build_plan
    from core.video_detector import VideoDetector
    workspace_dir = workspace_dir or os.getcwd()
    try:
        payload = dict(video_path=background_video_path, quote=quote_text, credit=credit_text,
                              theme_index=theme_index, pos_mode=pos_mode, vertical_offset=vertical_offset,
                              quote_size=quote_size, credit_size=credit_size, shade=shade, duration=duration,
                              auto_paginate=auto_paginate, music_volume=music_volume, autofit=autofit,
                              outline_enabled=outline_enabled, outline_color=outline_color, outline_width=outline_width,
                              outline_blur=outline_blur, outline_opacity=outline_opacity)
        output_path = output_path or str(Path(workspace_dir) / 'output_videos' / f'Reel_{time.time_ns()}.mp4')
        from core.footage_pool import FootagePool
        from core.persistence import file_mutex
        import uuid
        pool=FootagePool(workspace_dir);token=uuid.uuid4().hex
        with file_mutex(Path(workspace_dir)/'reel_export.lock',timeout=7200):
            plan=build_plan(payload,workspace_dir,VideoDetector(workspace_dir))
            pool.reserve(plan,token)
            try:
                pool.validate_export(token)
                result=render_plan(plan,output_path,workspace_dir,progress_callback=progress_callback)
                pool.finish(token,True)
                return result
            except Exception:
                pool.finish(token,False)
                raise
    except Exception as error:
        return dict(success=False, error=str(error), elapsed=0, output_path=str(output_path or ''))
