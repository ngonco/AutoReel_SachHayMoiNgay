"""Exercise a running local server, including a packaged EXE. Never changes saved settings."""
import argparse
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


def verify(base):
    def request(route,body=None,headers=None):
        data=None if body is None else json.dumps(body).encode('utf-8')
        req=urllib.request.Request(base+route,data=data,headers={'Content-Type':'application/json',**(headers or {})})
        with urllib.request.urlopen(req,timeout=180) as response:
            content=response.read()
            return response.status,response.headers,json.loads(content) if 'application/json' in response.headers.get('Content-Type','') else content
    def wait(job):
        deadline=time.monotonic()+600
        while job['status'] not in ['done','error']:
            assert time.monotonic()<deadline,'Render timeout'
            time.sleep(.5)
            job=request('/api/jobs/'+job['job_id'])[2]
        assert job['status']=='done',job
        return job['result']
    health=request('/api/health')[2]
    assert health['version']=='multi-scene-v1'
    assert b'Ph' in request('/app.js')[2]
    videos=request('/api/videos')[2]
    assert videos
    payload=dict(quote='Người biết nhặt rác là người biết giữ gìn đạo đức từng chút một.',video_path=videos[0]['path'],duration=4,theme_index=4)
    plan=request('/api/plan',payload)[2]
    assert len(plan['scenes'])==1
    assert request('/api/overlay/'+plan['plan_id']+'/0')[2].startswith(b'\x89PNG')
    _,_,job=request('/api/preview',{'plan_id':plan['plan_id']})
    _,_,duplicate=request('/api/preview',{'plan_id':plan['plan_id']})
    assert duplicate['job_id']==job['job_id'] or duplicate['status']=='done'
    start=time.monotonic();request('/api/health');assert time.monotonic()-start<2,'Server blocked by render'
    preview=wait(job)
    status,headers,chunk=request(preview['url'],headers={'Range':'bytes=0-99'})
    assert status==206 and len(chunk)==100 and headers['Accept-Ranges']=='bytes'
    assert headers['Content-Range'].startswith('bytes 0-99/')
    status,_,tail=request(preview['url'],headers={'Range':'bytes=-50'})
    assert status==206 and len(tail)==50
    try: request(preview['url'],headers={'Range':'bytes=9999999999-'})
    except urllib.error.HTTPError as error: assert error.code==416
    else: raise AssertionError('Missing HTTP 416')
    exported=wait(request('/api/render',{'plan_id':plan['plan_id'],'async':True})[2])
    assert exported['success'] and abs(exported['duration']-plan['duration'])<.001
    for body in [dict(quote=''),dict(quote='Câu nói',video_path='Z:/missing.mp4'),dict(plan_id='../../invalid')]:
        try: request('/api/render',body)
        except urllib.error.HTTPError as error:
            assert error.code==400
            assert json.load(error)['success'] is False
        else: raise AssertionError('Invalid input accepted')
    try: request('/api/preview_video/../app.py')
    except urllib.error.HTTPError as error: assert error.code in [400,404]
    else: raise AssertionError('Traversal accepted')
    print(json.dumps(dict(health=health,plan_id=plan['plan_id'],preview=preview['url'],export=exported['url'],duration=plan['duration'],checks='health,plan,overlay,queue,nonblocking,range,suffix-range,416,export,invalid-input,traversal'),ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8877');args=p.parse_args();verify(args.base)
