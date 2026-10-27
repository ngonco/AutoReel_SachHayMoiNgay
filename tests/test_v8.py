"""Library isolation, meaningful scene breaks, balanced lines and previous-quote exclusion."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw
from core.paginator import split_into_slides
from core.renderer import wrap_text, get_font
from core.video_detector import VideoDetector
from core.video_library import VideoLibraryService
from core.settings import load_settings, save_settings_patch
from core.footage_pool import FootagePool, FootageConflict, identity
from core.persistence import atomic_json

ROOT = Path(__file__).resolve().parent.parent


class SegmentationTests(unittest.TestCase):
    def test_sentence_punctuation_short_text_and_abbreviations(self):
        self.assertEqual(split_into_slides('Bình an. Yêu thương! Biết ơn?'), ['Bình an.', 'Yêu thương!', 'Biết ơn?'])
        self.assertEqual(split_into_slides('“Bình an.” (Yêu thương!)'), ['“Bình an.”', '(Yêu thương!)'])
        self.assertEqual(split_into_slides('TS. An ở TP. Huế có 3.14 đồng.'), ['TS. An ở TP. Huế có 3.14 đồng.'])
        self.assertEqual(split_into_slides('Bình an… Yêu thương.'), ['Bình an…', 'Yêu thương.'])

    def test_connectives_start_next_scene_losslessly(self):
        for connector in ['nhưng', 'mà', 'tuy nhiên', 'vì vậy', 'do đó', 'mặc dù', 'và ta', 'khi bạn']:
            text='Hãy sống tử tế với mọi người quanh mình, '+connector+' luôn biết yêu thương bằng những hành động nhỏ mỗi ngày.'
            scenes=split_into_slides(text)
            self.assertGreater(len(scenes),1,connector)
            self.assertTrue(any(s.startswith(connector+' ') for s in scenes[1:]),scenes)
            self.assertEqual(' '.join(scenes),text)
        self.assertEqual(split_into_slides('Yêu thương và biết ơn mỗi ngày.'),['Yêu thương và biết ơn mỗi ngày.'])
        long=' '.join(['ta sống tử tế để cuộc đời bình an']*40)
        scenes=split_into_slides(long)
        self.assertTrue(all(6<=len(s.split())<=24 for s in scenes))
        self.assertEqual(' '.join(scenes),long)

    def test_balanced_wrapping_preserves_phrases_and_width(self):
        draw=ImageDraw.Draw(Image.new('RGBA',(1080,1920)))
        for name in ['timesbd.ttf','segoeuib.ttf','segoeui.ttf']:
            font=get_font(name,68,str(ROOT))
            text='Hãy sống với lòng biết ơn và yêu thương để tìm thấy bình an.'
            lines=wrap_text(text,font,768,draw)
            self.assertEqual(' '.join(lines),text)
            self.assertTrue(all(draw.textlength(s,font=font)<=768 for s in lines))
            self.assertGreater(len(lines[-1].split()),2,lines)
            for left,right in zip(lines,lines[1:]):
                self.assertNotIn(left.split()[-1]+' '+right.split()[0],{'biết ơn','yêu thương','bình an'})
            overlong='a'*100
            chunks=wrap_text(overlong,font,768,draw)
            self.assertEqual(''.join(chunks),overlong)
            self.assertTrue(all(draw.textlength(s,font=font)<=768 for s in chunks))


class LibraryTests(unittest.TestCase):
    def test_recursive_selection_cancel_default_missing_empty_and_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);custom=root/'custom';nested=custom/'sub';nested.mkdir(parents=True)
            (nested/'one.MOV').write_bytes(b'clip')
            (custom/'ignored.txt').write_text('skip')
            defaults=root/'CLIP TƯỢNG PHẬT LQ'/'DỌC';defaults.mkdir(parents=True)
            (defaults/'default.mp4').write_bytes(b'default')
            detector=VideoDetector(root);service=VideoLibraryService(root,detector)
            def analyzed(path):return dict(path=path,name=Path(path).name)
            with patch.object(detector,'analyze_video',side_effect=analyzed):
                with patch('core.video_library.native_directory_dialog',return_value=str(custom)):
                    result=service.select()
                self.assertEqual([v['name'] for v in result['videos']],['one.MOV'])
                self.assertEqual(load_settings(root)['background_video_directory'],str(custom))
                with patch('core.video_library.native_directory_dialog',return_value=''):
                    self.assertTrue(service.select()['cancelled'])
                save_settings_patch(root,dict(quote='Giữ nguyên bản nháp'))
                self.assertEqual(load_settings(root)['background_video_directory'],str(custom))
                restarted=VideoDetector(root)
                with patch.object(restarted,'analyze_video',side_effect=analyzed):
                    self.assertEqual(len(restarted.scan_all_videos()),1)
                with self.assertRaises(ValueError):detector.scan_all_videos(str(root/'missing'))
                empty=root/'empty';empty.mkdir()
                with patch('core.video_library.native_directory_dialog',return_value=str(empty)):
                    with self.assertRaises(ValueError):service.select()
                self.assertEqual(load_settings(root)['background_video_directory'],str(custom))
                self.assertEqual(service.select(True)['directory'],'')
                self.assertEqual([v['name'] for v in detector.scan_all_videos()],['default.mp4'])
                self.assertEqual(load_settings(root)['quote'],'Giữ nguyên bản nháp')


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.videos=[]
        for i in range(5):
            path=self.root/f'{i}.mp4';path.write_bytes(f'footage-{i}'.encode())
            self.videos.append(dict(path=str(path),name=path.name,is_vertical=True))
        self.pool=FootagePool(self.root)

    def tearDown(self):self.temp.cleanup()

    def plan(self, videos=None, count=2, avoid=None, quote='A'):
        allocation,summary=self.pool.preview(videos or self.videos,count,avoid_ids=avoid,quote=quote)
        return dict(footage_pool=summary,scenes=[dict(footage_id=key) for key,_ in allocation])

    @staticmethod
    def ids(plan):return [s['footage_id'] for s in plan['scenes']]

    def test_previous_preview_no_counts_and_least_used_remaining(self):
        first=self.plan();avoid=self.ids(first)
        second=self.plan(avoid=avoid,quote='B')
        self.assertFalse(set(avoid)&set(self.ids(second)))
        state=self.pool._read();self.assertFalse(state['counts'])
        state['counts']={identity(v):10-i for i,v in enumerate(self.videos)}
        atomic_json(self.pool.path,state)
        least=self.plan(count=1,avoid=avoid,quote='B')
        self.assertEqual(self.ids(least),[identity(self.videos[-1])])

    def test_history_retained_but_old_library_excluded_and_duplicate_detected(self):
        old=self.plan(videos=self.videos[:2]);self.pool.reserve(old,'old');self.pool.finish('old',True)
        new=self.plan(videos=self.videos[2:],quote='B')
        self.assertTrue(set(self.ids(new))<=set(identity(v) for v in self.videos[2:]))
        self.pool.reserve(new,'new');self.pool.validate_export('new');self.pool.finish('new',True)
        back=self.plan(videos=self.videos[:2],quote='C')
        self.assertEqual(back['footage_pool']['total'],2)
        self.assertTrue(all(self.pool._read()['counts'][key]==1 for key in self.ids(old)))
        duplicate=self.root/'copy.mp4';duplicate.write_bytes(Path(self.videos[0]['path']).read_bytes())
        duplicated=[self.videos[0],dict(path=str(duplicate),name=duplicate.name,is_vertical=True)]
        self.assertEqual(self.plan(videos=duplicated,count=1)['footage_pool']['total'],1)

    def test_previous_export_survives_restart_and_fallback_only_after_new_options(self):
        old=self.plan();self.pool.reserve(old,'old');self.pool.validate_export('old');self.pool.finish('old',True)
        self.pool=FootagePool(self.root)
        following=self.plan(count=6,quote='B');ids=self.ids(following)
        self.assertFalse(set(ids[:3])&set(self.ids(old)))
        self.assertEqual(len(set(ids[:5])),5)
        self.assertEqual(following['footage_pool']['fallback_scenes'],[3,4])
        self.assertEqual(following['footage_pool']['repeated_scenes'],[5])
        self.pool.reserve(following,'next');self.pool.validate_export('next');self.pool.finish('next',True)

    def test_queued_different_quote_revalidated_against_previous_success(self):
        first=self.plan(count=2,quote='A');self.pool.reserve(first,'one')
        second=self.plan(count=2,quote='B');self.pool.reserve(second,'two')
        self.assertFalse(set(self.ids(first))&set(self.ids(second)))
        self.pool.validate_export('one');self.pool.finish('one',True)
        self.pool.validate_export('two');self.pool.finish('two',True)
        self.assertEqual(self.pool._read()['last_export']['quote'],'B')

    def test_failed_job_keeps_previous_success_and_one_clip_fallback(self):
        first=self.plan(count=1,quote='A');self.pool.reserve(first,'one');self.pool.finish('one',True)
        remembered=self.pool._read()['last_export']
        failed=self.plan(count=1,quote='B');self.pool.reserve(failed,'failed');self.pool.finish('failed',False)
        self.assertEqual(self.pool._read()['last_export'],remembered)
        only=self.plan(videos=self.videos[:1],count=3,avoid=self.ids(first),quote='C')
        self.assertEqual(len(set(self.ids(only))),1)
        self.assertEqual(only['footage_pool']['repeated_scenes'],[1,2])
        self.pool.reserve(only,'single');self.pool.validate_export('single');self.pool.finish('single',True)


if __name__=='__main__':unittest.main()
