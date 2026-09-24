const token = document.querySelector('meta[name="traywatch-token"]').content;
const $ = id => document.getElementById(id);
const state = {view:'overview', lastSeq:null, roster:[], draft:null, settingsLoaded:false, cropDirty:false, piConnected:false, jobRunning:false, analysisReady:false, reportReady:false};
const titles = {overview:'Overview',camera:'Camera & crop',frames:'Frames & dishes',analysis:'Analysis & report'};

async function api(path, data){
  const init = data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-Traywatch-Token':token},body:JSON.stringify(data)};
  const res = await fetch(path, init);
  const value = await res.json();
  if(!res.ok) throw new Error(value.error || `Request failed (${res.status})`);
  return value;
}
function notice(message, error=false){const n=$('notice');n.hidden=false;n.classList.toggle('error',error);n.textContent=message;clearTimeout(notice.timer);notice.timer=setTimeout(()=>n.hidden=true,7500)}
function setText(id,value){$(id).textContent=value ?? '—'}
function wallDate(text){if(!text)return null;const d=new Date(text.replace(' ','T')+'+08:00');return isNaN(d)?null:d}
function shortTime(text){return text ? text.slice(11,16) : '—'}
function age(text){const d=wallDate(text);if(!d)return 'Time unavailable';const mins=Math.max(0,Math.round((Date.now()-d)/60000));return mins<1?'Just now':`${mins} min ago`}
function safeButton(id,fn){$(id).addEventListener('click',async()=>{const b=$(id);b.disabled=true;try{await fn()}catch(e){notice(e.message,true)}finally{applyAvailability()}})}
function applyAvailability(){
  for(const id of ['sync-now','sync-frames','aim','check-crop'])$(id).disabled=state.jobRunning||!state.piConnected;
  $('apply-crop').disabled=state.jobRunning||!state.piConnected||!$('crop-confirm').checked||$('crop-image').hidden;
  document.querySelectorAll('[data-service]').forEach(b=>b.disabled=state.jobRunning||!state.piConnected);
  $('run-analysis').disabled=state.jobRunning||!state.analysisReady;
  $('run-report').disabled=state.jobRunning||!state.reportReady;
  $('run-fallback').disabled=state.jobRunning||!state.reportReady;
  $('approve-report').disabled=state.jobRunning||!state.draft||!$('report-confirm').checked;
}
function showView(view){if(!titles[view])view='overview';state.view=view;document.querySelectorAll('.view').forEach(el=>el.classList.toggle('active',el.id===`view-${view}`));document.querySelectorAll('.nav').forEach(el=>el.classList.toggle('active',el.dataset.view===view));setText('page-title',titles[view]);history.replaceState({},'',view==='overview'?'/':`/?view=${view}`);if(view==='frames'){loadFrames();loadRoster()}if(view==='analysis'){loadDaily();loadDraft();loadEstimate()}}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));

