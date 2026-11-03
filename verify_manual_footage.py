"""Isolated packaged manual footage and numeric neighbor regression."""
from verify_v13 import prepare, launch, stop_owned
from verify_v5 import api, wait_job
import json
from pathlib import Path


def main():
    workspace=prepare()
    clips=workspace/'CLIP TƯỢNG PHẬT LQ'/'DỌC'
    for index, number in enumerate((100,103,150,200)):
        (clips/f'{index}.mp4').rename(clips/f'IMG_{number}.mp4')
    base,pid=launch(workspace,port=8902)
    try:
        videos=api(base,'/api/videos')
        if isinstance(videos,dict):videos=videos['videos']
        paths={Path(v['path']).stem:v['path'] for v in videos}
        payload=dict(quote='Bình an.',theme_index=0,duration=4,music_mode='none',auto_paginate=False)
        def plan(number):
            body={**payload,'scene_video_preferences':{'0':dict(path=paths[f'IMG_{number}'],text=payload['quote'])}}
            return api(base,'/api/plan',body)
        first=plan(100)
        if 'plan' in first:first=first['plan']
        job=api(base,'/api/render',dict(plan_id=first['plan_id']))
        # Synchronous API still goes through JobManager and its reservation/commit.
        assert job.get('success'),job
        automatic=api(base,'/api/plan',payload)
        if 'plan' in automatic:automatic=automatic['plan']
        assert Path(automatic['scenes'][0]['video_path']).stem not in ('IMG_100','IMG_103')
        second=plan(103)
        if 'plan' in second:second=second['plan']
        assert Path(second['scenes'][0]['video_path']).stem=='IMG_103'
        assert second['footage_pool']['manual_scenes']==[0]
        result=api(base,'/api/render',dict(plan_id=second['plan_id']))
        assert result.get('success'),result
        history=json.loads((workspace/'footage_usage.json').read_text(encoding='utf-8'))
        assert sum(history['counts'].values())==2
        print('PASS: packaged manual selection, adjacent-number automatic avoidance, tracked Full HD exports and counts',flush=True)
    finally:stop_owned(pid,workspace)

if __name__=='__main__':main()
