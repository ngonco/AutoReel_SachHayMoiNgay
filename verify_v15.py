"""Packaged queue regression; isolated synthetic profile only."""
import argparse
import json
import urllib.error
from pathlib import Path
from verify_v13 import prepare,launch,stop_owned
from verify_v5 import api,wait_job

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--hold',action='store_true');args=parser.parse_args()
    w=prepare();base,pid=launch(w,port=8904)
    active=dict(workspace=str(w),base=base,pid=pid)
    Path('.cache/v15_active.json').write_text(json.dumps(active),encoding='utf-8')
    try:
        clips=api(base,'/api/videos');manual=clips[-1]['path']
        def add(text):return api(base,'/api/export_queue',dict(action='add',payload=dict(quote=text,theme_index=0,duration=4,music_mode='none',scene_video_preferences={'0':dict(path=manual,text=text)})))['selected_id']
        a=add('Bình an.');b=add('Biết ơn.')
        latest=dict(quote='Sống tử tế.',theme_index=0,duration=4,music_mode='none',scene_video_preferences={'0':dict(path=manual,text='Sống tử tế.')},imported_video_paths=[manual])
        api(base,'/api/export_queue',dict(action='update',id=a,payload=latest))
        api(base,'/api/export_queue',dict(action='move',id=b,direction=-1))
        # Deliberate missing source must fail only this item, leaving successful items intact.
        bad=add('Nguồn thiếu.')
        api(base,'/api/export_queue',dict(action='update',id=bad,payload=dict(quote='Nguồn thiếu.',video_path=str(w/'missing.mp4'))))
        job=api(base,'/api/batch_render',{'async':True});done=wait_job(base,job)
        items=api(base,'/api/export_queue')['items']
        assert [i['id'] for i in items]==[b,a,bad]
        assert [i['status'] for i in items]==['done','done','error'],items
        assert items[1]['payload']['quote']=='Sống tử tế.'
        history=json.loads((w/'footage_usage.json').read_text(encoding='utf-8'))
        assert sum(history['counts'].values())==2
        assert items[0]['result']['filename']!=items[1]['result']['filename']
        retry=api(base,'/api/batch_render',{'async':True});wait_job(base,retry)
        assert sum(json.loads((w/'footage_usage.json').read_text())['counts'].values())==2
        api(base,'/api/export_queue',dict(action='delete',id=bad))
        try:api(base,'/api/batch_render',{'async':True});raise AssertionError('Completed items were exported again')
        except urllib.error.HTTPError as e:assert e.code==400
        prefs=dict(expanded=False,size=160,filter='all',scroll=300,search='')
        api(base,'/api/footage_browser',prefs)
        stop_owned(pid,w);base,pid=launch(w,port=8904);active['pid']=pid
        assert len(api(base,'/api/export_queue')['items'])==2
        assert api(base,'/api/footage_browser')['size']==160
        assert api(base,'/api/footage_browser')['expanded'] is False
        active['passed']=True;Path('.cache/v15_active.json').write_text(json.dumps(active),encoding='utf-8')
        print('PASS: packaged latest queue drafts, order, manual footage, two Full HD exports, failure/retry, done-skip, persistence and browser preferences',flush=True)
    finally:
        if not args.hold:stop_owned(pid,w)

if __name__=='__main__':main()
