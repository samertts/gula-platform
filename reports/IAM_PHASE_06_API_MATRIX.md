# IAM Phase 6 API Matrix

| الشاشة | العملية | API | Method | Authentication | Membership required | Organization | Facility | Department | Workspace | Backend validation | Error | Test |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| My Organizations | عرض عضوياتي | `/niam/memberships/me` | GET | NIAM access token + active JTI session | actor account فقط | مستخرج من actor memberships | مستخرج من membership | مستخرج من membership | مستخرج من membership | active account، server query، expiry evaluation | 401، 404 عند actor غير صالح | `test_membership_api_phase6.py` |
| Membership Requests | تقديم طلب | `/niam/memberships/applications` | POST | active NIAM actor | لا؛ الطلب self-only | body organization validated | optional + belongs to org | optional + belongs to facility | optional + belongs to org | organization active، scope exact، actor == target account، idempotency key | 401، 403، 422 | `test_membership_phase6.py` |
| Organization Admin | اعتماد طلب | `/niam/memberships/applications/{id}/approve` | POST | active NIAM actor | ownership/representative active | target application org | context from application | context from application | context from application | actor organizational authority، application state، transaction | 401، 403، 404، 409 | service state tests + future DB/API integration |
| Organization Admin | إنشاء دعوة | `/niam/memberships/invitations` | POST | active NIAM actor | ownership/representative active | body org validated | optional | optional | optional | actor org authority، scope validation، random token hash، TTL، no duplicate pending | 401، 403، 409، 422 | service tests + future DB/API integration |
| Invitations | قبول دعوة | `/niam/memberships/invitations/{id}/accept` | POST | recipient active actor | invitation recipient or unresolved policy | invitation-owned | invitation-owned | invitation-owned | invitation-owned | token hash، expiry، one-use، recipient match، transaction | 401، 409 | service tests + future integration |
| Organization Admin | إلغاء دعوة | `/niam/memberships/invitations/{id}/revoke` | POST | active NIAM actor | ownership/representative active | invitation-owned | invitation-owned | invitation-owned | invitation-owned | pending status، actor scope authority، audit | 401، 403، 409 | service tests + future integration |
| Organization Admin | تعليق عضوية | `/niam/memberships/{id}/suspend` | POST | active NIAM actor | ownership/representative active | membership-owned | membership-owned | membership-owned | membership-owned | lifecycle matrix، reason، audit | 401، 403، 404، 409 | state/service tests |
| Organization Admin | إعادة تفعيل | `/niam/memberships/{id}/reactivate` | POST | active NIAM actor | ownership/representative active | membership-owned | membership-owned | membership-owned | membership-owned | legal transition، expiry، audit | 401، 403، 404، 409 | state/service tests |
| Organization Admin | إلغاء عضوية | `/niam/memberships/{id}/revoke` | POST | active NIAM actor | ownership/representative active | membership-owned | membership-owned | membership-owned | membership-owned | history preserved، status immutable terminal، audit | 401، 403، 404، 409 | state/service tests |

## ملاحظات العقد

لا توجد في Phase 6 endpoints تقبل `status`, `account_id`, `actor_id` أو authorization decision من العميل كقيم authoritative. لا تُعاد raw invitation token إلا في استجابة الإنشاء المصرح بها، ولا يُعاد `token_hash` في أي استجابة.

لا توجد endpoints mock أو fake acceptance في العقد الحالي. واجهات Frontend وMobile يجب استهلاك هذه المسارات نفسها، وأي capability أو membership list تُعامل كعرض لا كقرار تفويض.
