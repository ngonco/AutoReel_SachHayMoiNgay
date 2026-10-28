"""Reproducible portable Windows build; keeps the previous executable locally."""
from pathlib import Path
import shutil
import subprocess
import sys


def build():
    root=Path(__file__).resolve().parent
    staging=root/'.cache'/'package'
    cmd=[sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(staging),
         '--workpath',str(root/'build'),str(root/'AutoReelSachHay.spec')]
    subprocess.run(cmd,cwd=root,check=True)
    built=staging/'AutoReelSachHay.exe'
    target=root/'AutoReelSachHay_v10.exe'
    if target.exists():
        shutil.copy2(target,root/'AutoReelSachHay_v10.previous.exe')
    shutil.copy2(built,target)
    alternate=root/'dist'/'AutoReelSachHay'
    alternate.mkdir(parents=True,exist_ok=True)
    shutil.copy2(built,alternate/'AutoReelSachHay_v10.exe')
    print('Built:',target)
    return target

if __name__=='__main__':
    if sys.stdout and hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    build()
