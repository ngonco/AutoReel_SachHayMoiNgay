"""Persistent successful user downloads, independent of footage turns and batch exports."""
import hashlib
import time
import unicodedata
from pathlib import Path
from core.persistence import read_json, atomic_json, file_mutex


def quote_key(text):
    normalized=' '.join(unicodedata.normalize('NFC',str(text)).split())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


class QuoteDownloadHistory:
    def __init__(self, workspace):
        self.path=Path(workspace)/'quote_download_history.json'
        self.lock=self.path.with_suffix('.lock')
        self.recovery=Path(workspace)/'draft_recovery.json'

    def _read(self):
        data=read_json(self.path,lambda:dict(version=1,revision=0,quotes={}))
        if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('quotes'),dict):
            raise ValueError('Không đọc được lịch sử câu đã tải. File cũ được giữ nguyên để khôi phục.')
        for key,value in data['quotes'].items():
            if not isinstance(value,dict) or not isinstance(value.get('quote'),str) or quote_key(value['quote'])!=key:
                raise ValueError('Lịch sử câu đã tải không hợp lệ; không tự đặt lại dữ liệu.')
        return data

    def record(self, quote, saved_path, job_id):
        if not str(quote).strip():return
        with file_mutex(self.lock):
            data=self._read();key=quote_key(quote);previous=data['quotes'].get(key,{})
            if previous.get('last_job_id')==job_id:return
            data['quotes'][key]=dict(quote=quote,count=previous.get('count',0)+1,
                                    first_downloaded_at=previous.get('first_downloaded_at',time.time()),
                                    last_downloaded_at=time.time(),last_path=str(saved_path),last_job_id=job_id)
            data['revision']+=1;atomic_json(self.path,data)

    def snapshot(self):
        with file_mutex(self.lock):
            data=self._read()
            return dict(revision=data['revision'],records=[{k:v for k,v in value.items() if k not in ('last_path','last_job_id')}
                                                          for value in data['quotes'].values()])

    def annotate(self, catalog):
        history=self.snapshot();records={quote_key(item['quote']):item for item in history['records']}
        quotes=[]
        for quote in catalog['quotes']:
            record=records.get(quote_key(quote['quote']))
            quotes.append({**quote,'downloaded':bool(record),'last_downloaded_at':record['last_downloaded_at'] if record else None})
        return {**catalog,'quotes':quotes,'download_history':history,
                'sync':{**catalog['sync'],'download_revision':history['revision']}}

    def startup(self, catalog, settings):
        catalog=self.annotate(catalog)
        index=next((i for i,q in enumerate(catalog['quotes']) if not q['downloaded']),None)
        all_downloaded=bool(catalog['quotes']) and index is None
        if index is None:index=0 if catalog['quotes'] else -1
        target=catalog['quotes'][index]['quote'] if index>=0 else settings.get('quote')
        if settings.get('quote') is not None and (quote_key(settings['quote'])!=quote_key(target or '') or settings.get('scene_video_preferences')):
            with file_mutex(self.recovery.with_suffix('.lock')):
                # Keep the exact draft/settings before startup selects a different Sheet item.
                atomic_json(self.recovery,dict(version=1,saved_at=time.time(),settings=settings))
        return dict(catalog=catalog,index=index,all_downloaded=all_downloaded,recovery_available=self.recovery.is_file())

    def previous_draft(self):
        with file_mutex(self.recovery.with_suffix('.lock')):
            data=read_json(self.recovery,dict)
            if data.get('version')!=1 or not isinstance(data.get('settings'),dict):
                raise ValueError('Chưa có bản nháp trước để mở lại.')
            return data
