/* ============================================================
   GULA Platform - Core Application
   Lightweight SPA: Router, API, Pages, State
   ============================================================ */

/* ── Offline Queue ─────────────────────────────────────────────────────────
   Mutations (POST/PUT/DELETE) that fail because the device is offline are
   stored in IndexedDB and replayed automatically when connectivity returns.
   Medical data is NEVER dropped silently — it is either sent or queued.
   ─────────────────────────────────────────────────────────────────────── */
const _OQ = (() => {
  const DB_NAME  = 'gula-offline-q';
  const STORE    = 'ops';
  let _db = null;

  function open() {
    if (_db) return Promise.resolve(_db);
    return new Promise((res, rej) => {
      const r = indexedDB.open(DB_NAME, 1);
      r.onupgradeneeded = e =>
        e.target.result.createObjectStore(STORE, { autoIncrement: true });
      r.onsuccess = e => { _db = e.target.result; res(_db); };
      r.onerror   = rej;
    });
  }

  async function push(path, opts) {
    const db = await open();
    return new Promise((res, rej) => {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).add({ path, opts: { ...opts, body: opts.body }, ts: Date.now() });
      tx.oncomplete = res;
      tx.onerror    = rej;
    });
  }

  async function flush() {
    const db   = await open();
    const tx   = db.transaction(STORE, 'readwrite');
    const st   = tx.objectStore(STORE);
    const items = await new Promise(r => { const q = st.getAll();    q.onsuccess = () => r(q.result); });
    const keys  = await new Promise(r => { const q = st.getAllKeys(); q.onsuccess = () => r(q.result); });
    let synced = 0;
    for (let i = 0; i < items.length; i++) {
      try {
        await api(items[i].path, items[i].opts);
        const tx2 = db.transaction(STORE, 'readwrite');
        tx2.objectStore(STORE).delete(keys[i]);
        synced++;
      } catch { /* keep in queue */ }
    }
    if (synced > 0 && typeof toast === 'function')
      toast(`↑ تمت مزامنة ${synced} عملية محفوظة`, 'success');
    return synced;
  }

  return { push, flush };
})();

/* ── Connectivity Banner ───────────────────────────────────────────────────
   Shows a fixed bottom bar when offline; auto-flushes queue on reconnect.
   Injected once after DOMContentLoaded so it works on every page.
   ─────────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const bar = Object.assign(document.createElement('div'), { id: '_connBanner' });
  bar.style.cssText = [
    'position:fixed;bottom:0;inset-inline:0;z-index:9990',
    'padding:9px 16px;font-size:.8rem;text-align:center',
    'border-top:1px solid transparent',
    'transition:transform .25s ease,opacity .25s ease',
    'transform:translateY(100%);opacity:0;pointer-events:none',
  ].join(';');
  document.body.appendChild(bar);

  function show(msg, bg, col, border) {
    Object.assign(bar.style, {
      background: bg, color: col, borderTopColor: border,
      transform: 'translateY(0)', opacity: '1', pointerEvents: 'auto',
    });
    bar.textContent = msg;
  }
  function hide() {
    bar.style.transform = 'translateY(100%)';
    bar.style.opacity   = '0';
  }

  function goOffline() {
    show('🔌 لا يوجد اتصال — التغييرات ستُحفظ وتُزامَن لاحقاً',
      '#450a0a', '#fca5a5', '#dc2626');
  }
  function goOnline() {
    show('↑ عاد الاتصال — جاري المزامنة…', '#022c22', '#6ee7b7', '#10b981');
    _OQ.flush().finally(() => setTimeout(hide, 2500));
    // Ask the service worker to sync too (Background Sync API)
    if ('serviceWorker' in navigator && 'SyncManager' in window)
      navigator.serviceWorker.ready
        .then(sw => sw.sync.register('gula-queue'))
        .catch(() => {});
  }

  window.addEventListener('offline', goOffline);
  window.addEventListener('online',  goOnline);
  if (!navigator.onLine) goOffline();

  // Service-worker-initiated flush (when page was closed during offline)
  if ('serviceWorker' in navigator)
    navigator.serviceWorker.addEventListener('message', e => {
      if (e.data?.type === 'FLUSH_QUEUE') _OQ.flush();
    });
});

// ---- Constants ----
const PAGE_SIZE = 50;

// ---- State ----
// Token stored in httpOnly cookie (not accessible here - prevents XSS theft)
// Only non-sensitive user metadata (name, role, lab_id) stored in sessionStorage
const G = {
  user: JSON.parse(sessionStorage.getItem('user') || 'null'),
  page: null
};

// ---- API Helper with timeout & retry ----
const API_TIMEOUT = 15000; // 15 second timeout
const API_RETRY_DELAYS = [1000, 2000]; // Retry delays for GET requests

async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  // Token sent automatically via httpOnly cookie (credentials: 'include')
  // No Authorization header needed for web - prevents XSS token theft

  const isGet = !opts.method || opts.method === 'GET';
  const maxRetries = isGet ? API_RETRY_DELAYS.length : 0;

  // If device is offline and this is a mutation, queue and return a sentinel
  if (!navigator.onLine && !isGet && !opts._isReplay) {
    await _OQ.push(path, opts);
    if (typeof toast === 'function')
      toast('📥 حُفظت العملية — ستُرسل عند عودة الاتصال', 'info');
    return { _queued: true };
  }

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), API_TIMEOUT);
    let res;
    try {
      res = await fetch('/api' + path, { ...opts, headers, credentials: 'include', signal: controller.signal });
      clearTimeout(timer);
    } catch (e) {
      clearTimeout(timer);
      // Network error on a mutation → queue for later
      if (!isGet && !opts._isReplay) {
        await _OQ.push(path, opts);
        if (typeof toast === 'function')
          toast('📥 حُفظت العملية — ستُرسل عند عودة الاتصال', 'info');
        return { _queued: true };
      }
      if (e.name === 'AbortError') {
        if (attempt < maxRetries) { await _sleep(API_RETRY_DELAYS[attempt]); continue; }
        throw new Error('انتهت مهلة الاتصال - تحقق من الشبكة');
      }
      if (attempt < maxRetries) { await _sleep(API_RETRY_DELAYS[attempt]); continue; }
      throw new Error('خطأ في الاتصال - تحقق من الشبكة');
    }
    if (res.status === 401) { logout(); return; }
    if (res.status === 403) throw new Error('ليس لديك صلاحية لهذا الإجراء');
    if (res.status === 429) throw new Error('طلبات كثيرة جداً - حاول لاحقاً');
    // Retry on 502/503/504 for GET only
    if (isGet && res.status >= 502 && res.status <= 504 && attempt < maxRetries) {
      await _sleep(API_RETRY_DELAYS[attempt]); continue;
    }
    let data;
    try {
      data = await res.json();
    } catch {
      if (!res.ok) throw new Error('خطأ في الخادم');
      return {};
    }
    if (!res.ok) throw new Error(data.detail || data.detail_ar || 'خطأ في الخادم');
    return data;
  }
}

function _sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ---- Auth ----
async function logout() {
  // Clear httpOnly auth cookie via server endpoint
  try { await fetch('/api/logout', { method: 'POST', credentials: 'include' }); } catch {}
  sessionStorage.removeItem('user');
  G.user = null;
  window.location.replace('/login.html');
}

function checkAuth() {
  if (!G.user) { window.location.href = '/login.html'; return false; }
  return true;
}

// ---- UI Helpers ----
function $(id) { return document.getElementById(id); }

// XSS protection: escape user-provided strings before inserting into HTML
function esc(str) {
  if (str == null) return '';
  const d = document.createElement('div');
  d.textContent = String(str);
  return d.innerHTML;
}

// Escape for use inside HTML attribute values (e.g. onclick="fn('${escAttr(val)}')")
function escAttr(str) {
  if (str == null) return '';
  return String(str).replace(/&/g,'&amp;').replace(/'/g,'&#39;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function toast(msg, type = 'success') {
  const t = $('toast');
  t.textContent = msg;
  t.className = 'toast show ' + type;
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.className = 'toast', 3000);
}

let _modalFocusTimer;
/**
 * Open the modal dialog.
 * @param {string} title  - Plain text title (inserted via textContent — safe).
 * @param {string} html   - Trusted HTML body.  MUST only contain pre-escaped
 *                          user data (use esc()/escAttr() before inserting).
 *                          Never pass raw API strings directly as `html`.
 */
function openModal(title, html) {
  clearTimeout(_modalFocusTimer);
  $('modalTitle').textContent = title;
  $('modalBody').innerHTML = html;
  $('modal').style.display = 'flex';
  const firstInput = $('modalBody').querySelector('input,select,textarea');
  if (firstInput) _modalFocusTimer = setTimeout(() => { if (document.contains(firstInput)) firstInput.focus(); }, 50);
}

/** Safe variant: both title and body are treated as plain text — no XSS risk. */
function openModalText(title, message) {
  openModal(title, '<p>' + esc(message) + '</p>');
}

function closeModal() { clearTimeout(_modalFocusTimer); $('modal').style.display = 'none'; }

function toggleSidebar() { $('sidebar').classList.toggle('open'); }

function formatDate(d) {
  if (!d) return '-';
  return new Date(d).toLocaleDateString('ar-IQ', { year: 'numeric', month: 'short', day: 'numeric' });
}

function timeAgo(d) {
  const diff = (Date.now() - new Date(d)) / 1000;
  if (diff < 60) return 'الآن';
  if (diff < 3600) return Math.floor(diff / 60) + ' دقيقة';
  if (diff < 86400) return Math.floor(diff / 3600) + ' ساعة';
  return Math.floor(diff / 86400) + ' يوم';
}

function statusBadge(status) {
  const map = {
    collected: ['تم الجمع', 'blue'], received: ['مستلمة', 'blue'],
    processing: ['قيد المعالجة', 'yellow'], analyzed: ['مكتملة', 'green'],
    rejected: ['مرفوضة', 'red'], completed: ['مكتملة', 'green'],
    pending: ['معلقة', 'gray']
  };
  const [label, color] = map[status] || [esc(status), 'gray'];
  return `<span class="badge badge-${color}">${label}</span>`;
}

function resultFlag(val, low, high) {
  const v = parseFloat(val);
  if (isNaN(v) || !low || !high) return '';
  if (v < parseFloat(low)) return '<span class="val-low">&#x25BC; منخفض</span>';
  if (v > parseFloat(high)) return '<span class="val-high">&#x25B2; مرتفع</span>';
  return '<span class="val-normal">طبيعي</span>';
}

// Confirmation dialog replacing prompt() and confirm()
function confirmAction(title, message, onConfirm, hasInput = false, inputLabel = '') {
  let inputHtml = '';
  if (hasInput) {
    inputHtml = `<div class="field" style="margin-top:12px"><label>${esc(inputLabel)}</label><input id="confirmInput" class="search-input" required></div>`;
  }
  openModal(title, `
    <p style="margin-bottom:16px;color:var(--text-dim)">${esc(message)}</p>
    ${inputHtml}
    <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
      <button class="btn btn-outline" onclick="closeModal()">إلغاء</button>
      <button class="btn btn-primary" id="confirmBtn">تأكيد</button>
    </div>
  `);
  $('confirmBtn').onclick = function() {
    const val = hasInput ? $('confirmInput').value : true;
    if (hasInput && !val) { toast('الرجاء إدخال القيمة', 'error'); return; }
    closeModal();
    onConfirm(val);
  };
}

// Phone validation (Iraqi format)
function isValidPhone(phone) {
  const cleaned = phone.replace(/[\s\-\+]/g, '');
  // Iraqi: 07xxxxxxxxx (11 digits) or +9647xxxxxxxxx
  return /^(07\d{9}|9647\d{9}|\+9647\d{9})$/.test(cleaned);
}

// ---- Keyboard Shortcuts ----
document.addEventListener('keydown', function(e) {
  // Escape closes modal
  if (e.key === 'Escape' && $('modal').style.display === 'flex') {
    closeModal();
  }
});

// ---- WORKFLOW PAGE (⚡ إدخال سريع) ----
// Single workspace: patient search → test entry → WhatsApp share
// Keyboard-first: Enter moves between fields
let _wfPatient = null; // selected patient
let _wfTests = [];     // [{name,val,unit,low,high}]
let _wfPatientCache = [];

async function pageWorkflow() {
  $('page').innerHTML = `
    <div class="wf-layout">
      <!-- LEFT: Quick Patient List -->
      <div class="wf-left">
        <div class="wf-section-title">المرضى الأخيرون</div>
        <div class="wf-search-wrap">
          <input id="wfSearch" class="wf-search" placeholder="🔍 اسم أو هاتف..." autocomplete="off"
            oninput="wfSearchPatients(this.value)" onkeydown="if(event.key==='Enter'){wfSearchPatients(this.value,true)}">
        </div>
        <div id="wfPatientList" class="wf-patient-list"><div class="spinner"></div></div>
        <button class="btn btn-outline btn-sm" style="width:100%;margin-top:8px" onclick="wfNewPatient()">+ مريض جديد</button>
      </div>

      <!-- CENTER: Entry Workspace -->
      <div class="wf-center">
        <div id="wfPatientBanner" class="wf-patient-banner wf-unselected">
          <span>← اختر مريضاً من القائمة أو ابحث</span>
        </div>
        <div id="wfForm" class="wf-form" style="display:none">
          <div class="wf-field-row">
            <div class="field"><label>اسم الطبيب (اختياري)</label>
              <input id="wfDoctor" class="wf-input" placeholder="د. أحمد...">
            </div>
          </div>
          <div class="wf-tests-header">
            <span class="wf-section-title">التحاليل</span>
            <button class="btn btn-outline btn-sm" onclick="wfAddTest()">+ تحليل</button>
          </div>
          <div id="wfTests"></div>
          <div id="wfTypeSuggest" class="wf-suggest" style="display:none"></div>
          <div class="wf-actions">
            <button class="btn btn-primary" onclick="wfSubmit()" id="wfSubmitBtn">
              💾 حفظ وإنشاء الرابط
            </button>
            <button class="btn btn-outline" onclick="wfReset()">إعادة تعيين</button>
          </div>
        </div>
        <div id="wfResult" class="wf-result-box" style="display:none"></div>
      </div>

      <!-- RIGHT: Recent Orders -->
      <div class="wf-right">
        <div class="wf-section-title">آخر الطلبات</div>
        <div id="wfRecent" class="wf-recent-list"><div class="spinner"></div></div>
      </div>
    </div>
  `;
  _wfPatient = null;
  _wfTests = [];
  _wfPatientCache = [];
  wfLoadPatients();
  wfLoadRecent();
}

async function wfLoadPatients(query = '') {
  const el = $('wfPatientList');
  try {
    const path = query ? `/patients?search=${encodeURIComponent(query)}&limit=10` : `/patients?limit=10&skip=0`;
    const d = await api(path);
    const pts = d.patients || d;
    _wfPatientCache = Array.isArray(pts) ? pts : [];
    if (!_wfPatientCache.length) {
      el.innerHTML = '<div class="wf-empty">لا توجد نتائج</div>'; return;
    }
    el.innerHTML = _wfPatientCache.map(p => `
      <div class="wf-patient-item ${_wfPatient?.id === p.id ? 'active' : ''}"
           onclick="wfSelectPatient(${parseInt(p.id)})">
        <div class="wf-pt-name">${esc(p.full_name || p.name)}</div>
        <div class="wf-pt-phone">${esc(p.phone || '')}</div>
      </div>
    `).join('');
  } catch { el.innerHTML = '<div class="wf-empty">تعذر التحميل</div>'; }
}

let _wfSearchTimer;
function wfSearchPatients(q, immediate = false) {
  clearTimeout(_wfSearchTimer);
  const delay = immediate ? 0 : 350;
  _wfSearchTimer = setTimeout(() => wfLoadPatients(q.trim()), delay);
}

function wfSelectPatient(id) {
  const p = _wfPatientCache.find(x => x.id === id);
  if (!p) return;
  _wfPatient = p;
  // Update banner
  $('wfPatientBanner').className = 'wf-patient-banner wf-selected';
  $('wfPatientBanner').innerHTML = `
    <div class="wf-pt-selected-name">👤 ${esc(p.full_name || p.name)}</div>
    <div class="wf-pt-selected-meta">${esc(p.phone || '')} ${p.gender ? '· ' + esc(p.gender) : ''}</div>
    <button class="wf-pt-change" onclick="_wfPatient=null;wfReset()">تغيير</button>
  `;
  $('wfForm').style.display = 'block';
  $('wfResult').style.display = 'none';
  // Highlight in list
  document.querySelectorAll('.wf-patient-item').forEach(el => {
    el.classList.toggle('active', el.onclick?.toString().includes(`(${id})`));
  });
  // Re-render patient list to show active
  $('wfPatientList').querySelectorAll('.wf-patient-item').forEach(el => {
    el.classList.toggle('active', el.getAttribute('onclick')?.includes(`(${id})`));
  });
  if (!_wfTests.length) wfAddTest();
  // Focus first test name
  setTimeout(() => { const f = document.querySelector('.wf-tname'); if (f) f.focus(); }, 100);
}

async function wfLoadTypeSuggestions() {
  try {
    const d = await api('/test-types');
    return Array.isArray(d) ? d : [];
  } catch { return []; }
}
let _wfTypeCache = null;
async function wfGetTypes() {
  if (!_wfTypeCache) _wfTypeCache = await wfLoadTypeSuggestions();
  return _wfTypeCache;
}

