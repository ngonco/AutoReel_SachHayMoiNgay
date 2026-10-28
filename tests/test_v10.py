import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from core.draft_media import DraftMediaService, source_key
from core.planner import build_plan, fingerprint
from core.settings import save_settings_patch, load_settings, normalize_settings
from core.footage_pool import FootagePool
from core.video_detector import VideoDetector
from core.jobs import JobManager
from core.renderer import overlay_key


class FakeDetector:
    def __init__(self, root):
        self.videos=[]
        for i in range(4):
            path=Path(root)/f'{i}.mp4';path.write_bytes(f'video-{i}'.encode())
            self.videos.append(dict(path=str(path.resolve()),name=path.name,is_vertical=True,recommended_pos='bottom',thumb_url='/thumb.jpg'))
    def scan_all_videos(self, directory=None):return self.videos.copy()
    def analyze_video(self,path):return dict(path=str(Path(path).resolve()),name=Path(path).name,recommended_pos='bottom')


class PreferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.detector=FakeDetector(self.root)
        self.probe=patch('core.planner.probe',return_value=dict(duration=10,width=360,height=640,is_vertical=True));self.probe.start()
    def tearDown(self):self.probe.stop();self.temp.cleanup()
    def plan(self,**values):return build_plan(dict(quote='Câu thứ nhất.\nCâu thứ hai.',duration=1,**values),self.root,self.detector)
    def test_each_scene_preference_and_export_validation(self):
        preferred=self.detector.videos[3]['path']
        plan=self.plan(scene_video_preferences={'1':dict(path=preferred,text='Câu thứ hai.')})
        self.assertEqual(plan['scenes'][1]['video_path'],preferred)
        self.assertTrue(plan['scenes'][1]['suggestion']['accepted'])
        pool=FootagePool(self.root);pool.reserve(plan,'owned');pool.validate_export('owned');pool.finish('owned',True)
        history=json.loads((self.root/'footage_usage.json').read_text())
        self.assertEqual(sum(history['counts'].values()),2)
    def test_preference_cannot_override_usage_or_previous_or_repeat(self):
        first=self.plan();pool=FootagePool(self.root)
        state=pool._read();key=first['scenes'][1]['footage_id'];state['counts'][key]=20
        from core.persistence import atomic_json
        atomic_json(pool.path,state)
        preferred=first['scenes'][1]['video_path']
        plan=self.plan(scene_video_preferences={'1':dict(path=preferred,text='Câu thứ hai.')})
        self.assertNotEqual(plan['scenes'][1]['video_path'],preferred)
        self.assertIn('ít lượt',plan['scenes'][1]['suggestion']['reason'])
        avoided=self.plan(previous_footage_ids=[first['scenes'][0]['footage_id']])
        self.assertNotIn(first['scenes'][0]['footage_id'],[s['footage_id'] for s in avoided['scenes']])
        repeated=self.plan(scene_video_preferences={'1':dict(path=first['scenes'][0]['video_path'],text='Câu thứ hai.')})
        self.assertNotEqual(repeated['scenes'][0]['footage_id'],repeated['scenes'][1]['footage_id'])
    def test_stale_text_imports_autosave_and_overlay_reuse(self):
        target=self.detector.videos[3]['path']
        stale=self.plan(scene_video_preferences={'1':dict(path=target,text='Nội dung cũ')})
        self.assertNotEqual(stale['scenes'][1]['video_path'],target)
        p=self.plan();other=self.plan(scene_video_preferences={'1':dict(path=target,text='Câu thứ hai.')})
        self.assertEqual(p['scenes'][1]['overlay_key'],other['scenes'][1]['overlay_key'])
        self.assertNotEqual(p['plan_id'],other['plan_id'])
        save_settings_patch(self.root,dict(scene_video_preferences={'1':dict(path=target,text='Câu thứ hai.')},imported_video_paths=[target]))
        restored=load_settings(self.root);self.assertEqual(restored['scene_video_preferences']['1']['path'],target)
        self.assertEqual(restored['imported_video_paths'],[target])
    def test_batch_strips_draft_preferences(self):
        manager=JobManager(self.root)
        try:
            with patch.object(manager.executor,'submit') as submit:
                manager.batch([dict(quote='A',scene_video_preferences={'0':{}},imported_video_paths=['x'])],self.detector)
                item=submit.call_args.args[2][0]
                self.assertNotIn('scene_video_preferences',item);self.assertNotIn('imported_video_paths',item)
        finally:manager.close()
    def test_invalid_preference_shape_rejected(self):
        for value in [[],{'x':{}},{'1000':{}},{'1':'path'}]:
            with self.assertRaises(ValueError):normalize_settings(dict(scene_video_preferences=value))


class DraftCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.detector=FakeDetector(self.root)
        self.paused=True;self.service=DraftMediaService(self.root,lambda:self.paused)
    def tearDown(self):self.service.close();self.temp.cleanup()
    def plan(self):return dict(scenes=[dict(source=fingerprint(v['path'])) for v in self.detector.videos])
    def test_priority_folder_switch_and_export_pause(self):
        self.service.set_library(self.detector.videos)
        plan=self.plan();self.service.prepare(plan,2)
        keys=[source_key(s['source']) for s in plan['scenes']]
        self.assertEqual(self.service.pending[0],keys[2])
        time.sleep(.1);self.assertIsNone(self.service.active)
        self.service.set_library([self.detector.videos[1]])
        self.assertEqual(self.service.pending,[keys[1]])
    def test_cache_restart_source_invalidation_and_authorization(self):
        plan=self.plan();snapshot=self.service.prepare(plan)
        key=snapshot['scenes'][0]['key'];target=self.service.folder/(key+'.mp4');target.write_bytes(b'cache')
        ready=self.service.status(plan);self.assertEqual(ready['scenes'][0]['status'],'ready')
        self.assertEqual(self.service.media_path(key+'.mp4'),target)
        with self.assertRaises(ValueError):self.service.media_path('../session_state.json')
        with self.assertRaises(ValueError):self.service.media_path('f'*32+'.mp4')
        self.service.close();self.service=DraftMediaService(self.root,lambda:True)
        self.service.set_library(self.detector.videos)
        self.assertEqual(self.service.status(plan)['scenes'][0]['status'],'ready')
        Path(plan['scenes'][0]['source']['path']).write_bytes(b'changed-longer')
        with self.assertRaises(ValueError):self.service.media_path(key+'.mp4')
    def test_failure_does_not_consume_history_and_retry_is_explicit(self):
        self.service.set_library(self.detector.videos[:1]);plan=dict(scenes=self.plan()['scenes'][:1])
        with patch.object(self.service,'_convert',side_effect=ValueError('bad clip')) as convert:
            self.service.prepare(plan);self.paused=False
            deadline=time.monotonic()+3
            while time.monotonic()<deadline and self.service.status(plan)['scenes'][0]['status']!='error':time.sleep(.02)
            self.assertEqual(self.service.status(plan)['scenes'][0]['status'],'error');self.assertEqual(convert.call_count,1)
        self.assertFalse((self.root/'footage_usage.json').exists())
        self.paused=True;self.service.prepare(plan);self.assertEqual(self.service.status(plan)['scenes'][0]['status'],'queued')


if __name__=='__main__':unittest.main()
