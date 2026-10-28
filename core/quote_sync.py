"""Read-only public Google Sheet catalog; background refresh never touches drafts or footage."""
import copy
import csv
import hashlib
import io
import json
import logging
import math
from pathlib import Path
import threading
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from core.persistence import atomic_json, file_mutex, read_json
from core.pmdx_reader import get_all_quotes

SHEET_ID = '1Ku40G9gH89W7eRpN6u6NAYnxj2hGf8Gv-QL_34a2teI'
SHEET_NAME = 'Đạo lý hay mỗi ngày'
SHEET_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit'
CSV_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?' + urlencode(
    dict(tqx='out:csv', sheet=SHEET_NAME, range='A:A', headers='0'))
SYNC_INTERVAL = 30 * 60
MAX_BYTES = 2 * 1024 * 1024
CREDIT = 'Thanh Vị Sách Hay Mỗi Ngày'


def normalize_quote(text):
    return unicodedata.normalize('NFC', text.replace('\r\n', '\n').replace('\r', '\n')).strip()


def parse_quotes_csv(data):
    text = data.decode('utf-8-sig')
    if text.lstrip().startswith(('<', '{')):
        raise ValueError('Google chưa trả dữ liệu câu nói công khai. Danh sách cũ được giữ nguyên.')
    result = []
    for row in csv.reader(io.StringIO(text, newline=''), strict=True):
        quote = normalize_quote(row[0]) if row else ''
        if not quote:
            continue
        if len(quote) > 20000:
            raise ValueError('Sheet có câu dài quá 20.000 ký tự. Hãy rút ngắn câu đó rồi cập nhật lại.')
        result.append(quote)
        if len(result) > 10000:
            raise ValueError('Sheet vượt quá 10.000 câu. Danh sách cũ được giữ nguyên.')
    return result


def fetch_sheet_quotes():
    # No cookie jar, OAuth, API key, login or write request. Column B (done) is irrelevant.
    request = Request(CSV_URL, headers={'User-Agent': 'AutoReel-PublicSheet-ReadOnly/1.0', 'Cache-Control': 'no-cache'})
    try:
        with urlopen(request, timeout=20) as response:
            if urlparse(response.url).hostname != 'docs.google.com' or 'csv' not in response.headers.get('Content-Type', '').lower():
                raise ValueError('Sheet không còn đọc công khai được. Hãy kiểm tra quyền xem bằng liên kết; app giữ danh sách cũ.')
            data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('Dữ liệu Sheet quá lớn. Danh sách cũ được giữ nguyên.')
        return parse_quotes_csv(data)
    except HTTPError as error:
        if error.code in (401, 403, 404):
            raise ValueError('Không đọc công khai được Sheet. Hãy kiểm tra liên kết/quyền xem; app giữ danh sách cũ.') from error
        raise ValueError(f'Google tạm thời không trả dữ liệu (HTTP {error.code}); app giữ danh sách cũ.') from error
    except (URLError, OSError) as error:
        raise ValueError('Chưa kết nối được Google Sheet. App tiếp tục dùng danh sách gần nhất và thử lại sau 30 phút.') from error


def quote_records(texts):
    occurrences, result = {}, []
    for text in texts:
        digest = hashlib.sha256(text.encode('utf-8')).hexdigest()[:24]
        occurrences[digest] = occurrences.get(digest, 0) + 1
        result.append(dict(id=len(result) + 1, key=f'{digest}:{occurrences[digest]}', quote=text, credit=CREDIT))
    return result


