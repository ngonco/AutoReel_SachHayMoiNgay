const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function fixture(){
  let now=0;const frames=[],attached=[],draws=[];
  class Media{
    constructor(){this.dataset={};this.style={};this.paused=true;this.readyState=4;this.duration=20;this._time=0;this.playbackRate=1;this.loads=0;}
    setAttribute(){} removeAttribute(){this.src='';}
    load(){this.loads++;queueMicrotask(()=>this.onloadeddata?.());}
    play(){this.paused=false;return Promise.resolve();}pause(){this.paused=true;}
    get currentTime(){return this._time;}set currentTime(value){this._time=value;queueMicrotask(()=>this.onseeked?.());}
  }
  const canvas={width:360,height:640,dataset:{},parentElement:{append:v=>attached.push(v)},getContext:()=>({clearRect(){},drawImage(...a){draws.push(a);},globalAlpha:1})};
  const requests=[],times=[],statuses=[];
  const context=vm.createContext({document:{createElement:()=>new Media()},Audio:Media,console,
    performance:{now:()=>now},requestAnimationFrame:cb=>{frames.push(cb);return frames.length;},cancelAnimationFrame(){},setTimeout:()=>0,clearTimeout(){},module:{exports:{}}});
  vm.runInContext(fs.readFileSync('ui/draft_player.js','utf8'),context);
  const Player=context.module.exports.DraftPlayer;
  const media=[0,1,2].map(i=>({index:i,key:'proxy'+i,status:'ready',url:'/proxy'+i}));
  const player=new Player({canvas,request:async(path,body)=>{requests.push(path);return {scenes:media};},loadOverlay:async()=>({image:true}),
    onStatus:(...args)=>statuses.push(args),onTime:(...args)=>times.push(args)});
  const plan={plan_id:'one',duration:11.2,transition:.4,settings:{music_volume:.5},music:{path:'music',size:1,mtime_ns:1},music_url:'/music/one',
    scenes:[0,1,2].map(i=>({index:i,start:i*3.6,end:i*3.6+4,text_start:i?i*3.6+.2:0,text_end:i===2?11.2:(i+1)*3.6+.2,
      source_start:.5,source_end:2.5,speed:.5,source:{path:'clip'+i,size:1,mtime_ns:1},overlay_key:'text'+i}))};
  return {player,plan,canvas,attached,requests,times,statuses,draws,advance:t=>{now=t;},flush:async()=>{for(let i=0;i<8;i++)await Promise.resolve();}};
}
(async()=>{
  {
    const f=fixture();await f.player.setPlan(f.plan);await f.flush();
    assert.equal(f.attached.length,3,'Two decoders and music stay attached to the document for reliable media events');
    assert.equal(f.player.audio.src,'/music/one');assert.ok(f.draws.length);
    assert.ok(f.requests.every(p=>!p.includes('/api/preview')));
    f.player.operationStartedAt=1;f.advance(100);await f.player.play(1);await f.flush();f.player.tick(116);await f.flush();f.player.tick(132);
    assert.equal(f.player.mode,'scene');assert.equal(f.player.end,f.plan.scenes[1].text_end);
    f.player.pause();assert.ok(f.player.videos.every(v=>v.paused));
    await f.player.seek(8);await f.flush();f.player.draw();await f.flush();
    const source=f.player.videos[0];assert.equal(source.dataset.sceneIndex,2);
    assert.ok(Math.abs(source.currentTime-(.5+(8-7.2)*.5))<.02);
    f.player.clear();assert.equal(f.player.plan,null);
  }
  {
    const f=fixture();await f.player.setPlan(f.plan);await f.flush();
    const loads=f.player.videos.map(v=>v.loads);f.player.clear(true);
    await f.player.setPlan({...f.plan,plan_id:'design',scenes:f.plan.scenes.map(s=>({...s,overlay_key:'design'+s.index}))});await f.flush();
    assert.deepEqual(f.player.videos.map(v=>v.loads),loads,'Design changes reuse decoded background sources');
    assert.equal(f.player.audio.loads,1,'Changing design does not reload the soundtrack');
  }
  {
    const f=fixture();await f.player.setPlan(f.plan);await f.flush();
    f.player.media[0]={index:0,status:'preparing'};f.player.time=0;await f.player.play();f.player.tick(30);
    assert.equal(f.player.time,0,'Buffering freezes the master timeline');assert.ok(f.player.audio.paused);
    f.player.media[0]={index:0,status:'error',error:'bad clip'};f.player.tick(60);assert.equal(f.player.running,false);
    assert.match(f.statuses.at(-1)[0],/bad clip/);
  }
  {
    const f=fixture();await f.player.setPlan(f.plan);await f.flush();let rejectPlay,calls=0;
    f.player.audio.play=()=>{calls++;f.player.audio.paused=false;return new Promise((resolve,reject)=>{rejectPlay=reject;});};
    await f.player.play();await f.flush();assert.equal(calls,1);
    f.player.media[0]={index:0,status:'preparing'};f.player.tick(30);
    rejectPlay(Object.assign(new Error('Interrupted by buffering pause'),{name:'AbortError'}));await f.flush();
    assert.equal(f.player.audioBlocked,false,'Buffering must not permanently disable the soundtrack');
    f.player.media[0]={index:0,status:'ready',url:'/proxy0'};
    f.player.audio.play=()=>{calls++;f.player.audio.paused=false;return Promise.resolve();};
    f.player.tick(60);await f.flush();assert.equal(calls,2,'Sound automatically resumes once video data is ready');
    assert.equal(f.player.audio.paused,false);assert.ok(f.player.audio.volume>0);assert.equal(f.player.audio.muted,false);
  }
  {
    const f=fixture();await f.player.setPlan(f.plan);await f.flush();
    f.player.audio.play=()=>Promise.reject(Object.assign(new Error('Autoplay denied'),{name:'NotAllowedError'}));
    await f.player.play();await f.flush();assert.equal(f.player.audioBlocked,true);
    f.player.audio.play=()=>{f.player.audio.paused=false;return Promise.resolve();};
    f.player.enableAudio();await f.flush();assert.equal(f.player.audioBlocked,false);
    assert.ok(f.player.audio.volume>0,'Unlocking never leaves the actual soundtrack at volume zero');
  }
  {
    const f=fixture();await f.player.setPlan(f.plan);await f.flush();let rejectOld;
    f.player.audio.play=()=>new Promise((resolve,reject)=>{rejectOld=reject;});
    await f.player.play();await f.flush();
    await f.player.setPlan({...f.plan,plan_id:'new',music:{path:'new-music',size:2,mtime_ns:2}});
    rejectOld(Object.assign(new Error('Old play rejected'),{name:'NotAllowedError'}));await f.flush();
    assert.equal(f.player.audioBlocked,false,'An obsolete play promise cannot block a newer plan');
  }
  console.log('Draft player: attached decoders, source-time mapping, scene playback, seek, pause, design reuse and buffer/error clock checks passed.');
})().catch(e=>{console.error(e);process.exitCode=1;});
