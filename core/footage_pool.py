"""Persistent fair footage allocation: successful exports consume turns, preview does not."""
import hashlib
import json
import os
from pathlib import Path
import time
from core.persistence import file_mutex,read_json,atomic_json


class FootageConflict(ValueError):
    code='footage_conflict'


def identity(video):
    digest=hashlib.sha256()
    with Path(video['path']).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()[:24]


def process_alive(pid):
    if pid==os.getpid():return True
    if os.name=='nt':
        import ctypes
        from ctypes import wintypes
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
        kernel.OpenProcess.restype=wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        handle=kernel.OpenProcess(0x1000,False,int(pid))
        if not handle:return ctypes.get_last_error()==5
        try:
            code=wintypes.DWORD()
            return bool(kernel.GetExitCodeProcess(handle,ctypes.byref(code))) and code.value==259
        finally:kernel.CloseHandle(handle)
    try:os.kill(int(pid),0);return True
    except ProcessLookupError:return False
    except PermissionError:return True


class FootagePool:
    def __init__(self,workspace):
        self.path=Path(workspace)/'footage_usage.json'
        self.lock=self.path.with_suffix('.lock')

    @staticmethod
    def empty():return dict(version=1,revision=0,counts={},reservations={},inventory={},fingerprints={})

    def _identity(self,video,state):
        path=Path(video['path']).resolve();stat=path.stat()
        cache=state.setdefault('fingerprints',{})
        record=cache.get(str(path))
        if record and record['size']==stat.st_size and record['mtime_ns']==stat.st_mtime_ns:return record['id']
        key=identity(video)
        cache[str(path)]=dict(size=stat.st_size,mtime_ns=stat.st_mtime_ns,id=key)
        return key

    def _read(self):
        try:state=read_json(self.path,self.empty)
        except (ValueError,OSError) as error:
            raise ValueError('Không đọc được lịch sử footage. Giữ file footage_usage.json và kiểm tra trước khi xuất tiếp.') from error
        if state.get('version')!=1:raise ValueError('Phiên bản lịch sử footage không được hỗ trợ.')
        return state

    def _clean(self,state):
        changed=False
        for key,reservation in list(state['reservations'].items()):
            if not process_alive(reservation['pid']):
                del state['reservations'][key];changed=True
        for key,video in list(state['inventory'].items()):
            try:valid=self._identity(video,state)==key
            except OSError:valid=False
            if not valid:del state['inventory'][key];changed=True
        return changed

    @staticmethod
    def _candidates(active, counts, used, avoid, last):
        unused = set(active) - used
        candidates = unused or set(active)
        fresh = candidates - set(avoid)
        candidates = fresh or candidates
        minimum = min(counts[key] for key in candidates)
        candidates = {key for key in candidates if counts[key] == minimum}
        return candidates - {last} or candidates

    @staticmethod
    def _avoid(state, requested, quote):
        previous = state.get('last_export', {})
        return set(requested) | (set(previous.get('ids', []))
                                 if quote and previous.get('quote') != quote else set())

    def preview(self,videos,count,preferred=None,avoid_ids=None,quote=''):
        with file_mutex(self.lock):
            state=self._read();changed=self._clean(state)
            incoming={}
            for video in videos:
                key=self._identity(video,state)
                incoming.setdefault(key,video)
            preferred_key=self._identity(preferred,state) if preferred else None
            if preferred:incoming[preferred_key]=preferred
            for key,video in incoming.items():
                if state['inventory'].get(key)!=video:
                    state['inventory'][key]=video;changed=True
            if changed:state['revision']+=1
            atomic_json(self.path,state)
            # Inventory is a durable metadata archive, NOT the active library.
            inventory=incoming
            if not inventory:raise ValueError('Kho footage trống.')
            ordered=sorted(inventory,key=lambda k:(not inventory[k].get('is_vertical',True),inventory[k]['name'].casefold(),inventory[k]['path']))
            effective={key:state['counts'].get(key,0) for key in ordered}
            last=state.get('last')
            for reservation in state['reservations'].values():
                for key in reservation['ids']:
                    if key in effective:effective[key]+=1
                if reservation['ids']:last=reservation['ids'][-1]
            minimum=min(effective.values())
            remaining=sum(v==minimum for v in effective.values())
            requested = sorted(set(avoid_ids or []))
            avoid = self._avoid(state, requested, quote)
            result=[];used=set();seen=set();fallback=[];repeated=[]
            for i in range(count):
                eligible=self._candidates(ordered,effective,used,avoid,last)
                key=preferred_key if i==0 and preferred_key in eligible else next(k for k in ordered if k in eligible)
                if key in avoid:fallback.append(i)
                if key in seen:repeated.append(i)
                if len(used)==len(ordered):used.clear()
                used.add(key);seen.add(key)
                result.append((key,inventory[key]));effective[key]+=1;last=key
            return result,dict(revision=state['revision'],total=len(ordered),remaining=remaining,
                               preferred_replaced=bool(preferred_key and result and result[0][0]!=preferred_key),
                               active_ids=ordered,avoid_ids=sorted(avoid),requested_avoid_ids=requested,
                               quote=quote,fallback_scenes=fallback,repeated_scenes=repeated)

    def _check_sequence(self,state,ids,active,avoid,include_reserved=False):
        if not active or any(key not in state['inventory'] for key in active):
            raise FootageConflict('Kho footage đã thay đổi. Hãy cập nhật kịch bản.')
        counts={key:state['counts'].get(key,0) for key in active}
        last=state.get('last');used=set()
        if include_reserved:
            for reservation in state['reservations'].values():
                for key in reservation['ids']:
                    if key in counts:counts[key]+=1
                if reservation['ids']:last=reservation['ids'][-1]
        for key in ids:
            if key not in self._candidates(active,counts,used,avoid,last):
                raise FootageConflict('Lượt dùng hoặc câu trước vừa thay đổi. Hãy cập nhật kịch bản chống lặp.')
            if len(used)==len(active):used.clear()
            used.add(key);counts[key]+=1;last=key

    def reserve(self,plan,job_id):
        with file_mutex(self.lock):
            state=self._read()
            if self._clean(state):state['revision']+=1;atomic_json(self.path,state)
            if state['revision']!=plan['footage_pool']['revision']:
                raise FootageConflict('Lịch sử footage vừa thay đổi. Hãy cập nhật kịch bản trước khi xuất.')
            ids=[s['footage_id'] for s in plan['scenes']]
            context=plan['footage_pool']
            active=context.get('active_ids',list(state['inventory']))
            requested=context.get('requested_avoid_ids',[])
            quote=context.get('quote','')
            avoid=self._avoid(state,requested,quote)
            self._check_sequence(state,ids,active,avoid,True)
            state['reservations'][job_id]=dict(ids=ids,pid=os.getpid(),created_at=time.time(),
                                               active_ids=active,requested_avoid_ids=requested,quote=quote)
            state['revision']+=1;atomic_json(self.path,state)

    def validate_export(self,job_id):
        with file_mutex(self.lock):
            state=self._read()
            reservation=state['reservations'].get(job_id)
            if not reservation:raise FootageConflict('Lượt footage đã hết hiệu lực. Hãy cập nhật kịch bản.')
            self._check_sequence(state,reservation['ids'],reservation.get('active_ids',list(state['inventory'])),
                                 self._avoid(state,reservation.get('requested_avoid_ids',[]),reservation.get('quote','')))

    def finish(self,job_id,success):
        with file_mutex(self.lock):
            state=self._read();reservation=state['reservations'].pop(job_id,None)
            if not reservation:return
            if success:
                for key in reservation['ids']:state['counts'][key]=state['counts'].get(key,0)+1
                state['last']=reservation['ids'][-1]
                state['last_export']=dict(quote=reservation.get('quote',''),ids=reservation['ids'])
            state['revision']+=1;atomic_json(self.path,state)
