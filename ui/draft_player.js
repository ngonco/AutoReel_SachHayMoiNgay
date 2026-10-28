'use strict';
// This player consumes server scene/timing/layout data; it never allocates footage or lays out text.
class DraftPlayer {
  constructor({canvas,request,loadOverlay,onStatus,onTime,onState,onAudioBlocked,onAudioState}) {
    Object.assign(this,{canvas,request,loadOverlay,onStatus,onTime,onState,onAudioBlocked,onAudioState});
    this.ctx=canvas.getContext('2d');this.generation=0;this.running=false;this.time=0;
    this.videos=[0,1].map(index=>{const video=document.createElement('video');video.muted=true;video.playsInline=true;video.preload='auto';
      video.style.display='none';video.setAttribute('aria-hidden','true');video.dataset.draftSlot=index;canvas.parentElement?.append(video);return video;});
    this.slots=[{},{}];this.images=new Map();this.media=[];this.audio=new Audio();this.audio.loop=true;
    this.audio.style.display='none';this.audio.dataset.draftMusic='true';canvas.parentElement?.append(this.audio);
    this.audioBlocked=false;this.audioEpoch=0;this.audioPlayRequest=null;this.last=0;this.waiting=false;
  }
  unlockAudio() {
    this.audio.muted=false;this.audioBlocked=false;this.onAudioBlocked?.(false);
    // Resume the output graph in the actual click, before any plan/network awaits.
    const Context=typeof AudioContext!=='undefined'?AudioContext:null;
    if(Context&&!this.audioContext) {
      this.audioContext=new Context();this.musicSource=this.audioContext.createMediaElementSource(this.audio);
      this.musicGain=this.audioContext.createGain();this.musicGain.gain.value=0;
      this.analyser=this.audioContext.createAnalyser();this.analyser.fftSize=512;this.audioSamples=new Float32Array(512);
      this.musicSource.connect(this.musicGain);this.musicGain.connect(this.analyser);this.analyser.connect(this.audioContext.destination);
    }
    if(this.audioContext?.state!=='running'&&this.audioContext) {
      this.audioContext.resume().then(()=>{
        if(this.audioContext.state==='running'){this.audioBlocked=false;this.onAudioBlocked?.(false);if(this.running)this.requestAudio();}
      }).catch(()=>this.blockAudio());
    }
    this.audioTime();
  }
  blockAudio() {
    this.audioBlocked=true;this.onAudioBlocked?.(true);this.reportAudio();
  }
  pauseAudio() {
    this.audioEpoch++;this.audioPlayRequest=null;this.audio.pause();
  }
  requestAudio(force=false) {
    if(!this.running||!this.plan?.music||this.plan.settings.music_volume<=0||this.audioBlocked&&!force)return;
    if(this.waiting||this.audio.readyState<2)return;
    if(this.audioContext&&this.audioContext.state!=='running'){this.blockAudio();return;}
    if(this.audioPlayRequest||!this.audio.paused)return;
    this.audio.muted=false;this.audioTime();
    const request={epoch:this.audioEpoch,generation:this.generation};this.audioPlayRequest=request;
    Promise.resolve(this.audio.play()).then(()=>{
      if(request.epoch===this.audioEpoch&&request.generation===this.generation){this.audioBlocked=false;this.onAudioBlocked?.(false);}
    }).catch(error=>{
      if(request.epoch!==this.audioEpoch||request.generation!==this.generation||!this.running)return;
      // Buffering/pause/load can abort play. It is retryable, not an autoplay denial.
      if(error.name==='AbortError')return;
      if(error.name==='NotAllowedError')this.blockAudio();
      else {this.onStatus('Không phát được nhạc nháp. Hãy chọn bài khác.',true);this.pause();}
    }).finally(()=>{if(this.audioPlayRequest===request)this.audioPlayRequest=null;});
  }
  enableAudio() {
    this.unlockAudio();
    if(!this.running)this.play(this.mode==='scene'?this.sceneAt(this.time).index:null);
    else this.requestAudio(true);
  }
  reportAudio() {
    const volume=this.plan?.music?this.plan.settings.music_volume:0;
    let level=0;
    if(this.analyser&&this.audioContext.state==='running') {
      this.analyser.getFloatTimeDomainData(this.audioSamples);
      level=Math.sqrt(this.audioSamples.reduce((sum,value)=>sum+value*value,0)/this.audioSamples.length);
    }
    const state=!this.plan?.music?'none':volume<=0?'muted':this.audioBlocked?'blocked':this.audio.paused?'paused':'playing';
    if(this.canvas.dataset){this.canvas.dataset.audioState=state;this.canvas.dataset.audioRms=String(level);this.canvas.dataset.audioVolume=String(volume);}
    this.onAudioState?.({state,volume,level});
  }
  pause() {
    this.running=false;cancelAnimationFrame(this.raf);this.videos.forEach(v=>v.pause());this.pauseAudio();this.onState?.(false);this.reportAudio();
  }
  clear(preserveMedia=false) {
    this.pause();this.generation++;clearTimeout(this.pollTimer);
    if(!preserveMedia){this.plan=null;this.media=[];}
  }
  async setPlan(plan,index=0) {
    this.pause();const generation=++this.generation;clearTimeout(this.pollTimer);
    const previous=this.plan,oldMedia=this.media;
    this.plan=plan;this.hasFrame=false;this.time=plan.scenes[index].text_start+.21;this.end=plan.duration;
    const musicIdentity=plan.music?`${plan.music.path}:${plan.music.size}:${plan.music.mtime_ns}`:'';
    if(this.musicIdentity!==musicIdentity){
      this.pauseAudio();this.musicIdentity=musicIdentity;
      if(plan.music_url){this.audio.src=plan.music_url;this.audio.load();}
      else this.audio.removeAttribute('src');
    }
    this.media=plan.scenes.map((scene,i)=>{
      const old=previous?.scenes.findIndex(s=>s.source.path===scene.source.path&&s.source.mtime_ns===scene.source.mtime_ns&&s.source.size===scene.source.size);
      return old>=0&&oldMedia[old]?.status==='ready'?{...oldMedia[old],index:i}:{index:i,status:'queued'};
    });
    this.videos.forEach(v=>v.pause());this.slots=this.slots.map(slot=>slot.loading||slot.seeking?{}:slot);
    plan.scenes.forEach((scene,i)=>{
      this.loadOverlay(plan,i).then(image=>{if(generation!==this.generation)return;this.images.set(scene.overlay_key,image);if(!this.running)this.draw();}).catch(error=>{if(generation===this.generation)this.onStatus(error.message,true);});
    });
    this.reportAudio();
    try {
      const result=await this.request('/api/draft_prepare',{plan_id:plan.plan_id,selected_scene:index});
      if(generation!==this.generation)return;
      this.updateMedia(result);this.poll(generation);
    } catch(error) {if(generation===this.generation)this.onStatus(error.message,true);}
  }
  updateMedia(result) {
    this.media=result.scenes;
    const scene=this.sceneAt(this.time);this.preload(scene?.index||0);
    if(!this.running)this.draw();
    const current=this.media[scene?.index||0];
    if(current?.status==='error')this.onStatus(current.error,true);
    else if(!this.running)this.onStatus(current?.status==='ready'?'Nháp tức thì sẵn sàng. Bấm Phát để xem.':'Đang chuẩn bị clip lần đầu; các lần xem sau dùng lại bản nhẹ.');
  }
  poll(generation) {
    if(generation!==this.generation||!this.plan||this.media.every(m=>['ready','error'].includes(m.status)))return;
    this.pollTimer=setTimeout(async()=>{
      try {
        const result=await this.request('/api/draft_status/'+this.plan.plan_id);
        if(generation!==this.generation)return;this.updateMedia(result);this.poll(generation);
      } catch(error) {if(generation===this.generation){this.onStatus(error.message,true);this.poll(generation);}}
    },200);
  }
  sceneAt(time) {return this.plan?.scenes.find(s=>time>=s.text_start&&time<s.text_end)||this.plan?.scenes.at(-1);}
  layersAt(time) {return this.plan.scenes.filter(s=>time>=s.start&&time<s.end);}
  slotFor(scene) {
    const position=scene.index%2,video=this.videos[position],media=this.media[scene.index];
    if(!media||media.status!=='ready')return null;
    let slot=this.slots[position];
    if(slot.index!==scene.index||slot.url!==media.url) {
      video.pause();slot={index:scene.index,url:media.url,loading:true,stepped:false};this.slots[position]=slot;
      const generation=this.generation;
      video.onloadeddata=()=>{
        if(this.generation!==generation||this.slots[position]!==slot)return;
        slot.loading=false;this.seekSource(video,slot,scene.source_start);if(!this.running)this.draw();
      };
      video.onerror=()=>{if(this.generation===generation){slot.error='Không đọc được footage nháp. Hãy quét lại kho.';this.onStatus(slot.error,true);}};
      video.src=media.url;video.load();
      video.dataset.sceneIndex=scene.index;
    }
    if(slot.rate!==scene.speed){
      try {video.playbackRate=scene.speed;slot.stepped=Math.abs(video.playbackRate-scene.speed)>.001;}
      catch {slot.stepped=true;}
      slot.rate=scene.speed;
    }
    return {video,slot};
  }
  seekSource(video,slot,target) {
    if(slot.seeking||Math.abs(video.currentTime-target)<.018&&video.readyState>=2)return;
    slot.seeking=true;video.pause();
    const generation=this.generation;
    video.onseeked=()=>{slot.seeking=false;video.onseeked=null;if(generation===this.generation&&!this.running)this.draw();};
    try {video.currentTime=Math.max(0,target);} catch {slot.seeking=false;}
  }
  preload(index) {
    if(!this.plan)return;
    const scene=this.plan.scenes[index];if(scene)this.slotFor(scene);
    const next=this.plan.scenes[index+1];if(next)this.slotFor(next);
  }
  async seek(time) {
    if(!this.plan)return;
    this.time=Math.max(0,Math.min(this.plan.duration-1/30,time));this.last=performance.now();
    this.videos.forEach(video=>video.pause());
    this.layersAt(this.time).forEach(scene=>{const entry=this.slotFor(scene);if(entry&&!entry.slot.loading)this.seekSource(entry.video,entry.slot,this.sourceTime(scene,this.time));});
    this.audioTime();this.draw();
    const index=this.sceneAt(this.time)?.index||0;
    this.request('/api/draft_prepare',{plan_id:this.plan.plan_id,selected_scene:index}).catch(()=>{});
  }
  sourceTime(scene,time) {return Math.min(scene.source_end-1/60,scene.source_start+Math.max(0,time-scene.start)*scene.speed);}
  async play(index=null) {
    if(!this.plan)return;
    this.pause();
    if(index!==null){this.time=this.plan.scenes[index].text_start;this.end=this.plan.scenes[index].text_end;this.mode='scene';}
    else {this.end=this.plan.duration;this.mode='reel';if(this.time>=this.end-1/30)this.time=0;}
    this.running=true;this.last=performance.now();this.onState?.(true);
    this.audioTime();
    this.onStatus(this.mode==='scene'?`Đang xem cảnh ${index+1}.`:'Đang xem nháp toàn Reel.');
    this.tick(this.last);
  }
  audioTime() {
    if(Number.isFinite(this.audio.duration)&&this.audio.duration>0) {
      const target=this.time%this.audio.duration;
      if(Math.abs(this.audio.currentTime-target)>.12)this.audio.currentTime=target;
    }
    if(this.plan) {
      const fade=Math.min(1,this.time/.6,Math.max(0,this.plan.duration-this.time)/1.2);
      const volume=(this.plan.music?this.plan.settings.music_volume:0)*Math.max(0,fade);
      if(this.musicGain){this.audio.volume=1;this.musicGain.gain.value=volume;}
      else this.audio.volume=volume;
      this.audio.muted=false;
    }
  }
  draw(time=this.time) {
    if(!this.plan)return false;
    const layers=this.layersAt(time),scene=this.sceneAt(time),image=this.images.get(scene?.overlay_key);
    if(!image){if(this.canvas.dataset)this.canvas.dataset.waitReason='overlay';return false;}
    const entries=layers.map(s=>({scene:s,...(this.slotFor(s)||{})}));
    if(entries.some(e=>!e.video||e.slot.loading||e.slot.seeking||e.slot.error||e.video.readyState<2)){
      if(this.canvas.dataset)this.canvas.dataset.waitReason=entries.map(e=>`${e.scene.index}:${!e.video?'proxy':e.slot.loading?'loading':e.slot.seeking?'seeking':e.slot.error?'error':e.video.readyState}`).join(',');return false;
    }
    for(const entry of entries) {
      const target=this.sourceTime(entry.scene,time),{video,slot}=entry;
      if(slot.stepped) {
        if(Math.abs(video.currentTime-target)>1/30){this.seekSource(video,slot,target);return false;}
      } else if(Math.abs(video.currentTime-target)>.14){if(this.canvas.dataset)this.canvas.dataset.waitReason='sync:'+entry.scene.index;this.seekSource(video,slot,target);return false;}
      if(this.running&&!slot.stepped&&video.paused)video.play().catch(()=>{});
    }
    const width=this.canvas.width,height=this.canvas.height,ctx=this.ctx;
    ctx.clearRect(0,0,width,height);
    entries.forEach(({scene:s,video},i)=>{
      ctx.globalAlpha=i===0?1:Math.max(0,Math.min(1,(time-s.start)/this.plan.transition));
      ctx.drawImage(video,0,0,width,height);
    });
    ctx.globalAlpha=Math.max(0,Math.min(1,(time-scene.text_start)/.2,(scene.text_end-time)/.2));
    ctx.drawImage(image,0,0,width,height);ctx.globalAlpha=1;
    if(!this.hasFrame&&this.operationStartedAt&&this.canvas.dataset)
      this.canvas.dataset.firstFrameMs=String(Math.round(performance.now()-this.operationStartedAt));
    this.hasFrame=true;if(this.canvas.dataset)this.canvas.dataset.waitReason='';this.onTime?.(time,scene.index);return true;
  }
  tick(now) {
    if(!this.running||!this.plan)return;
    const failed=this.layersAt(this.time).map(scene=>this.media[scene.index]).find(item=>item?.status==='error');
    if(failed){this.pause();this.onStatus(failed.error+' Bấm Phát để thử lại.',true);return;}
    const decoderError=this.layersAt(this.time).map(scene=>this.slots[scene.index%2]).find(slot=>slot.error);
    if(decoderError||this.plan.music&&this.audio.error){this.pause();this.onStatus(decoderError?.error||'Không đọc được nhạc nháp. Hãy chọn bài khác.',true);return;}
    const delta=Math.min(.1,Math.max(0,(now-this.last)/1000));this.last=now;
    const target=Math.min(this.end-1/1000,this.time+delta);
    const musicWaiting=this.plan.music&&this.plan.settings.music_volume>0&&!this.audioBlocked&&this.audio.readyState<2;
    const ready=!musicWaiting&&this.draw(target);
    if(ready) {
      this.time=target;this.audioTime();
      if(this.waiting){this.waiting=false;this.onStatus('Đang xem nháp tức thì.');}
      this.requestAudio();
      if(this.time>=this.end-1/500){this.time=this.end;this.pause();this.onTime?.(this.time,this.sceneAt(this.time)?.index||0);this.onStatus('Đã phát hết. Có thể phát lại hoặc chọn footage khác.');return;}
      const index=this.sceneAt(this.time).index;
      // During overlap both slots are in use; preload the following scene afterwards.
      if(this.layersAt(this.time).length===1)this.preload(index);
    } else {
      this.pauseAudio();this.videos.forEach(video=>video.pause());
      if(!this.waiting){this.waiting=true;this.onStatus('Đang tải clip nháp; giữ đồng bộ hình, chữ và nhạc.');}
    }
    this.reportAudio();this.raf=requestAnimationFrame(time=>this.tick(time));
  }
}
if(typeof module!=='undefined')module.exports={DraftPlayer};
