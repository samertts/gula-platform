// Lang.jsx — language context, translations, switcher
// Languages: English (LTR), Arabic (RTL), Kurdish Sorani (RTL), Turkmen (LTR), Syriac (RTL)

const LANGS = {
  en: {
    dir: 'ltr', font: "'Poppins', sans-serif", name: 'English', code: 'EN',
    nav_main: 'Main', nav_manage: 'Manage', nav_system: 'System',
    nav_dashboard: 'Dashboard', nav_patients: 'Patients', nav_samples: 'Samples',
    nav_results: 'Results', nav_reports: 'Reports', nav_billing: 'Billing', nav_settings: 'Settings',
    nav_patient_profile: 'Patient Profile', nav_doctor_dash: 'Doctor Dashboard', nav_lab_queue: 'Lab Queue',
    search_placeholder: 'Search patients, samples…', system_online: 'System Online',
    welcome: 'Welcome back, Ahmed! 👋', welcome_sub: "Here's what's happening with your laboratory today",
    stat_patients: 'Total Patients', stat_samples: 'Samples Today',
    stat_reports: 'Reports Pending', stat_tests: 'Completed Tests', from_last_week: 'from last week',
    trends_title: 'Patient & Sample Trends', trends_sub: 'Weekly activity overview',
    status_title: 'Sample Status', status_sub: 'Distribution this week', complete: 'Complete',
    quick_title: 'Quick Actions', activity_title: 'Recent Activity',
    act_register: 'Register Patient', act_sample: 'Add Sample',
    act_report: 'Generate Report', act_download: 'Download Data',
    act1: 'Sample #S-0041 completed', act2: 'Report #R-045 pending review',
    act3: 'New patient registered', act4: 'System backup completed',
    hours_ago: 'hours ago', day_ago: '1 day ago',
    pat_title: 'Patients', pat_sub: 'total patients registered', pat_register: 'Register Patient',
    pat_search: 'Search by name or national ID…',
    col_id: 'Patient ID', col_name: 'Name', col_nid: 'National ID',
    col_phone: 'Phone', col_status: 'Status', col_tests: 'Tests',
    act_view: 'View', act_edit: 'Edit', status_active: 'Active', status_inactive: 'Inactive',
    samp_title: 'Samples', samp_sub: 'Track and manage all laboratory samples', samp_add: 'Add Sample',
    col_patient: 'Patient', col_test: 'Test', col_priority: 'Priority', col_date: 'Date',
    all: 'All', completed: 'Completed', pending: 'Pending', processing: 'Processing', failed: 'Failed',
    priority_normal: 'Normal', priority_high: 'High', act_retry: 'Retry',
    coming_soon: 'Coming soon in this prototype',
  },
  ar: {
    dir: 'rtl', font: "'Cairo', sans-serif", name: 'العربية', code: 'ع',
    nav_main: 'الرئيسية', nav_manage: 'الإدارة', nav_system: 'النظام',
    nav_dashboard: 'لوحة التحكم', nav_patients: 'المرضى', nav_samples: 'العينات',
    nav_results: 'النتائج', nav_reports: 'التقارير', nav_billing: 'الفواتير', nav_settings: 'الإعدادات',
    nav_patient_profile: 'ملف المريض', nav_doctor_dash: 'لوحة الطبيب', nav_lab_queue: 'قائمة الانتظار',
    search_placeholder: 'ابحث عن مرضى أو عينات…', system_online: 'النظام متصل',
    welcome: '!مرحباً بعودتك، أحمد 👋', welcome_sub: 'هنا ما يحدث في مختبرك اليوم',
    stat_patients: 'إجمالي المرضى', stat_samples: 'عينات اليوم',
    stat_reports: 'تقارير معلقة', stat_tests: 'فحوصات مكتملة', from_last_week: 'من الأسبوع الماضي',
    trends_title: 'اتجاهات المرضى والعينات', trends_sub: 'نظرة عامة على النشاط الأسبوعي',
    status_title: 'حالة العينات', status_sub: 'التوزيع هذا الأسبوع', complete: 'مكتمل',
    quick_title: 'إجراءات سريعة', activity_title: 'النشاط الأخير',
    act_register: 'تسجيل مريض جديد', act_sample: 'إضافة عينة',
    act_report: 'إنشاء تقرير', act_download: 'تنزيل البيانات',
    act1: 'اكتملت العينة #S-0041', act2: 'التقرير #R-045 في انتظار المراجعة',
    act3: 'تم تسجيل مريض جديد', act4: 'اكتمل النسخ الاحتياطي للنظام',
    hours_ago: 'ساعات مضت', day_ago: 'منذ يوم واحد',
    pat_title: 'المرضى', pat_sub: 'مريض مسجل إجمالاً', pat_register: 'تسجيل مريض',
    pat_search: '…ابحث بالاسم أو الهوية الوطنية',
    col_id: 'رقم المريض', col_name: 'الاسم', col_nid: 'الهوية الوطنية',
    col_phone: 'الهاتف', col_status: 'الحالة', col_tests: 'الفحوصات',
    act_view: 'عرض', act_edit: 'تعديل', status_active: 'نشط', status_inactive: 'غير نشط',
    samp_title: 'العينات', samp_sub: 'تتبع وإدارة جميع عينات المختبر', samp_add: 'إضافة عينة',
    col_patient: 'المريض', col_test: 'الفحص', col_priority: 'الأولوية', col_date: 'التاريخ',
    all: 'الكل', completed: 'مكتملة', pending: 'معلقة', processing: 'قيد المعالجة', failed: 'فاشلة',
    priority_normal: 'عادية', priority_high: 'عالية', act_retry: 'إعادة المحاولة',
    coming_soon: 'قريباً في هذا النموذج الأولي',
  },
  ku: {
    dir: 'rtl', font: "'Cairo', sans-serif", name: 'کوردی', code: 'ک',
    nav_main: 'سەرەکی', nav_manage: 'بەڕێوەبردن', nav_system: 'سیستەم',
    nav_dashboard: 'داشبۆرد', nav_patients: 'نەخۆشەکان', nav_samples: 'نموونەکان',
    nav_results: 'ئەنجامەکان', nav_reports: 'ڕاپۆرتەکان', nav_billing: 'پارەدان', nav_settings: 'ڕێکخستنەکان',
    nav_patient_profile: 'دۆسیەی نەخۆش', nav_doctor_dash: 'لوحەی دکتۆر', nav_lab_queue: 'ڕیزی چاوەڕوان',
    search_placeholder: '…گەڕان بۆ نەخۆش یان نموونە', system_online: 'سیستەم ئامادەیە',
    welcome: '!بەخێربێیتەوە، ئەحمەد 👋', welcome_sub: 'ئەمەیە ئەوەی ئەمڕۆ لە تاقیگەکەتدا دەبێت',
    stat_patients: 'کۆی نەخۆشەکان', stat_samples: 'نموونەکانی ئەمڕۆ',
    stat_reports: 'ڕاپۆرتە چاوەڕوانەکان', stat_tests: 'تاقیکردنەوەی تەواوبوو', from_last_week: 'لە هەفتەی ڕابردوو',
    trends_title: 'ئاراستەی نەخۆش و نموونە', trends_sub: 'پوختەی چالاکی هەفتانە',
    status_title: 'دۆخی نموونەکان', status_sub: 'دابەشکردن ئەم هەفتەیە', complete: 'تەواوبوو',
    quick_title: 'کردارە خێراکان', activity_title: 'چالاکیی دوایین',
    act_register: 'تۆمارکردنی نەخۆش', act_sample: 'زیادکردنی نموونە',
    act_report: 'دروستکردنی ڕاپۆرت', act_download: 'داگرتنی داتا',
    act1: 'نموونەی #S-0041 تەواو بوو', act2: 'ڕاپۆرتی #R-045 چاوەڕوانی پێداچوونەوەیە',
    act3: 'نەخۆشێکی نوێ تۆمارکرا', act4: 'پاراستنەوەی سیستەم تەواو بوو',
    hours_ago: 'کاتژمێر لەمەوبەر', day_ago: 'یەک ڕۆژ لەمەوبەر',
    pat_title: 'نەخۆشەکان', pat_sub: 'نەخۆشی تۆمارکراو کۆی گشتی', pat_register: 'تۆمارکردنی نەخۆش',
    pat_search: '…بگەڕێ بە ناو یان ناسنامەی نەتەوەیی',
    col_id: 'ناسنامەی نەخۆش', col_name: 'ناو', col_nid: 'ناسنامەی نەتەوەیی',
    col_phone: 'تەلەفۆن', col_status: 'دۆخ', col_tests: 'تاقیکردنەوەکان',
    act_view: 'بینین', act_edit: 'دەستکاری', status_active: 'چالاک', status_inactive: 'ناچالاک',
    samp_title: 'نموونەکان', samp_sub: 'شوێنکەوتن و بەڕێوەبردنی هەموو نموونەکانی تاقیگە', samp_add: 'زیادکردنی نموونە',
    col_patient: 'نەخۆش', col_test: 'تاقیکردنەوە', col_priority: 'پێشینەدان', col_date: 'بەروار',
    all: 'هەموو', completed: 'تەواوبوو', pending: 'چاوەڕوان', processing: 'پرۆسەکردن', failed: 'سەرنەکەوت',
    priority_normal: 'ئاسایی', priority_high: 'بەرز', act_retry: 'دووبارە هەوڵدان',
    coming_soon: 'بەمزووانە لەم نموونەیەدا',
  },
  tk: {
    dir: 'ltr', font: "'Poppins', sans-serif", name: 'Türkmen', code: 'TK',
    nav_main: 'Esasy', nav_manage: 'Dolandyrmak', nav_system: 'Ulgam',
    nav_dashboard: 'Dolandyryş', nav_patients: 'Näsaglar', nav_samples: 'Nusgalar',
    nav_results: 'Netijeler', nav_reports: 'Hasabatlar', nav_billing: 'Töleg', nav_settings: 'Sazlamalar',
    nav_patient_profile: 'Näsag Profili', nav_doctor_dash: 'Lukman Paneli', nav_lab_queue: 'Lab Nobaty',
    search_placeholder: 'Näsag ýa-da nusgalary gözläň…', system_online: 'Ulgam Işleýär',
    welcome: 'Hoş geldiňiz, Ahmed! 👋', welcome_sub: 'Şu gün laboratoriýaňyzda bolup geçýän zat',
    stat_patients: 'Ähli Näsaglar', stat_samples: 'Şu Günki Nusgalar',
    stat_reports: 'Garaşylýan Hasabatlar', stat_tests: 'Tamamlanan Synaglar', from_last_week: 'geçen hepdeden',
    trends_title: 'Näsag we Nusgalaryň Tendensiýasy', trends_sub: 'Hepdäniň işine genel bakış',
    status_title: 'Nusgalaryň Ýagdaýy', status_sub: 'Bu hepdäniň paýlanyşy', complete: 'Tamamlandy',
    quick_title: 'Çalt Hereketler', activity_title: 'Soňky Işler',
    act_register: 'Näsag Hasaba Al', act_sample: 'Nusgalyk Goş',
    act_report: 'Hasabat Dör', act_download: 'Maglumaty Ýükle',
    act1: '#S-0041 nusgasy tamamlandy', act2: '#R-045 hasabaty garaşýar',
    act3: 'Täze näsag hasaba alyndy', act4: 'Ulgam ätiýaçlygy tamamlandy',
    hours_ago: 'sagat öň', day_ago: '1 gün öň',
    pat_title: 'Näsaglar', pat_sub: 'jemi hasaba alnan näsag', pat_register: 'Näsag Hasaba Al',
    pat_search: 'Ady ýa-da milli ID boýunça gözläň…',
    col_id: 'Näsag ID', col_name: 'Ady', col_nid: 'Milli ID',
    col_phone: 'Telefon', col_status: 'Ýagdaý', col_tests: 'Synaglar',
    act_view: 'Gör', act_edit: 'Düzelt', status_active: 'Işjeň', status_inactive: 'Işjeň däl',
    samp_title: 'Nusgalar', samp_sub: 'Laboratoriýanyň ähli nusgalaryny yzarlaň we dolandyryň', samp_add: 'Nusgalyk Goş',
    col_patient: 'Näsag', col_test: 'Synag', col_priority: 'Ileri tutulmak', col_date: 'Senesi',
    all: 'Hemmesi', completed: 'Tamamlandy', pending: 'Garaşylýar', processing: 'Gaýtadan işlenýär', failed: 'Şowsuz',
    priority_normal: 'Adaty', priority_high: 'Ýokary', act_retry: 'Täzeden',
    coming_soon: 'Bu prototipde ýakyn wagtda',
  },
  sy: {
    dir: 'rtl', font: "'Noto Sans Syriac', serif", name: 'ܣܘܪܝܬ', code: 'ܣ',
    nav_main: 'ܪܝܫܝܐ', nav_manage: 'ܡܕܒܪܢܘܬܐ', nav_system: 'ܡܢܝܢܐ',
    nav_dashboard: 'ܠܘܚܐ ܕܒܩܘܪܝܐ', nav_patients: 'ܟܪ̈ܝܗܐ', nav_samples: 'ܢܘܣ̈ܟܐ',
    nav_results: 'ܦܐܪ̈ܐ', nav_reports: 'ܕܝܘܩ̈ܐ', nav_billing: 'ܦܪܥܐ', nav_settings: 'ܬܩܘܢܬܐ',
    nav_patient_profile: 'ܬܚܘܝܬܐ ܕܟܪܝܗܐ', nav_doctor_dash: 'ܠܘܚܐ ܕܐܣܝܐ', nav_lab_queue: 'ܛܘܪܣܐ ܕܥܘܡܪܐ',
    search_placeholder: '…ܒܩܝ ܟܪ̈ܝܗܐ ܐܘ ܢܘܣ̈ܟܐ', system_online: 'ܡܢܝܢܐ ܫܪܝܐ',
    welcome: '!ܒܪܝܟ ܬܘܒܟ ܐܚܡܕ 👋', welcome_sub: 'ܗܢܐ ܡܐ ܕܗܘܐ ܒܥܘܡܪܟ ܝܘܡܢܐ',
    stat_patients: 'ܟܠ ܟܪ̈ܝܗܐ', stat_samples: 'ܢܘܣ̈ܟܐ ܕܝܘܡܢܐ',
    stat_reports: 'ܕܝܘܩ̈ܐ ܕܣܟܝܢ', stat_tests: 'ܒܘܩ̈ܪܐ ܫܠ̈ܡܐ', from_last_week: 'ܡܢ ܫܒܘܥܐ ܕܥܒܪ',
    trends_title: 'ܡܐܙܠܬܐ ܕܟܪ̈ܝܗܐ ܘܢܘܣ̈ܟܐ', trends_sub: 'ܚܙܘܐ ܕܫܒܘܥܐ',
    status_title: 'ܐܣܝܐ ܕܢܘܣ̈ܟܐ', status_sub: 'ܦܠܓܘܬܐ ܕܫܒܘܥܐ', complete: 'ܫܠܡ',
    quick_title: 'ܦܘ̈ܠܚܢܐ ܚܡ̈ܫܐ', activity_title: 'ܦܘ̈ܠܚܢܐ ܐ̈ܚܪ̈ܝܐ',
    act_register: 'ܣܟܘܪ ܟܪܝܗܐ', act_sample: 'ܐܘܣܦ ܢܘܣܟܐ',
    act_report: 'ܥܒܕ ܕܝܘܩܐ', act_download: 'ܢܚܬ ܝܘ̈ܠܦܢܐ',
    act1: 'ܢܘܣܟܐ #S-0041 ܫܠܡ', act2: 'ܕܝܘܩܐ #R-045 ܣܟܐ ܒܘܩܪܐ',
    act3: 'ܟܪܝܗܐ ܚܕܬܐ ܣܟܝܪ', act4: 'ܢܛܪܬܐ ܕܡܢܝܢܐ ܫܠܡܬ',
    hours_ago: 'ܫ̈ܥܐ ܡܢ ܩܕܡ', day_ago: 'ܝܘܡܐ ܡܢ ܩܕܡ',
    pat_title: 'ܟܪ̈ܝܗܐ', pat_sub: 'ܟܪ̈ܝܗܐ ܣܟ̈ܝܪܐ ܒܟܠ', pat_register: 'ܣܟܘܪ ܟܪܝܗܐ',
    pat_search: '…ܒܩܝ ܒܫܡܐ ܐܘ ܗܘܝܬܐ',
    col_id: 'ܗܘܝܬܐ ܕܟܪܝܗܐ', col_name: 'ܫܡܐ', col_nid: 'ܗܘܝܬܐ ܥܡܝܐ',
    col_phone: 'ܬܠܦܘܢ', col_status: 'ܐܣܝܐ', col_tests: 'ܒܘ̈ܩܪܐ',
    act_view: 'ܚܙܝ', act_edit: 'ܫܚܠܦ', status_active: 'ܫܪܝܐ', status_inactive: 'ܠܐ ܫܪܝܐ',
    samp_title: 'ܢܘܣ̈ܟܐ', samp_sub: 'ܦܩܚ ܘܕܒܪ ܟܠ ܢܘܣ̈ܟܐ ܕܥܘܡܪܐ', samp_add: 'ܐܘܣܦ ܢܘܣܟܐ',
    col_patient: 'ܟܪܝܗܐ', col_test: 'ܒܘܩܪܐ', col_priority: 'ܩܕܡܝܘܬܐ', col_date: 'ܝܘܡܐ',
    all: 'ܟܠ', completed: 'ܫܠܡ', pending: 'ܣܟܐ', processing: 'ܡܥܒܕܢܘܬܐ', failed: 'ܠܐ ܥܒܕ',
    priority_normal: 'ܥܝܕܝ', priority_high: 'ܪܡܐ', act_retry: 'ܕܥܘ ܬܘܒ',
    coming_soon: 'ܩܪܝܒ ܒܗܢܐ ܕܡܘܬܐ',
  },
};

