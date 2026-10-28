"""Offline soundtrack library beside footage; public read-only Hugging Face downloads."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import urllib.parse
import urllib.request
import uuid
from core.media import run_media, tool_path
from core.persistence import file_mutex

REPOSITORY='vinhn8n/voicedaoly'
REMOTE_FOLDER='music background'
EXTENSIONS={'.mp3','.wav','.m4a','.aac','.flac','.ogg'}


def music_folder(workspace,settings):
    root=Path(settings.get('background_video_directory') or Path(workspace)/'CLIP TƯỢNG PHẬT LQ')
    return root/'NHẠC NỀN'


def music_tracks(workspace,settings):
    folder=music_folder(workspace,settings)
    if not folder.is_dir():return []
    tracks=[]
    for path in sorted(folder.iterdir(),key=lambda p:p.name.casefold()):
        if path.is_file() and path.suffix.lower() in EXTENSIONS:
            stat=path.stat();key=hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:32]
            tracks.append(dict(id=key,path=str(path.resolve()),name=path.stem,size=stat.st_size,mtime_ns=stat.st_mtime_ns,
                               url='/api/music_file/'+key))
    return tracks


@lru_cache(maxsize=512)
def audio_info(path,size,mtime_ns):
    result=run_media([tool_path('ffprobe'),'-v','error','-show_streams','-show_format','-of','json',str(path)],
                     capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    if result.returncode:raise ValueError('Không đọc được nhạc: '+Path(path).name)
    data=json.loads(result.stdout)
    stream=next((s for s in data.get('streams',[]) if s.get('codec_type')=='audio'),None)
    duration=float((stream or {}).get('duration') or data.get('format',{}).get('duration') or 0)
    if not stream or duration<=0:raise ValueError('File nhạc không có âm thanh hợp lệ: '+Path(path).name)
    return dict(duration=duration)


def choose_music(workspace,settings,quote,previous=''):
    mode=settings['music_mode'];tracks=music_tracks(workspace,settings)
    reason='';chosen=None
    if mode=='none':return None,dict(name='Tắt nhạc',reason='')
    if mode=='selected':
        chosen=next((t for t in tracks if t['path']==settings['music_path']),None)
        if not chosen:raise ValueError('Bài nhạc đã chọn không còn trong kho offline. Hãy chọn lại nhạc.')
    elif mode=='random' and tracks:
        candidates=[t for t in tracks if t['path']!=previous] or tracks
        seed=hashlib.sha256((' '.join(quote.split())+'|'+settings['music_seed']).encode()).hexdigest()
        chosen=candidates[int(seed,16)%len(candidates)]
    if chosen:
        path=Path(chosen['path']);stat=path.stat();info=audio_info(str(path),stat.st_size,stat.st_mtime_ns)
        return path,dict(name=chosen['name'],reason='',**info)
    return None,dict(name='Chưa có nhạc',reason='Kho nhạc offline chưa có bài. Bấm Tải/bổ sung kho nhạc hoặc chọn lại folder footage.')


def remote_manifest():
    with urllib.request.urlopen('https://huggingface.co/api/datasets/'+REPOSITORY,timeout=30) as response:
        revision=json.load(response)['sha']
    url='https://huggingface.co/api/datasets/'+REPOSITORY+'/tree/'+revision+'/'+urllib.parse.quote(REMOTE_FOLDER)+'?recursive=true&limit=1000'
    with urllib.request.urlopen(url,timeout=30) as response:
        data=json.load(response)
        if response.headers.get('Link'):raise ValueError('Kho nhạc quá lớn cho danh sách hiện tại; cần cập nhật bộ tải.')
    files=[f for f in data if f.get('type')=='file' and f.get('path','').startswith(REMOTE_FOLDER+'/') and Path(f['path']).suffix.lower() in EXTENSIONS]
    if not files:raise ValueError('Kho nhạc công khai chưa có file âm thanh.')
    return dict(revision=revision,files=files)


def download_track(folder,revision,item):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    filename=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',Path(item['path']).name).rstrip('. ')
    if not filename or filename in ('.','..'):raise ValueError('Tên nhạc không hợp lệ.')
    expected=item.get('lfs',{}).get('oid');size=int(item['size'])
    if not expected or len(expected)!=64 or not 0<size<512*1024*1024:raise ValueError('Thông tin kiểm tra file nhạc không hợp lệ.')
    target=folder/filename
    def valid(path):
        if not path.is_file() or path.stat().st_size!=size:return False
        with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()==expected
    with file_mutex(folder/(hashlib.sha256(filename.encode()).hexdigest()[:24]+'.download.lock'),timeout=180):
        if valid(target):return target
        if target.exists():
            target=target.with_name(target.stem+'.hf-'+expected[:8]+target.suffix)
            if valid(target):return target
            if target.exists():raise ValueError('File nhạc cùng tên đã thay đổi; giữ nguyên file để kiểm tra: '+target.name)
        partial=folder/(uuid.uuid4().hex+'.partial')
        url='https://huggingface.co/datasets/'+REPOSITORY+'/resolve/'+revision+'/'+urllib.parse.quote(item['path'],safe='/')
        try:
            with urllib.request.urlopen(url,timeout=45) as response,partial.open('wb') as stream:
                total=0;digest=hashlib.sha256()
                while True:
                    chunk=response.read(256*1024)
                    if not chunk:break
                    total+=len(chunk)
                    if total>size:raise ValueError('Dung lượng nhạc không khớp danh sách.')
                    digest.update(chunk);stream.write(chunk)
            if total!=size or digest.hexdigest()!=expected:raise ValueError('Nhạc tải chưa đủ hoặc sai mã kiểm tra.')
            audio_info(str(partial),size,partial.stat().st_mtime_ns)
            partial.replace(target);return target
        finally:partial.unlink(missing_ok=True)


class MusicLibraryService:
    def __init__(self,workspace):
        self.workspace=Path(workspace);self.lock=threading.Lock();self.state=dict(running=False,done=0,total=0,errors=[])
    def catalog(self,settings):
        with self.lock:status=dict(self.state)
        return dict(directory=str(music_folder(self.workspace,settings)),tracks=music_tracks(self.workspace,settings),download=status)
    def download(self,settings):
        with self.lock:
            if self.state['running']:return dict(self.state)
            folder=music_folder(self.workspace,settings)
            self.state=dict(running=True,done=0,total=0,errors=[],directory=str(folder))
        threading.Thread(target=self._download,args=(folder,),name='offline-music',daemon=True).start()
        with self.lock:return dict(self.state)
    def _download(self,folder):
        try:
            manifest=remote_manifest()
            with self.lock:self.state['total']=len(manifest['files'])
            with ThreadPoolExecutor(max_workers=3,thread_name_prefix='music-download') as executor:
                futures={executor.submit(self._track,folder,manifest['revision'],item):item for item in manifest['files']}
                for future in as_completed(futures):
                    try:future.result()
                    except Exception as error:
                        with self.lock:self.state['errors'].append(str(error))
                    with self.lock:self.state['done']+=1
        except Exception as error:
            with self.lock:self.state['errors'].append(str(error))
        finally:
            with self.lock:self.state['running']=False
    def _track(self,folder,revision,item):
        for attempt in range(2):
            try:return download_track(folder,revision,item)
            except Exception:
                if attempt:raise
                time.sleep(.3)
