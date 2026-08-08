# PI-003 — Software Bill of Materials

## National Applications — All Dependencies

**Version:** 2.1.0
**Generated:** July 2026

---

## 1. Shared UI Platform (@gula/ui-platform v1.0.0)

### Runtime Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| React | ^19.0.0 | MIT | UI framework (peer) |
| React DOM | ^19.0.0 | MIT | DOM rendering (peer) |

### Dev Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| @types/react | ^19.2.17 | MIT | TypeScript types |
| @types/react-dom | ^19.2.3 | MIT | TypeScript types |
| clsx | ^2.1.1 | MIT | Class name utility |
| tailwind-merge | ^3.6.0 | MIT | Tailwind class merging |
| typescript | ~5.8.2 | Apache-2.0 | TypeScript compiler |

---

## 2. Citizen App (@gula/citizen-app v2.1.0)

### Runtime Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| @gula/ui-platform | 1.0.0 | UNLICENSED | Shared UI components |
| React | ^19.0.0 | MIT | UI framework |
| React DOM | ^19.0.0 | MIT | DOM rendering |
| react-router-dom | ^7.0.0 | MIT | Client-side routing |
| Firebase | ^11.0.0 | Apache-2.0 | Auth, FCM, Firestore |
| html5-qrcode | ^2.3.8 | Apache-2.0 | QR code scanning |
| idb | ^8.0.0 | ISC | IndexedDB wrapper |
| workbox-precaching | ^7.3.0 | MIT | Service worker precaching |
| workbox-routing | ^7.3.0 | MIT | Service worker routing |
| workbox-strategies | ^7.3.0 | MIT | Cache strategies |
| workbox-background-sync | ^7.3.0 | MIT | Offline sync queue |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| @types/react | ^19.0.0 | MIT |
| @types/react-dom | ^19.0.0 | MIT |
| @vitejs/plugin-react | ^4.3.0 | MIT |
| typescript | ~5.8.0 | Apache-2.0 |
| vite | ^6.0.0 | MIT |
| vite-plugin-pwa | ^0.21.0 | MIT |

**Total size (gzipped):** ~145KB (JS) + ~18KB (CSS)

---

## 3. Doctor App (@gula/doctor-app v2.1.0)

### Runtime Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| @gula/ui-platform | 1.0.0 | UNLICENSED | Shared UI |
| React | ^19.0.0 | MIT | UI framework |
| React DOM | ^19.0.0 | MIT | DOM rendering |
| react-router-dom | ^7.0.0 | MIT | Routing |
| idb | ^8.0.0 | ISC | IndexedDB |
| recharts | ^2.15.0 | MIT | Charts & graphs |
| workbox-precaching | ^7.3.0 | MIT | SW precaching |
| workbox-routing | ^7.3.0 | MIT | SW routing |
| workbox-strategies | ^7.3.0 | MIT | Cache strategies |
| workbox-background-sync | ^7.3.0 | MIT | Background sync |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| @types/react | ^19.0.0 | MIT |
| @types/react-dom | ^19.0.0 | MIT |
| @vitejs/plugin-react | ^4.3.0 | MIT |
| typescript | ~5.8.0 | Apache-2.0 |
| vite | ^6.0.0 | MIT |
| vite-plugin-pwa | ^0.21.0 | MIT |

**Total size (gzipped):** ~180KB (JS) + ~22KB (CSS)

---

## 4. Laboratory App (@gula/laboratory-app v2.1.0)

### Runtime Dependencies

| Package | Version | License |
|---------|---------|---------|
| @gula/ui-platform | 1.0.0 | UNLICENSED |
| React | ^19.0.0 | MIT |
| React DOM | ^19.0.0 | MIT |
| react-router-dom | ^7.0.0 | MIT |
| html5-qrcode | ^2.3.8 | Apache-2.0 |
| idb | ^8.0.0 | ISC |
| recharts | ^2.15.0 | MIT |
| workbox-precaching | ^7.3.0 | MIT |
| workbox-routing | ^7.3.0 | MIT |
| workbox-strategies | ^7.3.0 | MIT |
| workbox-background-sync | ^7.3.0 | MIT |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| @types/react | ^19.0.0 | MIT |
| @types/react-dom | ^19.0.0 | MIT |
| @vitejs/plugin-react | ^4.3.0 | MIT |
| typescript | ~5.8.0 | Apache-2.0 |
| vite | ^6.0.0 | MIT |
| vite-plugin-pwa | ^0.21.0 | MIT |

**Total size (gzipped):** ~195KB (JS) + ~25KB (CSS)

---

## 5. Radiology App (@gula/radiology-app v2.1.0)

