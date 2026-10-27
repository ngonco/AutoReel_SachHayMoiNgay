"""A single render worker keeps memory bounded and exposes thread-safe job state."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import uuid
from core.planner import load_plan
from core.renderer import render_plan


class JobManager:
    def __init__(self, workspace_dir):
        self.workspace_dir = Path(workspace_dir)
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='reel-render')
        self.lock = threading.RLock()
        self.jobs = {}
        self.pending = {}

    def get(self, job_id):
        with self.lock:
            if job_id not in self.jobs:
                raise ValueError('Không tìm thấy tác vụ. Hãy thử lại.')
            return dict(self.jobs[job_id])

    def submit(self, plan, preview=False, output_path=None):
        key = ('preview' if preview else 'export', plan['plan_id'])
        with self.lock:
            if key in self.pending:
                return self.get(self.pending[key])
            job_id = uuid.uuid4().hex
            target = Path(output_path) if output_path else (self.workspace_dir / '.cache' / 'previews' / (plan['plan_id'] + '.mp4') if preview else self.workspace_dir / 'output_videos' / f'Reel_{job_id[:12]}.mp4')
            self.jobs[job_id] = dict(job_id=job_id, status='queued', progress=0, message='Đang chờ dựng…', plan_id=plan['plan_id'])
            self.pending[key] = job_id
            self.executor.submit(self._work, job_id, key, plan, target, preview)
            return self.get(job_id)

    def _work(self, job_id, key, plan, target, preview):
        def progress(percent, message):
            with self.lock:
                self.jobs[job_id].update(progress=percent, message=message)
        with self.lock:
            self.jobs[job_id].update(status='running')
        try:
            load_plan(plan['plan_id'], self.workspace_dir)
            if preview and target.is_file():
                result = dict(success=True, duration=plan['duration'], plan_id=plan['plan_id'], elapsed=0, cached=True)
            else:
                result = render_plan(plan, target, self.workspace_dir, preview, progress)
            result['filename'] = target.name
            result['url'] = ('/api/preview_video/' if preview else '/api/rendered_video/') + target.name
            with self.lock:
                self.jobs[job_id].update(status='done', progress=100, message='Đã sẵn sàng.', result=result)
        except Exception as error:
            import logging
            logging.exception('Render failed')
            with self.lock:
                self.jobs[job_id].update(status='error', error=str(error), message=str(error))
        finally:
            with self.lock:
                self.pending.pop(key, None)

    def batch(self, plans):
        job_id = uuid.uuid4().hex
        with self.lock:
            self.jobs[job_id] = dict(job_id=job_id, status='queued', progress=0, message='Đang chờ xuất hàng loạt…')
        self.executor.submit(self._batch_work, job_id, plans)
        return self.get(job_id)

    def _batch_work(self, job_id, plans):
        files, failures = [], []
        with self.lock:
            self.jobs[job_id]['status'] = 'running'
        for i, plan in enumerate(plans):
            def report(value, message):
                with self.lock:
                    self.jobs[job_id].update(progress=int((i + value / 100) / len(plans) * 100), message=f'Reel {i + 1}/{len(plans)}: {message}')
            try:
                target = self.workspace_dir / 'output_videos' / f'Batch_{job_id[:8]}_Cau_{i + 1:02d}.mp4'
                render_plan(plan, target, self.workspace_dir, progress_callback=report)
                files.append(target.name)
            except Exception as error:
                failures.append(dict(index=i + 1, error=str(error)))
        with self.lock:
            self.jobs[job_id].update(status='done', progress=100, result=dict(success=not failures, total_rendered=len(files), files=files, failures=failures), message=f'Đã xuất {len(files)}/{len(plans)} reel.')