class QuoteSyncService:
    def __init__(self, workspace, enabled=True, fetcher=None, interval=SYNC_INTERVAL, clock=None):
        self.workspace = Path(workspace)
        self.cache_path = self.workspace / '.cache' / 'quotes' / 'google_sheet.json'
        self.enabled = enabled
        self.fetcher = fetcher or fetch_sheet_quotes
        self.interval = interval
        self.clock = clock or time.time
        self.lock = threading.RLock()
        self.refresh_lock = threading.Lock()
        self.wake = threading.Event()
        self.stopped = threading.Event()
        self.worker = None
        self.source = 'local'
        self.quotes = quote_records([q['quote'] for q in get_all_quotes(str(self.workspace))])
        self.last_checked_at = self.last_success_at = self.next_check_at = None
        self.error = ''
        self.syncing = self.requested = False
        if enabled:
            try:
                cached = read_json(self.cache_path, dict)
                if not isinstance(cached, dict):
                    raise ValueError('Invalid sheet cache')
                if cached and (cached.get('version'), cached.get('sheet_id'), cached.get('sheet_name')) == (1, SHEET_ID, SHEET_NAME):
                    texts = cached['quotes']
                    if not isinstance(texts, list) or len(texts) > 10000 or any(not isinstance(q, str) or not q.strip() or len(q) > 20000 for q in texts):
                        raise ValueError('Invalid cached quotes')
                    last_success = float(cached['last_success_at'])
                    if not math.isfinite(last_success) or last_success < 0:
                        raise ValueError('Invalid cache timestamp')
                    self.quotes = quote_records(texts)
                    self.source = 'sheet'
                    self.last_success_at = last_success
            except (ValueError, OSError, KeyError, TypeError):
                logging.warning('Sheet cache unavailable; using local quotes until next refresh.')

    def _status(self):
        revision = hashlib.sha256(json.dumps(self.quotes, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
        return dict(enabled=self.enabled, syncing=self.syncing or self.requested, source=self.source,
                    count=len(self.quotes), revision=revision, sheet_name=SHEET_NAME, sheet_url=SHEET_URL,
                    interval_seconds=self.interval, last_checked_at=self.last_checked_at,
                    last_success_at=self.last_success_at, next_check_at=self.next_check_at, error=self.error)

    def status(self):
        with self.lock:
            return self._status()

    def snapshot(self):
        with self.lock:
            return dict(quotes=copy.deepcopy(self.quotes), sync=self._status())

    def get_quotes(self):
        with self.lock:
            return copy.deepcopy(self.quotes)

    def refresh(self):
        if not self.enabled or not self.refresh_lock.acquire(blocking=False):
            return self.status()
        try:
            with self.lock:
                self.syncing = True
                self.requested = False
                self.last_checked_at = self.clock()
            texts = self.fetcher()
            # Reuse CSV validation for injected sources too, without interpreting sheet text as code.
            if not isinstance(texts, list) or len(texts) > 10000 or any(not isinstance(q, str) or not q.strip() or len(q) > 20000 for q in texts):
                raise ValueError('Dữ liệu câu nói không hợp lệ. Danh sách cũ được giữ nguyên.')
            texts = [normalize_quote(q) for q in texts]
            now = self.clock()
            cached = dict(version=1, sheet_id=SHEET_ID, sheet_name=SHEET_NAME, quotes=texts, last_success_at=now)
            with file_mutex(self.cache_path.with_suffix('.lock')):
                atomic_json(self.cache_path, cached)
            with self.lock:
                self.quotes = quote_records(texts)
                self.source = 'sheet'
                self.last_success_at = now
                self.error = ''
        except Exception as error:
            logging.warning('Read-only sheet refresh failed: %s', error)
            with self.lock:
                self.error = str(error) or 'Chưa cập nhật được Sheet; danh sách cũ được giữ nguyên.'
        finally:
            with self.lock:
                self.syncing = False
                self.next_check_at = self.clock() + self.interval
            self.refresh_lock.release()
        return self.status()

    def _run(self):
        while not self.stopped.is_set():
            self.wake.clear()
            self.refresh()
            if self.stopped.is_set():
                break
            self.wake.wait(self.interval)

    def start(self):
        if not self.enabled:
            return
        with self.lock:
            if self.worker and self.worker.is_alive():
                return
            self.requested = True
            self.worker = threading.Thread(target=self._run, name='quote-sheet-sync', daemon=True)
            self.worker.start()

    def request_refresh(self):
        with self.lock:
            if self.enabled and not (self.syncing or self.requested):
                self.requested = True
                self.wake.set()
            return self._status()

    def close(self):
        self.stopped.set()
        self.wake.set()
        if self.worker:
            self.worker.join(timeout=1)
