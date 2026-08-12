# GULA Technical Leadership Report — Reconciliation

**التاريخ:** 2026-08-12

**الغرض:** مطابقة تقرير الإدارة والقيادة التقنية المرفق مع الحالة الفعلية للمستودع، ومنع تحويل التوصيات الاستراتيجية إلى ادعاءات تشغيلية أو تغييرات deployment قبل وجود evidence واعتماد.

## Executive assessment

التقرير مفيد كاتجاه إداري، لكنه يخلط بين وجود ملفات أو نماذج أولية وبين جاهزية إنتاجية مثبتة. المستودع يملك بالفعل أساساً واسعاً: FastAPI، عدة واجهات، Docker Compose، Terraform، Helm، workflows لـCodeQL وTrivy، نماذج Break-Glass، وتكاملات HL7/ASTM/DICOM. لكن وجود هذه المكونات لا يثبت أنها موحدة المصدر، أو أنها اجتازت تدفقاً end-to-end، أو أنها آمنة ومهيأة للإنتاج الوطني.

القرار الآمن هو اعتماد التقرير كـ**input لخارطة أولويات** لا كـrelease authorization. تبقى Wave 3 وCitizen C1 المرجع المعتمد، ولا تُنفذ تغييرات VPS/cloud، أو دمج واجهات، أو backfill، أو store/release operations ضمن هذه المراجعة.

## Claim-to-evidence matrix

| توصية/ادعاء التقرير | الدليل الفعلي | التقييم | القرار |
|---|---|---|---|
| Monolith-first يقلل التعقيد | يوجد backend مركزي، لكن توجد services و`nhop-platform` وواجهات متعددة | صحيح جزئياً | تثبيت source-of-truth قبل أي consolidation؛ لا حذف |
| Docker Compose جاهز | `docker-compose.yml` و`docker-compose.full.yml` وملفات Compose مرافقة موجودة | مثبت وجودياً، غير مثبت تشغيلياً | تشغيل smoke/deploy validation مستقل |
| Terraform وHelm موجودان | `terraform/` و`helm/gula-platform/Chart.yaml` موجودان | مثبت وجودياً | لا تغيير deployment behavior قبل مراجعة secrets/state/rollback |
| Backup PostgreSQL Local/S3 متوفر | لم يثبت وجود مسار backup/restore تشغيلي مكتمل في الفحص الأول | غير مثبت | C2 مستقل: backup/restore drill مع RPO/RTO وencryption |
| Offline-first جاهز | توجد `OfflineSyncEngine` وroutes integration، لكن ذلك لا يثبت mobile encrypted cache/sync conflict safety | جزئي/غير مكتمل | عدم إعلان offline-first؛ ابدأ contract وtests ثم mobile implementation |
| ASTM/HL7/DICOM جاهز | توجد standards/connectors/gateways، لكنها تحتاج contract وdevice sandbox وround-trip evidence | جزئي | اختبار device bridge مع synthetic messages فقط |
| Break-Glass مفعّل | توجد models/policies/routes وhealth-data governance references | وجود foundation فقط | مراجعة policy/authorization/audit/expiry/notification قبل التفعيل |
| Trivy وCodeQL موجودان | workflows `nightly.yml`, `codeql.yml`, `codeql-analysis.yml` موجودة، مع Bandit في CI | مثبت كـCI surface | تحقق من آخر runs والـfindings؛ لا تدّعِ clean posture من وجود workflow |
| توحيد frontend-v3 أو gula-web-suite | قرارات Wave 2 تجعل `frontend-v3` canonical web؛ `gula-web-suite` مسار مختلف يحتاج reconciliation | القرار القائم هو frontend-v3 | لا rename ولا حذف؛ migration map مستقل |
| Hetzner/Contabo يخفضان التكلفة 70% | لا توجد دراسة load/capacity/egress/backup/data-sovereignty تثبت النسبة | ادعاء غير مثبت | دراسة تكلفة ومخاطر واعتماد منفصل؛ لا نشر أو نقل بيانات |
| Freemium/Pilot للمختبرات | اقتراح تجاري لا يثبت entitlement، support، SLA، legal/privacy، أو isolation | قرار منتج/حوكمة | يكتب كـpilot charter؛ لا يغير subscriptions أو pricing تلقائياً |
| MVP خلال شهر/offline خلال شهرين/3–5 مختبرات في الشهر الثالث | جدول زمني إداري غير مربوط ببوابات الأمن والتفويض والاختبارات | غير معتمد | استبداله بموجات evidence-based لا بتواريخ ثابتة |

