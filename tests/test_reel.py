import json
from pathlib import Path
import tempfile
import unittest
import unicodedata
from unittest.mock import patch
from PIL import Image, ImageDraw
from core.paginator import split_into_slides, calculate_slide_timings
from core.pmdx_reader import DEFAULT_QUOTES
from core.settings import normalize_settings
from core.renderer import layout_overlay, render_overlay, SAFE_BOTTOM, soft_outline, paint_outlined_text, get_font
from core.planner import build_plan, load_plan

ROOT=Path(__file__).resolve().parent.parent

class ContentTests(unittest.TestCase):
    def test_outline_settings_defaults_validation_and_legacy_names(self):
        self.assertTrue(normalize_settings({})['outline_enabled'])
        style=normalize_settings(dict(outlineEnabled='false',outlineColor='#AABBCC',outlineWidth=99,outlineBlur=99,outlineOpacity=85))
        self.assertFalse(style['outline_enabled'])
        self.assertEqual((style['outline_color'],style['outline_width'],style['outline_blur'],style['outline_opacity']),('#aabbcc',16,24,.85))
        self.assertEqual(normalize_settings(dict(outline_color='invalid'))['outline_color'],'auto')
        self.assertEqual(normalize_settings(dict(outline_width=-8,outline_blur=-1))['outline_width'],0)

    def test_outline_fades_outward_without_covering_solid_glyphs(self):
        mask=Image.new('L',(80,80))
        ImageDraw.Draw(mask).rectangle((30,30,49,49),fill=255)
        style=normalize_settings(dict(outline_width=4,outline_blur=4,outline_opacity=1,outline_color='#123456'))
        halo=soft_outline(mask,style)
        alpha=halo.getchannel('A')
        self.assertEqual(alpha.getpixel((35,40)),0)
        self.assertGreater(alpha.getpixel((26,40)),alpha.getpixel((20,40)))
        self.assertGreater(alpha.getpixel((20,40)),alpha.getpixel((0,40)))
        self.assertEqual(halo.getpixel((26,40))[:3],(18,52,86))
        for overrides in [dict(outline_enabled=False),dict(outline_opacity=0),dict(outline_width=0,outline_blur=0)]:
            self.assertIsNone(soft_outline(mask,{**style,**overrides}).getchannel('A').getbbox())
        hard=soft_outline(mask,{**style,'outline_blur':0}).getchannel('A')
        self.assertEqual(hard.getpixel((25,40)),0)
        self.assertGreater(alpha.getpixel((25,40)),0)

    def test_outline_preserves_crisp_letter_fill(self):
        image=Image.new('RGBA',(180,110))
        font=get_font('segoeuib.ttf',42,str(ROOT))
        entries=[(30,30,'An')]
        off=paint_outlined_text(image,entries,font,(255,250,240,255),normalize_settings(dict(outline_enabled=False)))
        on=paint_outlined_text(image,entries,font,(255,250,240,255),normalize_settings())
        solid=[(x,y) for y in range(image.height) for x in range(image.width) if off.getpixel((x,y))[3]==255]
        self.assertTrue(solid)
        self.assertTrue(all(on.getpixel(point)==off.getpixel(point) for point in solid))
        self.assertGreater(sum(on.getchannel('A').tobytes()),sum(off.getchannel('A').tobytes()))
        kwargs=dict(theme_index=4,workspace_dir=str(ROOT))
        automatic=render_overlay('Bình an.','Sách Hay',**kwargs)
        explicit=render_overlay('Bình an.','Sách Hay',outline_color='#fff8e9',**kwargs)
        self.assertEqual(automatic.tobytes(),explicit.tobytes())

    def test_all_quotes_preserved_and_bounded(self):
        samples=DEFAULT_QUOTES+[' '.join(['Tỉnh thức, bình an và yêu thương.']*25), 'Một câu có dấu phân rã: hạnh phúc, và bình an.']
        for text in samples:
            with self.subTest(text=text[:40]):
                scenes=split_into_slides(text)
                for left, right in zip(scenes, scenes[1:]):
                    self.assertNotEqual(left.split()[-1].lower() + ' ' + right.split()[0].lower(), 'nhận lỗi')
                self.assertEqual(' '.join(scenes), ' '.join(unicodedata.normalize('NFC',text).split()))
                self.assertTrue(all(len(s.split())<=24 for s in scenes))
                timings=calculate_slide_timings(scenes,12)
                self.assertEqual(timings[0]['start'],0)
                self.assertGreaterEqual(timings[-1]['end'],12)
                for i,scene in enumerate(timings):
                    visible=scene['text_end']-scene['text_start']-.4
                    self.assertGreaterEqual(visible+1e-8,len(scene['text'].split())/3)
                    self.assertGreater(scene['end'],scene['start'])
                    if i:
                        self.assertAlmostEqual(timings[i-1]['end']-scene['start'],.4)
                        self.assertAlmostEqual(timings[i-1]['text_end'],scene['text_start'])

    def test_disabled_pagination_and_empty(self):
        self.assertEqual(split_into_slides(DEFAULT_QUOTES[0],False),[DEFAULT_QUOTES[0]])
        with self.assertRaises(ValueError): calculate_slide_timings([''])

    def test_enter_creates_exact_scenes_even_when_auto_is_disabled(self):
        expected=['Hạnh phúc đến từ yêu thương.', 'Hãy sống tử tế mỗi ngày.', 'Bình an trong từng việc nhỏ.']
        text='  '+expected[0]+'\r\n\r\n  '+expected[1]+'\r\n  '+expected[2]+'  \n'
        for auto in [True,False]:
            self.assertEqual(split_into_slides(text,auto),expected)
        long_line=' '.join(['Yêu thương và biết ơn.']*8)
        self.assertEqual(split_into_slides(long_line+'\nBình an.'),[long_line,'Bình an.'])
        self.assertEqual(split_into_slides('\n\nHạnh phúc.\n'),['Hạnh phúc.'])

    def test_wide_y_settings_and_full_safe_travel(self):
        for offset in [-1600,-1000,650,1200,1600]:
            self.assertEqual(normalize_settings({'vertical_offset':offset})['vertical_offset'],offset)
            self.assertEqual(normalize_settings({'verticalOffset':offset})['vertical_offset'],offset)
        self.assertEqual(normalize_settings({'vertical_offset':9999})['vertical_offset'],1600)
        self.assertEqual(normalize_settings({'vertical_offset':-9999})['vertical_offset'],-1600)
        for pos in ['top','center','bottom']:
            low=layout_overlay('Bình an mỗi ngày.','Sách Hay',pos_mode=pos,vertical_offset=-1600,workspace_dir=str(ROOT))
            high=layout_overlay('Bình an mỗi ngày.','Sách Hay',pos_mode=pos,vertical_offset=1600,workspace_dir=str(ROOT))
            self.assertEqual(low['top'],180)
            self.assertEqual(high['bottom'],SAFE_BOTTOM)
            self.assertGreater(high['top'],low['top'])

    def test_settings_migration(self):
        s=normalize_settings(dict(creditSize=32,quoteSize=80,themeIndex=4,verticalOffset=210,shade=70,musicVolume=85,autoPaginate=False))
        self.assertEqual((s['credit_size'],s['theme_index'],s['vertical_offset']),(32,4,210))
        self.assertEqual(s['music_volume'],.85)
        self.assertFalse(s['auto_paginate'])
        self.assertEqual(normalize_settings(dict(creditSize=20,credit_size=28))['credit_size'],28)

    def test_template_footer_and_text_bounds(self):
        for theme in range(5):
            for pos in ['top','center','bottom']:
                for offset in [-1600,1600]:
                    with self.subTest(theme=theme,pos=pos,offset=offset):
                        kw=dict(theme_index=theme,pos_mode=pos,vertical_offset=offset,quote_size=108,credit_size=32,workspace_dir=str(ROOT))
                        quote='Hạnh phúc bắt đầu từ những điều giản dị, khi ta biết yêu thương và sống chậm lại.'
                        credit='Thanh Vị Sách Hay Mỗi Ngày — Cùng nuôi dưỡng lòng biết ơn và yêu thương mỗi ngày trong cuộc sống'
                        layout=layout_overlay(quote,credit,**kw)
                        self.assertGreaterEqual(layout['top'],180)
                        self.assertLessEqual(layout['bottom'],SAFE_BOTTOM)
                        self.assertLess(layout['credit_y']+layout['cline']*len(layout['credits']),layout['bottom'])
                        im=render_overlay(quote,credit,**kw)
                        self.assertEqual(im.size,(1080,1920))
                        self.assertFalse(im.getchannel('A').crop((0,SAFE_BOTTOM+50,1080,1920)).getbbox() if theme in [2,4] else False)

    def test_plan_slowdown_cycle_and_invalidation(self):
        class Detector:
            def scan_all_videos(self, directory=None): return videos
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            paths=[root/'one.mp4',root/'two.mp4']
            for path in paths: path.write_bytes(b'video fixture '+path.name.encode())
            videos=[dict(name=p.name,path=str(p),recommended_pos='bottom',is_vertical=True) for p in paths]
            with patch('core.planner.probe', return_value=dict(width=1080,height=1920,duration=2.,is_vertical=True)):
                p=build_plan(dict(quote=' '.join(['Yêu thương và biết ơn mỗi ngày.']*10),video_path=str(paths[1])),root,Detector())
                self.assertGreater(len(p['scenes']),2)
                self.assertEqual([s['video_name'] for s in p['scenes'][:3]],['two.mp4','one.mp4','two.mp4'])
                self.assertTrue(all(s['speed']<1 for s in p['scenes']))
                self.assertEqual(load_plan(p['plan_id'],root)['plan_id'],p['plan_id'])
                paths[0].write_bytes(b'changed')
                with self.assertRaises(ValueError): load_plan(p['plan_id'],root)
            videos=[]
            with self.assertRaises(ValueError): build_plan(dict(quote='Câu nói'),root,Detector())
            single=root/'single';single.mkdir();one=single/'one.mp4';one.write_bytes(b'single fixture')
            videos=[dict(name=one.name,path=str(one),recommended_pos='top',is_vertical=True)]
            with patch('core.planner.probe', return_value=dict(width=1080,height=1920,duration=2.,is_vertical=True)):
                p=build_plan(dict(quote=DEFAULT_QUOTES[0]),single,Detector())
                self.assertTrue(all(s['video_name']=='one.mp4' for s in p['scenes']))
                manual='Hạnh phúc không phải đến từ việc yêu thương bản thân,\n mà là kết quả của việc ta đã yêu thương con người rất nhiều\n và đã nỗ lực mang hạnh phúc đến cho con người.'
                p=build_plan(dict(quote=manual,auto_paginate=False,vertical_offset=1200),single,Detector())
                self.assertEqual([s['text'] for s in p['scenes']],[s.strip() for s in manual.splitlines()])
                self.assertEqual(p['quote'],'\n'.join(s.strip() for s in manual.splitlines()))
                self.assertEqual(p['segmentation_mode'],'manual_lines')
                self.assertEqual(p['settings']['vertical_offset'],1200)

if __name__=='__main__': unittest.main()
