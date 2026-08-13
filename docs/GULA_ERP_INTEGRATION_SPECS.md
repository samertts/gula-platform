# متطلبات تكامل أنظمة تخطيط موارد المؤسسات (ERP Integration Specs) — منصة GULA
**تاريخ الإصدار:** 12 أغسطس 2026
**المستودع الرسمي:** [GitHub Repository](https://github.com/samertts/gula-platform)

---

## 1. نظرة عامة
لربط أنظمة تخطيط موارد المؤسسات (ERP) الخاصة بالمستشفيات المحلية مع منصة GULA الوطنية، توفر المنصة واجهات برمجة تطبيقات (APIs) معيارية مبنية على بروتوكول **REST / JSON** ومؤمنة عبر **JWT** و **OAuth 2.0**. يهدف التكامل إلى مزامنة البيانات المالية، إدارة الموارد البشرية، وتتبع المخزون الطبي بشكل لحظي وآمن.

---

## 2. النطاقات الرئيسية للتكامل (Integration Domains)

### أ. وحدة الموارد البشرية (HR & Staff Sync)
تتطلب مزامنة الكوادر الطبية والإدارية بين نظام الـ ERP والمستشفى لضمان دقة الصلاحيات (RBAC/ABAC).
- **مسار مزامنة الموظفين:** `POST /api/v1/erp/hr/staff-sync`
- **البيانات المطلوبة:**
  ```json
  {
    "hospital_id": "uuid-hospital-123",
    "employee_code": "EMP-9921",
    "full_name": "د. أحمد جاسم",
    "role": "DOCTOR",
    "department": "ICU",
    "status": "ACTIVE"
  }
  ```

### ب. وحدة المالية والفواتير (Billing & Financials)
ربط العمليات السريرية والوصفات الطبية بالدورة المالية والمحاسبية للمستشفى.
- **مسار إرسال الفواتير:** `POST /api/v1/erp/finance/invoices`
- **البيانات المطلوبة:**
  ```json
  {
    "invoice_id": "INV-2026-8812",
    "patient_id": "PAT-4412",
    "hospital_id": "uuid-hospital-123",
    "items": [
      {"description": "فحص تحليلي شامل", "amount": 45000, "currency": "IQD"}
    ],
    "total_amount": 45000
  }
  ```

### ج. وحدة المخازن والتموين الطبي (Inventory & Pharmacy)
تتبع مستويات الأدوية، المستلزمات الطبية، وتنبيهات النفاذ.
- **مسار تحديث المخزون:** `PUT /api/v1/erp/inventory/stock-update`
- **البيانات المطلوبة:**
  ```json
  {
    "hospital_id": "uuid-hospital-123",
    "item_code": "MED-INS-01",
    "item_name": "إنسولين ميكساتارد",
    "batch_number": "B2026-99",
    "quantity_available": 1250,
    "reorder_threshold": 100
  }
  ```

---

## 3. معايير الأمان وموثوقية الاتصال
1. **التشفير الإلزامي:** جميع طلبات الـ API تتطلب اتصالاً مشفراً عبر **TLS 1.3**.
2. **التحقق من الهوية:** استخدام مفاتيح API خاصة بالمستشفى (`X-API-Key`) وتوقيعات رقمية (HMAC) لضمان سلامة الحمولة (Payload).
3. **معالجة التراجع (Idempotency):** يجب أن تتضمن كل عملية مفتاح تفرّد (`Idempotency-Key`) لمنع تكرار المعاملات المالية أو المخزنية في حال انقطاع الاتصال.

---
*جميع الحقوق محفوظة © 2026 GULA Health National Platform.*
