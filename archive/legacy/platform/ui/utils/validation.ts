export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export function validateIraqiNationalId(id: string): ValidationResult {
  const cleaned = id.replace(/[\s-]/g, '');
  if (!/^\d{14}$/.test(cleaned)) {
    return { valid: false, error: 'National ID must be exactly 14 digits' };
  }
  const year = parseInt(cleaned.substring(0, 4), 10);
  const month = parseInt(cleaned.substring(4, 6), 10);
  const day = parseInt(cleaned.substring(6, 8), 10);
  if (year < 1900 || year > new Date().getFullYear()) {
    return { valid: false, error: 'Invalid birth year in national ID' };
  }
  if (month < 1 || month > 12) {
    return { valid: false, error: 'Invalid birth month in national ID' };
  }
  if (day < 1 || day > 31) {
    return { valid: false, error: 'Invalid birth day in national ID' };
  }
  return { valid: true };
}

export function validatePhone(phone: string): ValidationResult {
  const cleaned = phone.replace(/[\s+\-()]/g, '');
  if (/^07\d{9}$/.test(cleaned)) {
    return { valid: true };
  }
  if (/^7\d{9}$/.test(cleaned)) {
    return { valid: true };
  }
  if (/^9647\d{9}$/.test(cleaned)) {
    return { valid: true };
  }
  if (/^\+9647\d{9}$/.test(cleaned)) {
    return { valid: true };
  }
  return { valid: false, error: 'Invalid phone number format. Use Iraqi mobile number (07xx xxx xxxx)' };
}

export function validateEmail(email: string): ValidationResult {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!email) {
    return { valid: false, error: 'Email is required' };
  }
  if (!emailRegex.test(email)) {
    return { valid: false, error: 'Invalid email format' };
  }
  if (email.length > 254) {
    return { valid: false, error: 'Email is too long' };
  }
  return { valid: true };
}

export function validateRequired(value: string, fieldName: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, error: `${fieldName} is required` };
  }
  return { valid: true };
}

export function validateMinLength(value: string, min: number, fieldName: string): ValidationResult {
  if (value.length < min) {
    return { valid: false, error: `${fieldName} must be at least ${min} characters` };
  }
  return { valid: true };
}

export function validateMaxLength(value: string, max: number, fieldName: string): ValidationResult {
  if (value.length > max) {
    return { valid: false, error: `${fieldName} must not exceed ${max} characters` };
  }
  return { valid: true };
}

export function validatePassword(password: string): ValidationResult {
  if (password.length < 8) {
    return { valid: false, error: 'Password must be at least 8 characters' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one uppercase letter' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one lowercase letter' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, error: 'Password must contain at least one number' };
  }
  return { valid: true };
}

export function validateBloodType(type: string): ValidationResult {
  const validTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
  if (!validTypes.includes(type.toUpperCase())) {
    return { valid: false, error: 'Invalid blood type' };
  }
  return { valid: true };
}

export function validateLabTestName(name: string): ValidationResult {
  if (!name || name.trim().length === 0) {
    return { valid: false, error: 'Test name is required' };
  }
  if (name.length > 200) {
    return { valid: false, error: 'Test name must not exceed 200 characters' };
  }
  return { valid: true };
}
