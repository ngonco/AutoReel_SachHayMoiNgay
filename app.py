# -*- coding: utf-8 -*-
"""Local desktop studio: threaded HTTP API, authoritative plans and queued render jobs."""
import sys
import os
import json
import logging
from pathlib import Path
import socket
import subprocess
import threading
import time
import webbrowser
import multiprocessing
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote

# Must run before imports with optional multiprocessing hooks in frozen builds.
if __name__ == '__main__':
    multiprocessing.freeze_support()

BUNDLE_DIR = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
if getattr(sys, 'frozen', False):
    exe_dir = Path(sys.executable).parent
    BASE_DIR = next((p for p in [exe_dir, exe_dir.parent, exe_dir.parent.parent, Path.cwd()] if (p / 'CLIP TƯỢNG PHẬT LQ').is_dir()), exe_dir)
else:
    BASE_DIR = Path(__file__).resolve().parent

from core.pmdx_reader import get_all_quotes
from core.video_detector import VideoDetector
from core.planner import build_plan, load_plan
from core.renderer import scene_overlay
from core.settings import normalize_settings
from core.jobs import JobManager

video_detector = None
jobs = None
settings_lock = threading.Lock()


def read_settings():
    try:
        return normalize_settings(json.loads((BASE_DIR / 'settings.json').read_text(encoding='utf-8-sig')))
    except (OSError, ValueError, TypeError):
        return normalize_settings()


class ReelRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_GET(self):
        try:
            path = unquote(urlparse(self.path).path)
            if path in ('/', '/index.html', '/app.js', '/style.css'):
                name = 'index.html' if path == '/' else path[1:]
                return self._serve_file(BUNDLE_DIR / 'ui' / name, {'index.html': 'text/html; charset=utf-8', 'app.js': 'application/javascript; charset=utf-8', 'style.css': 'text/css; charset=utf-8'}[name])
            if path == '/api/health':
                return self._send_json(dict(success=True, version='multi-scene-v1', pid=os.getpid()))
            if path == '/api/quotes':
                return self._send_json(get_all_quotes(str(BASE_DIR)))
            if path == '/api/videos':
                return self._send_json(video_detector.scan_all_videos())
            if path == '/api/settings':
                return self._send_json(read_settings())
            if path.startswith('/api/jobs/'):
                return self._send_json(jobs.get(path.rsplit('/', 1)[-1]))
            if path.startswith('/api/overlay/'):
                _, _, _, plan_id, index = path.split('/')
                plan = load_plan(plan_id, BASE_DIR)
                scene = plan['scenes'][int(index)]
                folder = BASE_DIR / '.cache' / 'overlays'
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / f'{plan_id}_{int(index)}.png'
                if not target.is_file():
                    # Separate temporary files avoid races between parallel browser requests.
                    import uuid
                    tmp = folder / f'{uuid.uuid4().hex}.png'
                    scene_overlay(plan, scene, str(BASE_DIR)).save(tmp)
                    tmp.replace(target)
                return self._serve_file(target, 'image/png')
            routes = {'/api/thumb/': (BASE_DIR / 'assets' / 'thumbnails', 'image/jpeg'),
                      '/api/rendered_video/': (BASE_DIR / 'output_videos', 'video/mp4'),
                      '/api/preview_video/': (BASE_DIR / '.cache' / 'previews', 'video/mp4')}
            for prefix, (folder, mime) in routes.items():
                if path.startswith(prefix):
                    name = path[len(prefix):]
                    if name != Path(name).name or '\\' in name:
                        raise ValueError('Tên file không hợp lệ.')
                    return self._serve_file(folder / name, mime)
            if path == '/assets/thien_chuong.wav':
                p = BASE_DIR / 'assets' / 'thien_chuong.wav'
                return self._serve_file(p if p.is_file() else BUNDLE_DIR / 'assets' / p.name, 'audio/wav')
            self.send_error(404)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as error:
            logging.exception('GET failed')
            self._send_json(dict(success=False, error=str(error)), 400)

    def do_POST(self):
        try:
            path = urlparse(self.path).path
            length = int(self.headers.get('Content-Length', 0))
            if length > 1024 * 1024:
                raise ValueError('Yêu cầu quá lớn.')
            body = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            if path == '/api/settings':
                settings = normalize_settings(body)
                with settings_lock:
                    temp = BASE_DIR / 'settings.json.tmp'
                    temp.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')
                    temp.replace(BASE_DIR / 'settings.json')
                return self._send_json(dict(success=True, settings=settings))
            if path == '/api/plan':
                return self._send_json(build_plan(body, BASE_DIR, video_detector))
            if path in ('/api/preview', '/api/render'):
                plan = load_plan(str(body['plan_id']), BASE_DIR) if body.get('plan_id') else build_plan(body, BASE_DIR, video_detector)
                job = jobs.submit(plan, preview=path == '/api/preview')
                if path == '/api/preview' or body.get('async'):
                    return self._send_json(job, 202)
                # Legacy scripts still receive a completed render result.
                while job['status'] not in ('done', 'error'):
                    time.sleep(.2)
                    job = jobs.get(job['job_id'])
                return self._send_json(job.get('result', dict(success=False, error=job.get('error'))))
            if path == '/api/batch_render':
                videos = video_detector.scan_all_videos()
                if not videos:
                    raise ValueError('Kho video trống.')
                plans = [build_plan({**body, 'quote': q['quote'], 'video_path': videos[i % len(videos)]['path']}, BASE_DIR, video_detector) for i, q in enumerate(get_all_quotes(str(BASE_DIR)))]
                job = jobs.batch(plans)
                if body.get('async'):
                    return self._send_json(job, 202)
                while job['status'] not in ('done', 'error'):
                    time.sleep(.2)
                    job = jobs.get(job['job_id'])
                return self._send_json(job.get('result', dict(success=False, error=job.get('error'))))
            if path == '/api/open_folder':
                folder = BASE_DIR / 'output_videos'
                folder.mkdir(exist_ok=True)
                os.startfile(str(folder))
                return self._send_json(dict(success=True, path=str(folder)))
            if path == '/api/select_video':
                # A native picker returns a real local path, shared by preview and export.
                import tkinter as tk
                from tkinter.filedialog import askopenfilename
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                try:
                    name = askopenfilename(parent=root, title='Chọn video nền', filetypes=[('Video', '*.mp4 *.MOV *.mov *.mkv *.m4v')])
                finally:
                    root.destroy()
                return self._send_json(dict(success=True, video=video_detector.analyze_video(name) if name else None))
            self.send_error(404)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as error:
            logging.exception('POST failed')
            self._send_json(dict(success=False, error=str(error)), 400)

    def _send_json(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_file(self, path, mime):
        if not path.is_file():
            return self.send_error(404, 'File not found')
        size = path.stat().st_size
        start, end, status = 0, size - 1, 200
        range_header = self.headers.get('Range')
        if range_header:
            import re
            match = re.fullmatch(r'bytes=(\d*)-(\d*)', range_header)
            if not match or not any(match.groups()):
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.end_headers()
                return
            left, right = match.groups()
            start = int(left) if left else max(0, size - int(right))
            end = min(int(right), size - 1) if right and left else size - 1
            if start >= size or start > end:
                self.send_response(416)
                self.send_header('Content-Range', f'bytes */{size}')
                self.end_headers()
                return
            status = 206
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if status == 206:
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.end_headers()
        with path.open('rb') as source:
            source.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = source.read(min(256 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def log_message(self, format, *args):
        logging.debug(format, *args)


def find_free_port(start_port=8765):
    for port in range(start_port, start_port + 50):
        with socket.socket() as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError('Không tìm được cổng để mở ứng dụng.')


def launch_app_window(url):
    for p in [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Google\Chrome\Application\chrome.exe']:
        if Path(p).is_file():
            subprocess.Popen([p, f'--app={url}', '--window-size=1420,940'])
            return
    webbrowser.open(url)


def main():
    global video_detector, jobs
    logs = BASE_DIR / 'logs'
    logs.mkdir(exist_ok=True)
    logging.basicConfig(filename=logs / 'app.log', encoding='utf-8', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    # Windowed PyInstaller executables have no stdout/stderr handles.
    if sys.stdout is None:
        sys.stdout = open(logs / 'console.log', 'a', encoding='utf-8')
    if sys.stderr is None:
        sys.stderr = sys.stdout
    video_detector = VideoDetector(BASE_DIR)
    jobs = JobManager(BASE_DIR)
    if '--batch' in sys.argv:
        videos = video_detector.scan_all_videos()
        if not videos:
            raise ValueError('Kho video trống.')
        settings = read_settings()
        plans = [build_plan({**settings, 'quote': q['quote'], 'video_path': videos[i % len(videos)]['path']}, BASE_DIR, video_detector) for i, q in enumerate(get_all_quotes(str(BASE_DIR)))]
        job = jobs.batch(plans)
        while job['status'] not in ('done', 'error'):
            time.sleep(.5)
            job = jobs.get(job['job_id'])
        print(json.dumps(job, ensure_ascii=False))
        jobs.executor.shutdown()
        return
    port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else find_free_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), ReelRequestHandler)
    server.daemon_threads = True
    url = f'http://127.0.0.1:{port}'
    logging.info('Studio started: %s', url)
    print('Auto Reel: ' + url, flush=True)
    if '--headless' not in sys.argv:
        threading.Timer(.3, launch_app_window, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        jobs.executor.shutdown(wait=True)


if __name__ == '__main__':
    main()
