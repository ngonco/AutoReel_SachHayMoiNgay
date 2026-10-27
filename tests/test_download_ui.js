// Exercise download orchestration without rendering, dialogs or personal state.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function fixture() {
  const elements=new Map();
  const element=id=>{
    if(!elements.has(id))elements.set(id,{value:'Hạnh phúc không phải đến từ xa.',checked:false,style:{},classList:{add(){},toggle(){}},getContext(){return{};},pause(){}});
    return elements.get(id);
  };
  const calls=[];
  const context=vm.createContext({document:{getElementById:element},window:{addEventListener(){}},crypto:require('node:crypto').webcrypto,setTimeout,clearTimeout,console,
    fetch:async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(1)})});
  vm.runInContext(fs.readFileSync('ui/app.js','utf8'),context);
  vm.runInContext('renderScenes=()=>{};drawStill=()=>{};showStatic=()=>{};',context);
  context.record=async(path,body)=>{
    calls.push({path,body:structuredClone(body)});
    if(path==='/api/select_save_video')return {save_token:'chosen'};
    if(path==='/api/plan')return {plan_id:'plan',scenes:[]};
    if(path==='/api/render')return {job_id:'rendered',status:'done',result:{url:'/export.mp4',duration:4,filename:'export.mp4'}};
    if(path==='/api/save_video')return {job_id:'saved',status:'done',result:{saved_path:'D:/chosen.mp4'}};
    throw Error(path);
  };
  vm.runInContext('api=(path,body)=>record(path,body);',context);
  return {context,calls,element,run:code=>vm.runInContext(code,context)};
}
(async()=>{
  {
    const f=fixture();f.context.record=async(path)=>{f.calls.push({path});return {cancelled:true};};
    await f.run('downloadVideo()');
    assert.deepEqual(f.calls.map(c=>c.path),['/api/select_save_video']);
    assert.equal(f.element('btnDownloadVideo').disabled,false);
  }
  {
    const f=fixture();await f.run('downloadVideo()');await f.run('downloadVideo()');
    assert.equal(f.calls.filter(c=>c.path==='/api/render').length,1,'Repeated download must reuse Full HD');
    assert.equal(f.calls.filter(c=>c.path==='/api/save_video').length,2);
    f.element('quoteInput').value='Nội dung mới.';
    f.run('state.revision++');await f.run('downloadVideo()');
    assert.equal(f.calls.filter(c=>c.path==='/api/render').length,2,'Changed content needs a fresh render');
  }
  {
    const f=fixture(),original=f.context.record;
    f.context.record=async(path,body)=>{
      if(path==='/api/select_save_video'){
        f.element('quoteInput').value='Bản nháp đã thay đổi.';f.run('state.revision++');
      }
      return original(path,body);
    };
    await f.run('downloadVideo()');
    const planned=f.calls.find(c=>c.path==='/api/plan').body;
    assert.equal(planned.quote,'Hạnh phúc không phải đến từ xa.','Save must use the click-time snapshot');
    assert.equal(f.run('state.lastRenderedUrl'),null,'An older export must not replace the current preview');
  }
  {
    const f=fixture(),original=f.context.record;let fail=true;
    f.context.record=async(path,body)=>{
      if(path==='/api/save_video'&&fail){fail=false;throw Error('Disk full');}
      return original(path,body);
    };
    await f.run('downloadVideo()');await f.run('downloadVideo()');
    assert.equal(f.calls.filter(c=>c.path==='/api/render').length,1,'Copy failure must keep the finished render');
    f.run("state.settings.last_save_directory='D:/old';lastSavedSettings=payload();");
    assert.equal(f.run("Object.hasOwn(payload(),'last_save_directory')"),false,'Autosave must not overwrite the server-remembered folder');
  }
  console.log('Download UI: cancel, reuse, changes, snapshot, copy retry and folder isolation passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
