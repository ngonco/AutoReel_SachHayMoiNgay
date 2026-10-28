"""Verify anonymous Sheet sync in the packaged app on an isolated profile; never edit Google."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from io import BytesIO
from PIL import Image, ImageChops, ImageStat
import psutil
from core.media import run_media, tool_path, probe
from core.renderer import PREVIEW_SIZE, scene_overlay
from core.settings import save_settings_patch
from core.quote_sync import fetch_sheet_quotes
from verify_v5 import api, wait_job

ROOT=Path(__file__).resolve().parent
DRAFT='  Giữ nguyên câu đang soạn.\n\nKể cả dòng trống và Enter cuối.\n'


def prepare():
    workspace=ROOT/'.cache'/f'v9_smoke_{time.time_ns()}'
    clips=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC';clips.mkdir(parents=True)
    for index,color in enumerate(['0x3b7b67','0x42628e']):
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i',f'color=c={color}:s=180x320:r=30:d=2',
                   '-c:v','libx264','-pix_fmt','yuv420p',str(clips/f'{index}.mp4')],check=True,capture_output=True)
    (workspace/'quotes.txt').write_text('Câu cục bộ một.\nCâu cục bộ hai.\n',encoding='utf-8')
    save_settings_patch(workspace,dict(quote=DRAFT,quote_index=1,outline_width=7,duration=1))
    return workspace


def launch(workspace,port,disabled=False,visible=False):
    args=['wscript.exe',str(ROOT/'Mo_App_Auto_Reel.vbs'),'--workspace',str(workspace),'--port',str(port)]
    if disabled:args.append('--no-sheet-sync')
    if not visible:args.append('--headless')
    subprocess.run(args,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    base=f'http://127.0.0.1:{port}'
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            health=api(base,'/api/health');process=psutil.Process(health['pid'])
            assert health['version']=='multi-scene-v9',health
            assert Path(process.exe()).name=='AutoReelSachHay_v9.exe'
            assert str(workspace) in process.cmdline()
            return base,process.pid
        except (OSError,urllib.error.URLError):time.sleep(.4)
    raise TimeoutError('V9 did not start through launcher')


def stop_owned(pid,workspace):
    process=psutil.Process(pid);assert str(workspace) in process.cmdline()
    parent=process.parent()
    own_parent=parent if parent and Path(parent.exe()).name=='AutoReelSachHay_v9.exe' and str(workspace) in parent.cmdline() else None
    children=process.children(recursive=True)
    for child in children:child.terminate()
    process.terminate()
    if own_parent:
        try:own_parent.terminate()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(children+[process],timeout=10)


def synced(base,after=0):
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        status=api(base,'/api/quote_sync')
        if not status['syncing'] and (status['last_checked_at'] or 0)>after:
            assert status['source']=='sheet' and not status['error'],status
            assert status['interval_seconds']==1800
            assert 1790<status['next_check_at']-time.time()<=1800
            return api(base,'/api/quote_catalog')
        time.sleep(.3)
    raise TimeoutError('Packaged anonymous Sheet fetch timed out')


def main(hold,real_source=None):
    workspace=prepare();port=8897;pid=None
    session_before=(workspace/'session_state.json').read_bytes()
    report=dict(workspace=str(workspace))
    try:
        base,pid=launch(workspace,port)
        print('WORKSPACE',workspace,flush=True)
        catalog=synced(base)
        expected=fetch_sheet_quotes()
        assert [q['quote'] for q in catalog['quotes']]==expected
        assert len(api(base,'/api/quotes'))==len(expected)
        assert (workspace/'session_state.json').read_bytes()==session_before
        assert not (workspace/'footage_usage.json').exists()
        checked=catalog['sync']['last_checked_at']
        requested=api(base,'/api/quote_sync',{})
        assert requested['syncing']
        refreshed=synced(base,checked)
        assert (workspace/'session_state.json').read_bytes()==session_before
        print('Anonymous startup/manual sync:',len(expected),'quotes; schedule 1800 seconds; draft untouched.',flush=True)
        quote=min(expected,key=lambda q:len(q.split()))
        plan=api(base,'/api/plan',dict(quote=quote,duration=1))
        preview=wait_job(base,api(base,'/api/preview',dict(plan_id=plan['plan_id'])))
        history_path=workspace/'footage_usage.json'
        assert not json.loads(history_path.read_text(encoding='utf-8'))['counts']
        export=wait_job(base,api(base,'/api/render',dict(plan_id=plan['plan_id'],**{'async':True})))
        preview_path=workspace/'.cache'/'previews'/preview['filename']
        export_path=workspace/'output_videos'/export['filename']
        for path in [preview_path,export_path]:
            info=probe(path)
            assert (info['width'],info['height'])==(PREVIEW_SIZE if path==preview_path else (1080,1920))
            decoded=run_media([tool_path('ffmpeg'),'-v','error','-i',str(path),'-f','null','-'],capture_output=True)
            assert not decoded.returncode,decoded.stderr
        assert abs(probe(preview_path)['duration']-probe(export_path)['duration'])<.05
        assert (workspace/'session_state.json').read_bytes()==session_before
        sample_payload=dict(quote='Chỉ những người tu đến mức không thấy mình quan trọng nữa',auto_paginate=False,duration=1,quote_size=68)
        if real_source:sample_payload['video_path']=str(Path(real_source).resolve())
        sample=api(base,'/api/plan',sample_payload)
        sample_preview=wait_job(base,api(base,'/api/preview',dict(plan_id=sample['plan_id'])))
        started=time.monotonic();cached=api(base,'/api/preview',dict(plan_id=sample['plan_id']))
        cached_latency=time.monotonic()-started
        assert cached['status']=='done' and cached['result']['cached'] and cached_latency<2,cached
        sample_export=wait_job(base,api(base,'/api/render',dict(plan_id=sample['plan_id'],**{'async':True})))
        with urllib.request.urlopen(base+f"/api/overlay/{sample['plan_id']}/0",timeout=20) as response:
            actual_overlay=Image.open(BytesIO(response.read())).convert('RGBA')
        assert actual_overlay.tobytes()==scene_overlay(sample,sample['scenes'][0],str(workspace)).tobytes()
        actual_overlay.save(workspace/'uniform_line_overlay.png')
        sample_preview_path=workspace/'.cache'/'previews'/sample_preview['filename']
        sample_export_path=workspace/'output_videos'/sample_export['filename']
        for kind,path in [('preview',sample_preview_path),('fullhd',sample_export_path)]:
            shot=workspace/f'uniform_lines_{kind}.png'
            run_media([tool_path('ffmpeg'),'-y','-v','error','-ss','1.2','-i',str(path),'-frames:v','1',str(shot)],check=True,capture_output=True)
            decoded=run_media([tool_path('ffmpeg'),'-v','error','-i',str(path),'-f','null','-'],capture_output=True)
            assert not decoded.returncode,decoded.stderr
        small=Image.open(workspace/'uniform_lines_preview.png').convert('RGB')
        large=Image.open(workspace/'uniform_lines_fullhd.png').convert('RGB').resize(PREVIEW_SIZE,Image.Resampling.LANCZOS)
        mean_difference=sum(ImageStat.Stat(ImageChops.difference(small,large)).mean)/3
        assert mean_difference<20,mean_difference
        history_before=history_path.read_bytes()
        stop_owned(pid,workspace);pid=None
        base,pid=launch(workspace,port,disabled=True)
        assert api(base,'/api/quote_sync')['enabled'] is False
        assert [q['quote'] for q in api(base,'/api/quotes')]==['Câu cục bộ một.','Câu cục bộ hai.']
        assert (workspace/'session_state.json').read_bytes()==session_before
        assert json.loads(history_path.read_text(encoding='utf-8'))['counts']==json.loads(history_before)['counts']
        stop_owned(pid,workspace);pid=None
        base,pid=launch(workspace,port,visible=hold)
        restored=synced(base)
        assert [q['quote'] for q in restored['quotes']]==fetch_sheet_quotes()
        assert api(base,'/api/settings')['quote']==DRAFT
        assert json.loads(history_path.read_text(encoding='utf-8'))['counts']==json.loads(history_before)['counts']
        report.update(initial=catalog['sync'],manual=refreshed['sync'],restart=restored['sync'],
                      preview=preview,export=export,draft_preserved=True,history_preserved=True,
                      line_sample_preview=sample_preview,line_sample_export=sample_export,
                      cached_preview_latency=round(cached_latency,4),preview_fullhd_mean_pixel_difference=round(mean_difference,3),
                      disabled_profile_local_only=True,pid=pid,base=base,
                      exe_sha256=hashlib.sha256((ROOT/'AutoReelSachHay_v9.exe').read_bytes()).hexdigest())
        (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Packaged v9: public Sheet, cache/restart, manual sync, offline test mode, preview/export all passed.',flush=True)
        if hold:print('HELD',base,pid,flush=True);pid=None
    finally:
        if pid:stop_owned(pid,workspace)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--hold',action='store_true');parser.add_argument('--real-source')
    arguments=parser.parse_args();main(arguments.hold,arguments.real_source)
