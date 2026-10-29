'use strict';
// The server owns segmentation, timing, fonts, scenes and rendering.
const $ = id => document.getElementById(id);
const canvas = $('previewCanvas'), ctx = canvas.getContext('2d'), player = $('previewVideo');
const THEME_NAMES = ['Thiền Vàng', 'Tinh Khôi', 'Kinh Điển', 'Điện Ảnh', 'Sen Giấy', 'CHỮ CUỘN'];
const state = {quotes: [], videos: [], currentQuoteIndex: 0, currentVideo: null, plan: null,
  revision: 0, planPromise: null, selectedScene: 0, loadedPlan: null, loadedKind: null,
  lastRenderedUrl: null, lastExport: null, previewUrl: null, busyPreview: false, ready: false,
  previousFootageIds: [], lastAcceptedPlan: null, contextQuote: '', inventoryReady: true,
  busyExport: false, busyBatch: false, busyLibrary: false,
  quoteCatalogRevision:null, busyQuoteRefresh:false, batchTotal:0, downloadRevision:0,downloadRecords:[],busyMarkDownloaded:false,
  previewRequest:null, preparedPreviewPlan:null, pendingScenePlayback:null,
  musicTracks:[],previousMusicPath:'',
  settings: {credit_size:20, quote_size:68, theme_index:0, pos_mode:'auto', vertical_offset:0,
    shade:.7, duration:12, auto_paginate:true, autofit:true, music_volume:.85,scroll_speed:1,
    outline_enabled:true, outline_color:'auto', outline_width:4, outline_blur:8, outline_opacity:.85,
    background_video_directory:'',scene_video_preferences:{},imported_video_paths:[],music_mode:'random',music_path:'',music_seed:''}};
let saveTimer, planTimer, warmPreviewTimer;
let draft=null;
const overlayImages=new Map();
let saving=false, savePending=false, lastSavedSettings={}, saveSequence=0;
const saveClientId=crypto.randomUUID();

