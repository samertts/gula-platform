# مصادر وبيانات تكلفة بيئة DR في GULA

## افتراضات Terraform من المشروع
- المنطقة: `eu-central-1` (Frankfurt)، من `terraform/environments/dr/variables.tf`.
- بيئة DR تستخدم EKS، RDS PostgreSQL، ElastiCache Redis، ALB، NAT Gateway واحد، التخزين والمراقبة والأمن.
- RDS: `db.r6g.xlarge`، تخزين 500 GiB، حد أقصى 2,000 GiB، Single-AZ، احتفاظ نسخ احتياطي 7 أيام.
- Redis: `cache.r6g.large`، عقدتان، Single-AZ، بدون cluster mode.
- EKS: عقدة نظام واحدة `m5.xlarge` on-demand، عقدتا تطبيق `m5.xlarge` on-demand، وعقدة Spot واحدة `c5.xlarge` عند الإقلاع حسب `desired_size=1`، مع قرص 50 GiB للنظام و100 GiB لكل عقدة تطبيق/Spot.
- EKS control plane: Kubernetes 1.29، وتسعير النسخة القياسية المنشور من AWS هو 0.10 دولار/ساعة.
- الشبكة: NAT Gateway واحد، وAvailability Zones عددها 2.
- ALB: واحد، مع تسعير ساعة تشغيل + LCUs + IPv4 عام.

## مصادر AWS الرسمية
1. Amazon EKS Pricing: https://aws.amazon.com/eks/pricing/
   - الرسم القياسي للعنقود: $0.10 لكل عنقود/ساعة.
   - موارد العقد وEBS وIPv4 تُحاسب منفصلة.
2. Amazon EC2 On-Demand Pricing: https://aws.amazon.com/ec2/pricing/on-demand/
   - التسعير حسب instance-hour، مع احتساب الثانية للأنظمة المدعومة وبحد أدنى 60 ثانية.
   - النقل والـEBS وIPv4 تُحاسب منفصلة.
3. Amazon RDS Pricing: https://aws.amazon.com/rds/pricing/
   - RDS تُحاسب حسب الاستخدام، والتخزين والنسخ الاحتياطية والنقل تُحاسب منفصلة.
   - النسخ المحجوزة قد تخفض التكلفة حتى 69% وفق الصفحة الرسمية، بحسب الخيار والمنطقة والالتزام.
   - النقل بين المناطق لنسخ اللقطات والنسخ الاحتياطية العابرة للمناطق قد يُحاسب.
4. Amazon ElastiCache Pricing: https://aws.amazon.com/elasticache/pricing/
   - عقد ElastiCache تُحاسب بالساعة، وReserved Nodes قد تحقق خصماً يصل إلى 48.2% (No Upfront) أو أعلى حسب الخطة.
5. Amazon VPC Pricing: https://aws.amazon.com/vpc/pricing/
   - NAT Gateway: رسم ساعة + رسم معالجة لكل GiB.
   - مثال الصفحة يستخدم $0.045/ساعة و$0.045/GiB في منطقة المثال (Ohio)، ولا ينبغي اعتباره سعر Frankfurt دون التحقق من جدول المنطقة.
   - Gateway VPC Endpoint لـS3 لا يفرض رسماً بالساعة أو معالجة، ويمكنه تقليل مرور S3 عبر NAT.
6. Elastic Load Balancing Pricing: https://aws.amazon.com/elasticloadbalancing/pricing/
   - ALB: $0.0225/ساعة في مثال US East + رسوم LCU؛ المثال ليس سعراً مؤكداً لـFrankfurt.
7. CloudWatch Pricing: https://aws.amazon.com/cloudwatch/pricing/
   - أول 5 GB من السجلات شهرياً ضمن الطبقة المجانية بحسب الصفحة، وقد توجد رسوم للسجلات والقياسات والتنبيهات ولوحات المعلومات حسب الاستخدام والمنطقة.

