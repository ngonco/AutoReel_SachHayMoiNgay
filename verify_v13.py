"""Isolated adjustable scroll verification through source or the packaged launcher."""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

import numpy as np
from PIL import Image
import psutil
from core.media import run_media,tool_path,probe
from core.scroll_text import scroll_frame,FRAME_BOTTOM
from core.settings import save_settings_patch
from verify_v5 import api,wait_job
from verify_v12 import QUOTE

ROOT=Path(__file__).resolve().parent
CUSTOM=dict(scroll_quote_size=64,scroll_lines=5,scroll_outline_enabled=True,
            scroll_outline_color='#1f2f55',scroll_outline_width=5,scroll_outline_blur=10,
            scroll_outline_opacity=.7,scroll_fade_top=0,scroll_fade_bottom=72)


def prepare():
    workspace=ROOT/'.cache'/f'v13_smoke_{time.time_ns()}'
    clips=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC';clips.mkdir(parents=True)
    for i,color in enumerate(('#142332','#203040','#263c32','#1c3037')):
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i',f'color=c={color}:s=180x320:r=30:d=3',
                   '-c:v','libx264','-pix_fmt','yuv420p',str(clips/f'{i}.mp4')],capture_output=True,check=True)
    music=clips.parent/'NHẠC NỀN';music.mkdir()
    run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i','sine=frequency=330:duration=3',
               '-c:a','libmp3lame',str(music/'Test tone.mp3')],capture_output=True,check=True)
    (workspace/'quotes.txt').write_text(QUOTE.replace('\n',' ')+'\nBình an mỗi ngày.',encoding='utf-8')
    save_settings_patch(workspace,dict(theme_index=5,quote=QUOTE,duration=1,music_mode='selected',
                                     music_path=str(music/'Test tone.mp3'),quote_size=84,vertical_offset=-100))
    return workspace


def launch(workspace,source=False,port=8899):
    args=[sys.executable,str(ROOT/'app.py')] if source else ['wscript.exe',str(ROOT/'Mo_App_Auto_Reel.vbs')]
    args+=['--workspace',str(workspace),'--port',str(port),'--headless','--no-sheet-sync']
    temp=workspace/'tmp';temp.mkdir(exist_ok=True)
    with (workspace/'launcher.log').open('a',encoding='utf-8') as log:
        subprocess.Popen(args,stdout=log,stderr=log,env={**os.environ,'TEMP':str(temp),'TMP':str(temp)},creationflags=subprocess.CREATE_NO_WINDOW)
    base=f'http://127.0.0.1:{port}';deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            h=api(base,'/api/health');p=psutil.Process(h['pid'])
            assert h['version']=='multi-scene-v13' and str(workspace) in p.cmdline()
            if not source:assert Path(p.exe()).name=='AutoReelSachHay_v13.exe'
            return base,h['pid']
        except OSError:time.sleep(.3)
    raise TimeoutError('V13 did not start through launcher')


def stop_owned(pid,workspace):
    process=psutil.Process(pid);assert str(workspace) in process.cmdline()
    parent=process.parent();owned=[process,*process.children(recursive=True)]
    if parent and Path(parent.exe()).name=='AutoReelSachHay_v13.exe' and str(workspace) in parent.cmdline():owned.append(parent)
    for item in owned:
        try:item.terminate()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(owned,timeout=10)


