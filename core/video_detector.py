"""Video inventory and conservative subject-position estimates; local assets only."""
import json
from pathlib import Path
import threading
from PIL import Image
import cv2
import numpy as np
from core.media import probe, run_media, tool_path


class VideoDetector:
    def __init__(self, workspace_dir):
        self.workspace_dir = Path(workspace_dir)
        self.thumb_dir = self.workspace_dir / 'assets' / 'thumbnails'
        self.thumb_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.thumb_dir / 'video_cache.json'
        self.lock = threading.RLock()
        try:
            self.cache = json.loads(self.cache_file.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.cache = {}

    def scan_all_videos(self, directory=None):
        with self.lock:
            if directory is None:
                from core.settings import load_settings
                directory = load_settings(self.workspace_dir)['background_video_directory']
            if directory:
                root = Path(directory)
                if not root.is_dir():
                    raise ValueError('Folder video nền không tồn tại hoặc mất kết nối. Hãy chọn lại folder.')
                roots = [root]
            else:
                roots = [self.workspace_dir / 'CLIP TƯỢNG PHẬT LQ' / name for name in ('DỌC', 'NGANG')]
                roots.append(self.workspace_dir / 'assets' / 'imports')
            try:
                files = {p.resolve() for root in roots if root.exists() for p in root.rglob('*')
                         if p.is_file() and p.suffix.lower() in ('.mov', '.mp4', '.m4v', '.mkv')}
            except OSError as error:
                raise ValueError('Không đọc được folder video nền. Hãy kiểm tra kết nối và quyền truy cập.') from error
            results = []
            for p in sorted(files, key=lambda x: (x.name.casefold(), str(x))):
                try:
                    results.append(self.analyze_video(str(p)))
                except (ValueError, OSError):
                    continue
            if directory and not results:
                raise ValueError('Folder video nền không có clip hợp lệ. Hãy chọn folder khác.')
            return results

    def analyze_video(self, video_path):
        with self.lock:
            path = Path(video_path).resolve()
            stat = path.stat()
            key = str(path)
            old = self.cache.get(key, {})
            if old.get('cache_version') == 3 and old.get('mtime_ns') == stat.st_mtime_ns and old.get('size') == stat.st_size and Path(old.get('thumb_path', '')).is_file():
                return old
            info = probe(path)
            import hashlib
            thumb = self.thumb_dir / (hashlib.sha1(key.encode()).hexdigest()[:16] + '_thumb.jpg')
            if not thumb.is_file() or old.get('mtime_ns') != stat.st_mtime_ns:
                result = run_media([tool_path('ffmpeg'), '-y', '-v', 'error', '-ss', str(min(2., info['duration'] / 2)), '-i', str(path), '-frames:v', '1', '-vf', 'scale=270:480:force_original_aspect_ratio=increase,crop=270:480', str(thumb)], capture_output=True, timeout=45)
                if result.returncode or not thumb.is_file():
                    raise ValueError('Không tạo được ảnh xem trước: ' + path.name)
            head_y, kind = 600, 'default'
            try:
                image = np.array(Image.open(thumb).convert('RGB'))
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
                classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = classifier.detectMultiScale(gray, 1.1, 3, minSize=(20, 20))
                if len(faces):
                    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                    head_y, kind = int((y + h / 2) * 4), 'face'
                else:
                    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
                    mask = cv2.inRange(hsv, np.array([5, 25, 40]), np.array([35, 220, 255]))
                    rows = np.where(np.sum(mask > 0, axis=1) > image.shape[1] * .05)[0]
                    if len(rows):
                        head_y, kind = int(rows[0] * 4 + 160), 'color'
            except Exception:
                pass
            pos = 'bottom' if head_y < 960 else 'top'
            result = dict(name=path.name, path=str(path), mtime=stat.st_mtime, mtime_ns=stat.st_mtime_ns,
                          size=stat.st_size, **info, thumb_path=str(thumb), thumb_url='/api/thumb/' + thumb.name,
                          head_y=head_y, detection_type=kind, recommended_pos=pos, cache_version=3,
                          explanation='Ước lượng chủ thể ở nửa ' + ('trên → chữ nửa dưới' if pos == 'bottom' else 'dưới → chữ nửa trên') + '. Có thể chỉnh vị trí thủ công.')
            self.cache[key] = result
            import uuid
            temporary = self.cache_file.with_name(uuid.uuid4().hex + '.tmp')
            temporary.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(self.cache_file)
            return result