const LangContext = React.createContext({ lang: 'en', t: k => k, setLang: () => {} });

const LANG_ORDER = ['en', 'ar', 'ku', 'tk', 'sy'];

const langSwitcherStyles = {
  bar: {
    display: 'flex', gap: 2, background: '#F1F5F9', borderRadius: 8,
    padding: 3, flexShrink: 0,
  },
  btn: (active) => ({
    padding: '4px 10px', borderRadius: 6, fontSize: 11, fontWeight: 600,
    cursor: 'pointer', border: 'none', fontFamily: 'inherit',
    background: active ? '#fff' : 'transparent',
    color: active ? '#2563EB' : '#64748B',
    boxShadow: active ? '0 1px 3px rgb(0 0 0 / 0.1)' : 'none',
    transition: 'all 0.15s',
    minWidth: 30, textAlign: 'center',
  }),
};

function LangSwitcher({ lang, setLang }) {
  return (
    <div style={langSwitcherStyles.bar}>
      {LANG_ORDER.map(code => (
        <button
          key={code}
          style={langSwitcherStyles.btn(lang === code)}
          onClick={() => setLang(code)}
          title={LANGS[code].name}
        >
          {LANGS[code].code}
        </button>
      ))}
    </div>
  );
}

Object.assign(window, { LANGS, LangContext, LangSwitcher, LANG_ORDER });
