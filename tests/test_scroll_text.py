import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from core.scroll_text import build_track, scroll_frame, scroll_offset, tile_path, RECT
from core.settings import normalize_settings, save_settings_patch, load_settings
from core.planner import build_plan
from core.renderer import scene_overlay
from core.footage_pool import FootagePool
from test_v10 import FakeDetector


class ScrollTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.settings=normalize_settings(dict(theme_index=5,duration=1,music_mode='none'))
    def tearDown(self):self.temp.cleanup()
    def track(self,text,credit='',**settings):
        return build_track(text,credit,{**self.settings,**settings},self.root)
    def test_short_static_four_lines_and_long_holds(self):
        four=self.track('Bình an\nTử tế\nBiết ơn\nHạnh phúc')
        self.assertEqual(four['distance'],0)
        self.assertEqual(scroll_frame(four,1,self.root).tobytes(),scroll_frame(four,3,self.root).tobytes())
        long=self.track('\n'.join(['Cứ sống hiền lành và tử tế.']*12),'Thanh Vị Sách Hay Mỗi Ngày')
        self.assertGreater(long['distance'],0)
        self.assertEqual(scroll_offset(long,0),scroll_offset(long,2))
        self.assertEqual(scroll_offset(long,long['duration']-2),long['distance'])
        self.assertEqual(scroll_offset(long,long['duration']-1),long['distance'])
        self.assertEqual(long['lines'][-1]['kind'],'credit')
        self.assertEqual(long['duration']*30,round(long['duration']*30))
        self.assertLess(self.track('Nhiều chữ '*60,scroll_speed=1.5)['duration'],self.track('Nhiều chữ '*60,scroll_speed=.65)['duration'])
    def test_enter_blank_paragraph_unicode_and_tile_seams(self):
        track=self.track('Tử tế\n\nBình an\n'+' '.join(['Thiền định hạnh phúc']*140))
        self.assertEqual(track['lines'][1]['y']-track['lines'][0]['y'],82)
        for tile in track['tiles']:
            with Image.open(tile_path(track,tile['index'],self.root)) as image:
                self.assertLessEqual(image.height,512);self.assertEqual(image.width,842)
        for t in (1,track['duration']/2,track['duration']-1):
            image=scroll_frame(track,t,self.root)
            self.assertEqual(image.size,(RECT['width'],RECT['height']))
            self.assertEqual(image.getchannel('A').getextrema()[1],255)
            self.assertIsNone(image.crop((0,0,image.width,1)).getbbox())
            self.assertIsNone(image.crop((0,image.height-1,image.width,image.height)).getbbox())
        token=self.track('Ắ'*1000)
        self.assertGreater(len(token['lines']),1)
    def test_plan_independent_footage_and_reservations(self):
        detector=FakeDetector(self.root)
        with patch('core.planner.probe',return_value=dict(duration=3,width=360,height=640,is_vertical=True)):
            plan=build_plan({**self.settings,'quote':'Bình an mỗi ngày.\n\n'+'Sống thật tử tế. '*20},self.root,detector)
        self.assertEqual(plan['segmentation_mode'],'continuous_scroll')
        self.assertIn('\n\n',plan['quote'])
        self.assertGreater(len(plan['scenes']),1)
        self.assertEqual(len(set(s['overlay_key'] for s in plan['scenes'])),1)
        for a,b in zip(plan['scenes'],plan['scenes'][1:]):
            self.assertAlmostEqual(a['end']-b['start'],.4)
            self.assertLess(a['speed'],1)
        before=json.loads((self.root/'footage_usage.json').read_text())
        scene_overlay(plan,plan['scenes'][1],self.root)
        self.assertEqual(json.loads((self.root/'footage_usage.json').read_text())['counts'],before['counts'])
        pool=FootagePool(self.root);pool.reserve(plan,'test');pool.validate_export('test');pool.finish('test',False)
        self.assertEqual(sum(pool._read()['counts'].values()),0)
        with patch('core.planner.probe',return_value=dict(duration=3,width=360,height=640,is_vertical=True)):
            plan=build_plan({**self.settings,'quote':plan['quote']},self.root,detector)
        pool.reserve(plan,'success');pool.validate_export('success');pool.finish('success',True)
        self.assertEqual(sum(pool._read()['counts'].values()),len(plan['scenes']))
    def test_settings_preserve_legacy_and_restart(self):
        save_settings_patch(self.root,dict(theme_index=5,scroll_speed=.8,quote='Giữ\n\nEnter',quote_size=84,vertical_offset=-100))
        restored=load_settings(self.root)
        self.assertEqual(restored['theme_index'],5);self.assertEqual(restored['scroll_speed'],.8)
        save_settings_patch(self.root,dict(theme_index=0))
        self.assertEqual(load_settings(self.root)['quote_size'],84)
        self.assertEqual(load_settings(self.root)['vertical_offset'],-100)
        for speed in (float('nan'),float('inf')):
            with self.assertRaises(ValueError):normalize_settings(dict(scroll_speed=speed))

    def test_switch_defaults_on_once_and_preserves_old_draft_and_static_style(self):
        path=self.root/'session_state.json'
        path.write_text(json.dumps(dict(theme_index=3,quote='Giữ\n\nnguyên bản nháp',quote_size=86)),encoding='utf-8')
        before=path.read_bytes()
        initial=load_settings(self.root)
        self.assertEqual(initial['theme_index'],5)
        self.assertTrue(initial['scroll_toggle_initialized'])
        self.assertEqual(initial['static_theme_index'],3)
        self.assertEqual(initial['quote_size'],86)
        self.assertEqual(path.read_bytes(),before,'Reading settings must not rewrite the draft')
        save_settings_patch(self.root,dict(theme_index=3))
        restored=load_settings(self.root)
        self.assertEqual(restored['theme_index'],3,'An explicit off selection survives restart')
        self.assertEqual(restored['quote'],'Giữ\n\nnguyên bản nháp')
        self.assertEqual(restored['static_theme_index'],3)

    def test_empty_profile_defaults_to_scroll(self):
        initial=load_settings(self.root)
        self.assertEqual(initial['theme_index'],5)
        self.assertEqual(initial['static_theme_index'],0)


if __name__=='__main__':unittest.main()
