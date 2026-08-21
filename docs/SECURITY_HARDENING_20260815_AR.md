# تعزيز أمان منصة GULA — تقرير دفاعي

**التاريخ:** 15 أغسطس 2026

**النطاق:** أمان runtime والمنصة والتطبيق والبيانات، وليس إعدادات مستودع GitHub فقط.

**المبدأ الحاكم:** كل الاختبارات والضوابط في هذه الدفعة دفاعية ومصرح بها وغير تدميرية. لا تُضاف أبواب خلفية، ولا آليات persistence، ولا سرقة اعتماديات، ولا تنفيذ exploits ضد أنظمة خارجية. أي فكرة مستلهمة من الهندسة العكسية أو تحليل الثغرات تُستخدم فقط لبناء كشف ومنع واختبارات على fixtures اصطناعية أو أصول مملوكة لـGULA.

## الملخص التنفيذي

تستند هذه الدفعة إلى تحويل مفاهيم عامة من OWASP ASVS وNIST SSDF وCISA/HHS Healthcare Cybersecurity Performance Goals، مع إعادة تكوين أنماط من OpenFGA وOpenBao وTrivy وFalco وOpenSSF Scorecard داخل حدود GULA، دون نسخ كود أو واجهات. يوفّر ASVS أساسًا لاختبار الضوابط التقنية لتطبيقات الويب، بينما ينظم SSDF الممارسات في التحضير والحماية والإنتاج والاستجابة [1] [2]. وتؤكد CISA وHHS أن الأمن السيبراني في الصحة مرتبط مباشرة بسلامة المريض وسرية البيانات وتوافر الخدمات [3] [4].

| مجال الخطر | الضابط المنفذ في GULA | الحالة |
|---|---|---|
| إساءة استخدام AI وRAG | صلاحيات مؤسسية، rate limit، عزل namespace حسب المختبر، حدود حجم الإدخال، وفحص prompt/PII | منفذ |
| تسرب بيانات AI | حظر أنماط PII والـprompt injection قبل embedding/RAG، وتنقيح مخرجات chat | منفذ |
| brute-force على الحساب | عداد فشل وقفل مؤقت على `LabUser` و`User` مع migration `20260815_0021` | منفذ |
| log injection | تطهير `X-Request-ID` إلى قيمة bounded وآمنة للسجلات | منفذ |
| استخدام جلسة ملغاة للوصول إلى OpenAPI | فحص blacklist لـJTI في DocsAuthMiddleware | منفذ |
| عزل المؤسسات | namespace أصلي مثل `lab:<lab_id>:<collection>` وعدم قبول `lab_id` من العميل | منفذ في RAG |
| سلسلة التوريد | اعتماد مبادئ SBOM وTrivy وScorecard في خطة intake والفحص | موثق، والفحص التشغيلي التالي |
| runtime detection | عقد أحداث دفاعية مستوحى من Falco، دون تشغيل host sensor في هذه الدفعة | تصميم لاحق |

## التغييرات البرمجية

### 1. حراسة AI Fabric وعزل RAG

أصبحت وحدة AI Fabric مؤسسية افتراضيًا؛ فالطلبات المجهولة والمواطنون لا يصلون إلى نماذج AI الداخلية أو knowledge graph أو operational telemetry. تُستخدم صلاحيات GULA القائمة مثل `dashboard:read` و`patients:read` و`results:read` و`lab:read` و`audit:read` و`system:admin` بدل إنشاء صلاحيات وهمية.

يُعاد تشكيل اسم مجموعة RAG داخل الخادم. المستخدم لا يستطيع تمرير `lab_id` لاختيار مساحة مختبر آخر؛ فإذا كان الحساب مؤسسيًا تصبح المساحة `lab:<lab_id>:<collection>`. أما namespace الخاص بالمنصة فلا يُتاح إلا لدور يملك `system:admin`. كما تُرفض أسماء المسارات مثل `../shared` وتُفرض حدود على عدد chunks وطول النصوص و`top_k`.

هذا يعيد تكوين فكرة **fine-grained authorization** المستلهمة من OpenFGA، حيث تُفصل علاقة المستخدم بالمورد عن مجرد وجود جلسة صالحة، مع إبقاء التنفيذ داخل خدمات GULA الأصلية [5].

### 2. حماية مدخلات ومخرجات AI

قبل chat أو RAG query أو embedding، تمر المدخلات عبر `AIFirewall` الموجود في المنصة. تُرفض محاولات instruction override وsystem-prompt extraction وprivilege escalation وSQL/XSS-like patterns، إضافة إلى المدخلات التي تحتوي على أنماط PII. وتُفحص مخرجات chat ويُعاد النص المنقح عند اكتشاف بيانات حساسة.

هذه الحماية ليست بديلًا عن مراجعة بشرية أو clinical governance؛ فهي طبقة تقليل خطر وليست حكمًا طبيًا. كما أن بيانات الاختبار المستخدمة في الاختبارات الاصطناعية ولا تمثل سجلات مواطنين حقيقيين.

### 3. account lockout

أضيفت حقول `failed_login_attempts` و`locked_until` إلى حسابات المواطنين وحسابات المؤسسات. بعد خمس محاولات فاشلة افتراضيًا يبدأ قفل مؤقت مدته 15 دقيقة، ويمكن تغيير القيمتين عبر `MAX_FAILED_LOGIN_ATTEMPTS` و`LOGIN_LOCKOUT_MINUTES` في بيئة التشغيل. تستمر حماية IP وidentifier HMAC الموجودة، لذلك لا يعتمد النظام على طبقة واحدة فقط.

