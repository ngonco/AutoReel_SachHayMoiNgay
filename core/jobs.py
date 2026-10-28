"""Independent previews and tracked exports with persistent footage reservations."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import uuid
from core.planner import load_plan,build_plan
from core.renderer import render_plan
from core.footage_pool import FootagePool,FootageConflict
from core.persistence import file_mutex
from core.quote_downloads import QuoteDownloadHistory


class JobManager:
    def __init__(self, workspace_dir):
        self.workspace_dir=Path(workspace_dir)
        self.executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='reel-render')
        self.preview_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='reel-preview')
        self.preview_futures={};self.preview_clients={}
        self.lock=threading.RLock();self.jobs={};self.pending={}
        self.pool=FootagePool(workspace_dir)
        self.download_history=QuoteDownloadHistory(workspace_dir)

    def get(self,job_id):
        with self.lock:
            if job_id not in self.jobs:raise ValueError('Không tìm thấy tác vụ. Hãy thử lại.')
            return dict(self.jobs[job_id])

    def submit(self,plan,preview=False,output_path=None,preview_client=None):
        key=('preview' if preview else 'export',plan['plan_id'])
        with self.lock:
            if key in self.pending:return self.get(self.pending[key])
            if preview and preview_client:
                previous=self.preview_clients.get(preview_client)
                future=self.preview_futures.get(previous)
                if future and future.cancel():
                    old=self.jobs[previous]
                    old.update(status='error',code='preview_superseded',error='Bản xem trước cũ đã được thay bằng nội dung mới.',message='Đã bỏ bản xem trước cũ.')
                    self.pending.pop(('preview',old['plan_id']),None)
                    self.preview_futures.pop(previous,None)
            job_id=uuid.uuid4().hex
            target=Path(output_path) if output_path else (self.workspace_dir/'.cache'/'previews'/(plan['plan_id']+'.mp4') if preview else self.workspace_dir/'output_videos'/f'Reel_{job_id[:12]}.mp4')
            if not preview:self.pool.reserve(plan,job_id)
            self.jobs[job_id]=dict(job_id=job_id,status='queued',progress=0,message='Đang chuẩn bị xem…' if preview else 'Đang chờ dựng…',plan_id=plan['plan_id'],quote=plan.get('quote',''),kind='preview' if preview else 'export')
            if preview and target.is_file() and target.stat().st_size:
                load_plan(plan['plan_id'],self.workspace_dir)
                result=dict(success=True,duration=plan['duration'],plan_id=plan['plan_id'],elapsed=0,cached=True,
                            filename=target.name,url='/api/preview_video/'+target.name)
                self.jobs[job_id].update(status='done',progress=100,message='Đã sẵn sàng.',result=result)
                return self.get(job_id)
            self.pending[key]=job_id
            try:
                worker=self.preview_executor if preview else self.executor
                future=worker.submit(self._work,job_id,key,plan,target,preview)
                if preview:
                    self.preview_futures[job_id]=future
                    if preview_client:self.preview_clients[preview_client]=job_id
            except Exception:
                if not preview:self.pool.finish(job_id,False)
                self.pending.pop(key,None);raise
            return self.get(job_id)

    def _work(self,job_id,key,plan,target,preview):
        def progress(percent,message):
            with self.lock:self.jobs[job_id].update(progress=percent,message=message)
        with self.lock:self.jobs[job_id].update(status='running')
        try:
            load_plan(plan['plan_id'],self.workspace_dir)
            if preview:
                with file_mutex(target.with_suffix('.lock'),timeout=7200):
                    result=dict(success=True,duration=plan['duration'],plan_id=plan['plan_id'],elapsed=0,cached=True) if target.is_file() and target.stat().st_size else render_plan(plan,target,self.workspace_dir,True,progress)
            else:
                progress(0,'Đang chờ lượt xuất an toàn…')
                with file_mutex(self.workspace_dir/'reel_export.lock',timeout=7200):
                    self.pool.validate_export(job_id)
                    result=render_plan(plan,target,self.workspace_dir,False,progress)
                    self.pool.finish(job_id,True)
            result['filename']=target.name
            result['url']=('/api/preview_video/' if preview else '/api/rendered_video/')+target.name
            with self.lock:self.jobs[job_id].update(status='done',progress=100,message='Đã sẵn sàng.',result=result)
        except Exception as error:
            import logging
            logging.exception('Render failed')
            if not preview:self.pool.finish(job_id,False)
            with self.lock:self.jobs[job_id].update(status='error',error=str(error),code=getattr(error,'code',None),message=str(error))
        finally:
            with self.lock:
                self.pending.pop(key,None)
                self.preview_futures.pop(job_id,None)
                for client,latest in list(self.preview_clients.items()):
                    if latest==job_id:self.preview_clients.pop(client,None)

    def close(self):
        self.preview_executor.shutdown(wait=True)
        self.executor.shutdown(wait=True)

    def export_busy(self):
        with self.lock:
            return any(job['status'] in ('queued','running') and job.get('kind')!='preview' for job in self.jobs.values())

    def save_video(self, render_job_id, destination):
        source_job = self.get(render_job_id)
        if source_job.get('kind') != 'export' or source_job['status'] != 'done':
            raise ValueError('Cần video Full HD đã xuất thành công để tải.')
        result = source_job['result']
        filename = result['filename']
        source = self.workspace_dir / 'output_videos' / filename
        if Path(filename).name != filename or source.resolve().parent != (self.workspace_dir / 'output_videos').resolve() or not source.is_file():
            raise ValueError('Video xuất không còn tồn tại. Hãy xuất lại video.')
        job_id = uuid.uuid4().hex
        with self.lock:
            self.jobs[job_id] = dict(job_id=job_id,kind='save',status='queued',progress=0,message='Đang chờ lưu video…',plan_id=source_job['plan_id'],quote=source_job.get('quote',''))
            self.executor.submit(self._save_work, job_id, source, Path(destination))
        return self.get(job_id)

    def _save_work(self, job_id, source, destination):
        from core.downloads import copy_video
        def progress(percent, message):
            with self.lock:self.jobs[job_id].update(progress=percent,message=message)
        with self.lock:self.jobs[job_id]['status']='running'
        try:
            copy_video(source, destination, progress)
            warning=None
            try:self.download_history.record(self.jobs[job_id].get('quote',''),destination,job_id)
            except Exception as error:warning='Video đã lưu nhưng chưa ghi nhớ được trạng thái: '+str(error)
            with self.lock:self.jobs[job_id].update(status='done',progress=100,message=warning or 'Đã lưu video.',result=dict(success=True,saved_path=str(destination),filename=destination.name,history_warning=warning))
        except Exception as error:
            with self.lock:self.jobs[job_id].update(status='error',error=f'Không lưu được video: {error}',message='Lưu video thất bại. Bản Full HD vẫn được giữ trong ứng dụng.')

    def batch(self,items,detector=None):
        items=[{k:v for k,v in item.items() if k not in ('scene_video_preferences','imported_video_paths')} for item in items]
        if detector is None:
            from core.video_detector import VideoDetector
            detector=VideoDetector(self.workspace_dir)
        job_id=uuid.uuid4().hex
        with self.lock:self.jobs[job_id]=dict(job_id=job_id,status='queued',progress=0,total=len(items),message='Đang chờ xuất hàng loạt…')
        self.executor.submit(self._batch_work,job_id,items,detector)
        return self.get(job_id)

    def _batch_work(self,job_id,items,detector):
        files,failures=[],[];previous_music=''
        with self.lock:self.jobs[job_id]['status']='running'
        for i,item in enumerate(items):
            token=f'{job_id}_{i}'
            def report(value,message):
                with self.lock:self.jobs[job_id].update(progress=int((i+value/100)/len(items)*100),message=f'Reel {i+1}/{len(items)}: {message}')
            try:
                # Build each batch plan after the previous reel has committed its footage turns.
                payload={**item['settings'],'quote':item['quote'],'video_path':item['scenes'][0]['video_path']} if 'scenes' in item else item
                payload={**payload,'previous_music_path':previous_music}
                with file_mutex(self.workspace_dir/'reel_export.lock',timeout=7200):
                    for attempt in range(3):
                        plan=build_plan(payload,self.workspace_dir,detector)
                        try:
                            self.pool.reserve(plan,token);self.pool.validate_export(token)
                            break
                        except FootageConflict:
                            self.pool.finish(token,False)
                            if attempt==2:raise
                    target=self.workspace_dir/'output_videos'/f'Batch_{job_id[:8]}_Cau_{i+1:02d}.mp4'
                    render_plan(plan,target,self.workspace_dir,progress_callback=report)
                    self.pool.finish(token,True)
                    previous_music=(plan.get('music') or {}).get('path','')
                files.append(target.name)
            except Exception as error:
                self.pool.finish(token,False)
                failures.append(dict(index=i+1,error=str(error)))
        with self.lock:self.jobs[job_id].update(status='done',progress=100,result=dict(success=not failures,total_rendered=len(files),total_requested=len(items),files=files,failures=failures),message=f'Đã xuất {len(files)}/{len(items)} reel.')