async function loadLatest(seq){if(seq===state.lastSeq)return;try{const d=await api('/api/latest');$('latest-image').src=`data:image/jpeg;base64,${d.image}`;$('latest-image').hidden=false;$('latest-empty').hidden=true;state.lastSeq=d.seq;setText('latest-caption',`Pi frame ${String(d.seq).padStart(6,'0')} · ${d.wall} · stored image, not live video`)}catch(e){if(state.lastSeq===null){$('latest-image').hidden=true;$('latest-empty').hidden=false;setText('latest-empty',`No Pi image: ${e.message}`)}}}
function renderTimeline(rows){const t=$('timeline');t.replaceChildren();for(const r of rows.slice(-45)){const el=document.createElement('span');el.className='tick'+(Number(r.bytes)===0?' bad':'');el.title=`${r.wall||'Unknown time'} · ${Number(r.bytes)===0?'camera failure':'image stored'}`;t.append(el)}if(!rows.length)t.textContent='No rows recorded yet.'}
async function refresh(){
  try{
    const d=await api('/api/overview');const r=d.remote;const c=r?.capture;const latest=c?.latest;const service=r?.service;
    state.piConnected=!!r;$('rail-connection').textContent=r?'Pi connected':'Pi disconnected';$('rail-connection').className=r?'good-text':'bad-text';
    setText('updated',`Checked ${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`);
    if(!r){setText('capture-status','Disconnected');$('capture-status').className='bad-text';setText('capture-sub',(d.connection_error||'No Pi response').slice(0,100));setText('frame-time','—');setText('frame-age','Pi unavailable');setText('clock-status','Unknown');setText('clock-sub','Pi unavailable');setText('today-valid','—');setText('today-gaps','—');setText('cadence','—');setText('wb-status','—');setText('storage','—');state.lastSeq=null;if(d.local.latest){$('latest-image').src=`/api/frame/${String(d.local.latest.seq).padStart(6,'0')}`;$('latest-image').hidden=false;$('latest-empty').hidden=true;setText('photo-source','Laptop mirror · Pi offline');setText('latest-caption',`Last copied ${d.local.latest.wall} · ${age(d.local.latest.wall)} · stale copy`)}else{$('latest-image').hidden=true;$('latest-empty').hidden=false;setText('photo-source','No Pi connection')}}
    else{
      const stale=!latest||!wallDate(latest.wall)||Date.now()-wallDate(latest.wall).getTime()>(Number(c.cadence_seconds||120)+90)*1000;
      const active=service?.active==='active';
      setText('capture-status',active?(stale?'Active, no fresh frame':'Recording'):'Stopped');$('capture-status').className=active&&!stale?'good-text':active?'bad-text':'';
      setText('capture-sub',`${service?.active||'Unknown'} · ${service?.substate||'state unknown'}`);
      setText('frame-time',latest?shortTime(latest.wall):'None');setText('frame-age',latest?`${age(latest.wall)}${stale?' · stale':''}`:'No valid frame');
      setText('clock-status',r.clock?.synchronized===true?'Synced':r.clock?.synchronized===false?'Not synced':'Unknown');setText('clock-sub',r.clock?.timezone||'Timezone unknown');
      const rows=c.rows||[];setText('today-valid',r.frames?.filter(x=>x.wall?.slice(0,10)===r.clock?.now?.slice(0,10)).length??'—');setText('today-gaps',rows.filter(x=>Number(x.bytes)===0).length);setText('cadence',`${c.cadence_seconds||'—'} sec`);setText('wb-status',latest?((rows.find(x=>Number(x.seq)===Number(latest.seq))?.wb_locked)==='1'?'Locked':'Unverified'):'—');setText('storage',r.storage?.free_bytes!=null?`${(r.storage.free_bytes/1e9).toFixed(1)} GB`:'—');renderTimeline(rows);
      setText('photo-source','Latest stored Pi frame');if(latest)loadLatest(latest.seq);else{$('latest-image').hidden=true;$('latest-empty').hidden=false;setText('latest-empty','Capture has not stored a valid frame yet.')}
      if(c.crop&&!state.cropDirty)$('crop').value=c.crop.join(',');
    }
    const l=d.local;setText('mirror-count',`${l.valid} images`);setText('mirror-time',d.mirror?.last_success?`Synced ${new Date(d.mirror.last_success).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})} · latest frame ${l.latest?shortTime(l.latest.wall):'—'}`:l.latest?`Last frame ${shortTime(l.latest.wall)} · sync time unknown`:'No copied images');
    renderJob(d.job);
    if(!state.settingsLoaded){$('setting-host').value=d.settings.host||'';$('setting-user').value=d.settings.user||'';$('setting-dir').value=d.settings.remote_dir||'';state.settingsLoaded=true}
  }catch(e){notice(`Status check failed: ${e.message}`,true)}
}
function renderJob(job){const running=job?.state==='running';state.jobRunning=running;setText('job-status',job?.state?`${job.kind||'Operation'} · ${job.state}`:'Idle');setText('job-progress',job?.state==='failed'?job.error:job?.progress||job?.error||'No operation has started.');$('job-log').textContent=(job?.log||[]).join('\n');$('cancel-job').disabled=!running;applyAvailability();if(state.lastJobState==='running'&&!running){loadDaily();loadDraft();loadFrames();loadEstimate()}state.lastJobState=job?.state}

