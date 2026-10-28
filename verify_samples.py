"""Export three real examples and paired light previews; never shuts down the PC."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
from core.planner import build_plan
from core.renderer import render_plan, render_overlay, PREVIEW_SIZE
from core.video_detector import VideoDetector
from core.pmdx_reader import DEFAULT_QUOTES
from core.media import probe, run_media, tool_path

ROOT=Path(__file__).resolve().parent

def main():
    out=ROOT/'output_videos'/'verification';out.mkdir(parents=True,exist_ok=True)
    review=ROOT/'test_renders'/'verification';review.mkdir(parents=True,exist_ok=True)
    detector=VideoDetector(ROOT)
    videos=detector.scan_all_videos()
    if not videos: raise RuntimeError('Không có video nguồn.')
    shortest=min(videos,key=lambda v:v['duration'])
    cases=[('01_short',DEFAULT_QUOTES[11],4,videos[0]),('02_two_scenes',DEFAULT_QUOTES[0],0,videos[0]),('03_three_scenes',DEFAULT_QUOTES[8],2,shortest)]
    report=[];frames=[]
    for name,quote,theme,video in cases:
        plan=build_plan(dict(quote=quote,video_path=video['path'],theme_index=theme,vertical_offset=210),ROOT,detector)
        print(name,'scenes',len(plan['scenes']),'duration',plan['duration'],flush=True)
        for preview in [True,False]:
            target=out/(name+('_preview' if preview else '_fullhd')+'.mp4')
            result=render_plan(plan,target,ROOT,preview,lambda p,m:print(name,'preview' if preview else 'fullhd',p,m,flush=True))
            info=probe(target)
            assert (info['width'],info['height'])==(PREVIEW_SIZE if preview else (1080,1920))
            assert abs(info['duration']-plan['duration'])<.1
            check=run_media([tool_path('ffmpeg'),'-v','error','-i',str(target),'-f','null','-'],capture_output=True)
            assert check.returncode==0,check.stderr
            report.append(dict(name=target.name,scenes=len(plan['scenes']),**result,probe=info))
        # Include each scene and exact transition midpoints, plus near the end.
        stamps=[s['text_start']+min(1.,(s['text_end']-s['text_start'])/2) for s in plan['scenes']]
        stamps += [s['text_start'] for s in plan['scenes'][1:]]+[plan['duration']-.5]
        for i,stamp in enumerate(stamps):
            image=review/f'{name}_{i}.jpg'
            check=run_media([tool_path('ffmpeg'),'-y','-v','error','-ss',str(stamp),'-i',str(target),'-frames:v','1',str(image)],capture_output=True)
            assert check.returncode==0
            frames.append((f'{name} @ {stamp:.1f}s',image))
    background=Image.open(videos[0]['thumb_path']).convert('RGBA').resize((1080,1920))
    for theme in range(5):
        overlay=render_overlay('Hạnh phúc bắt đầu từ những điều giản dị, khi ta biết yêu thương và sống chậm lại.',
                               'Thanh Vị Sách Hay Mỗi Ngày — Cùng nuôi dưỡng lòng biết ơn và yêu thương mỗi ngày',
                               theme_index=theme,vertical_offset=350,quote_size=108,credit_size=32,workspace_dir=str(ROOT))
        path=review/f'footer_theme_{theme}.jpg'
        Image.alpha_composite(background,overlay).convert('RGB').save(path,quality=90)
        frames.append((f'Theme {theme+1} / long credit',path))
    columns=5;cw,ch=270,510
    sheet=Image.new('RGB',(columns*cw,((len(frames)+columns-1)//columns)*ch),'#101a26')
    draw=ImageDraw.Draw(sheet)
    for i,(label,path) in enumerate(frames):
        x,y=(i%columns)*cw,(i//columns)*ch
        image=Image.open(path).convert('RGB').resize((270,480))
        sheet.paste(image,(x,y+26));draw.text((x+5,y+5),label,fill='white')
    sheet.save(review/'review_sheet.jpg',quality=90)
    (review/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Verified:',len(report),'videos. Review:',review/'review_sheet.jpg',flush=True)

if __name__=='__main__': main()