function wfAddTest() {
  const idx = _wfTests.length;
  _wfTests.push({ name: '', val: '', unit: '', low: '', high: '' });
  const wrap = $('wfTests');
  const row = document.createElement('div');
  row.className = 'wf-test-row';
  row.dataset.idx = idx;
  row.innerHTML = `
    <div class="wf-test-fields">
      <div class="field wf-f-name">
        <label>اسم التحليل</label>
        <input class="wf-input wf-tname" data-idx="${idx}" placeholder="Glucose..." required autocomplete="off"
          oninput="wfTypeahead(this,${idx})"
          onkeydown="wfNavKey(event,${idx},'name')">
      </div>
      <div class="field wf-f-val">
        <label>القيمة</label>
        <input class="wf-input wf-tval" data-idx="${idx}" placeholder="5.2" required
          oninput="wfUpdateFlag(${idx})"
          onkeydown="wfNavKey(event,${idx},'val')">
      </div>
      <div class="field wf-f-unit">
        <label>الوحدة</label>
        <input class="wf-input wf-tunit" data-idx="${idx}" placeholder="mmol/L"
          onkeydown="wfNavKey(event,${idx},'unit')">
      </div>
      <div class="field wf-f-range">
        <label>أدنى</label>
        <input class="wf-input wf-tlow" data-idx="${idx}" type="number" step="any" placeholder="3.9"
          onkeydown="wfNavKey(event,${idx},'low')">
      </div>
      <div class="field wf-f-range">
        <label>أعلى</label>
        <input class="wf-input wf-thigh" data-idx="${idx}" type="number" step="any" placeholder="6.1"
          onkeydown="wfNavKey(event,${idx},'high')">
      </div>
      <div class="wf-flag" id="wfFlag${idx}"></div>
    </div>
    <button class="wf-del-btn" onclick="wfRemoveTest(${idx})" title="حذف">✕</button>
  `;
  wrap.appendChild(row);
  // Focus name field of new row
  setTimeout(() => row.querySelector('.wf-tname')?.focus(), 50);
}

function wfRemoveTest(idx) {
  const row = $('wfTests').querySelector(`[data-idx="${idx}"]`);
  if (row) row.remove();
}

function wfNavKey(e, idx, field) {
  if (e.key !== 'Enter') return;
  e.preventDefault();
  const fields = ['name', 'val', 'unit', 'low', 'high'];
  const i = fields.indexOf(field);
  if (i < fields.length - 1) {
    // Move to next field in same row
    const selectors = { name: '.wf-tname', val: '.wf-tval', unit: '.wf-tunit', low: '.wf-tlow', high: '.wf-thigh' };
    const row = $('wfTests').querySelector(`[data-idx="${idx}"]`);
    row?.querySelector(selectors[fields[i + 1]])?.focus();
  } else {
    // Last field → add new row or focus submit
    const nextRow = $('wfTests').querySelector(`[data-idx="${idx + 1}"]`);
    if (nextRow) {
      nextRow.querySelector('.wf-tname')?.focus();
    } else {
      wfAddTest();
    }
  }
}

async function wfTypeahead(input, idx) {
  const q = input.value.trim().toLowerCase();
  if (q.length < 2) { $('wfTypeSuggest').style.display = 'none'; return; }
  const types = await wfGetTypes();
  const matches = types.filter(t => t.name?.toLowerCase().includes(q) || t.name_ar?.includes(q)).slice(0, 6);
  if (!matches.length) { $('wfTypeSuggest').style.display = 'none'; return; }
  const sug = $('wfTypeSuggest');
  sug.style.display = 'block';
  sug.innerHTML = matches.map(t => `
    <div class="wf-sug-item" onclick="wfApplyType(${idx},'${escAttr(t.name || '')}','${escAttr(t.unit || '')}',${t.normal_low || ''},${t.normal_high || ''})">
      <span>${esc(t.name_ar || t.name)}</span>
      <span class="wf-sug-unit">${esc(t.unit || '')} ${t.normal_low != null ? '(' + t.normal_low + '-' + t.normal_high + ')' : ''}</span>
    </div>
  `).join('');
}

function wfApplyType(idx, name, unit, low, high) {
  const row = $('wfTests').querySelector(`[data-idx="${idx}"]`);
  if (!row) return;
  row.querySelector('.wf-tname').value = name;
  row.querySelector('.wf-tunit').value = unit;
  if (low)  row.querySelector('.wf-tlow').value  = low;
  if (high) row.querySelector('.wf-thigh').value = high;
  $('wfTypeSuggest').style.display = 'none';
  row.querySelector('.wf-tval')?.focus();
  wfUpdateFlag(idx);
}

function wfUpdateFlag(idx) {
  const row = $('wfTests').querySelector(`[data-idx="${idx}"]`);
  if (!row) return;
  const val  = parseFloat(row.querySelector('.wf-tval')?.value);
  const low  = parseFloat(row.querySelector('.wf-tlow')?.value);
  const high = parseFloat(row.querySelector('.wf-thigh')?.value);
  const flag = $(`wfFlag${idx}`);
  if (!flag) return;
  if (isNaN(val) || isNaN(low) || isNaN(high)) { flag.innerHTML = ''; return; }
  if (val < low)  { flag.innerHTML = '<span class="wf-flag-low">▼ منخفض</span>'; return; }
  if (val > high) { flag.innerHTML = '<span class="wf-flag-high">▲ مرتفع</span>'; return; }
  flag.innerHTML = '<span class="wf-flag-ok">✓ طبيعي</span>';
}

async function wfSubmit() {
  if (!_wfPatient) { toast('اختر مريضاً أولاً', 'error'); return; }
  const rows = $('wfTests').querySelectorAll('.wf-test-row');
  const results = [];
  for (const row of rows) {
    const name = row.querySelector('.wf-tname')?.value?.trim();
    const val  = row.querySelector('.wf-tval')?.value?.trim();
    if (!name || !val) continue;
    results.push({
      test_name: name,
      value: val,
      unit: row.querySelector('.wf-tunit')?.value?.trim() || undefined,
      normal_range_low:  parseFloat(row.querySelector('.wf-tlow')?.value)  || undefined,
      normal_range_high: parseFloat(row.querySelector('.wf-thigh')?.value) || undefined,
    });
  }
  if (!results.length) { toast('أدخل تحليلاً واحداً على الأقل', 'error'); return; }
  const btn = $('wfSubmitBtn');
  btn.disabled = true; btn.textContent = '... جاري الحفظ';
  try {
    const order = await api('/results/orders', { method: 'POST', body: JSON.stringify({
      patient_id: _wfPatient.id,
      doctor_name: $('wfDoctor')?.value?.trim() || undefined,
      results,
    })});
    // Build WhatsApp link from first result token
    const firstToken = order.results?.[0]?.result_token || order.order_id;
    const resultUrl = `${location.origin}/r/${firstToken || ''}`;
    const waText = `نتائج تحاليل ${_wfPatient.full_name || _wfPatient.name} جاهزة 🔬\n${resultUrl}`;
    const waLink = `https://wa.me/?text=${encodeURIComponent(waText)}`;
    $('wfResult').style.display = 'block';
    $('wfResult').innerHTML = `
      <div class="wf-success">
        <div class="wf-success-icon">✓</div>
        <div class="wf-success-title">تم الحفظ بنجاح!</div>
        <div class="wf-success-patient">${esc(_wfPatient.full_name || _wfPatient.name)}</div>
        <div class="wf-result-actions">
          <a href="${esc(waLink)}" target="_blank" rel="noopener" class="btn btn-wa">📤 واتساب</a>
          <button class="btn btn-outline" onclick="navigator.clipboard.writeText('${escAttr(resultUrl)}');toast('تم النسخ')">نسخ الرابط</button>
          <a href="/r/${escAttr(firstToken || '')}" target="_blank" rel="noopener" class="btn btn-outline">عرض النتيجة</a>
        </div>
        <div class="wf-result-link">${esc(resultUrl)}</div>
      </div>
    `;
    $('wfForm').style.display = 'none';
    wfLoadRecent();
    toast('تم الحفظ — جاهز للإرسال عبر واتساب');
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false; btn.textContent = '💾 حفظ وإنشاء الرابط';
}

function wfReset() {
  _wfPatient = null;
  _wfTests = [];
  $('wfPatientBanner').className = 'wf-patient-banner wf-unselected';
  $('wfPatientBanner').innerHTML = '<span>← اختر مريضاً من القائمة أو ابحث</span>';
  $('wfForm').style.display = 'none';
  $('wfResult').style.display = 'none';
  $('wfTests').innerHTML = '';
  $('wfTypeSuggest').style.display = 'none';
  document.querySelectorAll('.wf-patient-item').forEach(el => el.classList.remove('active'));
  $('wfSearch').value = '';
  wfLoadPatients();
}

async function wfNewPatient() {
  openModal('مريض جديد', `
    <form onsubmit="wfSaveNewPatient(event)">
      <div class="form-row">
        <div class="field"><label>الاسم الكامل *</label><input id="wfNpName" required maxlength="200" autofocus></div>
        <div class="field"><label>رقم الهاتف</label><input id="wfNpPhone" maxlength="20"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>الجنس</label>
          <select id="wfNpGender"><option value="">غير محدد</option><option value="ذكر">ذكر</option><option value="أنثى">أنثى</option></select>
        </div>
        <div class="field"><label>تاريخ الميلاد</label><input id="wfNpDob" type="date"></div>
      </div>
      <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="wfNpBtn">إضافة</button>
      </div>
    </form>
  `);
}

async function wfSaveNewPatient(e) {
  e.preventDefault();
  const btn = $('wfNpBtn');
  btn.disabled = true;
  try {
    const p = await api('/patients', { method: 'POST', body: JSON.stringify({
      full_name: $('wfNpName').value.trim(),
      phone: $('wfNpPhone').value.trim() || undefined,
      gender: $('wfNpGender').value || undefined,
      birth_date: $('wfNpDob').value || undefined,
    })});
    closeModal();
    _wfPatientCache.unshift(p);
    toast('تم إضافة المريض');
    wfSelectPatient(parseInt(p.id));
    wfLoadPatients();
  } catch (err) { toast(err.message, 'error'); }
  btn.disabled = false;
}

async function wfLoadRecent() {
  const el = $('wfRecent');
  if (!el) return;
  try {
    const d = await api('/results/orders?limit=15&skip=0');
    const orders = d.orders || [];
    if (!orders.length) { el.innerHTML = '<div class="wf-empty">لا توجد طلبات</div>'; return; }
    el.innerHTML = orders.map(o => {
      const firstToken = (o.results || [])[0]?.result_token;
      return `
        <div class="wf-recent-item" onclick="viewOrder(${parseInt(o.id)})">
          <div class="wf-rec-name">${esc(o.patient_name || '-')}</div>
          <div class="wf-rec-meta">${(o.results || []).length} تحليل · ${formatDate(o.created_at)}</div>
          ${firstToken ? `<a href="/r/${escAttr(firstToken)}" target="_blank" rel="noopener" class="wf-rec-link" onclick="event.stopPropagation()">📤</a>` : ''}
        </div>
      `;
    }).join('');
  } catch { el.innerHTML = '<div class="wf-empty">تعذر التحميل</div>'; }
}

// ---- Router ----
const routes = { dashboard: pageDashboard, workflow: pageWorkflow, patients: pagePatients, orders: pageOrders, samples: pageSamples, 'test-types': pageTestTypes, employees: pageEmployees, qc: pageQC, alerts: pageAlerts, lab: pageLab, profile: pageProfile, compliance: pageCompliance, admin: pageAdmin, tiers: pageTiers };

function navigate(page) {
  if (!routes[page]) page = 'dashboard';
  G.page = page;
  window.location.hash = page;
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.page === page));
  $('page').innerHTML = '<div class="spinner"></div>';
  $('sidebar').classList.remove('open');
  routes[page]();
}

// ---- Arabic Greeting ----
function arabicGreeting() {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return 'صباح الخير';
  if (h >= 12 && h < 17) return 'مساء الخير';
  if (h >= 17 && h < 21) return 'مساء النور';
  return 'أهلاً';
}

// ---- DASHBOARD PAGE ----
async function pageDashboard() {
  try {
    const [d, alertData] = await Promise.all([
      api('/dashboard'),
      api('/alerts?hours=24').catch(() => ({ total_alerts: 0, alerts: [] }))
    ]);
    const greetText = d.greeting || (arabicGreeting() + '، ' + (G.user?.name || 'مستخدم'));
    const criticalAlerts = alertData.total_alerts || 0;
    const pts = parseInt(d.patients) || 0;
    const ords = parseInt(d.orders) || 0;
    const tests = parseInt(d.tests) || 0;
    const critical = parseInt(d.critical) || 0;
    const todayPts = d.today?.patients || 0;
    const todayOrds = d.today?.orders || 0;
    const todayTests = d.today?.tests || 0;
    const weekPts = d.this_week?.patients || 0;
    const weekOrds = d.this_week?.orders || 0;
    // Completion rate (non-critical / total results)
    const compRate = tests > 0 ? Math.round(((tests - critical) / tests) * 100) : 100;

    $('page').innerHTML = `
      <!-- Greeting -->
      <div class="greeting-banner" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
        <div>
          <h2>${esc(greetText)}</h2>
          <p>نظرة شاملة على نشاط المختبر — ${new Date().toLocaleDateString('ar-IQ',{weekday:'long',year:'numeric',month:'long',day:'numeric'})}</p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-outline btn-sm" onclick="navigate('workflow')" style="border-color:#818cf840;color:#c7d2fe">⚡ إدخال سريع</button>
          <button class="btn btn-outline btn-sm" onclick="navigate('patients')" style="border-color:#818cf840;color:#c7d2fe">+ مريض جديد</button>
        </div>
      </div>

      ${criticalAlerts > 0 ? `
      <div class="alert-banner" onclick="navigate('alerts')" style="cursor:pointer">
        <div class="alert-icon">!</div>
        <div>
          <strong>${criticalAlerts} تنبيه حرج</strong> — نتائج تحتاج مراجعة فورية خلال آخر 24 ساعة
          <div style="font-size:.78rem;margin-top:3px;opacity:.8">اضغط هنا للمراجعة الآن</div>
        </div>
      </div>` : `
      <div class="info-box success" style="margin-bottom:16px">
        <span style="font-size:1.1rem">✓</span>
        <span>جميع النتائج ضمن النطاق الطبيعي — لا تنبيهات حرجة خلال آخر 24 ساعة</span>
      </div>`}

      <!-- Main Stats -->
      <div class="stats-grid" style="grid-template-columns:repeat(auto-fit,minmax(180px,1fr))">
        <div class="stat-card blue" style="cursor:pointer" onclick="navigate('patients')">
          <div class="stat-label">إجمالي المرضى</div>
          <div class="stat-value">${pts.toLocaleString('ar')}</div>
          <div class="stat-sub">+${todayPts} اليوم</div>
        </div>
        <div class="stat-card green" style="cursor:pointer" onclick="navigate('orders')">
          <div class="stat-label">الطلبات</div>
          <div class="stat-value">${ords.toLocaleString('ar')}</div>
          <div class="stat-sub">+${todayOrds} اليوم</div>
        </div>
        <div class="stat-card cyan">
          <div class="stat-label">التحاليل المُنجزة</div>
          <div class="stat-value">${tests.toLocaleString('ar')}</div>
          <div class="stat-sub">نتيجة مسجلة</div>
        </div>
        <div class="stat-card ${critical > 0 ? 'red' : 'green'}" style="cursor:pointer" onclick="navigate('alerts')">
          <div class="stat-label">نتائج حرجة</div>
          <div class="stat-value">${critical}</div>
          <div class="stat-sub">${critical > 0 ? 'تحتاج مراجعة' : 'لا شيء يستدعي القلق'}</div>
        </div>
      </div>

      <!-- Today + Week + Completion -->
      <div class="grid-2" style="margin-bottom:16px">
        <div class="card">
          <div class="card-title">إحصائيات اليوم والأسبوع</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px">
            <div style="background:#0f172a;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:1.4rem;font-weight:800;color:var(--primary)">${todayPts}</div>
              <div style="font-size:.72rem;color:var(--text-muted)">مرضى اليوم</div>
            </div>
            <div style="background:#0f172a;border-radius:8px;padding:12px;text-align:center">
              <div style="font-size:1.4rem;font-weight:800;color:var(--success)">${todayTests}</div>
              <div style="font-size:.72rem;color:var(--text-muted)">تحاليل اليوم</div>
            </div>
          </div>
          <div class="section-title">هذا الأسبوع</div>
          <div class="progress-wrap">
            <div class="progress-label"><span>المرضى</span><span>${weekPts}</span></div>
            <div class="progress-bar"><div class="progress-fill blue" style="width:${Math.min(100,weekPts > 0 ? 60 : 0)}%"></div></div>
          </div>
          <div class="progress-wrap">
            <div class="progress-label"><span>الطلبات</span><span>${weekOrds}</span></div>
            <div class="progress-bar"><div class="progress-fill green" style="width:${Math.min(100,weekOrds > 0 ? 70 : 0)}%"></div></div>
          </div>
          <div class="progress-wrap">
            <div class="progress-label"><span>التحاليل</span><span>${todayTests}</span></div>
            <div class="progress-bar"><div class="progress-fill cyan" style="width:${Math.min(100,todayTests > 0 ? 55 : 0)}%"></div></div>
          </div>
        </div>

        <div class="card">
          <div class="card-title">معدل جودة النتائج</div>
          <div class="ring-chart">
            <div class="ring" style="--pct:${compRate * 3.6}deg;background:conic-gradient(var(--success) ${compRate * 3.6}deg, var(--border) 0deg)">
              <span class="ring-val" style="font-size:.8rem;color:var(--success)">${compRate}%</span>
            </div>
            <div class="ring-legend">
              <div class="ring-item"><div class="ring-dot" style="background:var(--success)"></div>ضمن المعدل الطبيعي: ${tests - critical}</div>
              <div class="ring-item"><div class="ring-dot" style="background:var(--danger)"></div>غير طبيعية: ${critical}</div>
              <div class="ring-item"><div class="ring-dot" style="background:var(--border)"></div>الإجمالي: ${tests}</div>
            </div>
          </div>
          <div class="section-title" style="margin-top:14px">وصول سريع</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px">
            <button class="btn btn-outline btn-sm" onclick="navigate('workflow')">⚡ إدخال سريع</button>
            <button class="btn btn-outline btn-sm" onclick="navigate('samples')">🧪 العينات</button>
            <button class="btn btn-outline btn-sm" onclick="navigate('qc')">📊 مراقبة الجودة</button>
            ${G.user?.role === 'master_admin' || G.user?.role === 'admin' ? `<button class="btn btn-outline btn-sm" onclick="navigate('employees')">👥 الموظفون</button>` : ''}
          </div>
        </div>
      </div>

      <!-- Recent Orders + Abnormal -->
      <div class="grid-2">
        <div class="card">
          <div class="flex-between" style="margin-bottom:12px">
            <div class="card-title" style="margin:0">آخر الطلبات</div>
            <button class="btn btn-outline btn-sm" onclick="navigate('orders')">عرض الكل</button>
          </div>
          ${(d.recent_orders || []).length ? d.recent_orders.slice(0, 8).map(o => `
            <div class="activity-item" style="cursor:pointer" onclick="viewOrder(${parseInt(o.id || 0)})">
              <div class="activity-dot" style="background:${o.status === 'completed' ? 'var(--success)' : 'var(--primary)'}"></div>
              <div style="flex:1">
                <div class="activity-text">${esc(o.patient_name || 'مريض')}</div>
                <div class="activity-time">${parseInt(o.test_count) || 0} تحليل · ${timeAgo(o.date || o.created_at)}</div>
              </div>
              ${o.has_critical ? '<span style="color:var(--danger);font-size:.7rem;font-weight:700">⚠ حرج</span>' : ''}
            </div>
          `).join('') : '<div class="empty" style="padding:24px"><p>لا توجد طلبات حديثة</p><button class="btn btn-outline btn-sm" style="margin-top:10px" onclick="navigate(\'workflow\')">ابدأ بإضافة طلب</button></div>'}
        </div>

        <div class="card">
          <div class="flex-between" style="margin-bottom:12px">
            <div class="card-title" style="margin:0">نتائج تحتاج مراجعة</div>
            ${criticalAlerts > 0 ? `<button class="btn btn-outline btn-sm" onclick="navigate('alerts')">عرض التنبيهات</button>` : ''}
          </div>
          ${(d.abnormal_results || []).length ? `
            <div class="table-wrap">
              <table>
                <thead><tr><th>المريض</th><th>التحليل</th><th>القيمة</th><th>الحالة</th></tr></thead>
                <tbody>${d.abnormal_results.slice(0, 6).map(r => `<tr class="${r.flag === 'critical' ? 'critical-row' : ''}">
                  <td>${esc(r.patient_name || '-')}</td>
                  <td style="font-size:.8rem">${esc(r.test_name)}</td>
                  <td><strong>${esc(r.value)}</strong> <span style="font-size:.76rem;color:var(--text-muted)">${esc(r.unit || '')}</span></td>
                  <td>${resultFlag(r.value, r.normal_range_low, r.normal_range_high)}</td>
                </tr>`).join('')}</tbody>
              </table>
            </div>
          ` : '<div class="empty" style="padding:24px"><p style="color:var(--success)">✓ جميع النتائج طبيعية</p></div>'}
        </div>
      </div>
    `;
  } catch (e) {
    $('page').innerHTML = `
      <div class="empty" style="padding:60px 20px">
        <div style="font-size:2.5rem;margin-bottom:12px">⚡</div>
        <p style="margin-bottom:8px">تعذر تحميل البيانات</p>
        <p style="font-size:.8rem;color:var(--text-muted);margin-bottom:16px">${esc(e.message)}</p>
        <button class="btn btn-outline" onclick="pageDashboard()">إعادة المحاولة</button>
      </div>`;
  }
}

