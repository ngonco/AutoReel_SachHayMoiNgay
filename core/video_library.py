"""Native library selection, separate from user media and export destinations."""
import threading
from pathlib import Path
from core.settings import load_settings, save_settings_patch


def native_directory_dialog(directory):
    import tkinter as tk
    from tkinter.filedialog import askdirectory
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    try:
        return askdirectory(parent=root, title='Chọn folder video nền',
                            initialdir=str(directory), mustexist=True)
    finally:
        root.destroy()


class VideoLibraryService:
    def __init__(self, workspace, detector):
        self.workspace = Path(workspace)
        self.detector = detector
        self.lock = threading.Lock()

    def select(self, use_default=False):
        with self.lock:
            saved = load_settings(self.workspace)
            if use_default:
                directory = ''
            else:
                initial = Path(saved['background_video_directory'] or self.workspace)
                selected = native_directory_dialog(initial if initial.is_dir() else self.workspace)
                if not selected:
                    return dict(success=True, cancelled=True)
                directory = str(Path(selected).resolve())
            # Validate before replacing the remembered library. Never copy or alter source clips.
            videos = self.detector.scan_all_videos(directory)
            settings = save_settings_patch(self.workspace,
                                          dict(background_video_directory=directory, video_path=''))
            return dict(success=True, cancelled=False, directory=directory, videos=videos,
                        settings=settings)
