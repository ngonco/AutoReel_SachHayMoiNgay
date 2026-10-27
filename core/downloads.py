"""Native save destinations and atomic copies of completed Full HD jobs."""
from pathlib import Path
import os
import re
import tempfile
import threading
import unicodedata
import uuid
from core.settings import load_settings, save_settings_patch


def suggested_filename(quote):
    words = unicodedata.normalize('NFC', str(quote or '')).split()[:5]
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', ' '.join(words)).strip(' .')
    stem = stem[:160].rstrip(' .') or 'Reel'
    if re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', stem):
        stem = 'Reel ' + stem
    return stem + '.mp4'


def native_save_dialog(directory, filename):
    import tkinter as tk
    from tkinter.filedialog import asksaveasfilename
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    try:
        return asksaveasfilename(parent=root, title='Lưu video', initialdir=str(directory),
                                initialfile=filename, defaultextension='.mp4',
                                filetypes=[('Video MP4', '*.mp4')], confirmoverwrite=True)
    finally:
        root.destroy()


def copy_video(source, destination, progress):
    """Never leave a partial final file or destroy an existing file on failure."""
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        return
    temporary = None
    try:
        size = source.stat().st_size
        with source.open('rb') as src, tempfile.NamedTemporaryFile(
                dir=destination.parent, prefix='.reel-save-', suffix='.tmp', delete=False) as dst:
            temporary = Path(dst.name)
            copied = 0
            while chunk := src.read(1024 * 1024):
                dst.write(chunk)
                copied += len(chunk)
                progress(min(99, int(copied / max(1, size) * 100)), 'Đang lưu video…')
            dst.flush()
            os.fsync(dst.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class SaveVideoService:
    def __init__(self, workspace):
        self.workspace = Path(workspace)
        self.lock = threading.RLock()
        self.dialog_lock = threading.Lock()
        self.targets = {}

    def select(self, quote):
        with self.dialog_lock:
            remembered = load_settings(self.workspace)['last_save_directory']
            directory = Path(remembered) if remembered else self.workspace / 'output_videos'
            if not directory.is_dir():
                directory = self.workspace / 'output_videos'
                directory.mkdir(exist_ok=True)
            selected = native_save_dialog(directory, suggested_filename(quote))
            if not selected:
                return dict(success=True, cancelled=True)
            destination = Path(selected).resolve()
            if destination.suffix.lower() != '.mp4':
                raise ValueError('Hãy lưu video với đuôi .mp4.')
            save_settings_patch(self.workspace, dict(last_save_directory=str(destination.parent)))
            token = uuid.uuid4().hex
            with self.lock:
                self.targets[token] = dict(path=destination)
                if len(self.targets) > 100:
                    self.targets.pop(next(iter(self.targets)))
            return dict(success=True, cancelled=False, save_token=token, filename=destination.name)

    def save(self, token, render_job_id, jobs):
        with self.lock:
            target = self.targets.get(token)
            if not target:
                raise ValueError('Nơi lưu đã hết hiệu lực. Hãy bấm Tải video và chọn lại.')
            if target.get('job_id'):
                previous = jobs.get(target['job_id'])
                if previous['status'] != 'error':
                    return previous
            job = jobs.save_video(render_job_id, target['path'])
            target['job_id'] = job['job_id']
            return job
