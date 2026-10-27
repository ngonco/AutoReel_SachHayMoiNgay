"""Isolated EXE checks: draft persistence, late saves, footage cycle, single/batch exports."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request
from PIL import Image
from core.media import run_media,tool_path,probe
from core.footage_pool import identity

ROOT=Path(__file__).resolve().parent
DRAFT='Bình an trong từng việc nhỏ.\n\nYêu thương bằng hành động.\n'


def prepare():
    workspace=ROOT/'.cache'/f'v5_smoke_{time.time_ns()}'
    clips=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC';clips.mkdir(parents=True)
    for i,color in enumerate(['0x945942','0x3b7b67','0x42628e']):
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i',f'color=c={color}:s=180x320:r=30:d=2','-c:v','libx264','-pix_fmt','yuv420p',str(clips/f'clip_{i}.mp4')],check=True,capture_output=True)
    (workspace/'quotes.txt').write_text('Yêu thương.\nBiết ơn.\n',encoding='utf-8')
    return workspace


def api(base,route,body=None):
    request=urllib.request.Request(base+route,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=180) as response:return json.load(response)


def wait_job(base,job):
    deadline=time.monotonic()+600
    while job['status'] not in ['done','error']:
        if time.monotonic()>deadline:raise TimeoutError('Test render timed out')
        time.sleep(.4);job=api(base,'/api/jobs/'+job['job_id'])
    assert job['status']=='done',job
    return job['result']


def verify(base,workspace):
    videos=api(base,'/api/videos');assert len(videos)==3
    patch=dict(quote=DRAFT,quote_index=1,video_path=videos[1]['path'],safe_zone=True,outline_width=9,outline_blur=12,outline_opacity=.9)
    api(base,'/api/settings',{'_client_id':'integration','_sequence':3,'_patch':patch})
    api(base,'/api/settings',{'_client_id':'integration','_sequence':2,'_patch':{'quote':'Old draft'}})
    api(base,'/api/settings',{'verticalOffset':-600})
    saved=api(base,'/api/settings')
    assert saved['quote']==DRAFT and saved['video_path']==videos[1]['path']
    assert saved['outline_width']==9 and saved['safe_zone'] and saved['vertical_offset']==-600
    payload=dict(quote='Bình an.',duration=1,video_path=videos[0]['path'],quote_size=68,credit_size=24,outline_width=7,outline_blur=10)
    plan=api(base,'/api/plan',payload)
    history=workspace/'footage_usage.json'
    assert not json.loads(history.read_text(encoding='utf-8'))['counts']
    preview=wait_job(base,api(base,'/api/preview',{'plan_id':plan['plan_id']}))
    assert not json.loads(history.read_text(encoding='utf-8'))['counts'],'Preview consumed footage'
    exported=[];expected=[]
    for i in range(2):
        plan=api(base,'/api/plan',payload)
        result=wait_job(base,api(base,'/api/render',{'plan_id':plan['plan_id'],'async':True}))
        exported.append(workspace/'output_videos'/result['filename']);expected.append(plan['scenes'][0]['footage_id'])
        try:api(base,'/api/render',{'plan_id':plan['plan_id'],'async':True})
        except urllib.error.HTTPError as error:assert error.code==409
        else:raise AssertionError('Old consumed footage plan was accepted')
        print('Single export',i+1,result['filename'],flush=True)
    batch=wait_job(base,api(base,'/api/batch_render',{'duration':1,'outline_width':7,'outline_blur':10,'async':True}))
    assert batch['success'] and batch['total_rendered']==2,batch
    exported.extend(workspace/'output_videos'/name for name in batch['files'])
    references={identity(v):Image.open(v['thumb_path']).convert('RGB').getpixel((4,4)) for v in videos}
    sequence=[];report=[]
    for i,path in enumerate(exported):
        metadata=probe(path);assert(metadata['width'],metadata['height'])==(1080,1920)
        shot=workspace/f'color_{i}.png'
        run_media([tool_path('ffmpeg'),'-y','-v','error','-ss','0.5','-i',str(path),'-vf','crop=8:8:0:0','-frames:v','1',str(shot)],check=True,capture_output=True)
        color=Image.open(shot).convert('RGB').getpixel((4,4))
        key=min(references,key=lambda k:sum((a-b)**2 for a,b in zip(color,references[k])))
        sequence.append(key);report.append(dict(file=path.name,probe=metadata,footage_id=key))
        result=run_media([tool_path('ffmpeg'),'-v','error','-i',str(path),'-f','null','-'],capture_output=True)
        assert result.returncode==0,result.stderr
    assert sequence[:2]==expected
    counts=Counter({key:0 for key in references})
    for key in sequence:
        assert counts[key]==min(counts.values()),'Footage repeated before the library was exhausted'
        counts[key]+=1
    stored=json.loads(history.read_text(encoding='utf-8'))
    assert stored['counts']==dict(counts) and not stored['reservations']
    assert api(base,'/api/settings')['quote']==DRAFT,'Rendering overwrote the draft'
    (workspace/'verification.json').write_text(json.dumps(dict(preview=preview,exports=report,sequence=sequence,counts=dict(counts),draft=saved),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Draft, preview, single/batch export and complete footage cycle passed.',flush=True)


def main(exe,hold):
    import psutil
    workspace=prepare();port=8892;base=f'http://127.0.0.1:{port}'
    proc=None
    def stop_owned():
        nonlocal proc
        if proc and proc.poll() is None:
            parent=psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                try:child.terminate()
                except psutil.NoSuchProcess:pass
            try:proc.wait(timeout=20)
            except subprocess.TimeoutExpired:proc.terminate();proc.wait(timeout=10)
        proc=None
    def start_owned():
        nonlocal proc
        proc=subprocess.Popen([str(exe),'--headless','--workspace',str(workspace),'--port',str(port)],creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if proc.poll() is not None:raise RuntimeError('Test EXE exited before startup')
            try:
                health=api(base,'/api/health')
                owned={p.pid for p in psutil.Process(proc.pid).children(recursive=True)}|{proc.pid}
                if health['pid'] not in owned:raise RuntimeError('Test port belongs to another process')
                return
            except (urllib.error.URLError,ConnectionError):time.sleep(.5)
        raise TimeoutError('Test EXE startup timed out')
    try:
        start_owned();print('TEST_SERVER',base,'PROFILE',workspace,flush=True)
        verify(base,workspace)
        old_counts=json.loads((workspace/'footage_usage.json').read_text(encoding='utf-8'))['counts']
        stop_owned();start_owned()
        settings=api(base,'/api/settings')
        assert settings['quote']==DRAFT and settings['outline_width']==9
        assert json.loads((workspace/'footage_usage.json').read_text(encoding='utf-8'))['counts']==old_counts
        print('EXE restart restored the multiline draft, settings and footage history.',flush=True)
        (ROOT/'.cache'/'v5_live.json').write_text(json.dumps(dict(base=base,workspace=str(workspace),pid=api(base,'/api/health')['pid']),ensure_ascii=False),encoding='utf-8')
        if hold:
            print('READY_FOR_UI',base,flush=True)
            while not(workspace/'stop-ui.flag').exists():time.sleep(.5)
    finally:stop_owned()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--exe',type=Path,required=True);parser.add_argument('--hold',action='store_true');args=parser.parse_args();main(args.exe.resolve(),args.hold)