safeButton('refresh',refresh);
safeButton('sync-now',async()=>{await api('/api/sync',{});notice('Copying frames in the background.');await refresh()});
safeButton('sync-frames',async()=>{await api('/api/sync',{});notice('Copying frames in the background.');await refresh()});
safeButton('aim',async()=>{const d=await api('/api/aim',{});$('aim-image').src=`data:image/jpeg;base64,${d.image}`;$('aim-image').hidden=false;$('aim-empty').hidden=true;notice(`Aiming image ${d.sensor_width||d.width} × ${d.sensor_height||d.height} sensor pixels`)});
$('crop').addEventListener('input',()=>{state.cropDirty=true;$('crop-confirm').checked=false;$('apply-crop').disabled=true;$('crop-image').hidden=true;$('crop-empty').hidden=false});
$('crop-confirm').addEventListener('change',applyAvailability);
safeButton('check-crop',async()=>{const d=await api('/api/check-crop',{crop:$('crop').value.trim()});$('crop-image').src=`data:image/jpeg;base64,${d.image}`;$('crop-image').hidden=false;$('crop-empty').hidden=true;$('crop-confirm').checked=false;$('apply-crop').disabled=true;notice('Review the exact crop, then confirm if no person is visible.')});
safeButton('apply-crop',async()=>{if(!$('crop-confirm').checked)throw new Error('Confirm the reviewed crop first.');const d=await api('/api/apply-crop',{crop:$('crop').value.trim(),confirm:true});state.cropDirty=false;state.lastSeq=null;$('crop-confirm').checked=false;$('apply-crop').disabled=true;notice(d.message||'Crop applied.');refresh()});
document.querySelectorAll('[data-service]').forEach(b=>b.addEventListener('click',async()=>{b.disabled=true;try{const action=b.dataset.service;if(action==='stop'&&!confirm('Stop recording on the Pi? The stall will have a capture gap until started again.'))return;await api('/api/service',{action});notice(`Capture ${action} requested.`);refresh()}catch(e){notice(e.message,true)}finally{b.disabled=false}}));
safeButton('save-settings',async()=>{await api('/api/settings',{host:$('setting-host').value,user:$('setting-user').value,remote_dir:$('setting-dir').value});state.lastSeq=null;notice('Pi connection saved.');refresh()});

