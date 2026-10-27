import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from core.downloads import SaveVideoService, suggested_filename, copy_video
from core.jobs import JobManager
from core.settings import load_settings, save_settings_patch


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manager = JobManager(self.root)
        self.service = SaveVideoService(self.root)

    def tearDown(self):
        self.manager.executor.shutdown(wait=True)
        self.temp.cleanup()

    def completed_export(self):
        folder = self.root / 'output_videos'
        folder.mkdir(exist_ok=True)
        source = folder / 'Reel_fixture.mp4'
        source.write_bytes(b'complete full HD fixture' * 100000)
        self.manager.jobs['export'] = dict(job_id='export', kind='export', status='done', plan_id='fixture', result=dict(filename=source.name))
        return source

    def wait(self, job):
        for _ in range(200):
            current = self.manager.get(job['job_id'])
            if current['status'] in ('done', 'error'):
                return current
            time.sleep(.01)
        self.fail('Save job timed out')

    def select(self, target):
        with patch('core.downloads.native_save_dialog', return_value=str(target)):
            return self.service.select('Hạnh phúc không phải đến từ xa.')

    def test_names_and_windows_sanitizing(self):
        cases = [
            ('Hạnh phúc không phải đến từ xa.', 'Hạnh phúc không phải đến.mp4'),
            ('Hạnh phúc\n\nkhông phải đến từ xa.', 'Hạnh phúc không phải đến.mp4'),
            ('Yêu thương.', 'Yêu thương.mp4'),
            ('  ', 'Reel.mp4'),
            ('<>:"/\\|?*', 'Reel.mp4'),
            ('CON', 'Reel CON.mp4'),
            ('Sống: tốt / mỗi ngày', 'Sống tốt  mỗi ngày.mp4'),
        ]
        for text, expected in cases:
            self.assertEqual(suggested_filename(text), expected)

    def test_cancel_and_missing_remembered_folder(self):
        save_settings_patch(self.root, dict(last_save_directory=str(self.root / 'gone'), quote='Giữ bản nháp'))
        with patch('core.downloads.native_save_dialog', return_value='') as dialog:
            self.assertTrue(self.service.select('Bình an')['cancelled'])
        self.assertEqual(dialog.call_args.args[0], self.root / 'output_videos')
        self.assertEqual(self.manager.jobs, {})
        self.assertFalse((self.root / 'footage_usage.json').exists())
        self.assertEqual(load_settings(self.root)['quote'], 'Giữ bản nháp')
        self.assertEqual(load_settings(self.root)['last_save_directory'], str(self.root / 'gone'))

    def test_remember_copy_retry_and_no_footage_changes(self):
        source = self.completed_export()
        target = self.root / 'chosen' / 'Hạnh phúc không phải đến.mp4'
        target.parent.mkdir()
        target.write_bytes(b'previous version')
        selection = self.select(target)
        service_after_restart = SaveVideoService(self.root)
        with patch('core.downloads.native_save_dialog', return_value='') as dialog:
            service_after_restart.select('Câu khác')
        self.assertEqual(dialog.call_args.args[0], target.parent)
        token = selection['save_token']
        job = self.wait(self.service.save(token, 'export', self.manager))
        self.assertEqual(job['status'], 'done')
        self.assertEqual(source.read_bytes(), target.read_bytes())
        self.assertEqual(self.service.save(token, 'export', self.manager)['job_id'], job['job_id'])
        self.assertFalse((self.root / 'footage_usage.json').exists())
        self.assertFalse(list(target.parent.glob('.reel-save-*')))

    def test_reject_unknown_token_preview_missing_and_failed_jobs(self):
        with self.assertRaises(ValueError):self.service.save('invalid', 'export', self.manager)
        token = self.select(self.root / 'saved.mp4')['save_token']
        source = self.completed_export()
        for kind, status in [('preview', 'done'), ('export', 'error'), ('export', 'running')]:
            self.manager.jobs['export'].update(kind=kind, status=status)
            with self.assertRaises(ValueError):self.service.save(token, 'export', self.manager)
        self.manager.jobs['export'].update(kind='export', status='done')
        source.unlink()
        with self.assertRaises(ValueError):self.service.save(token, 'export', self.manager)

    def test_copy_failure_preserves_existing_destination_and_allows_retry(self):
        source = self.completed_export()
        target = self.root / 'saved.mp4'
        target.write_bytes(b'keep old file')
        token = self.select(target)['save_token']
        with patch('core.downloads.os.replace', side_effect=PermissionError('Access denied')):
            job = self.wait(self.service.save(token, 'export', self.manager))
        self.assertEqual(job['status'], 'error')
        self.assertEqual(target.read_bytes(), b'keep old file')
        self.assertTrue(source.exists())
        self.assertFalse(list(self.root.glob('.reel-save-*')))
        self.assertEqual(self.wait(self.service.save(token, 'export', self.manager))['status'], 'done')

    def test_directory_setting_does_not_change_render_plan(self):
        from core.planner import build_plan
        source = self.root / 'clip.mp4'
        source.write_bytes(b'clip')
        class Detector:
            def scan_all_videos(self):
                return [dict(path=str(source), name=source.name, is_vertical=True, recommended_pos='bottom')]
        with patch('core.planner.probe', return_value=dict(width=1080, height=1920, duration=3)):
            a = build_plan(dict(quote='Bình an',last_save_directory='D:/one'), self.root, Detector())
            b = build_plan(dict(quote='Bình an',last_save_directory='E:/two'), self.root, Detector())
        self.assertEqual(a['plan_id'], b['plan_id'])
        self.assertNotIn('last_save_directory', a['settings'])
