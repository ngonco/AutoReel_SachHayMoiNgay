# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import shutil

root = Path(SPECPATH)
ffmpeg = shutil.which('ffmpeg')
if not ffmpeg:
    raise RuntimeError('Build needs FFmpeg on PATH.')
media_bin = Path(ffmpeg).parent
# Shared FFmpeg builds need their adjacent DLLs; retain their relative folder.
data = [(str(root / 'ui'), 'ui'), (str(root / 'assets' / 'thien_chuong.wav'), 'assets')]
for font in ['timesbd.ttf', 'segoeui.ttf', 'segoeuib.ttf']:
    candidate = root / 'assets' / 'fonts' / font
    if not candidate.exists():
        candidate = Path('C:/Windows/Fonts') / font
    data.append((str(candidate), 'assets/fonts'))
for name in ['ffmpeg.exe', 'ffprobe.exe']:
    data.append((str(media_bin / name), 'bin'))
for dll in media_bin.glob('*.dll'):
    data.append((str(dll), 'bin'))

a = Analysis([str(root / 'app.py')], pathex=[str(root)], binaries=[], datas=data,
             hiddenimports=['PIL.Image','PIL.ImageDraw','PIL.ImageFont','PIL.ImageFilter','cv2','numpy','tkinter'],
             hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['torch','torchaudio','scipy','matplotlib','pandas','sklearn','transformers','gradio','streamlit','yt_dlp','IPython','pytest'],
             noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='AutoReelSachHay', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False, runtime_tmpdir=None,
          console=False, disable_windowed_traceback=False)
