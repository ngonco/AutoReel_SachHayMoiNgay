import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from core.scroll_text import build_track, scroll_frame, scroll_offset, tile_path, FRAME_BOTTOM, edge_mask
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
        self.assertEqual(track['lines'][1]['y']-track['lines'][0]['y'],track['quote_line_height']+(track['quote_line_height']+1)//2)
        for tile in track['tiles']:
            with Image.open(tile_path(track,tile['index'],self.root)) as image:
                self.assertLessEqual(image.height,512);self.assertEqual(image.width,842)
        for t in (1,track['duration']/2,track['duration']-1):
            image=scroll_frame(track,t,self.root)
            self.assertEqual(image.size,(track['rect']['width'],track['rect']['height']))
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

    def test_five_full_lines_and_dynamic_frame_keep_bottom(self):
        text='\n'.join(['Ắn ở tử tế, giữ lòng biết ơn.']*5)
        base=self.track(text)
        self.assertEqual(base['visible_lines'],5)
        self.assertEqual(base['distance'],0)
        for size in (28,48,80):
            for rows in (2,5,8):
                track=self.track(text,scroll_quote_size=size,scroll_lines=rows)
                self.assertEqual(track['rect']['y']+track['rect']['height'],FRAME_BOTTOM)
                self.assertGreaterEqual(track['rect']['y'],180)
                self.assertEqual(track['visible_lines'],rows)
                self.assertEqual(track['font_sizes']['quote'],size)
        larger=self.track(text,scroll_quote_size=64)
        self.assertGreater(larger['rect']['height'],base['rect']['height'])
        self.assertLess(larger['rect']['y'],base['rect']['y'])
        two=self.track(text,scroll_lines=2)
        self.assertGreater(two['distance'],0)
        self.assertNotEqual(two['asset_key'],base['asset_key'])

    def test_independent_fades_zero_and_outline_cache(self):
        none=edge_mask(100,200,0,0)
        self.assertEqual(none.getextrema(),(255,255))
        separate=edge_mask(100,200,10,40)
        self.assertEqual(separate.getpixel((20,0)),0)
        self.assertEqual(separate.getpixel((20,10)),255)
        self.assertLess(separate.getpixel((20,190)),100)
        self.assertEqual(separate.getpixel((20,199)),0)
        plain=self.track('Bình an mỗi ngày.',scroll_outline_enabled=False)
        outlined=self.track('Bình an mỗi ngày.',scroll_outline_width=10,scroll_outline_blur=24,scroll_outline_color='#ff0000')
        self.assertNotEqual(plain['asset_key'],outlined['asset_key'])
        self.assertEqual(outlined['halo'],84)
        self.assertGreater(outlined['rect']['height'],plain['rect']['height'])
        self.assertNotEqual(scroll_frame(plain,1,self.root).tobytes(),scroll_frame(outlined,1,self.root).tobytes())
        saved=save_settings_patch(self.root,dict(scroll_quote_size=64,scroll_lines=8,scroll_fade_top=0,scroll_fade_bottom=64,
                                               scroll_outline_color='#446688',scroll_outline_width=7,scroll_outline_blur=12,scroll_outline_opacity=.35))
        self.assertEqual(load_settings(self.root)['scroll_lines'],8)
        self.assertEqual(load_settings(self.root)['scroll_outline_color'],'#446688')
        self.assertEqual(saved['quote_size'],68,'Scroll controls must not alter static styles')

    def test_extreme_outline_tiles_match_single_raster_across_seams(self):
        from PIL import ImageDraw
        from core.renderer import get_font,paint_outlined_text
        track=self.track('\n'.join(['ẮẤỄỠỸẬỴ tử tế hạnh phúc']*14),scroll_quote_size=80,
                         scroll_outline_width=16,scroll_outline_blur=24,scroll_lines=8)
        assembled=Image.new('RGBA',(842,track['content_height']))
        for tile in track['tiles']:
            with Image.open(tile_path(track,tile['index'],self.root)) as image:assembled.paste(image,(0,tile['y']))
        direct=Image.new('RGBA',assembled.size)
        font=get_font('seguisb.ttf',80,self.root);pen=ImageDraw.Draw(direct)
        entries=[((842-pen.textlength(line['text'],font=font))/2,line['baseline'],line['text']) for line in track['lines']]
        direct=paint_outlined_text(direct,entries,font,(255,250,239,255),track['outline'],anchor='ls')
        from PIL import ImageChops
        self.assertIsNone(ImageChops.difference(assembled,direct).getbbox(),'Blur must not form seams between PNG tiles')


if __name__=='__main__':unittest.main()
