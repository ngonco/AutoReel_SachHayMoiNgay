"""Packaged v8 verification through the VBS launcher, always on an isolated profile."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.error
import psutil
from PIL import Image, ImageDraw
from core.media import run_media, tool_path, probe
from core.renderer import render_overlay
from verify_v5 import api, wait_job

ROOT=Path(__file__).resolve().parent


def prepare():
    workspace=ROOT/'.cache'/f'v8_smoke_{time.time_ns()}'
    defaults=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC'
    custom=workspace/'Kho nền riêng'/'Thư mục con'
    defaults.mkdir(parents=True);custom.mkdir(parents=True)
    for index,color in enumerate(['0x945942','0x3b7b67','0x42628e','0x805180','0x70752a']):
        destination=(defaults if index<2 else custom)/f'clip_{index}.mp4'
        run_media([tool_path('ffmpeg'),'-y','-v','error','-f','lavfi','-i',
                   f'color=c={color}:s=180x320:r=30:d=2','-c:v','libx264','-pix_fmt','yuv420p',str(destination)],
                  check=True,capture_output=True)
    (workspace/'quotes.txt').write_text('Hãy biết ơn.\nHãy yêu thương.\n',encoding='utf-8')
    return workspace


def launch(workspace,port,headless=True):
    args=['wscript.exe',str(ROOT/'Mo_App_Auto_Reel.vbs'),'--workspace',str(workspace),'--port',str(port)]
    if headless:args.append('--headless')
    subprocess.run(args,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    base=f'http://127.0.0.1:{port}'
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        try:
            health=api(base,'/api/health')
            assert health['version']=='multi-scene-v8',health
            process=psutil.Process(health['pid'])
            assert Path(process.exe()).name=='AutoReelSachHay_v8.exe'
            assert str(workspace) in process.cmdline(),process.cmdline()
            return base,process.pid
        except (OSError,urllib.error.URLError):time.sleep(.5)
    raise TimeoutError('Launcher did not start v8')


def stop_owned(pid,workspace):
    process=psutil.Process(pid)
    assert str(workspace) in process.cmdline()
    parent=process.parent()
    own_parent=parent if parent and Path(parent.exe()).name=='AutoReelSachHay_v8.exe' and str(workspace) in parent.cmdline() else None
    children=process.children(recursive=True)
    for child in children:child.terminate()
    process.terminate()
    if own_parent:
        try:own_parent.terminate()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(children+[process],timeout=10)


def history(workspace):
    return json.loads((workspace/'footage_usage.json').read_text(encoding='utf-8'))


def ids(plan):return {s['footage_id'] for s in plan['scenes']}


def verify(base,workspace):
    assert len(api(base,'/api/videos'))==2
    directory=str(workspace/'Kho nền riêng')
    draft='Bản nháp được giữ nguyên.\n\nMỗi dòng một cảnh.\n'
    api(base,'/api/settings',dict(background_video_directory=directory,quote=draft,outline_width=9))
    videos=api(base,'/api/videos');assert len(videos)==3
    assert all(Path(v['path']).is_relative_to(Path(directory)) for v in videos)
    first=api(base,'/api/plan',dict(quote='Hãy sống tử tế. Hãy luôn biết ơn.',duration=1))
    assert len(first['scenes'])==2
    second=api(base,'/api/plan',dict(quote='Bình an.',duration=1,previous_footage_ids=sorted(ids(first))))
    assert not ids(first)&ids(second)
    assert not history(workspace)['counts']
    before=history(workspace)
    preview=wait_job(base,api(base,'/api/preview',dict(plan_id=first['plan_id'])))
    assert history(workspace)['counts']==before['counts']
    full=wait_job(base,api(base,'/api/render',dict(plan_id=first['plan_id'],**{'async':True})))
    assert history(workspace)['last_export']['ids']==[s['footage_id'] for s in first['scenes']]
    third=api(base,'/api/plan',dict(quote='Yêu thương.',duration=1))
    assert not ids(first)&ids(third),'Previous successful quote not excluded'
    second_full=wait_job(base,api(base,'/api/render',dict(plan_id=third['plan_id'],**{'async':True})))
    batch=api(base,'/api/batch_render',dict(duration=1,**{'async':True}))
    # Another session may change the remembered folder while this batch is already queued.
    api(base,'/api/settings',dict(background_video_directory=''))
    result=wait_job(base,batch)
    assert result['success'] and result['total_rendered']==2,result
    plans=[]
    for path in (workspace/'.cache'/'plans').glob('*.json'):
        plan=json.loads(path.read_text(encoding='utf-8'))
        if plan['quote'] in {'Hãy biết ơn.','Hãy yêu thương.'}:
            assert plan['settings']['background_video_directory']==directory
            assert all(Path(s['video_path']).is_relative_to(Path(directory)) for s in plan['scenes'])
            plans.append(plan)
    assert len(plans)>=2
    exported=[workspace/'output_videos'/full['filename'],workspace/'output_videos'/second_full['filename']]
    exported.extend(workspace/'output_videos'/name for name in result['files'])
    preview_path=workspace/'.cache'/'previews'/preview['filename']
    for path in [preview_path]+exported:
        info=probe(path)
        assert (info['width'],info['height'])==((540,960) if path==preview_path else (1080,1920)),info
        decoded=run_media([tool_path('ffmpeg'),'-v','error','-i',str(path),'-f','null','-'],capture_output=True)
        assert not decoded.returncode,decoded.stderr
    assert abs(probe(preview_path)['duration']-probe(exported[0])['duration'])<.05
    for name,path in [('preview',preview_path),('fullhd',exported[0])]:
        shot=workspace/f'{name}.jpg'
        run_media([tool_path('ffmpeg'),'-y','-v','error','-ss','0.8','-i',str(path),'-frames:v','1',str(shot)],check=True,capture_output=True)
    # Compare actual background colors to planned content IDs for every scene.
    references={v['path']:Image.open(v['thumb_path']).convert('RGB').getpixel((4,4)) for v in videos}
    for index,scene in enumerate(first['scenes']):
        shot=workspace/f'scene_{index}.png'
        run_media([tool_path('ffmpeg'),'-y','-v','error','-ss',str(scene['text_start']+.8),'-i',str(exported[0]),
                   '-vf','crop=8:8:0:0','-frames:v','1',str(shot)],check=True,capture_output=True)
        color=Image.open(shot).convert('RGB').getpixel((4,4))
        closest=min(references,key=lambda key:sum((a-b)**2 for a,b in zip(color,references[key])))
        assert closest==scene['video_path'],(scene,color)
    api(base,'/api/settings',dict(background_video_directory=str(workspace/'missing')))
    try:api(base,'/api/videos')
    except urllib.error.HTTPError as error:assert error.code==400
    else:raise AssertionError('Missing library silently fell back')
    api(base,'/api/select_video_directory',dict(use_default=True))
    assert len(api(base,'/api/videos'))==2
    assert api(base,'/api/settings')['quote']==draft
    api(base,'/api/settings',dict(background_video_directory=directory,duration=1))
    # Shared full-size overlays: five themes, long credit, narrow phrase boundaries.
    sheet=Image.new('RGB',(1350,510),'#101a26');draw=ImageDraw.Draw(sheet)
    for theme in range(5):
        image=render_overlay('Hãy sống với lòng biết ơn và yêu thương để tìm thấy bình an.',
                             'Thanh Vị Sách Hay Mỗi Ngày — Cùng nuôi dưỡng lòng biết ơn và yêu thương mỗi ngày',
                             theme_index=theme,quote_size=108,credit_size=32,workspace_dir=str(ROOT))
        image_path=workspace/f'theme_{theme}.png';image.save(image_path)
        tile=Image.new('RGBA',image.size,'#234238');tile.alpha_composite(image)
        sheet.paste(tile.convert('RGB').resize((270,480)),(theme*270,30))
        draw.text((theme*270+8,8),f'Theme {theme+1}',fill='white')
    sheet.save(workspace/'balanced_lines.jpg',quality=90)
    assert not history(workspace)['reservations']
    report=dict(workspace=str(workspace),version='v8',first_plan=first,preview=preview,export=full,
                next_export=second_full,batch=result,settings=api(base,'/api/settings'),history=history(workspace))
    (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Packaged v8: library, clauses, preview, Full HD, footage colors, batch snapshot and errors passed.',flush=True)


def main(hold):
    workspace=prepare();port=8898;pid=None
    try:
        base,pid=launch(workspace,port)
        print('WORKSPACE',workspace,flush=True)
        verify(base,workspace)
        snapshot=history(workspace);settings=api(base,'/api/settings')
        stop_owned(pid,workspace);pid=None
        base,pid=launch(workspace,port,headless=not hold)
        assert api(base,'/api/settings')==settings
        assert history(workspace)==snapshot
        assert len(api(base,'/api/videos'))==3
        report=json.loads((workspace/'verification.json').read_text(encoding='utf-8'))
        report['restart_passed']=True;report['pid']=pid;report['base']=base
        (workspace/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Restart: folder, draft, settings, previous footage and counts preserved.',flush=True)
        if hold:
            print('HELD',base,pid,flush=True);pid=None
    finally:
        if pid:stop_owned(pid,workspace)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--hold',action='store_true')
    main(parser.parse_args().hold)