async function api(path, body) {
  const response = await fetch(path, body === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  const data = await response.json();
  if (!response.ok || data.success === false) {const error=new Error(data.error || 'Không thực hiện được yêu cầu.');error.code=data.code;throw error;}
  return data;
}
function payload() {
  const {last_save_directory, ...settings}=state.settings;
  return {...settings, quote:$('quoteInput').value.normalize('NFC'), quote_index:Math.max(0,state.currentQuoteIndex),
    credit:$('creditInput').value.normalize('NFC'), video_path:state.currentVideo?.path || '',
    previous_footage_ids:[...state.previousFootageIds],previous_music_path:state.previousMusicPath, safe_zone:$('safeZoneCheck').checked};
}
function changedSettings(snapshot) {
  return Object.fromEntries(Object.entries(snapshot).filter(([key,value])=>
    !['background_video_directory','previous_footage_ids','previous_music_path'].includes(key) && JSON.stringify(value)!==JSON.stringify(lastSavedSettings[key])));
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
  draft?.pause();
  player.pause();
  player.style.display = 'none';
  canvas.style.display = 'block';
  $('btnTogglePlayVideo').textContent = '▶ Phát toàn bộ reel';
}
function invalidate(options={}) {
  if (!state.ready) return;
  const quote=$('quoteInput').value.normalize('NFC').trim().split(/\s+/).join(' ');
  const content=$('quoteInput').value.normalize('NFC');
  const structureChanged=state.preferencesContent!==undefined&&(state.preferencesContent!==content||state.preferencePagination!==state.settings.auto_paginate||state.preferenceTheme!==undefined&&state.preferenceTheme!==state.settings.theme_index);
  if(structureChanged)
    state.settings.scene_video_preferences={};
  state.preferencesContent=content;state.preferencePagination=state.settings.auto_paginate;
  state.preferenceTheme=state.settings.theme_index;
  if(structureChanged){state.currentQuoteIndex=state.quotes.findIndex(q=>quoteIdentity(q.quote)===quoteIdentity(content));populateQuotes();}
  if(quote!==state.contextQuote) {
    const previous=state.lastAcceptedPlan;
    if(previous && previous.quote.trim().split(/\s+/).join(' ')!==quote)
      state.previousFootageIds=[...new Set(previous.scenes.map(scene=>scene.footage_id))];
    state.contextQuote=quote;
    state.previousMusicPath=state.lastAcceptedPlan?.music?.path||'';
    state.settings.music_seed=crypto.randomUUID();
  }
  state.revision++;
  draft?.clear(true);
  if(draft)draft.operationStartedAt=performance.now();
  state.plan = null;
  state.planPromise = null;
  state.loadedPlan = null;
  state.loadedKind = null;
  state.previewUrl = null;
  state.previewRequest = null;
  state.preparedPreviewPlan = null;
  clearTimeout(warmPreviewTimer);
  state.lastRenderedUrl = null;
  if(!options.preserveScene){if(structureChanged)state.selectedScene = 0;state.pendingScenePlayback=null;}
  $('btnWatchRendered').style.display = 'none';
  showStatic();
  status('Đang cập nhật cảnh cho nháp tức thì…');
  clearTimeout(planTimer);
  planTimer = setTimeout(() => ensurePlan().catch(error => status(error.message, true)), 350);
  updateDownloadStatus();
  queueSave();
}
async function ensurePlan() {
  if (state.plan) return state.plan;
  if (state.planPromise) return state.planPromise;
  const revision = state.revision;
  const promise = api('/api/plan', payload()).then(plan => {
    if (revision !== state.revision) throw new Error('Thiết lập vừa thay đổi. Hãy bấm Play lại sau khi cập nhật.');
    state.plan = plan;
    state.lastAcceptedPlan=plan;
    $('currentMusicName').textContent=`Nhạc Reel: ${plan.music_details?.name||'Tắt nhạc'}`+(plan.music_details?.reason?' · '+plan.music_details.reason:'');
    state.selectedScene = Math.min(state.selectedScene, plan.scenes.length - 1);
    renderScenes();
    drawStill();
    status(`${plan.scenes.length} ${sceneLabel(plan).toLowerCase()} · ${timeLabel(plan.duration)}. Đang chuẩn bị để xem nhanh.`);
    $('draftSeek').max=plan.duration;
    populateVideos();
    if(draft) {
      draft.setPlan(plan,state.selectedScene);
      if(state.pendingScenePlayback!==null) {
        const index=Math.min(state.pendingScenePlayback,plan.scenes.length-1);state.pendingScenePlayback=null;
        draft.play(index);
      }
    }
    return plan;
  }).finally(() => {if (revision === state.revision) state.planPromise = null;});
  state.planPromise = promise;
  return promise;
}
function timeLabel(t) {return Number(t).toFixed(1) + 's';}
function sceneLabel(plan=state.plan) {return plan?.text_track?'Footage':'Cảnh';}
function renderScenes() {
  const plan = state.plan;
  if (!plan) return;
  $('paginationBadge').textContent = `${plan.scenes.length} ${sceneLabel(plan).toLowerCase()}${plan.text_track?' · chữ liên tục':plan.segmentation_mode === 'manual_lines' ? ' theo dòng' : ''} · ${timeLabel(plan.duration)}`;
  $('totalDuration').textContent = `Tổng reel: ${timeLabel(plan.duration)} · tối thiểu ${state.settings.duration}s`;
  $('previewStyleName').textContent = THEME_NAMES[state.settings.theme_index];
  if(plan.text_track)$('scrollFrameInfo').textContent=`Khung ${plan.text_track.visible_lines} dòng · cao ${plan.text_track.rect.height} px · giữ đáy, mở lên trên. Tên trang thu theo cỡ chữ.`;
  const pool=plan.footage_pool;
  if(pool && (pool.fallback_scenes?.length || pool.repeated_scenes?.length))
    $('currentVideoName').textContent+=' Kho không đủ clip mới: đã quay vòng sau khi hết lựa chọn phù hợp.';
  const sceneScroll=$('sceneList').scrollTop;
  $('sceneList').replaceChildren();
  $('slideTabs').replaceChildren();
  plan.scenes.forEach((scene, index) => {
    const tab = document.createElement('button');
    tab.className = 'slide-tab' + (index === state.selectedScene ? ' active' : '');
    tab.textContent = `${sceneLabel(plan)} ${index + 1} · ${timeLabel(scene.text_start)}–${timeLabel(scene.text_end)}`;
    tab.dataset.scene=index;
    tab.onclick = () => seekScene(index);
    $('slideTabs').append(tab);
    const item = document.createElement('button');
    item.className = 'scene-card' + (index === state.selectedScene ? ' active' : '');
    item.dataset.scene = index;
    const meta = document.createElement('span');
    meta.className = 'scene-meta';
    meta.textContent = `${index + 1}. ${scene.video_name} · ${timeLabel(scene.text_start)}–${timeLabel(scene.text_end)} · nguồn ${timeLabel(scene.source_start)}–${timeLabel(scene.source_end)}` + (scene.speed < .999 ? ` · tốc độ ${scene.speed.toFixed(2)}×` : '');
    if(pool?.fallback_scenes?.includes(index)||pool?.repeated_scenes?.includes(index))meta.textContent+=' · ↻ Quay vòng do hết clip mới';
    const text = document.createElement('span');
    text.textContent = plan.text_track?'Chữ chạy liên tục trên toàn Reel':scene.text;
    const image=document.createElement('img');image.src=scene.thumb_url;image.alt=scene.video_name;image.loading='lazy';
    const content=document.createElement('span');content.className='scene-card-content';content.append(meta,text);
    item.append(image,content);
    item.onclick = () => seekScene(index);
    $('sceneList').append(item);
  });
  $('sceneList').scrollTop=sceneScroll;
  updateSceneLabels();
}
function updateSceneLabels() {
  if (!state.plan) return;
  const index = state.selectedScene, scene = state.plan.scenes[index];
  $('footageTargetLabel').textContent=state.plan.text_track?`Chọn clip cho footage ${index+1}`:`Chọn footage cho cảnh ${index+1}`;
  const suggestion=scene.suggestion;
  $('currentVideoName').textContent=`${sceneLabel()} ${index+1}: ${scene.video_name}`+(suggestion?.requested_path&&!suggestion.accepted?` · Gợi ý được thay thế: ${suggestion.reason}.`:'');
  $('previewSlideIndicator').textContent = `${sceneLabel()} ${index + 1} / ${state.plan.scenes.length}`;
  $('slidePreviewText').textContent = scene.text;
  $('aiRecommendText').textContent = `Cảnh ${index + 1}: ${scene.video_name} · chữ ${scene.resolved_pos === 'top' ? 'nửa trên' : scene.resolved_pos === 'center' ? 'chính giữa' : 'nửa dưới'}. Kiểm tra lại vị trí nếu chủ thể di chuyển.`;
  $('posBadge').textContent = state.plan.text_track?'Khung chữ cố định':state.settings.pos_mode === 'auto' ? 'Tự động theo từng cảnh' : 'Vị trí thủ công';
  $('btnPlayScene').textContent=`▶ Phát ${sceneLabel().toLowerCase()} đang chọn`;
  document.querySelectorAll('.scene-card, .slide-tab').forEach(element => {
    element.classList.toggle('active', Number(element.dataset.scene) === index);
  });
}
function seekScene(index) {
  if(!state.plan)return;
  state.selectedScene = index;
  updateSceneLabels();
  populateVideos();
  if (state.loadedPlan === state.plan?.plan_id && player.src && player.readyState >= 1) {
    player.currentTime = state.plan.scenes[index].text_start + .25;
    player.style.display = 'block';
    canvas.style.display = 'none';
  } else {showStatic();drawStill();draft?.seek(state.plan.scenes[index].text_start+.21);}
}
async function loadImage(url) {
  return new Promise((resolve,reject) => {const im = new Image(); im.onload=()=>resolve(im); im.onerror=()=>reject(new Error('Không tải được ảnh xem trước.')); im.src=url;});
}
function loadOverlay(plan,index) {
  const key=plan.text_track?`${plan.plan_id}:scroll`:plan.scenes[index].overlay_key||`${plan.plan_id}_${index}`;
  if(!overlayImages.has(key)) {
    const loading=plan.text_track?ScrollTextLayer.create(plan,loadImage,()=>{if(draft?.plan===plan&&!draft.running)draft.draw();}):loadImage(`/api/overlay/${plan.plan_id}/${index}`);
    const promise=loading.catch(error=>{overlayImages.delete(key);throw error;});
    overlayImages.set(key,promise);
    if(overlayImages.size>(plan.text_track?8:120))overlayImages.delete(overlayImages.keys().next().value);
  }
  return overlayImages.get(key);
}
async function drawStill() {
  const plan = state.plan, index = state.selectedScene;
  if (!plan) return;
  try {
    const scene = plan.scenes[index];
    const [background, overlay] = await Promise.all([loadImage(scene.thumb_url),plan.text_track?loadImage(`/api/overlay/${plan.plan_id}/${index}`):loadOverlay(plan,index)]);
    if (state.plan !== plan || state.selectedScene !== index || player.style.display !== 'none' || draft?.hasFrame&&draft.plan===plan) return;
    ctx.clearRect(0,0,1080,1920);
    const scale = Math.max(1080/background.width,1920/background.height);
    const w=background.width*scale,h=background.height*scale;
    ctx.drawImage(background,(1080-w)/2,(1920-h)/2,w,h);
    ctx.drawImage(overlay,0,0);
  } catch(error) {status(error.message,true);}
}
function populateQuotes() {
  $('quoteSelect').replaceChildren();
  if(state.currentQuoteIndex<0) {
    const draft=document.createElement('option');draft.value='';draft.textContent='Bản nháp hiện tại (giữ nguyên nội dung)';
    $('quoteSelect').append(draft);
  }
  state.quotes.forEach((q,index)=>{const option=document.createElement('option');option.value=index;option.textContent=`${q.downloaded?'✓ Đã tải':'○ Chưa tải'} · Câu ${index+1}: ${q.quote.substring(0,55)}…`;$('quoteSelect').append(option);});
  $('quoteSelect').value=state.currentQuoteIndex<0?'':String(state.currentQuoteIndex);
  $('quoteListLabel').textContent=`Chọn câu từ danh sách (${state.quotes.length} câu):`;
  updateQuoteCounter();
  $('btnBatchRender').textContent=`⚡ Xuất nhiều Reel (${state.quotes.length})`;
  if(state.busyBatch)return;
  $('batchModal').querySelector('h2').textContent=`⚡ Xuất nhiều Reel · ${state.quotes.length} câu nói`;
  $('batchModal').querySelector('p').textContent=`Xuất ${state.quotes.length} video Full HD, tự chia cảnh và ưu tiên footage ít dùng, tránh lặp câu trước khi còn lựa chọn.`;
  $('batchStatus').textContent=`Sẵn sàng xuất ${state.quotes.length} video…`;
  $('btnStartBatchRender').textContent=`Bắt đầu xuất ${state.quotes.length} video`;
}
function updateQuoteCounter() {
  $('quoteCounter').textContent=state.currentQuoteIndex<0?`Bản nháp · ${state.quotes.length} câu`:`Câu ${state.currentQuoteIndex+1} / ${state.quotes.length}`;
}
function downloadIdentity(text) {return String(text||'').normalize('NFC').trim().split(/\s+/).join(' ');}
function updateDownloadStatus() {
  const identity=downloadIdentity($('quoteInput').value);
  const record=state.downloadRecords.find(item=>downloadIdentity(item.quote)===identity&&item.is_downloaded!==false);
  const badge=$('quoteDownloadStatus');
  badge.textContent=record?'✓ ĐÃ TẢI VIDEO':'○ CHƯA TẢI VIDEO';badge.classList.toggle('downloaded',!!record);
  $('quoteDownloadDetail').textContent=record?(record.last_downloaded_at?
    `Lần tải gần nhất: ${new Date(record.last_downloaded_at*1000).toLocaleString('vi-VN')} · ${record.count} lần`:
    `Đã đánh dấu thủ công: ${new Date(record.status_at*1000).toLocaleString('vi-VN')}`):'Tự ghi nhận khi Tải video thành công, hoặc bấm đánh dấu nếu bạn đã tải trước đây.';
  $('btnMarkDownloaded').textContent=record?'↶ Bỏ đánh dấu đã tải':'✓ Đánh dấu đã tải';
  $('btnMarkDownloaded').disabled=state.busyMarkDownloaded||!identity;
  const remaining=state.quotes.filter(q=>!q.downloaded).length;
  $('quoteDownloadSummary').textContent=`${state.quotes.length-remaining} đã tải · ${remaining} chưa tải`+(state.quotes.length&&!remaining?' · Tất cả câu trong danh sách đã tải.':'');
  $('btnNextUndownloaded').disabled=!remaining;
}
async function markQuoteDownloaded() {
  if(state.busyMarkDownloaded)return;
  const quote=$('quoteInput').value,identity=downloadIdentity(quote);
  if(!identity)return;
  const marked=state.downloadRecords.some(item=>downloadIdentity(item.quote)===identity&&item.is_downloaded!==false);
  state.busyMarkDownloaded=true;updateDownloadStatus();
  let failure='';
  try {applyQuoteCatalog(await api('/api/mark_quote_downloaded',{quote,downloaded:!marked}));}
  catch(error){failure='Chưa lưu được đánh dấu: '+error.message;}
  finally {state.busyMarkDownloaded=false;updateDownloadStatus();if(failure)$('quoteDownloadDetail').textContent=failure;}
}
function nextUndownloaded() {
  const next=state.quotes.findIndex((q,i)=>!q.downloaded&&i>state.currentQuoteIndex);
  const index=next>=0?next:state.quotes.findIndex(q=>!q.downloaded);
  if(index>=0)loadQuote(index);
}
function quoteIdentity(text) {
  return text.normalize('NFC').replace(/\r\n?/g,'\n').trim();
}
function applyQuoteCatalog(catalog) {
  const previous=state.quotes[state.currentQuoteIndex];
  const draft=$('quoteInput').value;
  state.quotes=catalog.quotes;
  if(catalog.download_history){state.downloadRecords=catalog.download_history.records;state.downloadRevision=catalog.download_history.revision;}
  let index=previous?.key?state.quotes.findIndex(q=>q.key===previous.key):-1;
  if(index<0)index=state.quotes.findIndex(q=>quoteIdentity(q.quote)===quoteIdentity(draft));
  state.currentQuoteIndex=index;
  state.quoteCatalogRevision=catalog.sync.revision;
  populateQuotes();actionAvailability();
  updateDownloadStatus();
  if(state.startupAwaitingSheet&&catalog.sync.source==='sheet') {
    state.startupAwaitingSheet=false;
    const first=state.quotes.findIndex(q=>!q.downloaded);if(first>=0)loadQuote(first);
  }
  // Do not loadQuote/invalidate/autosave here: the user's draft, plan and jobs stay intact.
  renderQuoteSync(catalog.sync);
}
function renderQuoteSync(sync) {
  const label=$('quoteSyncStatus');
  $('btnSyncQuotes').disabled=!sync.enabled||sync.syncing;
  if(!sync.enabled){label.textContent='Đang dùng danh sách cục bộ; tự cập nhật Sheet đã tắt.';return;}
  if(sync.syncing){label.textContent=`Đang cập nhật Sheet “${sync.sheet_name}”… Giữ nguyên câu đang soạn.`;return;}
  if(sync.error){label.textContent=sync.error+` Đang giữ ${sync.count} câu gần nhất.`;return;}
  const when=sync.last_success_at?new Date(sync.last_success_at*1000).toLocaleString('vi-VN'):'';
  label.textContent=sync.source==='sheet'?`Google Sheet · ${sync.count} câu · Cập nhật ${when} · Tự kiểm tra mỗi 30 phút.`:'Đang dùng câu có sẵn; tự kiểm tra Sheet lúc mở app và mỗi 30 phút.';
}
async function refreshQuoteCatalog() {
  if(state.busyQuoteRefresh)return;
  state.busyQuoteRefresh=true;
  try {
    const sync=await api('/api/quote_sync');
    if(sync.revision!==state.quoteCatalogRevision||(sync.download_revision!==undefined&&sync.download_revision!==state.downloadRevision))applyQuoteCatalog(await api('/api/quote_catalog'));
    else renderQuoteSync(sync);
  } catch(error) {$('quoteSyncStatus').textContent='Chưa kiểm tra được danh sách: '+error.message;}
  finally {state.busyQuoteRefresh=false;}
}
async function syncQuotesNow() {
  $('btnSyncQuotes').disabled=true;
  try {renderQuoteSync(await api('/api/quote_sync',{}));setTimeout(refreshQuoteCatalog,1200);}
  catch(error){$('quoteSyncStatus').textContent=error.message;$('btnSyncQuotes').disabled=false;}
}
function loadQuote(index) {
  if (!state.quotes.length) return;
  state.currentQuoteIndex=(index+state.quotes.length)%state.quotes.length;
  $('quoteSelect').value=state.currentQuoteIndex;
  updateQuoteCounter();
  $('quoteInput').value=state.quotes[state.currentQuoteIndex].quote.normalize('NFC');
  updateDownloadStatus();
  invalidate();
}
function populateVideos() {
  const scroll=$('videoCarousel').scrollLeft;
  $('videoCarousel').replaceChildren();
  const options=state.plan?.footage_pool?.scene_choices?.[state.selectedScene]||[];
  const current=state.plan?.scenes?.[state.selectedScene]?.video_path;
  const query=($('footageSearch')?.value||'').toLocaleLowerCase('vi');
  const suitable=$('footageFilter')?.value==='suitable';
  const records=state.videos.map(video=>({video,option:options.find(o=>o.path===video.path)}))
    .filter(({video,option})=>video.name.toLocaleLowerCase('vi').includes(query)&&(!suitable||option?.eligible))
    .sort((a,b)=>Number(!!b.option?.eligible)-Number(!!a.option?.eligible)||(a.option?.effective_count||0)-(b.option?.effective_count||0)||a.video.name.localeCompare(b.video.name));
  records.forEach(({video,option})=>{
    const card=document.createElement('button');card.className='video-card'+(current===video.path?' active':'');
    card.title=option?`${option.effective_count} lượt hiệu dụng · ${option.eligible?'Phù hợp cảnh này':option.reason}`:video.name;
    const img=document.createElement('img');img.src=video.thumb_url;img.alt=video.name;img.loading='lazy';
    const badge=document.createElement('span');badge.className='video-card-badge';badge.textContent=video.name;
    const info=document.createElement('span');info.className='footage-usage';info.textContent=option?`${option.effective_count} lượt · ${option.eligible?'Phù hợp':option.reason}`:'';
    card.append(img,badge,info);card.onclick=()=>selectVideo(video);$('videoCarousel').append(card);
  });
  $('videoCarousel').scrollLeft=scroll;
  $('videoCountBadge').textContent=`${state.videos.length} clip`;
}
function populateMusic() {
  const select=$('musicSelect');select.replaceChildren();
  for(const [value,label] of [['random','🎲 Ngẫu nhiên theo Reel'],['none','Tắt nhạc']]){
    const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option);
  }
  const query=($('musicSearch').value||'').toLocaleLowerCase('vi');
  state.musicTracks.filter(track=>track.name.toLocaleLowerCase('vi').includes(query)||track.path===state.settings.music_path).forEach(track=>{
    const option=document.createElement('option');option.value='track:'+track.id;option.textContent=track.name;select.append(option);
  });
  const chosen=state.musicTracks.find(t=>t.path===state.settings.music_path);
  select.value=state.settings.music_mode==='selected'&&chosen?'track:'+chosen.id:state.settings.music_mode;
}
async function refreshMusicLibrary() {
  try {
    const catalog=await api('/api/music');state.musicTracks=catalog.tracks;
    $('musicDirectory').textContent=catalog.directory;populateMusic();
    const download=catalog.download;
    $('musicLibraryStatus').textContent=download.running?`Đang tải nhạc offline: ${download.done}/${download.total||'…'} bài · ${state.musicTracks.length} bài sẵn sàng.`:
      `${state.musicTracks.length} bài offline.`+(download.errors.length?` ${download.errors.length} bài chưa tải được; bấm Tải/bổ sung để thử lại.`:' Dùng lại ngay cả khi không có Internet.');
    $('btnDownloadMusic').disabled=download.running;
    clearTimeout(state.musicPollTimer);
    if(download.running)state.musicPollTimer=setTimeout(refreshMusicLibrary,1500);
  } catch(error){$('musicLibraryStatus').textContent='Không đọc được kho nhạc: '+error.message;}
}
function selectVideo(video) {
  draft?.unlockAudio();
  const legacy=state.currentVideo;
  state.currentVideo=video;
  const text=$('quoteInput').value.normalize('NFC').split(/\r?\n/).filter(line=>state.settings.theme_index===5||line.trim()).map(line=>line.trim().split(/\s+/).join(' ')).join('\n').trim();
  const previous=state.lastAcceptedPlan;
  const base=state.plan||(previous?.quote===text&&previous.settings?.auto_paginate===state.settings.auto_paginate?previous:null);
  const index=state.selectedScene,scene=base?.scenes[index];
  if(scene) {
    state.settings.scene_video_preferences={...state.settings.scene_video_preferences,[index]:{path:video.path,text:scene.text}};
    // The old video_path preference only applies to scene zero.
    state.currentVideo=index===0?video:legacy;
    state.pendingScenePlayback=index;
  }
  populateVideos();invalidate({preserveScene:true});
  if(state.ready){clearTimeout(planTimer);const revision=state.revision;ensurePlan().catch(error=>{if(revision===state.revision)status(error.message,true);});}
}
function actionAvailability() {
  const blocked=state.busyExport||state.busyBatch||state.busyLibrary||!state.inventoryReady;
  $('btnDownloadVideo').disabled=blocked;
  $('btnBatchRender').disabled=blocked||!state.quotes.length;
  $('btnStartBatchRender').disabled=blocked||!state.quotes.length;
  ['btnSelectVideoDirectory','btnRefreshVideos','btnDefaultVideoDirectory'].forEach(id=>{
    $(id).disabled=state.busyLibrary||state.busyExport||state.busyBatch;
  });
}
async function refreshLibrary(mode='refresh') {
  if(state.busyLibrary)return;
  state.busyLibrary=true;actionAvailability();
  $('libraryStatus').textContent='Đang đọc folder video nền…';
  try {
    let videos;
    if(mode==='refresh') {
      const refreshed=await Promise.all([api('/api/videos'),api('/api/settings')]);
      videos=refreshed[0];
      state.settings.background_video_directory=refreshed[1].background_video_directory||'';
    }
    else {
      const result=await api('/api/select_video_directory',{use_default:mode==='default'});
      if(result.cancelled){$('libraryStatus').textContent='Đã hủy chọn folder; giữ nguyên kho hiện tại.';return;}
      state.settings.background_video_directory=result.directory;
      state.settings.music_mode=result.settings?.music_mode||state.settings.music_mode;
      state.settings.music_path=result.settings?.music_path||'';
      videos=result.videos;
    }
    state.videos=videos;state.inventoryReady=videos.length>0;
    if(mode!=='refresh'){state.settings.scene_video_preferences={};state.settings.imported_video_paths=[];}
    state.currentVideo=mode==='refresh'?videos.find(v=>v.path===state.currentVideo?.path)||videos[0]||null:videos[0]||null;
    $('backgroundDirectory').textContent=state.settings.background_video_directory||'Kho mặc định · CLIP TƯỢNG PHẬT LQ + assets/imports';
    $('libraryStatus').textContent=videos.length?`Đã đọc ${videos.length} clip; folder được tự nhớ, bao gồm thư mục con.`:'Kho video trống. Hãy chọn folder hoặc thêm video.';
    populateVideos();invalidate();
    await refreshMusicLibrary();
  } catch(error) {
    // A cancelled/invalid new choice leaves the old library intact. A failed rescan is unavailable.
    if(mode==='refresh'){state.videos=[];state.currentVideo=null;state.inventoryReady=false;populateVideos();invalidate();}
    $('libraryStatus').textContent=error.message;status(error.message,true);
  } finally {state.busyLibrary=false;actionAvailability();}
}
function setScrollEnabled(enabled) {
  const s=state.settings;
  if(enabled) {
    if(s.theme_index<5)s.static_theme_index=s.theme_index;
    s.theme_index=5;
  } else s.theme_index=s.static_theme_index??0;
  s.scroll_toggle_initialized=true;
  applySettings();invalidate();
}
function applyScrollControls(s) {
  const fields=[['scrollQuoteSize','scroll_quote_size',28,80,48,1,' px'],['scrollLines','scroll_lines',2,8,5,1,' dòng'],
    ['scrollOutlineWidth','scroll_outline_width',0,16,2,1,' px'],['scrollOutlineBlur','scroll_outline_blur',0,24,3,1,' px'],
    ['scrollOutlineOpacity','scroll_outline_opacity',0,100,.85,100,'%'],
    ['scrollFadeTop','scroll_fade_top',0,96,18,1,' px'],['scrollFadeBottom','scroll_fade_bottom',0,96,18,1,' px']];
  fields.forEach(([id,key,min,max,fallback,factor,suffix])=>{
    s[key]??=fallback;
    const slider=$(id+'Slider'),number=$(id+'Number'),label=$(id+'Val');
    const display=()=>{slider.value=number.value=Math.round(s[key]*factor);label.textContent=number.value+suffix;};
    const change=input=>{
      const value=String(input.value).trim()===''?NaN:Number(input.value);
      if(Number.isFinite(value))s[key]=Math.max(min,Math.min(max,Math.round(value)))/factor;
      display();invalidate();
    };
    display();slider.oninput=()=>change(slider);number.onchange=()=>change(number);
  });
  s.scroll_outline_enabled??=true;s.scroll_outline_color??='#101018';
  const disable=()=>{['scrollOutlineColorInput',...['Width','Blur','Opacity'].flatMap(part=>['Slider','Number'].map(suffix=>'scrollOutline'+part+suffix))].forEach(id=>{$(id).disabled=!s.scroll_outline_enabled;});};
  $('scrollOutlineEnabledCheck').checked=s.scroll_outline_enabled;
  $('scrollOutlineEnabledCheck').onchange=()=>{s.scroll_outline_enabled=$('scrollOutlineEnabledCheck').checked;disable();invalidate();};
  $('scrollOutlineColorInput').value=s.scroll_outline_color==='auto'?'#101018':s.scroll_outline_color;
  $('scrollOutlineColorInput').oninput=()=>{s.scroll_outline_color=$('scrollOutlineColorInput').value;invalidate();};
  disable();
}
function applySettings() {
  const s=state.settings;
  const scrolling=s.theme_index===5;
  $('scrollDesignPanel').style.display=scrolling?'block':'none';
  applyScrollControls(s);
  $('scrollEnabledCheck').checked=scrolling;
  $('scrollEnabledCheck').onchange=()=>setScrollEnabled($('scrollEnabledCheck').checked);
  $('scrollEnabledState').textContent=scrolling?'Đang bật':'Đã tắt';
  $('scrollEnabledCheck').parentElement?.classList.toggle('enabled',scrolling);
  $('legacyDesignPanel').style.display=scrolling?'none':'';
  $('autoPaginateLabel').style.display=scrolling?'none':'';
  $('scrollControls').style.display=scrolling?'block':'none';
  $('timingPanelTitle').textContent=scrolling?'04 / Chữ cuộn & Thời lượng':'04 / Phân đoạn chữ & Thời lượng';
  $('quoteEnterHint').textContent=scrolling?'Nhấn Enter: xuống dòng trong dải chữ cuộn':'Nhấn Enter: mỗi dòng một cảnh';
  $('quoteLineHelp').textContent=scrolling?'Giữ ngắt dòng và đoạn trong cùng nội dung cuộn; footage chuyển độc lập, không ngắt chữ.':'Xuống dòng để tự chia các phần câu nói. Dòng trống được bỏ qua; chữ trong mỗi cảnh vẫn tự ngắt cho vừa khung.';
  $('sceneHelp').textContent=scrolling?'Chọn footage để thay clip; chữ vẫn chạy liên tục theo thời gian Reel.':'Bấm cảnh → chọn footage bên dưới → xem ngay cảnh vừa đổi';
  $('previewHelp').textContent=scrolling?'Chữ chạy liên tục trong khung cố định, mờ ở hai mép. Footage chuyển độc lập. Nháp dùng cùng lớp chữ và timeline với Full HD.':'Câu dài tự chia cảnh và tăng thời lượng đủ đọc. Nháp tức thì dùng cùng kế hoạch và lớp chữ của bản Full HD. Clip mới cần chuẩn bị bản nhẹ một lần; sau đó đổi chữ không phải dựng lại Reel. Chuyển cảnh và màu nháp có thể khác nhẹ bản xuất.';
  $('scrollSpeedSlider').value=Math.round((s.scroll_speed??1)*100);
  $('scrollSpeedVal').textContent=(s.scroll_speed??1).toFixed(2)+'×';
  $('scrollSpeedSlider').oninput=()=>{s.scroll_speed=Number($('scrollSpeedSlider').value)/100;$('scrollSpeedVal').textContent=s.scroll_speed.toFixed(2)+'×';invalidate();};
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
  document.querySelectorAll('.template-btn').forEach(el=>{el.classList.toggle('active',Number(el.dataset.theme)===s.theme_index);el.onclick=()=>{s.theme_index=Number(el.dataset.theme);s.static_theme_index=s.theme_index;s.scroll_toggle_initialized=true;applySettings();invalidate();};});
  document.querySelectorAll('.duration-btn').forEach(el=>{el.classList.toggle('active',Number(el.dataset.dur)===s.duration);el.onclick=()=>{s.duration=Number(el.dataset.dur);applySettings();invalidate();};});
  $('themeNameBadge').textContent=THEME_NAMES[s.theme_index];
}
async function pollJob(job, progress, interval=650) {
  while (!['done','error'].includes(job.status)) {
    progress?.(job);
    await new Promise(resolve=>setTimeout(resolve,interval));
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
  if(draft?.running&&draft.mode==='reel'){draft.pause();return;}
  try {
    draft?.unlockAudio();
    const plan=await ensurePlan();showStatic();
    if(draft.plan!==plan||draft.media.some(item=>item.status==='error'))draft.setPlan(plan,state.selectedScene);
    if(draft.mode!=='reel')draft.time=0;
    await draft.play();
  } catch(error){status(error.message,true);}
}
function createDraftPlayer() {
  draft=new DraftPlayer({canvas,request:api,loadOverlay,onStatus:status,
    onAudioBlocked:blocked=>{$('btnEnablePreviewAudio').hidden=!blocked;},
    onAudioState:audio=>{
      $('previewAudioStatus').textContent=audio.state==='none'?'Không có nhạc nền':audio.state==='muted'?'Âm lượng nhạc: 0%':
        audio.state==='blocked'?'Bấm Bật tiếng nháp để nghe nhạc':`♫ Nhạc nền ${Math.round(audio.volume*100)}% · ${audio.state==='playing'?'Đang phát':'Tạm dừng / đang chờ'}`;
      $('previewAudioLevel').value=Math.min(1,audio.level*8);
    },
    onTime:(time,index)=>{
      $('playbackTime').textContent=`${timeLabel(time)} / ${timeLabel(state.plan?.duration||0)}`;
      $('draftSeek').value=time;
      if(index!==state.selectedScene){state.selectedScene=index;updateSceneLabels();populateVideos();}
    },
    onState:running=>{$('btnTogglePlayVideo').textContent=running?'⏸ Tạm dừng nháp':'▶ Phát toàn Reel';}
  });
  $('btnPlayScene').onclick=async()=>{
    draft.unlockAudio();try {await ensurePlan();showStatic();draft.play(state.selectedScene);}catch(error){status(error.message,true);}
  };
  $('draftSeek').oninput=()=>{showStatic();draft.seek(Number($('draftSeek').value));};
  $('btnEnablePreviewAudio').onclick=()=>draft.enableAudio();
}
function renderProgress(job) {
  $('progressBox').classList.add('active');$('progressBarFill').style.width=job.progress+'%';
  $('progressPercent').textContent=job.progress+'%';$('progressStatus').textContent=job.message;
}
function exportKey(snapshot) {
  return JSON.stringify(Object.fromEntries(Object.entries(snapshot).filter(([key])=>!['quote_index','safe_zone','last_save_directory'].includes(key)).sort(([a],[b])=>a.localeCompare(b))));
}
function exportBusy(busy) {
  state.busyExport=busy;actionAvailability();
}
function exportError(error) {
  $('progressBox').classList.add('active');$('progressStatus').textContent=error.message;
}
async function renderSnapshot(snapshot,revision) {
  if(revision===state.revision) {
    clearTimeout(planTimer);clearTimeout(warmPreviewTimer);revision=++state.revision;state.planPromise=null;state.loadedPlan=null;state.loadedKind=null;showStatic();
    $('btnWatchRendered').style.display='none';
  }
  for(let attempt=0;attempt<2;attempt++) {
    const plan=await api('/api/plan',snapshot);
    if(revision===state.revision) {state.plan=plan;state.lastAcceptedPlan=plan;state.selectedScene=Math.min(state.selectedScene,plan.scenes.length-1);renderScenes();populateVideos();drawStill();draft?.setPlan(plan,state.selectedScene);}
    try {
      const job=await api('/api/render',{plan_id:plan.plan_id,async:true});
      const result=await pollJob(job,renderProgress);
      const exported={jobId:job.job_id,key:exportKey(snapshot),result};
      state.lastExport=exported;
      if(revision===state.revision) {state.lastRenderedUrl=result.url;$('btnWatchRendered').style.display='inline-flex';}
      return exported;
    } catch(error) {if(error.code!=='footage_conflict'||attempt===1)throw error;}
  }
}
async function downloadVideo() {
  const snapshot=payload(),revision=state.revision;exportBusy(true);
  try {
    if(!snapshot.quote.trim())throw new Error('Hãy nhập nội dung câu nói trước khi tải.');
    const selection=await api('/api/select_save_video',{quote:snapshot.quote});
    if(selection.cancelled)return;
    let exported=state.lastExport?.key===exportKey(snapshot)?state.lastExport:null;
    if(exported) {
      const response=await fetch(exported.result.url,{headers:{Range:'bytes=0-0'}});
      await response.arrayBuffer();
      if(!response.ok)exported=null;
    }
    if(!exported)exported=await renderSnapshot(snapshot,revision);
    const result=await pollJob(await api('/api/save_video',{save_token:selection.save_token,render_job_id:exported.jobId}),renderProgress);
    $('progressStatus').textContent=`Đã lưu video: ${result.saved_path}`+(result.history_warning?' · '+result.history_warning:'');
    try {applyQuoteCatalog(await api('/api/quote_catalog'));}catch(error){$('quoteDownloadDetail').textContent='Video đã lưu; chưa cập nhật được trạng thái: '+error.message;}
  } catch(error) {exportError(error);}
  finally {exportBusy(false);}
}
async function renderBatch() {
  state.batchTotal=state.quotes.length;state.busyBatch=true;actionAvailability();
  try {
    const result=await pollJob(await api('/api/batch_render',{...payload(),async:true}),job=>{
      if(job.total)state.batchTotal=job.total;
      $('batchStatus').textContent=job.message;$('batchPercent').textContent=job.progress+'%';$('batchBarFill').style.width=job.progress+'%';
    });
    $('batchStatus').textContent=`Đã xuất ${result.total_rendered}/${result.total_requested??state.batchTotal} reel.`+(result.failures.length?' Lỗi: '+result.failures.map(f=>`Câu ${f.index}: ${f.error}`).join('; '):'');
  } catch(error) {$('batchStatus').textContent=error.message;}
  finally {state.busyBatch=false;actionAvailability();}
}
async function initApp() {
  showStatic();status('Đang đọc nội dung và kho clip…');
  try {
    let libraryError='';
    const [startup,videos,settings]=await Promise.all([api('/api/startup_quote',{}),api('/api/videos').catch(error=>{libraryError=error.message;return [];}),api('/api/settings')]);
    const catalog=startup.catalog;
    const quotes=catalog.quotes;
    state.quotes=quotes;state.quoteCatalogRevision=catalog.sync.revision;state.videos=videos;state.settings=settings;lastSavedSettings=JSON.parse(JSON.stringify(settings));
    $('creditInput').value=settings.credit;
    await refreshMusicLibrary();
    state.downloadRecords=catalog.download_history.records;state.downloadRevision=catalog.download_history.revision;
    populateQuotes();
    if(startup.index>=0){
      loadQuote(startup.index);
      if(quoteIdentity(settings.quote||'')!==quoteIdentity(quotes[startup.index].quote))state.settings.scene_video_preferences={};
      if(quoteIdentity(settings.quote||'')!==quoteIdentity(quotes[startup.index].quote))state.settings.music_seed=crypto.randomUUID();
    } else {$('quoteInput').value=settings.quote||'';state.currentQuoteIndex=-1;}
    state.startupAwaitingSheet=catalog.sync.enabled&&catalog.sync.source!=='sheet';
    $('btnRestoreDraft').hidden=!startup.recovery_available;updateDownloadStatus();
    populateQuotes();renderQuoteSync(catalog.sync);
    if(videos.length) selectVideo(videos.find(v=>v.path===settings.video_path)||videos[0]);
    else populateVideos();
    state.inventoryReady=videos.length>0;
    $('backgroundDirectory').textContent=settings.background_video_directory||'Kho mặc định · CLIP TƯỢNG PHẬT LQ + assets/imports';
    $('libraryStatus').textContent=libraryError||`Đã đọc ${videos.length} clip; tự nhớ folder và lấy cả thư mục con.`;
    $('btnSelectVideoDirectory').onclick=()=>refreshLibrary('select');
    $('btnRefreshVideos').onclick=()=>refreshLibrary();
    $('btnDefaultVideoDirectory').onclick=()=>refreshLibrary('default');
    $('safeZoneCheck').checked=!!settings.safe_zone;
    $('safeZoneOverlay').classList.toggle('visible',!!settings.safe_zone);
    applySettings();
    $('quoteSelect').onchange=()=>{if($('quoteSelect').value!=='')loadQuote(Number($('quoteSelect').value));};
    $('btnPrevQuote').onclick=()=>loadQuote(state.currentQuoteIndex<0?-1:state.currentQuoteIndex-1);
    $('btnNextQuote').onclick=()=>loadQuote(state.currentQuoteIndex+1);
    $('btnRandQuote').onclick=()=>loadQuote(Math.floor(Math.random()*state.quotes.length));
    $('btnNextUndownloaded').onclick=nextUndownloaded;
    $('btnMarkDownloaded').onclick=markQuoteDownloaded;
    $('btnRestoreDraft').onclick=restorePreviousDraft;
    $('quoteInput').oninput=invalidate;$('creditInput').oninput=invalidate;
    $('btnSyncQuotes').onclick=syncQuotesNow;
    $('musicSearch').oninput=populateMusic;
    $('musicSelect').onchange=()=>{
      const value=$('musicSelect').value,track=state.musicTracks.find(t=>'track:'+t.id===value);
      state.settings.music_mode=track?'selected':value;state.settings.music_path=track?.path||'';
      invalidate({preserveScene:true});
    };
    $('btnRandomMusic').onclick=()=>{
      state.previousMusicPath=state.plan?.music?.path||'';state.settings.music_seed=crypto.randomUUID();
      state.settings.music_mode='random';state.settings.music_path='';populateMusic();invalidate({preserveScene:true});
    };
    const musicSample=new Audio();
    $('btnListenMusic').onclick=async()=>{
      try {
        if(!musicSample.paused){musicSample.pause();$('btnListenMusic').textContent='▶ Nghe nhạc';return;}
        const plan=await ensurePlan();if(!plan.music_url){status('Reel đang tắt nhạc.');return;}
        draft?.pause();musicSample.src=plan.music_url;musicSample.volume=state.settings.music_volume;
        await musicSample.play();$('btnListenMusic').textContent='⏸ Dừng nghe';
      } catch(error){status(error.message,true);}
    };
    musicSample.onended=()=>{$('btnListenMusic').textContent='▶ Nghe nhạc';};
    document.querySelector('main').addEventListener('pointerdown',event=>{if(!event.target.closest('#btnListenMusic')){musicSample.pause();$('btnListenMusic').textContent='▶ Nghe nhạc';}},true);
    $('btnDownloadMusic').onclick=async()=>{try {await api('/api/download_music',{});await refreshMusicLibrary();}catch(error){$('musicLibraryStatus').textContent=error.message;}};
    $('btnOpenMusicFolder').onclick=()=>api('/api/open_music_folder',{}).catch(error=>status(error.message,true));
    $('btnRandomVideo').onclick=()=>{if(state.videos.length)selectVideo(state.videos[Math.floor(Math.random()*state.videos.length)]);};
    document.querySelector('label[for="uploadVideoInput"]').onclick=async event=>{
      event.preventDefault();
      try {const result=await api('/api/select_video',{});if(result.video){if(!state.videos.some(v=>v.path===result.video.path))state.videos.push(result.video);state.settings.imported_video_paths=[...new Set([...(state.settings.imported_video_paths||[]),result.video.path])];state.inventoryReady=true;actionAvailability();selectVideo(result.video);}}
      catch(error){status(error.message,true);}
    };
    $('safeZoneCheck').onchange=()=>{$('safeZoneOverlay').classList.toggle('visible',$('safeZoneCheck').checked);queueSave();};
    $('btnTogglePlayVideo').onclick=togglePlayback;
    $('btnWatchRendered').onclick=()=>{draft?.pause();if(state.lastRenderedUrl&&state.plan)playUrl(state.lastRenderedUrl,'export',state.plan).catch(error=>status(error.message,true));};
    $('btnOpenFolder').onclick=()=>api('/api/open_folder',{}).catch(error=>status(error.message,true));
    $('btnDownloadVideo').onclick=downloadVideo;
    $('btnBatchRender').onclick=()=>{if(!state.busyBatch)populateQuotes();$('batchModal').classList.add('active');};
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
    createDraftPlayer();
    $('footageSearch').oninput=populateVideos;$('footageFilter').onchange=populateVideos;
    $('btnResetSceneVideo').onclick=()=>{
      const index=state.selectedScene;delete state.settings.scene_video_preferences[index];
      if(index===0)state.currentVideo=null;
      state.pendingScenePlayback=index;invalidate({preserveScene:true});
    };
    state.preferencesContent=$('quoteInput').value.normalize('NFC');state.preferencePagination=state.settings.auto_paginate;
    state.ready=true;
    document.querySelector('main').addEventListener('pointerdown',()=>{state.startupAwaitingSheet=false;},true);
    document.querySelector('main').addEventListener('keydown',()=>{state.startupAwaitingSheet=false;},true);
    state.contextQuote=$('quoteInput').value.normalize('NFC').trim().split(/\s+/).join(' ');
    actionAvailability();
    queueSave();
    setInterval(refreshQuoteCatalog,15000);
    setTimeout(refreshQuoteCatalog,1500);
    if(state.inventoryReady)await ensurePlan();
    else status(libraryError||'Kho video trống. Hãy chọn folder video nền.',true);
  } catch(error) {status(error.message,true);}
}
async function restorePreviousDraft() {
  try {
    const recovery=await api('/api/previous_draft');const saved=recovery.settings;
    const {background_video_directory,last_save_directory,...draftSettings}=saved;
    state.startupAwaitingSheet=false;
    state.settings={...state.settings,...draftSettings};
    $('quoteInput').value=saved.quote||'';$('creditInput').value=saved.credit;
    state.currentQuoteIndex=state.quotes.findIndex(q=>quoteIdentity(q.quote)===quoteIdentity(saved.quote||''));
    state.preferencesContent=$('quoteInput').value.normalize('NFC');state.preferencePagination=state.settings.auto_paginate;
    await api('/api/settings',draftSettings);
    state.videos=await api('/api/videos');state.currentVideo=state.videos.find(v=>v.path===saved.video_path)||null;
    state.inventoryReady=state.videos.length>0;applySettings();populateQuotes();populateVideos();invalidate();
    $('saveStatus').textContent='Đã mở lại bản nháp trước khi khởi động.';
  } catch(error){status(error.message,true);}
}
window.addEventListener('DOMContentLoaded',initApp);
window.addEventListener('pagehide',()=>{draft?.clear();saveBeforeExit();});
