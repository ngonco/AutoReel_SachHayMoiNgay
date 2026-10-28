const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
function fixture(){
  const elements=new Map(),timers=new Map();let timer=0;
  const element=id=>{if(!elements.has(id))elements.set(id,{value:'Bình an.',checked:false,style:{},textContent:'',classList:{add(){},toggle(){}},getContext(){return{};},pause(){},load(){this.loads=(this.loads||0)+1;},play(){this.plays=(this.plays||0)+1;},paused:true});return elements.get(id);};
  const context=vm.createContext({document:{getElementById:element},window:{addEventListener(){}},crypto:require('node:crypto').webcrypto,
    setTimeout:(cb,ms)=>{timers.set(++timer,{cb,ms});return timer;},clearTimeout:id=>timers.delete(id),console});
  vm.runInContext(fs.readFileSync('ui/app.js','utf8'),context);
  const run=code=>vm.runInContext(code,context);
  run("state.ready=true;state.plan={plan_id:'plan',quote:'Bình an.',duration:4,scenes:[{footage_id:'a'.repeat(24)}]};state.lastAcceptedPlan=state.plan;state.contextQuote='Bình an.';renderScenes=()=>{};drawStill=()=>{};populateQuotes=()=>{};playUrl=async url=>{playedUrl=url;};");
  const calls=[];
  context.record=async(path,body)=>{calls.push({path,body});return {status:'done',result:{url:'/preview.mp4'}};};
  run('api=(...args)=>record(...args)');
  return {context,run,element,calls,timers};
}
(async()=>{
  {
    const f=fixture();let setPlan=null,played=null;
    f.context.fakeDraft={running:false,mode:'scene',time:2,pause(){},clear(){},unlockAudio(){},setPlan(plan){this.plan=plan;setPlan=plan;},play(index){played=index;}};
    f.run('draft=fakeDraft');
    await f.run('togglePlayback()');
    assert.equal(f.calls.length,0,'Instant Play never submits a rendered preview job');
    assert.equal(f.context.fakeDraft.time,0,'Full Reel starts at zero after a scene preview');
    assert.equal(played,undefined);assert.ok(setPlan);
  }
  {
    const f=fixture();f.context.setTimeout=()=>0;f.run('populateVideos=()=>{};');
    f.run("state.plan={plan_id:'p',scenes:[{text:'Cảnh một.'},{text:'Cảnh hai.'}]};state.selectedScene=1;state.settings.scene_video_preferences={};state.currentVideo={path:'first.mp4'};");
    f.context.nextVideo={path:'replacement.mp4',name:'replacement.mp4'};
    f.run('selectVideo(nextVideo)');
    assert.equal(f.run('state.selectedScene'),1);
    assert.equal(f.run("state.settings.scene_video_preferences['1'].path"),'replacement.mp4');
    assert.equal(f.run('state.currentVideo.path'),'first.mp4','Selecting scene two does not change legacy scene-one hint');
    assert.equal(f.run('state.pendingScenePlayback'),1);
    f.run('state.settings.quote_size=80;invalidate({preserveScene:true})');
    assert.equal(f.run("state.settings.scene_video_preferences['1'].path"),'replacement.mp4');
    f.element('quoteInput').value='Câu mới.';f.run('invalidate()');
    assert.equal(f.run('Object.keys(state.settings.scene_video_preferences).length'),0);
  }
  const source=fs.readFileSync('ui/app.js','utf8');
  assert.equal(source.includes("api('/api/preview'"),false,'UI no longer creates whole-Reel draft MP4 jobs');
  const html=fs.readFileSync('ui/index.html','utf8');
  assert.ok(html.indexOf('id="sceneList"')<html.indexOf('id="videoCarousel"'));
  assert.ok(html.indexOf('id="sceneList"')>html.indexOf('02 / Kịch bản'));
  console.log('Instant draft UI: no render submission, per-scene preference, selection preservation and content reset passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
