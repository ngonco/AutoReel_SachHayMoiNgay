import tempfile
import unittest
from unittest.mock import patch
from core.export_queue import ExportQueue, FootagePreferences
from core.persistence import atomic_json

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.queue=ExportQueue(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def add(self,quote='A'):
        return self.queue.change(dict(action='add',payload=dict(quote=quote,music_mode='none')))['selected_id']
    def test_latest_order_lock_done_and_retry(self):
        a=self.add();b=self.add('B')
        self.queue.change(dict(action='update',id=a,payload=dict(quote='Latest',scene_video_preferences={'0':dict(path='manual.mp4',text='Latest')},imported_video_paths=['manual.mp4'])))
        self.queue.change(dict(action='move',id=b,direction=-1))
        claimed=self.queue.claim('job')
        self.assertEqual([i['quote'] for i in claimed],['B','Latest'])
        self.assertEqual(claimed[1]['scene_video_preferences']['0']['path'],'manual.mp4')
        for action in ('update','delete','move'):
            with self.assertRaises(ValueError):self.queue.change(dict(action=action,id=a,payload=dict(quote='X')))
        with self.assertRaises(ValueError):self.queue.claim('other')
        self.queue.progress(b,'job','done',result=dict(filename='a.mp4'))
        self.queue.progress(a,'job','error',error='missing')
        self.assertEqual([i['_queue_id'] for i in self.queue.claim('retry')],[a])
        self.queue.progress(a,'retry','done')
        with self.assertRaises(ValueError):self.queue.claim('empty')
        self.queue.change(dict(action='update',id=b,payload=dict(quote='Changed')))
        self.assertEqual(self.queue.snapshot()['items'][0]['status'],'pending')
    def test_restart_corruption_and_no_autorun(self):
        self.add();self.queue.claim('interrupted')
        with patch('core.export_queue.process_alive',return_value=False):
            self.assertEqual(ExportQueue(self.temp.name).snapshot()['items'][0]['status'],'error')
        self.queue.path.write_text('{bad',encoding='utf-8')
        with self.assertRaises(ValueError):self.queue.snapshot()
        self.assertEqual(self.queue.path.read_text(),'{bad')
    def test_preferences(self):
        prefs=FootagePreferences(self.temp.name)
        prefs.save(dict(expanded=False,size=160,filter='suitable',scroll=450,search='IMG'))
        self.assertEqual(FootagePreferences(self.temp.name).get()['scroll'],450)

if __name__=='__main__':unittest.main()
