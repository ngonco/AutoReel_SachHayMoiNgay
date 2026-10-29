"""Isolated v12 launcher, scrolling pixels, preview/export and persistence verification."""
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
from core.media import tool_path, run_media, probe
from core.scroll_text import scroll_frame
from core.settings import save_settings_patch
from verify_v5 import api, wait_job

ROOT=Path(__file__).resolve().parent
QUOTE='Cứ mong mọi điều tốt đẹp cho mọi người thật lòng, rồi hạnh phúc sẽ đến với mình rất tự nhiên.\n\nSống chậm một chút, giữ lòng biết ơn và trao nhau những điều tử tế.'


def prepare():
    workspace=ROOT/'.cache'/f'v12_smoke_{time.time_ns()}'
    clips=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC';clips.mkdir(parents=True)
    for index,color in enumerate(('#142332','#203040','#263c32','#1c3037')):
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i',f'color=c={color}:s=180x320:r=30:d=3',
                   '-c:v','libx264','-pix_fmt','yuv420p',str(clips/f'{index}.mp4')],check=True,capture_output=True)
    music=workspace/'CLIP TƯỢNG PHẬT LQ'/'NHẠC NỀN';music.mkdir()
    run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i','sine=frequency=330:duration=3',
               '-c:a','libmp3lame',str(music/'Test tone.mp3')],check=True,capture_output=True)
    (workspace/'quotes.txt').write_text(QUOTE.replace('\n',' ')+'\nBình an mỗi ngày.',encoding='utf-8')
    save_settings_patch(workspace,dict(theme_index=5,scroll_speed=1.,quote=QUOTE,duration=1,
                                     music_mode='selected',music_path=str(music/'Test tone.mp3')))
    return workspace


