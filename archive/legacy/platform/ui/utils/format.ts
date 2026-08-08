export type Locale = 'ar' | 'en';

export function getLocale(): Locale {
  if (typeof document !== 'undefined') {
    const htmlLang = document.documentElement.lang;
    if (htmlLang === 'ar') return 'ar';
    const saved = localStorage.getItem('gula-locale');
    if (saved === 'ar') return 'ar';
  }
  return 'en';
}

export function formatDate(
  date: Date | string | number,
  options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  },
  locale?: Locale,
): string {
  const d = date instanceof Date ? date : new Date(date);
  const loc = locale ?? getLocale();
  return d.toLocaleDateString(loc === 'ar' ? 'ar-IQ' : 'en-US', options);
}

export function formatDateTime(
  date: Date | string | number,
  locale?: Locale,
): string {
  return formatDate(date, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }, locale);
}

export function formatRelativeTime(
  date: Date | string | number,
  locale?: Locale,
): string {
  const d = date instanceof Date ? date : new Date(date);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  const loc = locale ?? getLocale();
  const rtf = new Intl.RelativeTimeFormat(loc === 'ar' ? 'ar-IQ' : 'en-US', { numeric: 'auto' });

  if (diffSecs < 60) return rtf.format(-diffSecs, 'second');
  if (diffMins < 60) return rtf.format(-diffMins, 'minute');
  if (diffHours < 24) return rtf.format(-diffHours, 'hour');
  if (diffDays < 30) return rtf.format(-diffDays, 'day');
  return formatDate(d, undefined, loc);
}

export function formatNumber(
  value: number,
  options: Intl.NumberFormatOptions = {},
  locale?: Locale,
): string {
  const loc = locale ?? getLocale();
  return new Intl.NumberFormat(loc === 'ar' ? 'ar-IQ' : 'en-US', options).format(value);
}

export function formatCurrency(
  value: number,
  currency: string = 'IQD',
  locale?: Locale,
): string {
  return formatNumber(value, { style: 'currency', currency }, locale);
}

export function formatPercentage(
  value: number,
  locale?: Locale,
): string {
  return formatNumber(value, { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 }, locale);
}

export function formatPhone(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 11 && cleaned.startsWith('07')) {
    return `+964 ${cleaned.slice(1, 4)} ${cleaned.slice(4, 7)} ${cleaned.slice(7)}`;
  }
  if (cleaned.length === 10 && cleaned.startsWith('7')) {
    return `+964 ${cleaned.slice(0, 3)} ${cleaned.slice(3, 6)} ${cleaned.slice(6)}`;
  }
  if (cleaned.startsWith('964')) {
    const national = cleaned.slice(3);
    return `+964 ${national.slice(0, 3)} ${national.slice(3, 6)} ${national.slice(6)}`;
  }
  return phone;
}

export function formatNationalId(id: string): string {
  const cleaned = id.replace(/\D/g, '');
  if (cleaned.length === 14) {
    return cleaned.replace(/(\d{3})(\d{3})(\d{4})(\d{4})/, '$1-$2-$3-$4');
  }
  return id;
}

export function truncate(str: string, maxLength: number, ellipsis = '...'): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + ellipsis;
}
