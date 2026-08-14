
## مراجع معمارية الربط الوطني

- **IHE HIE White Paper، الإصدار 2.2 (2024):** يميز بين نماذج Push، وCentralized Discovery and Retrieve، وFederated Discovery and Retrieve. كما يقرر أن الحوكمة يجب أن تغطي صيغة المحتوى، الترميز، البيانات الوصفية، إدارة هوية المريض، تعريف الشركاء، الخصوصية، الأمان، والتراخيص. المرجع: https://profiles.ihe.net/ITI/HIE-Whitepaper/index.html
- **HL7 FHIR R4، الإصدار 4.0.1:** يضم طبقات Conformance مثل StructureDefinition وCapabilityStatement وImplementationGuide، وأقسام Security/Privacy وConsent وProvenance وAuditEvent، إضافة إلى REST API وSearch وموارد الإدارة مثل Patient وPractitioner وOrganization وLocation، وموارد التشخيص مثل Observation وDiagnosticReport وSpecimen، وموارد الدفع مثل Coverage وClaim. المرجع: https://www.hl7.org/fhir/R4/

### دلالة تنفيذية أولية

الأنسب للعراق هو نموذج هجين: بوابة وطنية للسياسات والفهرسة والهوية والتدقيق، مع إبقاء السجلات التفصيلية داخل المستشفيات أو مستودعاتها الإقليمية. تُستخدم CapabilityStatement وImplementationGuide كعقد إلزامية، ويُسمح بالتدرج من Bundle/Document للتبادل الأولي إلى RESTful APIs للاستعلام الانتقائي، مع بوابات في المؤسسات ذات الشبكات غير المستقرة.

- **WHO Digital Health:** تربط الاستراتيجية العالمية للصحة الرقمية 2020–2027 توسيع الأثر الصحي بالحوكمة والبنية التحتية والقدرات والتقييم، وليس بالتقنية وحدها. المرجع: https://www.who.int/health-topics/digital-health
- **SMART App Launch v2.2.0 على FHIR R4:** يعرّف اكتشاف قدرات الخادم عبر `.well-known/smart-configuration`، ونمطين للتفويض: تطبيقات بواجهة مستخدم وBackend Services، ومصادقة مفضلة بالمفتاح غير المتماثل private-key JWT، مع scopes دقيقة مثل `user/Encounter.rs` و`system/Encounter.rs`. المرجع: https://hl7.org/fhir/smart-app-launch/

### دلالة تنفيذية إضافية

يجب فصل هوية المؤسسة عن هوية المستخدم، وإصدار صلاحيات قصيرة العمر ومحددة المورد والغرض. الربط بين المستشفيات سيكون عبر Backend Services مع شهادات ومفاتيح مدارة مركزياً، بينما تطبيقات الأطباء والمراجعين تستخدم SMART App Launch بعد موافقة مناسبة.

- **IHE MHD:** يقدم واجهة FHIR R4 مبسطة لمشاركة الوثائق الطبية، وتدعم النشر والاستعلام واسترجاع الوثائق عبر DocumentReference، ويمكن استخدامها كواجهة فوق XDS أو XCA، مع معاملات ITI-65 إلى ITI-68 وITI-105. المرجع: https://profiles.ihe.net/ITI/MHD/index.html
- **IHE PIXm:** يعرّف معاملات RESTful لإنشاء وتحديث وحذف سجلات المرضى في مدير cross-reference والاستعلام عن معرفات المريض عبر المجالات، ويتضمن ITI-83 للاستعلام وITI-104 لتغذية هوية المريض. المرجع: https://profiles.ihe.net/ITI/PIXm/index.html

### دلالة تنفيذية

يجب ألا تعتمد الشبكة الوطنية على رقم ملف المستشفى وحده. يلزم Master Patient Index مركزي أو اتحادي، مع احتفاظ كل مؤسسة بمعرفها المحلي وربطه بمعرف وطني بعد مطابقة حذرة ومراجعة بشرية للحالات الملتبسة. ويُفضّل بدء تبادل التقارير عبر MHD قبل فتح استعلامات سريرية واسعة.

- **IHE ATNA:** يضع العناصر الأساسية للأنظمة الآمنة: مصادقة العقد، مصادقة المستخدم، تسجيل الأحداث، وتشفير الاتصالات، مع الإشارة إلى التحكم بالوصول وتقييد الامتيازات. يشترط تسجيل الأحداث المتعلقة بالنشاط والمعاملات، ويدعم مستودع تدقيق مركزي أو اتحادي، وقد تم تحديثه ليتضمن FHIR AuditEvent وعمليات البحث فيه عبر RESTful ATNA. المرجع: https://profiles.ihe.net/ITI/TF/Volume1/ch-9.html

### دلالة تنفيذية

كل مستشفى يجب أن يتعامل كـSecure Node أو Secure Application، وكل بوابة تكامل تسجل عمليات القراءة والكتابة والتصدير والفشل والموافقة. لا يكفي تسجيل الطلبات في التطبيق؛ يجب تجميع سجل تدقيق مركزي مقاوم للعبث مع صلاحيات وصول وتحليل منفصلين.

## تفاصيل التشغيل العملي لـMHD وPIXm

- **MHD v4.2.5-comment على FHIR R4:** الأدوار الأساسية هي Document Source وDocument Consumer وDocument Responder، مع Document Recipient في سيناريوهات التسليم. المعاملات ذات الصلة: ITI-65 Provide Document Bundle للنشر، ITI-66 Find Document Lists، ITI-67 Find Document References، وITI-68 Retrieve Document. المرجع: https://profiles.ihe.net/ITI/MHD/1331_actors_and_transactions.html
- **PIXm v3.1.0 على FHIR R4:** يوفر معاملات RESTful لإنشاء وتحديث وحذف سجلات المرضى في Patient Identifier Cross-reference Manager والاستعلام عن المعرفات المتقاطعة. المعاملتان المحوريتان هما ITI-104 Patient Identity Feed FHIR وITI-83 Mobile Patient Identifier Cross-reference Query. لا يفرض PIXm خوارزمية المطابقة نفسها؛ إذ تبقى خوارزميات المطابقة وسياسات إدارة السجل الذهبي ضمن مسؤولية الجهة المالكة لـCross-reference Manager. المرجع: https://profiles.ihe.net/ITI/PIXm/volume-1.html

### دلالة تنفيذية

يُسجّل كل مستشفى كمجال هوية Patient Identifier Domain ومصدر هوية Patient Identity Source، ويرسل تغييرات المرضى إلى PIXm Manager عبر ITI-104. عند الإحالة أو البحث، يستعلم النظام المستهلك عبر ITI-83 ويستخدم المعرف المحلي المرتبط بالمؤسسة المستهدفة. لا ينبغي اعتبار نتيجة المطابقة الآلية حقيقة نهائية في الحالات الملتبسة؛ يجب توفير قائمة مراجعة بشرية ومسار دمج/فك دمج موثق.
