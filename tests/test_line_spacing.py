"""Diacritics must not move letter bodies off a scene's evenly spaced baselines."""
from pathlib import Path
import unittest
from unittest.mock import patch
from PIL import Image, ImageDraw
from core.renderer import get_font, layout_overlay, render_overlay, paint_outlined_text, SAFE_BOTTOM
from core.settings import normalize_settings

ROOT=Path(__file__).resolve().parent.parent


class LineSpacingTests(unittest.TestCase):
    def test_same_letter_bodies_stay_on_baseline_despite_different_accents(self):
        for name in ['timesbd.ttf','segoeuib.ttf','segoeui.ttf']:
            font=get_font(name,68,str(ROOT))
            lines=['AAA Chỉ những người tu','AAA đến mức không thấy','AAA mình quan trọng nữa']
            baselines=[100,210,320]
            image=paint_outlined_text(Image.new('RGBA',(1100,370)),[(20,y,text) for y,text in zip(baselines,lines)],
                                      font,(255,255,255,255),normalize_settings(dict(outline_enabled=False)),anchor='ls')
            width=int(ImageDraw.Draw(image).textlength('AAA',font=font))
            crops=[image.crop((20,y-80,20+width,y+25)).tobytes() for y in baselines]
            self.assertTrue(crops[0]==crops[1]==crops[2],name)

    def test_renderer_uses_uniform_baselines_for_quote_and_credit_in_all_themes(self):
        quote='Chỉ những người tu đến mức không thấy mình quan trọng nữa'
        credit='Chỉ những người tu đến mức không thấy mình quan trọng nữa — Sách hay mỗi ngày với lòng biết ơn và yêu thương'
        for theme in range(5):
            options=dict(theme_index=theme,quote_size=108,credit_size=32,workspace_dir=str(ROOT))
            layout=layout_overlay(quote,credit,**options)
            with patch('core.renderer.paint_outlined_text',wraps=paint_outlined_text) as painter:
                render_overlay(quote,credit,**options)
            for call,step,first in zip(painter.call_args_list,[layout['qline'],layout['cline']],
                                       [layout['quote_baseline'],layout['credit_baseline']]):
                entries=call.args[1]
                self.assertEqual(call.kwargs['anchor'],'ls')
                self.assertEqual([entry[1] for entry in entries],[first+i*step for i in range(len(entries))])
            draw=ImageDraw.Draw(Image.new('L',(1,1)))
            for lines,font,baseline,step,top,bottom in [
                (layout['lines'],layout['qfont'],layout['quote_baseline'],layout['qline'],layout['quote_y'],layout['credit_y']-40),
                (layout['credits'],layout['cfont'],layout['credit_baseline'],layout['cline'],layout['credit_y'],layout['bottom'])]:
                for index,text in enumerate(lines):
                    bounds=draw.textbbox((0,baseline+index*step),text,font=font,anchor='ls')
                    self.assertGreaterEqual(bounds[1],top)
                    self.assertLessEqual(bounds[3],bottom)
            self.assertLessEqual(layout['bottom'],SAFE_BOTTOM)


if __name__=='__main__':unittest.main()
