/* Phase 4 IndexedDB schema observer. Read-only/local-only; never exports record values. */
(() => {
  'use strict';
  if(globalThis.DeepSeekPhase4IndexedDBObserver){console.warn('[DS-P4-IDB] Already installed.');return;}
  const sensitive=/(token|cookie|authorization|csrf|session|secret|password|api[_-]?key|credential)/i, MAX_RECORDS=25;
  const typeOf=v=>v===null?'null':Array.isArray(v)?'array':v instanceof Date?'date':typeof v;
  const safeShape=(v,depth=0)=>{if(depth>3)return {type:'truncated_depth'};if(!v||typeof v!=='object'||v instanceof Date)return {type:typeOf(v)};if(Array.isArray(v))return {type:'array',items:v.length?safeShape(v[0],depth+1):{type:'unknown'}};const fields={};Object.keys(v).slice(0,100).forEach(k=>fields[sensitive.test(k)?'<REDACTED_FIELD>':k]=sensitive.test(k)?'<REDACTED>':safeShape(v[k],depth+1));return {type:'object',fields};};
  async function inspect(databaseName='deepseek-chat'){
    if(!indexedDB)return {status:'UNKNOWN',reason:'IndexedDB unavailable'};
    return new Promise(resolve=>{const r=indexedDB.open(databaseName);r.onerror=()=>resolve({status:'UNKNOWN',database:databaseName,error_category:r.error&&r.error.name||'open_error'});r.onsuccess=()=>{const db=r.result,out={status:'OBSERVED',database:db.name,version:db.version,stores:[]};if(!db.objectStoreNames.length){db.close();return resolve(out)}const tx=db.transaction(Array.from(db.objectStoreNames),'readonly');Array.from(db.objectStoreNames).forEach(name=>{const s=tx.objectStore(name),entry={name,keyPath:s.keyPath||null,autoIncrement:!!s.autoIncrement,indexes:Array.from(s.indexNames),record_count:'UNKNOWN',sampled_records:0,field_shapes:[]};out.stores.push(entry);const count=s.count();count.onsuccess=()=>entry.record_count=count.result;const cursor=s.openCursor();cursor.onsuccess=()=>{const c=cursor.result;if(!c||entry.sampled_records>=MAX_RECORDS)return;entry.sampled_records++;entry.field_shapes.push(safeShape(c.value));c.continue();};});tx.oncomplete=()=>{db.close();resolve(out)};tx.onerror=()=>{db.close();resolve(out)}};});}
  globalThis.DeepSeekPhase4IndexedDBObserver={inspect,help:()=>console.log('DeepSeekPhase4IndexedDBObserver.inspect("deepseek-chat") — reads metadata/field types only; no values, writes, deletes, or network.')};console.log('[DS-P4-IDB] Ready. Run DeepSeekPhase4IndexedDBObserver.inspect().');
})();
