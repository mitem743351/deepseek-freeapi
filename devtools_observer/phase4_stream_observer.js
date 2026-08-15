/* Phase 4 XHR stream observer. Passive/local-only. Paste after the base observer if desired. */
(() => {
  'use strict';
  if (globalThis.DeepSeekPhase4StreamObserver) { console.warn('[DS-P4-STREAM] Already installed.'); return; }
  const MAX_DELTA = 65536, MAX_EVENTS = 80, sensitive = /(token|cookie|authorization|csrf|session|secret|password|api[_-]?key|credential)/i;
  const state = { running: true, records: [], originals: {}, installedAt: new Date().toISOString() };
  const shape = (v, depth=0) => { if(depth>4)return {type:'truncated_depth'}; if(v===null)return {type:'null'}; if(Array.isArray(v))return {type:'array',length:v.length,items:v.length?shape(v[0],depth+1):{type:'unknown'}}; if(typeof v!=='object')return {type:typeof v,length:typeof v==='string'?v.length:undefined}; const keys={}; Object.keys(v).slice(0,80).forEach(k=>keys[sensitive.test(k)?'<REDACTED_FIELD>':k]=sensitive.test(k)?{type:'<REDACTED>'}:shape(v[k],depth+1)); return {type:'object',keys}; };
  const url = x => { try { const u=new URL(x,location.href); return {origin:u.origin,path:u.pathname}; } catch(_) { return {origin:'UNKNOWN',path:'UNKNOWN'}; } };
  const OriginalXHR = XMLHttpRequest, open = OriginalXHR.prototype.open, send = OriginalXHR.prototype.send;
  state.originals = { open, send };
  OriginalXHR.prototype.open = function(method, requestURL) { this.__dsP4 = { method:String(method||'GET').toUpperCase(), url:url(requestURL), seen:0, record:null }; return open.apply(this,arguments); };
  OriginalXHR.prototype.send = function() {
    const meta=this.__dsP4 || {method:'UNKNOWN',url:{origin:'UNKNOWN',path:'UNKNOWN'},seen:0,record:null};
    const onProgress=() => {
      if(!state.running) return;
      let text; try { text=this.responseText; } catch(_) { if(meta.record) meta.record.access='NOT_ACCESSIBLE'; return; }
      if(typeof text!=='string' || text.length<=meta.seen) return;
      const delta=text.slice(meta.seen, Math.min(text.length,meta.seen+MAX_DELTA)); meta.seen=text.length;
      if(!meta.record) { const ct=(()=>{try{return this.getResponseHeader('content-type')||'UNKNOWN'}catch(_){return'UNKNOWN'}})(); meta.record={status:'OBSERVED',timestamp:new Date().toISOString(),method:meta.method,origin:meta.url.origin,path:meta.url.path,content_type:ct,progress_notifications:0,delta_character_counts:[],sse_like_framing:'UNKNOWN',event_data_shapes:[],completion_marker:'UNKNOWN',raw_payloads_stored:false}; state.records.push(meta.record); }
      const r=meta.record; r.progress_notifications++; r.delta_character_counts.push(delta.length);
      if(/text\/event-stream/i.test(r.content_type)||/(?:^|\n)(?:event|data):/m.test(delta)) r.sse_like_framing='OBSERVED';
      delta.split(/\r?\n\r?\n/).slice(0,20).forEach(block=>{ const data=block.split(/\r?\n/).filter(line=>line.startsWith('data:')).map(line=>line.slice(5).trim()).join('\n'); if(!data||r.event_data_shapes.length>=MAX_EVENTS)return; if(data==='[DONE]'){r.completion_marker='data_DONE';return} try{r.event_data_shapes.push(shape(JSON.parse(data)))}catch(_){r.event_data_shapes.push({type:'text',length:data.length})} });
    };
    this.addEventListener('progress',onProgress); this.addEventListener('loadend',()=>{ if(meta.record)meta.record.loadend_observed=true; });
    return send.apply(this,arguments);
  };
  globalThis.DeepSeekPhase4StreamObserver={ status:()=>({running:state.running,records:state.records.length,installed_at:state.installedAt}), pause:()=>state.running=false, resume:()=>state.running=true, export:()=>JSON.parse(JSON.stringify({metadata:{local_only:true,raw_payloads_stored:false},records:state.records})), reset:()=>{OriginalXHR.prototype.open=open;OriginalXHR.prototype.send=send;delete globalThis.DeepSeekPhase4StreamObserver;} };
  console.log('[DS-P4-STREAM] Running: future XHR progress only; no raw payload export, no requests sent.');
})();
