"""Durable per-Reel drafts and cross-process batch ownership."""
import copy
import os
import uuid
from pathlib import Path
from core.persistence import file_mutex, read_json, atomic_json
from core.settings import normalize_settings
from core.footage_pool import process_alive

class ExportQueue:
    def __init__(self, workspace):
        self.path=Path(workspace)/'export_queue.json'
        self.lock=self.path.with_suffix('.lock')

    def _read(self):
        data=read_json(self.path,lambda:dict(version=1,items=[]))
        if data.get('version')!=1 or not isinstance(data.get('items'),list):
            raise ValueError('Danh sách xuất không hợp lệ. Hãy giữ file export_queue.json để kiểm tra.')
        changed=False
        for item in data['items']:
            if item['status'] in ('queued','running') and (not item.get('pid') or not process_alive(item['pid'])):
                item.update(status='error',error='Lượt xuất bị gián đoạn. Bấm xuất để thử lại.');changed=True
        if changed:atomic_json(self.path,data)
        return data

    def snapshot(self):
        with file_mutex(self.lock):return copy.deepcopy(self._read())

    def change(self, body):
        with file_mutex(self.lock):
            data=self._read();items=data['items'];action=body.get('action','add')
            item=next((i for i in items if i['id']==body.get('id')),None)
            if action!='add' and item is None:raise ValueError('Không tìm thấy Reel trong danh sách.')
            if item and item['status'] in ('queued','running'):raise ValueError('Reel đang trong lượt xuất, chưa thể sửa.')
            if action in ('add','update'):
                payload=normalize_settings(body.get('payload'))
                if not (payload.get('quote') or '').strip():raise ValueError('Hãy nhập nội dung Reel.')
                if action=='add':
                    item=dict(id=uuid.uuid4().hex,status='pending',payload=payload);items.append(item)
                elif item['payload']!=payload:item.update(payload=payload,status='pending',error=None,result=None)
            elif action=='delete':items.remove(item)
            elif action=='move':
                index=items.index(item);dest=max(0,min(len(items)-1,index+int(body.get('direction',0))))
                items.insert(dest,items.pop(index))
            else:raise ValueError('Thao tác danh sách không hợp lệ.')
            atomic_json(self.path,data)
            return dict(**copy.deepcopy(data),selected_id=item['id'])

    def claim(self, job_id):
        with file_mutex(self.lock):
            data=self._read()
            if any(i['status'] in ('queued','running') for i in data['items']):raise ValueError('Danh sách đang được xuất ở một phiên khác.')
            items=[i for i in data['items'] if i['status'] in ('pending','error')]
            if not items:raise ValueError('Danh sách chưa có Reel chờ xuất.')
            for item in items:item.update(status='queued',job_id=job_id,pid=os.getpid(),error=None)
            atomic_json(self.path,data)
            return [dict(**copy.deepcopy(i['payload']),_queue_id=i['id']) for i in items]

    def progress(self, item_id, job_id, status, **fields):
        with file_mutex(self.lock):
            data=self._read()
            item=next(i for i in data['items'] if i['id']==item_id)
            if item.get('job_id')!=job_id:raise ValueError('Lượt xuất đã thay đổi.')
            item.update(status=status,**fields);atomic_json(self.path,data)

class FootagePreferences:
    def __init__(self,workspace):
        self.path=Path(workspace)/'footage_browser.json';self.lock=self.path.with_suffix('.lock')
    def get(self):
        with file_mutex(self.lock):return read_json(self.path,lambda:dict(expanded=True,size=120,filter='all',scroll=0,search=''))
    def save(self,body):
        with file_mutex(self.lock):
            value=dict(expanded=bool(body.get('expanded',True)),size=max(80,min(200,int(body.get('size',120)))),
                       filter='suitable' if body.get('filter')=='suitable' else 'all',scroll=max(0,int(body.get('scroll',0))),search=str(body.get('search',''))[:200])
            atomic_json(self.path,value);return value