async function loadFrames(){try{const d=await api('/api/frames');const list=$('frame-list');list.replaceChildren();const rows=d.rows.filter(r=>Number(r.bytes)>0);setText('frame-count',`${rows.length} recent valid frames`);if(!rows.length){list.textContent='No copied frames yet.';return}for(const r of rows.slice(0,60)){const b=document.createElement('button');b.textContent=`${shortTime(r.wall)} · #${r.seq}`;b.addEventListener('click',()=>{document.querySelectorAll('#frame-list button').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');$('selected-frame').src=`/api/frame/${String(r.seq).padStart(6,'0')}`;$('selected-frame').hidden=false;$('selected-empty').hidden=true;setText('selected-caption',`Laptop copy · ${r.wall} · ${r.bytes} bytes`)});list.append(b)}}catch(e){notice(e.message,true)}}

function rowEl(row){const el=document.createElement('div');el.className='roster-row';const fields=[['block','text'],['from_ts','time'],['slot','number'],['dish','text'],['is_veg','checkbox']];for(const [key,type] of fields){const input=document.createElement('input');input.type=type;input.dataset.key=key;input.value=type==='checkbox'?'':row[key]||'';if(type==='checkbox')input.checked=String(row[key])==='1';if(key==='slot')input.min='1';input.setAttribute('aria-label',key==='is_veg'?'Vegetable dish':key.replace('_',' '));el.append(input)}const del=document.createElement('button');del.className='remove';del.type='button';del.textContent='×';del.title='Remove dish row';del.addEventListener('click',()=>el.remove());el.append(del);return el}
function renderRoster(){const day=$('roster-day').value;const host=$('roster-rows');host.replaceChildren();const head=document.createElement('div');head.className='roster-row roster-head';for(const x of ['Block','From','Slot','Dish','Veg','']){const s=document.createElement('span');s.textContent=x;head.append(s)}host.append(head);for(const row of state.roster.filter(x=>x.day===day))host.append(rowEl(row))}
async function loadRoster(){try{state.roster=(await api('/api/roster')).rows;if(!$('roster-day').value)$('roster-day').value=new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Singapore'});renderRoster()}catch(e){notice(e.message,true)}}
function collectDay(){const day=$('roster-day').value;const list=[];for(const el of document.querySelectorAll('#roster-rows .roster-row:not(.roster-head)')){const r={day};el.querySelectorAll('input').forEach(inp=>r[inp.dataset.key]=inp.type==='checkbox'?(inp.checked?'1':'0'):inp.value.trim());list.push(r)}return list}
$('load-roster').addEventListener('click',renderRoster);
$('add-row').addEventListener('click',()=>{const rows=collectDay();const last=rows.at(-1);$('roster-rows').append(rowEl({block:last?.block||'am',from_ts:last?.from_ts||'08:00',slot:Math.max(0,...rows.filter(r=>r.block===(last?.block||'am')).map(r=>Number(r.slot)||0))+1,dish:'',is_veg:'0'}))});
$('add-block').addEventListener('click',()=>{const rows=collectDay();const blocks=[...new Set(rows.map(r=>r.block))];if(!rows.length){notice('Add the opening dish map first.',true);return}const last=blocks.at(-1);const name=last==='am'?'pm':`block${blocks.length+1}`;for(const r of rows.filter(x=>x.block===last))$('roster-rows').append(rowEl({...r,block:name,from_ts:'14:30'}));notice('Edit the actual swap time and dish positions, then save.')});
safeButton('save-roster',async()=>{const day=$('roster-day').value;const all=[...state.roster.filter(r=>r.day!==day),...collectDay()];await api('/api/roster',{rows:all});notice('Dish map saved.');loadRoster()});

async function loadDaily(){try{const d=await api('/api/daily');const rows=d.rows;state.reportReady=rows.length>0&&!d.outdated&&rows.every(r=>r.mapping_status==='mapped');setText('daily-summary',rows.length?`${rows.length} dish-day rows · camera-estimated visual fill${d.outdated?' · newer frames or dish map: rerun analysis':state.reportReady?'':' · complete dish map needed'}`:'No analysed days yet.');const body=$('daily-table');body.replaceChildren();for(const r of rows.slice(-25)){const tr=document.createElement('tr');for(const val of [r.day,r.dish,r.leftover_close?`${Math.round(Number(r.leftover_close))}%`:'—',r.refills||'—',r.mapping_status||'—']){const td=document.createElement('td');td.textContent=val;tr.append(td)}body.append(tr)}applyAvailability()}catch(e){notice(e.message,true)}}
async function loadEstimate(){try{const e=await api('/api/analysis-estimate');state.analysisReady=e.frames>0;setText('cost-estimate',`${e.remaining} uncached / ${e.frames} copied frames · about US$${e.estimated_usd.toFixed(2)} at the current per-frame assumption. Actual API cost may differ.`);applyAvailability()}catch(e){setText('cost-estimate',`Estimate unavailable: ${e.message}`)}}
safeButton('run-analysis',async()=>{const e=await api('/api/analysis-estimate');if(!confirm(`Analyse ${e.remaining} uncached frames with Gemini? Approximate API cost US$${e.estimated_usd.toFixed(2)}; actual cost may differ.`))return;await api('/api/analyse',{});notice('Analysis started. Progress appears below.');await refresh()});
safeButton('run-report',async()=>{await api('/api/report',{no_llm:false});notice('Report draft started.');await refresh()});
safeButton('run-fallback',async()=>{await api('/api/report',{no_llm:true});notice('Simple report draft started.');await refresh()});
safeButton('cancel-job',async()=>{await api('/api/cancel',{});notice('Cancellation requested. Completed readings remain saved.')});
async function loadDraft(){try{const d=await api('/api/draft');state.draft=d.name;setText('draft-name',d.name||'None yet');$('draft-preview').hidden=!d.html;$('draft-empty').hidden=!!d.html;if(d.html)$('draft-preview').srcdoc=d.html;$('report-confirm').checked=false;$('approve-report').disabled=true;const a=await api('/api/approved');const list=$('approved-list');list.replaceChildren();if(a.files.length){const label=document.createElement('strong');label.textContent='Approved copies';list.append(label)}for(const name of a.files.slice(0,8)){const link=document.createElement('a');link.href=`/approved/${encodeURIComponent(name)}`;link.target='_blank';link.rel='noopener';link.textContent=name;list.append(link)}}catch(e){notice(e.message,true)}}
$('report-confirm').addEventListener('change',applyAvailability);
safeButton('approve-report',async()=>{const d=await api('/api/approve',{name:state.draft,confirm:true});notice(`Approved copy ${d.name} is ready to print.`);loadDraft()});
showView(new URLSearchParams(location.search).get('view')||'overview');applyAvailability();refresh();setInterval(refresh,10000);
