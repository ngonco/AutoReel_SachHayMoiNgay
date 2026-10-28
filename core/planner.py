"""Authoritative, persisted plans consumed by preview, export and batch."""
import hashlib
import json
from pathlib import Path
import unicodedata
from core.media import probe, resource_path
from core.paginator import split_into_slides, calculate_slide_timings
from core.settings import normalize_settings, load_settings
from core.footage_pool import FootagePool
from core.persistence import atomic_json

PLAN_VERSION = 'multi-scene-v10-instant-draft-offline-music-downloads-2'


def fingerprint(path):
    p = Path(path).resolve()
    stat = p.stat()
    return dict(path=str(p), size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def build_plan(payload, workspace_dir, detector):
    if 'background_video_directory' not in payload:
        payload = {**payload, 'background_video_directory': load_settings(workspace_dir)['background_video_directory']}
    normalized = normalize_settings(payload)
    settings = {k:v for k,v in normalized.items() if k not in ('quote','quote_index','video_path','safe_zone','last_save_directory','scene_video_preferences','imported_video_paths')}
    text = '\n'.join(' '.join(line.split()) for line in unicodedata.normalize('NFC', str(payload.get('quote') or '')).splitlines() if line.strip())
    if not text:
        raise ValueError('Hãy nhập nội dung câu nói.')
    if len(text) > 20000:
        raise ValueError('Nội dung tối đa 20.000 ký tự mỗi reel.')
    videos = detector.scan_all_videos(payload['background_video_directory'])
    for path in normalized['imported_video_paths']:
        if Path(path).is_file() and all(Path(v['path']).resolve()!=Path(path).resolve() for v in videos):
            try: videos.append(detector.analyze_video(path))
            except (OSError, ValueError): pass
    selected = payload.get('video_path')
    if selected:
        if not Path(selected).is_file():
            raise ValueError('Video đã chọn không còn tồn tại. Hãy chọn lại nguồn.')
        chosen = next((v for v in videos if Path(v['path']).resolve() == Path(selected).resolve()), None)
        if not chosen:
            chosen = detector.analyze_video(selected)
    else:
        chosen = next(iter(videos), None)
    if not chosen:
        raise ValueError('Kho video trống. Hãy thêm clip hoặc chọn video khác.')
    if all(Path(v['path']).resolve()!=Path(chosen['path']).resolve() for v in videos):videos.append(chosen)
    slides = split_into_slides(text, settings['auto_paginate'])
    timings = calculate_slide_timings(slides, settings['duration'])
    avoid_ids = payload.get('previous_footage_ids', [])
    if not isinstance(avoid_ids, list) or any(not isinstance(key, str) or len(key) != 24 or
                                             any(c not in '0123456789abcdef' for c in key) for key in avoid_ids):
        raise ValueError('Danh sách footage câu trước không hợp lệ.')
    preferences = {int(i):str(Path(value['path']).resolve()) for i,value in normalized['scene_video_preferences'].items()
                   if int(i)<len(slides) and value['text']==slides[int(i)] and value['path']}
    allocations, pool_info = FootagePool(workspace_dir).preview(videos, len(timings), chosen, avoid_ids, text, preferences)
    scenes = []
    for i, timing in enumerate(timings):
        footage_id, source = allocations[i]
        info = probe(source['path'])
        needed = timing['end'] - timing['start']
        trim_start = min(.5, info['duration'] / 4)
        take = min(needed, info['duration'] - trim_start)
        scenes.append({**timing, 'index': i, 'video_name': source['name'], 'footage_id': footage_id,
                       'video_path': str(Path(source['path']).resolve()), 'source_start': trim_start,
                       'source_end': trim_start + take, 'speed': take / needed,
                       'resolved_pos': source.get('recommended_pos', 'bottom') if settings['pos_mode'] == 'auto' else settings['pos_mode'],
                       'source': fingerprint(source['path']), 'source_info': info,
                       'thumb_url': source.get('thumb_url', ''), 'suggestion':pool_info['scene_suggestions'][i]})
    from core.music_library import choose_music
    music,music_details=choose_music(workspace_dir,settings,text,str(payload.get('previous_music_path') or ''))
    mode = 'manual_lines' if '\n' in text else ('auto' if settings['auto_paginate'] else 'single')
    plan = dict(version=PLAN_VERSION, settings=settings, quote=text, segmentation_mode=mode, scenes=scenes, footage_pool=pool_info,
                duration=timings[-1]['end'], transition=.4,
                music=fingerprint(music) if music else None,music_details=music_details)
    from core.renderer import overlay_key
    for scene in scenes:
        scene['overlay_key'] = overlay_key(plan, scene)
    key = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
    plan['plan_id'] = key
    plan['music_url'] = '/api/plan_music/'+key if music else None
    folder = Path(workspace_dir) / '.cache' / 'plans'
    folder.mkdir(parents=True, exist_ok=True)
    atomic_json(folder / (key + '.json'), plan)
    return plan


def load_plan(plan_id, workspace_dir):
    if len(plan_id) != 24 or any(c not in '0123456789abcdef' for c in plan_id):
        raise ValueError('Mã kế hoạch không hợp lệ.')
    path = Path(workspace_dir) / '.cache' / 'plans' / (plan_id + '.json')
    if not path.is_file():
        raise ValueError('Kế hoạch đã hết hạn. Hãy tạo lại bản xem trước.')
    plan = json.loads(path.read_text(encoding='utf-8'))
    if plan['version'] != PLAN_VERSION:
        raise ValueError('Template đã thay đổi. Hãy tạo lại bản xem trước.')
    for f in [s['source'] for s in plan['scenes']] + ([plan['music']] if plan.get('music') else []):
        if not Path(f['path']).is_file() or fingerprint(f['path']) != f:
            raise ValueError('File nguồn đã thay đổi. Hãy tạo lại bản xem trước.')
    return plan
