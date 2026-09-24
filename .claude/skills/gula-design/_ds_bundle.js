/* @ds-bundle: {"format":4,"namespace":"GULADesignSystem_019dd3","components":[],"sourceHashes":{"ui_kits/dashboard/App.jsx":"419b27f3a494","ui_kits/dashboard/BillingView.jsx":"b5ea0ae22fc3","ui_kits/dashboard/DashboardView.jsx":"3d6132d3c3a9","ui_kits/dashboard/DoctorDashView.jsx":"830b459c6401","ui_kits/dashboard/LabQueueView.jsx":"09b4a47478ac","ui_kits/dashboard/Lang.jsx":"16a8446cc8cb","ui_kits/dashboard/PatientProfileView.jsx":"b9642bff8d54","ui_kits/dashboard/PatientsView.jsx":"6bda770563f8","ui_kits/dashboard/ReportsView.jsx":"3f311c917780","ui_kits/dashboard/ResultsView.jsx":"ab399c7cd7cf","ui_kits/dashboard/SamplesView.jsx":"8dacb3409057","ui_kits/dashboard/Sidebar.jsx":"fa7e0df564bc","ui_kits/dashboard/TopBar.jsx":"95d08d1bd21b"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.GULADesignSystem_019dd3 = window.GULADesignSystem_019dd3 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// ui_kits/dashboard/App.jsx
try { (() => {
// App.jsx — GULA Platform root (multilingual + dark mode)
const {
  useState,
  useMemo
} = React;
function SettingsView({
  dark,
  setDark
}) {
  const {
    t,
    lang
  } = React.useContext(LangContext);
  const cfg = LANGS[lang];
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 28,
      flex: 1,
      overflowY: 'auto',
      fontFamily: cfg.font,
      direction: cfg.dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1,
      marginBottom: 24
    }
  }, t('nav_settings')), /*#__PURE__*/React.createElement("div", {
    style: {
      background: surface,
      borderRadius: 12,
      padding: 20,
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)',
      border: dark ? `1px solid ${border}` : 'none',
      maxWidth: 480
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: fg1,
      marginBottom: 16
    }
  }, "Appearance"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 0',
      borderBottom: `1px solid ${border}`
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: fg1
    }
  }, "Dark Mode"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2,
      marginTop: 2
    }
  }, "Switch between light and dark interface")), /*#__PURE__*/React.createElement("div", {
    onClick: () => setDark(d => !d),
    style: {
      width: 44,
      height: 24,
      borderRadius: 12,
      cursor: 'pointer',
      background: dark ? '#2563EB' : '#E2E8F0',
      position: 'relative',
      transition: 'background 0.2s',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 18,
      height: 18,
      borderRadius: '50%',
      background: '#fff',
      position: 'absolute',
      top: 3,
      left: dark ? 23 : 3,
      transition: 'left 0.2s',
      boxShadow: '0 1px 3px rgb(0 0 0/.2)'
    }
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '12px 0'
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: fg1
    }
  }, "Language"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2,
      marginTop: 2
    }
  }, "EN / \u0639 / \u06A9 / TK / \u0723 \u2014 switch in the top bar")))));
}
function App() {
  const [page, setPage] = useState('dashboard');
  const [lang, setLang] = useState(() => localStorage.getItem('gula_lang') || 'en');
  const [dark, setDark] = useState(() => localStorage.getItem('gula_dark') === 'true');

  // Persist preferences
  React.useEffect(() => {
    localStorage.setItem('gula_dark', dark);
  }, [dark]);
  React.useEffect(() => {
    localStorage.setItem('gula_lang', lang);
  }, [lang]);
  const ctxValue = useMemo(() => ({
    lang,
    setLang,
    t: key => LANGS[lang] && LANGS[lang][key] || key
  }), [lang]);
  const cfg = LANGS[lang];
  const isRtl = cfg.dir === 'rtl';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const side = dark ? '#1E293B' : '#fff';
  const sideBorder = dark ? '1px solid #334155' : undefined;
  const renderView = () => {
    if (page === 'dashboard') return /*#__PURE__*/React.createElement(DashboardView, {
      dark: dark
    });
    if (page === 'patients') return /*#__PURE__*/React.createElement(PatientsView, {
      dark: dark
    });
    if (page === 'samples') return /*#__PURE__*/React.createElement(SamplesView, {
      dark: dark
    });
    if (page === 'results') return /*#__PURE__*/React.createElement(ResultsView, {
      dark: dark
    });
    if (page === 'reports') return /*#__PURE__*/React.createElement(ReportsView, {
      dark: dark
    });
    if (page === 'billing') return /*#__PURE__*/React.createElement(BillingView, {
      dark: dark
    });
    if (page === 'patient_profile') return /*#__PURE__*/React.createElement(PatientProfileView, {
      dark: dark
    });
    if (page === 'doctor_dash') return /*#__PURE__*/React.createElement(DoctorDashView, {
      dark: dark
    });
    if (page === 'lab_queue') return /*#__PURE__*/React.createElement(LabQueueView, {
      dark: dark
    });
    if (page === 'settings') return /*#__PURE__*/React.createElement(SettingsView, {
      dark: dark,
      setDark: setDark
    });
    return null;
  };
  return /*#__PURE__*/React.createElement(LangContext.Provider, {
    value: ctxValue
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      height: '100vh',
      overflow: 'hidden',
      flexDirection: isRtl ? 'row-reverse' : 'row',
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: side,
      borderRight: !isRtl ? dark ? '1px solid #334155' : '1px solid #E2E8F0' : undefined,
      borderLeft: isRtl ? dark ? '1px solid #334155' : '1px solid #E2E8F0' : undefined
    }
  }, /*#__PURE__*/React.createElement(Sidebar, {
    active: page,
    onNavigate: setPage,
    dark: dark
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(TopBar, {
    page: page,
    lang: lang,
    setLang: setLang,
    dark: dark,
    setDark: setDark
  }), renderView())));
}
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(/*#__PURE__*/React.createElement(App, null));
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/App.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/BillingView.jsx
try { (() => {
// BillingView.jsx — Billing screen (multilingual)
const {
  useContext: useCtxB
} = React;
const INVOICES = [{
  id: 'INV-2026-041',
  patient: 'Ahmed Al-Rashidi',
  tests: ['CBC', 'Lipid Panel'],
  amount: 75000,
  currency: 'IQD',
  statusKey: 'completed',
  date: 'Apr 28, 2026'
}, {
  id: 'INV-2026-042',
  patient: 'Sara Khalil',
  tests: ['Thyroid Panel'],
  amount: 45000,
  currency: 'IQD',
  statusKey: 'pending',
  date: 'Apr 27, 2026'
}, {
  id: 'INV-2026-043',
  patient: 'Omar Hassan',
  tests: ['Urine Culture', 'HbA1c'],
  amount: 90000,
  currency: 'IQD',
  statusKey: 'completed',
  date: 'Apr 26, 2026'
}, {
  id: 'INV-2026-044',
  patient: 'Fatima Al-Amiri',
  tests: ['CBC', 'CMP'],
  amount: 60000,
  currency: 'IQD',
  statusKey: 'failed',
  date: 'Apr 25, 2026'
}, {
  id: 'INV-2026-045',
  patient: 'Kareem Saleh',
  tests: ['Testosterone'],
  amount: 35000,
  currency: 'IQD',
  statusKey: 'pending',
  date: 'Apr 24, 2026'
}];
const BILL_STATUS = {
  completed: {
    bg: '#DCFCE7',
    color: '#15803D',
    dot: '#10B981',
    label: 'Paid'
  },
  pending: {
    bg: '#FEF9C3',
    color: '#A16207',
    dot: '#F59E0B',
    label: 'Unpaid'
  },
  failed: {
    bg: '#FEE2E2',
    color: '#B91C1C',
    dot: '#EF4444',
    label: 'Overdue'
  }
};
function BillingView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxB(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const rowAlt = dark ? '#1A2744' : '#FAFBFC';
  const total = INVOICES.reduce((s, i) => s + i.amount, 0);
  const paid = INVOICES.filter(i => i.statusKey === 'completed').reduce((s, i) => s + i.amount, 0);
  const unpaid = INVOICES.filter(i => i.statusKey !== 'completed').reduce((s, i) => s + i.amount, 0);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 28,
      overflowY: 'auto',
      flex: 1,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1
    }
  }, t('nav_billing')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: fg2,
      marginTop: 2
    }
  }, INVOICES.length, " invoices this month")), /*#__PURE__*/React.createElement("button", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '8px 16px',
      borderRadius: 8,
      border: 'none',
      background: '#2563EB',
      color: '#fff',
      fontSize: 13,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: cfg.font
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "5",
    x2: "12",
    y2: "19"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "5",
    y1: "12",
    x2: "19",
    y2: "12"
  })), "New Invoice")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3,1fr)',
      gap: 14,
      marginBottom: 24
    }
  }, [{
    label: 'Total Revenue',
    value: `${(total / 1000).toFixed(0)}K IQD`,
    color: '#3B82F6'
  }, {
    label: 'Collected',
    value: `${(paid / 1000).toFixed(0)}K IQD`,
    color: '#10B981'
  }, {
    label: 'Outstanding',
    value: `${(unpaid / 1000).toFixed(0)}K IQD`,
    color: '#F59E0B'
  }].map(s => /*#__PURE__*/React.createElement("div", {
    key: s.label,
    style: {
      background: surface,
      borderRadius: 12,
      padding: '18px 20px',
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)',
      border: dark ? `1px solid ${border}` : 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2,
      fontWeight: 500,
      marginBottom: 6
    }
  }, s.label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 24,
      fontWeight: 700,
      color: s.color
    }
  }, s.value)))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: surface,
      borderRadius: 12,
      overflow: 'hidden',
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)',
      border: dark ? `1px solid ${border}` : 'none'
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse'
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
    style: {
      background: dark ? '#1A2744' : '#F8FAFC',
      borderBottom: `1.5px solid ${border}`
    }
  }, ['Invoice', 'Patient', 'Tests', 'Amount', 'Status', 'Date', ''].map((h, i) => /*#__PURE__*/React.createElement("th", {
    key: i,
    style: {
      padding: '10px 16px',
      textAlign: isRtl ? 'right' : 'left',
      fontSize: 11,
      fontWeight: 600,
      color: fg2,
      textTransform: 'uppercase',
      letterSpacing: '0.06em'
    }
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, INVOICES.map((inv, i) => {
    const bs = BILL_STATUS[inv.statusKey];
    return /*#__PURE__*/React.createElement("tr", {
      key: inv.id,
      style: {
        background: i % 2 === 0 ? surface : rowAlt
      }
    }, /*#__PURE__*/React.createElement("td", {
      style: {
        padding: '13px 16px',
        color: '#2563EB',
        fontWeight: 600,
        fontSize: 12,
        borderBottom: `1px solid ${border}`,
        textAlign: isRtl ? 'right' : 'left'
      }
    }, inv.id), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: '13px 16px',
        fontSize: 13,
        color: fg1,
        borderBottom: `1px solid ${border}`,
        textAlign: isRtl ? 'right' : 'left'
      }
    }, inv.patient), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: '13px 16px',
        fontSize: 12,
        color: fg2,
        borderBottom: `1px solid ${border}`,
        textAlign: isRtl ? 'right' : 'left'
      }
    }, inv.tests.join(', ')), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: '13px 16px',
        fontSize: 13,
        fontWeight: 700,
        color: fg1,
        borderBottom: `1px solid ${border}`,
        textAlign: isRtl ? 'right' : 'left'
      }
    }, inv.amount.toLocaleString(), " ", inv.currency), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: '13px 16px',
        borderBottom: `1px solid ${border}`,
        textAlign: isRtl ? 'right' : 'left'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '3px 10px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 600,
        background: bs.bg,
        color: bs.color
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: bs.dot
      }
    }), bs.label)), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: '13px 16px',
        fontSize: 12,
        color: fg2,
        borderBottom: `1px solid ${border}`,
        textAlign: isRtl ? 'right' : 'left'
      }
    }, inv.date), /*#__PURE__*/React.createElement("td", {
      style: {
        padding: '13px 16px',
        borderBottom: `1px solid ${border}`
      }
    }, /*#__PURE__*/React.createElement("button", {
      style: {
        background: 'none',
        border: 'none',
        fontSize: 12,
        fontWeight: 500,
        color: '#2563EB',
        cursor: 'pointer',
        fontFamily: cfg.font
      }
    }, t('act_view'))));
  })))));
}
Object.assign(window, {
  BillingView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/BillingView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/DashboardView.jsx
try { (() => {
// DashboardView.jsx — main dashboard (multilingual)
const {
  useContext: useCtxDash
} = React;
const dashStyles = {
  page: {
    padding: 28,
    overflowY: 'auto',
    flex: 1
  },
  welcome: {
    marginBottom: 24
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 700,
    color: '#0F172A',
    letterSpacing: '-0.01em'
  },
  welcomeSub: {
    fontSize: 13,
    color: '#64748B',
    marginTop: 4
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 16,
    marginBottom: 24
  },
  chartsGrid: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gap: 16,
    marginBottom: 24
  },
  bottomGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 16
  },
  card: {
    background: '#fff',
    borderRadius: 12,
    padding: 20,
    boxShadow: '0 1px 3px rgb(0 0 0/.07)'
  },
  cardTitle: {
    fontSize: 13,
    fontWeight: 600,
    color: '#0F172A',
    marginBottom: 2
  },
  cardSub: {
    fontSize: 11,
    color: '#94A3B8',
    marginBottom: 14
  },
  statTop: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 10
  },
  statLabel: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: 500,
    marginBottom: 4
  },
  statValue: {
    fontSize: 28,
    fontWeight: 700,
    color: '#0F172A',
    lineHeight: 1
  },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: 9,
    flexShrink: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  }
};
const STAT_ICONS = [{
  key: 'stat_patients',
  color: '#3B82F6',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "18",
    height: "18",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "9",
    cy: "7",
    r: "4"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M23 21v-2a4 4 0 0 0-3-3.87"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M16 3.13a4 4 0 0 1 0 7.75"
  })),
  value: '1,234',
  change: '+12%',
  positive: true
}, {
  key: 'stat_samples',
  color: '#8B5CF6',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "18",
    height: "18",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"
  })),
  value: '87',
  change: '+8%',
  positive: true
}, {
  key: 'stat_reports',
  color: '#F97316',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "18",
    height: "18",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "10"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "8",
    x2: "12",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "16",
    x2: "12.01",
    y2: "16"
  })),
  value: '23',
  change: '-5%',
  positive: false
}, {
  key: 'stat_tests',
  color: '#10B981',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "18",
    height: "18",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "20 6 9 17 4 12"
  })),
  value: '456',
  change: '+15%',
  positive: true
}];
const ACTIVITY_KEYS = [{
  actKey: 'act1',
  color: '#10B981',
  timeKey: 'hours_ago',
  timeVal: '2',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "13",
    height: "13",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "20 6 9 17 4 12"
  }))
}, {
  actKey: 'act2',
  color: '#F97316',
  timeKey: 'hours_ago',
  timeVal: '4',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "13",
    height: "13",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "10"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "8",
    x2: "12",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "16",
    x2: "12.01",
    y2: "16"
  }))
}, {
  actKey: 'act3',
  color: '#3B82F6',
  timeKey: 'hours_ago',
  timeVal: '6',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "13",
    height: "13",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "9",
    cy: "7",
    r: "4"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "19",
    y1: "8",
    x2: "19",
    y2: "14"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "22",
    y1: "11",
    x2: "16",
    y2: "11"
  }))
}, {
  actKey: 'act4',
  color: '#8B5CF6',
  timeKey: 'day_ago',
  timeVal: '',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "13",
    height: "13",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "22 12 18 12 15 21 9 3 6 12 2 12"
  }))
}];
const QUICK_KEYS = [{
  key: 'act_register',
  color: '#2563EB',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "5",
    x2: "12",
    y2: "19"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "5",
    y1: "12",
    x2: "19",
    y2: "12"
  }))
}, {
  key: 'act_sample',
  color: '#8B5CF6',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"
  }))
}, {
  key: 'act_report',
  color: '#10B981',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "14 2 14 8 20 8"
  }))
}, {
  key: 'act_download',
  color: '#F97316',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "7 10 12 15 17 10"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "15",
    x2: "12",
    y2: "3"
  }))
}];
function MiniBarChart() {
  const bars = [24, 28, 32, 26, 35, 20, 18];
  const samp = [12, 15, 18, 14, 22, 10, 8];
  const days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
  const max = 40;
  const h = 90;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      alignItems: 'flex-end',
      height: h + 22
    }
  }, bars.map((b, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 2,
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 2,
      alignItems: 'flex-end',
      height: h
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 10,
      height: b / max * h,
      background: '#3B82F6',
      borderRadius: '3px 3px 0 0'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 10,
      height: samp[i] / max * h,
      background: '#C4B5FD',
      borderRadius: '3px 3px 0 0'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 9,
      color: '#94A3B8',
      fontWeight: 500
    }
  }, days[i]))));
}
function DonutChart({
  t
}) {
  const data = [{
    labelKey: 'completed',
    value: 65,
    color: '#10B981'
  }, {
    labelKey: 'pending',
    value: 25,
    color: '#F59E0B'
  }, {
    labelKey: 'failed',
    value: 10,
    color: '#EF4444'
  }];
  const total = 100;
  const r = 36;
  const cx = 50;
  const cy = 50;
  const stroke = 16;
  const circ = 2 * Math.PI * r;
  let offset = 0;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 100 100",
    width: "86",
    height: "86"
  }, data.map((d, i) => {
    const dash = d.value / total * circ;
    const rot = offset / total * 360 - 90;
    offset += d.value;
    return /*#__PURE__*/React.createElement("circle", {
      key: i,
      cx: cx,
      cy: cy,
      r: r,
      fill: "none",
      stroke: d.color,
      strokeWidth: stroke,
      strokeDasharray: `${dash} ${circ - dash}`,
      transform: `rotate(${rot} ${cx} ${cy})`
    });
  }), /*#__PURE__*/React.createElement("text", {
    x: cx,
    y: cy - 4,
    textAnchor: "middle",
    fontSize: "13",
    fontWeight: "700",
    fill: "#0F172A",
    fontFamily: "Poppins"
  }, "65%"), /*#__PURE__*/React.createElement("text", {
    x: cx,
    y: cy + 10,
    textAnchor: "middle",
    fontSize: "8",
    fill: "#94A3B8",
    fontFamily: "Poppins"
  }, t('complete'))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 7
    }
  }, data.map(d => /*#__PURE__*/React.createElement("div", {
    key: d.labelKey,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 7
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: 2,
      background: d.color,
      flexShrink: 0
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: '#475569',
      fontWeight: 500
    }
  }, t(d.labelKey)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: '#0F172A',
      fontWeight: 600,
      marginLeft: 'auto'
    }
  }, d.value, "%")))));
}
function DashboardView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxDash(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const cardBg = dark ? '#1E293B' : '#fff';
  const pageBg = dark ? '#0F172A' : '#F8FAFC';
  const style = {
    fontFamily: cfg.font,
    direction: dir,
    background: pageBg
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.page,
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: dashStyles.welcome
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.welcomeTitle,
      color: fg1
    }
  }, t('welcome')), /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.welcomeSub,
      color: fg2
    }
  }, t('welcome_sub'))), /*#__PURE__*/React.createElement("div", {
    style: dashStyles.statsGrid
  }, STAT_ICONS.map(s => /*#__PURE__*/React.createElement("div", {
    key: s.key,
    style: {
      ...dashStyles.card,
      background: cardBg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: dashStyles.statTop
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.statLabel,
      color: fg2
    }
  }, t(s.key)), /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.statValue,
      color: fg1
    }
  }, s.value)), /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.iconBox,
      background: s.color
    }
  }, s.icon)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 500,
      color: s.positive ? '#10B981' : '#EF4444'
    }
  }, s.change, " ", t('from_last_week'))))), /*#__PURE__*/React.createElement("div", {
    style: dashStyles.chartsGrid
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.card,
      background: cardBg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.cardTitle,
      color: fg1
    }
  }, t('trends_title')), /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.cardSub,
      color: fg2
    }
  }, t('trends_sub')), /*#__PURE__*/React.createElement(MiniBarChart, null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 14,
      marginTop: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      fontSize: 11,
      color: '#475569'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 12,
      height: 4,
      background: '#3B82F6',
      borderRadius: 2
    }
  }), t('nav_patients')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 5,
      fontSize: 11,
      color: '#475569'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 12,
      height: 4,
      background: '#C4B5FD',
      borderRadius: 2
    }
  }), t('nav_samples')))), /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.card,
      background: cardBg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.cardTitle,
      color: fg1
    }
  }, t('status_title')), /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.cardSub,
      color: fg2
    }
  }, t('status_sub')), /*#__PURE__*/React.createElement(DonutChart, {
    t: t
  }))), /*#__PURE__*/React.createElement("div", {
    style: dashStyles.bottomGrid
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.card,
      background: cardBg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.cardTitle,
      color: fg1
    }
  }, t('quick_title')), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14,
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }
  }, QUICK_KEYS.map(a => /*#__PURE__*/React.createElement("button", {
    key: a.key,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '9px 12px',
      borderRadius: 8,
      border: '1.5px solid #E2E8F0',
      background: cardBg,
      cursor: 'pointer',
      fontFamily: cfg.font,
      fontSize: 13,
      fontWeight: 500,
      color: '#0F172A',
      textAlign: dir === 'rtl' ? 'right' : 'left',
      direction: dir
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 28,
      height: 28,
      borderRadius: 7,
      background: a.color + '18',
      color: a.color,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, a.icon), t(a.key))))), /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.card,
      background: cardBg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      ...dashStyles.cardTitle,
      color: fg1
    }
  }, t('activity_title')), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 14
    }
  }, ACTIVITY_KEYS.map((a, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '10px 0',
      borderBottom: i < ACTIVITY_KEYS.length - 1 ? '1px solid #F1F5F9' : 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 28,
      height: 28,
      borderRadius: 7,
      background: a.color,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, a.icon), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 500,
      color: fg1
    }
  }, t(a.actKey)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2,
      marginTop: 1
    }
  }, a.timeVal ? `${a.timeVal} ${t(a.timeKey)}` : t(a.timeKey)))))))));
}
Object.assign(window, {
  DashboardView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/DashboardView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/DoctorDashView.jsx
try { (() => {
// DoctorDashView.jsx — Doctor dashboard with alerts + pending approvals (multilingual)
const {
  useContext: useCtxDD
} = React;
const CRITICAL_ALERTS = [{
  id: 'R-0101',
  patient_ar: 'أحمد حسن',
  patient_en: 'Ahmed Hassan',
  test: 'Hemoglobin',
  value: '9.2 g/dL',
  flag: 'Critical Low',
  time: '10 min ago'
}, {
  id: 'R-0103',
  patient_ar: 'عمر جاسم',
  patient_en: 'Omar Jasim',
  test: 'WBC Count',
  value: '12.8 ×10³/µL',
  flag: 'Critical High',
  time: '25 min ago'
}, {
  id: 'R-0105',
  patient_ar: 'كريم صالح',
  patient_en: 'Kareem Saleh',
  test: 'HbA1c',
  value: '8.4%',
  flag: 'High',
  time: '1 hr ago'
}];
const PENDING = [{
  id: 'R-0102',
  patient_ar: 'سارة خالد',
  patient_en: 'Sara Khalid',
  test: 'Lipid Panel',
  time: 'Awaiting 2h'
}, {
  id: 'R-0104',
  patient_ar: 'فاطمة علي',
  patient_en: 'Fatima Ali',
  test: 'TSH',
  time: 'Awaiting 4h'
}, {
  id: 'R-0106',
  patient_ar: 'نور أحمد',
  patient_en: 'Nour Ahmed',
  test: 'Platelets',
  time: 'Awaiting 6h'
}];
function DoctorDashView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxDD(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const surface = dark ? '#1E293B' : '#fff';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const isRtl = dir === 'rtl';
  const patName = item => lang === 'ar' || lang === 'ku' || lang === 'sy' ? item.patient_ar : item.patient_en;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 28,
      overflowY: 'auto',
      flex: 1,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1,
      marginBottom: 4
    }
  }, t('nav_doctor_dash')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: fg2,
      marginBottom: 20
    }
  }, "Dr. Samer Al-Rashidi \xB7 April 28, 2026"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 14,
      marginBottom: 22
    }
  }, [{
    label: 'My Patients',
    value: '34',
    color: '#3B82F6'
  }, {
    label: 'Critical Alerts',
    value: CRITICAL_ALERTS.length.toString(),
    color: '#EF4444'
  }, {
    label: 'Pending Review',
    value: PENDING.length.toString(),
    color: '#F59E0B'
  }, {
    label: 'Approved Today',
    value: '12',
    color: '#10B981'
  }].map(s => /*#__PURE__*/React.createElement("div", {
    key: s.label,
    style: {
      background: surface,
      borderRadius: 11,
      padding: '16px 18px',
      border: dark ? `1px solid ${border}` : 'none',
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 26,
      fontWeight: 700,
      color: s.color
    }
  }, s.value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2,
      marginTop: 2
    }
  }, s.label)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: surface,
      borderRadius: 12,
      padding: 18,
      border: dark ? `1px solid ${border}` : `1.5px solid #FECACA`,
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.05)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: "#EF4444",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "9",
    x2: "12",
    y2: "13"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "17",
    x2: "12.01",
    y2: "17"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: '#EF4444'
    }
  }, "Critical Alerts"), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      background: '#FEE2E2',
      color: '#B91C1C',
      fontSize: 10,
      fontWeight: 700,
      padding: '1px 7px',
      borderRadius: 9999
    }
  }, CRITICAL_ALERTS.length)), CRITICAL_ALERTS.map((a, i) => /*#__PURE__*/React.createElement("div", {
    key: a.id,
    style: {
      padding: '10px 0',
      borderBottom: i < CRITICAL_ALERTS.length - 1 ? `1px solid ${border}` : 'none',
      display: 'flex',
      gap: 10,
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      borderRadius: 9,
      background: '#FEE2E2',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: "#EF4444",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "22 12 18 12 15 21 9 3 6 12 2 12"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: fg1
    }
  }, patName(a)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2
    }
  }, a.test, " \u2014 ", /*#__PURE__*/React.createElement("strong", {
    style: {
      color: '#EF4444'
    }
  }, a.value))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'flex-end',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 9,
      color: fg2
    }
  }, a.time), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '3px 10px',
      borderRadius: 6,
      border: 'none',
      background: '#EF4444',
      color: '#fff',
      fontSize: 10,
      fontWeight: 600,
      cursor: 'pointer'
    }
  }, "Review"))))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: surface,
      borderRadius: 12,
      padding: 18,
      border: dark ? `1px solid ${border}` : 'none',
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: "#F59E0B",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "10"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "12 6 12 12 16 14"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: fg1
    }
  }, "Pending Approval"), /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      background: '#FEF9C3',
      color: '#A16207',
      fontSize: 10,
      fontWeight: 700,
      padding: '1px 7px',
      borderRadius: 9999
    }
  }, PENDING.length)), PENDING.map((p, i) => /*#__PURE__*/React.createElement("div", {
    key: p.id,
    style: {
      padding: '10px 0',
      borderBottom: i < PENDING.length - 1 ? `1px solid ${border}` : 'none',
      display: 'flex',
      gap: 10,
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      borderRadius: 9,
      background: '#FEF9C3',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: "#F59E0B",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "14 2 14 8 20 8"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: fg1
    }
  }, patName(p)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2
    }
  }, p.test, " \xB7 ", p.time)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 5
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '3px 10px',
      borderRadius: 6,
      border: 'none',
      background: '#10B981',
      color: '#fff',
      fontSize: 10,
      fontWeight: 600,
      cursor: 'pointer'
    }
  }, "\u2713"), /*#__PURE__*/React.createElement("button", {
    style: {
      padding: '3px 10px',
      borderRadius: 6,
      border: `1.5px solid ${border}`,
      background: 'transparent',
      color: fg2,
      fontSize: 10,
      fontWeight: 600,
      cursor: 'pointer'
    }
  }, "\u2715")))))));
}
Object.assign(window, {
  DoctorDashView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/DoctorDashView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/LabQueueView.jsx
try { (() => {
// LabQueueView.jsx — Incoming samples queue with processing states (multilingual)
const {
  useContext: useCtxLQ,
  useState: useStateLQ
} = React;
const QUEUE = [{
  id: 'Q-001',
  patient_ar: 'محمد علي',
  patient_en: 'Mohammed Ali',
  test: 'CBC Panel',
  priority: 'stat',
  received: '08:12',
  state: 'processing',
  eta: '5 min'
}, {
  id: 'Q-002',
  patient_ar: 'زينب حسن',
  patient_en: 'Zainab Hassan',
  test: 'Lipid Panel',
  priority: 'routine',
  received: '08:45',
  state: 'waiting',
  eta: '20 min'
}, {
  id: 'Q-003',
  patient_ar: 'حسن كريم',
  patient_en: 'Hassan Kareem',
  test: 'Blood Culture',
  priority: 'stat',
  received: '09:01',
  state: 'processing',
  eta: '8 min'
}, {
  id: 'Q-004',
  patient_ar: 'ليلى أحمد',
  patient_en: 'Layla Ahmed',
  test: 'Thyroid Panel',
  priority: 'routine',
  received: '09:15',
  state: 'received',
  eta: '35 min'
}, {
  id: 'Q-005',
  patient_ar: 'عادل سالم',
  patient_en: 'Adel Salem',
  test: 'Urine R&M',
  priority: 'routine',
  received: '09:30',
  state: 'received',
  eta: '40 min'
}, {
  id: 'Q-006',
  patient_ar: 'ريم جاسم',
  patient_en: 'Reem Jasim',
  test: 'HbA1c',
  priority: 'urgent',
  received: '09:42',
  state: 'waiting',
  eta: '15 min'
}];
const STATE_MAP = {
  received: {
    label: 'Received',
    bg: '#EFF6FF',
    color: '#1D4ED8',
    dot: '#2563EB'
  },
  waiting: {
    label: 'Waiting',
    bg: '#FEF9C3',
    color: '#A16207',
    dot: '#F59E0B'
  },
  processing: {
    label: 'Processing',
    bg: '#F3E8FF',
    color: '#7E22CE',
    dot: '#8B5CF6',
    animate: true
  }
};
const PRIORITY_MAP = {
  stat: {
    label: 'STAT',
    bg: '#FEE2E2',
    color: '#B91C1C'
  },
  urgent: {
    label: 'URGENT',
    bg: '#FEF9C3',
    color: '#A16207'
  },
  routine: {
    label: 'Routine',
    bg: '#F1F5F9',
    color: '#64748B'
  }
};
function LabQueueView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxLQ(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const surface = dark ? '#1E293B' : '#fff';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const isRtl = dir === 'rtl';
  const statCount = QUEUE.filter(q => q.priority === 'stat').length;
  const procCount = QUEUE.filter(q => q.state === 'processing').length;
  const waitCount = QUEUE.filter(q => q.state === 'waiting').length;
  const patName = item => lang === 'ar' || lang === 'ku' || lang === 'sy' ? item.patient_ar : item.patient_en;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 28,
      overflowY: 'auto',
      flex: 1,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1
    }
  }, t('nav_lab_queue')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: fg2,
      marginTop: 2
    }
  }, QUEUE.length, " samples \u2014 ", statCount, " STAT")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '8px 14px',
      borderRadius: 8,
      border: `1.5px solid ${border}`,
      background: surface,
      color: fg2,
      fontSize: 12,
      fontWeight: 500,
      cursor: 'pointer',
      fontFamily: cfg.font
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "13",
    height: "13",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "5",
    x2: "12",
    y2: "19"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "5",
    y1: "12",
    x2: "19",
    y2: "12"
  })), "Add Sample"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 10,
      marginBottom: 20,
      flexWrap: 'wrap'
    }
  }, [{
    label: 'Processing',
    count: procCount,
    color: '#8B5CF6',
    bg: '#F3E8FF'
  }, {
    label: 'Waiting',
    count: waitCount,
    color: '#F59E0B',
    bg: '#FEF9C3'
  }, {
    label: 'STAT Priority',
    count: statCount,
    color: '#EF4444',
    bg: '#FEE2E2'
  }, {
    label: 'Total Queue',
    count: QUEUE.length,
    color: '#3B82F6',
    bg: '#EFF6FF'
  }].map(s => /*#__PURE__*/React.createElement("div", {
    key: s.label,
    style: {
      background: surface,
      borderRadius: 10,
      padding: '12px 16px',
      border: dark ? `1px solid ${border}` : 'none',
      boxShadow: dark ? 'none' : '0 1px 2px rgb(0 0 0/.06)',
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: 8,
      background: s.bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 14,
      fontWeight: 700,
      color: s.color
    }
  }, s.count), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2,
      fontWeight: 500
    }
  }, s.label)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, QUEUE.map(q => {
    const sm = STATE_MAP[q.state];
    const pm = PRIORITY_MAP[q.priority];
    return /*#__PURE__*/React.createElement("div", {
      key: q.id,
      style: {
        background: surface,
        borderRadius: 12,
        padding: '14px 18px',
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.06)',
        border: q.priority === 'stat' ? '1.5px solid #FECACA' : dark ? `1px solid ${border}` : 'none'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 40,
        height: 40,
        borderRadius: 10,
        background: sm.bg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 10,
        height: 10,
        borderRadius: '50%',
        background: sm.dot
      }
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 3
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 13,
        fontWeight: 700,
        color: fg1
      }
    }, patName(q)), /*#__PURE__*/React.createElement("span", {
      style: {
        padding: '1px 7px',
        borderRadius: 4,
        fontSize: 10,
        fontWeight: 700,
        background: pm.bg,
        color: pm.color
      }
    }, pm.label)), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: fg2
      }
    }, q.id, " \xB7 ", q.test, " \xB7 Received ", q.received)), /*#__PURE__*/React.createElement("div", {
      style: {
        textAlign: 'center',
        flexShrink: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 16,
        fontWeight: 700,
        color: fg1
      }
    }, q.eta), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 9,
        color: fg2,
        textTransform: 'uppercase',
        letterSpacing: '0.06em'
      }
    }, "ETA")), /*#__PURE__*/React.createElement("span", {
      style: {
        padding: '4px 12px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 600,
        background: sm.bg,
        color: sm.color,
        flexShrink: 0
      }
    }, sm.label), /*#__PURE__*/React.createElement("button", {
      style: {
        padding: '6px 14px',
        borderRadius: 7,
        border: 'none',
        background: '#2563EB',
        color: '#fff',
        fontSize: 11,
        fontWeight: 600,
        cursor: 'pointer',
        flexShrink: 0,
        fontFamily: cfg.font
      }
    }, t('act_view')));
  })));
}
Object.assign(window, {
  LabQueueView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/LabQueueView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/Lang.jsx
try { (() => {
// Lang.jsx — language context, translations, switcher
// Languages: English (LTR), Arabic (RTL), Kurdish Sorani (RTL), Turkmen (LTR), Syriac (RTL)

const LANGS = {
  en: {
    dir: 'ltr',
    font: "'Poppins', sans-serif",
    name: 'English',
    code: 'EN',
    nav_main: 'Main',
    nav_manage: 'Manage',
    nav_system: 'System',
    nav_dashboard: 'Dashboard',
    nav_patients: 'Patients',
    nav_samples: 'Samples',
    nav_results: 'Results',
    nav_reports: 'Reports',
    nav_billing: 'Billing',
    nav_settings: 'Settings',
    nav_patient_profile: 'Patient Profile',
    nav_doctor_dash: 'Doctor Dashboard',
    nav_lab_queue: 'Lab Queue',
    search_placeholder: 'Search patients, samples…',
    system_online: 'System Online',
    welcome: 'Welcome back, Ahmed! 👋',
    welcome_sub: "Here's what's happening with your laboratory today",
    stat_patients: 'Total Patients',
    stat_samples: 'Samples Today',
    stat_reports: 'Reports Pending',
    stat_tests: 'Completed Tests',
    from_last_week: 'from last week',
    trends_title: 'Patient & Sample Trends',
    trends_sub: 'Weekly activity overview',
    status_title: 'Sample Status',
    status_sub: 'Distribution this week',
    complete: 'Complete',
    quick_title: 'Quick Actions',
    activity_title: 'Recent Activity',
    act_register: 'Register Patient',
    act_sample: 'Add Sample',
    act_report: 'Generate Report',
    act_download: 'Download Data',
    act1: 'Sample #S-0041 completed',
    act2: 'Report #R-045 pending review',
    act3: 'New patient registered',
    act4: 'System backup completed',
    hours_ago: 'hours ago',
    day_ago: '1 day ago',
    pat_title: 'Patients',
    pat_sub: 'total patients registered',
    pat_register: 'Register Patient',
    pat_search: 'Search by name or national ID…',
    col_id: 'Patient ID',
    col_name: 'Name',
    col_nid: 'National ID',
    col_phone: 'Phone',
    col_status: 'Status',
    col_tests: 'Tests',
    act_view: 'View',
    act_edit: 'Edit',
    status_active: 'Active',
    status_inactive: 'Inactive',
    samp_title: 'Samples',
    samp_sub: 'Track and manage all laboratory samples',
    samp_add: 'Add Sample',
    col_patient: 'Patient',
    col_test: 'Test',
    col_priority: 'Priority',
    col_date: 'Date',
    all: 'All',
    completed: 'Completed',
    pending: 'Pending',
    processing: 'Processing',
    failed: 'Failed',
    priority_normal: 'Normal',
    priority_high: 'High',
    act_retry: 'Retry',
    coming_soon: 'Coming soon in this prototype'
  },
  ar: {
    dir: 'rtl',
    font: "'Cairo', sans-serif",
    name: 'العربية',
    code: 'ع',
    nav_main: 'الرئيسية',
    nav_manage: 'الإدارة',
    nav_system: 'النظام',
    nav_dashboard: 'لوحة التحكم',
    nav_patients: 'المرضى',
    nav_samples: 'العينات',
    nav_results: 'النتائج',
    nav_reports: 'التقارير',
    nav_billing: 'الفواتير',
    nav_settings: 'الإعدادات',
    nav_patient_profile: 'ملف المريض',
    nav_doctor_dash: 'لوحة الطبيب',
    nav_lab_queue: 'قائمة الانتظار',
    search_placeholder: 'ابحث عن مرضى أو عينات…',
    system_online: 'النظام متصل',
    welcome: '!مرحباً بعودتك، أحمد 👋',
    welcome_sub: 'هنا ما يحدث في مختبرك اليوم',
    stat_patients: 'إجمالي المرضى',
    stat_samples: 'عينات اليوم',
    stat_reports: 'تقارير معلقة',
    stat_tests: 'فحوصات مكتملة',
    from_last_week: 'من الأسبوع الماضي',
    trends_title: 'اتجاهات المرضى والعينات',
    trends_sub: 'نظرة عامة على النشاط الأسبوعي',
    status_title: 'حالة العينات',
    status_sub: 'التوزيع هذا الأسبوع',
    complete: 'مكتمل',
    quick_title: 'إجراءات سريعة',
    activity_title: 'النشاط الأخير',
    act_register: 'تسجيل مريض جديد',
    act_sample: 'إضافة عينة',
    act_report: 'إنشاء تقرير',
    act_download: 'تنزيل البيانات',
    act1: 'اكتملت العينة #S-0041',
    act2: 'التقرير #R-045 في انتظار المراجعة',
    act3: 'تم تسجيل مريض جديد',
    act4: 'اكتمل النسخ الاحتياطي للنظام',
    hours_ago: 'ساعات مضت',
    day_ago: 'منذ يوم واحد',
    pat_title: 'المرضى',
    pat_sub: 'مريض مسجل إجمالاً',
    pat_register: 'تسجيل مريض',
    pat_search: '…ابحث بالاسم أو الهوية الوطنية',
    col_id: 'رقم المريض',
    col_name: 'الاسم',
    col_nid: 'الهوية الوطنية',
    col_phone: 'الهاتف',
    col_status: 'الحالة',
    col_tests: 'الفحوصات',
    act_view: 'عرض',
    act_edit: 'تعديل',
    status_active: 'نشط',
    status_inactive: 'غير نشط',
    samp_title: 'العينات',
    samp_sub: 'تتبع وإدارة جميع عينات المختبر',
    samp_add: 'إضافة عينة',
    col_patient: 'المريض',
    col_test: 'الفحص',
    col_priority: 'الأولوية',
    col_date: 'التاريخ',
    all: 'الكل',
    completed: 'مكتملة',
    pending: 'معلقة',
    processing: 'قيد المعالجة',
    failed: 'فاشلة',
    priority_normal: 'عادية',
    priority_high: 'عالية',
    act_retry: 'إعادة المحاولة',
    coming_soon: 'قريباً في هذا النموذج الأولي'
  },
  ku: {
    dir: 'rtl',
    font: "'Cairo', sans-serif",
    name: 'کوردی',
    code: 'ک',
    nav_main: 'سەرەکی',
    nav_manage: 'بەڕێوەبردن',
    nav_system: 'سیستەم',
    nav_dashboard: 'داشبۆرد',
    nav_patients: 'نەخۆشەکان',
    nav_samples: 'نموونەکان',
    nav_results: 'ئەنجامەکان',
    nav_reports: 'ڕاپۆرتەکان',
    nav_billing: 'پارەدان',
    nav_settings: 'ڕێکخستنەکان',
    nav_patient_profile: 'دۆسیەی نەخۆش',
    nav_doctor_dash: 'لوحەی دکتۆر',
    nav_lab_queue: 'ڕیزی چاوەڕوان',
    search_placeholder: '…گەڕان بۆ نەخۆش یان نموونە',
    system_online: 'سیستەم ئامادەیە',
    welcome: '!بەخێربێیتەوە، ئەحمەد 👋',
    welcome_sub: 'ئەمەیە ئەوەی ئەمڕۆ لە تاقیگەکەتدا دەبێت',
    stat_patients: 'کۆی نەخۆشەکان',
    stat_samples: 'نموونەکانی ئەمڕۆ',
    stat_reports: 'ڕاپۆرتە چاوەڕوانەکان',
    stat_tests: 'تاقیکردنەوەی تەواوبوو',
    from_last_week: 'لە هەفتەی ڕابردوو',
    trends_title: 'ئاراستەی نەخۆش و نموونە',
    trends_sub: 'پوختەی چالاکی هەفتانە',
    status_title: 'دۆخی نموونەکان',
    status_sub: 'دابەشکردن ئەم هەفتەیە',
    complete: 'تەواوبوو',
    quick_title: 'کردارە خێراکان',
    activity_title: 'چالاکیی دوایین',
    act_register: 'تۆمارکردنی نەخۆش',
    act_sample: 'زیادکردنی نموونە',
    act_report: 'دروستکردنی ڕاپۆرت',
    act_download: 'داگرتنی داتا',
    act1: 'نموونەی #S-0041 تەواو بوو',
    act2: 'ڕاپۆرتی #R-045 چاوەڕوانی پێداچوونەوەیە',
    act3: 'نەخۆشێکی نوێ تۆمارکرا',
    act4: 'پاراستنەوەی سیستەم تەواو بوو',
    hours_ago: 'کاتژمێر لەمەوبەر',
    day_ago: 'یەک ڕۆژ لەمەوبەر',
    pat_title: 'نەخۆشەکان',
    pat_sub: 'نەخۆشی تۆمارکراو کۆی گشتی',
    pat_register: 'تۆمارکردنی نەخۆش',
    pat_search: '…بگەڕێ بە ناو یان ناسنامەی نەتەوەیی',
    col_id: 'ناسنامەی نەخۆش',
    col_name: 'ناو',
    col_nid: 'ناسنامەی نەتەوەیی',
    col_phone: 'تەلەفۆن',
    col_status: 'دۆخ',
    col_tests: 'تاقیکردنەوەکان',
    act_view: 'بینین',
    act_edit: 'دەستکاری',
    status_active: 'چالاک',
    status_inactive: 'ناچالاک',
    samp_title: 'نموونەکان',
    samp_sub: 'شوێنکەوتن و بەڕێوەبردنی هەموو نموونەکانی تاقیگە',
    samp_add: 'زیادکردنی نموونە',
    col_patient: 'نەخۆش',
    col_test: 'تاقیکردنەوە',
    col_priority: 'پێشینەدان',
    col_date: 'بەروار',
    all: 'هەموو',
    completed: 'تەواوبوو',
    pending: 'چاوەڕوان',
    processing: 'پرۆسەکردن',
    failed: 'سەرنەکەوت',
    priority_normal: 'ئاسایی',
    priority_high: 'بەرز',
    act_retry: 'دووبارە هەوڵدان',
    coming_soon: 'بەمزووانە لەم نموونەیەدا'
  },
  tk: {
    dir: 'ltr',
    font: "'Poppins', sans-serif",
    name: 'Türkmen',
    code: 'TK',
    nav_main: 'Esasy',
    nav_manage: 'Dolandyrmak',
    nav_system: 'Ulgam',
    nav_dashboard: 'Dolandyryş',
    nav_patients: 'Näsaglar',
    nav_samples: 'Nusgalar',
    nav_results: 'Netijeler',
    nav_reports: 'Hasabatlar',
    nav_billing: 'Töleg',
    nav_settings: 'Sazlamalar',
    nav_patient_profile: 'Näsag Profili',
    nav_doctor_dash: 'Lukman Paneli',
    nav_lab_queue: 'Lab Nobaty',
    search_placeholder: 'Näsag ýa-da nusgalary gözläň…',
    system_online: 'Ulgam Işleýär',
    welcome: 'Hoş geldiňiz, Ahmed! 👋',
    welcome_sub: 'Şu gün laboratoriýaňyzda bolup geçýän zat',
    stat_patients: 'Ähli Näsaglar',
    stat_samples: 'Şu Günki Nusgalar',
    stat_reports: 'Garaşylýan Hasabatlar',
    stat_tests: 'Tamamlanan Synaglar',
    from_last_week: 'geçen hepdeden',
    trends_title: 'Näsag we Nusgalaryň Tendensiýasy',
    trends_sub: 'Hepdäniň işine genel bakış',
    status_title: 'Nusgalaryň Ýagdaýy',
    status_sub: 'Bu hepdäniň paýlanyşy',
    complete: 'Tamamlandy',
    quick_title: 'Çalt Hereketler',
    activity_title: 'Soňky Işler',
    act_register: 'Näsag Hasaba Al',
    act_sample: 'Nusgalyk Goş',
    act_report: 'Hasabat Dör',
    act_download: 'Maglumaty Ýükle',
    act1: '#S-0041 nusgasy tamamlandy',
    act2: '#R-045 hasabaty garaşýar',
    act3: 'Täze näsag hasaba alyndy',
    act4: 'Ulgam ätiýaçlygy tamamlandy',
    hours_ago: 'sagat öň',
    day_ago: '1 gün öň',
    pat_title: 'Näsaglar',
    pat_sub: 'jemi hasaba alnan näsag',
    pat_register: 'Näsag Hasaba Al',
    pat_search: 'Ady ýa-da milli ID boýunça gözläň…',
    col_id: 'Näsag ID',
    col_name: 'Ady',
    col_nid: 'Milli ID',
    col_phone: 'Telefon',
    col_status: 'Ýagdaý',
    col_tests: 'Synaglar',
    act_view: 'Gör',
    act_edit: 'Düzelt',
    status_active: 'Işjeň',
    status_inactive: 'Işjeň däl',
    samp_title: 'Nusgalar',
    samp_sub: 'Laboratoriýanyň ähli nusgalaryny yzarlaň we dolandyryň',
    samp_add: 'Nusgalyk Goş',
    col_patient: 'Näsag',
    col_test: 'Synag',
    col_priority: 'Ileri tutulmak',
    col_date: 'Senesi',
    all: 'Hemmesi',
    completed: 'Tamamlandy',
    pending: 'Garaşylýar',
    processing: 'Gaýtadan işlenýär',
    failed: 'Şowsuz',
    priority_normal: 'Adaty',
    priority_high: 'Ýokary',
    act_retry: 'Täzeden',
    coming_soon: 'Bu prototipde ýakyn wagtda'
  },
  sy: {
    dir: 'rtl',
    font: "'Noto Sans Syriac', serif",
    name: 'ܣܘܪܝܬ',
    code: 'ܣ',
    nav_main: 'ܪܝܫܝܐ',
    nav_manage: 'ܡܕܒܪܢܘܬܐ',
    nav_system: 'ܡܢܝܢܐ',
    nav_dashboard: 'ܠܘܚܐ ܕܒܩܘܪܝܐ',
    nav_patients: 'ܟܪ̈ܝܗܐ',
    nav_samples: 'ܢܘܣ̈ܟܐ',
    nav_results: 'ܦܐܪ̈ܐ',
    nav_reports: 'ܕܝܘܩ̈ܐ',
    nav_billing: 'ܦܪܥܐ',
    nav_settings: 'ܬܩܘܢܬܐ',
    nav_patient_profile: 'ܬܚܘܝܬܐ ܕܟܪܝܗܐ',
    nav_doctor_dash: 'ܠܘܚܐ ܕܐܣܝܐ',
    nav_lab_queue: 'ܛܘܪܣܐ ܕܥܘܡܪܐ',
    search_placeholder: '…ܒܩܝ ܟܪ̈ܝܗܐ ܐܘ ܢܘܣ̈ܟܐ',
    system_online: 'ܡܢܝܢܐ ܫܪܝܐ',
    welcome: '!ܒܪܝܟ ܬܘܒܟ ܐܚܡܕ 👋',
    welcome_sub: 'ܗܢܐ ܡܐ ܕܗܘܐ ܒܥܘܡܪܟ ܝܘܡܢܐ',
    stat_patients: 'ܟܠ ܟܪ̈ܝܗܐ',
    stat_samples: 'ܢܘܣ̈ܟܐ ܕܝܘܡܢܐ',
    stat_reports: 'ܕܝܘܩ̈ܐ ܕܣܟܝܢ',
    stat_tests: 'ܒܘܩ̈ܪܐ ܫܠ̈ܡܐ',
    from_last_week: 'ܡܢ ܫܒܘܥܐ ܕܥܒܪ',
    trends_title: 'ܡܐܙܠܬܐ ܕܟܪ̈ܝܗܐ ܘܢܘܣ̈ܟܐ',
    trends_sub: 'ܚܙܘܐ ܕܫܒܘܥܐ',
    status_title: 'ܐܣܝܐ ܕܢܘܣ̈ܟܐ',
    status_sub: 'ܦܠܓܘܬܐ ܕܫܒܘܥܐ',
    complete: 'ܫܠܡ',
    quick_title: 'ܦܘ̈ܠܚܢܐ ܚܡ̈ܫܐ',
    activity_title: 'ܦܘ̈ܠܚܢܐ ܐ̈ܚܪ̈ܝܐ',
    act_register: 'ܣܟܘܪ ܟܪܝܗܐ',
    act_sample: 'ܐܘܣܦ ܢܘܣܟܐ',
    act_report: 'ܥܒܕ ܕܝܘܩܐ',
    act_download: 'ܢܚܬ ܝܘ̈ܠܦܢܐ',
    act1: 'ܢܘܣܟܐ #S-0041 ܫܠܡ',
    act2: 'ܕܝܘܩܐ #R-045 ܣܟܐ ܒܘܩܪܐ',
    act3: 'ܟܪܝܗܐ ܚܕܬܐ ܣܟܝܪ',
    act4: 'ܢܛܪܬܐ ܕܡܢܝܢܐ ܫܠܡܬ',
    hours_ago: 'ܫ̈ܥܐ ܡܢ ܩܕܡ',
    day_ago: 'ܝܘܡܐ ܡܢ ܩܕܡ',
    pat_title: 'ܟܪ̈ܝܗܐ',
    pat_sub: 'ܟܪ̈ܝܗܐ ܣܟ̈ܝܪܐ ܒܟܠ',
    pat_register: 'ܣܟܘܪ ܟܪܝܗܐ',
    pat_search: '…ܒܩܝ ܒܫܡܐ ܐܘ ܗܘܝܬܐ',
    col_id: 'ܗܘܝܬܐ ܕܟܪܝܗܐ',
    col_name: 'ܫܡܐ',
    col_nid: 'ܗܘܝܬܐ ܥܡܝܐ',
    col_phone: 'ܬܠܦܘܢ',
    col_status: 'ܐܣܝܐ',
    col_tests: 'ܒܘ̈ܩܪܐ',
    act_view: 'ܚܙܝ',
    act_edit: 'ܫܚܠܦ',
    status_active: 'ܫܪܝܐ',
    status_inactive: 'ܠܐ ܫܪܝܐ',
    samp_title: 'ܢܘܣ̈ܟܐ',
    samp_sub: 'ܦܩܚ ܘܕܒܪ ܟܠ ܢܘܣ̈ܟܐ ܕܥܘܡܪܐ',
    samp_add: 'ܐܘܣܦ ܢܘܣܟܐ',
    col_patient: 'ܟܪܝܗܐ',
    col_test: 'ܒܘܩܪܐ',
    col_priority: 'ܩܕܡܝܘܬܐ',
    col_date: 'ܝܘܡܐ',
    all: 'ܟܠ',
    completed: 'ܫܠܡ',
    pending: 'ܣܟܐ',
    processing: 'ܡܥܒܕܢܘܬܐ',
    failed: 'ܠܐ ܥܒܕ',
    priority_normal: 'ܥܝܕܝ',
    priority_high: 'ܪܡܐ',
    act_retry: 'ܕܥܘ ܬܘܒ',
    coming_soon: 'ܩܪܝܒ ܒܗܢܐ ܕܡܘܬܐ'
  }
};
const LangContext = React.createContext({
  lang: 'en',
  t: k => k,
  setLang: () => {}
});
const LANG_ORDER = ['en', 'ar', 'ku', 'tk', 'sy'];
const langSwitcherStyles = {
  bar: {
    display: 'flex',
    gap: 2,
    background: '#F1F5F9',
    borderRadius: 8,
    padding: 3,
    flexShrink: 0
  },
  btn: active => ({
    padding: '4px 10px',
    borderRadius: 6,
    fontSize: 11,
    fontWeight: 600,
    cursor: 'pointer',
    border: 'none',
    fontFamily: 'inherit',
    background: active ? '#fff' : 'transparent',
    color: active ? '#2563EB' : '#64748B',
    boxShadow: active ? '0 1px 3px rgb(0 0 0 / 0.1)' : 'none',
    transition: 'all 0.15s',
    minWidth: 30,
    textAlign: 'center'
  })
};
function LangSwitcher({
  lang,
  setLang
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: langSwitcherStyles.bar
  }, LANG_ORDER.map(code => /*#__PURE__*/React.createElement("button", {
    key: code,
    style: langSwitcherStyles.btn(lang === code),
    onClick: () => setLang(code),
    title: LANGS[code].name
  }, LANGS[code].code)));
}
Object.assign(window, {
  LANGS,
  LangContext,
  LangSwitcher,
  LANG_ORDER
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/Lang.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/PatientProfileView.jsx
try { (() => {
// PatientProfileView.jsx — Patient timeline + history (multilingual)
const {
  useContext: useCtxPP
} = React;
const PATIENT = {
  id: 'P-001',
  name_ar: 'أحمد حسن محمد',
  name_en: 'Ahmed Hassan Mohammed',
  nid: '19841204012345',
  dob: '1984-12-04',
  age: 41,
  gender_ar: 'ذكر',
  gender_en: 'Male',
  phone: '+964 770 123 4567',
  blood: 'A+',
  conditions: ['Type 2 Diabetes', 'Hypertension'],
  allergies: ['Penicillin']
};
const TIMELINE = [{
  date: 'Apr 28, 2026',
  test: 'Hemoglobin',
  value: '9.2 g/dL',
  flag: 'low',
  doctor: 'Dr. Samer',
  status: 'failed'
}, {
  date: 'Mar 15, 2026',
  test: 'HbA1c',
  value: '8.1%',
  flag: 'high',
  doctor: 'Dr. Layla',
  status: 'failed'
}, {
  date: 'Feb 10, 2026',
  test: 'CBC Panel',
  value: 'Normal',
  flag: 'ok',
  doctor: 'Dr. Samer',
  status: 'completed'
}, {
  date: 'Jan 05, 2026',
  test: 'Lipid Panel',
  value: 'LDL 112',
  flag: 'high',
  doctor: 'Dr. Hassan',
  status: 'failed'
}, {
  date: 'Dec 20, 2025',
  test: 'TSH',
  value: '2.4 mIU/L',
  flag: 'ok',
  doctor: 'Dr. Layla',
  status: 'completed'
}];
const FLAG_COLORS = {
  high: {
    bg: '#FEE2E2',
    color: '#B91C1C',
    label: '↑ High'
  },
  low: {
    bg: '#FEF9C3',
    color: '#A16207',
    label: '↓ Low'
  },
  ok: {
    bg: '#DCFCE7',
    color: '#15803D',
    label: '✓ Normal'
  }
};
function PatientProfileView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxPP(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const surface = dark ? '#1E293B' : '#fff';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const name = lang === 'ar' || lang === 'ku' || lang === 'sy' ? PATIENT.name_ar : PATIENT.name_en;
  const gender = lang === 'ar' || lang === 'ku' || lang === 'sy' ? PATIENT.gender_ar : PATIENT.gender_en;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 28,
      overflowY: 'auto',
      flex: 1,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1,
      marginBottom: 20
    }
  }, t('nav_patient_profile')), /*#__PURE__*/React.createElement("div", {
    style: {
      background: surface,
      borderRadius: 14,
      padding: 22,
      marginBottom: 18,
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)',
      border: dark ? `1px solid ${border}` : 'none',
      display: 'flex',
      gap: 20,
      alignItems: 'flex-start',
      flexWrap: 'wrap'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 64,
      height: 64,
      borderRadius: '50%',
      background: 'linear-gradient(135deg,#2563EB,#8B5CF6)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontWeight: 700,
      fontSize: 22,
      flexShrink: 0
    }
  }, name[0]), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 200
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1
    }
  }, name), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: fg2,
      marginTop: 2
    }
  }, PATIENT.id, " \xB7 ", gender, " \xB7 ", PATIENT.age, " yrs \xB7 ", PATIENT.blood), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginTop: 10,
      flexWrap: 'wrap'
    }
  }, PATIENT.conditions.map(c => /*#__PURE__*/React.createElement("span", {
    key: c,
    style: {
      padding: '2px 9px',
      borderRadius: 6,
      background: '#FEF9C3',
      color: '#A16207',
      fontSize: 11,
      fontWeight: 600
    }
  }, c)), PATIENT.allergies.map(a => /*#__PURE__*/React.createElement("span", {
    key: a,
    style: {
      padding: '2px 9px',
      borderRadius: 6,
      background: '#FEE2E2',
      color: '#B91C1C',
      fontSize: 11,
      fontWeight: 600
    }
  }, "\u26A0 ", a)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      fontSize: 12,
      color: fg2
    }
  }, /*#__PURE__*/React.createElement("div", null, "\uD83D\uDCDE ", PATIENT.phone), /*#__PURE__*/React.createElement("div", null, "\uD83E\uDEAA ", PATIENT.nid), /*#__PURE__*/React.createElement("div", null, "\uD83C\uDF82 ", PATIENT.dob))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4,1fr)',
      gap: 12,
      marginBottom: 18
    }
  }, [{
    label: 'Total Tests',
    value: TIMELINE.length,
    color: '#3B82F6'
  }, {
    label: 'Abnormal',
    value: TIMELINE.filter(t => t.flag !== 'ok').length,
    color: '#EF4444'
  }, {
    label: 'Normal',
    value: TIMELINE.filter(t => t.flag === 'ok').length,
    color: '#10B981'
  }, {
    label: 'Last Visit',
    value: 'Apr 28',
    color: '#8B5CF6'
  }].map(s => /*#__PURE__*/React.createElement("div", {
    key: s.label,
    style: {
      background: surface,
      borderRadius: 10,
      padding: '14px 16px',
      border: dark ? `1px solid ${border}` : 'none',
      boxShadow: dark ? 'none' : '0 1px 2px rgb(0 0 0/.06)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 22,
      fontWeight: 700,
      color: s.color
    }
  }, s.value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2,
      marginTop: 2
    }
  }, s.label)))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: surface,
      borderRadius: 14,
      padding: 20,
      border: dark ? `1px solid ${border}` : 'none',
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: fg1,
      marginBottom: 16
    }
  }, "Lab Results Timeline"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 0
    }
  }, TIMELINE.map((item, i) => {
    const fc = FLAG_COLORS[item.flag];
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      style: {
        display: 'flex',
        gap: 14,
        padding: '12px 0',
        borderBottom: i < TIMELINE.length - 1 ? `1px solid ${border}` : 'none',
        alignItems: 'center'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        flexShrink: 0,
        textAlign: 'center',
        width: 70
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 10,
        color: fg2,
        fontWeight: 500
      }
    }, item.date)), /*#__PURE__*/React.createElement("div", {
      style: {
        width: 10,
        height: 10,
        borderRadius: '50%',
        background: item.flag === 'ok' ? '#10B981' : '#EF4444',
        flexShrink: 0,
        border: `2px solid ${bg}`,
        boxShadow: `0 0 0 2px ${item.flag === 'ok' ? '#10B981' : '#EF4444'}`
      }
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 13,
        fontWeight: 600,
        color: fg1
      }
    }, item.test), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: fg2
      }
    }, item.doctor)), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 13,
        fontWeight: 700,
        color: fg1
      }
    }, item.value), /*#__PURE__*/React.createElement("span", {
      style: {
        padding: '2px 8px',
        borderRadius: 6,
        fontSize: 10,
        fontWeight: 700,
        background: fc.bg,
        color: fc.color
      }
    }, fc.label));
  }))));
}
Object.assign(window, {
  PatientProfileView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/PatientProfileView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/PatientsView.jsx
try { (() => {
// PatientsView.jsx — Patients screen (multilingual)
const {
  useState: useStateP,
  useContext: useCtxP
} = React;
const PATIENTS = [{
  id: 'P-001',
  name: 'Ahmed Al-Rashidi',
  nid: '19841204012345',
  phone: '+964 770 123 4567',
  statusKey: 'status_active',
  tests: 8
}, {
  id: 'P-002',
  name: 'Sara Khalil Mohammed',
  nid: '19950615078901',
  phone: '+964 771 234 5678',
  statusKey: 'status_active',
  tests: 3
}, {
  id: 'P-003',
  name: 'Omar Hassan Al-Jabouri',
  nid: '19780320034567',
  phone: '+964 772 345 6789',
  statusKey: 'status_inactive',
  tests: 14
}, {
  id: 'P-004',
  name: 'Fatima Al-Amiri',
  nid: '20010901056789',
  phone: '+964 773 456 7890',
  statusKey: 'status_active',
  tests: 2
}, {
  id: 'P-005',
  name: 'Kareem Saleh',
  nid: '19900712089012',
  phone: '+964 774 567 8901',
  statusKey: 'status_active',
  tests: 6
}];
const patStyles = {
  page: {
    padding: 28,
    overflowY: 'auto',
    flex: 1
  },
  header: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 20
  },
  title: {
    fontSize: 18,
    fontWeight: 700,
    color: '#0F172A'
  },
  sub: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 2
  },
  btn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '8px 16px',
    borderRadius: 8,
    border: 'none',
    background: '#2563EB',
    color: '#fff',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer'
  },
  searchWrap: {
    marginBottom: 16
  },
  searchInput: {
    width: '100%',
    padding: '8px 12px',
    border: '1.5px solid #E2E8F0',
    borderRadius: 8,
    fontSize: 13,
    color: '#0F172A',
    outline: 'none',
    background: '#fff'
  },
  table: {
    background: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    boxShadow: '0 1px 3px rgb(0 0 0/.07)',
    width: '100%',
    borderCollapse: 'collapse'
  },
  th: {
    padding: '10px 16px',
    textAlign: 'left',
    fontSize: 11,
    fontWeight: 600,
    color: '#94A3B8',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    background: '#F8FAFC',
    borderBottom: '1.5px solid #E2E8F0'
  },
  thRtl: {
    textAlign: 'right'
  },
  td: {
    padding: '12px 16px',
    fontSize: 13,
    color: '#0F172A',
    borderBottom: '1px solid #F1F5F9'
  },
  tdRtl: {
    textAlign: 'right'
  },
  actionBtn: {
    background: 'none',
    border: 'none',
    fontSize: 12,
    fontWeight: 500,
    color: '#2563EB',
    cursor: 'pointer',
    padding: '0 6px'
  }
};
function PatientsView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxP(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const [search, setSearch] = useStateP('');
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const filtered = PATIENTS.filter(p => p.name.toLowerCase().includes(search.toLowerCase()) || p.nid.includes(search));
  const thStyle = {
    ...patStyles.th,
    ...(isRtl ? patStyles.thRtl : {})
  };
  const tdStyle = {
    ...patStyles.td,
    ...(isRtl ? patStyles.tdRtl : {})
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      ...patStyles.page,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: patStyles.header
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      ...patStyles.title,
      color: fg1
    }
  }, t('pat_title')), /*#__PURE__*/React.createElement("div", {
    style: {
      ...patStyles.sub,
      color: fg2
    }
  }, PATIENTS.length, " ", t('pat_sub'))), /*#__PURE__*/React.createElement("button", {
    style: {
      ...patStyles.btn,
      fontFamily: cfg.font
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "5",
    x2: "12",
    y2: "19"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "5",
    y1: "12",
    x2: "19",
    y2: "12"
  })), t('pat_register'))), /*#__PURE__*/React.createElement("div", {
    style: patStyles.searchWrap
  }, /*#__PURE__*/React.createElement("input", {
    style: {
      ...patStyles.searchInput,
      fontFamily: cfg.font,
      direction: dir
    },
    placeholder: t('pat_search'),
    value: search,
    onChange: e => setSearch(e.target.value)
  })), /*#__PURE__*/React.createElement("table", {
    style: {
      ...patStyles.table,
      background: surface
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_id')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_name')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_nid')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_phone')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_status')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_tests')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }))), /*#__PURE__*/React.createElement("tbody", null, filtered.map((p, i) => /*#__PURE__*/React.createElement("tr", {
    key: p.id,
    style: {
      background: i % 2 === 0 ? '#fff' : '#FAFBFC'
    }
  }, /*#__PURE__*/React.createElement("td", {
    style: {
      ...tdStyle,
      color: '#2563EB',
      fontWeight: 600
    }
  }, p.id), /*#__PURE__*/React.createElement("td", {
    style: tdStyle
  }, p.name), /*#__PURE__*/React.createElement("td", {
    style: {
      ...tdStyle,
      fontFamily: 'monospace',
      fontSize: 12,
      color: '#64748B'
    }
  }, p.nid), /*#__PURE__*/React.createElement("td", {
    style: {
      ...tdStyle,
      color: '#64748B',
      fontSize: 12
    }
  }, p.phone), /*#__PURE__*/React.createElement("td", {
    style: tdStyle
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      padding: '2px 9px',
      borderRadius: 9999,
      fontSize: 11,
      fontWeight: 600,
      background: p.statusKey === 'status_active' ? '#DCFCE7' : '#F1F5F9',
      color: p.statusKey === 'status_active' ? '#15803D' : '#64748B'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 5,
      height: 5,
      borderRadius: '50%',
      background: p.statusKey === 'status_active' ? '#10B981' : '#94A3B8'
    }
  }), t(p.statusKey))), /*#__PURE__*/React.createElement("td", {
    style: {
      ...tdStyle,
      fontWeight: 600
    }
  }, p.tests), /*#__PURE__*/React.createElement("td", {
    style: tdStyle
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      ...patStyles.actionBtn,
      fontFamily: cfg.font
    }
  }, t('act_view')), /*#__PURE__*/React.createElement("button", {
    style: {
      ...patStyles.actionBtn,
      fontFamily: cfg.font,
      color: '#64748B'
    }
  }, t('act_edit'))))))));
}
Object.assign(window, {
  PatientsView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/PatientsView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/ReportsView.jsx
try { (() => {
// ReportsView.jsx — Reports screen (multilingual)
const {
  useContext: useCtxRep
} = React;
const REPORTS_DATA = [{
  id: 'RPT-001',
  title: 'Monthly Lab Summary — April 2026',
  type: 'Summary',
  generated: 'Apr 28, 2026',
  size: '2.4 MB',
  format: 'PDF'
}, {
  id: 'RPT-002',
  title: 'Critical Results Alert Report',
  type: 'Critical',
  generated: 'Apr 27, 2026',
  size: '1.1 MB',
  format: 'PDF'
}, {
  id: 'RPT-003',
  title: 'Patient Billing Statement — Q1',
  type: 'Billing',
  generated: 'Apr 25, 2026',
  size: '3.8 MB',
  format: 'Excel'
}, {
  id: 'RPT-004',
  title: 'Sample Turnaround Time Analysis',
  type: 'Analytics',
  generated: 'Apr 22, 2026',
  size: '0.9 MB',
  format: 'PDF'
}, {
  id: 'RPT-005',
  title: 'Equipment Quality Control Log',
  type: 'QC',
  generated: 'Apr 20, 2026',
  size: '1.6 MB',
  format: 'PDF'
}];
const TYPE_COLORS = {
  Summary: {
    bg: '#EFF6FF',
    color: '#1D4ED8'
  },
  Critical: {
    bg: '#FEE2E2',
    color: '#B91C1C'
  },
  Billing: {
    bg: '#FEF9C3',
    color: '#A16207'
  },
  Analytics: {
    bg: '#F3E8FF',
    color: '#7E22CE'
  },
  QC: {
    bg: '#DCFCE7',
    color: '#15803D'
  }
};
function ReportsView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxRep(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 28,
      overflowY: 'auto',
      flex: 1,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 24
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1
    }
  }, t('nav_reports')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: fg2,
      marginTop: 2
    }
  }, REPORTS_DATA.length, " reports available")), /*#__PURE__*/React.createElement("button", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '8px 16px',
      borderRadius: 8,
      border: 'none',
      background: '#2563EB',
      color: '#fff',
      fontSize: 13,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: cfg.font
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "5",
    x2: "12",
    y2: "19"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "5",
    y1: "12",
    x2: "19",
    y2: "12"
  })), t('act_report'))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3,1fr)',
      gap: 14,
      marginBottom: 24
    }
  }, [{
    label: 'Total Reports',
    value: '148',
    icon: '📊',
    color: '#3B82F6'
  }, {
    label: 'This Month',
    value: '23',
    icon: '📅',
    color: '#10B981'
  }, {
    label: 'Pending Review',
    value: '5',
    icon: '⏳',
    color: '#F59E0B'
  }].map(s => /*#__PURE__*/React.createElement("div", {
    key: s.label,
    style: {
      background: surface,
      borderRadius: 12,
      padding: 18,
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)',
      border: dark ? `1px solid ${border}` : 'none',
      display: 'flex',
      alignItems: 'center',
      gap: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 40,
      height: 40,
      borderRadius: 10,
      background: s.color + '18',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: 18
    }
  }, s.icon), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 22,
      fontWeight: 700,
      color: fg1
    }
  }, s.value), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: fg2
    }
  }, s.label))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, REPORTS_DATA.map(r => {
    const tc = TYPE_COLORS[r.type];
    return /*#__PURE__*/React.createElement("div", {
      key: r.id,
      style: {
        background: surface,
        borderRadius: 12,
        padding: '16px 20px',
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.06)',
        border: dark ? `1px solid ${border}` : 'none'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 40,
        height: 40,
        borderRadius: 9,
        background: r.format === 'PDF' ? '#FEE2E2' : '#DCFCE7',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0
      }
    }, /*#__PURE__*/React.createElement("svg", {
      viewBox: "0 0 24 24",
      width: "18",
      height: "18",
      fill: "none",
      stroke: r.format === 'PDF' ? '#EF4444' : '#10B981',
      strokeWidth: "2",
      strokeLinecap: "round",
      strokeLinejoin: "round"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
    }), /*#__PURE__*/React.createElement("polyline", {
      points: "14 2 14 8 20 8"
    }))), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 13,
        fontWeight: 600,
        color: fg1,
        marginBottom: 3
      }
    }, r.title), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        color: fg2
      }
    }, r.id, " \xB7 ", r.generated, " \xB7 ", r.size)), /*#__PURE__*/React.createElement("span", {
      style: {
        padding: '3px 10px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 600,
        background: tc.bg,
        color: tc.color,
        flexShrink: 0
      }
    }, r.type), /*#__PURE__*/React.createElement("button", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 5,
        padding: '6px 12px',
        borderRadius: 7,
        border: `1.5px solid ${border}`,
        background: 'transparent',
        color: fg2,
        fontSize: 12,
        fontWeight: 500,
        cursor: 'pointer',
        fontFamily: cfg.font,
        flexShrink: 0
      }
    }, /*#__PURE__*/React.createElement("svg", {
      viewBox: "0 0 24 24",
      width: "12",
      height: "12",
      fill: "none",
      stroke: "currentColor",
      strokeWidth: "2",
      strokeLinecap: "round",
      strokeLinejoin: "round"
    }, /*#__PURE__*/React.createElement("path", {
      d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
    }), /*#__PURE__*/React.createElement("polyline", {
      points: "7 10 12 15 17 10"
    }), /*#__PURE__*/React.createElement("line", {
      x1: "12",
      y1: "15",
      x2: "12",
      y2: "3"
    })), t('act_download')));
  })));
}
Object.assign(window, {
  ReportsView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/ReportsView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/ResultsView.jsx
try { (() => {
// ResultsView.jsx — Lab results with clinical flag logic (multilingual)
const {
  useContext: useCtxR,
  useState: useStateR
} = React;

// Medical-grade mock data with reference ranges
const RESULTS = [{
  id: 'R-0101',
  patient: 'أحمد حسن',
  patient_en: 'Ahmed Hassan',
  test: 'Hemoglobin',
  value: 9.2,
  unit: 'g/dL',
  ref: '13.5–17.5',
  refMin: 13.5,
  refMax: 17.5,
  statusKey: 'failed',
  date: 'Apr 28, 2026',
  doctor: 'Dr. Samer'
}, {
  id: 'R-0102',
  patient: 'سارة خالد',
  patient_en: 'Sara Khalid',
  test: 'LDL Cholesterol',
  value: 98,
  unit: 'mg/dL',
  ref: '<100',
  refMin: 0,
  refMax: 100,
  statusKey: 'completed',
  date: 'Apr 28, 2026',
  doctor: 'Dr. Layla'
}, {
  id: 'R-0103',
  patient: 'عمر جاسم',
  patient_en: 'Omar Jasim',
  test: 'WBC Count',
  value: 12.8,
  unit: '×10³/µL',
  ref: '4.5–11.0',
  refMin: 4.5,
  refMax: 11.0,
  statusKey: 'failed',
  date: 'Apr 27, 2026',
  doctor: 'Dr. Samer'
}, {
  id: 'R-0104',
  patient: 'فاطمة علي',
  patient_en: 'Fatima Ali',
  test: 'TSH',
  value: 2.1,
  unit: 'mIU/L',
  ref: '0.4–4.0',
  refMin: 0.4,
  refMax: 4.0,
  statusKey: 'completed',
  date: 'Apr 27, 2026',
  doctor: 'Dr. Hassan'
}, {
  id: 'R-0105',
  patient: 'كريم صالح',
  patient_en: 'Kareem Saleh',
  test: 'HbA1c',
  value: 8.4,
  unit: '%',
  ref: '<5.7',
  refMin: 0,
  refMax: 5.7,
  statusKey: 'failed',
  date: 'Apr 26, 2026',
  doctor: 'Dr. Layla'
}, {
  id: 'R-0106',
  patient: 'نور أحمد',
  patient_en: 'Nour Ahmed',
  test: 'Platelets',
  value: 245,
  unit: '×10³/µL',
  ref: '150–400',
  refMin: 150,
  refMax: 400,
  statusKey: 'completed',
  date: 'Apr 26, 2026',
  doctor: 'Dr. Samer'
}];

// Clinical logic: determine if value is abnormal
const isAbnormal = r => r.value < r.refMin || r.value > r.refMax;
const isHigh = r => r.value > r.refMax;
const isLow = r => r.value < r.refMin;
const FLAG = {
  high: {
    label: '↑ H',
    bg: '#FEE2E2',
    color: '#B91C1C'
  },
  low: {
    label: '↓ L',
    bg: '#FEF9C3',
    color: '#A16207'
  },
  ok: {
    label: '✓',
    bg: '#DCFCE7',
    color: '#15803D'
  }
};
const STATUS_S = {
  completed: {
    bg: '#DCFCE7',
    color: '#15803D',
    dot: '#10B981'
  },
  pending: {
    bg: '#FEF9C3',
    color: '#A16207',
    dot: '#F59E0B'
  },
  failed: {
    bg: '#FEE2E2',
    color: '#B91C1C',
    dot: '#EF4444'
  }
};
function ResultsView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxR(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const [filter, setFilter] = useStateR('all');
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const rowAlt = dark ? '#1A2744' : '#FAFBFC';
  const shown = filter === 'all' ? RESULTS : filter === 'abnormal' ? RESULTS.filter(r => isAbnormal(r)) : RESULTS.filter(r => r.statusKey === filter);
  const abnormalCount = RESULTS.filter(r => isAbnormal(r)).length;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 28,
      overflowY: 'auto',
      flex: 1,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 18,
      fontWeight: 700,
      color: fg1
    }
  }, t('nav_results')), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: fg2,
      marginTop: 2
    }
  }, RESULTS.length, " results \u2014 ", abnormalCount, " abnormal flags")), /*#__PURE__*/React.createElement("button", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6,
      padding: '8px 16px',
      borderRadius: 8,
      border: 'none',
      background: '#2563EB',
      color: '#fff',
      fontSize: 13,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: cfg.font
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "7 10 12 15 17 10"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "15",
    x2: "12",
    y2: "3"
  })), t('act_download'))), abnormalCount > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      background: '#FEF2F2',
      border: '1.5px solid #FECACA',
      borderRadius: 10,
      padding: '10px 14px',
      marginBottom: 14,
      display: 'flex',
      alignItems: 'center',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: "#EF4444",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "9",
    x2: "12",
    y2: "13"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "17",
    x2: "12.01",
    y2: "17"
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: '#B91C1C'
    }
  }, abnormalCount, " critical results require immediate review")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 6,
      marginBottom: 16,
      flexWrap: 'wrap'
    }
  }, [['all', 'All'], ['abnormal', `⚑ Abnormal (${abnormalCount})`], ['completed', t('completed')], ['pending', t('pending')], ['failed', t('failed')]].map(([f, label]) => /*#__PURE__*/React.createElement("button", {
    key: f,
    onClick: () => setFilter(f),
    style: {
      padding: '5px 12px',
      borderRadius: 7,
      border: '1.5px solid',
      borderColor: filter === f ? '#2563EB' : border,
      background: filter === f ? f === 'abnormal' ? '#FEE2E2' : '#EFF6FF' : surface,
      color: filter === f ? f === 'abnormal' ? '#B91C1C' : '#2563EB' : fg2,
      fontSize: 11,
      fontWeight: 600,
      cursor: 'pointer',
      fontFamily: cfg.font
    }
  }, label))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: surface,
      borderRadius: 12,
      overflow: 'hidden',
      boxShadow: dark ? 'none' : '0 1px 3px rgb(0 0 0/.07)',
      border: dark ? `1px solid ${border}` : 'none'
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse'
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", {
    style: {
      background: dark ? '#1A2744' : '#F8FAFC',
      borderBottom: `1.5px solid ${border}`
    }
  }, ['ID', t('col_patient'), 'Test', 'Result', 'Flag', 'Reference', t('col_status'), t('col_date')].map((h, i) => /*#__PURE__*/React.createElement("th", {
    key: i,
    style: {
      padding: '10px 14px',
      textAlign: isRtl ? 'right' : 'left',
      fontSize: 10,
      fontWeight: 600,
      color: fg2,
      textTransform: 'uppercase',
      letterSpacing: '0.06em'
    }
  }, h)))), /*#__PURE__*/React.createElement("tbody", null, shown.map((r, i) => {
    const sc = STATUS_S[r.statusKey];
    const abn = isAbnormal(r);
    const flag = abn ? isHigh(r) ? FLAG.high : FLAG.low : FLAG.ok;
    const td = {
      padding: '12px 14px',
      fontSize: 13,
      color: fg1,
      borderBottom: `1px solid ${border}`,
      textAlign: isRtl ? 'right' : 'left',
      background: abn && i % 2 === 0 ? dark ? '#2D1515' : '#FFF9F9' : i % 2 === 0 ? surface : rowAlt
    };
    return /*#__PURE__*/React.createElement("tr", {
      key: r.id
    }, /*#__PURE__*/React.createElement("td", {
      style: {
        ...td,
        color: '#2563EB',
        fontWeight: 600,
        fontSize: 11
      }
    }, r.id), /*#__PURE__*/React.createElement("td", {
      style: td
    }, lang === 'ar' || lang === 'ku' ? r.patient : r.patient_en), /*#__PURE__*/React.createElement("td", {
      style: {
        ...td,
        color: fg2,
        fontSize: 12
      }
    }, r.test), /*#__PURE__*/React.createElement("td", {
      style: {
        ...td,
        fontWeight: 700,
        color: abn ? '#EF4444' : '#10B981',
        fontFamily: 'monospace'
      }
    }, r.value, " ", /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        fontWeight: 400,
        color: fg2
      }
    }, r.unit)), /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-block',
        padding: '2px 7px',
        borderRadius: 5,
        fontSize: 11,
        fontWeight: 700,
        background: flag.bg,
        color: flag.color
      }
    }, flag.label)), /*#__PURE__*/React.createElement("td", {
      style: {
        ...td,
        fontFamily: 'monospace',
        fontSize: 11,
        color: fg2
      }
    }, r.ref), /*#__PURE__*/React.createElement("td", {
      style: td
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '3px 9px',
        borderRadius: 9999,
        fontSize: 10,
        fontWeight: 600,
        background: sc.bg,
        color: sc.color
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        width: 5,
        height: 5,
        borderRadius: '50%',
        background: sc.dot
      }
    }), t(r.statusKey))), /*#__PURE__*/React.createElement("td", {
      style: {
        ...td,
        color: fg2,
        fontSize: 11
      }
    }, r.date));
  })))));
}
Object.assign(window, {
  ResultsView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/ResultsView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/SamplesView.jsx
try { (() => {
// SamplesView.jsx — Samples screen (multilingual)
const {
  useState: useStateS,
  useContext: useCtxS
} = React;
const SAMPLES = [{
  id: 'S-0041',
  patient: 'Ahmed Al-Rashidi',
  test: 'CBC — Blood',
  statusKey: 'completed',
  date: 'Apr 28, 2026',
  priorityKey: 'priority_normal'
}, {
  id: 'S-0042',
  patient: 'Sara Khalil',
  test: 'Lipid Panel',
  statusKey: 'pending',
  date: 'Apr 28, 2026',
  priorityKey: 'priority_high'
}, {
  id: 'S-0043',
  patient: 'Omar Hassan',
  test: 'Urine Culture',
  statusKey: 'processing',
  date: 'Apr 27, 2026',
  priorityKey: 'priority_normal'
}, {
  id: 'S-0044',
  patient: 'Fatima Al-Amiri',
  test: 'Thyroid Panel',
  statusKey: 'failed',
  date: 'Apr 27, 2026',
  priorityKey: 'priority_high'
}, {
  id: 'S-0045',
  patient: 'Kareem Saleh',
  test: 'HbA1c',
  statusKey: 'completed',
  date: 'Apr 26, 2026',
  priorityKey: 'priority_normal'
}];
const STATUS_STYLES = {
  completed: {
    bg: '#DCFCE7',
    color: '#15803D',
    dot: '#10B981'
  },
  pending: {
    bg: '#FEF9C3',
    color: '#A16207',
    dot: '#F59E0B'
  },
  processing: {
    bg: '#EFF6FF',
    color: '#1D4ED8',
    dot: '#2563EB'
  },
  failed: {
    bg: '#FEE2E2',
    color: '#B91C1C',
    dot: '#EF4444'
  }
};
const sampStyles = {
  page: {
    padding: 28,
    overflowY: 'auto',
    flex: 1
  },
  header: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 20
  },
  title: {
    fontSize: 18,
    fontWeight: 700,
    color: '#0F172A'
  },
  sub: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 2
  },
  btn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '8px 16px',
    borderRadius: 8,
    border: 'none',
    background: '#2563EB',
    color: '#fff',
    fontSize: 13,
    fontWeight: 600,
    cursor: 'pointer'
  },
  filters: {
    display: 'flex',
    gap: 6,
    marginBottom: 16,
    flexWrap: 'wrap'
  },
  filterBtn: active => ({
    padding: '5px 14px',
    borderRadius: 7,
    border: '1.5px solid',
    borderColor: active ? '#2563EB' : '#E2E8F0',
    background: active ? '#EFF6FF' : '#fff',
    color: active ? '#2563EB' : '#64748B',
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer'
  }),
  table: {
    background: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    boxShadow: '0 1px 3px rgb(0 0 0/.07)',
    width: '100%',
    borderCollapse: 'collapse'
  },
  th: {
    padding: '10px 16px',
    fontSize: 11,
    fontWeight: 600,
    color: '#94A3B8',
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    background: '#F8FAFC',
    borderBottom: '1.5px solid #E2E8F0'
  },
  td: {
    padding: '13px 16px',
    fontSize: 13,
    color: '#0F172A',
    borderBottom: '1px solid #F1F5F9'
  }
};
const ALL_FILTERS = ['all', 'completed', 'pending', 'processing', 'failed'];
function SamplesView({
  dark
}) {
  const {
    t,
    lang
  } = useCtxS(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const isRtl = dir === 'rtl';
  const [filter, setFilter] = useStateS('all');
  const surface = dark ? '#1E293B' : '#fff';
  const bg = dark ? '#0F172A' : '#F8FAFC';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#64748B';
  const border = dark ? '#334155' : '#E2E8F0';
  const shown = filter === 'all' ? SAMPLES : SAMPLES.filter(s => s.statusKey === filter);
  const thStyle = {
    ...sampStyles.th,
    textAlign: isRtl ? 'right' : 'left'
  };
  const tdStyle = {
    ...sampStyles.td,
    textAlign: isRtl ? 'right' : 'left'
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      ...sampStyles.page,
      fontFamily: cfg.font,
      direction: dir,
      background: bg
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: sampStyles.header
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      ...sampStyles.title,
      color: fg1
    }
  }, t('samp_title')), /*#__PURE__*/React.createElement("div", {
    style: {
      ...sampStyles.sub,
      color: fg2
    }
  }, t('samp_sub'))), /*#__PURE__*/React.createElement("button", {
    style: {
      ...sampStyles.btn,
      fontFamily: cfg.font
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "#fff",
    strokeWidth: "2.5",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "5",
    x2: "12",
    y2: "19"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "5",
    y1: "12",
    x2: "19",
    y2: "12"
  })), t('samp_add'))), /*#__PURE__*/React.createElement("div", {
    style: sampStyles.filters
  }, ALL_FILTERS.map(f => /*#__PURE__*/React.createElement("button", {
    key: f,
    style: {
      ...sampStyles.filterBtn(filter === f),
      fontFamily: cfg.font
    },
    onClick: () => setFilter(f)
  }, t(f)))), /*#__PURE__*/React.createElement("table", {
    style: {
      ...sampStyles.table,
      background: surface
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_id')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_patient')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_test')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_priority')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_status')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }, t('col_date')), /*#__PURE__*/React.createElement("th", {
    style: thStyle
  }))), /*#__PURE__*/React.createElement("tbody", null, shown.map(s => {
    const sc = STATUS_STYLES[s.statusKey];
    return /*#__PURE__*/React.createElement("tr", {
      key: s.id
    }, /*#__PURE__*/React.createElement("td", {
      style: {
        ...tdStyle,
        color: '#2563EB',
        fontWeight: 600
      }
    }, "#", s.id), /*#__PURE__*/React.createElement("td", {
      style: tdStyle
    }, s.patient), /*#__PURE__*/React.createElement("td", {
      style: tdStyle
    }, s.test), /*#__PURE__*/React.createElement("td", {
      style: tdStyle
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 600,
        background: s.priorityKey === 'priority_high' ? '#FEE2E2' : '#F1F5F9',
        color: s.priorityKey === 'priority_high' ? '#B91C1C' : '#64748B'
      }
    }, t(s.priorityKey))), /*#__PURE__*/React.createElement("td", {
      style: tdStyle
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '3px 10px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 600,
        background: sc.bg,
        color: sc.color
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: sc.dot,
        flexShrink: 0
      }
    }), t(s.statusKey))), /*#__PURE__*/React.createElement("td", {
      style: {
        ...tdStyle,
        color: '#64748B',
        fontSize: 12
      }
    }, s.date), /*#__PURE__*/React.createElement("td", {
      style: tdStyle
    }, /*#__PURE__*/React.createElement("button", {
      style: {
        background: 'none',
        border: 'none',
        fontSize: 12,
        fontWeight: 500,
        color: '#2563EB',
        cursor: 'pointer',
        fontFamily: cfg.font
      }
    }, s.statusKey === 'failed' ? t('act_retry') : t('act_view'))));
  }))));
}
Object.assign(window, {
  SamplesView
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/SamplesView.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/Sidebar.jsx
try { (() => {
// Sidebar.jsx — GULA Platform navigation sidebar (multilingual)
const {
  useContext: useCtxSidebar
} = React;
const NAV_KEYS = [{
  id: 'dashboard',
  key: 'nav_dashboard',
  section: 'nav_main',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "3",
    width: "7",
    height: "7"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "3",
    width: "7",
    height: "7"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "14",
    y: "14",
    width: "7",
    height: "7"
  }), /*#__PURE__*/React.createElement("rect", {
    x: "3",
    y: "14",
    width: "7",
    height: "7"
  }))
}, {
  id: 'patients',
  key: 'nav_patients',
  section: 'nav_main',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "9",
    cy: "7",
    r: "4"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M23 21v-2a4 4 0 0 0-3-3.87"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M16 3.13a4 4 0 0 1 0 7.75"
  }))
}, {
  id: 'samples',
  key: 'nav_samples',
  section: 'nav_main',
  badge: 5,
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"
  }))
}, {
  id: 'results',
  key: 'nav_results',
  section: 'nav_main',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("polyline", {
    points: "9 11 12 14 22 4"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"
  }))
}, {
  id: 'patient_profile',
  key: 'nav_patient_profile',
  section: 'nav_main',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"
  }), /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "7",
    r: "4"
  }))
}, {
  id: 'doctor_dash',
  key: 'nav_doctor_dash',
  section: 'nav_main',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M22 12h-4l-3 9L9 3l-3 9H2"
  }))
}, {
  id: 'lab_queue',
  key: 'nav_lab_queue',
  section: 'nav_main',
  badge: 3,
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "8",
    y1: "6",
    x2: "21",
    y2: "6"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "8",
    y1: "12",
    x2: "21",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "8",
    y1: "18",
    x2: "21",
    y2: "18"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "3",
    y1: "6",
    x2: "3.01",
    y2: "6"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "3",
    y1: "12",
    x2: "3.01",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "3",
    y1: "18",
    x2: "3.01",
    y2: "18"
  }))
}, {
  id: 'reports',
  key: 'nav_reports',
  section: 'nav_manage',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
  }), /*#__PURE__*/React.createElement("polyline", {
    points: "14 2 14 8 20 8"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "16",
    y1: "13",
    x2: "8",
    y2: "13"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "16",
    y1: "17",
    x2: "8",
    y2: "17"
  }))
}, {
  id: 'billing',
  key: 'nav_billing',
  section: 'nav_manage',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "1",
    x2: "12",
    y2: "23"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"
  }))
}, {
  id: 'settings',
  key: 'nav_settings',
  section: 'nav_system',
  icon: /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    width: "16",
    height: "16"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "3"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M19.07 4.93a10 10 0 1 1-14.14 0"
  }))
}];
const sidebarStyles = {
  sidebar: dir => ({
    width: 220,
    minWidth: 220,
    height: '100%',
    background: '#fff',
    borderRight: dir === 'ltr' ? '1px solid #E2E8F0' : 'none',
    borderLeft: dir === 'rtl' ? '1px solid #E2E8F0' : 'none',
    display: 'flex',
    flexDirection: 'column',
    padding: '20px 0',
    flexShrink: 0
  }),
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '0 18px 20px',
    borderBottom: '1px solid #E2E8F0',
    marginBottom: 12
  },
  logoMark: {
    width: 36,
    height: 36,
    flexShrink: 0
  },
  logoText: {
    fontSize: 15,
    fontWeight: 700,
    letterSpacing: '-0.02em'
  },
  logoSub: {
    fontSize: 10,
    color: '#94A3B8',
    fontWeight: 500
  },
  section: {
    fontSize: 9,
    fontWeight: 600,
    color: '#94A3B8',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    padding: '10px 18px 4px'
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: 9,
    padding: '8px 18px',
    margin: '1px 8px',
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 500,
    color: '#475569',
    cursor: 'pointer'
  },
  itemActive: {
    background: '#EFF6FF',
    color: '#2563EB'
  },
  badge: {
    marginLeft: 'auto',
    background: '#EF4444',
    color: '#fff',
    fontSize: 9,
    fontWeight: 700,
    borderRadius: 9999,
    padding: '1px 6px'
  },
  badgeRtl: {
    marginRight: 'auto',
    marginLeft: 0
  },
  bottom: {
    marginTop: 'auto',
    padding: '12px 8px 0',
    borderTop: '1px solid #E2E8F0'
  },
  user: {
    display: 'flex',
    alignItems: 'center',
    gap: 9,
    padding: '8px 10px',
    borderRadius: 8,
    cursor: 'pointer'
  },
  avatar: {
    width: 30,
    height: 30,
    borderRadius: '50%',
    background: 'linear-gradient(135deg,#2563EB,#8B5CF6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
    fontWeight: 700,
    fontSize: 12,
    flexShrink: 0
  },
  userName: {
    fontSize: 12,
    fontWeight: 600,
    color: '#0F172A'
  },
  userRole: {
    fontSize: 10,
    color: '#94A3B8'
  }
};
function Sidebar({
  active,
  onNavigate,
  dark
}) {
  const {
    t,
    lang
  } = useCtxSidebar(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#475569';
  const activeItem = dark ? {
    background: '#1D3461',
    color: '#60A5FA'
  } : sidebarStyles.itemActive;
  const sections = ['nav_main', 'nav_manage', 'nav_system'];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      ...sidebarStyles.sidebar(dir),
      fontFamily: cfg.font,
      direction: dir,
      background: 'inherit',
      height: '100%'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: sidebarStyles.logo
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-mark.svg",
    style: sidebarStyles.logoMark,
    alt: "GULA"
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      ...sidebarStyles.logoText,
      color: fg1
    }
  }, "GULA"), /*#__PURE__*/React.createElement("div", {
    style: sidebarStyles.logoSub
  }, "Lab Platform"))), sections.map(sec => {
    const items = NAV_KEYS.filter(n => n.section === sec);
    if (!items.length) return null;
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: sec
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        ...sidebarStyles.section,
        color: dark ? '#475569' : '#94A3B8'
      }
    }, t(sec)), items.map(n => /*#__PURE__*/React.createElement("div", {
      key: n.id,
      style: {
        ...sidebarStyles.item,
        color: fg2,
        ...(active === n.id ? activeItem : {})
      },
      onClick: () => onNavigate(n.id)
    }, n.icon, t(n.key), n.badge && /*#__PURE__*/React.createElement("span", {
      style: {
        ...sidebarStyles.badge,
        ...(dir === 'rtl' ? sidebarStyles.badgeRtl : {})
      }
    }, n.badge))));
  }), /*#__PURE__*/React.createElement("div", {
    style: sidebarStyles.bottom
  }, /*#__PURE__*/React.createElement("div", {
    style: sidebarStyles.user
  }, /*#__PURE__*/React.createElement("div", {
    style: sidebarStyles.avatar
  }, "A"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: sidebarStyles.userName
  }, "Ahmed Al-Rashidi"), /*#__PURE__*/React.createElement("div", {
    style: sidebarStyles.userRole
  }, "Lab Manager")))));
}
Object.assign(window, {
  Sidebar
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/Sidebar.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/TopBar.jsx
try { (() => {
// TopBar.jsx — GULA Platform top bar (multilingual + dark mode)
const {
  useContext: useCtxTop
} = React;
const PAGE_KEY_MAP = {
  dashboard: 'nav_dashboard',
  patients: 'nav_patients',
  samples: 'nav_samples',
  results: 'nav_results',
  reports: 'nav_reports',
  billing: 'nav_billing',
  settings: 'nav_settings'
};
function TopBar({
  page,
  lang,
  setLang,
  dark,
  setDark
}) {
  const {
    t
  } = useCtxTop(LangContext);
  const cfg = LANGS[lang];
  const dir = cfg.dir;
  const bg = dark ? '#1E293B' : '#fff';
  const border = dark ? '#334155' : '#E2E8F0';
  const fg1 = dark ? '#F1F5F9' : '#0F172A';
  const fg2 = dark ? '#94A3B8' : '#475569';
  const searchBg = dark ? '#0F172A' : '#F8FAFC';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      height: 58,
      background: bg,
      borderBottom: `1px solid ${border}`,
      display: 'flex',
      alignItems: 'center',
      padding: '0 20px',
      gap: 12,
      flexShrink: 0,
      direction: dir,
      fontFamily: cfg.font
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 700,
      color: fg1,
      flex: 1
    }
  }, t(PAGE_KEY_MAP[page] || 'nav_dashboard')), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      background: searchBg,
      border: `1.5px solid ${border}`,
      borderRadius: 8,
      padding: '6px 12px',
      width: 200
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "14",
    height: "14",
    fill: "none",
    stroke: "#94A3B8",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round",
    style: {
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "11",
    cy: "11",
    r: "8"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "21",
    y1: "21",
    x2: "16.65",
    y2: "16.65"
  })), /*#__PURE__*/React.createElement("input", {
    style: {
      border: 'none',
      background: 'transparent',
      outline: 'none',
      fontSize: 12,
      color: fg2,
      width: '100%',
      fontFamily: cfg.font,
      direction: dir
    },
    placeholder: t('search_placeholder')
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      padding: '3px 10px',
      borderRadius: 9999,
      background: '#DCFCE7',
      color: '#15803D',
      fontSize: 11,
      fontWeight: 600,
      flexShrink: 0,
      whiteSpace: 'nowrap'
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "8",
    height: "8",
    fill: "#10B981"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "12"
  })), t('system_online')), /*#__PURE__*/React.createElement("div", {
    onClick: () => setDark(d => !d),
    title: "Toggle dark mode",
    style: {
      width: 34,
      height: 34,
      borderRadius: 8,
      border: `1.5px solid ${border}`,
      background: bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      flexShrink: 0
    }
  }, dark ? /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: "#F59E0B",
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("circle", {
    cx: "12",
    cy: "12",
    r: "5"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "1",
    x2: "12",
    y2: "3"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "12",
    y1: "21",
    x2: "12",
    y2: "23"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "4.22",
    y1: "4.22",
    x2: "5.64",
    y2: "5.64"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "18.36",
    y1: "18.36",
    x2: "19.78",
    y2: "19.78"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "1",
    y1: "12",
    x2: "3",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "21",
    y1: "12",
    x2: "23",
    y2: "12"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "4.22",
    y1: "19.78",
    x2: "5.64",
    y2: "18.36"
  }), /*#__PURE__*/React.createElement("line", {
    x1: "18.36",
    y1: "5.64",
    x2: "19.78",
    y2: "4.22"
  })) : /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: fg2,
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 34,
      height: 34,
      borderRadius: 8,
      border: `1.5px solid ${border}`,
      background: bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      cursor: 'pointer',
      position: 'relative',
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 24 24",
    width: "16",
    height: "16",
    fill: "none",
    stroke: fg2,
    strokeWidth: "2",
    strokeLinecap: "round",
    strokeLinejoin: "round"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M13.73 21a2 2 0 0 1-3.46 0"
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      top: 6,
      right: 6,
      width: 7,
      height: 7,
      background: '#EF4444',
      borderRadius: '50%',
      border: `1.5px solid ${bg}`
    }
  })), /*#__PURE__*/React.createElement(LangSwitcher, {
    lang: lang,
    setLang: setLang
  }));
}
Object.assign(window, {
  TopBar
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/TopBar.jsx", error: String((e && e.message) || e) }); }

})();