// ---- PATIENTS PAGE ----
let patientPage = 0;
async function pagePatients() {
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>المرضى</h2><p>إدارة سجلات المرضى</p></div>
        <button class="btn btn-primary" onclick="openAddPatient()">+ إضافة مريض</button>
      </div>
    </div>
    <div class="search-bar">
      <input class="search-input" id="patientSearch" placeholder="بحث بالاسم أو رقم الهاتف..." oninput="searchPatients()">
    </div>
    <div class="card"><div id="patientsTable"><div class="spinner"></div></div></div>
  `;
  loadPatients();
}

async function loadPatients(search = '') {
  try {
    const reqId = ++_lastSearchId;
    const d = await api(`/patients?search=${encodeURIComponent(search)}&skip=${patientPage * PAGE_SIZE}&limit=${PAGE_SIZE}`);
    if (reqId !== _lastSearchId) return; // stale response, discard
    const el = $('patientsTable');
    if (!d.patients.length) { el.innerHTML = '<div class="empty"><p>لا يوجد مرضى</p></div>'; return; }
    el.innerHTML = `
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>الاسم</th><th>الهاتف</th><th>الجنس</th><th>تاريخ الميلاد</th><th>المعرف الصحي</th><th>التسجيل</th><th></th></tr></thead>
        <tbody>${d.patients.map((p, i) => `<tr>
          <td>${patientPage * PAGE_SIZE + i + 1}</td>
          <td><strong>${esc(p.full_name)}</strong></td>
          <td dir="ltr">${esc(p.phone || '-')}</td>
          <td>${p.gender === 'male' ? 'ذكر' : p.gender === 'female' ? 'أنثى' : '-'}</td>
          <td>${formatDate(p.birth_date)}</td>
          <td><code style="color:var(--accent)">${esc(p.health_id || '-')}</code></td>
          <td>${formatDate(p.created_at)}</td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="viewPatient(${parseInt(p.id)})">عرض</button>
            <button class="btn btn-outline btn-sm" onclick="newOrderForPatient(${parseInt(p.id)})">+ طلب</button>
          </td>
        </tr>`).join('')}</tbody>
      </table></div>
      <div class="pagination">
        <span class="pagination-info">صفحة ${patientPage + 1} ${d.total ? '- إجمالي ' + d.total : ''}</span>
        <button ${patientPage === 0 ? 'disabled' : ''} onclick="patientPage=Math.max(0,patientPage-1);loadPatients()">السابق</button>
        <button ${d.patients.length < PAGE_SIZE ? 'disabled' : ''} onclick="patientPage++;loadPatients()">التالي</button>
      </div>
    `;
  } catch (e) { $('patientsTable').innerHTML = `<div class="empty"><p>تعذر تحميل البيانات</p></div>`; }
}

let searchTimer;
let _lastSearchId = 0;
function searchPatients() {
  clearTimeout(searchTimer);
  const el = $('patientSearch');
  if (!el) return;
  searchTimer = setTimeout(() => { patientPage = 0; loadPatients(el.value); }, 300);
}

function openAddPatient() {
  openModal('إضافة مريض جديد', `
    <form onsubmit="savePatient(event)">
      <div class="form-row">
        <div class="field"><label>الاسم الكامل *</label><input id="pName" required maxlength="200"></div>
        <div class="field"><label>رقم الهاتف *</label><input id="pPhone" required dir="ltr" placeholder="07xxxxxxxxx" maxlength="15"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>الجنس</label><select id="pGender"><option value="">-</option><option value="male">ذكر</option><option value="female">أنثى</option></select></div>
        <div class="field"><label>تاريخ الميلاد</label><input type="date" id="pDob" max="${new Date().toISOString().split('T')[0]}"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>البريد الإلكتروني</label><input type="email" id="pEmail" maxlength="100"></div>
        <div class="field"><label>الرقم الوطني</label><input id="pNatId" dir="ltr" maxlength="20" pattern="[0-9]*" placeholder="رقم مكون من 12 خانة"></div>
      </div>
      <div id="phoneError" style="color:var(--danger);font-size:.8rem;display:none;margin-bottom:8px">صيغة الهاتف غير صحيحة (مثال: 07xxxxxxxxx)</div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="savePatientBtn">حفظ</button>
      </div>
    </form>
  `);
}

async function savePatient(e) {
  e.preventDefault();
  const phone = $('pPhone').value.trim();
  if (!isValidPhone(phone)) {
    $('phoneError').style.display = 'block';
    return;
  }
  $('phoneError').style.display = 'none';

  const btn = $('savePatientBtn');
  btn.disabled = true;
  try {
    const body = {
      full_name: $('pName').value.trim(), phone: phone,
      gender: $('pGender').value || undefined, birth_date: $('pDob').value || undefined,
      email: $('pEmail').value || undefined, national_id: $('pNatId').value || undefined
    };
    const result = await api('/patients', { method: 'POST', body: JSON.stringify(body) });
    if (result.duplicate) {
      toast('تحذير: يوجد مريض مشابه - تحقق من البيانات', 'error');
      btn.disabled = false;
      return;
    }
    closeModal(); toast('تم إضافة المريض بنجاح'); loadPatients();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

async function viewPatient(id) {
  try {
    const p = await api(`/patients/${id}`);
    const ehr = await api(`/ehr/patient/${id}/summary`).catch(() => null);
    openModal('ملف المريض', `
      <div class="kpi-row" style="margin-bottom:16px">
        <div class="kpi"><span class="kpi-val">${esc(p.full_name)}</span><span class="kpi-label">الاسم</span></div>
        <div class="kpi"><span class="kpi-val" dir="ltr">${esc(p.phone || '-')}</span><span class="kpi-label">الهاتف</span></div>
        <div class="kpi"><span class="kpi-val">${esc(p.health_id || '-')}</span><span class="kpi-label">المعرف الصحي</span></div>
      </div>
      ${ehr && ehr.summary ? `
        <div class="card-title">آخر النتائج</div>
        <div class="table-wrap"><table>
          <thead><tr><th>التحليل</th><th>القيمة</th><th>التاريخ</th></tr></thead>
          <tbody>${ehr.summary.map(s => `<tr><td>${esc(s.test_name)}</td><td><strong>${esc(s.value)}</strong> ${esc(s.unit || '')}</td><td>${formatDate(s.date)}</td></tr>`).join('')}</tbody>
        </table></div>
      ` : '<div class="empty"><p>لا توجد نتائج سابقة</p></div>'}
      <div style="margin-top:16px">
        <button class="btn btn-primary btn-sm" onclick="closeModal();newOrderForPatient(${parseInt(p.id)})">+ طلب تحليل جديد</button>
      </div>
    `);
  } catch (e) { toast(e.message, 'error'); }
}

// ---- ORDERS & RESULTS PAGE ----
let orderPage = 0;
let _ordSearch = '';
let _ordSearchTimer2;

async function pageOrders() {
  orderPage = 0; _ordSearch = '';
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>الطلبات والنتائج</h2><p>إدارة طلبات التحاليل ونتائجها</p></div>
        <button class="btn btn-primary" onclick="openNewOrder()">+ طلب جديد</button>
      </div>
    </div>
    <div class="search-bar">
      <input class="search-input" id="ordSearch" placeholder="بحث باسم المريض أو الطبيب..." oninput="ordDoSearch()">
    </div>
    <div class="card"><div id="ordersTable"><div class="spinner"></div></div></div>
  `;
  loadOrders();
}

function ordDoSearch() {
  clearTimeout(_ordSearchTimer2);
  _ordSearchTimer2 = setTimeout(() => {
    const el = $('ordSearch');
    if (!el) return;
    _ordSearch = el.value.trim();
    orderPage = 0;
    loadOrders();
  }, 300);
}

async function loadOrders() {
  try {
    let url = `/results/orders?skip=${orderPage * PAGE_SIZE}&limit=${PAGE_SIZE}`;
    if (_ordSearch) url += `&search=${encodeURIComponent(_ordSearch)}`;
    const d = await api(url);
    const el = $('ordersTable');
    const orders = d.orders || [];
    if (!orders.length) {
      el.innerHTML = '<div class="empty"><p>لا توجد طلبات</p>' +
        (_ordSearch ? `<button class="btn btn-outline" style="margin-top:12px" onclick="$('ordSearch').value='';_ordSearch='';loadOrders()">مسح البحث</button>` : '') +
        '</div>';
      return;
    }
    el.innerHTML = `
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>المريض</th><th>الطبيب</th><th>التحاليل</th><th>الحالة</th><th>التاريخ</th><th></th></tr></thead>
        <tbody>${orders.map((o, i) => {
          // Backend is authoritative for is_critical (calculated from result flags)
          const isCritical = o.is_critical;
          const isLocked = o.locked;
          const sLabel = o.status === 'validated' ? 'معتمد ✓' : o.status === 'cancelled' ? 'ملغى' : o.status === 'completed' ? 'مكتمل' : 'معلق';
          const sCls = o.status === 'validated' ? 'badge-green' : o.status === 'cancelled' ? 'badge-red' : o.status === 'completed' ? 'badge-blue' : 'badge-gray';
          return `<tr class="${isCritical ? 'critical-row' : ''}">
            <td>${orderPage * PAGE_SIZE + i + 1}</td>
            <td><strong>${esc(o.patient_name || '-')}</strong>${isCritical ? ' <span style="color:var(--danger);font-size:.75rem">●</span>' : ''}</td>
            <td>${esc(o.doctor_name || '-')}</td>
            <td><span class="badge badge-blue">${(o.results || []).length} تحليل</span>${isCritical ? ' <span class="badge badge-red">حرج</span>' : ''}</td>
            <td><span class="badge ${sCls}">${sLabel}</span></td>
            <td>${formatDate(o.created_at)}</td>
            <td style="white-space:nowrap;display:flex;gap:4px">
              <button class="btn btn-outline btn-sm" onclick="viewOrder(${parseInt(o.id)})">تفاصيل</button>
              ${o.status === 'completed' && !isLocked ? `<button class="btn btn-sm" style="background:var(--success);color:#fff" onclick="validateOrder(${parseInt(o.id)})">اعتماد</button>` : ''}
              ${o.status === 'pending' ? `<button class="btn btn-outline btn-sm" style="color:var(--danger)" onclick="cancelOrder(${parseInt(o.id)})">إلغاء</button>` : ''}
            </td>
          </tr>`;
        }).join('')}</tbody>
      </table></div>
      <div class="pagination">
        <span class="pagination-info">صفحة ${orderPage + 1}${d.total ? ' - إجمالي ' + d.total : ''}</span>
        <button ${orderPage === 0 ? 'disabled' : ''} onclick="orderPage=Math.max(0,orderPage-1);loadOrders()">السابق</button>
        <button ${orders.length < PAGE_SIZE ? 'disabled' : ''} onclick="orderPage++;loadOrders()">التالي</button>
      </div>
    `;
  } catch (e) { $('ordersTable').innerHTML = `<div class="empty"><p>تعذر تحميل البيانات</p></div>`; }
}

async function viewOrder(id) {
  try {
    const o = await api(`/results/orders/${id}`);
    const firstToken = (o.results || []).find(r => r.result_token)?.result_token;
    const waText = firstToken
      ? `نتائج تحاليل ${o.patient_name} جاهزة 🔬\n${location.origin}/r/${firstToken}`
      : '';
    const role = G.user?.role;
    const canValidate = (role === 'admin' || role === 'master_admin' || role === 'doctor') && o.status === 'completed' && !o.locked;

    openModal(`طلب #${parseInt(o.id)} — ${esc(o.patient_name || '')}`, `
      <div class="kpi-row" style="margin-bottom:16px">
        <div class="kpi"><span class="kpi-val">${esc(o.patient_name || '-')}</span><span class="kpi-label">المريض</span></div>
        <div class="kpi"><span class="kpi-val">${esc(o.doctor_name || '-')}</span><span class="kpi-label">الطبيب</span></div>
        <div class="kpi"><span class="kpi-val">${formatDate(o.created_at)}</span><span class="kpi-label">التاريخ</span></div>
        <div class="kpi">
          <span class="kpi-val">
            ${o.status === 'validated' ? '<span class="badge badge-green">معتمد ✓</span>' :
              o.status === 'cancelled' ? '<span class="badge badge-red">ملغى</span>' :
              o.status === 'completed' ? '<span class="badge badge-blue">مكتمل</span>' :
              '<span class="badge badge-gray">معلق</span>'}
            ${o.is_critical ? '<span class="badge badge-red" style="margin-right:4px">حرج</span>' : ''}
          </span>
          <span class="kpi-label">الحالة${o.locked ? ' 🔒' : ''}</span>
        </div>
      </div>
      ${o.validated_at ? `<div style="font-size:.8rem;color:var(--text-muted);margin-bottom:12px">تم الاعتماد: ${formatDate(o.validated_at)}</div>` : ''}
      <div class="table-wrap"><table>
        <thead><tr><th>التحليل</th><th>القيمة</th><th>الوحدة</th><th>المدى الطبيعي</th><th>الحالة</th></tr></thead>
        <tbody>${(o.results || []).map(r => `<tr class="${r.flag === 'critical' || r.flag === 'H' || r.flag === 'L' ? 'critical-row' : ''}">
          <td>${esc(r.test_name)}</td>
          <td><strong>${esc(r.value ?? r.value_text ?? '-')}</strong></td>
          <td>${esc(r.unit || '')}</td>
          <td style="direction:ltr;text-align:right">${esc(r.normal_range_low ?? '?')} – ${esc(r.normal_range_high ?? '?')}</td>
          <td>${resultFlag(r.value, r.normal_range_low, r.normal_range_high)}</td>
        </tr>`).join('')}</tbody>
      </table></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px">
        ${firstToken ? `
          <a href="/r/${escAttr(firstToken)}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">🔗 عرض النتائج</a>
          <a href="https://wa.me/?text=${encodeURIComponent(waText)}" target="_blank" rel="noopener" class="btn btn-wa btn-sm">📤 واتساب</a>
          <button class="btn btn-outline btn-sm" onclick="navigator.clipboard.writeText('${location.origin}/r/${escAttr(firstToken)}').then(()=>toast('تم نسخ الرابط'))">نسخ الرابط</button>
        ` : ''}
        <button class="btn btn-outline btn-sm" onclick="window.print()">🖨️ طباعة</button>
        ${canValidate ? `<button class="btn btn-sm" style="background:var(--success);color:#fff" onclick="validateOrder(${parseInt(o.id)})">✓ اعتماد وقفل</button>` : ''}
      </div>
    `);
  } catch (e) { toast(e.message, 'error'); }
}

async function validateOrder(id) {
  const role = G.user?.role;
  if (role !== 'admin' && role !== 'master_admin' && role !== 'doctor') {
    toast('فقط المدراء والأطباء يمكنهم اعتماد الطلبات', 'error');
    return;
  }
  confirmAction('اعتماد وقفل الطلب', 'بعد الاعتماد لا يمكن تعديل النتائج. هل أنت متأكد؟', async () => {
    try {
      await api(`/results/orders/${id}/validate`, { method: 'POST' });
      toast('تم اعتماد وقفل الطلب بنجاح');
      closeModal();
      loadOrders();
    } catch (e) { toast(e.message, 'error'); }
  });
}

