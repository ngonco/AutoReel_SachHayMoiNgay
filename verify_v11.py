"""V11 isolated startup, manual status, soundtrack PCM and no-bell packaging checks."""
import argparse
from array import array
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import psutil
from core.media import tool_path,run_media,probe
from core.music_library import music_folder
from core.settings import save_settings_patch
from verify_v5 import api,wait_job

ROOT=Path(__file__).resolve().parent


def prepare():
    workspace=ROOT/'.cache'/f'v11_smoke_{time.time_ns()}'
    clips=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC';clips.mkdir(parents=True)
    for index,hue in enumerate((0,90)):
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i','testsrc2=s=180x320:r=30:d=3',
                   '-vf',f'hue=h={hue}','-c:v','libx264','-pix_fmt','yuv420p',str(clips/f'{index}.mp4')],check=True,capture_output=True)
    music=music_folder(workspace,{});music.mkdir(parents=True)
    run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i','sine=frequency=330:duration=3',
               '-c:a','libmp3lame',str(music/'Test tone.mp3')],check=True,capture_output=True)
    actual=next(iter(music_folder(ROOT,{}).glob('*.mp3')),None)
    if actual:shutil.copy2(actual,music/actual.name)
    (workspace/'quotes.txt').write_text('Bình an mỗi ngày.\nLuôn giữ lòng biết ơn.\n',encoding='utf-8')
    save_settings_patch(workspace,dict(quote='Bản nháp trước.\nGiữ dòng này.',duration=1,music_mode='selected',music_path=str((music/'Test tone.mp3').resolve())))
    return workspace


def launch(workspace,source=False,port=8899):
    args=[sys.executable,str(ROOT/'app.py')] if source else ['wscript.exe',str(ROOT/'Mo_App_Auto_Reel.vbs')]
    args+=['--workspace',str(workspace),'--port',str(port),'--headless','--no-sheet-sync']
    with (workspace/'launcher.log').open('a',encoding='utf-8') as log:
        subprocess.Popen(args,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    base=f'http://127.0.0.1:{port}';deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            health=api(base,'/api/health');process=psutil.Process(health['pid'])
            assert health['version']=='multi-scene-v11' and str(workspace) in process.cmdline()
            if not source:assert Path(process.exe()).name=='AutoReelSachHay_v11.exe'
            return base,health['pid']
        except OSError:time.sleep(.3)
    raise TimeoutError('V11 launcher did not start')


def stop_owned(pid,workspace):
    process=psutil.Process(pid);assert str(workspace) in process.cmdline()
    parent=process.parent();owned=[process,*process.children(recursive=True)]
    if parent and Path(parent.exe()).name=='AutoReelSachHay_v11.exe' and str(workspace) in parent.cmdline():owned.append(parent)
    for child in owned:
        try:child.terminate()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(owned,timeout=10)


def check(base,workspace,fullhd=False):
    quotes=api(base,'/api/quote_catalog')['quotes'];videos=api(base,'/api/videos')
    plan=api(base,'/api/plan',dict(quote=quotes[1]['quote'],duration=1,music_mode='selected',music_path=str(music_folder(workspace,{})/'Test tone.mp3')))
    footage_before=(workspace/'footage_usage.json').read_bytes();draft_before=(workspace/'session_state.json').read_bytes()
    marked=api(base,'/api/mark_quote_downloaded',dict(quote=quotes[0]['quote'],downloaded=True))
    assert [q['downloaded'] for q in marked['quotes']]==[True,False]
    assert marked['download_history']['records'][0]['count']==0 and marked['download_history']['records'][0]['last_downloaded_at'] is None
    assert api(base,'/api/startup_quote',{})['index']==1
    repeated=api(base,'/api/mark_quote_downloaded',dict(quote=quotes[0]['quote'],downloaded=True))
    assert repeated['download_history']['revision']==marked['download_history']['revision']
    unmarked=api(base,'/api/mark_quote_downloaded',dict(quote=quotes[0]['quote'],downloaded=False))
    assert not unmarked['quotes'][0]['downloaded'] and api(base,'/api/startup_quote',{})['index']==0
    api(base,'/api/mark_quote_downloaded',dict(quote=quotes[0]['quote'],downloaded=True))
    assert (workspace/'footage_usage.json').read_bytes()==footage_before
    assert (workspace/'session_state.json').read_bytes()==draft_before
    for name in ('index.html','app.js','draft_player.js','style.css'):
        with urllib.request.urlopen(base+'/'+name) as response:packed=response.read()
        assert packed==(ROOT/'ui'/name).read_bytes(),name
    with urllib.request.urlopen(base+'/index.html') as response:html=response.read().decode()
    assert 'btnTestAudio' not in html and 'Chuông thiền' not in html
    try:urllib.request.urlopen(base+'/assets/thien_chuong.wav')
    except urllib.error.HTTPError as error:assert error.code==404
    else:raise AssertionError('Legacy bell endpoint must be removed')
    pcm=run_media([tool_path('ffmpeg'),'-v','error','-ss','1','-i',plan['music']['path'],'-t','1','-f','f32le','-ac','1','-ar','48000','-'],capture_output=True,check=True).stdout
    samples=array('f');samples.frombytes(pcm);source_rms=math.sqrt(sum(v*v for v in samples)/len(samples));assert source_rms>.01
    report=dict(workspace=str(workspace),manual_mark_unmark=True,idempotent=True,no_footage_or_draft_changes=True,
                source_rms=source_rms,bell_endpoint_removed=True,exact_ui=True)
    if fullhd:
        result=wait_job(base,api(base,'/api/render',dict(plan_id=plan['plan_id'],**{'async':True})))
        output=workspace/'output_videos'/result['filename'];info=probe(output);assert (info['width'],info['height'])==(1080,1920)
        run_media([tool_path('ffmpeg'),'-v','error','-i',str(output),'-f','null','-'],capture_output=True,check=True)
        pcm=run_media([tool_path('ffmpeg'),'-v','error','-ss','1','-i',str(output),'-t','1','-f','f32le','-ac','1','-ar','48000','-'],capture_output=True,check=True).stdout
        samples=array('f');samples.frombytes(pcm);report['export_rms']=math.sqrt(sum(v*v for v in samples)/len(samples));assert report['export_rms']>.01
        report['export']=result
        assert [q['downloaded'] for q in api(base,'/api/quote_catalog')['quotes']]==[True,False]
    (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',action='store_true');parser.add_argument('--hold',action='store_true');parser.add_argument('--fullhd',action='store_true')
    args=parser.parse_args();workspace=prepare();base,pid=launch(workspace,args.source)
    (ROOT/'.cache/v11_active.json').write_text(json.dumps(dict(workspace=str(workspace),base=base,pid=pid)),encoding='utf-8')
    print('WORKSPACE',workspace,flush=True)
    try:print(json.dumps(check(base,workspace,args.fullhd),ensure_ascii=False),flush=True)
    finally:
        if not args.hold:stop_owned(pid,workspace)


if __name__=='__main__':main()
