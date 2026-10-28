// Catalog updates must never replace the active draft, plan, export or batch snapshot.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function fixture(){
  const elements=new Map();
  const element=id=>{
    if(!elements.has(id))elements.set(id,{value:'',textContent:'',checked:false,style:{},children:[],
      classList:{add(){},toggle(){}},getContext(){return{};},pause(){},
      replaceChildren(){this.children=[];},append(child){this.children.push(child);},querySelector(selector){return element(id+':'+selector);}});
    return elements.get(id);
  };
  const context=vm.createContext({document:{getElementById:element,createElement:()=>({})},window:{addEventListener(){}},
    crypto:require('node:crypto').webcrypto,setTimeout:()=>0,clearTimeout(){},setInterval(){},console});
  vm.runInContext(fs.readFileSync('ui/app.js','utf8'),context);
  const run=code=>vm.runInContext(code,context);
  run("state.ready=true;state.quotes=[{key:'a',quote:'Câu một.'},{key:'b',quote:'Câu hai.'}];state.currentQuoteIndex=1;state.plan={plan_id:'keep'};state.revision=9;state.lastRenderedUrl='/keep.mp4';");
  element('quoteInput').value='  Bản nháp đang sửa.\n\nGiữ cả Enter cuối.\n';
  const sync={enabled:true,syncing:false,source:'sheet',count:2,revision:'new',sheet_name:'Đạo lý hay mỗi ngày',last_success_at:1000,error:''};
  return {context,run,element,sync,apply:quotes=>{context.catalog={quotes,sync:{...sync,count:quotes.length}};run('applyQuoteCatalog(catalog)');}};
}
(async()=>{
  {
    const f=fixture(),draft=f.element('quoteInput').value;
    f.apply([{key:'b',quote:'Câu hai.'},{key:'a',quote:'Câu một.'},{key:'c',quote:'Câu mới.'}]);
    assert.equal(f.run('state.currentQuoteIndex'),0);
    assert.equal(f.element('quoteInput').value,draft);
    assert.equal(f.run('state.plan.plan_id'),'keep');assert.equal(f.run('state.revision'),9);
    assert.equal(f.run('state.lastRenderedUrl'),'/keep.mp4');
    assert.match(f.element('btnBatchRender').textContent,/3/);
    f.apply([{key:'a',quote:'Câu một.'},{key:'b-edited',quote:'Câu hai đã sửa.'}]);
    assert.equal(f.run('state.currentQuoteIndex'),-1);
    assert.equal(f.element('quoteSelect').value,'');assert.match(f.element('quoteCounter').textContent,/Bản nháp/);
    assert.equal(f.element('quoteInput').value,draft);
    f.apply([]);
    assert.equal(f.run('state.quotes.length'),0);assert.equal(f.element('btnBatchRender').disabled,true);
    assert.equal(f.element('btnDownloadVideo').disabled,false,'Manual draft remains exportable when sheet is empty');
    assert.equal(f.element('quoteInput').value,draft);
  }
  {
    const f=fixture();f.run("state.busyBatch=true;state.batchTotal=2;");
    f.element('batchStatus').textContent='Đang xuất câu 1/2';f.element('batchModal:h2').textContent='2 câu nói';
    f.apply([{key:'a',quote:'Câu một.'},{key:'b',quote:'Câu hai.'},{key:'c',quote:'Câu mới.'}]);
    assert.equal(f.element('batchStatus').textContent,'Đang xuất câu 1/2');
    assert.equal(f.element('batchModal:h2').textContent,'2 câu nói');assert.equal(f.run('state.batchTotal'),2);
    f.context.fakeApi=async()=>({status:'done',total:2,result:{total_rendered:2,total_requested:2,failures:[]}});
    f.run('api=fakeApi');await f.run('renderBatch()');
    assert.equal(f.element('batchStatus').textContent,'Đã xuất 2/2 reel.');
  }
  {
    const f=fixture(),calls=[];f.run("state.quoteCatalogRevision='same'");
    f.context.fakeApi=async path=>{calls.push(path);return {...f.sync,revision:'same'};};
    f.run('api=(...args)=>fakeApi(...args)');await f.run('refreshQuoteCatalog()');
    assert.deepEqual(calls,['/api/quote_sync']);
    const draft=f.element('quoteInput').value;
    f.context.fakeApi=async()=>{throw Error('Không kết nối');};await f.run('refreshQuoteCatalog()');
    assert.equal(f.element('quoteInput').value,draft);assert.equal(f.run('state.quotes.length'),2);
    assert.match(f.element('quoteSyncStatus').textContent,/Không kết nối/);
  }
  console.log('Sheet UI: add/edit/delete/reorder/empty preserve draft, plan, export and running batch; errors keep list.');
})().catch(error=>{console.error(error);process.exitCode=1;});
