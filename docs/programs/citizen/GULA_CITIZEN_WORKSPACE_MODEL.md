# GULA Citizen Workspace Model

Citizen Workspace هو مساحة مواطنية داخل GULA application shell. يبدأ الحساب هنا بسياق المواطن الحالي، ثم يمكنه الانتقال إلى سياق child/dependent أو workspace مهني فقط إذا أثبت الخادم العلاقة والتحقق والمنظمة والصلاحيات.

عند التبديل يعيد الخادم تقييم account status، identity level، relationship، role، organization، policy، consent، entitlement، device/session، وdata scope. يمسح العميل أي cache لا يثبت صلاحيته للسياق الجديد، ويعرض current profile بوضوح.

الواجهة progressive disclosure وArabic-first، وتضم Home وMy Health وAppointments وResults وPrivacy/Security وHelp تدريجياً. لا تظهر capabilities غير المثبتة بعقد API وتفويض واختبار.
