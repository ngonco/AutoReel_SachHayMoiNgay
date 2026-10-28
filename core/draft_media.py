"""Reusable background-only proxies. Never reserve or commit footage turns."""
import hashlib
import json
from pathlib import Path
import threading
import time
import uuid
from core.media import run_media, tool_path, probe
from core.persistence import file_mutex

PROXY_VERSION = 'draft-360x640-h264-30-gop15-v1'


def source_key(source):
    return hashlib.sha256(json.dumps([PROXY_VERSION, source], sort_keys=True).encode()).hexdigest()[:32]


class DraftMediaService:
    def __init__(self, workspace, export_busy=lambda:False):
        self.folder = Path(workspace)/'.cache'/'draft_media'
        self.folder.mkdir(parents=True, exist_ok=True)
        self.export_busy = export_busy
        self.condition = threading.Condition()
        self.sources = {}; self.pending = []; self.states = {}; self.active = None
        self.closed = False
        self.background_after = 0
        self.thread = threading.Thread(target=self._worker, name='draft-media', daemon=True)
        self.thread.start()

    def _register(self, source):
        path = Path(source['path']).resolve()
        stat = path.stat()
        actual = dict(path=str(path),size=stat.st_size,mtime_ns=stat.st_mtime_ns)
        if actual != source:
            raise ValueError('File nguồn đã thay đổi. Hãy cập nhật kịch bản.')
        key = source_key(source)
        self.sources[key] = source
        target = self.folder/(key+'.mp4')
        if target.is_file() and target.stat().st_size:
            self.states[key] = dict(status='ready',url='/api/draft_media/'+key+'.mp4')
        else:
            self.states.setdefault(key, dict(status='queued'))
        return key

    def set_library(self, videos):
        with self.condition:
            keys = []
            for video in videos:
                try:
                    path = Path(video['path']).resolve(); stat = path.stat()
                    keys.append(self._register(dict(path=str(path),size=stat.st_size,mtime_ns=stat.st_mtime_ns)))
                except OSError: continue
            # A folder switch discards queued work for the old library, never its media/cache.
            self.pending = [key for key in keys if self.states[key]['status']=='queued' and key!=self.active]
            self.background_after = time.monotonic()+1
            self.condition.notify_all()

    def prepare(self, plan, selected=0):
        with self.condition:
            keys = [self._register(scene['source']) for scene in plan['scenes']]
            selected = max(0,min(int(selected),len(keys)-1))
            priority = list(dict.fromkeys([keys[selected],*keys]))
            self.background_after = 0
            for key in priority:
                if self.states[key]['status']=='error': self.states[key] = dict(status='queued')
            self.pending = list(dict.fromkeys([*[k for k in priority if self.states[k]['status']=='queued' and k!=self.active],*self.pending]))
            self.condition.notify_all()
            return self._snapshot(keys)

    def status(self, plan):
        with self.condition:
            keys = [self._register(scene['source']) for scene in plan['scenes']]
            return self._snapshot(keys)

    def _snapshot(self, keys):
        return dict(scenes=[dict(index=i,key=key,**self.states[key]) for i,key in enumerate(keys)],
                    library=dict(ready=sum(s['status']=='ready' for s in self.states.values()),
                                 queued=len(self.pending),running=bool(self.active)))

    def media_path(self, name):
        if len(name)!=36 or not name.endswith('.mp4') or any(c not in '0123456789abcdef' for c in name[:-4]):
            raise ValueError('Mã footage nháp không hợp lệ.')
        with self.condition:
            source = self.sources.get(name[:-4])
            if not source: raise ValueError('Footage chưa được xác thực trong kho hoặc kịch bản.')
            self._register(source)
        return self.folder/name

    def _convert(self, key, source):
        target = self.folder/(key+'.mp4')
        with file_mutex(target.with_suffix('.lock'),timeout=1200):
            if target.is_file() and target.stat().st_size: return
            partial = self.folder/(key+'.'+uuid.uuid4().hex+'.partial.mp4')
            try:
                result = run_media([tool_path('ffmpeg'),'-y','-v','error','-threads','2','-i',source['path'],
                                    '-map','0:v:0','-an','-vf',
                                    'scale=360:640:force_original_aspect_ratio=increase,crop=360:640,setsar=1,fps=30',
                                    '-threads','2','-c:v','libx264','-preset','ultrafast','-crf','26',
                                    '-pix_fmt','yuv420p','-g','15','-keyint_min','15','-sc_threshold','0',
                                    '-movflags','+faststart',str(partial)],capture_output=True,timeout=1200)
                if result.returncode: raise ValueError('Không chuẩn bị được clip: '+Path(source['path']).name)
                probe(partial)
                with self.condition: self._register(source)
                partial.replace(target)
            finally:
                partial.unlink(missing_ok=True)

    def _worker(self):
        while True:
            with self.condition:
                self.condition.wait_for(lambda:self.closed or bool(self.pending),timeout=1)
                if self.closed:return
                if not self.pending:continue
                if time.monotonic()<self.background_after:
                    self.condition.wait(timeout=.2);continue
                if self.export_busy():
                    self.condition.wait(timeout=.5);continue
                key = self.pending.pop(0)
                if self.states[key]['status']=='ready':continue
                self.active=key;self.states[key]=dict(status='preparing')
                source=dict(self.sources[key])
            try:
                self._convert(key, source)
                result=dict(status='ready',url='/api/draft_media/'+key+'.mp4')
            except Exception as error:
                result=dict(status='error',error=str(error))
            with self.condition:
                self.states[key]=result;self.active=None

    def close(self):
        with self.condition:self.closed=True;self.pending.clear();self.condition.notify_all()
        self.thread.join(timeout=2)
