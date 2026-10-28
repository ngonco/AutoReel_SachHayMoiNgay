"""Preview latency: one-pass rendering, its own worker, instant cache and stale queue removal."""
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from PIL import Image
from core.renderer import render_plan, PREVIEW_SIZE
from core.jobs import JobManager


def plan(count=3,identity='a'):
    scenes=[]
    for index in range(count):
        scenes.append(dict(video_path='fixture.mp4',source_start=.5,source_end=2.,speed=.375,
                           start=index*4,end=(index+1)*4,text_start=index*4,text_end=(index+1)*4,
                           resolved_pos='bottom',text='Bình an.'))
    return dict(plan_id=identity*24,duration=count*4,music=None,settings=dict(music_volume=0),scenes=scenes)


class RenderPreviewTests(unittest.TestCase):
    def execute(self,preview,count):
        calls=[];p=plan(count)
        with tempfile.TemporaryDirectory() as temp:
            def encoded(command):calls.append(command);Path(command[-1]).write_bytes(b'encoded fixture')
            with patch('core.planner.load_plan',return_value=p),patch('core.renderer._execute',side_effect=encoded),\
                 patch('core.renderer.scene_overlay',return_value=Image.new('RGBA',(1080,1920))):
                render_plan(p,Path(temp)/'result.mp4',temp,preview=preview)
        return calls

    def test_up_to_four_scenes_use_one_preview_encode_with_same_timeline(self):
        calls=self.execute(True,3)
        self.assertEqual(len(calls),1)
        command=calls[0];graph=command[command.index('-filter_complex')+1]
        self.assertEqual(PREVIEW_SIZE,(360,640))
        self.assertIn('scale=360:640',graph)
        self.assertIn('xfade=transition=fade:duration=0.4:offset=4',graph)
        self.assertIn('st=4:d=0.2',graph)
        self.assertEqual(command[command.index('-preset')+1],'ultrafast')
        self.assertEqual(command[command.index('-ss')+1],'0.5')

    def test_fullhd_keeps_export_quality_and_many_scenes_bound_preview_decoders(self):
        full=self.execute(False,2)
        self.assertEqual(len(full),3)
        self.assertIn('scale=1080:1920',full[0][full[0].index('-vf')+1])
        self.assertEqual(full[-1][full[-1].index('-preset')+1],'veryfast')
        self.assertEqual(full[-1][full[-1].index('-crf')+1],'19')
        self.assertEqual(len(self.execute(True,5)),6)


class PreviewQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.manager=JobManager(self.root)

    def tearDown(self):self.manager.close();self.temp.cleanup()

    def wait(self,job):
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            current=self.manager.get(job['job_id'])
            if current['status'] in ('done','error'):return current
            threading.Event().wait(.01)
        self.fail('Preview blocked behind another queue')

    def test_preview_does_not_wait_for_export_queue_or_consume_footage(self):
        release=threading.Event();entered=threading.Event()
        def blocking():entered.set();release.wait(5)
        self.manager.executor.submit(blocking);self.assertTrue(entered.wait(1))
        def rendered(p,target,*args):Path(target).parent.mkdir(parents=True,exist_ok=True);Path(target).write_bytes(b'preview');return dict(success=True)
        try:
            with patch('core.jobs.load_plan',side_effect=lambda key,root:plan(identity=key[0])),\
                 patch('core.jobs.render_plan',side_effect=rendered),patch.object(self.manager.pool,'reserve') as reserved:
                self.assertEqual(self.wait(self.manager.submit(plan(),preview=True))['status'],'done')
                reserved.assert_not_called()
            self.assertFalse((self.root/'footage_usage.json').exists())
        finally:release.set()

    def test_cached_preview_returns_done_even_with_preview_worker_busy(self):
        release=threading.Event();self.manager.preview_executor.submit(lambda:release.wait(5))
        target=self.root/'.cache'/'previews'/('a'*24+'.mp4');target.parent.mkdir(parents=True);target.write_bytes(b'cached')
        try:
            with patch('core.jobs.load_plan',return_value=plan()),patch('core.jobs.render_plan') as render:
                job=self.manager.submit(plan(),preview=True)
                self.assertEqual(job['status'],'done');self.assertTrue(job['result']['cached']);render.assert_not_called()
        finally:release.set()

    def test_new_client_plan_drops_obsolete_queued_preview_and_deduplicates_current(self):
        release=threading.Event();self.manager.preview_executor.submit(lambda:release.wait(5))
        try:
            with patch('core.jobs.load_plan',return_value=plan(identity='b')),patch('core.jobs.render_plan',return_value=dict(success=True)):
                old=self.manager.submit(plan(identity='a'),preview=True,preview_client='page')
                new=self.manager.submit(plan(identity='b'),preview=True,preview_client='page')
                self.assertEqual(self.manager.get(old['job_id'])['code'],'preview_superseded')
                self.assertEqual(self.manager.submit(plan(identity='b'),preview=True,preview_client='page')['job_id'],new['job_id'])
                release.set();self.assertEqual(self.wait(new)['status'],'done')
        finally:release.set()


if __name__=='__main__':unittest.main()
