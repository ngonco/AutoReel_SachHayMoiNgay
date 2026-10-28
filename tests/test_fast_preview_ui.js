const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
function fixture(){
  const elements=new Map(),timers=new Map();let timer=0;
  const element=id=>{if(!elements.has(id))elements.set(id,{value:'Bình an.',checked:false,style:{},textContent:'',classList:{add(){},toggle(){}},getContext(){return{};},pause(){},load(){this.loads=(this.loads||0)+1;},play(){this.plays=(this.plays||0)+1;},paused:true});return elements.get(id);};
  const context=vm.createContext({document:{getElementById:element},window:{addEventListener(){}},crypto:require('node:crypto').webcrypto,
    setTimeout:(cb,ms)=>{timers.set(++timer,{cb,ms});return timer;},clearTimeout:id=>timers.delete(id),console});
  vm.runInContext(fs.readFileSync('ui/app.js','utf8'),context);
  const run=code=>vm.runInContext(code,context);
  run("state.ready=true;state.plan={plan_id:'plan',quote:'Bình an.',duration:4,scenes:[{footage_id:'a'.repeat(24)}]};state.lastAcceptedPlan=state.plan;state.contextQuote='Bình an.';renderScenes=()=>{};drawStill=()=>{};playUrl=async url=>{playedUrl=url;};");
  const calls=[];
  context.record=async(path,body)=>{calls.push({path,body});return {status:'done',result:{url:'/preview.mp4'}};};
  run('api=(...args)=>record(...args)');
  return {context,run,element,calls,timers};
}
(async()=>{
  {
    const f=fixture();f.run('scheduleWarmPreview(state.plan)');
    const warm=[...f.timers.values()].find(t=>t.ms===900);assert.ok(warm);warm.cb();
    await f.run('state.previewRequest.promise');
    assert.equal(f.calls.length,1);assert.equal(f.calls[0].path,'/api/preview');
    assert.ok(f.calls[0].body.preview_client_id);
    assert.equal(f.element('previewVideo').loads,1);assert.equal(f.element('previewVideo').plays,undefined);
    assert.equal(f.run('state.loadedPlan'),null,'Preload must not change active scene/player state');
    await f.run('togglePlayback()');assert.equal(f.calls.length,1,'Play uses the prepared MP4 without another server request');
    assert.equal(f.run('playedUrl'),'/preview.mp4');
  }
  {
    const f=fixture();let complete;
    f.context.record=async(path,body)=>{f.calls.push({path,body});return await new Promise(resolve=>{complete=resolve;});};
    const warming=f.run('preparePreview(state.plan)');
    const clicking=f.run('togglePlayback()');
    await Promise.resolve();complete({status:'done',result:{url:'/shared.mp4'}});
    await Promise.all([warming,clicking]);assert.equal(f.calls.length,1,'Click and background prep share one request');
  }
  {
    const f=fixture();let complete;
    f.context.record=async()=>await new Promise(resolve=>{complete=resolve;});
    const old=f.run('preparePreview(state.plan)');
    f.element('quoteInput').value='Câu mới.';f.run("invalidate();state.plan={plan_id:'new',quote:'Câu mới.',scenes:[],duration:4};");
    complete({status:'done',result:{url:'/obsolete.mp4'}});await old;
    assert.equal(f.run('state.previewUrl'),null);assert.equal(f.element('previewVideo').loads,undefined);
  }
  console.log('Fast preview UI: background prep, preload without autoplay, instant reuse, shared request and stale-result isolation passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
