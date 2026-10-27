from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from core.footage_pool import FootagePool,FootageConflict
from core.settings import save_settings_patch,load_settings


class DraftTests(unittest.TestCase):
    def test_old_app_settings_cannot_overwrite_new_autosave(self):
        with tempfile.TemporaryDirectory() as temp:
            old=Path(temp)/'settings.json'
            old.write_text(json.dumps(dict(quote_size=80,vertical_offset=300)),encoding='utf-8')
            self.assertEqual(load_settings(temp)['quote_size'],80)
            save_settings_patch(temp,dict(quote='Dòng 1.\nDòng 2.',outline_width=7))
            old.write_text(json.dumps(dict(quote_size=42,outline_width=4)),encoding='utf-8')
            self.assertEqual(load_settings(temp)['quote_size'],80)
            self.assertEqual(load_settings(temp)['outline_width'],7)
            self.assertEqual(load_settings(temp)['quote'],'Dòng 1.\nDòng 2.')

    def test_exact_multiline_draft_and_partial_settings_survive(self):
        with tempfile.TemporaryDirectory() as temp:
            quote='  Dòng thứ nhất.\n\nDòng thứ hai.\n'
            save_settings_patch(temp,dict(quote=quote,video_path='D:/nguon.mov',outline_width=9,safe_zone=True))
            saved=save_settings_patch(temp,dict(verticalOffset=-900))
            self.assertEqual(saved['quote'],quote)
            self.assertEqual(saved['video_path'],'D:/nguon.mov')
            self.assertEqual(saved['outline_width'],9)
            self.assertEqual(saved['vertical_offset'],-900)
            self.assertTrue(saved['safe_zone'])
            save_settings_patch(temp,dict(quote=''))
            self.assertEqual(save_settings_patch(temp,dict(credit='Nguồn'))['quote'],'')

    def test_late_save_cannot_overwrite_newer_input(self):
        with tempfile.TemporaryDirectory() as temp:
            def save(seq,text):return save_settings_patch(temp,{'_client_id':'tab-1','_sequence':seq,'_patch':{'quote':text}})
            save(2,'Bản mới.\nGiữ xuống dòng.')
            self.assertEqual(save(1,'Bản cũ')['quote'],'Bản mới.\nGiữ xuống dòng.')
            saved=save_settings_patch(temp,{'_client_id':'tab-2','_sequence':1,'_patch':{'outline_width':7}})
            self.assertEqual(saved['quote'],'Bản mới.\nGiữ xuống dòng.')
            self.assertEqual(saved['outline_width'],7)

    def test_concurrent_partial_saves_merge_without_resetting_other_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            fields=[dict(quote='Câu một.\nCâu hai.'),dict(credit='Nguồn mới'),dict(outline_blur=19),dict(safe_zone=True)]
            with ThreadPoolExecutor(max_workers=4) as executor:list(executor.map(lambda p:save_settings_patch(temp,p),fields))
            result=save_settings_patch(temp,{})
            for item in fields:
                for key,value in item.items():self.assertEqual(result[key],value)


class FootageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.videos=[]
        for i in range(3):
            path=self.root/f'{i}.mp4';path.write_bytes(b'fixture'+str(i).encode())
            self.videos.append(dict(name=path.name,path=str(path),is_vertical=True,recommended_pos='bottom'))
        self.pool=FootagePool(self.root)

    def tearDown(self):self.temp.cleanup()

    def plan(self,count=1,preferred=None):
        allocations,summary=self.pool.preview(self.videos,count,preferred or self.videos[0])
        return dict(footage_pool=summary,scenes=[dict(footage_id=key) for key,_ in allocations])

    def test_preview_is_free_and_cycles_use_every_clip_before_repeating(self):
        first=self.plan();self.assertEqual(first,self.plan())
        state=json.loads((self.root/'footage_usage.json').read_text(encoding='utf-8'))
        self.assertEqual(state['counts'],{})
        sequence=[]
        for i in range(7):
            plan=self.plan();key=plan['scenes'][0]['footage_id'];sequence.append(key)
            self.pool.reserve(plan,str(i));self.pool.validate_export(str(i));self.pool.finish(str(i),True)
        self.assertEqual(len(set(sequence[:3])),3)
        self.assertEqual(len(set(sequence[3:6])),3)
        self.assertEqual(sequence[0],sequence[6])
        other=FootagePool(self.root)
        _,summary=other.preview(self.videos,1,self.videos[0])
        self.assertEqual(summary['remaining'],2)

    def test_scene_count_larger_than_library_only_repeats_after_full_cycle(self):
        ids=[s['footage_id'] for s in self.plan(8)['scenes']]
        self.assertEqual(len(set(ids[:3])),3)
        self.assertEqual(len(set(ids[3:6])),3)
        self.assertEqual(ids[0],ids[3])

    def test_duplicate_video_content_is_one_footage_even_with_different_filename(self):
        copy=self.root/'copied_name.mp4';copy.write_bytes(Path(self.videos[0]['path']).read_bytes())
        duplicate={**self.videos[0],'name':copy.name,'path':str(copy)}
        allocation,summary=self.pool.preview(self.videos+[duplicate],4,duplicate)
        self.assertEqual(summary['total'],3)
        self.assertEqual(len({key for key,_ in allocation[:3]}),3)
        self.assertIn(allocation[3][0],{key for key,_ in allocation[:3]})

    def test_reservations_prevent_queued_duplicates_and_failures_return_turns(self):
        old=self.plan();self.pool.reserve(old,'one')
        with self.assertRaises(FootageConflict):self.pool.reserve(old,'stale')
        second=self.plan()
        self.assertNotEqual(old['scenes'][0]['footage_id'],second['scenes'][0]['footage_id'])
        self.pool.reserve(second,'two')
        self.pool.finish('one',False)
        self.pool.validate_export('two');self.pool.finish('two',True)
        self.assertEqual(self.plan()['scenes'][0]['footage_id'],old['scenes'][0]['footage_id'])

    def test_concurrent_submission_uses_distinct_first_cycle_sources(self):
        def reserve_one(i):
            for retry in range(20):
                plan=self.plan()
                try:self.pool.reserve(plan,str(i));return plan['scenes'][0]['footage_id']
                except FootageConflict:continue
            raise AssertionError('Reservation retry exhausted')
        with ThreadPoolExecutor(max_workers=3) as executor:ids=list(executor.map(reserve_one,range(3)))
        self.assertEqual(len(set(ids)),3)
        for i in range(3):self.pool.finish(str(i),False)

    def test_dead_process_reservation_is_released(self):
        plan=self.plan();self.pool.reserve(plan,'crashed')
        with patch('core.footage_pool.process_alive',return_value=False):new=self.plan()
        self.assertEqual(new['scenes'][0]['footage_id'],plan['scenes'][0]['footage_id'])


class JobFootageTests(unittest.TestCase):
    def test_failed_render_returns_reserved_footage(self):
        from core.jobs import JobManager
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'one.mp4';path.write_bytes(b'fixture-one')
            pool=FootagePool(temp)
            allocation,summary=pool.preview([dict(name=path.name,path=str(path),is_vertical=True)],1)
            plan=dict(plan_id='a'*24,footage_pool=summary,scenes=[dict(footage_id=allocation[0][0])])
            manager=JobManager(temp)
            with patch('core.jobs.load_plan',return_value=plan),patch('core.jobs.render_plan',side_effect=RuntimeError('test render failed')),self.assertLogs(level='ERROR'):
                job=manager.submit(plan)
                manager.executor.shutdown(wait=True)
            self.assertEqual(manager.get(job['job_id'])['status'],'error')
            state=json.loads((Path(temp)/'footage_usage.json').read_text(encoding='utf-8'))
            self.assertEqual(state['counts'],{})
            self.assertEqual(state['reservations'],{})

    def test_batch_plans_use_history_from_each_completed_reel(self):
        from core.jobs import JobManager
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);videos=[]
            for i in range(3):
                path=root/f'{i}.mp4';path.write_bytes(f'fixture-{i}'.encode())
                videos.append(dict(name=path.name,path=str(path),is_vertical=True,recommended_pos='bottom'))
            class Detector:
                def scan_all_videos(self):return videos
            sequence=[]
            def rendered(plan,*args,**kwargs):
                sequence.extend(s['footage_id'] for s in plan['scenes'])
                return dict(success=True)
            manager=JobManager(root)
            with patch('core.planner.probe',return_value=dict(width=1080,height=1920,duration=2,is_vertical=True)),patch('core.jobs.render_plan',side_effect=rendered):
                job=manager.batch([dict(quote='Bình an.',video_path=videos[0]['path']) for _ in range(4)],Detector())
                manager.executor.shutdown(wait=True)
            self.assertEqual(manager.get(job['job_id'])['result']['total_rendered'],4)
            self.assertEqual(len(set(sequence[:3])),3)
            self.assertIn(sequence[3],sequence[:3])

if __name__=='__main__':unittest.main()