def check(base,workspace,fullhd):
    settings=api(base,'/api/settings')
    assert settings['scroll_quote_size']==48 and settings['scroll_lines']==5
    default=api(base,'/api/plan',{**settings,'quote':QUOTE})
    assert default['text_track']['visible_lines']==5
    api(base,'/api/settings',CUSTOM)
    settings=api(base,'/api/settings')
    for key,value in CUSTOM.items():assert settings[key]==value,key
    plan=api(base,'/api/plan',{**settings,'quote':QUOTE});track=plan['text_track'];rect=track['rect']
    assert track['font_sizes']['quote']==64 and track['visible_lines']==5 and track['distance']>0
    assert rect['height']>default['text_track']['rect']['height'] and rect['y']+rect['height']==FRAME_BOTTOM
    assert default['text_track']['asset_key']!=track['asset_key']
    for size,rows in ((28,2),(28,8),(80,2),(80,8)):
        edge=api(base,'/api/plan',{**settings,'quote':QUOTE,'scroll_quote_size':size,'scroll_lines':rows,
                                 'scroll_outline_width':16,'scroll_outline_blur':24,'scroll_fade_top':96,'scroll_fade_bottom':96})
        assert edge['text_track']['rect']['y']>=180 and edge['text_track']['rect']['y']+edge['text_track']['rect']['height']==FRAME_BOTTOM
    for name in ('index.html','app.js','scroll_player.js','draft_player.js','style.css'):
        with urllib.request.urlopen(base+'/'+name) as response:assert response.read()==(ROOT/'ui'/name).read_bytes(),name
    with urllib.request.urlopen(f'{base}/api/scroll_asset/{plan["plan_id"]}/mask') as response:
        mask=Image.open(io.BytesIO(response.read())).convert('RGBA')
        assert mask.size==(rect['width'],rect['height']) and mask.getpixel((0,0))[3]==255 and mask.getpixel((0,mask.height-1))[3]==0
    for scene in plan['scenes']:
        with urllib.request.urlopen(f'{base}/api/overlay/{plan["plan_id"]}/{scene["index"]}') as response:
            picture=Image.open(io.BytesIO(response.read()));bbox=picture.getbbox()
            assert bbox and bbox[0]>=rect['x'] and bbox[1]>=rect['y'] and bbox[2]<=rect['x']+rect['width'] and bbox[3]<=FRAME_BOTTOM
    history=(workspace/'footage_usage.json').read_bytes()
    preview=wait_job(base,api(base,'/api/preview',dict(plan_id=plan['plan_id'])))
    assert (workspace/'footage_usage.json').read_bytes()==history
    report=dict(workspace=str(workspace),default_five_lines=True,extreme_controls_safe=True,custom= CUSTOM,
                rect=rect,preview=preview,preview_preserves_history=True,exact_ui=True)
    if fullhd:
        result=wait_job(base,api(base,'/api/render',dict(plan_id=plan['plan_id'],**{'async':True})))
        output=workspace/'output_videos'/result['filename'];info=probe(output)
        assert (info['width'],info['height'])==(1080,1920)
        run_media([tool_path('ffmpeg'),'-v','error','-i',str(output),'-f','null','-'],check=True,capture_output=True)
        scores=[]
        for index,t in enumerate((1.,plan['scenes'][1]['text_start'],plan['duration']/2,plan['duration']-1)):
            t=int(t*30+.999999)/30
            raw=run_media([tool_path('ffmpeg'),'-v','error','-ss',str(t),'-i',str(output),'-frames:v','1','-f','image2pipe','-vcodec','png','-'],check=True,capture_output=True).stdout
            image=Image.open(io.BytesIO(raw)).convert('RGB');image.save(workspace/f'frame-{index}.png')
            pixels=np.array(image);region=pixels[rect['y']:FRAME_BOTTOM,rect['x']:rect['x']+rect['width']]
            expected=np.array(scroll_frame(track,t,workspace))[:,:,3]>220
            score=float(np.mean(np.min(region,axis=2)[expected]>180));assert score>.87,(t,score)
            scores.append(score)
            outside=np.min(pixels,axis=2)>180;outside[rect['y']:FRAME_BOTTOM,rect['x']:rect['x']+rect['width']]=False
            assert not outside.any()
        pcm=run_media([tool_path('ffmpeg'),'-v','error','-ss','1','-i',str(output),'-t','1','-f','f32le','-ac','1','-ar','48000','-'],check=True,capture_output=True).stdout
        rms=float(np.sqrt(np.mean(np.frombuffer(pcm,dtype=np.float32)**2)));assert rms>.01
        report.update(export=result,matched_text_pixels=scores,audio_rms=rms)
    assert api(base,'/api/settings')['quote_size']==84 and api(base,'/api/settings')['vertical_offset']==-100
    for index in range(5):
        old=api(base,'/api/plan',{**settings,'theme_index':index,'quote':'Bình an mỗi ngày.'})
        assert 'text_track' not in old
        with urllib.request.urlopen(f'{base}/api/overlay/{old["plan_id"]}/0') as response:Image.open(io.BytesIO(response.read())).load()
    report['legacy_styles_preserved']=True
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');parser.add_argument('--hold',action='store_true');parser.add_argument('--fullhd',action='store_true')
    args=parser.parse_args();workspace=prepare();base,pid=launch(workspace,args.source)
    active=dict(workspace=str(workspace),base=base,pid=pid)
    (ROOT/'.cache/v13_active.json').write_text(json.dumps(active),encoding='utf-8')
    print('WORKSPACE',workspace,flush=True)
    try:
        report=check(base,workspace,args.fullhd)
        stop_owned(pid,workspace);base,pid=launch(workspace,args.source)
        restored=api(base,'/api/settings')
        for key,value in CUSTOM.items():assert restored[key]==value,key
        report['restart_persistence']=True;active['pid']=pid
        (ROOT/'.cache/v13_active.json').write_text(json.dumps(active),encoding='utf-8')
        (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False),flush=True)
    finally:
        if not args.hold:stop_owned(pid,workspace)


if __name__=='__main__':main()