## Priority decisions

الأولوية الأولى ليست شراء VPS أو تجميد واجهات، بل تثبيت بوابات الأمان والبيانات التي تسمح بالتوسع. يجب أن يسبق أي pilot حقيقي workflow إداري audited لإنشاء وتفعيل وإلغاء `CitizenRelationship`، ثم Demo isolation وsynthetic cohort، ثم contract tests للمواعيد والنتائج والمستندات.

بعد ذلك تُنفذ backup/restore validation، ثم device bridge sandbox، ثم offline synchronization المحدود. لا يجوز استخدام cache أو retry أو offline queue لتجاوز authorization أو state machine أو immutable audit.

## C2 execution update

تم تنفيذ C2 كأول تحسين آمن من التقرير: خدمة workflow إدارية لإنشاء pending relationship وتفعيلها وإلغائها، مع Idempotency-Key وrequest fingerprint وscope بلا wildcard وsource/patient validation وaudit. لا ينفذ C2 backfill أو auto-match أو dual-write، ويدعم في نسخته الأولى `legacy_user/self/citizen_workspace` فقط.

الدليل الفعلي بعد التنفيذ هو `2305 passed, 251 warnings` في Backend full suite، و`12 passed` في اختبارات C1/C2 المشتركة، وfresh SQLite migration إلى `20260812_0001 (head)` مع downgrade/re-upgrade ناجح. هذه النتيجة تثبت الدفعة البرمجية، ولا تثبت production readiness أو cohort activation.

## Recommended waves

| Wave | النطاق | Gate قبل الانتقال |
|---|---|---|
| C2 | **منفذ:** audited relationship activation/revocation، idempotency، duplicate prevention | `2305 passed` وnegative authorization/C2 workflow evidence؛ لا cohort production |
| O1 | PostgreSQL backup encryption، restore drill، RPO/RTO، retention | restore على بيئة معزولة وchecksum/secret review |
| I1 | ASTM/HL7/DICOM synthetic device sandbox وmessage validation | round-trip tests وinvalid message rejection |
| O2 | Break-Glass policy review، step-up، expiry، reason، notification، citizen transparency policy | authorization/audit/privacy sign-off |
| F1 | frontend-v3 shell consolidation map وlegacy freeze policy | build/e2e/route inventory؛ لا rename/delete |
| M1 | mobile offline contract: encrypted cache، sync states، stale markers، conflict rejection | Android/iOS tests على low-end/intermittent network |
| P1 | pilot charter لـ3–5 facilities مع synthetic/demo boundary وsupport/rollback | security/privacy/operations approval |

## Management decisions still required

تحتاج التوصيات التالية قراراً صريحاً قبل التنفيذ: اختيار hosting provider، قبول/رفض نقل البيانات خارج السيادة المطلوبة، RPO/RTO، نموذج pilot وفترة التجربة، pricing/freemium، supported device protocols، حدود Break-Glass، وموعد/معيار تجميد legacy frontends. لا تُستنتج هذه القرارات من وجود ملفات في المستودع.

## Evidence boundaries

الفحص الحالي أثبت وجود source surfaces، وليس readiness. يلزم لكل surface أمر تشغيل/اختبار وسجل نتيجة: deployment smoke، Terraform plan في بيئة آمنة دون apply، Helm template/lint، backup restore، CodeQL/Trivy latest run، ASTM/HL7/DICOM round-trip، Break-Glass authorization test، وoffline sync conflict tests.

**الخلاصة:** التقرير صالح كوثيقة قيادة وتوجيه، لكنه لا يبرر إعلان المنصة جاهزة وطنياً أو تجارياً. تم تنفيذ C2 كدفعة مراجعة، بينما تبقى O1/I1/O2/F1/M1 موجات مستقلة غير منفذة، مع إبقاء Wave 3 وCitizen C1 دون هدم أو عمليات تدميرية.