## ملاحظات منهجية
- الأسعار النهائية تتغير بحسب المنطقة، نوع نظام التشغيل، حجم النقل، حجم السجلات، عدد الطلبات، الضرائب، الخصومات، وSavings Plans/Reserved Instances.
- يجب استخدام AWS Pricing Calculator أو AWS Price List API بحساب AWS والمنطقة الفعلية قبل اعتماد الميزانية.
- التقدير النهائي ينبغي أن يعرض نطاقاً لا رقماً واحداً، ويفصل تكلفة الموارد الدائمة عن تكلفة النقل والبيانات والمراقبة.

## تحقق مرئي إضافي من Vantage في 19 أغسطس 2026
- صفحة Vantage لـ m5.xlarge تعرض سعر البداية العام $0.192/ساعة On-Demand و$0.066 Spot، مع خيار منطقة EU (Frankfurt) في القائمة؛ القيمة الظاهرة افتراضياً كانت US East (N. Virginia)، لذا يلزم اختيار Frankfurt صراحة قبل اعتمادها كسعر المنطقة.
- صفحة Vantage لـ db.r6g.xlarge تعرض سعر البداية العام $0.450/ساعة On-Demand و$0.260/ساعة 1-Year Reserved، مع خيارات PostgreSQL وSingle-AZ وEU (Frankfurt)؛ القيمة الظاهرة افتراضياً كانت US East (N. Virginia)، لذا لا تُستخدم كقيمة Frankfurt النهائية دون اختيار المنطقة.
- المصدر المرئي: https://instances.vantage.sh/aws/ec2/m5.xlarge و https://instances.vantage.sh/aws/rds/db.r6g.xlarge

## ملاحظة تحقق من واجهة Vantage
واجهة Vantage تعرض EU (Frankfurt) كخيار منطقة لكنها تفتح افتراضياً على US East (N. Virginia). لذلك لا يجوز نقل السعر الظاهر مباشرة إلى نموذج GULA قبل تغيير المنطقة فعلياً أو استخدام AWS Price List API/Calculator للمنطقة `eu-central-1`. صفحات التحقق: https://instances.vantage.sh/aws/ec2/m5.xlarge و https://instances.vantage.sh/aws/rds/db.r6g.xlarge

## إرشادات AWS الرسمية حول DR
- AWS Whitepaper: https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html
  يوضح أن استراتيجيات DR تمتد من النسخ والاستعادة منخفضة التكلفة إلى Active/Active الأعلى تعقيداً، وأن الاختيار يعتمد على RTO/RPO. كما يوصي بالاختبار الدوري وباستخدام IaC، ويذكر أن النسخ المتواصل وحده لا يحمي من تلف البيانات أو الحذف الخبيث دون نسخ نقطية زمنية.
- AWS Architecture Blog: https://aws.amazon.com/blogs/architecture/disaster-recovery-dr-architecture-on-aws-part-iii-pilot-light-and-warm-standby/
  يعرّف Warm Standby بأنه بيئة وظيفية منخفضة السعة تعمل دائماً ويمكنها استقبال الطلبات فوراً على مستوى منخفض ثم التوسع، بينما Pilot Light يحتاج إلى تشغيل موارد إضافية قبل استقبال الطلبات. ويؤكد أن كلا النهجين يتطلبان نسخاً احتياطية بالإضافة إلى النسخ/التكرار.
- AWS Well-Architected REL13-BP02: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_disaster_recovery.html
  يصنف Warm Standby تقريباً عند RPO بالثواني وRTO بالدقائق، مع بيئة مصغرة وظيفية في المنطقة الاحتياطية، ويذكر أن التكلفة والتعقيد يزدادان مع انخفاض RTO/RPO. كما يقترح AWS Elastic Disaster Recovery كبديل قد يحقق أهدافاً مشابهة بتكلفة Pilot Light.
