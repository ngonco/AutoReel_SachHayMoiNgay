import hashlib
from io import BytesIO
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from core.music_library import choose_music,music_tracks,music_folder,download_track
from core.settings import normalize_settings


class MusicTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.folder=music_folder(self.root,{})
        self.folder.mkdir(parents=True)
        for i in range(3):(self.folder/f'Nhạc {i}.mp3').write_bytes(f'audio{i}'.encode())
    def tearDown(self):self.temp.cleanup()
    def test_random_is_stable_across_design_changes_and_avoids_previous(self):
        settings=normalize_settings(dict(music_seed='fixed'))
        with patch('core.music_library.audio_info',return_value=dict(duration=20)):
            first,details=choose_music(self.root,settings,'Bình an.')
            same,_=choose_music(self.root,{**settings,'quote_size':98},'Bình an.')
            self.assertEqual(first,same)
            other,_=choose_music(self.root,settings,'Bình an.',str(first.resolve()))
            self.assertNotEqual(first,other)
            selected,_=choose_music(self.root,{**settings,'music_mode':'selected','music_path':str(first.resolve())},'Other')
            self.assertEqual(selected,first)
        self.assertEqual(choose_music(self.root,{**settings,'music_mode':'none'},'A')[0],None)
    def test_folder_follows_footage_and_missing_selected_reports_error(self):
        target=self.root/'footage'
        self.assertEqual(music_folder(self.root,dict(background_video_directory=str(target))),target/'NHẠC NỀN')
        with self.assertRaises(ValueError):choose_music(self.root,normalize_settings(dict(music_mode='selected',music_path='missing')),'A')
        self.assertEqual(len(music_tracks(self.root,{})),3)
    def test_download_hash_reuse_and_preserves_same_named_local_file(self):
        data=b'valid audio data';sha=hashlib.sha256(data).hexdigest()
        item=dict(path='music background/Test.mp3',size=len(data),lfs=dict(oid=sha))
        def response(*args,**kwargs):return BytesIO(data)
        existing=self.folder/'Test.mp3';existing.write_bytes(b'personal audio')
        with patch('urllib.request.urlopen',side_effect=response) as request,patch('core.music_library.audio_info',return_value=dict(duration=1)):
            target=download_track(self.folder,'revision',item)
            self.assertEqual(existing.read_bytes(),b'personal audio');self.assertNotEqual(target,existing)
            self.assertEqual(target.read_bytes(),data)
            download_track(self.folder,'revision',item);self.assertEqual(request.call_count,1)
        bad={**item,'path':'music background/Broken.mp3','lfs':dict(oid='0'*64)}
        with patch('urllib.request.urlopen',side_effect=response):
            with self.assertRaises(ValueError):download_track(self.folder,'revision',bad)
        self.assertFalse((self.folder/'Broken.mp3').exists());self.assertEqual(list(self.folder.glob('*.partial')),[])


if __name__=='__main__':unittest.main()