async function cancelOrder(id) {
  confirmAction('إلغاء الطلب', 'هل أنت متأكد من إلغاء هذا الطلب؟', async () => {
    try {
      await api(`/results/orders/${id}/cancel`, { method: 'POST' });
      toast('تم إلغاء الطلب');
      loadOrders();
    } catch (e) { toast(e.message, 'error'); }
  });
}

let _ordSelectedPatient = null;

function openNewOrder() {
  _ordSelectedPatient = null;
  openModal('طلب تحليل جديد', `
    <form onsubmit="submitOrder(event)">
      <!-- Patient Search -->
      <div class="field" style="margin-bottom:10px">
        <label>المريض *</label>
        <div class="search-with-results">
          <input id="ordPatientSearch" class="search-input" placeholder="ابحث بالاسم أو الهاتف..."
            autocomplete="off" oninput="searchOrderPatient(this.value)">
          <div id="ordPatientDropdown" class="search-dropdown" style="display:none"></div>
        </div>
        <input type="hidden" id="ordPatientId">
        <div id="ordPatientBadge" style="margin-top:6px;font-size:.82rem;color:var(--text-muted)">لم يتم اختيار مريض</div>
      </div>

      <div class="form-row">
        <div class="field"><label>اسم الطبيب</label><input id="ordDoctor" maxlength="200" placeholder="د. أحمد..."></div>
        <div class="field"><label>ملاحظات</label><input id="ordNotes" maxlength="300" placeholder="اختياري"></div>
      </div>

      <div class="flex-between" style="margin:14px 0 8px">
        <div class="card-title" style="margin:0;font-size:.83rem">التحاليل</div>
        <button type="button" class="btn btn-outline btn-sm" onclick="addTestRow()">+ إضافة تحليل</button>
      </div>
      <div id="orderTests"></div>

      <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="submitOrderBtn">💾 حفظ الطلب</button>
      </div>
    </form>
  `);
  addTestRow();
}

let _ordSearchTimer;
async function searchOrderPatient(q) {
  clearTimeout(_ordSearchTimer);
  const dd = $('ordPatientDropdown');
  if (!q || q.length < 2) { dd.style.display = 'none'; return; }
  _ordSearchTimer = setTimeout(async () => {
    try {
      const d = await api(`/patients?search=${encodeURIComponent(q)}&limit=8`);
      const pts = d.patients || d;
      if (!pts.length) { dd.innerHTML = '<div class="sd-item" style="color:var(--text-muted)">لا توجد نتائج</div>'; dd.style.display = 'block'; return; }
      dd.innerHTML = pts.map(p => `
        <div class="sd-item" onclick="selectOrderPatient(${parseInt(p.id)},'${escAttr(p.full_name)}','${escAttr(p.phone||'')}')">
          <strong>${esc(p.full_name)}</strong>
          <span style="color:var(--text-muted);font-size:.78rem;margin-right:6px" dir="ltr">${esc(p.phone||'-')}</span>
        </div>
      `).join('');
      dd.style.display = 'block';
    } catch { dd.style.display = 'none'; }
  }, 300);
}

function selectOrderPatient(id, name, phone) {
  _ordSelectedPatient = id;
  $('ordPatientId').value = id;
  $('ordPatientSearch').value = name;
  $('ordPatientDropdown').style.display = 'none';
  $('ordPatientBadge').innerHTML = `<span style="color:var(--success)">✓ ${esc(name)}</span> <span dir="ltr" style="color:var(--text-muted)">${esc(phone)}</span>`;
}

function newOrderForPatient(id) {
  openNewOrder();
  // Pre-fill patient id — name will just show as "تم الاختيار"
  _ordSelectedPatient = id;
  $('ordPatientId').value = id;
  $('ordPatientBadge').innerHTML = `<span style="color:var(--success)">✓ مريض #${id}</span>`;
  $('ordPatientSearch').value = 'مريض #' + id;
}

let _ttCache = null;
async function getOrderTestTypes() {
  if (_ttCache) return _ttCache;
  try { _ttCache = await api('/test-types'); return _ttCache || []; }
  catch { return []; }
}

function addTestRow() {
  const wrap = $('orderTests');
  const idx = wrap.querySelectorAll('.order-test-row').length;
  const div = document.createElement('div');
  div.className = 'order-test-row';
  div.style.cssText = 'background:var(--bg-input);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:8px;position:relative';
  div.innerHTML = `
    <button type="button" onclick="this.parentElement.remove()" style="position:absolute;top:6px;left:8px;background:none;border:none;color:var(--danger);cursor:pointer;font-size:1rem">×</button>
    <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr;gap:8px;flex-wrap:wrap">
      <div class="field" style="margin:0">
        <label style="font-size:.75rem">اسم التحليل *</label>
        <input class="t-name" required maxlength="100" placeholder="Glucose..." autocomplete="off"
          oninput="suggestTestType(this,${idx})">
        <div class="tt-suggest" style="display:none;position:absolute;z-index:50;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;max-height:150px;overflow-y:auto;min-width:200px"></div>
      </div>
      <div class="field" style="margin:0"><label style="font-size:.75rem">القيمة *</label><input class="t-val" required placeholder="5.2" oninput="updateOrderFlag(this)"></div>
      <div class="field" style="margin:0"><label style="font-size:.75rem">الوحدة</label><input class="t-unit" class="t-unit" maxlength="20" placeholder="mg/dL"></div>
      <div class="field" style="margin:0"><label style="font-size:.75rem">أدنى</label><input class="t-low" type="number" step="any" oninput="updateOrderFlag(this)"></div>
      <div class="field" style="margin:0"><label style="font-size:.75rem">أعلى</label><input class="t-high" type="number" step="any" oninput="updateOrderFlag(this)"></div>
    </div>
    <div class="t-flag" style="font-size:.75rem;margin-top:4px;font-weight:700"></div>
  `;
  wrap.appendChild(div);
  div.querySelector('.t-name').focus();
}

function updateOrderFlag(input) {
  const row = input.closest('.order-test-row');
  const val = parseFloat(row.querySelector('.t-val').value);
  const low = parseFloat(row.querySelector('.t-low').value);
  const high = parseFloat(row.querySelector('.t-high').value);
  const flag = row.querySelector('.t-flag');
  if (isNaN(val) || isNaN(low) || isNaN(high)) { flag.textContent = ''; return; }
  if (val < low) flag.innerHTML = '<span style="color:var(--warning)">▼ منخفض</span>';
  else if (val > high) flag.innerHTML = '<span style="color:var(--danger)">▲ مرتفع</span>';
  else flag.innerHTML = '<span style="color:var(--success)">✓ طبيعي</span>';
}

async function suggestTestType(input, idx) {
  const q = input.value.toLowerCase();
  const types = await getOrderTestTypes();
  const matches = types.filter(t => t.name && t.name.toLowerCase().includes(q)).slice(0, 5);
  const sug = input.nextElementSibling;
  if (!sug || !matches.length || !q) { if(sug) sug.style.display='none'; return; }
  sug.innerHTML = matches.map(t => `
    <div style="padding:7px 10px;cursor:pointer;font-size:.82rem;border-bottom:1px solid var(--border)"
      onclick="fillTestType(this,${JSON.stringify(escAttr(t.name||''))},${JSON.stringify(t.unit||'')},${t.normal_range_low||'null'},${t.normal_range_high||'null'})">
      ${esc(t.name)} ${t.unit ? `<span style="color:var(--text-muted)">${esc(t.unit)}</span>` : ''}
    </div>
  `).join('');
  sug.style.display = 'block';
}

function fillTestType(el, name, unit, low, high) {
  const row = el.closest('.order-test-row');
  row.querySelector('.t-name').value = name;
  row.querySelector('.t-unit').value = unit || '';
  if (low !== null) row.querySelector('.t-low').value = low;
  if (high !== null) row.querySelector('.t-high').value = high;
  el.parentElement.style.display = 'none';
}

async function submitOrder(e) {
  e.preventDefault();
  if (!$('ordPatientId').value) { toast('الرجاء اختيار مريض من قائمة البحث', 'error'); return; }
  const btn = $('submitOrderBtn');
  btn.disabled = true; btn.textContent = 'جاري الحفظ...';
  try {
    const rows = $('orderTests').querySelectorAll('.order-test-row');
    const results = Array.from(rows).map(r => ({
      test_name: r.querySelector('.t-name').value.trim(),
      value: r.querySelector('.t-val').value.trim(),
      unit: r.querySelector('.t-unit').value.trim() || undefined,
      normal_range_low: r.querySelector('.t-low').value !== '' ? parseFloat(r.querySelector('.t-low').value) : undefined,
      normal_range_high: r.querySelector('.t-high').value !== '' ? parseFloat(r.querySelector('.t-high').value) : undefined
    })).filter(r => r.test_name);
    if (!results.length) { toast('أضف تحليلاً واحداً على الأقل', 'error'); btn.disabled=false; btn.textContent='💾 حفظ الطلب'; return; }
    await api('/results/orders', { method: 'POST', body: JSON.stringify({
      patient_id: parseInt($('ordPatientId').value),
      doctor_name: $('ordDoctor').value.trim() || undefined,
      notes: $('ordNotes').value.trim() || undefined,
      results
    })});
    closeModal(); toast('✓ تم حفظ الطلب بنجاح'); loadOrders();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false; btn.textContent = '💾 حفظ الطلب';
}

// ---- SAMPLES PAGE ----
async function pageSamples() {
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>العينات</h2><p>تتبع العينات بالباركود</p></div>
      </div>
    </div>
    <div class="toolbar" role="radiogroup" aria-label="تصفية العينات">
      <div class="filter-chip active" onclick="filterSamples(this,'')">الكل</div>
      <div class="filter-chip" onclick="filterSamples(this,'collected')">تم الجمع</div>
      <div class="filter-chip" onclick="filterSamples(this,'received')">مستلمة</div>
      <div class="filter-chip" onclick="filterSamples(this,'processing')">قيد المعالجة</div>
      <div class="filter-chip" onclick="filterSamples(this,'analyzed')">مكتملة</div>
      <div class="filter-chip" onclick="filterSamples(this,'rejected')">مرفوضة</div>
    </div>
    <div class="card"><div id="samplesTable"><div class="spinner"></div></div></div>
  `;
  loadSamples();
}

let currentSampleFilter = '';
async function loadSamples(status) {
  if (status !== undefined) currentSampleFilter = status;
  try {
    const d = await api(`/samples?status=${currentSampleFilter}&limit=${PAGE_SIZE}`);
    const el = $('samplesTable');
    const samples = d.samples || d;
    if (!samples || !samples.length) { el.innerHTML = '<div class="empty"><p>لا توجد عينات</p></div>'; return; }
    el.innerHTML = `
      <div class="table-wrap"><table>
        <thead><tr><th>الباركود</th><th>النوع</th><th>الحالة</th><th>الموقع</th><th>ملاحظات</th><th></th></tr></thead>
        <tbody>${samples.map(s => `<tr>
          <td><code style="color:var(--accent)">${esc(s.barcode)}</code></td>
          <td>${esc(s.sample_type)}</td>
          <td>${statusBadge(s.status)}</td>
          <td>${esc(s.storage_location || '-')}</td>
          <td>${esc(s.notes || '-')}</td>
          <td>
            <select class="btn btn-outline btn-sm" onchange="updateSampleStatus('${escAttr(s.barcode)}',this.value)" style="padding:4px 8px">
              <option value="">تحديث</option>
              <option value="received">استلام</option>
              <option value="processing">معالجة</option>
              <option value="analyzed">اكتمال</option>
              <option value="rejected">رفض</option>
            </select>
          </td>
        </tr>`).join('')}</tbody>
      </table></div>
    `;
  } catch (e) { $('samplesTable').innerHTML = `<div class="empty"><p>تعذر تحميل البيانات</p></div>`; }
}

function filterSamples(el, status) {
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadSamples(status);
}

async function updateSampleStatus(barcode, status) {
  if (!status) return;
  if (status === 'rejected') {
    confirmAction('رفض العينة', 'هل أنت متأكد من رفض هذه العينة؟', function(reason) {
      doUpdateSample(barcode, status, reason);
    }, true, 'سبب الرفض');
    return;
  }
  doUpdateSample(barcode, status);
}

async function doUpdateSample(barcode, status, rejectionReason) {
  try {
    let body = { status };
    if (rejectionReason) body.rejection_reason = rejectionReason;
    await api(`/samples/${encodeURIComponent(barcode)}`, { method: 'PUT', body: JSON.stringify(body) });
    toast('تم تحديث حالة العينة'); loadSamples();
  } catch (e) { toast(e.message, 'error'); }
}

// ---- LAB PAGE ----
async function pageLab() {
  $('page').innerHTML = `
    <div class="page-header"><h2>المختبر</h2><p>إعدادات ومعلومات المختبر</p></div>
    <div id="labStats" style="margin-bottom:16px"></div>
    <div class="card" id="labForm"><div class="spinner"></div></div>
  `;

  // Load lab info and stats in parallel
  const [lab, dash] = await Promise.all([
    api('/labs/me').catch(() => null),
    api('/dashboard').catch(() => null),
  ]);

  if (!lab) {
    $('labForm').innerHTML = '<div class="empty"><p>تعذر تحميل بيانات المختبر</p></div>';
    return;
  }

  // Stats section
  if (dash) {
    const s = dash.stats || dash;
    $('labStats').innerHTML = `
      <div class="stats-grid">
        <div class="stat-card blue">
          <div class="stat-label">إجمالي المرضى</div>
          <div class="stat-value">${parseInt(s.total_patients) || 0}</div>
          <div class="stat-sub">مريض مسجل</div>
        </div>
        <div class="stat-card green">
          <div class="stat-label">الطلبات (30 يوم)</div>
          <div class="stat-value">${parseInt(s.orders_this_month || s.total_orders) || 0}</div>
          <div class="stat-sub">طلب تحليل</div>
        </div>
        <div class="stat-card yellow">
          <div class="stat-label">اليوم</div>
          <div class="stat-value">${parseInt(s.orders_today || s.today_orders) || 0}</div>
          <div class="stat-sub">طلب اليوم</div>
        </div>
        <div class="stat-card ${lab.is_active ? 'green' : 'red'}">
          <div class="stat-label">حالة المختبر</div>
          <div class="stat-value" style="font-size:1.3rem">${lab.is_active ? 'نشط ✓' : 'معطل ✗'}</div>
          <div class="stat-sub">${esc(lab.city || '')}</div>
        </div>
      </div>
    `;
  }

  $('labForm').innerHTML = `
    <div class="card-title">معلومات المختبر</div>
    <form onsubmit="saveLab(event)" style="margin-top:12px">
      <div class="form-row">
        <div class="field"><label>اسم المختبر</label><input id="labNameF" value="${escAttr(lab.name || '')}" maxlength="200"></div>
        <div class="field"><label>المدينة</label><input id="labCity" value="${escAttr(lab.city || '')}" maxlength="100"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>العنوان</label><input id="labAddress" value="${escAttr(lab.address || '')}" maxlength="300"></div>
        <div class="field"><label>الهاتف</label><input id="labPhone" value="${escAttr(lab.phone || '')}" dir="ltr" maxlength="20"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>رقم الترخيص</label><input value="${escAttr(lab.license_number || '-')}" disabled></div>
        <div class="field"><label>الحالة</label><input value="${lab.is_active ? 'نشط' : 'معطل'}" disabled style="color:${lab.is_active ? 'var(--success)' : 'var(--danger)'}"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px">
        <button type="submit" class="btn btn-primary" id="saveLabBtn">حفظ التعديلات</button>
        <button type="button" class="btn btn-outline" onclick="pageLab()">↻ تحديث</button>
      </div>
    </form>
  `;
}

async function saveLab(e) {
  e.preventDefault();
  const btn = $('saveLabBtn');
  btn.disabled = true;
  try {
    await api('/labs/me', { method: 'PUT', body: JSON.stringify({
      name: $('labNameF').value, city: $('labCity').value,
      address: $('labAddress').value, phone: $('labPhone').value
    })});
    toast('تم حفظ بيانات المختبر');
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

// ---- ADMIN PAGE ----
async function pageAdmin() {
  if (G.user?.role !== 'master_admin') {
    $('page').innerHTML = '<div class="empty"><p>ليس لديك صلاحية الوصول لهذه الصفحة</p></div>';
    return;
  }
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>إدارة المنصة</h2><p>لوحة تحكم المدير العام - صلاحيات كاملة</p></div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-outline" onclick="openCreateLab()">+ إضافة مختبر</button>
          <button class="btn btn-primary" onclick="openCreateAdminUser()">+ إضافة مستخدم</button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div id="adminStats"><div class="spinner"></div></div>

    <!-- Tabs -->
    <div style="display:flex;gap:0;background:#0f172a;border-radius:10px;padding:4px;margin-top:16px;width:fit-content">
      <div class="tab active" id="tabLabs" onclick="adminTab('labs')" style="padding:8px 20px;border-radius:8px;cursor:pointer;font-size:.9rem;color:#e2e8f0;background:#1e293b">المختبرات</div>
      <div class="tab" id="tabUsers" onclick="adminTab('users')" style="padding:8px 20px;border-radius:8px;cursor:pointer;font-size:.9rem;color:#64748b">المستخدمون</div>
      <div class="tab" id="tabAudit" onclick="adminTab('audit')" style="padding:8px 20px;border-radius:8px;cursor:pointer;font-size:.9rem;color:#64748b">سجل الأحداث</div>
    </div>

    <!-- Tab content -->
    <div id="adminTabContent" style="margin-top:16px"><div class="spinner"></div></div>
  `;
  loadAdminStats();
  loadAdminLabs();
}

async function loadAdminStats() {
  try {
    const stats = await api('/admin/stats');
    $('adminStats').innerHTML = `
      <div class="stats-grid">
        <div class="stat-card blue"><div class="stat-label">المختبرات</div><div class="stat-value">${parseInt(stats.total_labs) || 0}</div><div class="stat-sub">إجمالي المختبرات</div></div>
        <div class="stat-card green"><div class="stat-label">المستخدمون</div><div class="stat-value">${parseInt(stats.total_users) || 0}</div><div class="stat-sub">جميع الأدوار</div></div>
        <div class="stat-card cyan"><div class="stat-label">المرضى</div><div class="stat-value">${parseInt(stats.total_patients) || 0}</div><div class="stat-sub">سجلات طبية</div></div>
        <div class="stat-card yellow"><div class="stat-label">النتائج</div><div class="stat-value">${parseInt(stats.total_results) || 0}</div><div class="stat-sub">نتيجة تحليل</div></div>
      </div>
    `;
  } catch { $('adminStats').innerHTML = ''; }
}

let _adminTab = 'labs';
function adminTab(tab) {
  _adminTab = tab;
  ['labs','users','audit'].forEach(t => {
    const el = $('tab' + t.charAt(0).toUpperCase() + t.slice(1));
    if (el) { el.style.background = t === tab ? '#1e293b' : ''; el.style.color = t === tab ? '#e2e8f0' : '#64748b'; }
  });
  if (tab === 'labs') loadAdminLabs();
  else if (tab === 'users') loadAdminUsers();
  else if (tab === 'audit') loadAdminAudit();
}

async function loadAdminLabs() {
  const el = $('adminTabContent');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const d = await api('/admin/labs?limit=100');
    const labs = d.labs || d;
    if (!labs.length) { el.innerHTML = '<div class="card"><div class="empty"><p>لا توجد مختبرات مسجلة</p><button class="btn btn-primary" style="margin-top:12px" onclick="openCreateLab()">إضافة أول مختبر</button></div></div>'; return; }
    el.innerHTML = `
      <div class="card">
        <div class="card-title">المختبرات المسجلة (${labs.length})</div>
        <div class="table-wrap"><table>
          <thead><tr><th>#</th><th>المختبر</th><th>المدينة</th><th>المستخدمون</th><th>المرضى</th><th>الحالة</th><th></th></tr></thead>
          <tbody>${labs.map((l, i) => `<tr>
            <td>${i+1}</td>
            <td><strong>${esc(l.name)}</strong>${l.license_number ? `<div style="font-size:.78rem;color:var(--text-muted)">${esc(l.license_number)}</div>` : ''}</td>
            <td>${esc(l.city || '-')}</td>
            <td style="text-align:center">${parseInt(l.user_count) || 0}</td>
            <td style="text-align:center">${parseInt(l.patient_count) || 0}</td>
            <td>${l.is_active ? '<span class="badge badge-green">نشط</span>' : '<span class="badge badge-red">معطل</span>'}</td>
            <td><button class="btn btn-outline btn-sm" onclick="toggleLab(${parseInt(l.id)},${l.is_active})">${l.is_active ? 'تعطيل' : 'تفعيل'}</button></td>
          </tr>`).join('')}</tbody>
        </table></div>
      </div>
    `;
  } catch (e) { el.innerHTML = `<div class="empty"><p>تعذر تحميل المختبرات: ${esc(e.message)}</p></div>`; }
}

