import type { ReactNode, SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function createIcon(path: ReactNode, viewBox = '0 0 24 24') {
  return ({ size = 24, className, ...props }: IconProps) => (
    <svg
      width={size}
      height={size}
      viewBox={viewBox}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      {...props}
    >
      {path}
    </svg>
  );
}

export const LabTest = createIcon(
  <><path d="M8 2v4l-3 5v10h14V11l-3-5V2" /><path d="M8 14h8" /><path d="M12 10v8" /></>
);

export const Radiology = createIcon(
  <><circle cx="12" cy="12" r="10" /><path d="M12 6v12M6 12h12" /></>
);

export const Pharmacy = createIcon(
  <><path d="M10 4a2 2 0 00-2 2v2h8V6a2 2 0 00-2-2h-4z" /><path d="M6 8v10a2 2 0 002 2h8a2 2 0 002-2V8" /><path d="M10 12v4" /><path d="M14 12v4" /></>
);

export const Hospital = createIcon(
  <><rect x="4" y="2" width="16" height="20" rx="2" /><path d="M9 22v-6h6v6" /><path d="M12 10v4" /><path d="M10 12h4" /></>
);

export const Patient = createIcon(
  <><circle cx="12" cy="8" r="4" /><path d="M20 21a8 8 0 10-16 0" /></>
);

export const Doctor = createIcon(
  <><circle cx="12" cy="8" r="4" /><path d="M20 21a8 8 0 00-16 0" /><path d="M10 14l2 2 4-4" /></>
);

export const Nurse = createIcon(
  <><path d="M12 4v12M6 10h12" /><circle cx="12" cy="17" r="5" /></>
);

export const Emergency = createIcon(
  <><polygon points="13 2 3 14 12 14 11 22 21 10 12 10" /></>
);

export const Ambulance = createIcon(
  <><rect x="2" y="10" width="20" height="10" rx="2" /><path d="M8 20a2 2 0 100-4 2 2 0 000 4z" /><path d="M18 20a2 2 0 100-4 2 2 0 000 4z" /><path d="M12 10V4M9 7h6" /></>
);

export const BloodDrop = createIcon(
  <><path d="M12 21.5c-3.3 0-6-2.4-6-5.8 0-4.4 4-9.7 6-11.8 2 2.1 6 7.4 6 11.8 0 3.4-2.7 5.8-6 5.8z" /></>
);

export const Vaccine = createIcon(
  <><path d="M18 6l-3 3" /><path d="M8 16l-3 3" /><path d="M10 14l2 2" /><path d="M14 10l2 2" /><path d="M12 12l2 2" /><rect x="6" y="10" width="12" height="12" rx="2" /><path d="M10 2v4M14 2v4M12 6v4" /></>
);

export const Prescription = createIcon(
  <><path d="M4 3h10a4 4 0 010 8H4" /><path d="M4 11v10" /><path d="M14 13l5 5" /><path d="M14 18l5-5" /></>
);

export const Appointment = createIcon(
  <><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M3 10h18" /><path d="M8 2v4" /><path d="M16 2v4" /><path d="M8 14h.01" /><path d="M12 14h.01" /><path d="M16 14h.01" /><path d="M8 18h.01" /><path d="M12 18h.01" /></>
);

export const HealthCard = createIcon(
  <><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /><path d="M6 14h.01" /><path d="M10 14h4" /></>
);

export const QRCode = createIcon(
  <><rect x="3" y="3" width="6" height="6" rx="1" /><rect x="15" y="3" width="6" height="6" rx="1" /><rect x="15" y="15" width="6" height="6" rx="1" /><path d="M3 15h3v3H3z" /><path d="M9 15v6" /><path d="M15 9v3" /><path d="M9 12h3" /></>
);

export const Offline = createIcon(
  <><path d="M12 2a10 10 0 0110 10" /><path d="M2 12a10 10 0 0110-10" /><path d="M4.9 4.9l14.2 14.2" /><path d="M2 12h2" /><path d="M20 12h2" /></>
);

export const Sync = createIcon(
  <><path d="M21 2v6h-6" /><path d="M3 12a9 9 0 0115.4-5.4L21 8" /><path d="M3 22v-6h6" /><path d="M21 12a9 9 0 01-15.4 5.4L3 16" /></>
);

export const Family = createIcon(
  <><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></>
);

export const Consent = createIcon(
  <><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0110 0v4" /><path d="M12 15v3" /></>
);

export const Telemedicine = createIcon(
  <><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></>
);

export const BloodTest = createIcon(
  <><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" /><path d="M14 2v6h6" /><path d="M9 13v4" /><path d="M12 15v2" /><path d="M15 11v6" /></>
);

export const Report = createIcon(
  <><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" /><path d="M14 2v6h6" /><path d="M8 13h8" /><path d="M8 17h8" /><path d="M8 9h1" /></>
);

export const LabDevice = createIcon(
  <><rect x="5" y="3" width="14" height="18" rx="2" /><path d="M8 9h8" /><path d="M8 13h8" /><path d="M8 17h5" /></>
);

export const Result = createIcon(
  <><circle cx="12" cy="12" r="10" /><path d="M8 12l2.5 2.5L16 9" /></>
);
