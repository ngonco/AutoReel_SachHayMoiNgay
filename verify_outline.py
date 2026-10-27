"""Visual outline review and optional packaged-app preview/export verification."""
import argparse
import io
import json
from pathlib import Path
import shutil
import time
import urllib.request
from PIL import Image,ImageDraw,ImageChops
from core.renderer import render_overlay
from core.media import probe,run_media,tool_path
from core.video_detector import VideoDetector

ROOT=Path(__file__).resolve().parent
QUOTE='Bình an bắt đầu từ những điều giản dị trong cuộc sống.'


def make_sheet():
    review=ROOT/'test_renders'/'verification';review.mkdir(parents=True,exist_ok=True)
    video=VideoDetector(ROOT).scan_all_videos()[0]
    background=Image.open(video['thumb_path']).convert('RGBA').resize((1080,1920))
    sheet=Image.new('RGB',(1395,5*385),'#111b29');draw=ImageDraw.Draw(sheet)
    styles=[dict(outline_enabled=False),dict(),dict(outline_width=10,outline_blur=16,outline_opacity=1)]
    for theme in range(5):
        for column,style in enumerate(styles):
            overlay=render_overlay(QUOTE,theme_index=theme,shade=0,vertical_offset=350,workspace_dir=str(ROOT),**style)
            im=Image.alpha_composite(background,overlay).convert('RGB')
            crop=im.crop((55,1000,985,1710)).resize((465,355))
            sheet.paste(crop,(column*465,theme*385+30))
            draw.text((column*465+8,theme*385+8),f'Theme {theme+1} / '+['Off','Soft 4px / blur 8px','Strong 10px / blur 16px'][column],fill='white')
    path=review/'v4_outline_comparison.jpg';sheet.save(path,quality=94)
    print(path,flush=True)


def verify(base):
    def request(route,body=None):
        req=urllib.request.Request(base+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=180) as response:
            raw=response.read()
            return json.loads(raw) if 'application/json' in response.headers.get('Content-Type','') else raw
    videos=request('/api/videos')
    payload=dict(quote=QUOTE,video_path=videos[0]['path'],duration=5,shade=.1,quote_size=68,credit_size=26,
                 outline_enabled=True,outline_color='#101018',outline_width=7,outline_blur=10,outline_opacity=.9)
    plan=request('/api/plan',payload)
    off=request('/api/plan',{**payload,'outline_enabled':False})
    assert plan['plan_id']!=off['plan_id']
    def overlay(p):return Image.open(io.BytesIO(request('/api/overlay/'+p['plan_id']+'/0'))).convert('RGBA')
    on_image,off_image=overlay(plan),overlay(off)
    assert ImageChops.difference(on_image,off_image).convert('RGB').getbbox()
    zero=request('/api/plan',{**payload,'outline_opacity':0})
    assert overlay(zero).tobytes()==off_image.tobytes()
    white=request('/api/plan',{**payload,'outline_color':'#FFFFFF'})
    assert white['settings']['outline_color']=='#ffffff'
    assert ImageChops.difference(overlay(white),on_image).convert('RGB').getbbox()
    report=[]
    out=ROOT/'output_videos'/'verification';out.mkdir(exist_ok=True)
    for preview in [True,False]:
        job=request('/api/preview' if preview else '/api/render',{'plan_id':plan['plan_id'],'async':True})
        deadline=time.monotonic()+600
        while job['status'] not in ['done','error']:
            assert time.monotonic()<deadline
            time.sleep(.6);job=request('/api/jobs/'+job['job_id'])
        assert job['status']=='done',job
        result=job['result']
        src=ROOT/('.cache/previews' if preview else 'output_videos')/result['filename']
        target=out/('v4_soft_outline_preview.mp4' if preview else 'v4_soft_outline_fullhd.mp4')
        shutil.copy2(src,target)
        metadata=probe(target)
        assert (metadata['width'],metadata['height'])==((540,960) if preview else (1080,1920))
        assert abs(metadata['duration']-plan['duration'])<.1
        check=run_media([tool_path('ffmpeg'),'-v','error','-i',str(target),'-f','null','-'],capture_output=True)
        assert check.returncode==0,check.stderr
        report.append(dict(file=target.name,probe=metadata,result=result))
        print('Verified',target.name,metadata,flush=True)
    review=ROOT/'test_renders'/'verification'
    run_media([tool_path('ffmpeg'),'-y','-v','error','-ss','1.2','-i',str(target),'-frames:v','1',str(review/'v4_outline_export.jpg')],check=True,capture_output=True)
    (review/'v4_outline_report.json').write_text(json.dumps(dict(plan=plan,videos=report),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Outline API and render verification passed.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base');args=parser.parse_args()
    make_sheet()
    if args.base:verify(args.base)
