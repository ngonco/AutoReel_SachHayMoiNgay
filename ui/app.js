'use strict';
// The server owns segmentation, timing, fonts, scenes and rendering.
const $ = id => document.getElementById(id);
const canvas = $('previewCanvas'), ctx = canvas.getContext('2d'), player = $('previewVideo');
const THEME_NAMES = ['Thiền Vàng', 'Tinh Khôi', 'Kinh Điển', 'Điện Ảnh', 'Sen Giấy'];
const state = {quotes: [], videos: [], currentQuoteIndex: 0, currentVideo: null, plan: null,
  revision: 0, planPromise: null, selectedScene: 0, loadedPlan: null, loadedKind: null,
  lastRenderedUrl: null, previewUrl: null, busyPreview: false, ready: false,
  settings: {credit_size:20, quote_size:68, theme_index:0, pos_mode:'auto', vertical_offset:0,
    shade:.7, duration:12, auto_paginate:true, autofit:true, music_volume:.85,
    outline_enabled:true, outline_color:'auto', outline_width:4, outline_blur:8, outline_opacity:.85}};
let saveTimer, planTimer;
let saving=false, savePending=false, lastSavedSettings={}, saveSequence=0;
const saveClientId=crypto.randomUUID();

async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok || data.success === false) {const error=new Error(data.error || 'Không thực hiện được yêu cầu.');error.code=data.code;throw error;}
  return data;
}
function payload() {
  return {...state.settings, quote:$('quoteInput').value.normalize('NFC'), quote_index:state.currentQuoteIndex,
    credit:$('creditInput').value.normalize('NFC'), video_path:state.currentVideo?.path || '', safe_zone:$('safeZoneCheck').checked};
}
function changedSettings(snapshot) {
  return Object.fromEntries(Object.entries(snapshot).filter(([key,value])=>JSON.stringify(value)!==JSON.stringify(lastSavedSettings[key])));
}
function queueSave() {
  if(!state.ready)return;
  savePending=true;$('saveStatus').textContent='Đang lưu…';
  clearTimeout(saveTimer);saveTimer=setTimeout(flushSaves,250);
}
async function flushSaves() {
  if(saving)return;
  saving=true;let failed=false;
  try {
    while(savePending) {
      savePending=false;
      const snapshot=JSON.parse(JSON.stringify(payload())),patch=changedSettings(snapshot);
      if(Object.keys(patch).length)await api('/api/settings',{_client_id:saveClientId,_sequence:++saveSequence,_patch:patch});
      lastSavedSettings=snapshot;
    }
    $('saveStatus').textContent='Đã lưu tự động';
  } catch(error) {
    failed=true;savePending=true;$('saveStatus').textContent='Chưa lưu được; đang tự thử lại: '+error.message;
  } finally {
    saving=false;
    if(savePending){clearTimeout(saveTimer);saveTimer=setTimeout(flushSaves,failed?2500:0);}
  }
}
function saveBeforeExit() {
  if(!state.ready)return;
  clearTimeout(saveTimer);
  const patch=changedSettings(payload());
  if(!Object.keys(patch).length)return;
  const body=JSON.stringify({_client_id:saveClientId,_sequence:++saveSequence,_patch:patch});
  if(!navigator.sendBeacon('/api/settings',new Blob([body],{type:'application/json'})))
    fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body,keepalive:true}).catch(()=>{});
}
function status(message, error=false) {
  $('playbackStatus').textContent = message;
  $('playbackStatus').classList.toggle('error', error);
}
function showStatic() {
  player.pause();
  player.style.display = 'none';
  canvas.style.display = 'block';
  $('btnTogglePlayVideo').textContent = '▶ Phát toàn bộ reel';
}
function invalidate() {
  if (!state.ready) return;
  state.revision++;
  state.plan = null;
  state.planPromise = null;
  state.loadedPlan = null;
  state.previewUrl = null;
  state.lastRenderedUrl = null;
  state.selectedScene = 0;
  $('btnWatchRendered').style.display = 'none';
  showStatic();
  status('Thiết lập đã đổi. Đang cập nhật cảnh; bản xem trước sẽ dựng lại khi bấm Play.');
  clearTimeout(planTimer);
  planTimer = setTimeout(() => ensurePlan().catch(error => status(error.message, true)), 350);
  queueSave();
}
async function ensurePlan() {
  if (state.plan) return state.plan;
  if (state.planPromise) return state.planPromise;
  const revision = state.revision;
  const promise = api('/api/plan', payload()).then(plan => {
    if (revision !== state.revision) throw new Error('Thiết lập vừa thay đổi. Hãy bấm Play lại sau khi cập nhật.');
    state.plan = plan;
    state.selectedScene = Math.min(state.selectedScene, plan.scenes.length - 1);
    renderScenes();
    drawStill();
    status(`Sẵn sàng: ${plan.scenes.length} cảnh · ${timeLabel(plan.duration)}. Bấm Play để dựng và xem toàn bộ.`);
    return plan;
  }).finally(() => {if (revision === state.revision) state.planPromise = null;});
  state.planPromise = promise;
  return promise;
}
function timeLabel(t) {return Number(t).toFixed(1) + 's';}
function renderScenes() {
  const plan = state.plan;
  if (!plan) return;
  $('paginationBadge').textContent = `${plan.scenes.length} cảnh${plan.segmentation_mode === 'manual_lines' ? ' theo dòng' : ''} · ${timeLabel(plan.duration)}`;
  $('totalDuration').textContent = `Tổng reel: ${timeLabel(plan.duration)} · tối thiểu ${state.settings.duration}s`;
  $('btnRenderSingle').textContent = `▶ XUẤT REEL · ${timeLabel(plan.duration)}`;
  $('previewStyleName').textContent = THEME_NAMES[state.settings.theme_index];
  const first=plan.scenes[0],pool=plan.footage_pool;
  if(pool)$('currentVideoName').textContent=`Cảnh đầu: ${first.video_name} · ${pool.remaining}/${pool.total} clip chưa dùng ở lượt này.`+(pool.preferred_replaced?' Clip đã chọn được đổi theo lượt footage chống trùng.':'');
  $('sceneList').replaceChildren();
  $('slideTabs').replaceChildren();
  plan.scenes.forEach((scene, index) => {
    const tab = document.createElement('button');
    tab.className = 'slide-tab' + (index === state.selectedScene ? ' active' : '');
    tab.textContent = `Cảnh ${index + 1} · ${timeLabel(scene.text_start)}–${timeLabel(scene.text_end)}`;
    tab.onclick = () => seekScene(index);
    $('slideTabs').append(tab);
    const item = document.createElement('button');
    item.className = 'scene-card' + (index === state.selectedScene ? ' active' : '');
    item.dataset.scene = index;
    const meta = document.createElement('span');
    meta.className = 'scene-meta';
    meta.textContent = `${index + 1}. ${scene.video_name} · ${timeLabel(scene.text_start)}–${timeLabel(scene.text_end)} · nguồn ${timeLabel(scene.source_start)}–${timeLabel(scene.source_end)}` + (scene.speed < .999 ? ` · tốc độ ${scene.speed.toFixed(2)}×` : '');
    const text = document.createElement('span');
    text.textContent = scene.text;
    item.append(meta, text);
    item.onclick = () => seekScene(index);
    $('sceneList').append(item);
  });
  updateSceneLabels();
}
function updateSceneLabels() {
  if (!state.plan) return;
  const index = state.selectedScene, scene = state.plan.scenes[index];
  $('previewSlideIndicator').textContent = `Cảnh ${index + 1} / ${state.plan.scenes.length}`;
  $('slidePreviewText').textContent = scene.text;
  $('aiRecommendText').textContent = `Cảnh ${index + 1}: ${scene.video_name} · chữ ${scene.resolved_pos === 'top' ? 'nửa trên' : scene.resolved_pos === 'center' ? 'chính giữa' : 'nửa dưới'}. Kiểm tra lại vị trí nếu chủ thể di chuyển.`;
  $('posBadge').textContent = state.settings.pos_mode === 'auto' ? 'Tự động theo từng cảnh' : 'Vị trí thủ công';
  document.querySelectorAll('.scene-card, .slide-tab').forEach(element => {
    const list = [...element.parentElement.children];
    element.classList.toggle('active', list.indexOf(element) === index);
  });
}
function seekScene(index) {
  state.selectedScene = index;
  updateSceneLabels();
  if (state.loadedPlan === state.plan?.plan_id && player.src && player.readyState >= 1) {
    player.currentTime = state.plan.scenes[index].text_start + .25;
    player.style.display = 'block';
    canvas.style.display = 'none';
  } else drawStill();
}
async function loadImage(url) {
  return new Promise((resolve,reject) => {const im = new Image(); im.onload=()=>resolve(im); im.onerror=()=>reject(new Error('Không tải được ảnh xem trước.')); im.src=url;});
}
async function drawStill() {
  const plan = state.plan, index = state.selectedScene;
  if (!plan) return;
  try {
    const scene = plan.scenes[index];
    const [background, overlay] = await Promise.all([loadImage(scene.thumb_url),loadImage(`/api/overlay/${plan.plan_id}/${index}`)]);
    if (state.plan !== plan || state.selectedScene !== index || player.style.display !== 'none') return;
    ctx.clearRect(0,0,1080,1920);
    const scale = Math.max(1080/background.width,1920/background.height);
    const w=background.width*scale,h=background.height*scale;
    ctx.drawImage(background,(1080-w)/2,(1920-h)/2,w,h);
    ctx.drawImage(overlay,0,0);
  } catch(error) {status(error.message,true);}
}
function populateQuotes() {
  $('quoteSelect').replaceChildren();
  state.quotes.forEach((q,index)=>{const option=document.createElement('option');option.value=index;option.textContent=`Câu ${index+1}: ${q.quote.substring(0,55)}…`;$('quoteSelect').append(option);});
  $('btnBatchRender').textContent=`⚡ XUẤT ${state.quotes.length} REEL`;
}
function loadQuote(index) {
  if (!state.quotes.length) return;
  state.currentQuoteIndex=(index+state.quotes.length)%state.quotes.length;
  $('quoteSelect').value=state.currentQuoteIndex;
  $('quoteCounter').textContent=`Câu ${state.currentQuoteIndex+1} / ${state.quotes.length}`;
  $('quoteInput').value=state.quotes[state.currentQuoteIndex].quote.normalize('NFC');
  invalidate();
}
function populateVideos() {
  $('videoCarousel').replaceChildren();
  state.videos.forEach(video=>{
    const card=document.createElement('button');card.className='video-card'+(state.currentVideo?.path===video.path?' active':'');
    const img=document.createElement('img');img.src=video.thumb_url;img.alt=video.name;img.loading='lazy';
    const badge=document.createElement('span');badge.className='video-card-badge';badge.textContent=video.name;
    card.append(img,badge);card.onclick=()=>selectVideo(video);$('videoCarousel').append(card);
  });
  $('videoCountBadge').textContent=`${state.videos.length} clip`;
}
function selectVideo(video) {
  state.currentVideo=video;
  $('currentVideoName').textContent=`Cảnh đầu: ${video.name} (${timeLabel(video.duration)}). Cảnh sau tự chọn clip khác.`;
  populateVideos();invalidate();
}
function applySettings() {
  const s=state.settings;
  const sliders={verticalSlider:['vertical_offset','verticalVal',' px',1],shadeSlider:['shade','shadeVal','%',100],quoteSizeSlider:['quote_size','quoteSizeVal','',1],creditSizeSlider:['credit_size','creditSizeVal','',1],musicVolSlider:['music_volume','musicVolVal','%',100],outlineWidthSlider:['outline_width','outlineWidthVal',' px',1],outlineBlurSlider:['outline_blur','outlineBlurVal',' px',1],outlineOpacitySlider:['outline_opacity','outlineOpacityVal','%',100]};
  Object.entries(sliders).forEach(([id,[key,label,suffix,factor]])=>{
    $(id).value=Math.round(s[key]*factor);$(label).textContent=$(id).value+suffix;
    $(id).oninput=()=>{s[key]=Number($(id).value)/factor;$(label).textContent=$(id).value+suffix;if(key==='vertical_offset')$('verticalNumber').value=s[key];invalidate();};
  });
  $('verticalNumber').value=s.vertical_offset;
  $('verticalNumber').onchange=()=>{
    const input=$('verticalNumber');
    if(input.value.trim()==='' || !Number.isFinite(input.valueAsNumber)) {input.value=s.vertical_offset;return;}
    s.vertical_offset=Math.max(Number(input.min),Math.min(Number(input.max),Math.trunc(input.valueAsNumber)));
    input.value=s.vertical_offset;
    $('verticalSlider').value=s.vertical_offset;
    $('verticalVal').textContent=s.vertical_offset+' px';
    invalidate();
  };
  const outlineControls=['outlineAutoColorCheck','outlineColorInput','outlineWidthSlider','outlineBlurSlider','outlineOpacitySlider'];
  const setOutlineDisabled=()=>outlineControls.forEach(id=>{$(id).disabled=!s.outline_enabled;});
  $('outlineEnabledCheck').checked=s.outline_enabled;
  $('outlineEnabledCheck').onchange=()=>{s.outline_enabled=$('outlineEnabledCheck').checked;setOutlineDisabled();invalidate();};
  $('outlineAutoColorCheck').checked=s.outline_color==='auto';
  $('outlineColorInput').value=s.outline_color==='auto'?(s.theme_index===4?'#fff8e9':'#101018'):s.outline_color;
  $('outlineColorInput').oninput=()=>{s.outline_color=$('outlineColorInput').value;$('outlineAutoColorCheck').checked=false;invalidate();};
  $('outlineAutoColorCheck').onchange=()=>{s.outline_color=$('outlineAutoColorCheck').checked?'auto':$('outlineColorInput').value;applySettings();invalidate();};
  setOutlineDisabled();
  [['autofitCheck','autofit'],['autoPaginateCheck','auto_paginate']].forEach(([id,key])=>{$(id).checked=s[key];$(id).onchange=()=>{s[key]=$(id).checked;invalidate();};});
  document.querySelectorAll('.pos-chip').forEach(el=>{el.classList.toggle('active',el.dataset.pos===s.pos_mode);el.onclick=()=>{s.pos_mode=el.dataset.pos;applySettings();invalidate();};});
  document.querySelectorAll('.template-btn').forEach(el=>{el.classList.toggle('active',Number(el.dataset.theme)===s.theme_index);el.onclick=()=>{s.theme_index=Number(el.dataset.theme);applySettings();invalidate();};});
  document.querySelectorAll('.duration-btn').forEach(el=>{el.classList.toggle('active',Number(el.dataset.dur)===s.duration);el.onclick=()=>{s.duration=Number(el.dataset.dur);applySettings();invalidate();};});
  $('themeNameBadge').textContent=THEME_NAMES[s.theme_index];
}
async function pollJob(job, progress) {
  while (!['done','error'].includes(job.status)) {
    progress?.(job);
    await new Promise(resolve=>setTimeout(resolve,650));
    job=await api(`/api/jobs/${job.job_id}`);
  }
  progress?.(job);
  if(job.status==='error') {const error=new Error(job.error);error.code=job.code;throw error;}
  return job.result;
}
async function playUrl(url, kind, plan) {
  if(state.loadedPlan!==plan.plan_id || state.loadedKind!==kind || player.getAttribute('src')!==url) {
    player.src=url;
    await new Promise((resolve,reject)=>{
      player.onloadedmetadata=()=>{player.onloadedmetadata=null;player.onerror=null;resolve();};
      player.onerror=()=>{player.onloadedmetadata=null;reject(new Error('Không phát được video. Kiểm tra nhật ký hoặc mở file đã xuất.'));};
      player.load();
    });
  }
  if (state.plan?.plan_id !== plan.plan_id) return;
  state.loadedPlan=plan.plan_id;state.loadedKind=kind;
  player.loop=false;player.muted=false;player.volume=1;
  player.controls=true;player.style.display='block';canvas.style.display='none';
  if(player.ended || player.currentTime>=plan.duration-.1) player.currentTime=0;
  try {await player.play();} catch {status('Video đã sẵn sàng. Bấm nút phát trên video để bắt đầu.');}
}
async function togglePlayback() {
  if(state.busyPreview) return;
  if(state.loadedPlan===state.plan?.plan_id && !player.paused) {player.pause();return;}
  const button=$('btnTogglePlayVideo');
  state.busyPreview=true;button.disabled=true;
  try {
    const plan=await ensurePlan(), revision=state.revision;
    if(state.loadedPlan===plan.plan_id && state.loadedKind) {
      await playUrl(state.loadedKind === 'export' ? state.lastRenderedUrl : state.previewUrl,state.loadedKind,plan);return;
    }
    status('Đang chuẩn bị bản xem trước nhẹ…');
    const result=await pollJob(await api('/api/preview',{plan_id:plan.plan_id}),job=>status(`${job.message} · ${job.progress}%`));
    if(revision!==state.revision) {status('Thiết lập đã đổi. Bấm Play để dựng bản mới.');return;}
    state.previewUrl=result.url;
    await playUrl(result.url,'preview',plan);
    status(`Đang xem toàn bộ reel · ${plan.scenes.length} cảnh · ${timeLabel(plan.duration)}`);
  } catch(error) {status(error.message,true);}
  finally {state.busyPreview=false;button.disabled=false;button.textContent=player.paused?'▶ Phát toàn bộ reel':'⏸ Tạm dừng reel';}
}
function renderProgress(job) {
  $('progressBox').classList.add('active');$('progressBarFill').style.width=job.progress+'%';
  $('progressPercent').textContent=job.progress+'%';$('progressStatus').textContent=job.message;
}
async function renderSingle() {
  const button=$('btnRenderSingle');button.disabled=true;
  try {
    let plan,result,revision;
    for(let attempt=0;attempt<2;attempt++) {
      clearTimeout(planTimer);state.revision++;state.plan=null;state.planPromise=null;state.loadedPlan=null;showStatic();
      $('btnWatchRendered').style.display='none';
      plan=await ensurePlan();revision=state.revision;
      try {result=await pollJob(await api('/api/render',{plan_id:plan.plan_id,async:true}),renderProgress);break;}
      catch(error){if(error.code!=='footage_conflict'||attempt===1)throw error;}
    }
    $('progressStatus').textContent=`Đã xuất ${timeLabel(result.duration)} · ${result.filename}`;
    if(revision===state.revision) {state.lastRenderedUrl=result.url;$('btnWatchRendered').style.display='inline-flex';}
  } catch(error) {$('progressBox').classList.add('active');$('progressStatus').textContent=error.message;}
  finally {button.disabled=false;}
}
async function renderBatch() {
  const button=$('btnStartBatchRender');button.disabled=true;
  try {
    const result=await pollJob(await api('/api/batch_render',{...payload(),async:true}),job=>{
      $('batchStatus').textContent=job.message;$('batchPercent').textContent=job.progress+'%';$('batchBarFill').style.width=job.progress+'%';
    });
    $('batchStatus').textContent=`Đã xuất ${result.total_rendered}/${state.quotes.length} reel.`+(result.failures.length?' Lỗi: '+result.failures.map(f=>`Câu ${f.index}: ${f.error}`).join('; '):'');
  } catch(error) {$('batchStatus').textContent=error.message;}
  finally {button.disabled=false;}
}
async function initApp() {
  showStatic();status('Đang đọc nội dung và kho clip…');
  try {
    const [quotes,videos,settings]=await Promise.all([api('/api/quotes'),api('/api/videos'),api('/api/settings')]);
    state.quotes=quotes;state.videos=videos;state.settings=settings;lastSavedSettings=JSON.parse(JSON.stringify(settings));
    $('creditInput').value=settings.credit;
    populateQuotes();loadQuote(Math.min(settings.quote_index||0,Math.max(0,quotes.length-1)));
    if(settings.quote!==null && typeof settings.quote==='string')$('quoteInput').value=settings.quote;
    if(videos.length) selectVideo(videos.find(v=>v.path===settings.video_path)||videos[0]);
    $('safeZoneCheck').checked=!!settings.safe_zone;
    $('safeZoneOverlay').classList.toggle('visible',!!settings.safe_zone);
    applySettings();
    $('quoteSelect').onchange=()=>loadQuote(Number($('quoteSelect').value));
    $('btnPrevQuote').onclick=()=>loadQuote(state.currentQuoteIndex-1);
    $('btnNextQuote').onclick=()=>loadQuote(state.currentQuoteIndex+1);
    $('btnRandQuote').onclick=()=>loadQuote(Math.floor(Math.random()*state.quotes.length));
    $('quoteInput').oninput=invalidate;$('creditInput').oninput=invalidate;
    $('btnRandomVideo').onclick=()=>{if(state.videos.length)selectVideo(state.videos[Math.floor(Math.random()*state.videos.length)]);};
    document.querySelector('label[for="uploadVideoInput"]').onclick=async event=>{
      event.preventDefault();
      try {const result=await api('/api/select_video',{});if(result.video){if(!state.videos.some(v=>v.path===result.video.path))state.videos.push(result.video);selectVideo(result.video);}}
      catch(error){status(error.message,true);}
    };
    $('safeZoneCheck').onchange=()=>{$('safeZoneOverlay').classList.toggle('visible',$('safeZoneCheck').checked);queueSave();};
    const sample=new Audio('/assets/thien_chuong.wav');
    $('btnTestAudio').onclick=()=>{sample.volume=state.settings.music_volume;sample.currentTime=0;sample.play().catch(error=>status(error.message,true));};
    $('btnTogglePlayVideo').onclick=togglePlayback;
    $('btnWatchRendered').onclick=()=>{if(state.lastRenderedUrl&&state.plan)playUrl(state.lastRenderedUrl,'export',state.plan).catch(error=>status(error.message,true));};
    $('btnOpenFolder').onclick=()=>api('/api/open_folder',{}).catch(error=>status(error.message,true));
    $('btnRenderSingle').onclick=renderSingle;
    $('btnBatchRender').onclick=()=>{$('batchModal').classList.add('active');};
    $('btnCloseBatchModal').onclick=()=>$('batchModal').classList.remove('active');
    $('btnStartBatchRender').onclick=renderBatch;
    player.onplay=()=>{$('btnTogglePlayVideo').textContent='⏸ Tạm dừng reel';};
    player.onpause=()=>{$('btnTogglePlayVideo').textContent='▶ Tiếp tục reel';};
    player.onended=()=>{$('btnTogglePlayVideo').textContent='↻ Phát lại toàn bộ reel';status('Đã phát hết câu nói. Có thể phát lại từ đầu.');};
    player.ontimeupdate=()=>{
      if(!state.plan||state.loadedPlan!==state.plan.plan_id)return;
      const i=state.plan.scenes.findIndex(s=>player.currentTime>=s.text_start&&player.currentTime<s.text_end);
      if(i>=0&&i!==state.selectedScene){state.selectedScene=i;updateSceneLabels();}
      $('playbackTime').textContent=`${timeLabel(player.currentTime)} / ${timeLabel(state.plan.duration)}`;
    };
    state.ready=true;
    queueSave();
    await ensurePlan();
  } catch(error) {status(error.message,true);}
}
window.addEventListener('DOMContentLoaded',initApp);
window.addEventListener('pagehide',saveBeforeExit);
