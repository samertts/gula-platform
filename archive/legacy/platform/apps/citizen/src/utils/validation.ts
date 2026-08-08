import { NATIONAL_ID_LENGTH, PHONE_LENGTH, OTP_LENGTH } from './constants';

export interface ValidationResult {
  valid: boolean;
  error?: string;
  errorEn?: string;
}

export function validateIraqiNationalId(id: string): ValidationResult {
  const cleaned = id.replace(/\D/g, '');
  if (!cleaned) {
    return { valid: false, error: 'الرجاء إدخال الرقم الوطني', errorEn: 'Please enter national ID' };
  }
  if (cleaned.length !== NATIONAL_ID_LENGTH) {
    return {
      valid: false,
      error: `الرقم الوطني يجب أن يتكون من ${NATIONAL_ID_LENGTH} رقم`,
      errorEn: `National ID must be ${NATIONAL_ID_LENGTH} digits`,
    };
  }
  return { valid: true };
}

export function validatePhone(phone: string): ValidationResult {
  const cleaned = phone.replace(/\D/g, '');
  if (!cleaned) {
    return { valid: false, error: 'الرجاء إدخال رقم الهاتف', errorEn: 'Please enter phone number' };
  }
  if (cleaned.length < 10 || cleaned.length > 11) {
    return { valid: false, error: 'رقم الهاتف غير صحيح', errorEn: 'Invalid phone number' };
  }
  if (!cleaned.startsWith('07') && !cleaned.startsWith('7')) {
    return { valid: false, error: 'رقم الهاتف يجب أن يبدأ بـ 07', errorEn: 'Phone must start with 07' };
  }
  return { valid: true };
}

export function validateEmail(email: string): ValidationResult {
  if (!email) {
    return { valid: false, error: 'الرجاء إدخال البريد الإلكتروني', errorEn: 'Please enter email' };
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { valid: false, error: 'البريد الإلكتروني غير صحيح', errorEn: 'Invalid email address' };
  }
  return { valid: true };
}

export function validateOTP(otp: string): ValidationResult {
  const cleaned = otp.replace(/\D/g, '');
  if (!cleaned) {
    return { valid: false, error: 'الرجاء إدخال رمز التحقق', errorEn: 'Please enter OTP' };
  }
  if (cleaned.length !== OTP_LENGTH) {
    return {
      valid: false,
      error: `رمز التحقق يجب أن يتكون من ${OTP_LENGTH} أرقام`,
      errorEn: `OTP must be ${OTP_LENGTH} digits`,
    };
  }
  return { valid: true };
}

export function validateRequired(value: string, fieldName: string, fieldNameEn: string): ValidationResult {
  if (!value || !value.trim()) {
    return {
      valid: false,
      error: `الرجاء إدخال ${fieldName}`,
      errorEn: `Please enter ${fieldNameEn}`,
    };
  }
  return { valid: true };
}

export function validateMinLength(value: string, min: number, fieldName: string): ValidationResult {
  if (value.length < min) {
    return {
      valid: false,
      error: `يجب أن يكون ${fieldName} على الأقل ${min} أحرف`,
      errorEn: `${fieldName} must be at least ${min} characters`,
    };
  }
  return { valid: true };
}

export function validateBloodType(type: string): ValidationResult {
  const validTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
  if (!validTypes.includes(type)) {
    return { valid: false, error: 'فصيلة الدم غير صحيحة', errorEn: 'Invalid blood type' };
  }
  return { valid: true };
}

export function validateName(name: string): ValidationResult {
  if (!name || !name.trim()) {
    return { valid: false, error: 'الرجاء إدخال الاسم', errorEn: 'Please enter name' };
  }
  if (name.trim().length < 3) {
    return { valid: false, error: 'الاسم يجب أن يكون 3 أحرف على الأقل', errorEn: 'Name must be at least 3 characters' };
  }
  if (name.trim().length > 100) {
    return { valid: false, error: 'الاسم طويل جداً', errorEn: 'Name is too long' };
  }
  return { valid: true };
}

export function validateDateOfBirth(dob: string): ValidationResult {
  if (!dob) {
    return { valid: false, error: 'الرجاء إدخال تاريخ الميلاد', errorEn: 'Please enter date of birth' };
  }
  const date = new Date(dob);
  const now = new Date();
  if (isNaN(date.getTime())) {
    return { valid: false, error: 'تاريخ الميلاد غير صحيح', errorEn: 'Invalid date of birth' };
  }
  if (date > now) {
    return { valid: false, error: 'تاريخ الميلاد لا يمكن أن يكون في المستقبل', errorEn: 'Date of birth cannot be in the future' };
  }
  return { valid: true };
}
