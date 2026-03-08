# NHOP — National Health Operations Platform

منصة عمليات صحية وطنية مفتوحة المصدر لإدارة المختبرات والبيانات الصحية.

---

## نظرة عامة

NHOP منصة صحية رقمية وطنية تربط المختبرات، الأطباء، والمرضى في نظام موحد وخفيف وقابل للتوسع.
مصممة لتبدأ كنظام **LIS** (Laboratory Information System) وتتوسع تدريجياً نحو **منصة صحية وطنية شاملة**.

### الأطراف المستفيدة

| الطرف | البوابة | الوظيفة |
|-------|---------|---------|
| فني المختبر | `/lab` | إدارة الطلبات، العينات، إدخال النتائج، الاعتماد |
| الطبيب | `/doctor` | طلب تحاليل، عرض النتائج، تحليل AI |
| المريض | `/portal` | تتبع الطلبات، تحميل التقارير |
| المدير | `/admin` | إدارة المستخدمين، كتالوج الفحوصات، إحصائيات، سجل العمليات |

---

## البنية التقنية

```
nhop-platform/
├── nhop/                        # Node.js + Express (الخادم الرئيسي)
│   ├── server.js                # نقطة الدخول + CORS + تحميل الإضافات
│   ├── core/
│   │   └── database/db.js       # اتصال PostgreSQL
│   ├── migrations/
│   │   └── 001_init.sql         # مخطط قاعدة البيانات
│   └── extensions/
│       ├── auth/                # JWT + إدارة المستخدمين + Audit Logs
│       ├── lab.workflow/        # سير العمل المخبري الكامل + تقرير TAT
│       ├── doctor.portal/       # بوابة الطبيب + تحليل AI
│       ├── patient.portal/      # بوابة المريض
│       └── patients/            # إدارة سجلات المرضى
│
├── nhop-frontend/               # React 19 + TypeScript + Vite
│   └── src/
│       ├── pages/
│       │   ├── lab/             # dashboard, orders, samples, results, queue, approval, critical, tat-report
│       │   ├── doctor/          # dashboard, patients, patient-detail, new-order
│       │   ├── patient/         # dashboard, results, orders, track, report
│       │   ├── admin/           # dashboard, catalog, users, link-patient, audit-log
│       │   └── shared/          # profile
│       ├── components/          # Layout, Toast
│       ├── store/               # Zustand (auth state)
│       └── api/                 # Axios client
│
└── national-health-lab-platform/ # Python FastAPI (خدمة ذكاء اصطناعي)
    └── backend/
        ├── main.py
        ├── auth.py
        ├── models/
        └── routers/
```

### Stack التقني

| الطبقة | التقنية | السبب |
|--------|---------|-------|
| Frontend | React 19 + TypeScript + Vite | أداء عالٍ، نظام أنواع، بناء سريع |
| State Management | Zustand | خفيف وبسيط |
| Backend | Node.js + Express (Plugin Architecture) | خفيف، قابل للتوسع بالإضافات |
| AI / ML | Python FastAPI | مكتبات Python الغنية بالذكاء الاصطناعي |
| Database | PostgreSQL | موثوقية، ACID، مناسب للأنظمة الصحية |
| Auth | JWT + Refresh Tokens + bcryptjs | معيار صناعي آمن |
| CSS | Custom RTL Design System | دعم كامل للعربية، بدون مكتبات ثقيلة |

---

## نموذج قاعدة البيانات

```sql
users              -- المستخدمون (admin, lab_staff, doctor, patient, citizen)
patients           -- سجلات المرضى (مرتبطة بـ users)
test_catalog       -- كتالوج الفحوصات (27+ فحص مضمّن)
lab_orders         -- طلبات التحليل
lab_order_items    -- عناصر الطلب (الفحوصات المطلوبة)
samples            -- العينات (مع باركود وحالة)
test_results       -- النتائج (مع قيم طبيعية وعلامات الانحراف)
refresh_tokens     -- توكنات التجديد
audit_logs         -- سجل العمليات الكامل
```

---

## API Endpoints

### المصادقة `/auth`
| Method | Path | الوصف |
|--------|------|-------|
| POST | `/auth/register` | تسجيل مستخدم جديد |
| POST | `/auth/login` | تسجيل الدخول (JWT) |
| POST | `/auth/refresh` | تجديد التوكن |
| GET | `/auth/me` | بيانات المستخدم الحالي |
| PATCH | `/auth/me` | تحديث الملف الشخصي |
| POST | `/auth/change-password` | تغيير كلمة المرور |
| GET | `/auth/users` | قائمة المستخدمين (admin) |
| POST | `/auth/users` | إضافة مستخدم (admin) |
| PATCH | `/auth/users/:id/status` | تفعيل/تعطيل مستخدم |
| POST | `/auth/users/:id/reset-password` | إعادة تعيين كلمة المرور |
| GET | `/auth/audit-logs` | سجل العمليات (admin) |

