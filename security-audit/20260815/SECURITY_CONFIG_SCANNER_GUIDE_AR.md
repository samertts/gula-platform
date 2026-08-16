# دليل ماسح أمن التكوين والبنية التحتية

## الغرض

الملف `scripts/security_scan_config.py` هو ماسح محلي deterministic لملفات YAML وJSON وTOML وTerraform وDocker وKubernetes وGitHub Actions. لا ينفذ التكوين، ولا يتصل بالشبكة، ولا يطبع قيمة سرية كاملة.

## التشغيل المحلي

من جذر المستودع:

```bash
python3 scripts/security_scan_config.py . --fail-on HIGH
```

لحفظ تقرير JSON منقح:

```bash
python3 scripts/security_scan_config.py . \
  --fail-on HIGH \
  --json security-audit/ci/security-config-findings.json
```

يُرجع البرنامج exit code يساوي `1` إذا وجد finding بدرجة مساوية أو أعلى من `--fail-on`. يمكن استخدام `--fail-on CRITICAL` في مرحلة الإنذار التدريجي، لكن لا ينبغي استخدامه لقبول الإنتاج دون مراجعة جميع Findings الأقل.

## ما يفحصه

يفحص الماسح الأسرار الظاهرة، المفاتيح الخاصة، AWS/GitHub/JWT-like tokens، قيم password/secret/token/api-key، HTTP غير المحلي، الصور غير المثبتة على `latest`، الحاويات privileged، hostPath، service-account token التلقائي، Actions غير المثبتة على commit SHA، الأوامر mutating، wildcard bind، أخطاء JSON/TOML، الملفات غير UTF-8، والحجم الزائد.

تُستثنى مجلدات `.git` و`node_modules` و`dist` و`build` و`__pycache__` و`.pytest_cache` و`readiness-evidence` و`security-audit` حتى لا تتحول artifacts والتقارير إلى نتائج زائفة.

## دمج CI

أُضيف workflow مستقل باسم `security-config-scan.yml` يعمل على Pull Requests وعلى `main` و`develop`. يستخدم Actions مثبتة على commit SHA، أقل صلاحية `contents: read`، و`persist-credentials: false`. تُرفع النتائج المنقحة فقط عند الفشل وبمدة احتفاظ سبعة أيام.

## تفسير النتائج

| الدرجة | المعنى | الإجراء |
|---|---|---|
| `CRITICAL` | سر مكشوف أو privileged container | إيقاف فوري ومعالجة قبل أي merge أو نشر |
| `HIGH` | HTTP غير آمن، latest image، hostPath، Action غير مثبت أو service-account token | يمنع Go حتى يراجع ويغلق أو يُقبل رسمياً |
| `MEDIUM` | wildcard bind أو إعداد يحتاج تبريراً بيئياً | يعالج أو يُقيد بملف بيئة واضح |
| `LOW` | ملاحظة تحسين | تدخل في backlog ولا تُستخدم وحدها لاتخاذ قرار Go |

في التشغيل الأول داخل GULA، ظهر عدد كبير من النتائج في ملفات Docker/Kubernetes وdev overlays. هذه النتائج **ليست دليلاً على أن كل ملف مصاب بثغرة مؤكدة**؛ بعضها policy findings يحتاج تصنيفاً حسب البيئة، مثل HTTP المحلي في dev أو bind المطلوب في شبكة داخلية. يجب معالجة الصور غير المثبتة، الأسرار الحقيقية، privileged، وHTTP غير المحلي في manifests القابلة للنشر قبل قبول Production.

## حدود الماسح

لا يكشف الماسح SSRF runtime، أو tenant isolation، أو أخطاء صلاحيات قواعد البيانات، أو ثغرات NID/payment، أو سلامة TLS الفعلية، أو مشاكل Kubernetes admission، أو malware داخل الملفات الثنائية. لذلك لا يحل محل `semgrep` أو `trivy` أو `checkov` أو Pentest مرخص أو اختبارات Staging متعددة العمال.

> لا تُخزن الأسرار في المستودع أو في تقرير JSON. استخدم GitHub Environment/Vault، وراجع artifacts قبل مشاركتها خارج فريق الأمن.
