/* ============================================================
   GULA Platform - Core Application
   Lightweight SPA: Router, API, Pages, State
   ============================================================ */

// ---- Constants ----
const PAGE_SIZE = 50;

// ---- State ----
const G = {
  token: localStorage.getItem('token'),
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  page: null
};

// ---- API Helper ----
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (G.token) headers['Authorization'] = 'Bearer ' + G.token;
  const res = await fetch('/api' + path, { ...opts, headers });
  if (res.status === 401) { logout(); return; }
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'خطأ في الخادم');
  return data;
}

// ---- Auth ----
function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  G.token = null;
  G.user = null;
  window.location.replace('/login.html');
}

function checkAuth() {
  if (!G.token || !G.user) { window.location.href = '/login.html'; return false; }
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
function openModal(title, html) {
  clearTimeout(_modalFocusTimer);
  $('modalTitle').textContent = title;
  $('modalBody').innerHTML = html;
  $('modal').style.display = 'flex';
  const firstInput = $('modalBody').querySelector('input,select,textarea');
  if (firstInput) _modalFocusTimer = setTimeout(() => { if (document.contains(firstInput)) firstInput.focus(); }, 50);
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

// ---- Router ----
const routes = { dashboard: pageDashboard, patients: pagePatients, orders: pageOrders, samples: pageSamples, qc: pageQC, alerts: pageAlerts, lab: pageLab, admin: pageAdmin };

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

    $('page').innerHTML = `
      <div class="greeting-banner">
        <h2>${esc(greetText)}</h2>
        <p>نظرة عامة على نشاط المختبر</p>
      </div>
      ${criticalAlerts > 0 ? `
      <div class="alert-banner" onclick="navigate('alerts')">
        <div class="alert-icon">!</div>
        <div>
          <strong>${criticalAlerts} تنبيه حرج</strong> - نتائج تحتاج مراجعة فورية خلال آخر 24 ساعة
        </div>
      </div>` : ''}
      <div class="stats-grid">
        <div class="stat-card blue"><div class="stat-label">المرضى</div><div class="stat-value">${parseInt(d.patients) || 0}</div><div class="stat-sub">إجمالي المسجلين</div></div>
        <div class="stat-card green"><div class="stat-label">الطلبات</div><div class="stat-value">${parseInt(d.orders) || 0}</div><div class="stat-sub">إجمالي الطلبات</div></div>
        <div class="stat-card cyan"><div class="stat-label">التحاليل</div><div class="stat-value">${parseInt(d.tests) || 0}</div><div class="stat-sub">نتيجة تحليل</div></div>
        <div class="stat-card red"><div class="stat-label">حرجة</div><div class="stat-value">${parseInt(d.critical) || 0}</div><div class="stat-sub">نتائج غير طبيعية</div></div>
      </div>
      <div class="grid-2">
        <div class="card">
          <div class="card-title">إحصائيات اليوم</div>
          <div class="kpi-row">
            <div class="kpi"><span class="kpi-val">${d.today?.patients || 0}</span><span class="kpi-label">مرضى جدد</span></div>
            <div class="kpi"><span class="kpi-val">${d.today?.orders || 0}</span><span class="kpi-label">طلبات</span></div>
            <div class="kpi"><span class="kpi-val">${d.today?.tests || 0}</span><span class="kpi-label">تحاليل</span></div>
          </div>
          <div class="card-title" style="margin-top:16px">هذا الأسبوع</div>
          <div class="kpi-row">
            <div class="kpi"><span class="kpi-val">${d.this_week?.patients || 0}</span><span class="kpi-label">مرضى</span></div>
            <div class="kpi"><span class="kpi-val">${d.this_week?.orders || 0}</span><span class="kpi-label">طلبات</span></div>
            <div class="kpi"><span class="kpi-val">${d.this_week?.tests || 0}</span><span class="kpi-label">تحاليل</span></div>
          </div>
        </div>
        <div class="card">
          <div class="card-title">آخر الطلبات</div>
          ${(d.recent_orders || []).length ? d.recent_orders.slice(0, 6).map(o => `
            <div class="activity-item">
              <div class="activity-dot" style="background:${o.status === 'completed' ? 'var(--success)' : 'var(--primary)'}"></div>
              <div>
                <div class="activity-text">${esc(o.patient_name || 'مريض')} - ${parseInt(o.test_count) || 0} تحاليل</div>
                <div class="activity-time">${timeAgo(o.date || o.created_at)}</div>
              </div>
            </div>
          `).join('') : '<div class="empty"><p>لا توجد طلبات حديثة</p></div>'}
        </div>
      </div>
      ${(d.abnormal_results || []).length ? `
      <div class="card" style="margin-top:16px">
        <div class="card-title">نتائج غير طبيعية تحتاج مراجعة</div>
        <div class="table-wrap"><table>
          <thead><tr><th>المريض</th><th>التحليل</th><th>القيمة</th><th>المدى الطبيعي</th><th>الحالة</th></tr></thead>
          <tbody>
            ${d.abnormal_results.slice(0, 10).map(r => `<tr class="${r.flag === 'critical' ? 'critical-row' : ''}">
              <td>${esc(r.patient_name || '-')}</td><td>${esc(r.test_name)}</td>
              <td><strong>${esc(r.value)}</strong> ${esc(r.unit || '')}</td>
              <td>${esc(r.normal_range_low || '?')} - ${esc(r.normal_range_high || '?')}</td>
              <td>${resultFlag(r.value, r.normal_range_low, r.normal_range_high)}</td>
            </tr>`).join('')}
          </tbody>
        </table></div>
      </div>` : ''}
    `;
  } catch (e) {
    $('page').innerHTML = `<div class="empty"><p>تعذر تحميل البيانات</p></div>`;
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
async function pageOrders() {
  $('page').innerHTML = `
    <div class="page-header">
      <div class="page-header-row">
        <div><h2>الطلبات والنتائج</h2><p>إدارة طلبات التحاليل ونتائجها</p></div>
        <button class="btn btn-primary" onclick="openNewOrder()">+ طلب جديد</button>
      </div>
    </div>
    <div class="card"><div id="ordersTable"><div class="spinner"></div></div></div>
  `;
  loadOrders();
}

async function loadOrders() {
  try {
    const d = await api(`/results/orders?skip=${orderPage * PAGE_SIZE}&limit=${PAGE_SIZE}`);
    const el = $('ordersTable');
    if (!d.orders.length) { el.innerHTML = '<div class="empty"><p>لا توجد طلبات</p></div>'; return; }
    el.innerHTML = `
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>المريض</th><th>الطبيب</th><th>التحاليل</th><th>التاريخ</th><th></th></tr></thead>
        <tbody>${d.orders.map((o, i) => `<tr>
          <td>${orderPage * PAGE_SIZE + i + 1}</td>
          <td><strong>${esc(o.patient_name || '-')}</strong></td>
          <td>${esc(o.doctor_name || '-')}</td>
          <td><span class="badge badge-blue">${(o.results || []).length} تحليل</span></td>
          <td>${formatDate(o.created_at)}</td>
          <td><button class="btn btn-outline btn-sm" onclick="viewOrder(${parseInt(o.id)})">تفاصيل</button></td>
        </tr>`).join('')}</tbody>
      </table></div>
    `;
  } catch (e) { $('ordersTable').innerHTML = `<div class="empty"><p>تعذر تحميل البيانات</p></div>`; }
}

async function viewOrder(id) {
  try {
    const o = await api(`/results/orders/${id}`);
    openModal(`طلب #${parseInt(o.id)}`, `
      <div class="kpi-row" style="margin-bottom:16px">
        <div class="kpi"><span class="kpi-val">${esc(o.patient_name || '-')}</span><span class="kpi-label">المريض</span></div>
        <div class="kpi"><span class="kpi-val">${esc(o.doctor_name || '-')}</span><span class="kpi-label">الطبيب</span></div>
        <div class="kpi"><span class="kpi-val">${formatDate(o.created_at)}</span><span class="kpi-label">التاريخ</span></div>
      </div>
      <div class="table-wrap"><table>
        <thead><tr><th>التحليل</th><th>القيمة</th><th>الوحدة</th><th>المدى الطبيعي</th><th>الحالة</th><th>رابط</th></tr></thead>
        <tbody>${(o.results || []).map(r => `<tr>
          <td>${esc(r.test_name)}</td>
          <td><strong>${esc(r.value || r.value_text || '-')}</strong></td>
          <td>${esc(r.unit || '')}</td>
          <td>${esc(r.normal_range_low || '?')} - ${esc(r.normal_range_high || '?')}</td>
          <td>${resultFlag(r.value, r.normal_range_low, r.normal_range_high)}</td>
          <td>${r.result_token ? `<a href="/r/${escAttr(r.result_token)}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">مشاركة</a>` : '-'}</td>
        </tr>`).join('')}</tbody>
      </table></div>
    `);
  } catch (e) { toast(e.message, 'error'); }
}

function openNewOrder() {
  openModal('طلب تحليل جديد', `
    <form onsubmit="submitOrder(event)">
      <div class="form-row">
        <div class="field"><label>رقم المريض *</label><input id="ordPatientId" required type="number" min="1"></div>
        <div class="field"><label>اسم الطبيب</label><input id="ordDoctor" maxlength="200"></div>
      </div>
      <div class="card-title">التحاليل</div>
      <div id="orderTests"></div>
      <button type="button" class="btn btn-outline btn-sm" onclick="addTestRow()" style="margin-bottom:16px">+ إضافة تحليل</button>
      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button type="button" class="btn btn-outline" onclick="closeModal()">إلغاء</button>
        <button type="submit" class="btn btn-primary" id="submitOrderBtn">حفظ الطلب</button>
      </div>
    </form>
  `);
  addTestRow();
}

function newOrderForPatient(id) {
  openNewOrder();
  $('ordPatientId').value = id;
}

function addTestRow() {
  const div = document.createElement('div');
  div.className = 'form-row';
  div.style.marginBottom = '8px';
  div.innerHTML = `
    <div class="field"><label>اسم التحليل</label><input class="t-name" required maxlength="100"></div>
    <div class="field"><label>القيمة</label><input class="t-val" required></div>
    <div class="field"><label>الوحدة</label><input class="t-unit" maxlength="20"></div>
    <div class="field"><label>أدنى</label><input class="t-low" type="number" step="any" min="0"></div>
    <div class="field"><label>أعلى</label><input class="t-high" type="number" step="any" min="0"></div>
  `;
  $('orderTests').appendChild(div);
}

async function submitOrder(e) {
  e.preventDefault();
  const btn = $('submitOrderBtn');
  btn.disabled = true;
  try {
    const rows = $('orderTests').querySelectorAll('.form-row');
    const results = Array.from(rows).map(r => ({
      test_name: r.querySelector('.t-name').value,
      value: r.querySelector('.t-val').value,
      unit: r.querySelector('.t-unit').value,
      normal_range_low: parseFloat(r.querySelector('.t-low').value) || undefined,
      normal_range_high: parseFloat(r.querySelector('.t-high').value) || undefined
    }));
    await api('/results/orders', { method: 'POST', body: JSON.stringify({
      patient_id: parseInt($('ordPatientId').value),
      doctor_name: $('ordDoctor').value || undefined,
      results
    })});
    closeModal(); toast('تم حفظ الطلب بنجاح'); loadOrders();
  } catch (e) { toast(e.message, 'error'); }
  btn.disabled = false;
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
  try {
    const lab = await api('/labs/me');
    $('page').innerHTML = `
      <div class="page-header"><h2>المختبر</h2><p>إعدادات ومعلومات المختبر</p></div>
      <div class="card">
        <form onsubmit="saveLab(event)">
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
            <div class="field"><label>الحالة</label><input value="${lab.is_active ? 'نشط' : 'معطل'}" disabled></div>
          </div>
          <div style="margin-top:16px"><button type="submit" class="btn btn-primary" id="saveLabBtn">حفظ التعديلات</button></div>
        </form>
      </div>
    `;
  } catch (e) {
    $('page').innerHTML = `<div class="empty"><p>تعذر تحميل البيانات</p></div>`;
  }
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
  try {
    const stats = await api('/admin/stats');
    const labs = await api('/admin/labs?limit=50');
    $('page').innerHTML = `
      <div class="page-header"><h2>إدارة المنصة</h2><p>لوحة تحكم المدير العام</p></div>
      <div class="stats-grid">
        <div class="stat-card blue"><div class="stat-label">المختبرات</div><div class="stat-value">${parseInt(stats.total_labs) || 0}</div></div>
        <div class="stat-card green"><div class="stat-label">المستخدمون</div><div class="stat-value">${parseInt(stats.total_users) || 0}</div></div>
        <div class="stat-card cyan"><div class="stat-label">المرضى</div><div class="stat-value">${parseInt(stats.total_patients) || 0}</div></div>
        <div class="stat-card yellow"><div class="stat-label">النتائج</div><div class="stat-value">${parseInt(stats.total_results) || 0}</div></div>
      </div>
      <div class="card">
        <div class="card-title">المختبرات المسجلة</div>
        <div class="table-wrap"><table>
          <thead><tr><th>المختبر</th><th>المدينة</th><th>المستخدمون</th><th>المرضى</th><th>الحالة</th><th></th></tr></thead>
          <tbody>${(labs.labs || labs).map(l => `<tr>
            <td><strong>${esc(l.name)}</strong></td>
            <td>${esc(l.city || '-')}</td>
            <td>${parseInt(l.user_count) || 0}</td>
            <td>${parseInt(l.patient_count) || 0}</td>
            <td>${l.is_active ? '<span class="badge badge-green">نشط</span>' : '<span class="badge badge-red">معطل</span>'}</td>
            <td><button class="btn btn-outline btn-sm" onclick="toggleLab(${parseInt(l.id)})">${l.is_active ? 'تعطيل' : 'تفعيل'}</button></td>
          </tr>`).join('')}</tbody>
        </table></div>
      </div>
    `;
  } catch (e) { $('page').innerHTML = `<div class="empty"><p>تعذر تحميل البيانات</p></div>`; }
}

async function toggleLab(id) {
  confirmAction(
    'تأكيد التغيير',
    'هل أنت متأكد من تغيير حالة هذا المختبر؟ هذا سيؤثر على جميع مستخدمي المختبر.',
    async function() {
      try {
        await api(`/admin/labs/${id}/toggle`, { method: 'PUT' });
        toast('تم تحديث حالة المختبر'); pageAdmin();
      } catch (e) { toast(e.message, 'error'); }
    }
  );
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

// ---- Init ----
function init() {
  if (!checkAuth()) return;

  // Set user info in sidebar
  $('userName').textContent = G.user.name || 'المستخدم';
  $('userRole').textContent = G.user.role === 'master_admin' ? 'مدير عام' : G.user.role === 'admin' ? 'مدير مختبر' : 'موظف';
  $('userAvatar').textContent = (G.user.name || 'م')[0];

  // Show admin nav for master_admin
  if (G.user.role === 'master_admin') $('adminNav').style.display = '';

  // Set lab name
  if (G.user.lab_name) $('labName').textContent = G.user.lab_name;

  // Route
  const page = window.location.hash.replace('#', '') || 'dashboard';
  navigate(page);
}

window.addEventListener('hashchange', () => {
  const page = window.location.hash.replace('#', '') || 'dashboard';
  navigate(page);
});

init();
