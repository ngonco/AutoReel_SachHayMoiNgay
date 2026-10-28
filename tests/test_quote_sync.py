"""Anonymous Sheet reads, durable fallback, exact scheduling and draft isolation."""
import csv
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from core.quote_sync import (QuoteSyncService, parse_quotes_csv, fetch_sheet_quotes,
                             CSV_URL, SHEET_ID, SHEET_NAME, SYNC_INTERVAL, MAX_BYTES)


class CsvTests(unittest.TestCase):
    def test_column_a_all_rows_done_ignored_nfc_and_multiline(self):
        raw='\ufeff"Hạnh phúc, \"\"bình an\"\"","done"\r\n"Dòng một.\r\nDòng hai.",""\r\n"",done\r\n"Yêu thương.",done\r\n"Yêu thương.",\r\n'
        self.assertEqual(parse_quotes_csv(raw.encode()),['Hạnh phúc, "bình an"','Dòng một.\nDòng hai.','Yêu thương.','Yêu thương.'])
        self.assertEqual(parse_quotes_csv(b''),[])
        self.assertEqual(parse_quotes_csv(b'""\n\n'),[])

    def test_reject_html_json_bad_csv_encoding_and_oversize_quote(self):
        for raw in [b'<html>Sign in</html>',b'{"error":"denied"}',b'"not closed',b'\xff',('x'*20001).encode()]:
            with self.subTest(raw=raw[:30]),self.assertRaises((ValueError,csv.Error)):
                parse_quotes_csv(raw)

    def test_fetch_is_cookie_free_read_only_and_checks_response(self):
        class Response(io.BytesIO):
            url=CSV_URL
            headers={'Content-Type':'text/csv; charset=utf-8'}
        with patch('core.quote_sync.urlopen',return_value=Response('"Bình an.",done\n'.encode())) as opened:
            self.assertEqual(fetch_sheet_quotes(),['Bình an.'])
            request=opened.call_args.args[0]
            self.assertEqual(request.get_method(),'GET')
            self.assertFalse(request.has_header('Authorization'))
            self.assertFalse(request.has_header('Cookie'))
            self.assertIn('range=A%3AA',request.full_url)
            self.assertEqual(opened.call_args.kwargs['timeout'],20)
        response=Response(b'<html>login</html>');response.headers={'Content-Type':'text/html'}
        with patch('core.quote_sync.urlopen',return_value=response),self.assertRaisesRegex(ValueError,'công khai'):
            fetch_sheet_quotes()
        response=Response(b'x'*(MAX_BYTES+1))
        with patch('core.quote_sync.urlopen',return_value=response),self.assertRaisesRegex(ValueError,'quá lớn'):
            fetch_sheet_quotes()
        for error in [HTTPError(CSV_URL,403,'Forbidden',{},None),URLError('offline')]:
            with patch('core.quote_sync.urlopen',side_effect=error),self.assertRaises(ValueError):fetch_sheet_quotes()


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        (self.root/'quotes.txt').write_text('Câu cục bộ.\n',encoding='utf-8')
        self.now=1000

    def tearDown(self):self.temp.cleanup()

    def service(self,fetcher):return QuoteSyncService(self.root,fetcher=fetcher,clock=lambda:self.now)

    def test_full_snapshot_add_edit_delete_empty_and_stable_revision(self):
        values=[['Câu một.','Câu hai.'],['Câu hai.','Câu một.'],['Câu hai đã sửa.','Câu mới.'],[]]
        service=self.service(lambda:values.pop(0))
        service.refresh();old=service.get_quotes();old_revision=service.status()['revision']
        service.refresh();reordered=service.get_quotes()
        self.assertEqual(reordered[1]['key'],old[0]['key'])
        self.assertNotEqual(service.status()['revision'],old_revision)
        service.refresh();self.assertEqual([q['quote'] for q in service.get_quotes()],['Câu hai đã sửa.','Câu mới.'])
        service.refresh();self.assertEqual(service.get_quotes(),[])
        restarted=self.service(lambda:[])
        self.assertEqual(restarted.get_quotes(),[])
        self.assertEqual(restarted.status()['source'],'sheet')

    def test_offline_retains_cache_after_restart_and_does_not_touch_personal_files(self):
        files=['session_state.json','footage_usage.json']
        for name in files:(self.root/name).write_text('{"keep":"exact bytes"}',encoding='utf-8')
        service=self.service(lambda:['Đã tải.']);service.refresh()
        snapshot=service.snapshot();cache=service.cache_path.read_bytes()
        copied=service.get_quotes();copied.clear();self.assertEqual(len(service.get_quotes()),1)
        def offline():raise ValueError('Mất mạng; giữ danh sách gần nhất.')
        service=self.service(offline);self.now=2000
        with self.assertLogs(level='WARNING'):service.refresh()
        self.assertEqual(service.get_quotes(),snapshot['quotes'])
        self.assertEqual(service.cache_path.read_bytes(),cache)
        self.assertEqual(service.status()['last_success_at'],1000)
        self.assertEqual(service.status()['last_checked_at'],2000)
        self.assertEqual(service.status()['next_check_at'],3800)
        for name in files:self.assertEqual((self.root/name).read_text(encoding='utf-8'),'{"keep":"exact bytes"}')

    def test_failure_before_first_fetch_uses_local_and_cache_failure_is_atomic(self):
        def offline():raise ValueError('offline')
        service=self.service(offline)
        with self.assertLogs(level='WARNING'):service.refresh()
        self.assertEqual(service.get_quotes()[0]['quote'],'Câu cục bộ.')
        service.fetcher=lambda:['Câu từ Sheet.'];service.refresh();before=service.cache_path.read_bytes()
        service.fetcher=lambda:['Không được ghi dở.']
        with patch('core.quote_sync.atomic_json',side_effect=PermissionError('disk')),self.assertLogs(level='WARNING'):
            service.refresh()
        self.assertEqual(service.cache_path.read_bytes(),before)
        self.assertEqual(service.get_quotes()[0]['quote'],'Câu từ Sheet.')

    def test_startup_then_every_1800_seconds_even_after_failure(self):
        calls=[]
        def fetched():
            calls.append(self.now)
            if len(calls)==2:raise ValueError('offline')
            return ['Câu mới.']
        service=self.service(fetched)
        waits=[]
        class Wake:
            def clear(inner):pass
            def wait(inner,seconds):
                waits.append(seconds);self.now+=seconds
                if len(waits)==2:service.stopped.set()
        service.wake=Wake()
        with self.assertLogs(level='WARNING'):service._run()
        self.assertEqual(SYNC_INTERVAL,1800)
        self.assertEqual(calls,[1000,2800])
        self.assertEqual(waits,[1800,1800])
        self.assertEqual(service.get_quotes()[0]['quote'],'Câu mới.')

    def test_background_start_does_not_block_snapshots_and_manual_requests_coalesce(self):
        entered=threading.Event();release=threading.Event();calls=[]
        def fetched():
            calls.append(1);entered.set();release.wait(5);return ['Đồng bộ nền.']
        service=self.service(fetched)
        try:
            service.start();self.assertTrue(entered.wait(2))
            self.assertTrue(service.status()['syncing'])
            self.assertEqual(service.get_quotes()[0]['quote'],'Câu cục bộ.')
            for _ in range(5):service.request_refresh()
            release.set()
            for _ in range(100):
                if not service.status()['syncing']:break
                threading.Event().wait(.01)
            self.assertEqual(calls,[1])
            self.assertEqual(service.get_quotes()[0]['quote'],'Đồng bộ nền.')
        finally:release.set();service.close()

    def test_disabled_profile_never_reads_network_or_sheet_cache(self):
        service=self.service(lambda:['Cache.']);service.refresh()
        with patch('core.quote_sync.fetch_sheet_quotes') as fetched:
            disabled=QuoteSyncService(self.root,enabled=False)
            disabled.start();disabled.refresh();disabled.request_refresh();disabled.close()
            fetched.assert_not_called()
        self.assertEqual(disabled.get_quotes()[0]['quote'],'Câu cục bộ.')

    def test_corrupt_cache_does_not_prevent_startup_or_publish_partial_data(self):
        service=self.service(lambda:['Dữ liệu tốt.']);service.refresh()
        valid=json.loads(service.cache_path.read_text(encoding='utf-8'))
        for broken in [[1],'{bad json}',{**valid,'last_success_at':'not a timestamp'},
                       {**valid,'last_success_at':float('nan')},{**valid,'quotes':['']}]:
            service.cache_path.write_text(broken if isinstance(broken,str) else json.dumps(broken),encoding='utf-8')
            with self.assertLogs(level='WARNING'):fallback=self.service(lambda:['Khôi phục.'])
            self.assertEqual(fallback.status()['source'],'local')
            self.assertEqual(fallback.get_quotes()[0]['quote'],'Câu cục bộ.')
            fallback.refresh();self.assertEqual(fallback.get_quotes()[0]['quote'],'Khôi phục.')

    def test_catalog_api_and_batch_freeze_the_submitted_quote_list(self):
        import app
        service=self.service(lambda:['Câu một.','Câu hai.']);service.refresh()
        submitted=[]
        class Detector:
            def scan_all_videos(inner,directory=None):return [dict(path='fixture.mp4')]
        class Jobs:
            def batch(inner,items,detector):
                submitted.extend(items)
                service.fetcher=lambda:['Câu hai đã sửa.','Bài mới.','Bài mới nữa.']
                service.refresh()
                return dict(job_id='frozen',status='done',total=len(items))
        with patch.multiple(app,BASE_DIR=self.root,quote_sync=service,video_detector=Detector(),jobs=Jobs()):
            server=ThreadingHTTPServer(('127.0.0.1',0),app.ReelRequestHandler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            def api(path,body=None):
                request=Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
                with urlopen(request,timeout=5) as response:return json.load(response)
            try:
                self.assertEqual(len(api('/api/quotes')),2)
                self.assertEqual(api('/api/quote_catalog')['sync']['interval_seconds'],1800)
                job=api('/api/batch_render',{'async':True})
                self.assertEqual(job['total'],2)
                self.assertEqual([item['quote'] for item in submitted],['Câu một.','Câu hai.'])
                self.assertEqual(len(api('/api/quotes')),3)
                status=api('/api/quote_sync',{})
                self.assertTrue(status['syncing'])
                self.assertFalse((self.root/'session_state.json').exists())
            finally:
                server.shutdown();server.server_close();thread.join(timeout=2)


if __name__=='__main__':unittest.main()
