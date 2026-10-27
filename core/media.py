"""Local media tools shared by analysis, preview and export."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def resource_path(*parts):
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)).joinpath(*parts)


def tool_path(name):
    bundled = resource_path('bin', name + ('.exe' if os.name == 'nt' else ''))
    found = str(bundled) if bundled.is_file() else shutil.which(name)
    if not found:
        raise ValueError(f'Không tìm thấy {name}. Hãy cài FFmpeg hoặc dùng bản ứng dụng có thư mục bin.')
    return found


def run_media(args, **kwargs):
    return subprocess.run(args, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0, **kwargs)


def probe(path):
    result = run_media([tool_path('ffprobe'), '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
    if result.returncode:
        raise ValueError('Không đọc được video: ' + Path(path).name)
    data = json.loads(result.stdout)
    stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
    if not stream:
        raise ValueError('File không có hình ảnh video: ' + Path(path).name)
    width, height = stream['width'], stream['height']
    rotation = next((x.get('rotation', 0) for x in stream.get('side_data_list', []) if 'rotation' in x), stream.get('tags', {}).get('rotate', 0))
    if abs(int(rotation)) % 180 == 90:
        width, height = height, width
    duration = float(stream.get('duration') or data.get('format', {}).get('duration') or 0)
    if duration <= 0:
        raise ValueError('Thời lượng video không hợp lệ: ' + Path(path).name)
    return dict(width=width, height=height, duration=duration, is_vertical=height >= width)
