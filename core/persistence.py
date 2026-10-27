"""Cross-process locks and atomic local JSON writes for drafts and footage history."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import threading
import time
import uuid

_guard=threading.Lock()
_locks={}


@contextmanager
def file_mutex(path, timeout=15):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with _guard: local=_locks.setdefault(str(path.resolve()),threading.RLock())
    with local:
        with path.open('a+b') as handle:
            if handle.tell()==0:handle.write(b'0');handle.flush()
            deadline=time.monotonic()+timeout
            while True:
                try:
                    handle.seek(0)
                    if os.name=='nt':
                        import msvcrt
                        msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
                    else:
                        import fcntl
                        fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                    break
                except (OSError,BlockingIOError):
                    if time.monotonic()>=deadline:raise TimeoutError('Dữ liệu đang được phiên khác sử dụng. Hãy thử lại.')
                    time.sleep(.1)
            try:yield
            finally:
                handle.seek(0)
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(),fcntl.LOCK_UN)


def read_json(path, default):
    try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except FileNotFoundError:return default()


def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        with temp.open('w',encoding='utf-8') as stream:
            json.dump(data,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        temp.replace(path)
    finally:
        if temp.exists():temp.unlink()
