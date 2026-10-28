"""Isolated source/packaged smoke checks for scene choices and reusable draft media."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import shutil
import time
import urllib.request
from io import BytesIO
from PIL import Image, ImageChops, ImageStat
import psutil
from core.media import run_media, tool_path, probe
from core.renderer import scene_overlay
from core.settings import save_settings_patch
from core.music_library import music_folder
from verify_v5 import api, wait_job

ROOT=Path(__file__).resolve().parent


def prepare():
    workspace=ROOT/'.cache'/f'v10_smoke_{time.time_ns()}'
    clips=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC';clips.mkdir(parents=True)
    for index,hue in enumerate((0,60,120,180)):
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i','testsrc2=s=180x320:r=30:d=3',
                   '-vf',f'hue=h={hue}','-c:v','libx264','-pix_fmt','yuv420p',str(clips/f'{index}.mp4')],check=True,capture_output=True)
    music=music_folder(workspace,{});music.mkdir(parents=True)
    for index in range(2):
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i',f'sine=frequency={220+index*110}:duration=3',
                   '-c:a','libmp3lame',str(music/f'Test music {index}.mp3')],check=True,capture_output=True)
    actual=next(iter(music_folder(ROOT,{}).glob('*.mp3')),None)
    if actual:shutil.copy2(actual,music/actual.name)
    (workspace/'quotes.txt').write_text('Câu đầu tiên.\nCâu tiếp theo.\n',encoding='utf-8')
    save_settings_patch(workspace,dict(quote='Chỉ những người tu đến mức không thấy mình quan trọng nữa.\nHãy giữ lòng bình an.',duration=1))
    return workspace


def launch(workspace,source=False,port=8898):
    args=[sys.executable,str(ROOT/'app.py')] if source else ['wscript.exe',str(ROOT/'Mo_App_Auto_Reel.vbs')]
    args+=['--workspace',str(workspace),'--port',str(port),'--no-sheet-sync','--headless']
    log=(workspace/'launcher.log').open('a',encoding='utf-8')
    process=subprocess.Popen(args,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    log.close();base=f'http://127.0.0.1:{port}'
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            health=api(base,'/api/health');owned=psutil.Process(health['pid'])
            assert str(workspace) in owned.cmdline()
            assert health['version']=='multi-scene-v10',health
            if not source:assert Path(owned.exe()).name=='AutoReelSachHay_v10.exe'
            return base,health['pid']
        except OSError:time.sleep(.3)
    raise TimeoutError('V10 launcher did not start')


def stop_owned(pid,workspace):
    process=psutil.Process(pid);assert str(workspace) in process.cmdline()
    parent=process.parent();owned=[process,*process.children(recursive=True)]
    if parent and Path(parent.exe()).name=='AutoReelSachHay_v10.exe' and str(workspace) in parent.cmdline():owned.append(parent)
    for child in owned:
        try:child.terminate()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(owned,timeout=10)


def ready(base,plan,index=0):
    start=time.monotonic();snapshot=api(base,'/api/draft_prepare',dict(plan_id=plan['plan_id'],selected_scene=index))
    while not all(s['status']=='ready' for s in snapshot['scenes']):
        assert not any(s['status']=='error' for s in snapshot['scenes']),snapshot
        if time.monotonic()-start>180:raise TimeoutError(snapshot)
        time.sleep(.1);snapshot=api(base,'/api/draft_status/'+plan['plan_id'])
    return snapshot,time.monotonic()-start


def frame(path,time_point,target):
    run_media([tool_path('ffmpeg'),'-y','-v','error','-ss',str(time_point),'-i',str(path),'-frames:v','1',str(target)],check=True,capture_output=True)
    return Image.open(target).convert('RGB')


def check_real(base,workspace,source,fullhd):
    payload=dict(quote='Chỉ những người tu đến mức không thấy mình quan trọng nữa.',duration=1,
                 auto_paginate=False,video_path=str(Path(source).resolve()),music_seed='real-mov')
    plan=api(base,'/api/plan',payload);assert plan['scenes'][0]['video_path']==str(Path(source).resolve())
    before=api(base,'/api/download_history');media,cold=ready(base,plan)
    proxy=workspace/'.cache'/'draft_media'/(media['scenes'][0]['key']+'.mp4')
    run_media([tool_path('ffmpeg'),'-v','error','-i',str(proxy),'-f','null','-'],check=True,capture_output=True)
    report=dict(real_source=Path(source).name,proxy_seconds=round(cold,3),rotation_proxy=probe(proxy))
    if fullhd:
        exported=wait_job(base,api(base,'/api/render',dict(plan_id=plan['plan_id'],**{'async':True})))
        output=workspace/'output_videos'/exported['filename'];run_media([tool_path('ffmpeg'),'-v','error','-i',str(output),'-f','null','-'],check=True,capture_output=True)
        time_point=2.;scene=plan['scenes'][0]
        background=frame(proxy,scene['source_start']+time_point*scene['speed'],workspace/'real_proxy_frame.png').resize((360,640)).convert('RGBA')
        overlay=scene_overlay(plan,scene,str(workspace)).resize((360,640),Image.Resampling.LANCZOS)
        composed=Image.alpha_composite(background,overlay).convert('RGB');composed.save(workspace/'real_live_composite.png')
        hd=frame(output,time_point,workspace/'real_fullhd_frame.png').resize((360,640),Image.Resampling.LANCZOS)
        report['mean_rgb_difference']=sum(ImageStat.Stat(ImageChops.difference(composed,hd)).mean)/3
        report['export']=exported
        assert report['mean_rgb_difference']<20,report
    assert api(base,'/api/download_history')==before
    (workspace/'real_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def check(base,workspace,fullhd=False):
    videos=api(base,'/api/videos');settings=api(base,'/api/settings')
    payload=dict(quote=settings['quote'],duration=1,pos_mode='bottom')
    plan=api(base,'/api/plan',payload)
    history=workspace/'footage_usage.json';before=json.loads(history.read_text())
    media,cold=ready(base,plan)
    music=api(base,'/api/music');assert len(music['tracks'])>=2
    assert plan['music'] and plan['music_url'] and plan['music_details']['name']
    request=urllib.request.Request(base+plan['music_url'],headers={'Range':'bytes=0-31'})
    with urllib.request.urlopen(request) as response:assert response.status==206 and len(response.read())==32
    random_other=api(base,'/api/plan',{**payload,'previous_music_path':plan['music']['path'],'music_seed':'new-seed'})
    assert random_other['music']['path']!=plan['music']['path']
    for item in media['scenes']:
        path=workspace/'.cache'/'draft_media'/(item['key']+'.mp4')
        info=probe(path);assert (info['width'],info['height'])==(360,640)
        run_media([tool_path('ffmpeg'),'-v','error','-i',str(path),'-f','null','-'],check=True,capture_output=True)
        request=urllib.request.Request(base+item['url'],headers={'Range':'bytes=0-31'})
        with urllib.request.urlopen(request) as response:assert response.status==206 and len(response.read())==32
    after=json.loads(history.read_text());assert before['counts']==after['counts'] and before.get('last_export')==after.get('last_export')
    assert not list((workspace/'.cache'/'previews').glob('*.mp4'))
    choices=plan['footage_pool']['scene_choices'][1]
    current=plan['scenes'][1]['video_path'];replacement=next(c for c in choices if c['eligible'] and c['path']!=current)
    preferred={'1':dict(path=replacement['path'],text=plan['scenes'][1]['text'])}
    changed=api(base,'/api/plan',{**payload,'scene_video_preferences':preferred})
    assert changed['scenes'][1]['video_path']==replacement['path']
    assert changed['scenes'][1]['suggestion']['accepted']
    assert changed['scenes'][1]['overlay_key']==plan['scenes'][1]['overlay_key']
    save=api(base,'/api/settings',dict(scene_video_preferences=preferred))
    assert save['settings']['scene_video_preferences']==preferred
    _,warm=ready(base,changed,1)
    for theme in range(5):
        themed=api(base,'/api/plan',{**payload,'theme_index':theme,'scene_video_preferences':preferred})
        for scene in themed['scenes']:
            with urllib.request.urlopen(base+f'/api/overlay/{themed["plan_id"]}/{scene["index"]}') as response:
                actual=Image.open(BytesIO(response.read())).convert('RGBA')
            expected=scene_overlay(themed,scene,str(workspace));assert ImageChops.difference(actual,expected).getbbox() is None
    exported=None
    if fullhd:
        exported=wait_job(base,api(base,'/api/render',dict(plan_id=changed['plan_id'],**{'async':True})))
        output=workspace/'output_videos'/exported['filename'];info=probe(output)
        assert (info['width'],info['height'])==(1080,1920)
        run_media([tool_path('ffmpeg'),'-v','error','-i',str(output),'-f','null','-'],check=True,capture_output=True)
        assert api(base,'/api/download_history')['records']==[],'Render success alone must not mark a quote downloaded'
    report=dict(workspace=str(workspace),base=base,cold_proxy_seconds=round(cold,3),warm_prepare_seconds=round(warm,3),
                scenes=len(plan['scenes']),range=True,preview_turns_unchanged=True,themes=5,music_tracks=len(music['tracks']),export=exported)
    (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');parser.add_argument('--hold',action='store_true');parser.add_argument('--fullhd',action='store_true');parser.add_argument('--real-source')
    args=parser.parse_args();workspace=prepare();base,pid=launch(workspace,args.source)
    (ROOT/'.cache'/'v10_active.json').write_text(json.dumps(dict(workspace=str(workspace),base=base,pid=pid)),encoding='utf-8')
    print('WORKSPACE',workspace,flush=True)
    try:
        print(json.dumps(check(base,workspace,args.fullhd),ensure_ascii=False),flush=True)
        if args.real_source:print(json.dumps(check_real(base,workspace,args.real_source,args.fullhd),ensure_ascii=False),flush=True)
    finally:
        if not args.hold:stop_owned(pid,workspace)


if __name__=='__main__':main()
