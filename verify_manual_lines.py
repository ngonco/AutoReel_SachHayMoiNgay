"""Integration check for explicit line scenes and wider Y through a running app/EXE."""
import argparse
import json
from pathlib import Path
import shutil
import time
import urllib.request
from core.media import probe, run_media, tool_path

ROOT=Path(__file__).resolve().parent
LINES=[
    'Hạnh phúc không phải đến từ việc yêu thương bản thân,',
    'mà là kết quả của việc ta đã yêu thương con người rất nhiều',
    'và đã nỗ lực mang hạnh phúc đến cho con người.'
]


def verify(base):
    def api(route,body=None):
        request=urllib.request.Request(base+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=180) as response:return json.load(response)
    videos=api('/api/videos')
    text='\r\n  '+LINES[0]+'\r\n\r\n'+LINES[1]+'\r\n'+LINES[2]+'  \r\n'
    for auto in [True,False]:
        plan=api('/api/plan',dict(quote=text,video_path=videos[0]['path'],auto_paginate=auto))
        assert [s['text'] for s in plan['scenes']]==LINES
        assert plan['quote']=='\n'.join(LINES)
        assert plan['segmentation_mode']=='manual_lines'
    for y in [-1600,-900,650,1200,1600]:
        p=api('/api/plan',dict(quote=text,video_path=videos[0]['path'],vertical_offset=y))
        assert p['settings']['vertical_offset']==y
    print('Manual boundaries and Y API checks passed.',flush=True)
    report=[]
    out=ROOT/'output_videos'/'verification';out.mkdir(exist_ok=True)
    review=ROOT/'test_renders'/'verification';review.mkdir(exist_ok=True)
    for preview in [True,False]:
        route='/api/preview' if preview else '/api/render'
        job=api(route,{'plan_id':plan['plan_id'],'async':True})
        deadline=time.monotonic()+600
        while job['status'] not in ['done','error']:
            assert time.monotonic()<deadline,'Timed out'
            time.sleep(.7)
            job=api('/api/jobs/'+job['job_id'])
        assert job['status']=='done',job
        result=job['result']
        source=ROOT/('.cache/previews' if preview else 'output_videos')/result['filename']
        target=out/('v3_manual_lines_preview.mp4' if preview else 'v3_manual_lines_fullhd.mp4')
        shutil.copy2(source,target)
        info=probe(target)
        assert (info['width'],info['height'])==((540,960) if preview else (1080,1920))
        assert abs(info['duration']-plan['duration'])<.1
        check=run_media([tool_path('ffmpeg'),'-v','error','-i',str(target),'-f','null','-'],capture_output=True)
        assert check.returncode==0,check.stderr
        report.append(dict(file=target.name,probe=info,result=result))
        print('Verified',target.name,info,flush=True)
    for i,scene in enumerate(plan['scenes']):
        check=run_media([tool_path('ffmpeg'),'-y','-v','error','-ss',str(scene['text_start']+1),'-i',str(target),'-frames:v','1',str(review/f'v3_manual_scene_{i+1}.jpg')],capture_output=True)
        assert check.returncode==0
    (review/'v3_manual_report.json').write_text(json.dumps(dict(plan=plan,videos=report),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Manual integration complete.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',required=True);args=parser.parse_args();verify(args.base)
