import { useState } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';
import { motion } from 'motion/react';
import { 
  User, 
  Calendar, 
  Phone, 
  Mail, 
  Fingerprint, 
  ArrowRight, 
  CheckCircle2, 
  AlertCircle,
  ShieldCheck,
  Smartphone,
  MapPin
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { toast } from 'sonner';

export function PatientRegistration() {
  const { t, language } = useLanguage();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    fullName: '',
    dob: '',
    gender: 'male',
    phone: '',
    email: '',
    nationalId: '',
    street: '',
    city: '',
    state: '',
    zip: '',
    country: 'Iraq'
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateField = (name: string, value: string) => {
    let error = '';
    if (name === 'fullName' && !value) error = 'Full name is required';
    if (name === 'dob' && !value) error = 'Date of birth is required';
    if (name === 'phone' && !value.match(/^\+?[0-9]{10,14}$/)) error = 'Invalid phone number';
    if (name === 'email' && value && !value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) error = 'Invalid email';
    if (name === 'nationalId' && !value.match(/^[0-9]{12}$/)) error = 'National ID must be 12 digits';
    if (name === 'street' && !value) error = 'Street address is required';
    if (name === 'city' && !value) error = 'City is required';
    if (name === 'state' && !value) error = 'Governorate/State is required';
    if (name === 'zip' && !value) error = 'Zip/Postal code is required';
    
    setErrors(prev => ({ ...prev, [name]: error }));
    return !error;
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    validateField(field, value);
  };

  const validate = () => {
    const fieldsToValidate = ['fullName', 'dob', 'phone', 'nationalId', 'street', 'city', 'state', 'zip'];
    let isValid = true;
    fieldsToValidate.forEach(field => {
      if (!validateField(field, formData[field as keyof typeof formData])) {
        isValid = false;
      }
    });

    // Special check for email since it's optional but needs format check if present
    if (formData.email && !validateField('email', formData.email)) {
      isValid = false;
    }

    return isValid;
  };

  const isRtl = language === 'AR' || language === 'KU' || language === 'SY';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    // Simulated Registration with Network Awareness
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setIsSuccess(true);
      toast.success(isRtl ? 'تم تسجيل البيانات بنجاح' : 'Registration completed successfully');
    } catch (error) {
      toast.error('Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="p-8 max-w-2xl mx-auto flex items-center justify-center min-h-[60vh]">
        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-6"
        >
          <div className="w-24 h-24 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 size={48} />
          </div>
          <h2 className="text-3xl font-black text-slate-900">
            {isRtl ? 'تم طلب التسجيل' : 'Registration Requested'}
          </h2>
          <p className="text-slate-500 max-w-md mx-auto">
            {isRtl 
              ? 'بياناتك قيد المراجعة الآن. ستتلقى رمز "هوية جولا الرقمية" (GULA ID) عبر الرسائل النصية قريباً.' 
              : 'Your data is being verified. You will receive your GULA ID via SMS shortly.'}
          </p>
          <button 
            onClick={() => window.location.reload()}
            className="px-8 py-4 bg-slate-900 text-white rounded-2xl font-bold hover:shadow-xl transition-all"
          >
            {isRtl ? 'العودة للرئيسية' : 'Back to Dashboard'}
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center gap-6 mb-12">
        <div className="p-4 bg-indigo-600 text-white rounded-3xl shadow-xl shadow-indigo-100">
          <Fingerprint size={32} />
        </div>
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">
            {isRtl ? 'تسجيل الهوية الصحية' : 'Digital Health Identity'}
          </h1>
          <p className="text-slate-500 font-medium">Join the unified national clinical network</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Personal Info */}
          <section className="space-y-6 bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <User size={18} className="text-indigo-600" />
              <h3 className="font-black text-sm uppercase tracking-widest text-slate-400">Personal Information</h3>
            </div>
            
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Full Name (as per ID)</label>
              <input 
                type="text"
                value={formData.fullName}
                onChange={e => handleInputChange('fullName', e.target.value)}
                className={cn(
                  "w-full bg-slate-50 border rounded-2xl p-4 text-sm focus:ring-2 focus:ring-indigo-600 transition-all",
                  errors.fullName ? "border-red-300 ring-1 ring-red-100" : (formData.fullName ? "border-emerald-300" : "border-slate-100")
                )}
                placeholder="Ex: Ahmed Yaseen..."
              />
              {errors.fullName && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.fullName}</p>}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Date of Birth</label>
                <div className="relative">
                  <Calendar className="absolute left-4 top-4 text-slate-400" size={16} />
                  <input 
                    type="date"
                    value={formData.dob}
                    onChange={e => handleInputChange('dob', e.target.value)}
                    className={cn(
                      "w-full bg-slate-50 border rounded-2xl p-4 pl-12 text-sm focus:ring-2 focus:ring-indigo-600 transition-all",
                      errors.dob ? "border-red-300 ring-1 ring-red-100" : (formData.dob ? "border-emerald-300" : "border-slate-100")
                    )}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Gender</label>
                <select 
                  value={formData.gender}
                  onChange={e => setFormData({...formData, gender: e.target.value})}
                  className="w-full bg-slate-50 border border-slate-100 rounded-2xl p-4 text-sm focus:ring-2 focus:ring-indigo-600"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase text-slate-400 ml-1">National ID (12 Digits)</label>
              <div className="relative">
                <Fingerprint className="absolute left-4 top-4 text-slate-400" size={16} />
                <input 
                  type="text"
                  value={formData.nationalId}
                  onChange={e => handleInputChange('nationalId', e.target.value)}
                  className={cn(
                    "w-full bg-slate-50 border rounded-2xl p-4 pl-12 text-sm font-mono tracking-widest transition-all",
                    errors.nationalId ? "border-red-300 ring-1 ring-red-100" : (formData.nationalId && !errors.nationalId ? "border-emerald-300" : "border-slate-100")
                  )}
                  placeholder="0000 0000 0000"
                />
              </div>
              {errors.nationalId && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.nationalId}</p>}
            </div>
          </section>

          {/* Contact Info */}
          <section className="space-y-6 bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <Smartphone size={18} className="text-indigo-600" />
              <h3 className="font-black text-sm uppercase tracking-widest text-slate-400">Communication</h3>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Phone Number</label>
              <div className="relative">
                <Phone className="absolute left-4 top-4 text-slate-400" size={16} />
                <input 
                  type="tel"
                  value={formData.phone}
                  onChange={e => handleInputChange('phone', e.target.value)}
                  className={cn(
                    "w-full bg-slate-50 border rounded-2xl p-4 pl-12 text-sm transition-all",
                    errors.phone ? "border-red-300 ring-1 ring-red-100" : (formData.phone && !errors.phone ? "border-emerald-300" : "border-slate-100")
                  )}
                  placeholder="+964..."
                />
              </div>
              {errors.phone && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.phone}</p>}
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Email Address (Optional)</label>
              <div className="relative">
                <Mail className="absolute left-4 top-4 text-slate-400" size={16} />
                <input 
                  type="email"
                  value={formData.email}
                  onChange={e => handleInputChange('email', e.target.value)}
                  className={cn(
                    "w-full bg-slate-50 border rounded-2xl p-4 pl-12 text-sm transition-all",
                    errors.email ? "border-red-300 ring-1 ring-red-100" : (formData.email && !errors.email ? "border-emerald-300" : "border-slate-100")
                  )}
                  placeholder="name@example.com"
                />
              </div>
              {errors.email && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.email}</p>}
            </div>

            <div className="p-4 bg-indigo-50/50 border border-indigo-100 rounded-3xl mt-4">
              <div className="flex gap-3">
                <ShieldCheck size={20} className="text-indigo-600 shrink-0" />
                <p className="text-[10px] text-indigo-900 leading-relaxed font-medium">
                  Your data is encrypted using GULA Secure Protocol. National ID verification is required for access to full medical history.
                </p>
              </div>
            </div>
          </section>

          {/* Address Info */}
          <section className="space-y-6 bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm md:col-span-2">
            <div className="flex items-center gap-3 mb-2">
              <MapPin size={18} className="text-indigo-600" />
              <h3 className="font-black text-sm uppercase tracking-widest text-slate-400">Physical Address</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2 space-y-2">
                <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Street Address</label>
                <input 
                  type="text"
                  value={formData.street}
                  onChange={e => handleInputChange('street', e.target.value)}
                  className={cn(
                    "w-full bg-slate-50 border rounded-2xl p-4 text-sm focus:ring-2 focus:ring-indigo-600 transition-all",
                    errors.street ? "border-red-300 ring-1 ring-red-100" : (formData.street && !errors.street ? "border-emerald-300" : "border-slate-100")
                  )}
                  placeholder="Street name, Building number..."
                />
                {errors.street && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.street}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-slate-400 ml-1">City</label>
                <input 
                  type="text"
                  value={formData.city}
                  onChange={e => handleInputChange('city', e.target.value)}
                  className={cn(
                    "w-full bg-slate-50 border rounded-2xl p-4 text-sm focus:ring-2 focus:ring-indigo-600 transition-all",
                    errors.city ? "border-red-300 ring-1 ring-red-100" : (formData.city && !errors.city ? "border-emerald-300" : "border-slate-100")
                  )}
                  placeholder="Ex: Erbil, Baghdad..."
                />
                {errors.city && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.city}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Governorate / State</label>
                <input 
                  type="text"
                  value={formData.state}
                  onChange={e => handleInputChange('state', e.target.value)}
                  className={cn(
                    "w-full bg-slate-50 border rounded-2xl p-4 text-sm focus:ring-2 focus:ring-indigo-600 transition-all",
                    errors.state ? "border-red-300 ring-1 ring-red-100" : (formData.state && !errors.state ? "border-emerald-300" : "border-slate-100")
                  )}
                  placeholder="State name..."
                />
                {errors.state && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.state}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Zip / Postal Code</label>
                <input 
                  type="text"
                  value={formData.zip}
                  onChange={e => handleInputChange('zip', e.target.value)}
                  className={cn(
                    "w-full bg-slate-50 border rounded-2xl p-4 text-sm focus:ring-2 focus:ring-indigo-600 transition-all",
                    errors.zip ? "border-red-300 ring-1 ring-red-100" : (formData.zip && !errors.zip ? "border-emerald-300" : "border-slate-100")
                  )}
                  placeholder="Zip code..."
                />
                {errors.zip && <p className="text-red-500 text-[10px] font-bold mt-1 uppercase">{errors.zip}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-slate-400 ml-1">Country</label>
                <select 
                  value={formData.country}
                  onChange={e => setFormData({...formData, country: e.target.value})}
                  className="w-full bg-slate-50 border border-slate-100 rounded-2xl p-4 text-sm focus:ring-2 focus:ring-indigo-600"
                >
                  <option value="Iraq">Iraq</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
          </section>
        </div>

        <div className="flex justify-between items-center bg-slate-900 p-6 rounded-[2rem] text-white overflow-hidden relative">
          <div className="flex items-center gap-4 relative z-10">
            <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur">
              <AlertCircle size={20} />
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-white/50">Data Acknowledgement</p>
              <p className="text-xs font-medium text-white/90">Clicking register confirms your clinical consent.</p>
            </div>
          </div>
          
          <button 
            type="submit"
            disabled={isSubmitting}
            className="px-10 py-5 bg-indigo-600 rounded-2xl font-black uppercase tracking-widest text-xs hover:bg-indigo-500 transition-all flex items-center gap-3 shadow-2xl relative z-10 disabled:opacity-50"
          >
            {isSubmitting ? (
              <span className="animate-pulse">Processing...</span>
            ) : (
              <>
                Register Entry <ArrowRight size={16} />
              </>
            )}
          </button>
          
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full -mr-32 -mt-32 blur-3xl pointer-events-none" />
        </div>
      </form>
    </div>
  );
}
