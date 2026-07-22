export class DemoDataGenerator {
  private arabicFirstNames = [
    'محمد', 'أحمد', 'علي', 'حسن', 'حسين', 'عمر', 'خالد', 'إبراهيم',
    'فاطمة', 'زينب', 'مريم', 'سارة', 'نور', 'هدى', 'آمنة', 'رقية',
  ];

  private englishFirstNames = [
    'John', 'Sarah', 'Michael', 'Emily', 'David', 'Emma', 'James', 'Olivia',
  ];

  private arabicLastNames = [
    'العامري', 'الجبوري', 'التميمي', 'السهيل', 'الكبيسي', 'العاني',
    'البغدادي', 'النجفي', 'الكربلائي', 'الحلي', 'البصري', 'الموصلي',
  ];

  private englishLastNames = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
  ];

  private labNames = [
    { ar: 'مختبر الأمل الطبي', en: 'Al-Amal Medical Laboratory' },
    { ar: 'مختبر النور للتشخيص', en: 'Al-Noor Diagnostic Laboratory' },
    { ar: 'مختبر البركة المركزي', en: 'Al-Baraka Central Laboratory' },
    { ar: 'مختبر الفارابي', en: 'Al-Farabi Laboratory' },
    { ar: 'مختبر السلام الصحي', en: 'Al-Salam Health Laboratory' },
  ];

  private hospitalNames = [
    { ar: 'مستشفى بغداد التعليمي', en: 'Baghdad Teaching Hospital' },
    { ar: 'مستشفى ابن سينا', en: 'Ibn Sina Hospital' },
    { ar: 'مستشفى الكندي', en: 'Al-Kindi Hospital' },
    { ar: 'مستشفى الرشيد', en: 'Al-Rashid Hospital' },
  ];

  private testTypes = [
    { name: 'CBC', arName: 'صورة دم كاملة', unit: '', refRange: '' },
    { name: 'Glucose', arName: 'سكر الدم', unit: 'mg/dL', refRange: '70-110' },
    { name: 'HbA1c', arName: 'سكر تراكمي', unit: '%', refRange: '4.0-5.6' },
    { name: 'HDL', arName: 'دهون عالية الكثافة', unit: 'mg/dL', refRange: '40-60' },
    { name: 'LDL', arName: 'دهون منخفضة الكثافة', unit: 'mg/dL', refRange: '<100' },
    { name: 'Triglycerides', arName: 'دهون ثلاثية', unit: 'mg/dL', refRange: '<150' },
    { name: 'ALT', arName: 'إنزيم الكبد ALT', unit: 'U/L', refRange: '10-40' },
    { name: 'AST', arName: 'إنزيم الكبد AST', unit: 'U/L', refRange: '10-35' },
    { name: 'Creatinine', arName: 'كرياتينين', unit: 'mg/dL', refRange: '0.6-1.2' },
    { name: 'BUN', arName: 'يوريا الدم', unit: 'mg/dL', refRange: '7-20' },
    { name: 'WBC', arName: 'كريات بيض', unit: 'K/uL', refRange: '4.5-11.0' },
    { name: 'RBC', arName: 'كريات حمر', unit: 'M/uL', refRange: '4.5-5.9' },
    { name: 'Hemoglobin', arName: 'هيموغلوبين', unit: 'g/dL', refRange: '13.5-17.5' },
    { name: 'Platelets', arName: 'صفائح دموية', unit: 'K/uL', refRange: '150-450' },
    { name: 'TSH', arName: 'هرمون الغدة الدرقية', unit: 'mIU/L', refRange: '0.4-4.0' },
    { name: 'Vitamin D', arName: 'فيتامين د', unit: 'ng/mL', refRange: '30-100' },
  ];

  private idCounter = 0;

  private nextId(prefix: string): string {
    this.idCounter++;
    return `${prefix}-${Date.now()}-${this.idCounter}`;
  }

  private randomInt(min: number, max: number): number {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  private randomFloat(min: number, max: number, decimals: number = 1): number {
    return parseFloat((Math.random() * (max - min) + min).toFixed(decimals));
  }

  private randomDate(start: Date, end: Date): string {
    const date = new Date(start.getTime() + Math.random() * (end.getTime() - start.getTime()));
    return date.toISOString();
  }

  private randomElement<T>(arr: T[]): T {
    return arr[Math.floor(Math.random() * arr.length)]!;
  }

  private randomElements<T>(arr: T[], count: number): T[] {
    const shuffled = [...arr].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }

  private randomPhone(): string {
    return `07${this.randomInt(7000000000, 7999999999)}`;
  }

  generatePatients(count: number): any[] {
    const patients: any[] = [];
    for (let i = 0; i < count; i++) {
      const isArabic = Math.random() > 0.3;
      const firstName = isArabic
        ? this.randomElement(this.arabicFirstNames)
        : this.randomElement(this.englishFirstNames);
      const lastName = isArabic
        ? this.randomElement(this.arabicLastNames)
        : this.randomElement(this.englishLastNames);
      const gender = Math.random() > 0.5 ? 'male' : 'female';
      const birthDate = this.randomDate(new Date('1940-01-01'), new Date('2020-12-31'));
      const age = new Date().getFullYear() - new Date(birthDate).getFullYear();

      patients.push({
        id: this.nextId('PAT'),
        name: `${firstName} ${lastName}`,
        nameAr: isArabic ? `${firstName} ${lastName}` : undefined,
        firstName,
        lastName,
        gender,
        dateOfBirth: birthDate,
        age,
        phone: this.randomPhone(),
        email: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@example.com`,
        nationalId: `${this.randomInt(1000000000, 9999999999)}`,
        address: isArabic
          ? `شارع ${this.randomInt(1, 100)}، بغداد`
          : `${this.randomInt(1, 100)} Main Street, Baghdad`,
        bloodType: this.randomElement(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']),
        city: isArabic ? 'بغداد' : 'Baghdad',
        createdAt: this.randomDate(new Date('2023-01-01'), new Date()),
        updatedAt: this.randomDate(new Date('2023-01-01'), new Date()),
      });
    }
    return patients;
  }

  generateLabs(count: number): any[] {
    const labs: any[] = [];
    for (let i = 0; i < count; i++) {
      const template = this.randomElement(this.labNames);
      labs.push({
        id: this.nextId('LAB'),
        name: template.en,
        nameAr: template.ar,
        code: `LAB-${String(i + 1).padStart(3, '0')}`,
        phone: this.randomPhone(),
        email: `lab${i + 1}@example.com`,
        city: this.randomElement(['Baghdad', 'Basra', 'Mosul', 'Erbil', 'Najaf', 'Karbala']),
        cityAr: this.randomElement(['بغداد', 'البصرة', 'الموصل', 'أربيل', 'النجف', 'كربلاء']),
        address: `Street ${this.randomInt(1, 100)}, District ${this.randomInt(1, 20)}`,
        status: this.randomElement(['active', 'active', 'active', 'inactive']),
        capacity: this.randomInt(100, 1000),
        createdAt: this.randomDate(new Date('2022-01-01'), new Date()),
      });
    }
    return labs;
  }

  generateHospitals(count: number): any[] {
    const hospitals: any[] = [];
    for (let i = 0; i < count; i++) {
      const template = this.randomElement(this.hospitalNames);
      hospitals.push({
        id: this.nextId('HOS'),
        name: template.en,
        nameAr: template.ar,
        code: `HOS-${String(i + 1).padStart(3, '0')}`,
        phone: this.randomPhone(),
        city: this.randomElement(['Baghdad', 'Basra', 'Mosul']),
        beds: this.randomInt(50, 500),
        departments: this.randomElements(
          ['ER', 'ICU', 'Cardiology', 'Pediatrics', 'Orthopedics', 'Neurology', 'Oncology', 'Radiology'],
          this.randomInt(3, 6)
        ),
        status: 'active',
      });
    }
    return hospitals;
  }

  generateDoctors(count: number): any[] {
    const doctors: any[] = [];
    const specialties = [
      'Cardiology', 'Pediatrics', 'Internal Medicine', 'Orthopedics',
      'Neurology', 'Oncology', 'General Surgery', 'Family Medicine',
    ];
    for (let i = 0; i < count; i++) {
      doctors.push({
        id: this.nextId('DOC'),
        name: `${this.randomElement(this.englishFirstNames)} ${this.randomElement(this.englishLastNames)}`,
        nameAr: `${this.randomElement(this.arabicFirstNames)} ${this.randomElement(this.arabicLastNames)}`,
        specialty: this.randomElement(specialties),
        licenseNumber: `LIC-${this.randomInt(10000, 99999)}`,
        phone: this.randomPhone(),
        email: `doctor${i + 1}@example.com`,
        hospitalId: this.nextId('HOS'),
        status: this.randomElement(['active', 'active', 'active', 'inactive']),
      });
    }
    return doctors;
  }

  generateLabResults(count: number): any[] {
    const results: any[] = [];
    for (let i = 0; i < count; i++) {
      const test = this.randomElement(this.testTypes);
      const value = test.name === 'CBC'
        ? `${this.randomFloat(4.5, 11.0, 1)} K/uL`
        : `${this.randomFloat(parseFloat(test.refRange.split('-')[0] || '0'), parseFloat(test.refRange.split('-')[1] || '200'), 1)} ${test.unit}`;
      results.push({
        id: this.nextId('RES'),
        patientId: this.nextId('PAT'),
        labId: this.nextId('LAB'),
        orderId: this.nextId('ORD'),
        testName: test.name,
        testNameAr: test.arName,
        value,
        unit: test.unit,
        referenceRange: test.refRange,
        isAbnormal: Math.random() > 0.85,
        status: this.randomElement(['completed', 'completed', 'completed', 'pending', 'verified']),
        collectedAt: this.randomDate(new Date('2024-01-01'), new Date()),
        completedAt: this.randomDate(new Date('2024-01-01'), new Date()),
        verifiedBy: this.nextId('DOC'),
        createdAt: this.randomDate(new Date('2024-01-01'), new Date()),
      });
    }
    return results;
  }

  generateDocuments(count: number): any[] {
    const documents: any[] = [];
    const docTypes = ['lab_report', 'prescription', 'radiology', 'referral', 'medical_certificate', 'national_id'];
    for (let i = 0; i < count; i++) {
      documents.push({
        id: this.nextId('DOC'),
        patientId: this.nextId('PAT'),
        type: this.randomElement(docTypes),
        title: `Document ${i + 1}`,
        status: this.randomElement(['processed', 'pending', 'processing', 'failed']),
        category: this.randomElement(['laboratory', 'clinical', 'administrative', 'government']),
        pages: this.randomInt(1, 10),
        fileSize: this.randomInt(10000, 5000000),
        mimeType: 'application/pdf',
        ocrCompleted: Math.random() > 0.3,
        ocrConfidence: this.randomFloat(75, 99, 1),
        classification: this.randomElement(['laboratory_report', 'prescription', 'referral']),
        createdAt: this.randomDate(new Date('2024-01-01'), new Date()),
      });
    }
    return documents;
  }

  generateOrders(count: number): any[] {
    const orders: any[] = [];
    const statuses = ['pending', 'in_progress', 'completed', 'cancelled', 'verified'];
    for (let i = 0; i < count; i++) {
      const testCount = this.randomInt(1, 5);
      orders.push({
        id: this.nextId('ORD'),
        patientId: this.nextId('PAT'),
        labId: this.nextId('LAB'),
        doctorId: this.nextId('DOC'),
        tests: this.randomElements(this.testTypes, testCount).map(t => t.name),
        status: this.randomElement(statuses),
        priority: this.randomElement(['routine', 'routine', 'urgent', 'stat']),
        createdAt: this.randomDate(new Date('2024-01-01'), new Date()),
        updatedAt: this.randomDate(new Date('2024-01-01'), new Date()),
        notes: '',
      });
    }
    return orders;
  }

  generateSamples(count: number): any[] {
    const samples: any[] = [];
    const types = ['blood', 'urine', 'stool', 'sputum', 'csf', 'tissue'];
    const statuses = ['collected', 'in_transit', 'received', 'processing', 'completed', 'rejected'];
    for (let i = 0; i < count; i++) {
      samples.push({
        id: this.nextId('SMP'),
        orderId: this.nextId('ORD'),
        patientId: this.nextId('PAT'),
        type: this.randomElement(types),
        typeAr: this.randomElement(['دم', 'بول', 'براز', 'بلغم', 'سائل دماغي', 'نسيج']),
        barcode: `BC-${this.randomInt(100000, 999999)}`,
        status: this.randomElement(statuses),
        collectedAt: this.randomDate(new Date('2024-01-01'), new Date()),
        receivedAt: this.randomDate(new Date('2024-01-01'), new Date()),
        collectedBy: this.nextId('USR'),
        notes: Math.random() > 0.8 ? 'Sample hemolyzed' : '',
      });
    }
    return samples;
  }

  generateUsers(count: number): any[] {
    const users: any[] = [];
    const roles = ['admin', 'doctor', 'lab_technician', 'lab_manager', 'nurse', 'reception', 'auditor', 'citizen'];
    for (let i = 0; i < count; i++) {
      const role = roles[i % roles.length];
      users.push({
        id: this.nextId('USR'),
        email: `${role}${i + 1}@demo.gula-platform.org`,
        name: `${this.randomElement(this.englishFirstNames)} ${this.randomElement(this.englishLastNames)}`,
        nameAr: `${this.randomElement(this.arabicFirstNames)} ${this.randomElement(this.arabicLastNames)}`,
        role,
        labId: this.nextId('LAB'),
        hospitalId: this.nextId('HOS'),
        phone: this.randomPhone(),
        active: true,
        createdAt: this.randomDate(new Date('2023-01-01'), new Date()),
      });
    }
    return users;
  }

  generateAppointments(count: number): any[] {
    const appointments: any[] = [];
    const statuses = ['scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show'];
    for (let i = 0; i < count; i++) {
      appointments.push({
        id: this.nextId('APT'),
        patientId: this.nextId('PAT'),
        doctorId: this.nextId('DOC'),
        labId: this.nextId('LAB'),
        date: this.randomDate(new Date('2024-06-01'), new Date('2024-12-31')),
        type: this.randomElement(['checkup', 'followup', 'emergency', 'routine']),
        status: this.randomElement(statuses),
        notes: Math.random() > 0.7 ? 'Patient requested morning appointment' : '',
        createdAt: this.randomDate(new Date('2024-01-01'), new Date()),
      });
    }
    return appointments;
  }
}
