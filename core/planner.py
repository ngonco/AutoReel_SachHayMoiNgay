"""Authoritative, persisted plans consumed by preview, export and batch."""
import hashlib
import json
from pathlib import Path
import unicodedata
from core.media import probe, resource_path
from core.paginator import split_into_slides, calculate_slide_timings
from core.settings import normalize_settings

PLAN_VERSION = 'multi-scene-v2-template-2'


def fingerprint(path):
    p = Path(path).resolve()
    stat = p.stat()
    return dict(path=str(p), size=stat.st_size, mtime_ns=stat.st_mtime_ns)


def build_plan(payload, workspace_dir, detector):
    settings = normalize_settings(payload)
    text = unicodedata.normalize('NFC', str(payload.get('quote', ''))).strip()
    if not text:
        raise ValueError('Hãy nhập nội dung câu nói.')
    if len(text) > 20000:
        raise ValueError('Nội dung tối đa 20.000 ký tự mỗi reel.')
    videos = detector.scan_all_videos()
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
    ordered = sorted(videos, key=lambda v: (not v.get('is_vertical', True), v['name'].casefold(), v['path']))
    pool = [chosen] + [v for v in ordered if Path(v['path']).resolve() != Path(chosen['path']).resolve()]
    slides = split_into_slides(text, settings['auto_paginate'])
    timings = calculate_slide_timings(slides, settings['duration'])
    scenes = []
    for i, timing in enumerate(timings):
        source = pool[i % len(pool)]
        info = probe(source['path'])
        needed = timing['end'] - timing['start']
        trim_start = min(.5, info['duration'] / 4)
        take = min(needed, info['duration'] - trim_start)
        scenes.append({**timing, 'index': i, 'video_name': source['name'],
                       'video_path': str(Path(source['path']).resolve()), 'source_start': trim_start,
                       'source_end': trim_start + take, 'speed': take / needed,
                       'resolved_pos': source.get('recommended_pos', 'bottom') if settings['pos_mode'] == 'auto' else settings['pos_mode'],
                       'source': fingerprint(source['path']), 'source_info': info,
                       'thumb_url': source.get('thumb_url', '')})
    music = Path(workspace_dir) / 'assets' / 'thien_chuong.wav'
    if not music.is_file():
        music = resource_path('assets', 'thien_chuong.wav')
    plan = dict(version=PLAN_VERSION, settings=settings, quote=' '.join(text.split()), scenes=scenes,
                duration=timings[-1]['end'], transition=.4,
                music=fingerprint(music) if music.is_file() else None)
    key = hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
    plan['plan_id'] = key
    folder = Path(workspace_dir) / '.cache' / 'plans'
    folder.mkdir(parents=True, exist_ok=True)
    (folder / (key + '.json')).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
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