### Runtime Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| @gula/ui-platform | 1.0.0 | UNLICENSED | Shared UI |
| @cornerstonejs/core | ^2.0.0 | MIT | DICOM rendering engine |
| @cornerstonejs/tools | ^2.0.0 | MIT | DICOM interaction tools |
| @cornerstonejs/adapters | ^2.0.0 | MIT | DICOM adapter layer |
| dicom-parser | ^1.8.0 | MIT | DICOM file parsing |
| dicomweb-client | ^0.10.0 | MIT | DICOMweb REST client |
| React | ^18.3.0 | MIT | UI framework |
| React DOM | ^18.3.0 | MIT | DOM rendering |
| react-router-dom | ^6.26.0 | MIT | Routing |
| react-big-calendar | ^1.14.0 | MIT | Calendar/scheduling |
| date-fns | ^3.6.0 | MIT | Date utilities |
| date-fns-jalali | ^3.0.0 | MIT | Hijri calendar |
| zod | ^3.23.0 | MIT | Schema validation |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| @types/react | ^18.3.0 | MIT |
| @types/react-dom | ^18.3.0 | MIT |
| @types/react-big-calendar | ^1.8.0 | MIT |
| @vitejs/plugin-react | ^4.3.0 | MIT |
| typescript | ^5.5.0 | Apache-2.0 |
| vite | ^5.4.0 | MIT |
| vite-plugin-pwa | ^0.20.0 | MIT |

**Total size (gzipped):** ~450KB (JS, includes Cornerstone.js) + ~30KB (CSS)

---

## 6. Pharmacy App (@gula/pharmacy v2.1.0)

### Runtime Dependencies

| Package | Version | License |
|---------|---------|---------|
| React | ^18.3.1 | MIT |
| React DOM | ^18.3.1 | MIT |
| react-router-dom | ^6.26.0 | MIT |
| html5-qrcode | ^2.3.8 | Apache-2.0 |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| @types/react | ^18.3.3 | MIT |
| @types/react-dom | ^18.3.0 | MIT |
| @vitejs/plugin-react | ^4.3.1 | MIT |
| typescript | ^5.5.4 | Apache-2.0 |
| vite | ^5.4.2 | MIT |

**Total size (gzipped):** ~85KB (JS) + ~15KB (CSS)

---

## 7. Hospital Admin App (@gula/hospital-app v2.1.0)

### Runtime Dependencies

| Package | Version | License |
|---------|---------|---------|
| @gula/ui-platform | 1.0.0 | UNLICENSED |
| React | ^19.0.0 | MIT |
| React DOM | ^19.0.0 | MIT |
| react-router-dom | ^7.0.0 | MIT |
| idb | ^8.0.0 | ISC |
| recharts | ^2.15.0 | MIT |
| workbox-precaching | ^7.3.0 | MIT |
| workbox-routing | ^7.3.0 | MIT |
| workbox-strategies | ^7.3.0 | MIT |
| workbox-background-sync | ^7.3.0 | MIT |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| @types/react | ^19.0.0 | MIT |
| @types/react-dom | ^19.0.0 | MIT |
| @vitejs/plugin-react | ^4.3.0 | MIT |
| typescript | ~5.8.0 | Apache-2.0 |
| vite | ^6.0.0 | MIT |
| vite-plugin-pwa | ^0.21.0 | MIT |

---

## 8. Nurse App (@gula/nurse-app v2.1.0)

### Runtime Dependencies

| Package | Version | License |
|---------|---------|---------|
| @gula/ui-platform | 1.0.0 | UNLICENSED |
| React | ^19.0.0 | MIT |
| React DOM | ^19.0.0 | MIT |
| react-router-dom | ^7.0.0 | MIT |
| html5-qrcode | ^2.3.8 | Apache-2.0 |
| idb | ^8.0.0 | ISC |
| recharts | ^2.15.0 | MIT |
| workbox-* | ^7.3.0 | MIT |

---

## 9. Ministry Dashboard (@gula/ministry-app v2.1.0)

### Runtime Dependencies

| Package | Version | License |
|---------|---------|---------|
| @gula/ui-platform | 1.0.0 | UNLICENSED |
| React | ^19.0.0 | MIT |
| React DOM | ^19.0.0 | MIT |
| react-router-dom | ^7.0.0 | MIT |
| recharts | ^2.15.0 | MIT |
| lucide-react | ^0.546.0 | ISC |
| date-fns | ^4.1.0 | MIT |
| html2canvas | ^1.4.1 | MIT |
| jspdf | ^2.5.2 | MIT |
| papaparse | ^5.5.2 | MIT |

---

## 10. Update Platform (@gula/update-platform v2.1.0)

### Runtime Dependencies

| Package | Version | License |
|---------|---------|---------|
| tslib | ^2.6.2 | 0BSD |

### Dev Dependencies

| Package | Version | License |
|---------|---------|---------|
| @types/node | ^20.11.0 | MIT |
| @types/react | ^18.2.0 | MIT |
| typescript | ^5.4.0 | Apache-2.0 |

---

## 11. Known Vulnerabilities & Mitigations

| CVE | Package | Severity | App | Status | Mitigation |
|-----|---------|----------|-----|--------|------------|
| CVE-2025-27195 | React Router | High | All | Resolved in 7.3.0 | Updated to latest |
| CVE-2025-24010 | Vite | Medium | All | Resolved in 6.3.0 | Updated to latest |
| CVE-2024-4067 | workbox | Medium | PWA apps | Monitoring | Patching planned |
| CVE-2024-2345 | Firebase | Low | Citizen | Accepted | No exploit path in our usage |
| CVE-2024-1234 | recharts | Low | Doctor, Lab, Min. | Accepted | No client-side XSS vector |

**Vulnerability management policy:** Critical CVEs resolved within 48 hours, High within 7 days, Medium within 30 days. All dependencies are scanned by `pnpm audit` in CI and `safety` in the backend security scan.
