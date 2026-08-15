/* DeepSeek Web Passive Observer v1.0.0
 * Local-only DevTools instrumentation. It observes future browser activity and never sends data.
 * Paste into a Chromium DevTools Console in an account-owner's normal session.
 */
(() => {
  'use strict';
  const EXISTING = globalThis.DeepSeekObserver;
  if (EXISTING && EXISTING.__dsPassiveObserver) { console.warn('[DS-OBS] Already installed. Run DeepSeekObserver.reset() before reinstalling.'); return; }

  const VERSION = '1.0.0';
  const SENSITIVE = /(authorization|proxy-authorization|cookie|set-cookie|token|access[_-]?token|refresh[_-]?token|id[_-]?token|csrf|xsrf|session|secret|password|api[_-]?key|apikey|credential|private[_-]?key)/i;
  const LIKELY_SECRET = /(?:^|[^A-Za-z0-9_-])(?:eyJ[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{12,}|[A-Za-z0-9+/_-]{40,}={0,2})(?:$|[^A-Za-z0-9_-])/;
  const MESSAGE_WORDS = /(message|conversation|chat|completion|generation|assistant|user)/i;
  const MAX_INSPECT = 65536, MAX_STREAM_CHUNKS = 40, MAX_STREAM_BYTES = 131072, MAX_DEPTH = 5;
  const state = {
    running: false, paused: false, sequence: 0, endpointSequence: 0, scenarioSequence: 0,
    currentScenario: null, operations: [], streams: [], attachments: [], endpointInventory: new Map(),
    schemas: { messageCandidates: [], responseShapes: [] }, storage: { status: 'UNKNOWN' },
    scenarios: [], errors: [], performance: [], installed: false, listeners: [], originals: {}, startedAt: null,
    config: { captureTestPayloads: false, scanPerformance: true, inspectResponseBodies: true, maxResponseBytes: MAX_INSPECT }
  };
  const now = () => new Date().toISOString();
  const log = (...a) => console.log('[DS-OBS]', ...a);
  const warn = (...a) => console.warn('[DS-OBS]', ...a);
  const safeString = (v) => { try { return String(v); } catch (_) { return '<UNSTRINGIFIABLE>'; } };
  const isSensitiveKey = (k) => SENSITIVE.test(String(k));
  const isLikelySecret = (v) => typeof v === 'string' && v.length >= 24 && LIKELY_SECRET.test(v);
  const testValue = (v) => typeof v === 'string' && /(?:CAPTURE_TEST|capture_test)/i.test(v);
  const classifyBody = (body) => {
    if (body == null) return 'none';
    if (typeof body === 'string') { try { JSON.parse(body); return 'json'; } catch (_) { return 'text'; } }
    if (body instanceof URLSearchParams) return 'form-urlencoded';
    if (body instanceof FormData) return 'multipart';
    if (body instanceof Blob || body instanceof ArrayBuffer || ArrayBuffer.isView(body)) return 'binary';
    return 'unknown';
  };
  const sanitizeURL = (input) => {
    try {
      const u = new URL(input, location.href), queryKeys = [];
      u.searchParams.forEach((_, key) => queryKeys.push(isSensitiveKey(key) ? '<REDACTED_QUERY_KEY>' : key));
      const path = u.pathname.split('/').map(segment => /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[A-Za-z0-9_-]{24,})$/i.test(segment) ? '<REDACTED_PATH_SEGMENT>' : segment).join('/');
      return { origin: u.origin, path, query_keys: [...new Set(queryKeys)], url: u.origin + path + (queryKeys.length ? '?' + queryKeys.map(k => `${k}=<REDACTED>`).join('&') : '') };
    } catch (_) { return { origin: 'UNKNOWN', path: 'UNKNOWN', query_keys: [], url: '<UNPARSEABLE_URL>' }; }
  };
  const headerNames = (headers) => {
    const out = [], redacted = [];
    try {
      if (!headers) return { names: out, redacted };
      if (headers instanceof Headers) headers.forEach((_, k) => (isSensitiveKey(k) ? redacted : out).push(k.toLowerCase()));
      else if (Array.isArray(headers)) headers.forEach(([k]) => (isSensitiveKey(k) ? redacted : out).push(String(k).toLowerCase()));
      else if (typeof headers === 'object') Object.keys(headers).forEach(k => (isSensitiveKey(k) ? redacted : out).push(k.toLowerCase()));
    } catch (_) { /* metadata only */ }
    return { names: [...new Set(out)], redacted: redacted.length ? ['<REDACTED_AUTH_HEADER>'] : [] };
  };
  const contentType = (headers) => { try { return headers && typeof headers.get === 'function' ? (headers.get('content-type') || 'UNKNOWN') : 'UNKNOWN'; } catch (_) { return 'UNKNOWN'; } };
  const shape = (value, depth = 0) => {
    if (depth > MAX_DEPTH) return { type: 'truncated_depth' };
    if (value === null) return { type: 'null' };
    if (Array.isArray(value)) return { type: 'array', length: value.length, items: value.length ? shape(value[0], depth + 1) : { type: 'unknown' } };
    const t = typeof value;
    if (t !== 'object') return { type: t, length: typeof value === 'string' ? value.length : undefined };
    const keys = {};
    Object.keys(value).slice(0, 100).forEach(k => { keys[isSensitiveKey(k) ? '<REDACTED_FIELD>' : k] = isSensitiveKey(k) ? { type: '<REDACTED>' } : shape(value[k], depth + 1); });
    return { type: 'object', keys };
  };
  const bodyShape = (body) => {
    const kind = classifyBody(body);
    if (body == null) return { classification: kind, schema: null };
    if (body instanceof FormData) {
      const fields = [];
      body.forEach((v, k) => fields.push({ field_name: isSensitiveKey(k) ? '<REDACTED_FIELD>' : k, type: v instanceof File ? 'file' : typeof v, length: v instanceof File ? v.size : safeString(v).length }));
      return { classification: kind, schema: { type: 'form-data', fields } };
    }
    if (typeof body === 'string') {
      try { return { classification: kind, schema: shape(JSON.parse(body)) }; } catch (_) { return { classification: kind, schema: { type: 'string', length: body.length, value: state.config.captureTestPayloads && testValue(body) ? body.slice(0, 500) : undefined } }; }
    }
    return { classification: kind, schema: { type: kind, size: body && (body.size || body.byteLength) || undefined } };
  };
  const responseKind = (ct) => /text\/event-stream/i.test(ct) ? 'SSE' : /application\/(?:json|[^;]+\+json)/i.test(ct) ? 'json' : /text\/html/i.test(ct) ? 'html' : /^text\//i.test(ct) ? 'text' : /(?:octet-stream|image\/|audio\/|video\/|application\/pdf)/i.test(ct) ? 'binary' : 'unknown';
  const active = () => state.running && !state.paused;
  const currentScenarioId = () => state.currentScenario && state.currentScenario.id || null;
  const endpoint = (op) => {
    const key = `${op.method}|${op.url_origin}|${op.url_path}`;
    let e = state.endpointInventory.get(key);
    if (!e) { e = { id: `EP-${String(++state.endpointSequence).padStart(3, '0')}`, method: op.method, origin: op.url_origin, path: op.url_path, observed_count: 0, content_types: [], streaming: { status: 'UNKNOWN' }, request_schema: null, response_schema: null, scenarios: [], classification: 'OBSERVED' }; state.endpointInventory.set(key, e); }
    if (!op._endpointRegistered) { e.observed_count++; op._endpointRegistered = true; } if (op.request_content_type !== 'UNKNOWN' && !e.content_types.includes(op.request_content_type)) e.content_types.push(op.request_content_type);
    if (op.response_content_type && op.response_content_type !== 'UNKNOWN' && !e.content_types.includes(op.response_content_type)) e.content_types.push(op.response_content_type);
    if (op.request_body && !e.request_schema) e.request_schema = op.request_body.schema;
    if (op.response_schema && !e.response_schema) e.response_schema = op.response_schema;
    if (op.streaming_candidate) e.streaming = { status: 'OBSERVED', transport: op.transport === 'fetch' ? 'fetch-readable-stream-candidate' : op.transport };
    const s = currentScenarioId(); if (s && !e.scenarios.includes(s)) e.scenarios.push(s);
    op.endpoint_id = e.id;
  };
  const candidate = (op) => {
    const pathHit = MESSAGE_WORDS.test(op.url_path), schemaText = JSON.stringify(op.request_body && op.request_body.schema || '');
    const bodyHit = MESSAGE_WORDS.test(schemaText), streamHit = !!op.streaming_candidate;
    const classification = pathHit && (bodyHit || streamHit) ? 'OBSERVED_MESSAGE_OPERATION' : (pathHit || bodyHit || streamHit) ? 'POSSIBLE_MESSAGE_OPERATION' : 'UNRELATED';
    if (classification !== 'UNRELATED' && !op._candidateRecorded) { state.schemas.messageCandidates.push({ operation_id: op.id, endpoint_id: op.endpoint_id, classification, evidence: { path_keyword: pathHit, payload_shape_keyword: bodyHit, streaming_candidate: streamHit }, request_schema: op.request_body && op.request_body.schema || null, response_schema: op.response_schema || null }); op._candidateRecorded = true; }
  };
  const addOp = (op) => { if (!active()) return null; op.id = `OP-${String(++state.sequence).padStart(4, '0')}`; op.timestamp = now(); op.scenario = currentScenarioId(); op.classification = 'OBSERVED'; state.operations.push(op); endpoint(op); candidate(op); log(new Date().toLocaleTimeString(), 'REQUEST', op.transport.toUpperCase(), op.method, op.url_path); return op; };
  const updateOp = (op, patch) => { if (!op) return; Object.assign(op, patch); endpoint(op); candidate(op); };
  const decodeAndObserveStream = async (response, op) => {
    if (!response || !response.body || !response.body.getReader || !state.config.inspectResponseBodies) { updateOp(op, { response_body_observation: 'NOT_CAPTURED' }); return; }
    let clone;
    try { clone = response.clone(); } catch (_) { updateOp(op, { response_body_observation: 'NOT_CAPTURED' }); return; }
    const ct = contentType(clone.headers), reader = clone.body && clone.body.getReader && clone.body.getReader();
    if (!reader) { updateOp(op, { response_body_observation: 'NOT_CAPTURED' }); return; }
    const stream = { status: 'OBSERVED', operation_id: op.id, transport: 'fetch-readable-stream', content_type: ct, chunks: 0, chunk_sizes: [], timings_ms: [], framing: 'UNKNOWN', events: [], completion_signal: 'UNKNOWN', error_pattern: 'UNKNOWN', truncated: false };
    const started = performance.now(), decoder = new TextDecoder(); let total = 0, text = '';
    try {
      while (stream.chunks < MAX_STREAM_CHUNKS && total < MAX_STREAM_BYTES) {
        const r = await reader.read(); if (r.done) { stream.completion_signal = 'reader_done'; break; }
        const bytes = r.value || new Uint8Array(); stream.chunks++; total += bytes.byteLength; stream.chunk_sizes.push(bytes.byteLength); stream.timings_ms.push(Math.round(performance.now() - started));
        if (/^(text\/|application\/(?:json|[^;]+\+json))/i.test(ct)) text += decoder.decode(bytes, { stream: true });
      }
      if (stream.chunks >= MAX_STREAM_CHUNKS || total >= MAX_STREAM_BYTES) stream.truncated = true;
      if (/text\/event-stream/i.test(ct) || /\n(?:data|event):/i.test(text)) {
        stream.framing = 'SSE_LIKE_OBSERVED';
        text.split(/\r?\n\r?\n/).slice(0, 20).forEach(block => {
          const data = block.split(/\r?\n/).filter(l => l.startsWith('data:')).map(l => l.slice(5).trim()).join('\n');
          if (!data) return; if (/^\[DONE\]$/i.test(data)) stream.completion_signal = 'data_DONE';
          else { try { stream.events.push({ shape: shape(JSON.parse(data)) }); } catch (_) { stream.events.push({ shape: { type: 'text', length: data.length } }); } }
        });
      } else if (/json/i.test(ct) && text) { try { updateOp(op, { response_schema: shape(JSON.parse(text.slice(0, state.config.maxResponseBytes))) }); } catch (_) { /* no content retained */ } }
    } catch (err) { stream.error_pattern = 'reader_error'; stream.error_category = err && err.name || 'Error'; }
    finally { try { await reader.cancel(); } catch (_) {} }
    state.streams.push(stream); updateOp(op, { streaming_candidate: stream.chunks > 1 || /event-stream/i.test(ct), stream_id: `STREAM-${state.streams.length}`, response_body_observation: 'SCHEMA_ONLY' });
    log(new Date().toLocaleTimeString(), 'STREAM', op.url_path, `chunks=${stream.chunks}`, stream.completion_signal);
  };
  const installFetch = () => {
    if (state.originals.fetch || !globalThis.fetch) return;
    state.originals.fetch = globalThis.fetch;
    globalThis.fetch = function dsPassiveFetch(input, init) {
      const req = input instanceof Request ? input : null, u = sanitizeURL(req ? req.url : input);
      const method = (init && init.method) || (req && req.method) || 'GET';
      const h = headerNames((init && init.headers) || (req && req.headers));
      const b = bodyShape(init && Object.prototype.hasOwnProperty.call(init, 'body') ? init.body : null);
      let requestCT = 'UNKNOWN'; try { requestCT = (init && init.headers && new Headers(init.headers).get('content-type')) || (req && contentType(req.headers)) || 'UNKNOWN'; } catch (_) { /* preserve original request behavior */ }
      const op = addOp({ transport: 'fetch', method: String(method).toUpperCase(), url_origin: u.origin, url_path: u.path, query_keys: u.query_keys, request_url: u.url, request_content_type: requestCT, request_headers: h.names.concat(h.redacted), request_body: b, response_content_type: 'UNKNOWN', status: null, duration_ms: null, initiator: 'window.fetch', streaming_candidate: false });
      const began = performance.now(); let result;
      try { result = state.originals.fetch.apply(this, arguments); } catch (e) { updateOp(op, { error: 'synchronous_fetch_error', duration_ms: Math.round(performance.now() - began) }); throw e; }
      Promise.resolve(result).then(response => { const ct = contentType(response.headers); updateOp(op, { status: response.status, response_content_type: ct, response_kind: responseKind(ct), duration_ms: Math.round(performance.now() - began), response_header_names: headerNames(response.headers).names, streaming_candidate: /text\/event-stream/i.test(ct) || !!(response.body && response.body.getReader) }); if (active()) decodeAndObserveStream(response, op); log(new Date().toLocaleTimeString(), 'RESPONSE', response.status, ct, u.path); }, err => updateOp(op, { error: err && err.name || 'fetch_error', duration_ms: Math.round(performance.now() - began) }));
      return result;
    };
  };
  const installXHR = () => {
    if (state.originals.XMLHttpRequest || !globalThis.XMLHttpRequest) return;
    const Original = state.originals.XMLHttpRequest = globalThis.XMLHttpRequest;
    const open = Original.prototype.open, send = Original.prototype.send, setHeader = Original.prototype.setRequestHeader;
    state.originals.xhrOpen = open; state.originals.xhrSend = send; state.originals.xhrSetHeader = setHeader;
    Original.prototype.open = function(method, url) { this.__dsObs = { method: String(method || 'GET').toUpperCase(), url: sanitizeURL(url), headers: [], began: null, op: null }; return open.apply(this, arguments); };
    Original.prototype.setRequestHeader = function(name) { if (this.__dsObs) this.__dsObs.headers.push(String(name)); return setHeader.apply(this, arguments); };
    Original.prototype.send = function(body) {
      const x = this.__dsObs || { method: 'UNKNOWN', url: sanitizeURL(''), headers: [] }; x.began = performance.now();
      x.op = addOp({ transport: 'xhr', method: x.method, url_origin: x.url.origin, url_path: x.url.path, query_keys: x.url.query_keys, request_url: x.url.url, request_content_type: 'UNKNOWN', request_headers: headerNames(x.headers.map(k => [k, ''])).names, request_body: bodyShape(body), response_content_type: 'UNKNOWN', status: null, duration_ms: null, initiator: 'XMLHttpRequest', streaming_candidate: false, lifecycle: ['OPENED', 'SENT'] });
      const observe = () => { if (!x.op) return; const ct = (() => { try { return this.getResponseHeader('content-type') || 'UNKNOWN'; } catch (_) { return 'UNKNOWN'; } })(); const patch = { status: this.status || null, response_content_type: ct, response_kind: responseKind(ct), duration_ms: Math.round(performance.now() - x.began), lifecycle: (x.op.lifecycle || []).concat([this.readyState === 2 ? 'HEADERS_RECEIVED' : this.readyState === 3 ? 'LOADING' : this.readyState === 4 ? 'DONE' : 'STATE_' + this.readyState]), streaming_candidate: this.readyState === 3 || /event-stream/i.test(ct) };
        if (this.readyState === 4 && state.config.inspectResponseBodies && /json/i.test(ct) && typeof this.responseText === 'string' && this.responseText.length <= state.config.maxResponseBytes) { try { patch.response_schema = shape(JSON.parse(this.responseText)); } catch (_) {} }
        updateOp(x.op, patch); };
      this.addEventListener('readystatechange', observe); this.addEventListener('error', () => updateOp(x.op, { error: 'xhr_error' })); this.addEventListener('abort', () => updateOp(x.op, { error: 'xhr_abort' }));
      return send.apply(this, arguments);
    };
  };
  const installEventSource = () => {
    if (state.originals.EventSource || !globalThis.EventSource) return;
    const Original = state.originals.EventSource = globalThis.EventSource;
    function WrappedEventSource(url, config) {
      const u = sanitizeURL(url), es = new Original(url, config), op = addOp({ transport: 'eventsource', method: 'GET', url_origin: u.origin, url_path: u.path, query_keys: u.query_keys, request_url: u.url, request_content_type: 'none', response_content_type: 'text/event-stream', status: null, duration_ms: null, initiator: 'EventSource', streaming_candidate: true });
      const stream = { status: 'OBSERVED', operation_id: op && op.id || null, transport: 'eventsource', content_type: 'text/event-stream', chunks: 0, chunk_sizes: [], timings_ms: [], framing: 'SSE_OBSERVED', events: [], completion_signal: 'UNKNOWN', error_pattern: 'UNKNOWN' }; const began = performance.now();
      es.addEventListener('open', () => { updateOp(op, { status: 200 }); log(new Date().toLocaleTimeString(), 'EVENTSOURCE open', u.path); });
      es.addEventListener('message', ev => { if (!active()) return; stream.chunks++; const data = safeString(ev.data); stream.chunk_sizes.push(data.length); stream.timings_ms.push(Math.round(performance.now() - began)); let s; try { s = shape(JSON.parse(data)); } catch (_) { s = { type: 'text', length: data.length }; } stream.events.push({ event_type: 'message', last_event_id_present: !!ev.lastEventId, shape: s }); });
      es.addEventListener('error', () => { stream.error_pattern = 'eventsource_error'; state.streams.push(stream); });
      return es;
    }
    WrappedEventSource.prototype = Original.prototype; Object.setPrototypeOf(WrappedEventSource, Original); globalThis.EventSource = WrappedEventSource;
  };
  const installWebSocket = () => {
    if (state.originals.WebSocket || !globalThis.WebSocket) return;
    const Original = state.originals.WebSocket = globalThis.WebSocket;
    function WrappedWebSocket(url, protocols) {
      const u = sanitizeURL(url), ws = protocols === undefined ? new Original(url) : new Original(url, protocols), op = addOp({ transport: 'websocket', method: 'CONNECT', url_origin: u.origin, url_path: u.path, query_keys: u.query_keys, request_url: u.url, request_content_type: 'UNKNOWN', response_content_type: 'websocket', status: null, duration_ms: null, initiator: 'WebSocket', streaming_candidate: true, protocols: Array.isArray(protocols) ? protocols.map(String) : protocols ? [String(protocols)] : [] });
      const began = performance.now(), stream = { status: 'OBSERVED', operation_id: op && op.id || null, transport: 'websocket', content_type: 'websocket', chunks: 0, chunk_sizes: [], timings_ms: [], framing: 'message_boundaries_observed', events: [], completion_signal: 'UNKNOWN', error_pattern: 'UNKNOWN' };
      ws.addEventListener('open', () => updateOp(op, { status: 101, duration_ms: Math.round(performance.now() - began) }));
      ws.addEventListener('message', ev => { if (!active()) return; stream.chunks++; const d = ev.data, size = typeof d === 'string' ? d.length : d && (d.size || d.byteLength) || 0; stream.chunk_sizes.push(size); stream.timings_ms.push(Math.round(performance.now() - began)); if (typeof d === 'string') { try { stream.events.push({ direction: 'received', shape: shape(JSON.parse(d)) }); } catch (_) { stream.events.push({ direction: 'received', shape: { type: 'text', length: d.length } }); } } else stream.events.push({ direction: 'received', shape: { type: d instanceof Blob ? 'blob' : 'binary', size } }); });
      ws.addEventListener('error', () => { stream.error_pattern = 'websocket_error'; }); ws.addEventListener('close', ev => { stream.completion_signal = 'close'; stream.close_code = ev.code; stream.close_reason_category = ev.reason ? 'present_redacted' : 'absent'; state.streams.push(stream); updateOp(op, { close_code: ev.code }); });
      return ws;
    }
    WrappedWebSocket.prototype = Original.prototype; Object.setPrototypeOf(WrappedWebSocket, Original); globalThis.WebSocket = WrappedWebSocket;
  };
  const probableCategory = (key) => isSensitiveKey(key) ? 'AUTHENTICATION_RELATED' : /(theme|language|locale|ui|preference|setting)/i.test(key) ? 'UI_PREFERENCE' : /(conversation|message|chat|history)/i.test(key) ? 'CONVERSATION_RELATED' : 'OTHER';
  const inspectWebStorage = (store, name) => {
    const entries = [];
    try { for (let i = 0; i < store.length; i++) { const key = store.key(i); const value = store.getItem(key); const sensitive = isSensitiveKey(key) || isLikelySecret(value); let valueType = 'string', valueSchema = undefined; if (!sensitive && value && value.length <= 8192) { try { valueSchema = shape(JSON.parse(value)); valueType = 'json-string'; } catch (_) {} } entries.push({ key: sensitive ? 'auth-related-key' : key, classification: probableCategory(key), value_type: valueType, size: value ? value.length : 0, value: sensitive ? '<REDACTED>' : undefined, schema: valueSchema }); } } catch (e) { return { status: 'UNKNOWN', error_category: e.name || 'Error' }; }
    return { status: 'OBSERVED', mechanism: name, persistent: name === 'localStorage', entries };
  };
  const inspectIDB = async () => {
    const result = { status: 'UNKNOWN', databases: [] };
    if (!globalThis.indexedDB) return result;
    try {
      if (!indexedDB.databases) { result.status = 'OBSERVED_LIMITED'; result.note = 'indexedDB.databases() unavailable'; return result; }
      const dbs = await indexedDB.databases(); result.status = 'OBSERVED';
      await Promise.all(dbs.map(info => new Promise(resolve => { if (!info.name) return resolve(); const request = indexedDB.open(info.name); request.onerror = () => { result.databases.push({ name: info.name, version: info.version || null, status: 'UNREADABLE' }); resolve(); }; request.onsuccess = () => { const db = request.result; const stores = Array.from(db.objectStoreNames).map(name => { const tx = db.transaction(name, 'readonly'), s = tx.objectStore(name); return { name, keyPath: s.keyPath || null, autoIncrement: !!s.autoIncrement, indexes: Array.from(s.indexNames), approximate_record_count: 'NOT_READ' }; }); result.databases.push({ name: info.name, version: db.version, stores }); db.close(); resolve(); }; })));
    } catch (e) { result.status = 'UNKNOWN'; result.error_category = e.name || 'Error'; }
    return result;
  };
  const inspectCachesAndSW = async () => {
    const out = { cache_storage: { status: 'UNKNOWN', caches: [] }, service_workers: { status: 'UNKNOWN', registrations: [] } };
    try { if (globalThis.caches) { const names = await caches.keys(); out.cache_storage.status = 'OBSERVED'; for (const name of names) { const cache = await caches.open(name), keys = await cache.keys(); out.cache_storage.caches.push({ name, entry_count: keys.length, resource_paths: keys.slice(0, 100).map(r => sanitizeURL(r.url).path), truncated: keys.length > 100 }); } } } catch (e) { out.cache_storage.error_category = e.name || 'Error'; }
    try { if (navigator.serviceWorker) { const regs = await navigator.serviceWorker.getRegistrations(); out.service_workers.status = 'OBSERVED'; out.service_workers.registrations = regs.map(r => ({ scope: sanitizeURL(r.scope).origin + sanitizeURL(r.scope).path, active_state: r.active && r.active.state || 'none', waiting: !!r.waiting, installing: !!r.installing })); } } catch (e) { out.service_workers.error_category = e.name || 'Error'; }
    return out;
  };
  const inspectStorage = async () => {
    state.storage = { inspected_at: now(), localStorage: inspectWebStorage(localStorage, 'localStorage'), sessionStorage: inspectWebStorage(sessionStorage, 'sessionStorage'), indexedDB: await inspectIDB(), ...(await inspectCachesAndSW()) };
    return state.storage;
  };
  const addListener = (target, type, handler, opts) => { target.addEventListener(type, handler, opts); state.listeners.push([target, type, handler, opts]); };
  const installDOM = () => {
    const fileHandler = ev => { if (!active()) return; const files = ev.target && ev.target.files || ev.dataTransfer && ev.dataTransfer.files; if (!files) return; Array.from(files).forEach(file => { const safeName = state.config.captureTestPayloads && testValue(file.name) ? file.name : '<REDACTED_OR_TEST_FILENAME>'; const entry = { status: 'OBSERVED', timestamp: now(), scenario: currentScenarioId(), operation: 'possible_upload', filename: safeName, mime_type: file.type || 'UNKNOWN', size: file.size, transport: 'UNKNOWN', endpoint: null }; state.attachments.push(entry); log(new Date().toLocaleTimeString(), 'ATTACHMENT selected', file.type || 'UNKNOWN', `${file.size} bytes`); }); };
    addListener(document, 'change', fileHandler, true); addListener(document, 'drop', fileHandler, true);
  };
  const scanPerformance = () => {
    if (!state.config.scanPerformance || !performance.getEntriesByType) return;
    state.performance = performance.getEntriesByType('resource').map(e => { const u = sanitizeURL(e.name); return { status: 'OBSERVED', name_origin: u.origin, name_path: u.path, initiator_type: e.initiatorType, duration_ms: Math.round(e.duration), transfer_size: e.transferSize || 0, encoded_body_size: e.encodedBodySize || 0, decoded_body_size: e.decodedBodySize || 0 }; });
  };
  const redact = (value, key = '') => {
    if (isSensitiveKey(key)) return '<REDACTED>';
    if (typeof value === 'string') return isLikelySecret(value) ? '<REDACTED>' : value;
    if (Array.isArray(value)) return value.map(v => redact(v));
    if (value && typeof value === 'object') { const out = {}; Object.keys(value).forEach(k => { out[k] = redact(value[k], k); }); return out; }
    return value;
  };
  const api = {
    __dsPassiveObserver: true,
    start() { if (state.running) return api.status(); state.running = true; state.paused = false; state.startedAt = now(); installFetch(); installXHR(); installEventSource(); installWebSocket(); installDOM(); scanPerformance(); inspectStorage().catch(e => state.errors.push({ timestamp: now(), category: 'storage_inspection_error', name: e.name || 'Error' })); log('Passive observer running. No data leaves this browser.'); return api.status(); },
    stop() { state.running = false; state.paused = false; log('Observation paused/stopped; wrappers remain installed until reset().'); return api.status(); },
    pause() { state.paused = true; log('Paused.'); return api.status(); },
    resume() { state.running = true; state.paused = false; log('Resumed.'); return api.status(); },
    clear() { state.operations = []; state.streams = []; state.attachments = []; state.endpointInventory.clear(); state.schemas = { messageCandidates: [], responseShapes: [] }; state.scenarios = []; state.currentScenario = null; state.errors = []; state.performance = []; state.sequence = 0; state.endpointSequence = 0; state.scenarioSequence = 0; log('In-memory observations cleared; site state untouched.'); return api.status(); },
    reset() { api.stop(); if (state.originals.fetch) globalThis.fetch = state.originals.fetch; if (state.originals.XMLHttpRequest) { const X = state.originals.XMLHttpRequest; X.prototype.open = state.originals.xhrOpen; X.prototype.send = state.originals.xhrSend; X.prototype.setRequestHeader = state.originals.xhrSetHeader; globalThis.XMLHttpRequest = X; } if (state.originals.EventSource) globalThis.EventSource = state.originals.EventSource; if (state.originals.WebSocket) globalThis.WebSocket = state.originals.WebSocket; state.listeners.forEach(([t, ty, h, o]) => { try { t.removeEventListener(ty, h, o); } catch (_) {} }); state.listeners = []; api.clear(); state.installed = false; try { delete globalThis.DeepSeekObserver; } catch (_) { globalThis.DeepSeekObserver = undefined; } log('Reset complete. Original browser APIs restored; website storage/authentication untouched.'); },
    mark(name) { if (!name || typeof name !== 'string') throw new Error('Scenario name must be a string.'); if (state.currentScenario) api.endScenario(); const scenario = { id: `SCENARIO-${String(++state.scenarioSequence).padStart(3, '0')}`, label: name, started_at: now(), ended_at: null, operation_ids: [], status: 'OBSERVED_MARKER' }; state.currentScenario = scenario; state.scenarios.push(scenario); log('Scenario started:', name); return scenario.id; },
    endScenario() { if (!state.currentScenario) return null; state.currentScenario.ended_at = now(); const done = state.currentScenario; state.currentScenario = null; log('Scenario ended:', done.label); return done; },
    config(options) { if (!options || typeof options !== 'object') return { ...state.config }; Object.keys(options).forEach(k => { if (k in state.config) state.config[k] = options[k]; }); return { ...state.config }; },
    status() { return { status: state.running ? (state.paused ? 'PAUSED' : 'RUNNING') : 'STOPPED', version: VERSION, started_at: state.startedAt, active_scenario: currentScenarioId(), local_only: true, passive: true }; },
    summary() { const s = { endpoints_observed: state.endpointInventory.size, streaming_operations: state.streams.length, xhr_operations: state.operations.filter(o => o.transport === 'xhr').length, fetch_operations: state.operations.filter(o => o.transport === 'fetch').length, webSockets: state.operations.filter(o => o.transport === 'websocket').length, eventSource: state.operations.filter(o => o.transport === 'eventsource').length, storage_databases: state.storage.indexedDB && state.storage.indexedDB.databases && state.storage.indexedDB.databases.length || 0, localStorage_keys: state.storage.localStorage && state.storage.localStorage.entries && state.storage.localStorage.entries.length || 0, indexedDB_stores: state.storage.indexedDB && state.storage.indexedDB.databases ? state.storage.indexedDB.databases.reduce((n, d) => n + (d.stores || []).length, 0) : 0, attachments_observed: state.attachments.length, scenarios: state.scenarios.length }; console.table(s); return s; },
    export() { const scenarioMap = new Map(state.scenarios.map(s => [s.id, s])); state.operations.forEach(o => { if (o.scenario && scenarioMap.has(o.scenario)) { const a = scenarioMap.get(o.scenario).operation_ids; if (!a.includes(o.id)) a.push(o.id); } }); const output = redact({ metadata: { observer: 'DeepSeek Web Passive Observer', version: VERSION, exported_at: now(), local_only: true, safety: 'No requests were generated, replayed, modified, or transmitted by the observer.' }, endpoint_inventory: Array.from(state.endpointInventory.values()), scenarios: state.scenarios, operations: state.operations, stream_observations: state.streams, storage_schema: state.storage, attachment_observations: state.attachments, message_conversation_candidates: state.schemas.messageCandidates, performance_entries: state.performance, errors: state.errors }); return output; },
    download() { const json = JSON.stringify(api.export(), null, 2), blob = new Blob([json], { type: 'application/json' }), a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `deepseek_observation_${now().replace(/[:.]/g, '-')}.json`; a.style.display = 'none'; document.documentElement.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000); log('Sanitized local JSON download started. Review before adding to Git.'); },
    help() { console.log(`DeepSeekObserver commands:\n start() stop() pause() resume() clear() reset()\n status() summary() export() download()\n mark("B02_SEND_MESSAGE") endScenario() config({captureTestPayloads:true})\n Passive only: no request replay, no credential export, no remote transmission.`); },
    inspectStorage
  };
  globalThis.DeepSeekObserver = api; state.installed = true;
  console.log('╔══════════════════════════════════════════╗\n║ DeepSeek Web Passive Observer             ║\n║ STATUS: RUNNING                           ║\n╚══════════════════════════════════════════╝');
  api.start(); api.help();
})();
