const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const calls=[];
function context(){return {clearRect(){},drawImage(...args){calls.push({op:this.globalCompositeOperation,args});},save(){},restore(){}};}
const sandbox=vm.createContext({document:{createElement:()=>({getContext:()=>context()})},module:{exports:{}}});
vm.runInContext(fs.readFileSync('ui/scroll_player.js','utf8'),sandbox);
const {ScrollTextLayer}=sandbox.module.exports;
const plan={plan_id:'p',text_track:{rect:{x:119,y:1325,width:842,height:256},distance:900,initial_offset:0,
  scroll_start:2,scroll_end:18,duration:20,fade_seconds:.2,tiles:[0,1,2].map(index=>({index,y:index*512,height:512}))}};
(async()=>{
  const requested=[];
  const layer=await ScrollTextLayer.create(plan,async url=>{requested.push(url);return {url};});
  assert.equal(requested.length,2,'Only mask and initial visible tile load initially');
  assert.equal(layer.offset(1),0);assert.equal(layer.offset(2),0);assert.equal(layer.offset(18),900);assert.equal(layer.offset(19),900);
  assert.equal(layer.offset(10),450,'Motion uses global Reel time independently of footage boundaries');
  const pen=context();await layer.prepare(10);
  assert.equal(layer.draw(pen,10,1080,1920),true);
  assert.ok(calls.some(call=>call.op==='destination-in'),'Fade mask clips the full glyph and halo layer');
  const placed=calls.at(-1).args;assert.deepEqual(placed.slice(1),[119,1325,842,256]);
  const short=new ScrollTextLayer({...plan,text_track:{...plan.text_track,distance:0,initial_offset:-50}},async()=>({}));
  assert.equal(short.offset(0),-50);assert.equal(short.offset(19),-50);
  const failed=new ScrollTextLayer(plan,async()=>{throw new Error('Asset failed');});
  await assert.rejects(failed.prepare(0),/Asset failed/);assert.throws(()=>failed.draw(pen,0,1080,1920),/Asset failed/);
  console.log('Scroll player: global time, endpoint holds, static content, lazy assets, mask clipping and asset errors passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