### المختبر `/lab`
| Method | Path | الوصف |
|--------|------|-------|
| GET | `/lab/catalog` | كتالوج الفحوصات |
| POST | `/lab/orders` | إنشاء طلب تحليل |
| GET | `/lab/orders` | قائمة الطلبات (مع فلاتر) |
| GET | `/lab/work-queue` | قائمة المهام المعلقة |
| PATCH | `/lab/samples/:id/collect` | جمع العينة |
| PATCH | `/lab/samples/:id/receive` | استلام العينة |
| PATCH | `/lab/samples/:id/reject` | رفض العينة |
| POST | `/lab/results` | إدخال نتائج |
| PATCH | `/lab/results/:id/approve` | اعتماد نتيجة |
| POST | `/lab/orders/:id/approve-all` | اعتماد جميع نتائج طلب |
| POST | `/lab/orders/:id/release` | إصدار للمريض |
| GET | `/lab/critical-values` | النتائج الحرجة |
| GET | `/lab/tat-report` | تقرير زمن الاستجابة (TAT) |
| GET | `/lab/reports/:orderId` | تقرير PDF |

### الطبيب `/doctor`
| Method | Path | الوصف |
|--------|------|-------|
| GET | `/doctor/patients` | قائمة مرضاي |
| GET | `/doctor/patients/:id` | ملف مريض كامل |
| GET | `/doctor/patients/:id/results` | اتجاهات نتائج مريض |
| POST | `/doctor/analyze/:patientId` | تحليل AI للمريض |

### بوابة المريض `/portal`
| Method | Path | الوصف |
|--------|------|-------|
| GET | `/portal/orders` | طلباتي |
| GET | `/portal/orders/:id/status` | تتبع طلب (timeline) |
| GET | `/portal/results` | نتائجي |
| GET | `/portal/report/:orderId` | تقريري (PDF) |
| GET | `/portal/health-summary` | الملخص الصحي |

---

## التشغيل

### المتطلبات
- Node.js 18+
- PostgreSQL 14+
- Python 3.11+ (للخدمات AI الاختيارية)

### الإعداد السريع

```bash
# 1. استنساخ المستودع
git clone https://github.com/your-org/nhop-platform.git
cd nhop-platform

# 2. إعداد متغيرات البيئة
cp nhop/.env.example nhop/.env
# عدّل البيانات في .env

# 3. تهيئة قاعدة البيانات
cd nhop && npm install && npm run migrate

# 4. تشغيل الخادم
npm start        # الإنتاج
npm run dev      # التطوير (nodemon)

# 5. تشغيل الواجهة الأمامية
cd ../nhop-frontend
npm install
npm run dev      # localhost:5173
npm run build    # بناء الإنتاج
```

### متغيرات البيئة (nhop/.env)

```env
PORT=3000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nhop_db
DB_USER=postgres
DB_PASSWORD=your_password
JWT_SECRET=your_jwt_secret_min_32_chars
JWT_EXPIRES=8h
ALLOWED_ORIGINS=http://localhost:5173
```

---

## نظام الأدوار والصلاحيات

```
admin      → وصول كامل + سجل عمليات + تقارير
lab_staff  → /lab/* (المختبر)
doctor     → /doctor/* (بوابة الطبيب)
patient    → /portal/* (بوابة المريض)
citizen    → /portal/* (مواطن غير مرتبط بسجل طبي)
```

---

## الأمان

- كلمات المرور مشفرة بـ bcryptjs (cost factor: 12)
- JWT مع refresh tokens (انتهاء منفصل)
- RBAC على مستوى كل route وendpoint
- CORS محكوم للـ origins المسموح بها فقط
- **Audit Log** لكل عملية حساسة (تسجيل دخول، إدخال نتائج، اعتماد، إصدار)

---

## الفحوصات المضمّنة (27 فحص)

`CBC` `HGB` `WBC` `PLT` `GLU` `HBA1C` `CHOL` `LDL` `HDL` `TG`
`CREA` `BUN` `ALT` `AST` `TSH` `T3` `T4` `UA` `URIC` `CRP`
`ESR` `VITD` `VITB12` `FERR` `IRON` `COVID` `CULT`

---

## المساهمة

انظر [ROADMAP.md](./ROADMAP.md) لخارطة الطريق الكاملة وقائمة الـ 50 ميزة المخططة.

---

## الرخصة

MIT License — لأغراض البحث والتطوير الصحي والحكومي.