async function loadAdminUsers() {
  const el = $('adminTabContent');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const d = await api('/admin/users?limit=100');
    const users = d.users || d;
    const roleLabel = { master_admin: 'مدير عام', ministry_admin: 'وزارة', province_admin: 'محافظة', admin: 'مدير مختبر', doctor: 'طبيب', staff: 'موظف', technician: 'تقني', citizen: 'مواطن' };
    const roleColor = { master_admin: 'badge-blue', ministry_admin: 'badge-blue', province_admin: 'badge-cyan', admin: 'badge-green', doctor: 'badge-cyan', staff: 'badge-gray', technician: 'badge-gray', citizen: 'badge-gray' };
    el.innerHTML = `
      <div class="card">
        <div class="card-title">جميع المستخدمين (${users.length || 0})</div>
        <div class="table-wrap"><table>
          <thead><tr><th>#</th><th>الاسم</th><th>البريد</th><th>الدور</th><th>المختبر</th><th>الحالة</th><th></th></tr></thead>
          <tbody>${(users || []).map((u, i) => `<tr>
            <td>${i+1}</td>
            <td><strong>${esc(u.name || '-')}</strong></td>
            <td dir="ltr" style="font-size:.82rem;color:var(--text-dim)">${esc(u.email || '-')}</td>
            <td><span class="badge ${roleColor[u.role] || 'badge-gray'}">${esc(roleLabel[u.role] || u.role)}</span></td>
            <td style="font-size:.82rem">${esc(u.lab_name || (u.lab_id ? '#'+u.lab_id : 'منصة'))}</td>
            <td>${u.is_active !== false ? '<span class="badge badge-green">نشط</span>' : '<span class="badge badge-red">معطل</span>'}</td>
            <td>${u.role !== 'master_admin' ? `<button class="btn btn-outline btn-sm" onclick="toggleAdminUser(${parseInt(u.id)},${u.is_active !== false})">${u.is_active !== false ? 'تعطيل' : 'تفعيل'}</button>` : '<span style="font-size:.78rem;color:var(--text-muted)">محمي</span>'}</td>
          </tr>`).join('')}</tbody>
        </table></div>
      </div>
    `;
  } catch (e) { el.innerHTML = `<div class="empty"><p>تعذر تحميل المستخدمين: ${esc(e.message)}</p></div>`; }
}

async function loadAdminAudit() {
  const el = $('adminTabContent');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const d = await api('/admin/audit-logs?limit=50');
    const logs = d.logs || d;
    if (!logs.length) { el.innerHTML = '<div class="card"><div class="empty"><p>لا توجد أحداث مسجلة بعد</p></div></div>'; return; }
    el.innerHTML = `
      <div class="card">
        <div class="card-title">سجل الأحداث (آخر 50)</div>
        <div class="table-wrap"><table>
          <thead><tr><th>الحدث</th><th>المستخدم</th><th>النوع</th><th>IP</th><th>التاريخ</th></tr></thead>
          <tbody>${logs.map(l => `<tr>
            <td><strong>${esc(l.action || '-')}</strong></td>
            <td style="font-size:.82rem">${esc(l.user_id ? '#'+l.user_id : '-')}</td>
            <td style="font-size:.82rem">${esc(l.resource_type || '-')}</td>
            <td dir="ltr" style="font-size:.78rem;color:var(--text-muted)">${esc(l.ip_address || '-')}</td>
            <td style="font-size:.8rem">${formatDate(l.created_at)}</td>
          </tr>`).join('')}</tbody>
        </table></div>
      </div>
    `;
  } catch (e) { el.innerHTML = `<div class="empty"><p>تعذر تحميل السجل: ${esc(e.message)}</p></div>`; }
}

async function toggleLab(id, isActive) {
  confirmAction(
    isActive ? 'تعطيل المختبر' : 'تفعيل المختبر',
    isActive ? 'هل أنت متأكد؟ سيؤثر هذا على جميع مستخدمي المختبر ويمنعهم من تسجيل الدخول.' : 'هل تريد إعادة تفعيل هذا المختبر؟',
    async function() {
      try {
        await api(`/admin/labs/${id}/toggle`, { method: 'PUT' });
        toast(isActive ? 'تم تعطيل المختبر' : 'تم تفعيل المختبر');
        loadAdminLabs();
      } catch (e) { toast(e.message, 'error'); }
    }
  );
}