لا يكشف endpoint تسجيل الدخول ما إذا كان البريد موجودًا أو مقفولًا؛ فالرد الخارجي يبقى عامًا، بينما تُسجل حالة القفل في audit event دون كتابة البريد أو كلمة المرور أو token.

### 4. سلامة السجلات ووثائق API

يُرفض `X-Request-ID` إذا احتوى محارف أو طولًا غير آمن، ويُولّد معرف UUID جديد بدل إدخال قيمة قد تلوث سجلات التشغيل. كما لا تُتاح وثائق `/docs` و`/redoc` و`/openapi.json` باستخدام JTI ملغى في Redis، حتى لا تستمر جلسة administrator مسروقة أو ملغاة في الوصول إلى سطح المعلومات.

## الاستفادة الأصلية من المشاريع العامة

| المصدر العام | الفكرة الدفاعية المعاد تكوينها في GULA | حدود الاستخدام |
|---|---|---|
| OWASP ASVS | متطلبات تحقق للتوثيق والجلسات والصلاحيات والتحقق من المدخلات وحماية البيانات | معيار مرجعي، لا نسخ كود |
| NIST SSDF | دورة PO/PS/PW/RV لإدارة المخاطر والثغرات وسلسلة التوريد | تكييف قائم على المخاطر، لا checklist عمياء |
| CISA/HHS HPH CPGs | أولوية MFA والنسخ الاحتياطي وإدارة الثغرات والاستجابة والتوافر | إرشادات طوعية؛ يجب تكييفها مع تشغيل GULA |
| OpenFGA | نمذجة العلاقات الدقيقة بين actor وlab وresource | تنفيذ GULA الأصلي عبر dependencies وtenant namespace |
| OpenBao | هوية مستقرة وaliases وسياسات وتدقيق وصول الأسرار | لا تخزين أسرار حقيقية في fixtures؛ التكامل التشغيلي منفصل |
| Trivy | CVE/IaC/SBOM/secret scanning للأصول المملوكة | لا فحص لأنظمة خارجية أو repositories غير مصرح بها |
| Falco | قواعد كشف سلوك runtime الشاذ والاتصالات والامتيازات | لا kernel sensor أو host deployment في هذه الدفعة |
| OpenSSF Scorecard | تقييم provenance والحماية والاعتماديات قبل إدخال مشروع | مؤشر قرار، وليس ضمانًا أمنيًا منفردًا |

تمت مراجعة metadata الخاصة بالتراخيص قبل التوثيق: OpenFGA وTrivy وFalco وOpenSSF Scorecard تحت Apache-2.0، وOpenBao تحت MPL-2.0. لم يُنسخ كود أو UI من أي منها.

## الاختبارات الأمنية المضافة

أضيفت اختبارات غير تدميرية تثبت أن معرفات الطلب bounded، وأن أسماء RAG path-like مرفوضة، وأن namespace يتضمن `lab_id` من الحساب وليس من العميل، وأن المواطن لا يصل إلى AI Fabric، وأن doctor لا يرى provider inventory، وأن lockout يبدأ بعد الحد وينتهي عند نجاح الدخول أو انقضاء القفل.

## ما لم يُنفذ عمدًا

لم تُنفذ محاولات اختراق على `www.gula-platform.org` أو على أجهزة طبية أو بوابات خارجية. لم تُضف backdoor أو exploit runner أو credential harvester أو reverse shell أو persistence mechanism. كما لم يُنشر Falco host sensor أو OpenBao production cluster أو Trivy scanner على حسابات خارجية؛ هذه تكاملات تشغيلية تحتاج بيئة مملوكة وموافقة منفصلة.

## الدفعة التالية المقترحة

الأولوية التالية هي إضافة سجل ثغرات داخلي tenant-scoped مع lifecycle من الاكتشاف إلى المعالجة وإعادة الاختبار، وتوليد SBOM للإصدارات، وفحص Trivy للأصول المبنية، ومراقبة runtime على gateway داخل بيئة staging مملوكة فقط. بعد ذلك يمكن إضافة سياسات egress allowlist للموصلات الخارجية، وتوحيد كل مسارات الجلسات القديمة والجديدة خلف identity service واحد، واختبار tenant isolation للـAI clinical payloads التي تحتوي `patient_id`.

## المراجع

[1]: https://owasp.org/www-project-application-security-verification-standard/ "OWASP Application Security Verification Standard"

[2]: https://csrc.nist.gov/projects/ssdf "NIST Secure Software Development Framework"

[3]: https://www.cisa.gov/topics/cybersecurity-best-practices/healthcare "CISA Healthcare and Public Health Cybersecurity"

[4]: https://hhscyber.hhs.gov/ "HHS Cyber Gateway"

[5]: https://openfga.dev/ "OpenFGA Fine-Grained Authorization"

[6]: https://openbao.org/docs/concepts/identity/ "OpenBao Identity"

[7]: https://trivy.dev/ "Trivy Security Scanner"

[8]: https://falco.org/docs/ "Falco Runtime Security"

[9]: https://openssf.org/projects/scorecard/ "OpenSSF Scorecard"