def launch(workspace,source=False,port=8898):
    args=[sys.executable,str(ROOT/'app.py')] if source else ['wscript.exe',str(ROOT/'Mo_App_Auto_Reel.vbs')]
    args+=['--workspace',str(workspace),'--port',str(port),'--headless','--no-sheet-sync']
    temp=workspace/'tmp';temp.mkdir(exist_ok=True)
    env={**os.environ,'TEMP':str(temp),'TMP':str(temp)}
    with (workspace/'launcher.log').open('a',encoding='utf-8') as log:
        subprocess.Popen(args,stdout=log,stderr=log,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
    base=f'http://127.0.0.1:{port}';deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            health=api(base,'/api/health');process=psutil.Process(health['pid'])
            assert health['version']=='multi-scene-v12' and str(workspace) in process.cmdline()
            if not source:assert Path(process.exe()).name=='AutoReelSachHay_v12.exe'
            return base,health['pid']
        except OSError:time.sleep(.3)
    raise TimeoutError('V12 launcher did not start')


def stop_owned(pid,workspace):
    process=psutil.Process(pid);assert str(workspace) in process.cmdline()
    parent=process.parent();owned=[process,*process.children(recursive=True)]
    if parent and Path(parent.exe()).name=='AutoReelSachHay_v12.exe' and str(workspace) in parent.cmdline():owned.append(parent)
    for child in owned:
        try:child.terminate()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(owned,timeout=10)


def check(base,workspace,fullhd=False):
    settings=api(base,'/api/settings')
    payload={**settings,'quote':QUOTE,'theme_index':5,'scroll_speed':1.}
    plan=api(base,'/api/plan',payload);track=plan['text_track']
    assert plan['segmentation_mode']=='continuous_scroll' and '\n\n' in plan['quote']
    assert track['distance']>0 and len(plan['scenes'])>=2
    original=(workspace/'footage_usage.json').read_bytes()
    for asset in ('mask','0',str(track['tiles'][-1]['index'])):
        with urllib.request.urlopen(f'{base}/api/scroll_asset/{plan["plan_id"]}/{asset}') as response:
            Image.open(io.BytesIO(response.read())).load()
    for i in range(len(plan['scenes'])):
        with urllib.request.urlopen(f'{base}/api/overlay/{plan["plan_id"]}/{i}') as response:
            image=Image.open(io.BytesIO(response.read())).convert('RGBA')
            bbox=image.getbbox();assert bbox and bbox[0]>=119 and bbox[1]>=1325 and bbox[2]<=961 and bbox[3]<=1581
    api(base,'/api/draft_prepare',dict(plan_id=plan['plan_id'],selected_scene=0))
    preview=wait_job(base,api(base,'/api/preview',dict(plan_id=plan['plan_id'])))
    assert (workspace/'footage_usage.json').read_bytes()==original,'Preview consumed footage'
    for name in ('index.html','app.js','scroll_player.js','draft_player.js','style.css'):
        with urllib.request.urlopen(base+'/'+name) as response:assert response.read()==(ROOT/'ui'/name).read_bytes(),name
    report=dict(workspace=str(workspace),plan_id=plan['plan_id'],duration=plan['duration'],footage=len(plan['scenes']),
                preview=preview,preview_preserves_history=True,exact_ui=True)
    if fullhd:
        result=wait_job(base,api(base,'/api/render',dict(plan_id=plan['plan_id'],**{'async':True})))
        output=workspace/'output_videos'/result['filename'];info=probe(output)
        assert (info['width'],info['height'])==(1080,1920)
        run_media([tool_path('ffmpeg'),'-v','error','-i',str(output),'-f','null','-'],check=True,capture_output=True)
        rect=track['rect'];scores=[]
        samples=[1.,plan['scenes'][1]['text_start'],plan['duration']/2,plan['duration']-1]
        for index,t in enumerate(samples):
            # Input seek returns the first frame on or after the requested timestamp.
            frame_time=int(t*30+.999999)/30
            raw=run_media([tool_path('ffmpeg'),'-v','error','-ss',str(frame_time),'-i',str(output),'-frames:v','1','-f','image2pipe','-vcodec','png','-'],check=True,capture_output=True).stdout
            frame=Image.open(io.BytesIO(raw)).convert('RGB');frame.save(workspace/f'frame-{index}.png')
            crop=np.array(frame.crop((rect['x'],rect['y'],rect['x']+rect['width'],rect['y']+rect['height'])))
            expected=np.array(scroll_frame(track,frame_time,workspace))[:,:,3]>.8*255
            white=np.min(crop,axis=2)>180
            score=float(np.sum(white&expected)/max(1,np.sum(expected)));assert score>.87,(t,score)
            scores.append(score)
            # Encoded glyphs never escape the fixed viewport, even at transitions.
            all_white=np.min(np.array(frame),axis=2)>180
            all_white[rect['y']:rect['y']+rect['height'],rect['x']:rect['x']+rect['width']]=False
            assert not all_white.any()
        pcm=run_media([tool_path('ffmpeg'),'-v','error','-ss','1','-i',str(output),'-t','1','-f','f32le','-ac','1','-ar','48000','-'],check=True,capture_output=True).stdout
        rms=float(np.sqrt(np.mean(np.frombuffer(pcm,dtype=np.float32)**2)));assert rms>.01
        history=json.loads((workspace/'footage_usage.json').read_text())
        assert sum(history['counts'].values())==len(plan['scenes'])
        report.update(export=result,matched_text_pixels=scores,audio_rms=rms,export_counts=True)
        short=api(base,'/api/plan',{**payload,'quote':'Bình an mỗi ngày.','credit':'','duration':4,'music_mode':'none'})
        assert short['text_track']['distance']==0
        short_result=wait_job(base,api(base,'/api/render',dict(plan_id=short['plan_id'],**{'async':True})))
        report['short_static_export']=short_result
        longer=api(base,'/api/plan',{**payload,'quote':QUOTE+'\n'+QUOTE})
        assert len(longer['scenes'])>4
        before_long=json.loads((workspace/'footage_usage.json').read_text())['counts']
        long_preview=wait_job(base,api(base,'/api/preview',dict(plan_id=longer['plan_id'])))
        assert json.loads((workspace/'footage_usage.json').read_text())['counts']==before_long
        report['more_than_four_footage_preview']=long_preview
    # Actual normalized restart data, including legacy settings, on the isolated profile only.
    api(base,'/api/settings',dict(theme_index=5,scroll_speed=.8,quote=QUOTE,quote_size=84,vertical_offset=-100))
    restored=api(base,'/api/settings');assert restored['scroll_speed']==.8 and restored['quote']==QUOTE
    for index in range(5):
        old=api(base,'/api/plan',{**payload,'theme_index':index,'quote':'Bình an mỗi ngày.'})
        assert 'text_track' not in old
        with urllib.request.urlopen(f'{base}/api/overlay/{old["plan_id"]}/0') as response:Image.open(io.BytesIO(response.read())).load()
    report['five_legacy_styles']=True
    (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');parser.add_argument('--hold',action='store_true');parser.add_argument('--fullhd',action='store_true')
    args=parser.parse_args();workspace=prepare();base,pid=launch(workspace,args.source)
    active=dict(workspace=str(workspace),base=base,pid=pid)
    (ROOT/'.cache/v12_active.json').write_text(json.dumps(active),encoding='utf-8')
    print('WORKSPACE',workspace,flush=True)
    try:
        report=check(base,workspace,args.fullhd)
        stop_owned(pid,workspace)
        base,pid=launch(workspace,args.source)
        restored=api(base,'/api/settings')
        assert restored['theme_index']==5 and restored['scroll_speed']==.8 and restored['quote']==QUOTE
        assert restored['quote_size']==84 and restored['vertical_offset']==-100
        report['restart_persistence']=True
        active.update(pid=pid)
        (ROOT/'.cache/v12_active.json').write_text(json.dumps(active),encoding='utf-8')
        (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False),flush=True)
    finally:
        if not args.hold:stop_owned(pid,workspace)


if __name__=='__main__':main()
