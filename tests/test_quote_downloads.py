import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from core.quote_downloads import QuoteDownloadHistory, quote_key
from core.jobs import JobManager
from core.settings import normalize_settings


class QuoteDownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.history=QuoteDownloadHistory(self.root)
        self.catalog=dict(quotes=[dict(id=i,quote=q) for i,q in enumerate(('Bình an.','Biết ơn.','Yêu thương.'))],sync=dict(revision='sheet'))
    def tearDown(self):self.temp.cleanup()
    def test_downloads_persist_deduplicate_content_and_track_repeated_saves(self):
        self.history.record('Biết ơn.','chosen.mp4','one');self.history.record('Biết ơn.','chosen.mp4','one')
        self.history.record('  Biết\nơn.  ','other.mp4','two')
        restarted=QuoteDownloadHistory(self.root);snapshot=restarted.snapshot()
        self.assertEqual(len(snapshot['records']),1);self.assertEqual(snapshot['records'][0]['count'],2)
        quotes=restarted.annotate(self.catalog)['quotes'];self.assertEqual([q['downloaded'] for q in quotes],[False,True,False])
        self.assertNotIn('last_path',snapshot['records'][0])
    def test_first_undownloaded_startup_exact_draft_recovery_and_all_done(self):
        saved=normalize_settings(dict(quote='  Bản nháp riêng.\n\nGiữ Enter.\n',quote_size=84))
        self.history.record('Bình an.','one.mp4','one')
        result=self.history.startup(self.catalog,saved)
        self.assertEqual(result['index'],1);self.assertTrue(result['recovery_available'])
        self.assertEqual(self.history.previous_draft()['settings'],saved)
        self.history.record('Biết ơn.','two.mp4','two');self.history.record('Yêu thương.','three.mp4','three')
        all_done=self.history.startup(self.catalog,normalize_settings())
        self.assertEqual(all_done['index'],0);self.assertTrue(all_done['all_downloaded'])
        empty=self.history.startup(dict(quotes=[],sync={}),saved);self.assertEqual(empty['index'],-1)
    def test_sheet_edit_delete_reorder_and_duplicate_rows(self):
        self.history.record('Biết ơn.','one.mp4','one')
        catalog=dict(quotes=[dict(quote=q) for q in ('Biết ơn.','Biết ơn.','Biết ơn mỗi ngày.')],sync={})
        result=self.history.annotate(catalog)
        self.assertEqual([q['downloaded'] for q in result['quotes']],[True,True,False])
        self.assertEqual(self.history.startup(catalog,normalize_settings())['index'],2)
        self.history.annotate(dict(quotes=[],sync={}))
        self.assertEqual(len(self.history.snapshot()['records']),1,'Sheet removal never erases download history')
    def test_only_completed_save_records_not_render_preview_or_batch(self):
        manager=JobManager(self.root)
        try:
            manager.jobs['save']=dict(quote='Bình an.',status='queued')
            with patch('core.downloads.copy_video',side_effect=OSError('disk full')):
                manager._save_work('save',self.root/'source.mp4',self.root/'chosen.mp4')
            self.assertEqual(self.history.snapshot()['records'],[])
            with patch('core.downloads.copy_video'):
                manager._save_work('save',self.root/'source.mp4',self.root/'chosen.mp4')
            self.assertEqual(len(self.history.snapshot()['records']),1)
            self.assertEqual(manager.get('save')['status'],'done')
            manager.jobs['next']=dict(quote='Biết ơn.',status='queued')
            with patch('core.downloads.copy_video'),patch.object(manager.download_history,'record',side_effect=OSError('history unwritable')):
                manager._save_work('next',self.root/'source.mp4',self.root/'chosen.mp4')
            self.assertEqual(manager.get('next')['status'],'done','A saved file remains successful if history write fails')
            self.assertIn('chưa ghi nhớ',manager.get('next')['result']['history_warning'])
        finally:manager.close()
    def test_corrupt_history_is_preserved(self):
        self.history.path.write_text('{bad',encoding='utf-8')
        with self.assertRaises(ValueError):self.history.record('A','path','id')
        self.assertEqual(self.history.path.read_text(),'{bad')
    def test_manual_mark_unmark_restart_and_real_download_counts(self):
        self.history.mark('Bình an.')
        once=self.history.snapshot();self.history.mark('  Bình\nan.  ')
        self.assertEqual(self.history.snapshot(),once,'Marking an already marked quote is idempotent')
        record=once['records'][0];self.assertEqual(record['count'],0);self.assertIsNone(record['last_downloaded_at'])
        self.assertEqual(record['status_source'],'manual')
        self.assertEqual(self.history.startup(self.catalog,normalize_settings())['index'],1)
        self.history.mark('Bình an.',False)
        restarted=QuoteDownloadHistory(self.root)
        self.assertFalse(restarted.annotate(self.catalog)['quotes'][0]['downloaded'])
        self.assertEqual(restarted.startup(self.catalog,normalize_settings())['index'],0)
        restarted.record('Bình an.','actual.mp4','actual')
        self.assertEqual(restarted.snapshot()['records'][0]['count'],1)
        restarted.mark('Bình an.',False)
        self.assertEqual(restarted.snapshot()['records'][0]['count'],1,'Unmarking preserves the actual download audit')
        self.assertEqual(len(restarted.snapshot()['records']),1)
        self.assertFalse((self.root/'footage_usage.json').exists(),'Manual marks never consume footage turns')
    def test_manual_validation_preserves_history(self):
        for quote in (None,'','  ','x'*20001):
            with self.assertRaises(ValueError):self.history.mark(quote)
        with self.assertRaises(ValueError):self.history.mark('A','true')
        self.assertFalse(self.history.path.exists())


if __name__=='__main__':unittest.main()