async function toggleAdminUser(id, isActive) {
  confirmAction(
    isActive ? 'تعطيل المستخدم' : 'تفعيل المستخدم',
    isActive ? 'هل أنت متأكد من تعطيل هذا المستخدم؟' : 'هل تريد إعادة تفعيل هذا المستخدم؟',
    async () => {
      try {
        await api(`/admin/users/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: !isActive }) });
        toast(isActive ? 'تم تعطيل المستخدم' : 'تم تفعيل المستخدم');
        loadAdminUsers();
      } catch (e) { toast(e.message, 'error'); }
    }
  );
}

function openCreateLab() {
  openModal('إضافة مختبر جديد', `
    <form onsubmit="saveNewLab(event)">
      <div class="form-row">
        <div class="field"><label>اسم المختبر *</label><input id="nlName" required maxlength="200" placeholder="مختبر الأمل"></div>
        <div class="field"><label>المدينة *</label><input id="nlCity" required maxlength="100" placeholder="بغداد"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>العنوان</label><input id="nlAddress" maxlength="300" placeholder="الشارع والحي"></div>
        <div class="field"><label>رقم الهاتف</label><input id="nlPhone" type="tel" placeholder="07xxxxxxxxx"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>رقم الترخيص</label><input id="nlLicense" maxlength="100" placeholder="LAB-2025-001"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="saveLabBtn">إنشاء المختبر</button>
      </div>
    </form>
  `);
}

async function saveNewLab(e) {
  e.preventDefault();
  const btn = $('saveLabBtn'); btn.disabled = true;
  try {
    await api('/admin/labs', { method: 'POST', body: JSON.stringify({
      name: $('nlName').value.trim(),
      city: $('nlCity').value.trim(),
      address: $('nlAddress').value.trim() || undefined,
      phone: $('nlPhone').value.trim() || undefined,
      license_number: $('nlLicense').value.trim() || undefined,
    }) });
    closeModal(); toast('تم إنشاء المختبر بنجاح'); loadAdminStats(); loadAdminLabs();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

function openCreateAdminUser() {
  openModal('إضافة مستخدم جديد', `
    <form onsubmit="saveAdminUser(event)">
      <div class="form-row">
        <div class="field"><label>الاسم الكامل *</label><input id="auName" required maxlength="200" placeholder="الاسم الكامل"></div>
        <div class="field"><label>البريد الإلكتروني *</label><input id="auEmail" type="email" required maxlength="100" placeholder="user@lab.com"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>كلمة المرور *</label><input id="auPw" type="password" required minlength="8" placeholder="8 أحرف+أرقام على الأقل"></div>
        <div class="field"><label>الدور الوظيفي *</label>
          <select id="auRole">
            <option value="admin">مدير مختبر</option>
            <option value="staff">موظف</option>
            <option value="technician">تقني مختبر</option>
            <option value="doctor">طبيب</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <div class="field" style="grid-column:span 2"><label>معرّف المختبر (اختياري - رقم ID)</label><input id="auLabId" type="number" min="1" placeholder="مثال: 1 أو 2"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="saveAUBtn">إنشاء المستخدم</button>
      </div>
    </form>
  `);
}

async function saveAdminUser(e) {
  e.preventDefault();
  const pw = $('auPw').value;
  if (pw.length < 8) { toast('كلمة المرور يجب أن تكون 8 أحرف على الأقل', 'error'); return; }
  const btn = $('saveAUBtn'); btn.disabled = true;
  try {
    await api('/admin/users', { method: 'POST', body: JSON.stringify({
      name: $('auName').value.trim(),
      email: $('auEmail').value.trim(),
      password: pw,
      role: $('auRole').value,
      lab_id: $('auLabId').value ? parseInt($('auLabId').value) : undefined,
    }) });
    closeModal(); toast('تم إنشاء المستخدم بنجاح'); loadAdminStats(); loadAdminUsers();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

// ---- QC PAGE ----
async function pageQC() {
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>مراقبة الجودة</h2><p>Westgard Rules - تتبع جودة الأجهزة والتحاليل</p></div>
        <button class="btn btn-primary" onclick="openAddQC()">+ إضافة QC</button>
      </div>
    </div>
    <div id="qcSummary"><div class="spinner"></div></div>
    <div class="card" style="margin-top:16px"><div id="qcTable"><div class="spinner"></div></div></div>
  `;
  loadQCSummary();
  loadQCResults();
}

async function loadQCSummary() {
  try {
    const d = await api('/qc/summary?days=7');
    const el = $('qcSummary');
    if (!d.tests || !d.tests.length) {
      el.innerHTML = '<div class="card"><div class="empty"><p>لا توجد بيانات مراقبة جودة بعد</p></div></div>';
      return;
    }
    el.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card ${d.overall_pass_rate >= 95 ? 'green' : d.overall_pass_rate >= 80 ? 'yellow' : 'red'}">
          <div class="stat-label">نسبة النجاح الكلية</div>
          <div class="stat-value">${d.overall_pass_rate}%</div>
          <div class="stat-sub">آخر 7 أيام</div>
        </div>
        ${d.tests.slice(0, 3).map(t => `
          <div class="stat-card ${t.status === 'good' ? 'green' : t.status === 'review' ? 'yellow' : 'red'}">
            <div class="stat-label">${esc(t.test_code)}</div>
            <div class="stat-value">${t.pass_rate}%</div>
            <div class="stat-sub">${t.total} فحص - ${t.issues} مشكلة</div>
          </div>
        `).join('')}
      </div>
    `;
  } catch (e) { $('qcSummary').innerHTML = ''; }
}

async function loadQCResults() {
  try {
    const d = await api('/qc?days=7&limit=30');
    const el = $('qcTable');
    if (!d.qc_results || !d.qc_results.length) {
      el.innerHTML = '<div class="empty"><p>لا توجد نتائج QC</p></div>';
      return;
    }
    el.innerHTML = `
      <div class="card-title">آخر نتائج مراقبة الجودة</div>
      <div class="table-wrap"><table>
        <thead><tr><th>التحليل</th><th>المستوى</th><th>المتوقع</th><th>المقاس</th><th>الحالة</th><th>المخالفة</th><th>التاريخ</th></tr></thead>
        <tbody>${d.qc_results.map(q => `<tr class="${q.status === 'fail' ? 'critical-row' : q.status === 'warning' ? 'warning-row' : ''}">
          <td>${esc(q.test_code)}</td>
          <td>${esc(q.level)}</td>
          <td>${esc(q.expected_value)}</td>
          <td><strong>${esc(q.measured_value)}</strong></td>
          <td><span class="badge badge-${q.status === 'pass' ? 'green' : q.status === 'warning' ? 'yellow' : 'red'}">${q.status === 'pass' ? 'ناجح' : q.status === 'warning' ? 'تحذير' : 'فشل'}</span></td>
          <td>${esc(q.violation || '-')}</td>
          <td>${formatDate(q.created_at)}</td>
        </tr>`).join('')}</tbody>
      </table></div>
    `;
  } catch (e) { $('qcTable').innerHTML = '<div class="empty"><p>تعذر تحميل البيانات</p></div>'; }
}

function openAddQC() {
  openModal('إضافة فحص مراقبة جودة', `
    <form onsubmit="saveQC(event)">
      <div class="form-row">
        <div class="field"><label>رمز التحليل *</label><input id="qcTest" required placeholder="مثال: glucose"></div>
        <div class="field"><label>المستوى *</label><select id="qcLevel" required><option value="low">Low</option><option value="normal" selected>Normal</option><option value="high">High</option></select></div>
      </div>
      <div class="form-row">
        <div class="field"><label>القيمة المتوقعة *</label><input id="qcExpected" type="number" step="any" required></div>
        <div class="field"><label>القيمة المقاسة *</label><input id="qcMeasured" type="number" step="any" required></div>
      </div>
      <div class="form-row">
        <div class="field"><label>الانحراف المعياري (SD)</label><input id="qcSD" type="number" step="any"></div>
        <div class="field"><label>الوحدة</label><input id="qcUnit"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>اسم الجهاز</label><input id="qcInstrument"></div>
        <div class="field"><label>رقم اللوت</label><input id="qcLot"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="saveQCBtn">حفظ</button>
      </div>
    </form>
  `);
}

async function saveQC(e) {
  e.preventDefault();
  const btn = $('saveQCBtn');
  btn.disabled = true;
  try {
    const body = {
      test_code: $('qcTest').value, level: $('qcLevel').value,
      expected_value: parseFloat($('qcExpected').value), measured_value: parseFloat($('qcMeasured').value),
      sd: $('qcSD').value ? parseFloat($('qcSD').value) : undefined,
      unit: $('qcUnit').value || undefined,
      instrument_name: $('qcInstrument').value || undefined,
      lot_number: $('qcLot').value || undefined,
    };
    const result = await api('/qc', { method: 'POST', body: JSON.stringify(body) });
    closeModal();
    const statusMsg = result.evaluation?.status === 'pass' ? 'ناجح' : result.evaluation?.status === 'warning' ? 'تحذير!' : 'فشل!';
    toast(`تم تسجيل QC - ${statusMsg}`, result.evaluation?.status === 'pass' ? 'success' : 'error');
    loadQCSummary(); loadQCResults();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

// ---- ALERTS PAGE ----
async function pageAlerts() {
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>التنبيهات الحرجة</h2><p>نتائج تحتاج مراجعة فورية</p></div>
      </div>
    </div>
    <div class="toolbar">
      <div class="filter-chip active" onclick="filterAlerts(this, 24)">24 ساعة</div>
      <div class="filter-chip" onclick="filterAlerts(this, 48)">48 ساعة</div>
      <div class="filter-chip" onclick="filterAlerts(this, 168)">أسبوع</div>
    </div>
    <div id="alertStats"></div>
    <div class="card" style="margin-top:16px"><div id="alertsTable"><div class="spinner"></div></div></div>
  `;
  loadAlerts(24);
  loadAlertStats();
}

let _alertHours = 24;
async function loadAlerts(hours) {
  if (hours !== undefined) _alertHours = hours;
  try {
    const d = await api(`/alerts?hours=${_alertHours}`);
    const el = $('alertsTable');
    if (!d.alerts || !d.alerts.length) {
      el.innerHTML = '<div class="empty"><p>لا توجد تنبيهات حرجة - ممتاز!</p></div>';
      return;
    }
    el.innerHTML = `
      <div class="card-title">${d.total_alerts} تنبيه حرج</div>
      <div class="table-wrap"><table>
        <thead><tr><th>المريض</th><th>الهاتف</th><th>التحليل</th><th>القيمة</th><th>المدى الطبيعي</th><th>الطبيب</th><th>التاريخ</th></tr></thead>
        <tbody>${d.alerts.map(a => `<tr class="critical-row">
          <td><strong>${esc(a.patient_name)}</strong></td>
          <td dir="ltr">${esc(a.patient_phone || '-')}</td>
          <td>${esc(a.test_name)}</td>
          <td><span class="val-critical"><strong>${esc(a.value)}</strong></span> ${esc(a.unit || '')}</td>
          <td>${esc(a.normal_range)}</td>
          <td>${esc(a.doctor_name || '-')}</td>
          <td>${timeAgo(a.created_at)}</td>
        </tr>`).join('')}</tbody>
      </table></div>
    `;
  } catch (e) { $('alertsTable').innerHTML = '<div class="empty"><p>تعذر تحميل التنبيهات</p></div>'; }
}

async function loadAlertStats() {
  try {
    const d = await api('/alerts/stats');
    $('alertStats').innerHTML = `
      <div class="stats-grid">
        <div class="stat-card red"><div class="stat-label">آخر 24 ساعة</div><div class="stat-value">${d.last_24h || 0}</div></div>
        <div class="stat-card yellow"><div class="stat-label">آخر 7 أيام</div><div class="stat-value">${d.last_7d || 0}</div></div>
        <div class="stat-card blue"><div class="stat-label">آخر 30 يوم</div><div class="stat-value">${d.last_30d || 0}</div></div>
      </div>
    `;
  } catch (e) { $('alertStats').innerHTML = ''; }
}

function filterAlerts(el, hours) {
  document.querySelectorAll('.toolbar .filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadAlerts(hours);
}

// ---- COMPLIANCE & SECURITY PAGE ----
async function pageCompliance() {
  // Belt-and-suspenders: frontend role check (backend enforces this too via 403)
  if (!G.user || (G.user.role !== 'admin' && G.user.role !== 'master_admin')) {
    $('page').innerHTML = '<div class="empty"><p>ليس لديك صلاحية الوصول لهذه الصفحة</p></div>';
    return;
  }
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div>
          <h2>الأمن والامتثال</h2>
          <p>لوحة تدقيق ISO 27001 — حالة النظام الأمنية الشاملة</p>
        </div>
        <button class="btn btn-outline btn-sm" onclick="pageCompliance()">↻ تحديث</button>
      </div>
    </div>
    <div id="complianceBody"><div class="spinner"></div></div>
  `;
  try {
    const [status, timeSyncData] = await Promise.all([
      api('/compliance/system-status'),
      api('/compliance/time-sync').catch(() => null)
    ]);

    const svc = status.services || {};
    const sec = status.security || {};
    const data = status.data || {};
    const checklist = status.compliance_checklist || {};
    const alerts = status.alerts || [];

    function badge(ok, passLabel = 'PASS', failLabel = 'FAIL') {
      if (ok === true || ok === 'pass') return `<span class="badge badge-green">${passLabel}</span>`;
      if (ok === false || ok === 'fail') return `<span class="badge badge-red">${failLabel}</span>`;
      return `<span class="badge badge-gray">غير معروف</span>`;
    }
    function statusDot(s) {
      const color = s === 'pass' ? 'var(--success)' : s === 'fail' ? 'var(--danger)' : 'var(--warning)';
      return `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${color};margin-left:6px"></span>`;
    }
    function checkItem(key, label) {
      const val = checklist[key] || '';
      const isPass = val.startsWith('PASS');
      const isPending = val.startsWith('PENDING');
      const color = isPass ? 'var(--success)' : isPending ? 'var(--warning)' : 'var(--text-dim)';
      const icon = isPass ? '✓' : isPending ? '⏳' : '✗';
      return `<tr>
        <td style="color:${color};font-weight:600">${icon}</td>
        <td>${label}</td>
        <td style="color:${color};font-size:.8rem">${esc(val)}</td>
      </tr>`;
    }

    $('complianceBody').innerHTML = `
      ${alerts.length ? `
      <div class="alert-banner" style="margin-bottom:16px">
        <div class="alert-icon">!</div>
        <div>
          <strong>${alerts.length} تنبيه أمني</strong><br>
          ${alerts.map(a => `<div style="font-size:.85rem;margin-top:4px">${esc(a)}</div>`).join('')}
        </div>
      </div>` : `
      <div style="background:var(--success-bg);border:1px solid var(--success);border-radius:var(--radius);padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px;color:var(--success)">
        <strong>✓</strong> جميع الأنظمة تعمل بشكل طبيعي — لا تنبيهات أمنية
      </div>`}

      <div class="stats-grid">
        <div class="stat-card ${svc.database?.status === 'pass' ? 'green' : 'red'}">
          <div class="stat-label">قاعدة البيانات</div>
          <div class="stat-value" style="font-size:1.4rem">${svc.database?.status === 'pass' ? '✓' : '✗'}</div>
          <div class="stat-sub">${svc.database?.latency_ms ? `زمن الاستجابة: ${svc.database.latency_ms} ms` : 'غير متاح'}</div>
        </div>
        <div class="stat-card ${sec.audit_chain?.status === 'pass' ? 'green' : 'red'}">
          <div class="stat-label">سلسلة التدقيق</div>
          <div class="stat-value" style="font-size:1.4rem">${sec.audit_chain?.status === 'pass' ? '✓' : '✗'}</div>
          <div class="stat-sub">${sec.audit_chain?.entries_checked || 0} سجل مُتحقق</div>
        </div>
        <div class="stat-card ${sec.audit_anchor?.status === 'pass' ? 'green' : 'yellow'}">
          <div class="stat-label">نقطة الارتساء الخارجية</div>
          <div class="stat-value" style="font-size:1.4rem">${sec.audit_anchor?.status === 'pass' ? '✓' : '⏳'}</div>
          <div class="stat-sub">${sec.audit_anchor?.total_anchors || 0} نقطة تحقق</div>
        </div>
        <div class="stat-card ${sec.time_sync?.status === 'pass' ? 'green' : sec.time_sync?.status === 'fail' ? 'red' : 'yellow'}">
          <div class="stat-label">مزامنة الوقت NTP</div>
          <div class="stat-value" style="font-size:1.4rem">${sec.time_sync?.status === 'pass' ? '✓' : '?'}</div>
          <div class="stat-sub">${timeSyncData?.ntp_status === 'synchronized' ? 'متزامن' : 'يحتاج تفعيل'}</div>
        </div>
      </div>

      <div class="grid-2" style="margin-top:16px">
        <div class="card">
          <div class="card-title">تفاصيل الأمان</div>
          <table style="width:100%;font-size:.9rem;border-collapse:collapse">
            <tbody>
              <tr style="border-bottom:1px solid var(--border)">
                <td style="padding:10px 0;color:var(--text-dim)">إجمالي سجلات التدقيق</td>
                <td style="padding:10px 0;text-align:left;font-weight:600">${data.total_audit_entries?.toLocaleString('ar') || 0}</td>
              </tr>
              <tr style="border-bottom:1px solid var(--border)">
                <td style="padding:10px 0;color:var(--text-dim)">فشل تسجيل الدخول (24 ساعة)</td>
                <td style="padding:10px 0;text-align:left;font-weight:600;color:${(data.failed_logins_24h || 0) > 10 ? 'var(--danger)' : 'var(--text)'}">${data.failed_logins_24h || 0}</td>
              </tr>
              <tr style="border-bottom:1px solid var(--border)">
                <td style="padding:10px 0;color:var(--text-dim)">سلامة سلسلة الهاش</td>
                <td style="padding:10px 0;text-align:left">${badge(sec.audit_chain?.status === 'pass', 'سليمة', 'مُخترقة')}</td>
              </tr>
              <tr style="border-bottom:1px solid var(--border)">
                <td style="padding:10px 0;color:var(--text-dim)">آخر نقطة ارتساء</td>
                <td style="padding:10px 0;text-align:left;font-size:.8rem">${sec.audit_anchor?.latest_anchor_id ? `سجل #${sec.audit_anchor.latest_anchor_id}` : 'لا توجد بعد'}</td>
              </tr>
              <tr style="border-bottom:1px solid var(--border)">
                <td style="padding:10px 0;color:var(--text-dim)">وضع البيئة</td>
                <td style="padding:10px 0;text-align:left">${badge(status.environment === 'production', 'إنتاج', 'تطوير')}</td>
              </tr>
              <tr>
                <td style="padding:10px 0;color:var(--text-dim)">إصدار المنصة</td>
                <td style="padding:10px 0;text-align:left;font-family:monospace">${esc(status.platform_version || '-')}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="card">
          <div class="card-title">قائمة الامتثال</div>
          <table style="width:100%;font-size:.9rem;border-collapse:collapse">
            <tbody>
              ${checkItem('fhir_r4', 'HL7 FHIR R4 — بيانات المختبر')}
              ${checkItem('dhis2_export', 'DHIS2 — تقارير وزارة الصحة')}
              ${checkItem('audit_immutability', 'سجل التدقيق غير قابل للتعديل')}
              ${checkItem('rbac', 'التحكم في الوصول RBAC')}
              ${checkItem('secure_cookies', 'حماية الجلسات (httpOnly Cookies)')}
              ${checkItem('docs_protected', 'حماية صفحة التوثيق /docs')}
              ${checkItem('disaster_recovery', 'اختبار الاسترجاع (ISO 27001 A.17.1)')}
              ${checkItem('cmc_registration', 'تسجيل هيئة الاتصالات CMC')}
              ${checkItem('iso_27001', 'شهادة ISO 27001')}
              ${checkItem('pentest', 'اختبار الاختراق السنوي')}
            </tbody>
          </table>
        </div>
      </div>

      ${timeSyncData ? `
      <div class="card" style="margin-top:16px;${timeSyncData.drift_warning ? 'border-color:var(--warning)' : ''}">
        <div class="card-title">حالة وقت الخادم (NTP)</div>
        ${timeSyncData.drift_warning ? `<div style="background:var(--warning-bg);border:1px solid var(--warning);border-radius:var(--radius-sm);padding:8px 12px;margin-bottom:12px;font-size:.85rem;color:var(--warning)">⚠ DRIFT DETECTED — الانحراف ${esc(timeSyncData.ntp_offset_human || '')} يتجاوز الحد المسموح (${timeSyncData.max_offset_seconds}s)</div>` : ''}
        <div class="kpi-row">
          <div class="kpi"><span class="kpi-val" style="font-size:.95rem;font-family:monospace">${esc(timeSyncData.server_time_utc?.replace('T',' ').split('.')[0] || '-')} UTC</span><span class="kpi-label">وقت الخادم الحالي</span></div>
          <div class="kpi"><span class="kpi-val" style="color:${timeSyncData.ntp_synchronized ? (timeSyncData.drift_warning ? 'var(--warning)' : 'var(--success)') : 'var(--danger)'}">${timeSyncData.ntp_synchronized ? (timeSyncData.drift_warning ? '⚠ متزامن (drift)' : '✓ متزامن') : '✗ غير متزامن'}</span><span class="kpi-label">حالة NTP</span></div>
          ${timeSyncData.ntp_offset_human ? `<div class="kpi"><span class="kpi-val" style="font-family:monospace;color:${timeSyncData.drift_warning ? 'var(--warning)' : 'var(--success)'}">${esc(timeSyncData.ntp_offset_human)}</span><span class="kpi-label">الانحراف الحالي</span></div>` : ''}
          <div class="kpi"><span class="kpi-val" style="font-size:.75rem;color:${timeSyncData.drift_warning ? 'var(--warning)' : timeSyncData.ntp_synchronized ? 'var(--success)' : 'var(--danger)'}">${esc(timeSyncData.audit_impact || '-')}</span><span class="kpi-label">أثر التدقيق</span></div>
        </div>
      </div>` : ''}

      ${(() => {
        const dr = status.disaster_recovery;
        if (!dr) return `
        <div class="card" style="margin-top:16px;border-color:var(--warning)">
          <div class="card-title">اختبار الاسترجاع (ISO 27001 A.17.1)</div>
          <div style="display:flex;align-items:center;gap:12px;padding:8px 0">
            <span style="font-size:1.4rem">⏳</span>
            <div>
              <div style="font-weight:600;color:var(--warning)">لم يتم الاختبار بعد</div>
              <div style="font-size:.85rem;color:var(--text-dim);margin-top:4px">شغّل: <code>./scripts/restore-test.sh</code> واحفظ النتيجة كدليل</div>
            </div>
          </div>
        </div>`;
        const isPass = dr.status === 'PASS';
        return `
        <div class="card" style="margin-top:16px;border-color:${isPass ? 'var(--success)' : 'var(--danger)'}">
          <div class="card-title">اختبار الاسترجاع — دليل موثّق (ISO 27001 A.17.1)</div>
          <div class="kpi-row">
            <div class="kpi"><span class="kpi-val" style="color:${isPass ? 'var(--success)' : 'var(--danger)'}">${isPass ? '✓ PASS' : '✗ FAIL'}</span><span class="kpi-label">النتيجة</span></div>
            <div class="kpi"><span class="kpi-val">${esc(dr.restore_seconds || '-')} ث</span><span class="kpi-label">وقت الاسترجاع</span></div>
            <div class="kpi"><span class="kpi-val" style="font-size:.85rem">${esc(dr.tested_ago || '-')} مضى</span><span class="kpi-label">آخر اختبار</span></div>
            <div class="kpi"><span class="kpi-val" style="font-size:.75rem;font-family:monospace">${esc(dr.backup_file || '-')}</span><span class="kpi-label">الملف المختبر</span></div>
          </div>
          <div style="font-size:.8rem;color:var(--text-muted);margin-top:4px">اختُبر بواسطة: ${esc(dr.tested_by || '-')} — ${esc(dr.tested_at_human || '-')}</div>
        </div>`;
      })()}

      <div class="card" style="margin-top:16px">
        <div class="card-title" style="margin-bottom:12px">معلومات للمراجعين الحكوميين</div>
        <div style="font-size:.85rem;color:var(--text-dim);line-height:1.8">
          <div>🔗 FHIR DiagnosticReport: <code style="color:var(--accent)">/api/compliance/fhir/diagnostic-report/{id}</code></div>
          <div>🔗 FHIR ServiceRequest: <code style="color:var(--accent)">/api/compliance/fhir/service-request/{id}</code></div>
          <div>🔗 DHIS2 تصدير: <code style="color:var(--accent)">/api/compliance/dhis2/aggregate</code></div>
          <div>🔗 سلامة سلسلة الهاش: <code style="color:var(--accent)">/api/compliance/audit-integrity</code></div>
          <div style="margin-top:8px;color:var(--text-muted)">تقرير الأمان الكامل: <code>/api/compliance/security-report</code> — متاح للمراجعين المخولين فقط</div>
        </div>
      </div>
    `;
  } catch (e) {
    $('complianceBody').innerHTML = `<div class="empty"><p>تعذر تحميل بيانات الامتثال</p><button class="btn btn-outline" style="margin-top:12px" onclick="pageCompliance()">إعادة المحاولة</button></div>`;
  }
}


// ---- TEST TYPES PAGE ----
async function pageTestTypes() {
  const canEdit = G.user?.role === 'admin' || G.user?.role === 'master_admin';
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>أنواع التحاليل</h2><p>قائمة التحاليل المعتمدة مع المدى الطبيعي</p></div>
        ${canEdit ? '<button class="btn btn-primary" onclick="openAddTestType()">+ إضافة تحليل</button>' : ''}
      </div>
    </div>
    <div class="search-bar">
      <input class="search-input" id="ttSearch" placeholder="بحث باسم التحليل أو التصنيف..." oninput="searchTestTypes()">
    </div>
    <div class="card"><div id="ttTable"><div class="spinner"></div></div></div>
  `;
  loadTestTypes();
}

async function loadTestTypes(search = '') {
  try {
    const url = '/test-types' + (search ? '?search=' + encodeURIComponent(search) : '');
    const d = await api(url);
    const el = $('ttTable');
    const types = Array.isArray(d) ? d : (d.test_types || d.items || []);
    const canEdit = G.user?.role === 'admin' || G.user?.role === 'master_admin';
    if (!types.length) {
      el.innerHTML = '<div class="empty"><p>لا توجد تحاليل مسجلة</p></div>';
      return;
    }
    const catLabel = { hematology: 'دموية', chemistry: 'كيمياء', microbiology: 'ميكروبيولوجيا', immunology: 'مناعة', urinalysis: 'بول', other: 'أخرى' };
    el.innerHTML = `
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>اسم التحليل</th><th>الوحدة</th><th>أدنى</th><th>أعلى</th><th>التصنيف</th>${canEdit ? '<th></th>' : ''}</tr></thead>
        <tbody>${types.map((t, i) => `<tr>
          <td>${i + 1}</td>
          <td><strong>${esc(t.name)}</strong></td>
          <td><code style="color:var(--accent)">${esc(t.unit || '-')}</code></td>
          <td>${t.normal_range_low != null ? esc(t.normal_range_low) : '-'}</td>
          <td>${t.normal_range_high != null ? esc(t.normal_range_high) : '-'}</td>
          <td>${t.category ? `<span class="badge badge-blue">${esc(catLabel[t.category] || t.category)}</span>` : '-'}</td>
          ${canEdit ? `<td>
            <button class="btn btn-outline btn-sm" onclick="openEditTestType(${parseInt(t.id)},'${escAttr(t.name)}','${escAttr(t.unit||'')}',${t.normal_range_low??''},'${escAttr(t.category||'')}',${t.normal_range_high??''})">تعديل</button>
            <button class="btn btn-danger btn-sm" style="margin-right:4px" onclick="deleteTestType(${parseInt(t.id)})">حذف</button>
          </td>` : ''}
        </tr>`).join('')}</tbody>
      </table></div>
      <div style="padding:12px 0;color:var(--text-muted);font-size:.8rem;text-align:center">${types.length} تحليل مسجل</div>
    `;
  } catch (e) {
    $('ttTable').innerHTML = `<div class="empty"><p>تعذر تحميل قائمة التحاليل: ${esc(e.message)}</p></div>`;
  }
}

let _ttSearchTimer;
function searchTestTypes() {
  clearTimeout(_ttSearchTimer);
  const el = $('ttSearch');
  if (!el) return;
  _ttSearchTimer = setTimeout(() => loadTestTypes(el.value), 300);
}

function openAddTestType() {
  openModal('إضافة تحليل جديد', `
    <form onsubmit="saveTestType(event)">
      <div class="form-row">
        <div class="field"><label>اسم التحليل *</label><input id="ttName" required maxlength="100" placeholder="مثال: Hemoglobin"></div>
        <div class="field"><label>الوحدة</label><input id="ttUnit" maxlength="20" placeholder="مثال: g/dL"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>أدنى حد طبيعي</label><input id="ttLow" type="number" step="any" min="0" placeholder="0.0"></div>
        <div class="field"><label>أعلى حد طبيعي</label><input id="ttHigh" type="number" step="any" min="0" placeholder="0.0"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>التصنيف</label>
          <select id="ttCat">
            <option value="">-- اختر --</option>
            <option value="hematology">دموية — Hematology</option>
            <option value="chemistry">كيمياء — Chemistry</option>
            <option value="microbiology">ميكروبيولوجيا — Microbiology</option>
            <option value="immunology">مناعة — Immunology</option>
            <option value="urinalysis">تحليل بول — Urinalysis</option>
            <option value="other">أخرى</option>
          </select>
        </div>
        <div class="field"><label>وصف (اختياري)</label><input id="ttDesc" maxlength="200"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="saveTTBtn">حفظ</button>
      </div>
    </form>
  `);
}

async function saveTestType(e) {
  e.preventDefault();
  const btn = $('saveTTBtn');
  btn.disabled = true;
  try {
    await api('/test-types', { method: 'POST', body: JSON.stringify({
      name: $('ttName').value.trim(),
      unit: $('ttUnit').value.trim() || undefined,
      normal_range_low: $('ttLow').value !== '' ? parseFloat($('ttLow').value) : undefined,
      normal_range_high: $('ttHigh').value !== '' ? parseFloat($('ttHigh').value) : undefined,
      category: $('ttCat').value || undefined,
      description: $('ttDesc').value.trim() || undefined,
    }) });
    closeModal(); toast('تم إضافة التحليل بنجاح'); loadTestTypes();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

function openEditTestType(id, name, unit, low, category, high) {
  openModal('تعديل التحليل', `
    <form onsubmit="updateTestType(event,${id})">
      <div class="form-row">
        <div class="field"><label>اسم التحليل *</label><input id="ettName" required value="${escAttr(name)}" maxlength="100"></div>
        <div class="field"><label>الوحدة</label><input id="ettUnit" value="${escAttr(unit)}" maxlength="20"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>أدنى حد طبيعي</label><input id="ettLow" type="number" step="any" value="${low !== '' ? esc(low) : ''}"></div>
        <div class="field"><label>أعلى حد طبيعي</label><input id="ettHigh" type="number" step="any" value="${high !== '' ? esc(high) : ''}"></div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="updateTTBtn">حفظ التعديل</button>
      </div>
    </form>
  `);
}

async function updateTestType(e, id) {
  e.preventDefault();
  const btn = $('updateTTBtn');
  btn.disabled = true;
  try {
    await api(`/test-types/${id}`, { method: 'PUT', body: JSON.stringify({
      name: $('ettName').value.trim(),
      unit: $('ettUnit').value.trim() || undefined,
      normal_range_low: $('ettLow').value !== '' ? parseFloat($('ettLow').value) : undefined,
      normal_range_high: $('ettHigh').value !== '' ? parseFloat($('ettHigh').value) : undefined,
    }) });
    closeModal(); toast('تم تحديث التحليل'); loadTestTypes();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

async function deleteTestType(id) {
  confirmAction('حذف التحليل', 'هل أنت متأكد من حذف هذا التحليل؟ لا يمكن التراجع.', async () => {
    try {
      await api(`/test-types/${id}`, { method: 'DELETE' });
      toast('تم حذف التحليل'); loadTestTypes();
    } catch (e) { toast(e.message, 'error'); }
  });
}

// ---- EMPLOYEES PAGE ----
async function pageEmployees() {
  if (G.user?.role !== 'admin' && G.user?.role !== 'master_admin') {
    $('page').innerHTML = '<div class="empty"><p>ليس لديك صلاحية الوصول لهذه الصفحة</p></div>';
    return;
  }
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>الموظفون</h2><p>إدارة موظفي المختبر وصلاحياتهم</p></div>
        <button class="btn btn-primary" onclick="openAddEmployee()">+ إضافة موظف</button>
      </div>
    </div>
    <div class="card"><div id="empTable"><div class="spinner"></div></div></div>
  `;
  loadEmployees();
}

async function loadEmployees() {
  try {
    const d = await api('/labs/me/employees');
    const el = $('empTable');
    const employees = Array.isArray(d) ? d : (d.employees || d.users || []);
    if (!employees.length) {
      el.innerHTML = '<div class="empty"><p>لا يوجد موظفون مسجلون في هذا المختبر</p></div>';
      return;
    }
    const roleLabel = { admin: 'مدير', staff: 'موظف', technician: 'تقني', master_admin: 'مدير عام' };
    const roleBadge = { admin: 'badge-blue', staff: 'badge-gray', technician: 'badge-blue', master_admin: 'badge-blue' };
    el.innerHTML = `
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>الاسم</th><th>البريد الإلكتروني</th><th>الدور</th><th>الحالة</th><th>تاريخ الإضافة</th><th></th></tr></thead>
        <tbody>${employees.map((emp, i) => `<tr>
          <td>${i + 1}</td>
          <td><strong>${esc(emp.name || '-')}</strong></td>
          <td dir="ltr" style="color:var(--text-dim)">${esc(emp.email || '-')}</td>
          <td><span class="badge ${roleBadge[emp.role] || 'badge-gray'}">${esc(roleLabel[emp.role] || emp.role)}</span></td>
          <td>${emp.is_active !== false ? '<span class="badge badge-green">نشط</span>' : '<span class="badge badge-red">معطل</span>'}</td>
          <td>${formatDate(emp.created_at)}</td>
          <td>
            ${emp.id !== G.user?.id ? `<button class="btn btn-outline btn-sm" onclick="toggleEmployee(${parseInt(emp.id)},${emp.is_active !== false})">${emp.is_active !== false ? 'تعطيل' : 'تفعيل'}</button>` : '<span style="color:var(--text-muted);font-size:.8rem">أنت</span>'}
          </td>
        </tr>`).join('')}</tbody>
      </table></div>
      <div style="padding:12px 0;color:var(--text-muted);font-size:.8rem;text-align:center">${employees.length} موظف مسجل</div>
    `;
  } catch (e) {
    $('empTable').innerHTML = `<div class="empty"><p>تعذر تحميل قائمة الموظفين: ${esc(e.message)}</p></div>`;
  }
}

function openAddEmployee() {
  openModal('إضافة موظف جديد', `
    <form onsubmit="saveEmployee(event)">
      <div class="form-row">
        <div class="field"><label>الاسم الكامل *</label><input id="empName" required maxlength="200" placeholder="الاسم الكامل"></div>
        <div class="field"><label>البريد الإلكتروني *</label><input id="empEmail" type="email" required maxlength="100" placeholder="employee@lab.com"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>كلمة المرور *</label><input id="empPw" type="password" required minlength="8" placeholder="8 أحرف على الأقل (أحرف وأرقام)"></div>
      </div>
      <div class="form-row">
        <div class="field"><label>الدور الوظيفي</label>
          <select id="empRole">
            <option value="staff">موظف — يدخل البيانات ويرى النتائج</option>
            <option value="technician">تقني — تشغيل الأجهزة وإدخال النتائج</option>
            <option value="admin">مدير — صلاحيات إدارية كاملة</option>
          </select>
        </div>
      </div>
      <div style="margin-top:16px;display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="saveEmpBtn">إضافة الموظف</button>
      </div>
    </form>
  `);
}

async function saveEmployee(e) {
  e.preventDefault();
  const pw = $('empPw').value;
  if (pw.length < 8 || !/[a-zA-Z]/.test(pw) || !/\d/.test(pw)) {
    toast('كلمة المرور يجب أن تكون 8 أحرف وتحتوي على أحرف وأرقام', 'error');
    return;
  }
  const btn = $('saveEmpBtn');
  btn.disabled = true;
  try {
    await api('/labs/me/employees', { method: 'POST', body: JSON.stringify({
      name: $('empName').value.trim(),
      email: $('empEmail').value.trim(),
      password: pw,
      role: $('empRole').value,
    }) });
    closeModal(); toast('تم إضافة الموظف بنجاح'); loadEmployees();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
}

async function toggleEmployee(id, isActive) {
  confirmAction(
    isActive ? 'تعطيل الموظف' : 'تفعيل الموظف',
    isActive ? 'هل أنت متأكد من تعطيل هذا الموظف؟ لن يتمكن من تسجيل الدخول.' : 'هل تريد إعادة تفعيل حساب هذا الموظف؟',
    async () => {
      try {
        await api(`/labs/me/employees/${id}`, { method: 'PUT', body: JSON.stringify({ is_active: !isActive }) });

        toast(isActive ? 'تم تعطيل الموظف' : 'تم تفعيل الموظف');
        loadEmployees();
      } catch (e) { toast(e.message, 'error'); }
    }
  );
}

// ---- PROFILE PAGE ----
async function pageProfile() {
  const u = G.user;
  const roleLabel = u?.role === 'master_admin' ? 'مدير عام' : u?.role === 'admin' ? 'مدير مختبر' : 'موظف';
  const roleColor = u?.role === 'master_admin' ? 'badge-blue' : u?.role === 'admin' ? 'badge-green' : 'badge-gray';
  $('page').innerHTML = `
    <div class="page-header"><h2>الملف الشخصي</h2><p>معلومات حسابك الشخصي</p></div>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">معلومات الحساب</div>
        <div style="display:flex;flex-direction:column;align-items:center;padding:20px 0;gap:12px">
          <div class="user-avatar" style="width:64px;height:64px;font-size:1.6rem">${esc((u?.name || 'م')[0])}</div>
          <div style="text-align:center">
            <div style="font-size:1.3rem;font-weight:700">${esc(u?.name || '-')}</div>
            <div style="font-size:.85rem;color:var(--text-muted);margin-top:4px" dir="ltr">${esc(u?.email || '-')}</div>
            <div style="margin-top:10px"><span class="badge ${roleColor}">${roleLabel}</span></div>
          </div>
        </div>
        <div style="border-top:1px solid var(--border);padding-top:16px;margin-top:8px">
          <table style="width:100%;font-size:.88rem;border-collapse:collapse">
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:10px 0;color:var(--text-muted)">المعرف</td>
              <td style="padding:10px 0;font-family:monospace;text-align:left">#${parseInt(u?.id || 0)}</td>
            </tr>
            <tr style="border-bottom:1px solid var(--border)">
              <td style="padding:10px 0;color:var(--text-muted)">رقم المختبر</td>
              <td style="padding:10px 0;font-family:monospace;text-align:left">${u?.lab_id ? '#' + parseInt(u.lab_id) : 'مدير عام'}</td>
            </tr>
            <tr>
              <td style="padding:10px 0;color:var(--text-muted)">الجلسة الحالية</td>
              <td style="padding:10px 0;font-size:.8rem;text-align:left;color:var(--success)">نشطة ✓</td>
            </tr>
          </table>
        </div>
      </div>
      <div class="card">
        <div class="card-title">تغيير كلمة المرور</div>
        <form onsubmit="changePassword(event)" style="margin-top:8px">
          <div class="field" style="margin-bottom:14px">
            <label>كلمة المرور الحالية *</label>
            <input type="password" id="cpCurrent" required autocomplete="current-password">
          </div>
          <div class="field" style="margin-bottom:14px">
            <label>كلمة المرور الجديدة *</label>
            <input type="password" id="cpNew" required minlength="8" placeholder="8 أحرف على الأقل (أحرف وأرقام)" autocomplete="new-password">
          </div>
          <div class="field" style="margin-bottom:20px">
            <label>تأكيد كلمة المرور الجديدة *</label>
            <input type="password" id="cpConfirm" required autocomplete="new-password">
          </div>
          <button type="submit" class="btn btn-primary" id="cpBtn" style="width:100%">تغيير كلمة المرور</button>
        </form>
      </div>
    </div>
  `;
}

async function changePassword(e) {
  e.preventDefault();
  const newPw = $('cpNew').value;
  const confirm = $('cpConfirm').value;
  if (newPw !== confirm) { toast('كلمات المرور الجديدة غير متطابقة', 'error'); return; }
  if (newPw.length < 8 || !/[a-zA-Z]/.test(newPw) || !/\d/.test(newPw)) {
    toast('كلمة المرور يجب أن تكون 8 أحرف وتحتوي على أحرف وأرقام', 'error');
    return;
  }
  const btn = $('cpBtn');
  btn.disabled = true;
  btn.textContent = 'جاري التغيير...';
  try {
    await api('/auth/change-password', { method: 'POST', body: JSON.stringify({
      current_password: $('cpCurrent').value,
      new_password: newPw,
    }) });
    toast('تم تغيير كلمة المرور بنجاح');
    $('cpCurrent').value = ''; $('cpNew').value = ''; $('cpConfirm').value = '';
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
  btn.textContent = 'تغيير كلمة المرور';
}

// ---- Welcome / System-Check Dialog ----
async function showWelcomeDialog() {
  // Only show once per session
  if (sessionStorage.getItem('_welcomed')) return;
  sessionStorage.setItem('_welcomed', '1');

  const u = G.user;
  const roleLabel = u.role === 'master_admin' ? 'مدير عام' : u.role === 'admin' ? 'مدير مختبر' : u.role === 'doctor' ? 'طبيب' : 'موظف';
  const greeting = arabicGreeting();

  // Fetch system health in parallel
  let health = {};
  try {
    health = await fetch('/health', { credentials: 'include' }).then(r => r.json()).catch(() => ({}));
  } catch {}

  const dbOk = health.database === 'connected';
  const sysStatus = health.status === 'healthy' ? 'سليم' : 'يحتاج فحص';
  const sysColor = health.status === 'healthy' ? '#10b981' : '#f59e0b';
  const version = health.version || '—';

  openModal(`${greeting}، ${esc(u.name || 'مستخدم')} 👋`, `
    <div style="display:flex;flex-direction:column;gap:16px">

      <!-- System Status -->
      <div style="background:#0f172a;border-radius:12px;padding:16px;border:1px solid #1e293b">
        <div style="font-size:.8rem;color:#64748b;margin-bottom:10px;font-weight:600;letter-spacing:.05em">حالة النظام</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:10px;height:10px;border-radius:50%;background:${sysColor}"></div>
            <span style="font-size:.85rem">النظام: <strong>${sysStatus}</strong></span>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:10px;height:10px;border-radius:50%;background:${dbOk ? '#10b981' : '#ef4444'}"></div>
            <span style="font-size:.85rem">قاعدة البيانات: <strong>${dbOk ? 'متصلة' : 'غير متصلة'}</strong></span>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <div style="width:10px;height:10px;border-radius:50%;background:#10b981"></div>
            <span style="font-size:.85rem">الحساب: <strong>${esc(roleLabel)}</strong></span>
          </div>
          <div style="display:flex;align-items:center;gap:8px;color:#64748b">
            <span style="font-size:.8rem">الإصدار: <strong dir="ltr">${esc(version)}</strong></span>
          </div>
        </div>
      </div>

      <!-- User Info -->
      <div style="display:flex;align-items:center;gap:14px;background:#0f172a;border-radius:12px;padding:14px;border:1px solid #1e293b">
        <div class="user-avatar" style="width:52px;height:52px;font-size:1.4rem;flex-shrink:0">${esc((u.name || 'م')[0])}</div>
        <div>
          <div style="font-size:1rem;font-weight:700">${esc(u.name || 'مستخدم')}</div>
          <div style="font-size:.82rem;color:#64748b;margin-top:2px" dir="ltr">${esc(u.email || '')}</div>
          <div style="margin-top:6px"><span class="badge badge-blue">${esc(roleLabel)}</span></div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div>
        <div style="font-size:.8rem;color:#64748b;margin-bottom:8px;font-weight:600">وصول سريع</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px">
          <button class="btn btn-outline btn-sm" onclick="closeModal();navigate('dashboard')">📊 لوحة التحكم</button>
          <button class="btn btn-outline btn-sm" onclick="closeModal();navigate('workflow')">⚡ إدخال سريع</button>
          <button class="btn btn-outline btn-sm" onclick="closeModal();navigate('patients')">👥 المرضى</button>
          <button class="btn btn-outline btn-sm" onclick="closeModal();navigate('profile')">🔑 تغيير كلمة المرور</button>
          ${u.role === 'master_admin' ? `<button class="btn btn-outline btn-sm" onclick="closeModal();navigate('admin')">⚙️ إدارة المنصة</button>` : ''}
        </div>
      </div>

      <div style="display:flex;justify-content:flex-end">
        <button class="btn btn-primary" onclick="closeModal()">ابدأ العمل →</button>
      </div>
    </div>
  `);
}

// ---- Init ----
function init() {
  if (!checkAuth()) return;

  // Set user info in sidebar
  $('userName').textContent = G.user.name || 'المستخدم';
  $('userRole').textContent = G.user.role === 'master_admin' ? 'مدير عام' : G.user.role === 'admin' ? 'مدير مختبر' : G.user.role === 'doctor' ? 'طبيب' : G.user.role === 'technician' ? 'تقني' : 'موظف';
  $('userAvatar').textContent = (G.user.name || 'م')[0];

  // Show compliance nav for admin and master_admin
  if (G.user.role === 'admin' || G.user.role === 'master_admin') $('complianceNav').style.display = '';
  // Show admin nav for master_admin
  if (G.user.role === 'master_admin') $('adminNav').style.display = '';
  // Show employees nav for admin and master_admin
  if (G.user.role === 'admin' || G.user.role === 'master_admin') $('employeesNav').style.display = '';

  // Set lab name
  if (G.user.lab_name) $('labName').textContent = G.user.lab_name;

  // Load subscription tier badge (non-blocking)
  api('/tiers/my').then(sub => {
    if (!sub) return;
    const TIER_ICONS = { starter: '🌱', growth: '🚀', enterprise: '🏢' };
    const TIER_LABELS = { starter: 'المبتدئ', growth: 'النمو', enterprise: 'المؤسسي' };
    const t = sub.tier || 'starter';
    const badge = document.getElementById('tierBadge');
    const icon = document.getElementById('tierBadgeIcon');
    const label = document.getElementById('tierBadgeLabel');
    if (badge && icon && label) {
      icon.textContent = TIER_ICONS[t] || '🌱';
      label.textContent = TIER_LABELS[t] || t;
      badge.style.display = '';
      // Hide "upgrade" arrow if already enterprise
      const upArrow = badge.querySelector('span:last-child');
      if (upArrow && t === 'enterprise') upArrow.style.display = 'none';
    }
  }).catch(() => { /* tier info not critical */ });

  // Show welcome dialog on first load of the session
  setTimeout(showWelcomeDialog, 800);

  // Route
  const page = window.location.hash.replace('#', '') || 'dashboard';
  navigate(page);
}

window.addEventListener('hashchange', () => {
  const page = window.location.hash.replace('#', '') || 'dashboard';
  navigate(page);
});

// ============================================================
// OFFLINE SYNC ENGINE
// Queue writes when offline, sync automatically when back online
// - Idempotency keys prevent duplicate submissions (server + client)
// - Queue sorted by timestamp (FIFO ordering)
// - Exponential backoff: 2^attempt seconds (max 5 retries)
// - Failed items are MARKED not deleted (no silent data loss)
// ============================================================

const OFFLINE_QUEUE_KEY = 'gula_offline_queue';
const OFFLINE_FAILED_KEY = 'gula_offline_failed';  // permanently failed — require manual action
const OFFLINE_MAX_RETRIES = 5;

function offlineEnqueue(item) {
  const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
  const idempotencyKey = item.idempotency_key || crypto.randomUUID();
  // Prevent double-enqueue of the same operation (client-side dedup)
  if (queue.some(q => q.idempotency_key === idempotencyKey)) return;
  queue.push({ ...item, ts: Date.now(), idempotency_key: idempotencyKey, retries: 0, status: 'pending' });
  // Keep sorted by timestamp (FIFO — process oldest first)
  queue.sort((a, b) => a.ts - b.ts);
  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
  _updateConnectionBadge();
}

function offlineQueueSize() {
  return JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]').length;
}

function offlineFailedCount() {
  return JSON.parse(localStorage.getItem(OFFLINE_FAILED_KEY) || '[]').length;
}

// Expose failed queue for manual review / retry from UI
function offlineGetFailed() {
  return JSON.parse(localStorage.getItem(OFFLINE_FAILED_KEY) || '[]');
}

function offlineClearFailed() {
  localStorage.removeItem(OFFLINE_FAILED_KEY);
  _updateConnectionBadge();
}

async function offlineSync() {
  if (!navigator.onLine) return;
  const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
  if (!queue.length) return;

  const stillPending = [];
  const permanentlyFailed = JSON.parse(localStorage.getItem(OFFLINE_FAILED_KEY) || '[]');
  let synced = 0;

  for (const item of queue) {
    // Skip items still in backoff window (2^retries seconds)
    const backoffMs = Math.pow(2, item.retries || 0) * 1000;
    if (item.last_attempt && Date.now() - item.last_attempt < backoffMs) {
      stillPending.push(item);
      continue;
    }
    try {
      const { type, payload, idempotency_key } = item;
      const idempotencyHeader = { 'Idempotency-Key': idempotency_key };
      if (type === 'result_patch') {
        await api(`/results/${payload.result_id}`, {
          method: 'PATCH',
          headers: idempotencyHeader,
          body: JSON.stringify(payload.data)
        });
      } else if (type === 'order_create') {
        await api('/results/order', {
          method: 'POST',
          headers: idempotencyHeader,
          body: JSON.stringify(payload)
        });
      }
      synced++;
    } catch (err) {
      // Server already processed it (idempotency) — count as success, don't retry
      if (err?.message?.includes('409') || err?.message?.includes('مكرر')) {
        synced++;
        continue;
      }
      const nextRetry = (item.retries || 0) + 1;
      if (nextRetry > OFFLINE_MAX_RETRIES) {
        // MARK as permanently failed — NEVER auto-delete, user must acknowledge
        permanentlyFailed.push({
          ...item,
          status: 'failed',
          failed_at: Date.now(),
          error: err?.message || 'Unknown error',
        });
        _showToast(`⚠️ عملية تحتاج مراجعة يدوية — انظر سجل الأخطاء`, 'error');
      } else {
        stillPending.push({ ...item, retries: nextRetry, last_attempt: Date.now() });
      }
    }
  }

  localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(stillPending));
  localStorage.setItem(OFFLINE_FAILED_KEY, JSON.stringify(permanentlyFailed));
  _updateConnectionBadge();
  if (synced > 0) {
    _showToast(`تمت مزامنة ${synced} عملية`, 'success');
  }
}

function _updateConnectionBadge() {
  const badge = document.getElementById('_connBadge');
  if (!badge) return;
  const pending = offlineQueueSize();
  const failed = offlineFailedCount();
  if (failed > 0) {
    badge.textContent = `🔴 ${failed} عملية فاشلة — مراجعة مطلوبة`;
    badge.style.background = '#7f1d1d';
    badge.style.cursor = 'pointer';
    badge.onclick = () => alert(`يوجد ${failed} عملية فاشلة تحتاج مراجعة يدوية.\nافتح Developer Console وشغّل: offlineGetFailed()`);
  } else if (!navigator.onLine) {
    badge.textContent = '🔴 بدون إنترنت' + (pending ? ` (${pending} معلق)` : '');
    badge.style.background = '#dc2626';
    badge.style.cursor = 'default';
    badge.onclick = null;
  } else if (pending > 0) {
    badge.textContent = `🟡 مزامنة... (${pending})`;
    badge.style.background = '#d97706';
    badge.style.cursor = 'default';
    badge.onclick = null;
  } else {
    badge.textContent = '🟢 متصل';
    badge.style.background = '#16a34a';
    badge.style.cursor = 'default';
    badge.onclick = null;
  }
}

function _injectConnectionBadge() {
  if (document.getElementById('_connBadge')) return;
  const badge = document.createElement('div');
  badge.id = '_connBadge';
  badge.style.cssText = 'position:fixed;bottom:12px;left:12px;padding:4px 10px;border-radius:20px;color:#fff;font-size:12px;z-index:9999;transition:background .3s';
  document.body.appendChild(badge);
  _updateConnectionBadge();
}

function _showToast(msg, type = 'info') {
  const t = document.createElement('div');
  t.textContent = msg;
  t.style.cssText = `position:fixed;bottom:48px;left:12px;padding:8px 16px;border-radius:8px;color:#fff;font-size:13px;z-index:9999;background:${type === 'success' ? '#16a34a' : '#2563eb'}`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// Auto-sync every 5 seconds + on reconnect
setInterval(offlineSync, 5000);
window.addEventListener('online', () => { _updateConnectionBadge(); offlineSync(); });
window.addEventListener('offline', _updateConnectionBadge);

// Inject badge after DOM ready
document.addEventListener('DOMContentLoaded', _injectConnectionBadge);

// ── Global Error Boundaries ─────────────────────────────────────────────────
// Catch unhandled promise rejections (e.g. network errors in async functions)
// so they never silently fail or expose stack traces to the user.
window.addEventListener('unhandledrejection', (event) => {
  event.preventDefault(); // suppress browser default "Unhandled promise rejection" console.error
  const reason = event.reason;
  // 401 → session expired: redirect to login
  if (reason && reason.status === 401) {
    if (!window.location.pathname.includes('login')) {
      _showToast('انتهت جلستك. يرجى تسجيل الدخول مجدداً.', 'info');
      setTimeout(() => { window.location.href = '/login.html'; }, 1500);
    }
    return;
  }
  // 503 → server maintenance
  if (reason && reason.status === 503) {
    _showToast('الخادم في وضع الصيانة. يرجى المحاولة بعد قليل.', 'info');
    return;
  }
  // 429 → rate limit
  if (reason && reason.status === 429) {
    _showToast('طلبات كثيرة. يرجى الانتظار لحظة.', 'info');
    return;
  }
  // Generic unhandled error (log to console, show toast in production)
  console.error('[GULA] Unhandled rejection:', reason);
  if (reason && reason.message && reason.message !== 'Failed to fetch') {
    _showToast('حدث خطأ غير متوقع. يرجى تحديث الصفحة.', 'error');
  }
});

// Catch synchronous script errors (e.g. ReferenceError in event handlers)
window.addEventListener('error', (event) => {
  if (event.filename && event.filename.includes('gula.js')) {
    console.error('[GULA] Script error:', event.message, 'at', event.lineno);
  }
});

// ---- TIERS PAGE ----
async function pageTiers() {
  $('page').innerHTML = '<div class="spinner"></div>';
  const isAdmin = G.user?.role === 'admin' || G.user?.role === 'master_admin';

  const TIER_INFO = {
    starter:    { label: 'المبتدئ',    color: '#64748b', icon: '🌱', price: 'مجاني',       maxP: 500,  maxS: 5,  maxB: 1,  maxO: 100,  ai: 0 },
    growth:     { label: 'النمو',      color: '#2563eb', icon: '🚀', price: '$49/شهر',     maxP: 2000, maxS: 20, maxB: 3,  maxO: 500,  ai: 50 },
    enterprise: { label: 'المؤسسي',   color: '#7c3aed', icon: '🏢', price: 'حسب الاتفاق', maxP: 99999,maxS: 200,maxB: 99, maxO: 9999, ai: 500 },
  };

  let sub = null, demands = [], myRequests = [];
  try {
    sub = await api('/tiers/my');
  } catch { /* not available */ }
  try { myRequests = (await api('/tiers/my/requests')) || []; } catch { /* ok */ }
  if (isAdmin && G.user?.role === 'master_admin') {
    try { demands = (await api('/admin/tiers/demands')) || []; } catch { /* ok */ }
  }

  const tierKey = sub?.tier || 'starter';
  const tierInfo = TIER_INFO[tierKey] || TIER_INFO.starter;
  const depMode = sub?.deployment_mode || 'single';
  const secLevel = sub?.security_level || 'standard';
  const DEP_LABELS = { single: 'مختبر واحد', multi_branch: 'متعدد الفروع', government: 'حكومي' };
  const SEC_LABELS = { standard: 'قياسي', high_security: 'أمان عالٍ', air_gapped: 'معزول تماماً' };

  function tierCard(key) {
    const t = TIER_INFO[key]; const isCurrent = key === tierKey;
    return `
    <div class="card" style="border:2px solid ${isCurrent ? t.color : 'var(--border)'};transition:.2s;${isCurrent?'box-shadow:0 0 0 3px '+t.color+'22':''}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
          <div style="font-size:1.8rem;margin-bottom:6px">${t.icon}</div>
          <div style="font-size:1.15rem;font-weight:700;color:${t.color}">${t.label}</div>
          <div style="font-size:.85rem;color:var(--text-muted);margin-top:2px">${t.price}</div>
        </div>
        ${isCurrent ? `<span class="badge badge-blue">الباقة الحالية</span>` : ''}
      </div>
      <ul style="margin:16px 0 0;padding-right:18px;font-size:.82rem;color:var(--text-muted);line-height:2">
        <li>حتى ${t.maxP === 99999 ? 'غير محدود' : t.maxP.toLocaleString()} مريض</li>
        <li>حتى ${t.maxS} موظف</li>
        <li>حتى ${t.maxB === 99 ? 'غير محدود' : t.maxB} فرع</li>
        <li>حتى ${t.maxO === 9999 ? 'غير محدود' : t.maxO} طلب يومياً</li>
        <li>${t.ai === 0 ? 'بدون ذكاء اصطناعي' : 'حتى ' + t.ai + ' استدعاء ذكاء/يوم'}</li>
      </ul>
      ${!isCurrent && isAdmin ? `
        <button class="btn btn-outline" style="width:100%;margin-top:14px;font-size:.82rem" onclick="requestUpgrade('${key}')">
          طلب الترقية إلى ${t.label}
        </button>` : ''}
      ${!isCurrent && !isAdmin ? `
        <button class="btn btn-outline" style="width:100%;margin-top:14px;font-size:.82rem" onclick="sendDemand('${key}')">
          أريد هذه الباقة
        </button>` : ''}
    </div>`;
  }

  const masterAdminPanel = G.user?.role === 'master_admin' && demands.length > 0 ? `
    <div class="card" style="margin-top:20px">
      <div class="card-title">طلبات الترقية (المدير العام)</div>
      <table class="table" style="font-size:.82rem">
        <thead><tr><th>المختبر</th><th>الباقة المطلوبة</th><th>الطلبات</th><th>الأولوية</th><th>إجراء</th></tr></thead>
        <tbody>
          ${demands.map(d => `
          <tr>
            <td>#${d.lab_id}</td>
            <td><span class="badge badge-blue">${TIER_INFO[d.target_tier]?.label || d.target_tier}</span></td>
            <td>${d.unique_requesters || 0}</td>
            <td>${(d.weighted_score || 0).toFixed(1)}</td>
            <td><button class="btn btn-sm btn-primary" onclick="approveUpgrade(${d.lab_id},'${d.target_tier}')">موافقة</button></td>
          </tr>`).join('')}
        </tbody>
      </table>
    </div>` : '';

  const historyRows = myRequests.map(r => {
    const st = { pending:'🟡 معلق', approved:'🟢 موافق', rejected:'🔴 مرفوض' }[r.status] || r.status;
    return `<tr>
      <td>${TIER_INFO[r.target_tier]?.label || r.target_tier}</td>
      <td>${st}</td>
      <td style="direction:ltr;text-align:right">${r.created_at ? r.created_at.slice(0,10) : '-'}</td>
      <td style="color:var(--text-muted);font-size:.78rem">${esc(r.review_note || '-')}</td>
    </tr>`;
  }).join('');

  $('page').innerHTML = `
    <div class="page-header">
      <h2>إدارة الاشتراك</h2>
      <p>عرض وإدارة باقة مختبرك</p>
    </div>

    <!-- Current status banner -->
    <div class="card" style="background:linear-gradient(135deg,${tierInfo.color}22,${tierInfo.color}11);border:1px solid ${tierInfo.color}44;margin-bottom:20px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
        <div style="display:flex;align-items:center;gap:14px">
          <div style="font-size:2.5rem">${tierInfo.icon}</div>
          <div>
            <div style="font-size:1.3rem;font-weight:700;color:${tierInfo.color}">${tierInfo.label}</div>
            <div style="font-size:.82rem;color:var(--text-muted);margin-top:2px">
              ${DEP_LABELS[depMode] || depMode} &nbsp;•&nbsp; أمان ${SEC_LABELS[secLevel] || secLevel}
            </div>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          ${sub?.expires_at ? `<span class="badge badge-yellow">تنتهي ${sub.expires_at.slice(0,10)}</span>` : '<span class="badge badge-green">نشط</span>'}
          ${sub?.trial_ends_at ? `<span class="badge badge-yellow">تجريبي حتى ${sub.trial_ends_at.slice(0,10)}</span>` : ''}
        </div>
      </div>
      ${sub ? `
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-top:16px;padding-top:16px;border-top:1px solid ${tierInfo.color}33">
        <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700">${sub.max_patients?.toLocaleString()}</div><div style="font-size:.72rem;color:var(--text-muted)">الحد الأقصى للمرضى</div></div>
        <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700">${sub.max_staff}</div><div style="font-size:.72rem;color:var(--text-muted)">الحد الأقصى للموظفين</div></div>
        <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700">${sub.max_branches}</div><div style="font-size:.72rem;color:var(--text-muted)">الفروع</div></div>
        <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700">${sub.max_orders_per_day}</div><div style="font-size:.72rem;color:var(--text-muted)">طلب يومياً</div></div>
        <div style="text-align:center"><div style="font-size:1.2rem;font-weight:700">${sub.max_ai_calls_per_day}</div><div style="font-size:.72rem;color:var(--text-muted)">ذكاء اصطناعي/يوم</div></div>
      </div>` : ''}
    </div>

    <!-- Tier cards -->
    <div class="grid-3" style="margin-bottom:20px">
      ${tierCard('starter')}
      ${tierCard('growth')}
      ${tierCard('enterprise')}
    </div>

    <!-- My upgrade requests history -->
    ${myRequests.length > 0 ? `
    <div class="card" style="margin-bottom:20px">
      <div class="card-title">طلبات الترقية السابقة</div>
      <table class="table" style="font-size:.82rem">
        <thead><tr><th>الباقة المطلوبة</th><th>الحالة</th><th>التاريخ</th><th>ملاحظة</th></tr></thead>
        <tbody>${historyRows}</tbody>
      </table>
    </div>` : ''}

    ${masterAdminPanel}
  `;

  window.requestUpgrade = async function(targetTier) {
    const reason = prompt(`سبب الترقية إلى باقة ${TIER_INFO[targetTier]?.label || targetTier} (اختياري):`) ?? '';
    try {
      await api('/tiers/upgrade', { method: 'POST', body: JSON.stringify({ target_tier: targetTier, reason }) });
      showToast('تم إرسال طلب الترقية بنجاح', 'success');
      pageTiers();
    } catch (e) { showToast('خطأ: ' + (e.message || 'فشل الطلب'), 'error'); }
  };
  window.sendDemand = async function(targetTier) {
    const reason = prompt(`أخبرنا لماذا تحتاج باقة ${TIER_INFO[targetTier]?.label || targetTier}:`) ?? '';
    try {
      await api('/tiers/upgrade-demand', { method: 'POST', body: JSON.stringify({ target_tier: targetTier, reason }) });
      showToast('تم تسجيل طلبك — سيتم مراجعته من قِبل الإدارة', 'success');
    } catch (e) { showToast('خطأ: ' + (e.message || 'فشل الطلب'), 'error'); }
  };
  window.approveUpgrade = async function(labId, targetTier) {
    if (!confirm(`تأكيد ترقية المختبر #${labId} إلى ${TIER_INFO[targetTier]?.label || targetTier}؟`)) return;
    try {
      await api(`/admin/tiers/${labId}`, { method: 'PUT', body: JSON.stringify({ tier: targetTier }) });
      showToast('تمت الترقية بنجاح', 'success');
      pageTiers();
    } catch (e) { showToast('خطأ: ' + (e.message || 'فشل الترقية'), 'error'); }
  };
}

// ── Service Worker Registration ─────────────────────────────────────────────
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then(reg => {
        // Listen for updates — notify user to refresh for new version
        reg.addEventListener('updatefound', () => {
          const newWorker = reg.installing;
          if (!newWorker) return;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              _showToast('تحديث جديد متاح. يرجى تحديث الصفحة (F5).', 'info');
            }
          });
        });
      })
      .catch(() => { /* SW registration failure is non-fatal */ });
  });
}

init();
