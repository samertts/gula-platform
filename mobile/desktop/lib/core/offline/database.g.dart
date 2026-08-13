// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $PatientsTable extends Patients with TableInfo<$PatientsTable, Patient> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PatientsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _labIdMeta = const VerificationMeta('labId');
  @override
  late final GeneratedColumn<String> labId = GeneratedColumn<String>(
    'lab_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _nationalIdMeta = const VerificationMeta(
    'nationalId',
  );
  @override
  late final GeneratedColumn<String> nationalId = GeneratedColumn<String>(
    'national_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _sndhsHealthIdMeta = const VerificationMeta(
    'sndhsHealthId',
  );
  @override
  late final GeneratedColumn<String> sndhsHealthId = GeneratedColumn<String>(
    'sndhs_health_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _firstNameMeta = const VerificationMeta(
    'firstName',
  );
  @override
  late final GeneratedColumn<String> firstName = GeneratedColumn<String>(
    'first_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fatherNameMeta = const VerificationMeta(
    'fatherName',
  );
  @override
  late final GeneratedColumn<String> fatherName = GeneratedColumn<String>(
    'father_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _grandFatherNameMeta = const VerificationMeta(
    'grandFatherName',
  );
  @override
  late final GeneratedColumn<String> grandFatherName = GeneratedColumn<String>(
    'grand_father_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _lastNameMeta = const VerificationMeta(
    'lastName',
  );
  @override
  late final GeneratedColumn<String> lastName = GeneratedColumn<String>(
    'last_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _fullNameMeta = const VerificationMeta(
    'fullName',
  );
  @override
  late final GeneratedColumn<String> fullName = GeneratedColumn<String>(
    'full_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _motherNameMeta = const VerificationMeta(
    'motherName',
  );
  @override
  late final GeneratedColumn<String> motherName = GeneratedColumn<String>(
    'mother_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _genderMeta = const VerificationMeta('gender');
  @override
  late final GeneratedColumn<String> gender = GeneratedColumn<String>(
    'gender',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _dateOfBirthMeta = const VerificationMeta(
    'dateOfBirth',
  );
  @override
  late final GeneratedColumn<String> dateOfBirth = GeneratedColumn<String>(
    'date_of_birth',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _phoneMeta = const VerificationMeta('phone');
  @override
  late final GeneratedColumn<String> phone = GeneratedColumn<String>(
    'phone',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _emailMeta = const VerificationMeta('email');
  @override
  late final GeneratedColumn<String> email = GeneratedColumn<String>(
    'email',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _addressMeta = const VerificationMeta(
    'address',
  );
  @override
  late final GeneratedColumn<String> address = GeneratedColumn<String>(
    'address',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _cityMeta = const VerificationMeta('city');
  @override
  late final GeneratedColumn<String> city = GeneratedColumn<String>(
    'city',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _bloodGroupMeta = const VerificationMeta(
    'bloodGroup',
  );
  @override
  late final GeneratedColumn<String> bloodGroup = GeneratedColumn<String>(
    'blood_group',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _maritalStatusMeta = const VerificationMeta(
    'maritalStatus',
  );
  @override
  late final GeneratedColumn<String> maritalStatus = GeneratedColumn<String>(
    'marital_status',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _occupationMeta = const VerificationMeta(
    'occupation',
  );
  @override
  late final GeneratedColumn<String> occupation = GeneratedColumn<String>(
    'occupation',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _photoUrlMeta = const VerificationMeta(
    'photoUrl',
  );
  @override
  late final GeneratedColumn<String> photoUrl = GeneratedColumn<String>(
    'photo_url',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _insuranceProviderMeta = const VerificationMeta(
    'insuranceProvider',
  );
  @override
  late final GeneratedColumn<String> insuranceProvider =
      GeneratedColumn<String>(
        'insurance_provider',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _insuranceNumberMeta = const VerificationMeta(
    'insuranceNumber',
  );
  @override
  late final GeneratedColumn<String> insuranceNumber = GeneratedColumn<String>(
    'insurance_number',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _notesMeta = const VerificationMeta('notes');
  @override
  late final GeneratedColumn<String> notes = GeneratedColumn<String>(
    'notes',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _tagsMeta = const VerificationMeta('tags');
  @override
  late final GeneratedColumn<String> tags = GeneratedColumn<String>(
    'tags',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _qrTokenMeta = const VerificationMeta(
    'qrToken',
  );
  @override
  late final GeneratedColumn<String> qrToken = GeneratedColumn<String>(
    'qr_token',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _deletedAtMeta = const VerificationMeta(
    'deletedAt',
  );
  @override
  late final GeneratedColumn<String> deletedAt = GeneratedColumn<String>(
    'deleted_at',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    labId,
    nationalId,
    sndhsHealthId,
    firstName,
    fatherName,
    grandFatherName,
    lastName,
    fullName,
    motherName,
    gender,
    dateOfBirth,
    phone,
    email,
    address,
    city,
    bloodGroup,
    maritalStatus,
    occupation,
    photoUrl,
    insuranceProvider,
    insuranceNumber,
    notes,
    tags,
    qrToken,
    createdAt,
    updatedAt,
    deletedAt,
    syncStatus,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'patients';
  @override
  VerificationContext validateIntegrity(
    Insertable<Patient> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('lab_id')) {
      context.handle(
        _labIdMeta,
        labId.isAcceptableOrUnknown(data['lab_id']!, _labIdMeta),
      );
    }
    if (data.containsKey('national_id')) {
      context.handle(
        _nationalIdMeta,
        nationalId.isAcceptableOrUnknown(data['national_id']!, _nationalIdMeta),
      );
    }
    if (data.containsKey('sndhs_health_id')) {
      context.handle(
        _sndhsHealthIdMeta,
        sndhsHealthId.isAcceptableOrUnknown(
          data['sndhs_health_id']!,
          _sndhsHealthIdMeta,
        ),
      );
    }
    if (data.containsKey('first_name')) {
      context.handle(
        _firstNameMeta,
        firstName.isAcceptableOrUnknown(data['first_name']!, _firstNameMeta),
      );
    } else if (isInserting) {
      context.missing(_firstNameMeta);
    }
    if (data.containsKey('father_name')) {
      context.handle(
        _fatherNameMeta,
        fatherName.isAcceptableOrUnknown(data['father_name']!, _fatherNameMeta),
      );
    }
    if (data.containsKey('grand_father_name')) {
      context.handle(
        _grandFatherNameMeta,
        grandFatherName.isAcceptableOrUnknown(
          data['grand_father_name']!,
          _grandFatherNameMeta,
        ),
      );
    }
    if (data.containsKey('last_name')) {
      context.handle(
        _lastNameMeta,
        lastName.isAcceptableOrUnknown(data['last_name']!, _lastNameMeta),
      );
    }
    if (data.containsKey('full_name')) {
      context.handle(
        _fullNameMeta,
        fullName.isAcceptableOrUnknown(data['full_name']!, _fullNameMeta),
      );
    } else if (isInserting) {
      context.missing(_fullNameMeta);
    }
    if (data.containsKey('mother_name')) {
      context.handle(
        _motherNameMeta,
        motherName.isAcceptableOrUnknown(data['mother_name']!, _motherNameMeta),
      );
    }
    if (data.containsKey('gender')) {
      context.handle(
        _genderMeta,
        gender.isAcceptableOrUnknown(data['gender']!, _genderMeta),
      );
    } else if (isInserting) {
      context.missing(_genderMeta);
    }
    if (data.containsKey('date_of_birth')) {
      context.handle(
        _dateOfBirthMeta,
        dateOfBirth.isAcceptableOrUnknown(
          data['date_of_birth']!,
          _dateOfBirthMeta,
        ),
      );
    }
    if (data.containsKey('phone')) {
      context.handle(
        _phoneMeta,
        phone.isAcceptableOrUnknown(data['phone']!, _phoneMeta),
      );
    }
    if (data.containsKey('email')) {
      context.handle(
        _emailMeta,
        email.isAcceptableOrUnknown(data['email']!, _emailMeta),
      );
    }
    if (data.containsKey('address')) {
      context.handle(
        _addressMeta,
        address.isAcceptableOrUnknown(data['address']!, _addressMeta),
      );
    }
    if (data.containsKey('city')) {
      context.handle(
        _cityMeta,
        city.isAcceptableOrUnknown(data['city']!, _cityMeta),
      );
    }
    if (data.containsKey('blood_group')) {
      context.handle(
        _bloodGroupMeta,
        bloodGroup.isAcceptableOrUnknown(data['blood_group']!, _bloodGroupMeta),
      );
    }
    if (data.containsKey('marital_status')) {
      context.handle(
        _maritalStatusMeta,
        maritalStatus.isAcceptableOrUnknown(
          data['marital_status']!,
          _maritalStatusMeta,
        ),
      );
    }
    if (data.containsKey('occupation')) {
      context.handle(
        _occupationMeta,
        occupation.isAcceptableOrUnknown(data['occupation']!, _occupationMeta),
      );
    }
    if (data.containsKey('photo_url')) {
      context.handle(
        _photoUrlMeta,
        photoUrl.isAcceptableOrUnknown(data['photo_url']!, _photoUrlMeta),
      );
    }
    if (data.containsKey('insurance_provider')) {
      context.handle(
        _insuranceProviderMeta,
        insuranceProvider.isAcceptableOrUnknown(
          data['insurance_provider']!,
          _insuranceProviderMeta,
        ),
      );
    }
    if (data.containsKey('insurance_number')) {
      context.handle(
        _insuranceNumberMeta,
        insuranceNumber.isAcceptableOrUnknown(
          data['insurance_number']!,
          _insuranceNumberMeta,
        ),
      );
    }
    if (data.containsKey('notes')) {
      context.handle(
        _notesMeta,
        notes.isAcceptableOrUnknown(data['notes']!, _notesMeta),
      );
    }
    if (data.containsKey('tags')) {
      context.handle(
        _tagsMeta,
        tags.isAcceptableOrUnknown(data['tags']!, _tagsMeta),
      );
    }
    if (data.containsKey('qr_token')) {
      context.handle(
        _qrTokenMeta,
        qrToken.isAcceptableOrUnknown(data['qr_token']!, _qrTokenMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('deleted_at')) {
      context.handle(
        _deletedAtMeta,
        deletedAt.isAcceptableOrUnknown(data['deleted_at']!, _deletedAtMeta),
      );
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    } else if (isInserting) {
      context.missing(_syncStatusMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Patient map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Patient(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      labId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}lab_id'],
      ),
      nationalId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}national_id'],
      ),
      sndhsHealthId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sndhs_health_id'],
      ),
      firstName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}first_name'],
      )!,
      fatherName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}father_name'],
      ),
      grandFatherName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}grand_father_name'],
      ),
      lastName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_name'],
      ),
      fullName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}full_name'],
      )!,
      motherName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mother_name'],
      ),
      gender: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}gender'],
      )!,
      dateOfBirth: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}date_of_birth'],
      ),
      phone: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}phone'],
      ),
      email: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}email'],
      ),
      address: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}address'],
      ),
      city: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}city'],
      ),
      bloodGroup: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}blood_group'],
      ),
      maritalStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}marital_status'],
      ),
      occupation: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}occupation'],
      ),
      photoUrl: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}photo_url'],
      ),
      insuranceProvider: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}insurance_provider'],
      ),
      insuranceNumber: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}insurance_number'],
      ),
      notes: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}notes'],
      ),
      tags: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}tags'],
      ),
      qrToken: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}qr_token'],
      ),
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
      deletedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}deleted_at'],
      ),
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
    );
  }

  @override
  $PatientsTable createAlias(String alias) {
    return $PatientsTable(attachedDatabase, alias);
  }
}

class Patient extends DataClass implements Insertable<Patient> {
  final String id;
  final String? labId;
  final String? nationalId;
  final String? sndhsHealthId;
  final String firstName;
  final String? fatherName;
  final String? grandFatherName;
  final String? lastName;
  final String fullName;
  final String? motherName;
  final String gender;
  final String? dateOfBirth;
  final String? phone;
  final String? email;
  final String? address;
  final String? city;
  final String? bloodGroup;
  final String? maritalStatus;
  final String? occupation;
  final String? photoUrl;
  final String? insuranceProvider;
  final String? insuranceNumber;
  final String? notes;
  final String? tags;
  final String? qrToken;
  final String createdAt;
  final String updatedAt;
  final String? deletedAt;
  final String syncStatus;
  const Patient({
    required this.id,
    this.labId,
    this.nationalId,
    this.sndhsHealthId,
    required this.firstName,
    this.fatherName,
    this.grandFatherName,
    this.lastName,
    required this.fullName,
    this.motherName,
    required this.gender,
    this.dateOfBirth,
    this.phone,
    this.email,
    this.address,
    this.city,
    this.bloodGroup,
    this.maritalStatus,
    this.occupation,
    this.photoUrl,
    this.insuranceProvider,
    this.insuranceNumber,
    this.notes,
    this.tags,
    this.qrToken,
    required this.createdAt,
    required this.updatedAt,
    this.deletedAt,
    required this.syncStatus,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    if (!nullToAbsent || labId != null) {
      map['lab_id'] = Variable<String>(labId);
    }
    if (!nullToAbsent || nationalId != null) {
      map['national_id'] = Variable<String>(nationalId);
    }
    if (!nullToAbsent || sndhsHealthId != null) {
      map['sndhs_health_id'] = Variable<String>(sndhsHealthId);
    }
    map['first_name'] = Variable<String>(firstName);
    if (!nullToAbsent || fatherName != null) {
      map['father_name'] = Variable<String>(fatherName);
    }
    if (!nullToAbsent || grandFatherName != null) {
      map['grand_father_name'] = Variable<String>(grandFatherName);
    }
    if (!nullToAbsent || lastName != null) {
      map['last_name'] = Variable<String>(lastName);
    }
    map['full_name'] = Variable<String>(fullName);
    if (!nullToAbsent || motherName != null) {
      map['mother_name'] = Variable<String>(motherName);
    }
    map['gender'] = Variable<String>(gender);
    if (!nullToAbsent || dateOfBirth != null) {
      map['date_of_birth'] = Variable<String>(dateOfBirth);
    }
    if (!nullToAbsent || phone != null) {
      map['phone'] = Variable<String>(phone);
    }
    if (!nullToAbsent || email != null) {
      map['email'] = Variable<String>(email);
    }
    if (!nullToAbsent || address != null) {
      map['address'] = Variable<String>(address);
    }
    if (!nullToAbsent || city != null) {
      map['city'] = Variable<String>(city);
    }
    if (!nullToAbsent || bloodGroup != null) {
      map['blood_group'] = Variable<String>(bloodGroup);
    }
    if (!nullToAbsent || maritalStatus != null) {
      map['marital_status'] = Variable<String>(maritalStatus);
    }
    if (!nullToAbsent || occupation != null) {
      map['occupation'] = Variable<String>(occupation);
    }
    if (!nullToAbsent || photoUrl != null) {
      map['photo_url'] = Variable<String>(photoUrl);
    }
    if (!nullToAbsent || insuranceProvider != null) {
      map['insurance_provider'] = Variable<String>(insuranceProvider);
    }
    if (!nullToAbsent || insuranceNumber != null) {
      map['insurance_number'] = Variable<String>(insuranceNumber);
    }
    if (!nullToAbsent || notes != null) {
      map['notes'] = Variable<String>(notes);
    }
    if (!nullToAbsent || tags != null) {
      map['tags'] = Variable<String>(tags);
    }
    if (!nullToAbsent || qrToken != null) {
      map['qr_token'] = Variable<String>(qrToken);
    }
    map['created_at'] = Variable<String>(createdAt);
    map['updated_at'] = Variable<String>(updatedAt);
    if (!nullToAbsent || deletedAt != null) {
      map['deleted_at'] = Variable<String>(deletedAt);
    }
    map['sync_status'] = Variable<String>(syncStatus);
    return map;
  }

  PatientsCompanion toCompanion(bool nullToAbsent) {
    return PatientsCompanion(
      id: Value(id),
      labId: labId == null && nullToAbsent
          ? const Value.absent()
          : Value(labId),
      nationalId: nationalId == null && nullToAbsent
          ? const Value.absent()
          : Value(nationalId),
      sndhsHealthId: sndhsHealthId == null && nullToAbsent
          ? const Value.absent()
          : Value(sndhsHealthId),
      firstName: Value(firstName),
      fatherName: fatherName == null && nullToAbsent
          ? const Value.absent()
          : Value(fatherName),
      grandFatherName: grandFatherName == null && nullToAbsent
          ? const Value.absent()
          : Value(grandFatherName),
      lastName: lastName == null && nullToAbsent
          ? const Value.absent()
          : Value(lastName),
      fullName: Value(fullName),
      motherName: motherName == null && nullToAbsent
          ? const Value.absent()
          : Value(motherName),
      gender: Value(gender),
      dateOfBirth: dateOfBirth == null && nullToAbsent
          ? const Value.absent()
          : Value(dateOfBirth),
      phone: phone == null && nullToAbsent
          ? const Value.absent()
          : Value(phone),
      email: email == null && nullToAbsent
          ? const Value.absent()
          : Value(email),
      address: address == null && nullToAbsent
          ? const Value.absent()
          : Value(address),
      city: city == null && nullToAbsent ? const Value.absent() : Value(city),
      bloodGroup: bloodGroup == null && nullToAbsent
          ? const Value.absent()
          : Value(bloodGroup),
      maritalStatus: maritalStatus == null && nullToAbsent
          ? const Value.absent()
          : Value(maritalStatus),
      occupation: occupation == null && nullToAbsent
          ? const Value.absent()
          : Value(occupation),
      photoUrl: photoUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(photoUrl),
      insuranceProvider: insuranceProvider == null && nullToAbsent
          ? const Value.absent()
          : Value(insuranceProvider),
      insuranceNumber: insuranceNumber == null && nullToAbsent
          ? const Value.absent()
          : Value(insuranceNumber),
      notes: notes == null && nullToAbsent
          ? const Value.absent()
          : Value(notes),
      tags: tags == null && nullToAbsent ? const Value.absent() : Value(tags),
      qrToken: qrToken == null && nullToAbsent
          ? const Value.absent()
          : Value(qrToken),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
      deletedAt: deletedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(deletedAt),
      syncStatus: Value(syncStatus),
    );
  }

  factory Patient.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Patient(
      id: serializer.fromJson<String>(json['id']),
      labId: serializer.fromJson<String?>(json['labId']),
      nationalId: serializer.fromJson<String?>(json['nationalId']),
      sndhsHealthId: serializer.fromJson<String?>(json['sndhsHealthId']),
      firstName: serializer.fromJson<String>(json['firstName']),
      fatherName: serializer.fromJson<String?>(json['fatherName']),
      grandFatherName: serializer.fromJson<String?>(json['grandFatherName']),
      lastName: serializer.fromJson<String?>(json['lastName']),
      fullName: serializer.fromJson<String>(json['fullName']),
      motherName: serializer.fromJson<String?>(json['motherName']),
      gender: serializer.fromJson<String>(json['gender']),
      dateOfBirth: serializer.fromJson<String?>(json['dateOfBirth']),
      phone: serializer.fromJson<String?>(json['phone']),
      email: serializer.fromJson<String?>(json['email']),
      address: serializer.fromJson<String?>(json['address']),
      city: serializer.fromJson<String?>(json['city']),
      bloodGroup: serializer.fromJson<String?>(json['bloodGroup']),
      maritalStatus: serializer.fromJson<String?>(json['maritalStatus']),
      occupation: serializer.fromJson<String?>(json['occupation']),
      photoUrl: serializer.fromJson<String?>(json['photoUrl']),
      insuranceProvider: serializer.fromJson<String?>(
        json['insuranceProvider'],
      ),
      insuranceNumber: serializer.fromJson<String?>(json['insuranceNumber']),
      notes: serializer.fromJson<String?>(json['notes']),
      tags: serializer.fromJson<String?>(json['tags']),
      qrToken: serializer.fromJson<String?>(json['qrToken']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
      deletedAt: serializer.fromJson<String?>(json['deletedAt']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'labId': serializer.toJson<String?>(labId),
      'nationalId': serializer.toJson<String?>(nationalId),
      'sndhsHealthId': serializer.toJson<String?>(sndhsHealthId),
      'firstName': serializer.toJson<String>(firstName),
      'fatherName': serializer.toJson<String?>(fatherName),
      'grandFatherName': serializer.toJson<String?>(grandFatherName),
      'lastName': serializer.toJson<String?>(lastName),
      'fullName': serializer.toJson<String>(fullName),
      'motherName': serializer.toJson<String?>(motherName),
      'gender': serializer.toJson<String>(gender),
      'dateOfBirth': serializer.toJson<String?>(dateOfBirth),
      'phone': serializer.toJson<String?>(phone),
      'email': serializer.toJson<String?>(email),
      'address': serializer.toJson<String?>(address),
      'city': serializer.toJson<String?>(city),
      'bloodGroup': serializer.toJson<String?>(bloodGroup),
      'maritalStatus': serializer.toJson<String?>(maritalStatus),
      'occupation': serializer.toJson<String?>(occupation),
      'photoUrl': serializer.toJson<String?>(photoUrl),
      'insuranceProvider': serializer.toJson<String?>(insuranceProvider),
      'insuranceNumber': serializer.toJson<String?>(insuranceNumber),
      'notes': serializer.toJson<String?>(notes),
      'tags': serializer.toJson<String?>(tags),
      'qrToken': serializer.toJson<String?>(qrToken),
      'createdAt': serializer.toJson<String>(createdAt),
      'updatedAt': serializer.toJson<String>(updatedAt),
      'deletedAt': serializer.toJson<String?>(deletedAt),
      'syncStatus': serializer.toJson<String>(syncStatus),
    };
  }

  Patient copyWith({
    String? id,
    Value<String?> labId = const Value.absent(),
    Value<String?> nationalId = const Value.absent(),
    Value<String?> sndhsHealthId = const Value.absent(),
    String? firstName,
    Value<String?> fatherName = const Value.absent(),
    Value<String?> grandFatherName = const Value.absent(),
    Value<String?> lastName = const Value.absent(),
    String? fullName,
    Value<String?> motherName = const Value.absent(),
    String? gender,
    Value<String?> dateOfBirth = const Value.absent(),
    Value<String?> phone = const Value.absent(),
    Value<String?> email = const Value.absent(),
    Value<String?> address = const Value.absent(),
    Value<String?> city = const Value.absent(),
    Value<String?> bloodGroup = const Value.absent(),
    Value<String?> maritalStatus = const Value.absent(),
    Value<String?> occupation = const Value.absent(),
    Value<String?> photoUrl = const Value.absent(),
    Value<String?> insuranceProvider = const Value.absent(),
    Value<String?> insuranceNumber = const Value.absent(),
    Value<String?> notes = const Value.absent(),
    Value<String?> tags = const Value.absent(),
    Value<String?> qrToken = const Value.absent(),
    String? createdAt,
    String? updatedAt,
    Value<String?> deletedAt = const Value.absent(),
    String? syncStatus,
  }) => Patient(
    id: id ?? this.id,
    labId: labId.present ? labId.value : this.labId,
    nationalId: nationalId.present ? nationalId.value : this.nationalId,
    sndhsHealthId: sndhsHealthId.present
        ? sndhsHealthId.value
        : this.sndhsHealthId,
    firstName: firstName ?? this.firstName,
    fatherName: fatherName.present ? fatherName.value : this.fatherName,
    grandFatherName: grandFatherName.present
        ? grandFatherName.value
        : this.grandFatherName,
    lastName: lastName.present ? lastName.value : this.lastName,
    fullName: fullName ?? this.fullName,
    motherName: motherName.present ? motherName.value : this.motherName,
    gender: gender ?? this.gender,
    dateOfBirth: dateOfBirth.present ? dateOfBirth.value : this.dateOfBirth,
    phone: phone.present ? phone.value : this.phone,
    email: email.present ? email.value : this.email,
    address: address.present ? address.value : this.address,
    city: city.present ? city.value : this.city,
    bloodGroup: bloodGroup.present ? bloodGroup.value : this.bloodGroup,
    maritalStatus: maritalStatus.present
        ? maritalStatus.value
        : this.maritalStatus,
    occupation: occupation.present ? occupation.value : this.occupation,
    photoUrl: photoUrl.present ? photoUrl.value : this.photoUrl,
    insuranceProvider: insuranceProvider.present
        ? insuranceProvider.value
        : this.insuranceProvider,
    insuranceNumber: insuranceNumber.present
        ? insuranceNumber.value
        : this.insuranceNumber,
    notes: notes.present ? notes.value : this.notes,
    tags: tags.present ? tags.value : this.tags,
    qrToken: qrToken.present ? qrToken.value : this.qrToken,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
    deletedAt: deletedAt.present ? deletedAt.value : this.deletedAt,
    syncStatus: syncStatus ?? this.syncStatus,
  );
  Patient copyWithCompanion(PatientsCompanion data) {
    return Patient(
      id: data.id.present ? data.id.value : this.id,
      labId: data.labId.present ? data.labId.value : this.labId,
      nationalId: data.nationalId.present
          ? data.nationalId.value
          : this.nationalId,
      sndhsHealthId: data.sndhsHealthId.present
          ? data.sndhsHealthId.value
          : this.sndhsHealthId,
      firstName: data.firstName.present ? data.firstName.value : this.firstName,
      fatherName: data.fatherName.present
          ? data.fatherName.value
          : this.fatherName,
      grandFatherName: data.grandFatherName.present
          ? data.grandFatherName.value
          : this.grandFatherName,
      lastName: data.lastName.present ? data.lastName.value : this.lastName,
      fullName: data.fullName.present ? data.fullName.value : this.fullName,
      motherName: data.motherName.present
          ? data.motherName.value
          : this.motherName,
      gender: data.gender.present ? data.gender.value : this.gender,
      dateOfBirth: data.dateOfBirth.present
          ? data.dateOfBirth.value
          : this.dateOfBirth,
      phone: data.phone.present ? data.phone.value : this.phone,
      email: data.email.present ? data.email.value : this.email,
      address: data.address.present ? data.address.value : this.address,
      city: data.city.present ? data.city.value : this.city,
      bloodGroup: data.bloodGroup.present
          ? data.bloodGroup.value
          : this.bloodGroup,
      maritalStatus: data.maritalStatus.present
          ? data.maritalStatus.value
          : this.maritalStatus,
      occupation: data.occupation.present
          ? data.occupation.value
          : this.occupation,
      photoUrl: data.photoUrl.present ? data.photoUrl.value : this.photoUrl,
      insuranceProvider: data.insuranceProvider.present
          ? data.insuranceProvider.value
          : this.insuranceProvider,
      insuranceNumber: data.insuranceNumber.present
          ? data.insuranceNumber.value
          : this.insuranceNumber,
      notes: data.notes.present ? data.notes.value : this.notes,
      tags: data.tags.present ? data.tags.value : this.tags,
      qrToken: data.qrToken.present ? data.qrToken.value : this.qrToken,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      deletedAt: data.deletedAt.present ? data.deletedAt.value : this.deletedAt,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Patient(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('nationalId: $nationalId, ')
          ..write('sndhsHealthId: $sndhsHealthId, ')
          ..write('firstName: $firstName, ')
          ..write('fatherName: $fatherName, ')
          ..write('grandFatherName: $grandFatherName, ')
          ..write('lastName: $lastName, ')
          ..write('fullName: $fullName, ')
          ..write('motherName: $motherName, ')
          ..write('gender: $gender, ')
          ..write('dateOfBirth: $dateOfBirth, ')
          ..write('phone: $phone, ')
          ..write('email: $email, ')
          ..write('address: $address, ')
          ..write('city: $city, ')
          ..write('bloodGroup: $bloodGroup, ')
          ..write('maritalStatus: $maritalStatus, ')
          ..write('occupation: $occupation, ')
          ..write('photoUrl: $photoUrl, ')
          ..write('insuranceProvider: $insuranceProvider, ')
          ..write('insuranceNumber: $insuranceNumber, ')
          ..write('notes: $notes, ')
          ..write('tags: $tags, ')
          ..write('qrToken: $qrToken, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('deletedAt: $deletedAt, ')
          ..write('syncStatus: $syncStatus')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
    id,
    labId,
    nationalId,
    sndhsHealthId,
    firstName,
    fatherName,
    grandFatherName,
    lastName,
    fullName,
    motherName,
    gender,
    dateOfBirth,
    phone,
    email,
    address,
    city,
    bloodGroup,
    maritalStatus,
    occupation,
    photoUrl,
    insuranceProvider,
    insuranceNumber,
    notes,
    tags,
    qrToken,
    createdAt,
    updatedAt,
    deletedAt,
    syncStatus,
  ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Patient &&
          other.id == this.id &&
          other.labId == this.labId &&
          other.nationalId == this.nationalId &&
          other.sndhsHealthId == this.sndhsHealthId &&
          other.firstName == this.firstName &&
          other.fatherName == this.fatherName &&
          other.grandFatherName == this.grandFatherName &&
          other.lastName == this.lastName &&
          other.fullName == this.fullName &&
          other.motherName == this.motherName &&
          other.gender == this.gender &&
          other.dateOfBirth == this.dateOfBirth &&
          other.phone == this.phone &&
          other.email == this.email &&
          other.address == this.address &&
          other.city == this.city &&
          other.bloodGroup == this.bloodGroup &&
          other.maritalStatus == this.maritalStatus &&
          other.occupation == this.occupation &&
          other.photoUrl == this.photoUrl &&
          other.insuranceProvider == this.insuranceProvider &&
          other.insuranceNumber == this.insuranceNumber &&
          other.notes == this.notes &&
          other.tags == this.tags &&
          other.qrToken == this.qrToken &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt &&
          other.deletedAt == this.deletedAt &&
          other.syncStatus == this.syncStatus);
}

class PatientsCompanion extends UpdateCompanion<Patient> {
  final Value<String> id;
  final Value<String?> labId;
  final Value<String?> nationalId;
  final Value<String?> sndhsHealthId;
  final Value<String> firstName;
  final Value<String?> fatherName;
  final Value<String?> grandFatherName;
  final Value<String?> lastName;
  final Value<String> fullName;
  final Value<String?> motherName;
  final Value<String> gender;
  final Value<String?> dateOfBirth;
  final Value<String?> phone;
  final Value<String?> email;
  final Value<String?> address;
  final Value<String?> city;
  final Value<String?> bloodGroup;
  final Value<String?> maritalStatus;
  final Value<String?> occupation;
  final Value<String?> photoUrl;
  final Value<String?> insuranceProvider;
  final Value<String?> insuranceNumber;
  final Value<String?> notes;
  final Value<String?> tags;
  final Value<String?> qrToken;
  final Value<String> createdAt;
  final Value<String> updatedAt;
  final Value<String?> deletedAt;
  final Value<String> syncStatus;
  final Value<int> rowid;
  const PatientsCompanion({
    this.id = const Value.absent(),
    this.labId = const Value.absent(),
    this.nationalId = const Value.absent(),
    this.sndhsHealthId = const Value.absent(),
    this.firstName = const Value.absent(),
    this.fatherName = const Value.absent(),
    this.grandFatherName = const Value.absent(),
    this.lastName = const Value.absent(),
    this.fullName = const Value.absent(),
    this.motherName = const Value.absent(),
    this.gender = const Value.absent(),
    this.dateOfBirth = const Value.absent(),
    this.phone = const Value.absent(),
    this.email = const Value.absent(),
    this.address = const Value.absent(),
    this.city = const Value.absent(),
    this.bloodGroup = const Value.absent(),
    this.maritalStatus = const Value.absent(),
    this.occupation = const Value.absent(),
    this.photoUrl = const Value.absent(),
    this.insuranceProvider = const Value.absent(),
    this.insuranceNumber = const Value.absent(),
    this.notes = const Value.absent(),
    this.tags = const Value.absent(),
    this.qrToken = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.deletedAt = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  PatientsCompanion.insert({
    required String id,
    this.labId = const Value.absent(),
    this.nationalId = const Value.absent(),
    this.sndhsHealthId = const Value.absent(),
    required String firstName,
    this.fatherName = const Value.absent(),
    this.grandFatherName = const Value.absent(),
    this.lastName = const Value.absent(),
    required String fullName,
    this.motherName = const Value.absent(),
    required String gender,
    this.dateOfBirth = const Value.absent(),
    this.phone = const Value.absent(),
    this.email = const Value.absent(),
    this.address = const Value.absent(),
    this.city = const Value.absent(),
    this.bloodGroup = const Value.absent(),
    this.maritalStatus = const Value.absent(),
    this.occupation = const Value.absent(),
    this.photoUrl = const Value.absent(),
    this.insuranceProvider = const Value.absent(),
    this.insuranceNumber = const Value.absent(),
    this.notes = const Value.absent(),
    this.tags = const Value.absent(),
    this.qrToken = const Value.absent(),
    required String createdAt,
    required String updatedAt,
    this.deletedAt = const Value.absent(),
    required String syncStatus,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       firstName = Value(firstName),
       fullName = Value(fullName),
       gender = Value(gender),
       createdAt = Value(createdAt),
       updatedAt = Value(updatedAt),
       syncStatus = Value(syncStatus);
  static Insertable<Patient> custom({
    Expression<String>? id,
    Expression<String>? labId,
    Expression<String>? nationalId,
    Expression<String>? sndhsHealthId,
    Expression<String>? firstName,
    Expression<String>? fatherName,
    Expression<String>? grandFatherName,
    Expression<String>? lastName,
    Expression<String>? fullName,
    Expression<String>? motherName,
    Expression<String>? gender,
    Expression<String>? dateOfBirth,
    Expression<String>? phone,
    Expression<String>? email,
    Expression<String>? address,
    Expression<String>? city,
    Expression<String>? bloodGroup,
    Expression<String>? maritalStatus,
    Expression<String>? occupation,
    Expression<String>? photoUrl,
    Expression<String>? insuranceProvider,
    Expression<String>? insuranceNumber,
    Expression<String>? notes,
    Expression<String>? tags,
    Expression<String>? qrToken,
    Expression<String>? createdAt,
    Expression<String>? updatedAt,
    Expression<String>? deletedAt,
    Expression<String>? syncStatus,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (labId != null) 'lab_id': labId,
      if (nationalId != null) 'national_id': nationalId,
      if (sndhsHealthId != null) 'sndhs_health_id': sndhsHealthId,
      if (firstName != null) 'first_name': firstName,
      if (fatherName != null) 'father_name': fatherName,
      if (grandFatherName != null) 'grand_father_name': grandFatherName,
      if (lastName != null) 'last_name': lastName,
      if (fullName != null) 'full_name': fullName,
      if (motherName != null) 'mother_name': motherName,
      if (gender != null) 'gender': gender,
      if (dateOfBirth != null) 'date_of_birth': dateOfBirth,
      if (phone != null) 'phone': phone,
      if (email != null) 'email': email,
      if (address != null) 'address': address,
      if (city != null) 'city': city,
      if (bloodGroup != null) 'blood_group': bloodGroup,
      if (maritalStatus != null) 'marital_status': maritalStatus,
      if (occupation != null) 'occupation': occupation,
      if (photoUrl != null) 'photo_url': photoUrl,
      if (insuranceProvider != null) 'insurance_provider': insuranceProvider,
      if (insuranceNumber != null) 'insurance_number': insuranceNumber,
      if (notes != null) 'notes': notes,
      if (tags != null) 'tags': tags,
      if (qrToken != null) 'qr_token': qrToken,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (deletedAt != null) 'deleted_at': deletedAt,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (rowid != null) 'rowid': rowid,
    });
  }

  PatientsCompanion copyWith({
    Value<String>? id,
    Value<String?>? labId,
    Value<String?>? nationalId,
    Value<String?>? sndhsHealthId,
    Value<String>? firstName,
    Value<String?>? fatherName,
    Value<String?>? grandFatherName,
    Value<String?>? lastName,
    Value<String>? fullName,
    Value<String?>? motherName,
    Value<String>? gender,
    Value<String?>? dateOfBirth,
    Value<String?>? phone,
    Value<String?>? email,
    Value<String?>? address,
    Value<String?>? city,
    Value<String?>? bloodGroup,
    Value<String?>? maritalStatus,
    Value<String?>? occupation,
    Value<String?>? photoUrl,
    Value<String?>? insuranceProvider,
    Value<String?>? insuranceNumber,
    Value<String?>? notes,
    Value<String?>? tags,
    Value<String?>? qrToken,
    Value<String>? createdAt,
    Value<String>? updatedAt,
    Value<String?>? deletedAt,
    Value<String>? syncStatus,
    Value<int>? rowid,
  }) {
    return PatientsCompanion(
      id: id ?? this.id,
      labId: labId ?? this.labId,
      nationalId: nationalId ?? this.nationalId,
      sndhsHealthId: sndhsHealthId ?? this.sndhsHealthId,
      firstName: firstName ?? this.firstName,
      fatherName: fatherName ?? this.fatherName,
      grandFatherName: grandFatherName ?? this.grandFatherName,
      lastName: lastName ?? this.lastName,
      fullName: fullName ?? this.fullName,
      motherName: motherName ?? this.motherName,
      gender: gender ?? this.gender,
      dateOfBirth: dateOfBirth ?? this.dateOfBirth,
      phone: phone ?? this.phone,
      email: email ?? this.email,
      address: address ?? this.address,
      city: city ?? this.city,
      bloodGroup: bloodGroup ?? this.bloodGroup,
      maritalStatus: maritalStatus ?? this.maritalStatus,
      occupation: occupation ?? this.occupation,
      photoUrl: photoUrl ?? this.photoUrl,
      insuranceProvider: insuranceProvider ?? this.insuranceProvider,
      insuranceNumber: insuranceNumber ?? this.insuranceNumber,
      notes: notes ?? this.notes,
      tags: tags ?? this.tags,
      qrToken: qrToken ?? this.qrToken,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      deletedAt: deletedAt ?? this.deletedAt,
      syncStatus: syncStatus ?? this.syncStatus,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (labId.present) {
      map['lab_id'] = Variable<String>(labId.value);
    }
    if (nationalId.present) {
      map['national_id'] = Variable<String>(nationalId.value);
    }
    if (sndhsHealthId.present) {
      map['sndhs_health_id'] = Variable<String>(sndhsHealthId.value);
    }
    if (firstName.present) {
      map['first_name'] = Variable<String>(firstName.value);
    }
    if (fatherName.present) {
      map['father_name'] = Variable<String>(fatherName.value);
    }
    if (grandFatherName.present) {
      map['grand_father_name'] = Variable<String>(grandFatherName.value);
    }
    if (lastName.present) {
      map['last_name'] = Variable<String>(lastName.value);
    }
    if (fullName.present) {
      map['full_name'] = Variable<String>(fullName.value);
    }
    if (motherName.present) {
      map['mother_name'] = Variable<String>(motherName.value);
    }
    if (gender.present) {
      map['gender'] = Variable<String>(gender.value);
    }
    if (dateOfBirth.present) {
      map['date_of_birth'] = Variable<String>(dateOfBirth.value);
    }
    if (phone.present) {
      map['phone'] = Variable<String>(phone.value);
    }
    if (email.present) {
      map['email'] = Variable<String>(email.value);
    }
    if (address.present) {
      map['address'] = Variable<String>(address.value);
    }
    if (city.present) {
      map['city'] = Variable<String>(city.value);
    }
    if (bloodGroup.present) {
      map['blood_group'] = Variable<String>(bloodGroup.value);
    }
    if (maritalStatus.present) {
      map['marital_status'] = Variable<String>(maritalStatus.value);
    }
    if (occupation.present) {
      map['occupation'] = Variable<String>(occupation.value);
    }
    if (photoUrl.present) {
      map['photo_url'] = Variable<String>(photoUrl.value);
    }
    if (insuranceProvider.present) {
      map['insurance_provider'] = Variable<String>(insuranceProvider.value);
    }
    if (insuranceNumber.present) {
      map['insurance_number'] = Variable<String>(insuranceNumber.value);
    }
    if (notes.present) {
      map['notes'] = Variable<String>(notes.value);
    }
    if (tags.present) {
      map['tags'] = Variable<String>(tags.value);
    }
    if (qrToken.present) {
      map['qr_token'] = Variable<String>(qrToken.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    if (deletedAt.present) {
      map['deleted_at'] = Variable<String>(deletedAt.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PatientsCompanion(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('nationalId: $nationalId, ')
          ..write('sndhsHealthId: $sndhsHealthId, ')
          ..write('firstName: $firstName, ')
          ..write('fatherName: $fatherName, ')
          ..write('grandFatherName: $grandFatherName, ')
          ..write('lastName: $lastName, ')
          ..write('fullName: $fullName, ')
          ..write('motherName: $motherName, ')
          ..write('gender: $gender, ')
          ..write('dateOfBirth: $dateOfBirth, ')
          ..write('phone: $phone, ')
          ..write('email: $email, ')
          ..write('address: $address, ')
          ..write('city: $city, ')
          ..write('bloodGroup: $bloodGroup, ')
          ..write('maritalStatus: $maritalStatus, ')
          ..write('occupation: $occupation, ')
          ..write('photoUrl: $photoUrl, ')
          ..write('insuranceProvider: $insuranceProvider, ')
          ..write('insuranceNumber: $insuranceNumber, ')
          ..write('notes: $notes, ')
          ..write('tags: $tags, ')
          ..write('qrToken: $qrToken, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('deletedAt: $deletedAt, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $OrdersTable extends Orders with TableInfo<$OrdersTable, Order> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $OrdersTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _labIdMeta = const VerificationMeta('labId');
  @override
  late final GeneratedColumn<String> labId = GeneratedColumn<String>(
    'lab_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _patientIdMeta = const VerificationMeta(
    'patientId',
  );
  @override
  late final GeneratedColumn<String> patientId = GeneratedColumn<String>(
    'patient_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _patientNameMeta = const VerificationMeta(
    'patientName',
  );
  @override
  late final GeneratedColumn<String> patientName = GeneratedColumn<String>(
    'patient_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _orderNumberMeta = const VerificationMeta(
    'orderNumber',
  );
  @override
  late final GeneratedColumn<String> orderNumber = GeneratedColumn<String>(
    'order_number',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _priorityMeta = const VerificationMeta(
    'priority',
  );
  @override
  late final GeneratedColumn<String> priority = GeneratedColumn<String>(
    'priority',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _testTypesMeta = const VerificationMeta(
    'testTypes',
  );
  @override
  late final GeneratedColumn<String> testTypes = GeneratedColumn<String>(
    'test_types',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _doctorNameMeta = const VerificationMeta(
    'doctorName',
  );
  @override
  late final GeneratedColumn<String> doctorName = GeneratedColumn<String>(
    'doctor_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _doctorIdMeta = const VerificationMeta(
    'doctorId',
  );
  @override
  late final GeneratedColumn<String> doctorId = GeneratedColumn<String>(
    'doctor_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _diagnosisMeta = const VerificationMeta(
    'diagnosis',
  );
  @override
  late final GeneratedColumn<String> diagnosis = GeneratedColumn<String>(
    'diagnosis',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _notesMeta = const VerificationMeta('notes');
  @override
  late final GeneratedColumn<String> notes = GeneratedColumn<String>(
    'notes',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _requestedByMeta = const VerificationMeta(
    'requestedBy',
  );
  @override
  late final GeneratedColumn<String> requestedBy = GeneratedColumn<String>(
    'requested_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _collectedByMeta = const VerificationMeta(
    'collectedBy',
  );
  @override
  late final GeneratedColumn<String> collectedBy = GeneratedColumn<String>(
    'collected_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _collectionDateMeta = const VerificationMeta(
    'collectionDate',
  );
  @override
  late final GeneratedColumn<String> collectionDate = GeneratedColumn<String>(
    'collection_date',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _receivedDateMeta = const VerificationMeta(
    'receivedDate',
  );
  @override
  late final GeneratedColumn<String> receivedDate = GeneratedColumn<String>(
    'received_date',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _completedDateMeta = const VerificationMeta(
    'completedDate',
  );
  @override
  late final GeneratedColumn<String> completedDate = GeneratedColumn<String>(
    'completed_date',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    labId,
    patientId,
    patientName,
    orderNumber,
    status,
    priority,
    testTypes,
    doctorName,
    doctorId,
    diagnosis,
    notes,
    requestedBy,
    collectedBy,
    collectionDate,
    receivedDate,
    completedDate,
    createdAt,
    updatedAt,
    syncStatus,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'orders';
  @override
  VerificationContext validateIntegrity(
    Insertable<Order> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('lab_id')) {
      context.handle(
        _labIdMeta,
        labId.isAcceptableOrUnknown(data['lab_id']!, _labIdMeta),
      );
    } else if (isInserting) {
      context.missing(_labIdMeta);
    }
    if (data.containsKey('patient_id')) {
      context.handle(
        _patientIdMeta,
        patientId.isAcceptableOrUnknown(data['patient_id']!, _patientIdMeta),
      );
    } else if (isInserting) {
      context.missing(_patientIdMeta);
    }
    if (data.containsKey('patient_name')) {
      context.handle(
        _patientNameMeta,
        patientName.isAcceptableOrUnknown(
          data['patient_name']!,
          _patientNameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_patientNameMeta);
    }
    if (data.containsKey('order_number')) {
      context.handle(
        _orderNumberMeta,
        orderNumber.isAcceptableOrUnknown(
          data['order_number']!,
          _orderNumberMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_orderNumberMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('priority')) {
      context.handle(
        _priorityMeta,
        priority.isAcceptableOrUnknown(data['priority']!, _priorityMeta),
      );
    }
    if (data.containsKey('test_types')) {
      context.handle(
        _testTypesMeta,
        testTypes.isAcceptableOrUnknown(data['test_types']!, _testTypesMeta),
      );
    } else if (isInserting) {
      context.missing(_testTypesMeta);
    }
    if (data.containsKey('doctor_name')) {
      context.handle(
        _doctorNameMeta,
        doctorName.isAcceptableOrUnknown(data['doctor_name']!, _doctorNameMeta),
      );
    }
    if (data.containsKey('doctor_id')) {
      context.handle(
        _doctorIdMeta,
        doctorId.isAcceptableOrUnknown(data['doctor_id']!, _doctorIdMeta),
      );
    }
    if (data.containsKey('diagnosis')) {
      context.handle(
        _diagnosisMeta,
        diagnosis.isAcceptableOrUnknown(data['diagnosis']!, _diagnosisMeta),
      );
    }
    if (data.containsKey('notes')) {
      context.handle(
        _notesMeta,
        notes.isAcceptableOrUnknown(data['notes']!, _notesMeta),
      );
    }
    if (data.containsKey('requested_by')) {
      context.handle(
        _requestedByMeta,
        requestedBy.isAcceptableOrUnknown(
          data['requested_by']!,
          _requestedByMeta,
        ),
      );
    }
    if (data.containsKey('collected_by')) {
      context.handle(
        _collectedByMeta,
        collectedBy.isAcceptableOrUnknown(
          data['collected_by']!,
          _collectedByMeta,
        ),
      );
    }
    if (data.containsKey('collection_date')) {
      context.handle(
        _collectionDateMeta,
        collectionDate.isAcceptableOrUnknown(
          data['collection_date']!,
          _collectionDateMeta,
        ),
      );
    }
    if (data.containsKey('received_date')) {
      context.handle(
        _receivedDateMeta,
        receivedDate.isAcceptableOrUnknown(
          data['received_date']!,
          _receivedDateMeta,
        ),
      );
    }
    if (data.containsKey('completed_date')) {
      context.handle(
        _completedDateMeta,
        completedDate.isAcceptableOrUnknown(
          data['completed_date']!,
          _completedDateMeta,
        ),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    } else if (isInserting) {
      context.missing(_syncStatusMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Order map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Order(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      labId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}lab_id'],
      )!,
      patientId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}patient_id'],
      )!,
      patientName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}patient_name'],
      )!,
      orderNumber: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}order_number'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      priority: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}priority'],
      ),
      testTypes: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}test_types'],
      )!,
      doctorName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}doctor_name'],
      ),
      doctorId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}doctor_id'],
      ),
      diagnosis: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}diagnosis'],
      ),
      notes: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}notes'],
      ),
      requestedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}requested_by'],
      ),
      collectedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}collected_by'],
      ),
      collectionDate: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}collection_date'],
      ),
      receivedDate: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}received_date'],
      ),
      completedDate: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}completed_date'],
      ),
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
    );
  }

  @override
  $OrdersTable createAlias(String alias) {
    return $OrdersTable(attachedDatabase, alias);
  }
}

class Order extends DataClass implements Insertable<Order> {
  final String id;
  final String labId;
  final String patientId;
  final String patientName;
  final String orderNumber;
  final String status;
  final String? priority;
  final String testTypes;
  final String? doctorName;
  final String? doctorId;
  final String? diagnosis;
  final String? notes;
  final String? requestedBy;
  final String? collectedBy;
  final String? collectionDate;
  final String? receivedDate;
  final String? completedDate;
  final String createdAt;
  final String updatedAt;
  final String syncStatus;
  const Order({
    required this.id,
    required this.labId,
    required this.patientId,
    required this.patientName,
    required this.orderNumber,
    required this.status,
    this.priority,
    required this.testTypes,
    this.doctorName,
    this.doctorId,
    this.diagnosis,
    this.notes,
    this.requestedBy,
    this.collectedBy,
    this.collectionDate,
    this.receivedDate,
    this.completedDate,
    required this.createdAt,
    required this.updatedAt,
    required this.syncStatus,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['lab_id'] = Variable<String>(labId);
    map['patient_id'] = Variable<String>(patientId);
    map['patient_name'] = Variable<String>(patientName);
    map['order_number'] = Variable<String>(orderNumber);
    map['status'] = Variable<String>(status);
    if (!nullToAbsent || priority != null) {
      map['priority'] = Variable<String>(priority);
    }
    map['test_types'] = Variable<String>(testTypes);
    if (!nullToAbsent || doctorName != null) {
      map['doctor_name'] = Variable<String>(doctorName);
    }
    if (!nullToAbsent || doctorId != null) {
      map['doctor_id'] = Variable<String>(doctorId);
    }
    if (!nullToAbsent || diagnosis != null) {
      map['diagnosis'] = Variable<String>(diagnosis);
    }
    if (!nullToAbsent || notes != null) {
      map['notes'] = Variable<String>(notes);
    }
    if (!nullToAbsent || requestedBy != null) {
      map['requested_by'] = Variable<String>(requestedBy);
    }
    if (!nullToAbsent || collectedBy != null) {
      map['collected_by'] = Variable<String>(collectedBy);
    }
    if (!nullToAbsent || collectionDate != null) {
      map['collection_date'] = Variable<String>(collectionDate);
    }
    if (!nullToAbsent || receivedDate != null) {
      map['received_date'] = Variable<String>(receivedDate);
    }
    if (!nullToAbsent || completedDate != null) {
      map['completed_date'] = Variable<String>(completedDate);
    }
    map['created_at'] = Variable<String>(createdAt);
    map['updated_at'] = Variable<String>(updatedAt);
    map['sync_status'] = Variable<String>(syncStatus);
    return map;
  }

  OrdersCompanion toCompanion(bool nullToAbsent) {
    return OrdersCompanion(
      id: Value(id),
      labId: Value(labId),
      patientId: Value(patientId),
      patientName: Value(patientName),
      orderNumber: Value(orderNumber),
      status: Value(status),
      priority: priority == null && nullToAbsent
          ? const Value.absent()
          : Value(priority),
      testTypes: Value(testTypes),
      doctorName: doctorName == null && nullToAbsent
          ? const Value.absent()
          : Value(doctorName),
      doctorId: doctorId == null && nullToAbsent
          ? const Value.absent()
          : Value(doctorId),
      diagnosis: diagnosis == null && nullToAbsent
          ? const Value.absent()
          : Value(diagnosis),
      notes: notes == null && nullToAbsent
          ? const Value.absent()
          : Value(notes),
      requestedBy: requestedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(requestedBy),
      collectedBy: collectedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(collectedBy),
      collectionDate: collectionDate == null && nullToAbsent
          ? const Value.absent()
          : Value(collectionDate),
      receivedDate: receivedDate == null && nullToAbsent
          ? const Value.absent()
          : Value(receivedDate),
      completedDate: completedDate == null && nullToAbsent
          ? const Value.absent()
          : Value(completedDate),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
      syncStatus: Value(syncStatus),
    );
  }

  factory Order.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Order(
      id: serializer.fromJson<String>(json['id']),
      labId: serializer.fromJson<String>(json['labId']),
      patientId: serializer.fromJson<String>(json['patientId']),
      patientName: serializer.fromJson<String>(json['patientName']),
      orderNumber: serializer.fromJson<String>(json['orderNumber']),
      status: serializer.fromJson<String>(json['status']),
      priority: serializer.fromJson<String?>(json['priority']),
      testTypes: serializer.fromJson<String>(json['testTypes']),
      doctorName: serializer.fromJson<String?>(json['doctorName']),
      doctorId: serializer.fromJson<String?>(json['doctorId']),
      diagnosis: serializer.fromJson<String?>(json['diagnosis']),
      notes: serializer.fromJson<String?>(json['notes']),
      requestedBy: serializer.fromJson<String?>(json['requestedBy']),
      collectedBy: serializer.fromJson<String?>(json['collectedBy']),
      collectionDate: serializer.fromJson<String?>(json['collectionDate']),
      receivedDate: serializer.fromJson<String?>(json['receivedDate']),
      completedDate: serializer.fromJson<String?>(json['completedDate']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'labId': serializer.toJson<String>(labId),
      'patientId': serializer.toJson<String>(patientId),
      'patientName': serializer.toJson<String>(patientName),
      'orderNumber': serializer.toJson<String>(orderNumber),
      'status': serializer.toJson<String>(status),
      'priority': serializer.toJson<String?>(priority),
      'testTypes': serializer.toJson<String>(testTypes),
      'doctorName': serializer.toJson<String?>(doctorName),
      'doctorId': serializer.toJson<String?>(doctorId),
      'diagnosis': serializer.toJson<String?>(diagnosis),
      'notes': serializer.toJson<String?>(notes),
      'requestedBy': serializer.toJson<String?>(requestedBy),
      'collectedBy': serializer.toJson<String?>(collectedBy),
      'collectionDate': serializer.toJson<String?>(collectionDate),
      'receivedDate': serializer.toJson<String?>(receivedDate),
      'completedDate': serializer.toJson<String?>(completedDate),
      'createdAt': serializer.toJson<String>(createdAt),
      'updatedAt': serializer.toJson<String>(updatedAt),
      'syncStatus': serializer.toJson<String>(syncStatus),
    };
  }

  Order copyWith({
    String? id,
    String? labId,
    String? patientId,
    String? patientName,
    String? orderNumber,
    String? status,
    Value<String?> priority = const Value.absent(),
    String? testTypes,
    Value<String?> doctorName = const Value.absent(),
    Value<String?> doctorId = const Value.absent(),
    Value<String?> diagnosis = const Value.absent(),
    Value<String?> notes = const Value.absent(),
    Value<String?> requestedBy = const Value.absent(),
    Value<String?> collectedBy = const Value.absent(),
    Value<String?> collectionDate = const Value.absent(),
    Value<String?> receivedDate = const Value.absent(),
    Value<String?> completedDate = const Value.absent(),
    String? createdAt,
    String? updatedAt,
    String? syncStatus,
  }) => Order(
    id: id ?? this.id,
    labId: labId ?? this.labId,
    patientId: patientId ?? this.patientId,
    patientName: patientName ?? this.patientName,
    orderNumber: orderNumber ?? this.orderNumber,
    status: status ?? this.status,
    priority: priority.present ? priority.value : this.priority,
    testTypes: testTypes ?? this.testTypes,
    doctorName: doctorName.present ? doctorName.value : this.doctorName,
    doctorId: doctorId.present ? doctorId.value : this.doctorId,
    diagnosis: diagnosis.present ? diagnosis.value : this.diagnosis,
    notes: notes.present ? notes.value : this.notes,
    requestedBy: requestedBy.present ? requestedBy.value : this.requestedBy,
    collectedBy: collectedBy.present ? collectedBy.value : this.collectedBy,
    collectionDate: collectionDate.present
        ? collectionDate.value
        : this.collectionDate,
    receivedDate: receivedDate.present ? receivedDate.value : this.receivedDate,
    completedDate: completedDate.present
        ? completedDate.value
        : this.completedDate,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
    syncStatus: syncStatus ?? this.syncStatus,
  );
  Order copyWithCompanion(OrdersCompanion data) {
    return Order(
      id: data.id.present ? data.id.value : this.id,
      labId: data.labId.present ? data.labId.value : this.labId,
      patientId: data.patientId.present ? data.patientId.value : this.patientId,
      patientName: data.patientName.present
          ? data.patientName.value
          : this.patientName,
      orderNumber: data.orderNumber.present
          ? data.orderNumber.value
          : this.orderNumber,
      status: data.status.present ? data.status.value : this.status,
      priority: data.priority.present ? data.priority.value : this.priority,
      testTypes: data.testTypes.present ? data.testTypes.value : this.testTypes,
      doctorName: data.doctorName.present
          ? data.doctorName.value
          : this.doctorName,
      doctorId: data.doctorId.present ? data.doctorId.value : this.doctorId,
      diagnosis: data.diagnosis.present ? data.diagnosis.value : this.diagnosis,
      notes: data.notes.present ? data.notes.value : this.notes,
      requestedBy: data.requestedBy.present
          ? data.requestedBy.value
          : this.requestedBy,
      collectedBy: data.collectedBy.present
          ? data.collectedBy.value
          : this.collectedBy,
      collectionDate: data.collectionDate.present
          ? data.collectionDate.value
          : this.collectionDate,
      receivedDate: data.receivedDate.present
          ? data.receivedDate.value
          : this.receivedDate,
      completedDate: data.completedDate.present
          ? data.completedDate.value
          : this.completedDate,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Order(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('patientId: $patientId, ')
          ..write('patientName: $patientName, ')
          ..write('orderNumber: $orderNumber, ')
          ..write('status: $status, ')
          ..write('priority: $priority, ')
          ..write('testTypes: $testTypes, ')
          ..write('doctorName: $doctorName, ')
          ..write('doctorId: $doctorId, ')
          ..write('diagnosis: $diagnosis, ')
          ..write('notes: $notes, ')
          ..write('requestedBy: $requestedBy, ')
          ..write('collectedBy: $collectedBy, ')
          ..write('collectionDate: $collectionDate, ')
          ..write('receivedDate: $receivedDate, ')
          ..write('completedDate: $completedDate, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('syncStatus: $syncStatus')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    labId,
    patientId,
    patientName,
    orderNumber,
    status,
    priority,
    testTypes,
    doctorName,
    doctorId,
    diagnosis,
    notes,
    requestedBy,
    collectedBy,
    collectionDate,
    receivedDate,
    completedDate,
    createdAt,
    updatedAt,
    syncStatus,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Order &&
          other.id == this.id &&
          other.labId == this.labId &&
          other.patientId == this.patientId &&
          other.patientName == this.patientName &&
          other.orderNumber == this.orderNumber &&
          other.status == this.status &&
          other.priority == this.priority &&
          other.testTypes == this.testTypes &&
          other.doctorName == this.doctorName &&
          other.doctorId == this.doctorId &&
          other.diagnosis == this.diagnosis &&
          other.notes == this.notes &&
          other.requestedBy == this.requestedBy &&
          other.collectedBy == this.collectedBy &&
          other.collectionDate == this.collectionDate &&
          other.receivedDate == this.receivedDate &&
          other.completedDate == this.completedDate &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt &&
          other.syncStatus == this.syncStatus);
}

class OrdersCompanion extends UpdateCompanion<Order> {
  final Value<String> id;
  final Value<String> labId;
  final Value<String> patientId;
  final Value<String> patientName;
  final Value<String> orderNumber;
  final Value<String> status;
  final Value<String?> priority;
  final Value<String> testTypes;
  final Value<String?> doctorName;
  final Value<String?> doctorId;
  final Value<String?> diagnosis;
  final Value<String?> notes;
  final Value<String?> requestedBy;
  final Value<String?> collectedBy;
  final Value<String?> collectionDate;
  final Value<String?> receivedDate;
  final Value<String?> completedDate;
  final Value<String> createdAt;
  final Value<String> updatedAt;
  final Value<String> syncStatus;
  final Value<int> rowid;
  const OrdersCompanion({
    this.id = const Value.absent(),
    this.labId = const Value.absent(),
    this.patientId = const Value.absent(),
    this.patientName = const Value.absent(),
    this.orderNumber = const Value.absent(),
    this.status = const Value.absent(),
    this.priority = const Value.absent(),
    this.testTypes = const Value.absent(),
    this.doctorName = const Value.absent(),
    this.doctorId = const Value.absent(),
    this.diagnosis = const Value.absent(),
    this.notes = const Value.absent(),
    this.requestedBy = const Value.absent(),
    this.collectedBy = const Value.absent(),
    this.collectionDate = const Value.absent(),
    this.receivedDate = const Value.absent(),
    this.completedDate = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  OrdersCompanion.insert({
    required String id,
    required String labId,
    required String patientId,
    required String patientName,
    required String orderNumber,
    required String status,
    this.priority = const Value.absent(),
    required String testTypes,
    this.doctorName = const Value.absent(),
    this.doctorId = const Value.absent(),
    this.diagnosis = const Value.absent(),
    this.notes = const Value.absent(),
    this.requestedBy = const Value.absent(),
    this.collectedBy = const Value.absent(),
    this.collectionDate = const Value.absent(),
    this.receivedDate = const Value.absent(),
    this.completedDate = const Value.absent(),
    required String createdAt,
    required String updatedAt,
    required String syncStatus,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       labId = Value(labId),
       patientId = Value(patientId),
       patientName = Value(patientName),
       orderNumber = Value(orderNumber),
       status = Value(status),
       testTypes = Value(testTypes),
       createdAt = Value(createdAt),
       updatedAt = Value(updatedAt),
       syncStatus = Value(syncStatus);
  static Insertable<Order> custom({
    Expression<String>? id,
    Expression<String>? labId,
    Expression<String>? patientId,
    Expression<String>? patientName,
    Expression<String>? orderNumber,
    Expression<String>? status,
    Expression<String>? priority,
    Expression<String>? testTypes,
    Expression<String>? doctorName,
    Expression<String>? doctorId,
    Expression<String>? diagnosis,
    Expression<String>? notes,
    Expression<String>? requestedBy,
    Expression<String>? collectedBy,
    Expression<String>? collectionDate,
    Expression<String>? receivedDate,
    Expression<String>? completedDate,
    Expression<String>? createdAt,
    Expression<String>? updatedAt,
    Expression<String>? syncStatus,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (labId != null) 'lab_id': labId,
      if (patientId != null) 'patient_id': patientId,
      if (patientName != null) 'patient_name': patientName,
      if (orderNumber != null) 'order_number': orderNumber,
      if (status != null) 'status': status,
      if (priority != null) 'priority': priority,
      if (testTypes != null) 'test_types': testTypes,
      if (doctorName != null) 'doctor_name': doctorName,
      if (doctorId != null) 'doctor_id': doctorId,
      if (diagnosis != null) 'diagnosis': diagnosis,
      if (notes != null) 'notes': notes,
      if (requestedBy != null) 'requested_by': requestedBy,
      if (collectedBy != null) 'collected_by': collectedBy,
      if (collectionDate != null) 'collection_date': collectionDate,
      if (receivedDate != null) 'received_date': receivedDate,
      if (completedDate != null) 'completed_date': completedDate,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (rowid != null) 'rowid': rowid,
    });
  }

  OrdersCompanion copyWith({
    Value<String>? id,
    Value<String>? labId,
    Value<String>? patientId,
    Value<String>? patientName,
    Value<String>? orderNumber,
    Value<String>? status,
    Value<String?>? priority,
    Value<String>? testTypes,
    Value<String?>? doctorName,
    Value<String?>? doctorId,
    Value<String?>? diagnosis,
    Value<String?>? notes,
    Value<String?>? requestedBy,
    Value<String?>? collectedBy,
    Value<String?>? collectionDate,
    Value<String?>? receivedDate,
    Value<String?>? completedDate,
    Value<String>? createdAt,
    Value<String>? updatedAt,
    Value<String>? syncStatus,
    Value<int>? rowid,
  }) {
    return OrdersCompanion(
      id: id ?? this.id,
      labId: labId ?? this.labId,
      patientId: patientId ?? this.patientId,
      patientName: patientName ?? this.patientName,
      orderNumber: orderNumber ?? this.orderNumber,
      status: status ?? this.status,
      priority: priority ?? this.priority,
      testTypes: testTypes ?? this.testTypes,
      doctorName: doctorName ?? this.doctorName,
      doctorId: doctorId ?? this.doctorId,
      diagnosis: diagnosis ?? this.diagnosis,
      notes: notes ?? this.notes,
      requestedBy: requestedBy ?? this.requestedBy,
      collectedBy: collectedBy ?? this.collectedBy,
      collectionDate: collectionDate ?? this.collectionDate,
      receivedDate: receivedDate ?? this.receivedDate,
      completedDate: completedDate ?? this.completedDate,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      syncStatus: syncStatus ?? this.syncStatus,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (labId.present) {
      map['lab_id'] = Variable<String>(labId.value);
    }
    if (patientId.present) {
      map['patient_id'] = Variable<String>(patientId.value);
    }
    if (patientName.present) {
      map['patient_name'] = Variable<String>(patientName.value);
    }
    if (orderNumber.present) {
      map['order_number'] = Variable<String>(orderNumber.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (priority.present) {
      map['priority'] = Variable<String>(priority.value);
    }
    if (testTypes.present) {
      map['test_types'] = Variable<String>(testTypes.value);
    }
    if (doctorName.present) {
      map['doctor_name'] = Variable<String>(doctorName.value);
    }
    if (doctorId.present) {
      map['doctor_id'] = Variable<String>(doctorId.value);
    }
    if (diagnosis.present) {
      map['diagnosis'] = Variable<String>(diagnosis.value);
    }
    if (notes.present) {
      map['notes'] = Variable<String>(notes.value);
    }
    if (requestedBy.present) {
      map['requested_by'] = Variable<String>(requestedBy.value);
    }
    if (collectedBy.present) {
      map['collected_by'] = Variable<String>(collectedBy.value);
    }
    if (collectionDate.present) {
      map['collection_date'] = Variable<String>(collectionDate.value);
    }
    if (receivedDate.present) {
      map['received_date'] = Variable<String>(receivedDate.value);
    }
    if (completedDate.present) {
      map['completed_date'] = Variable<String>(completedDate.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('OrdersCompanion(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('patientId: $patientId, ')
          ..write('patientName: $patientName, ')
          ..write('orderNumber: $orderNumber, ')
          ..write('status: $status, ')
          ..write('priority: $priority, ')
          ..write('testTypes: $testTypes, ')
          ..write('doctorName: $doctorName, ')
          ..write('doctorId: $doctorId, ')
          ..write('diagnosis: $diagnosis, ')
          ..write('notes: $notes, ')
          ..write('requestedBy: $requestedBy, ')
          ..write('collectedBy: $collectedBy, ')
          ..write('collectionDate: $collectionDate, ')
          ..write('receivedDate: $receivedDate, ')
          ..write('completedDate: $completedDate, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SamplesTable extends Samples with TableInfo<$SamplesTable, Sample> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SamplesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _labIdMeta = const VerificationMeta('labId');
  @override
  late final GeneratedColumn<String> labId = GeneratedColumn<String>(
    'lab_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _orderIdMeta = const VerificationMeta(
    'orderId',
  );
  @override
  late final GeneratedColumn<String> orderId = GeneratedColumn<String>(
    'order_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _patientIdMeta = const VerificationMeta(
    'patientId',
  );
  @override
  late final GeneratedColumn<String> patientId = GeneratedColumn<String>(
    'patient_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _sampleTypeMeta = const VerificationMeta(
    'sampleType',
  );
  @override
  late final GeneratedColumn<String> sampleType = GeneratedColumn<String>(
    'sample_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _barcodeMeta = const VerificationMeta(
    'barcode',
  );
  @override
  late final GeneratedColumn<String> barcode = GeneratedColumn<String>(
    'barcode',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _containerTypeMeta = const VerificationMeta(
    'containerType',
  );
  @override
  late final GeneratedColumn<String> containerType = GeneratedColumn<String>(
    'container_type',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _volumeMeta = const VerificationMeta('volume');
  @override
  late final GeneratedColumn<double> volume = GeneratedColumn<double>(
    'volume',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _collectedAtMeta = const VerificationMeta(
    'collectedAt',
  );
  @override
  late final GeneratedColumn<String> collectedAt = GeneratedColumn<String>(
    'collected_at',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _collectedByMeta = const VerificationMeta(
    'collectedBy',
  );
  @override
  late final GeneratedColumn<String> collectedBy = GeneratedColumn<String>(
    'collected_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _receivedAtMeta = const VerificationMeta(
    'receivedAt',
  );
  @override
  late final GeneratedColumn<String> receivedAt = GeneratedColumn<String>(
    'received_at',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _receivedByMeta = const VerificationMeta(
    'receivedBy',
  );
  @override
  late final GeneratedColumn<String> receivedBy = GeneratedColumn<String>(
    'received_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _processedAtMeta = const VerificationMeta(
    'processedAt',
  );
  @override
  late final GeneratedColumn<String> processedAt = GeneratedColumn<String>(
    'processed_at',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _processedByMeta = const VerificationMeta(
    'processedBy',
  );
  @override
  late final GeneratedColumn<String> processedBy = GeneratedColumn<String>(
    'processed_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _storageLocationMeta = const VerificationMeta(
    'storageLocation',
  );
  @override
  late final GeneratedColumn<String> storageLocation = GeneratedColumn<String>(
    'storage_location',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _rejectionReasonMeta = const VerificationMeta(
    'rejectionReason',
  );
  @override
  late final GeneratedColumn<String> rejectionReason = GeneratedColumn<String>(
    'rejection_reason',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _notesMeta = const VerificationMeta('notes');
  @override
  late final GeneratedColumn<String> notes = GeneratedColumn<String>(
    'notes',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    labId,
    orderId,
    patientId,
    sampleType,
    barcode,
    status,
    containerType,
    volume,
    collectedAt,
    collectedBy,
    receivedAt,
    receivedBy,
    processedAt,
    processedBy,
    storageLocation,
    rejectionReason,
    notes,
    createdAt,
    updatedAt,
    syncStatus,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'samples';
  @override
  VerificationContext validateIntegrity(
    Insertable<Sample> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('lab_id')) {
      context.handle(
        _labIdMeta,
        labId.isAcceptableOrUnknown(data['lab_id']!, _labIdMeta),
      );
    } else if (isInserting) {
      context.missing(_labIdMeta);
    }
    if (data.containsKey('order_id')) {
      context.handle(
        _orderIdMeta,
        orderId.isAcceptableOrUnknown(data['order_id']!, _orderIdMeta),
      );
    } else if (isInserting) {
      context.missing(_orderIdMeta);
    }
    if (data.containsKey('patient_id')) {
      context.handle(
        _patientIdMeta,
        patientId.isAcceptableOrUnknown(data['patient_id']!, _patientIdMeta),
      );
    } else if (isInserting) {
      context.missing(_patientIdMeta);
    }
    if (data.containsKey('sample_type')) {
      context.handle(
        _sampleTypeMeta,
        sampleType.isAcceptableOrUnknown(data['sample_type']!, _sampleTypeMeta),
      );
    } else if (isInserting) {
      context.missing(_sampleTypeMeta);
    }
    if (data.containsKey('barcode')) {
      context.handle(
        _barcodeMeta,
        barcode.isAcceptableOrUnknown(data['barcode']!, _barcodeMeta),
      );
    } else if (isInserting) {
      context.missing(_barcodeMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('container_type')) {
      context.handle(
        _containerTypeMeta,
        containerType.isAcceptableOrUnknown(
          data['container_type']!,
          _containerTypeMeta,
        ),
      );
    }
    if (data.containsKey('volume')) {
      context.handle(
        _volumeMeta,
        volume.isAcceptableOrUnknown(data['volume']!, _volumeMeta),
      );
    }
    if (data.containsKey('collected_at')) {
      context.handle(
        _collectedAtMeta,
        collectedAt.isAcceptableOrUnknown(
          data['collected_at']!,
          _collectedAtMeta,
        ),
      );
    }
    if (data.containsKey('collected_by')) {
      context.handle(
        _collectedByMeta,
        collectedBy.isAcceptableOrUnknown(
          data['collected_by']!,
          _collectedByMeta,
        ),
      );
    }
    if (data.containsKey('received_at')) {
      context.handle(
        _receivedAtMeta,
        receivedAt.isAcceptableOrUnknown(data['received_at']!, _receivedAtMeta),
      );
    }
    if (data.containsKey('received_by')) {
      context.handle(
        _receivedByMeta,
        receivedBy.isAcceptableOrUnknown(data['received_by']!, _receivedByMeta),
      );
    }
    if (data.containsKey('processed_at')) {
      context.handle(
        _processedAtMeta,
        processedAt.isAcceptableOrUnknown(
          data['processed_at']!,
          _processedAtMeta,
        ),
      );
    }
    if (data.containsKey('processed_by')) {
      context.handle(
        _processedByMeta,
        processedBy.isAcceptableOrUnknown(
          data['processed_by']!,
          _processedByMeta,
        ),
      );
    }
    if (data.containsKey('storage_location')) {
      context.handle(
        _storageLocationMeta,
        storageLocation.isAcceptableOrUnknown(
          data['storage_location']!,
          _storageLocationMeta,
        ),
      );
    }
    if (data.containsKey('rejection_reason')) {
      context.handle(
        _rejectionReasonMeta,
        rejectionReason.isAcceptableOrUnknown(
          data['rejection_reason']!,
          _rejectionReasonMeta,
        ),
      );
    }
    if (data.containsKey('notes')) {
      context.handle(
        _notesMeta,
        notes.isAcceptableOrUnknown(data['notes']!, _notesMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    } else if (isInserting) {
      context.missing(_syncStatusMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Sample map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Sample(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      labId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}lab_id'],
      )!,
      orderId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}order_id'],
      )!,
      patientId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}patient_id'],
      )!,
      sampleType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sample_type'],
      )!,
      barcode: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}barcode'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      containerType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}container_type'],
      ),
      volume: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}volume'],
      ),
      collectedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}collected_at'],
      ),
      collectedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}collected_by'],
      ),
      receivedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}received_at'],
      ),
      receivedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}received_by'],
      ),
      processedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}processed_at'],
      ),
      processedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}processed_by'],
      ),
      storageLocation: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}storage_location'],
      ),
      rejectionReason: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}rejection_reason'],
      ),
      notes: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}notes'],
      ),
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
    );
  }

  @override
  $SamplesTable createAlias(String alias) {
    return $SamplesTable(attachedDatabase, alias);
  }
}

class Sample extends DataClass implements Insertable<Sample> {
  final String id;
  final String labId;
  final String orderId;
  final String patientId;
  final String sampleType;
  final String barcode;
  final String status;
  final String? containerType;
  final double? volume;
  final String? collectedAt;
  final String? collectedBy;
  final String? receivedAt;
  final String? receivedBy;
  final String? processedAt;
  final String? processedBy;
  final String? storageLocation;
  final String? rejectionReason;
  final String? notes;
  final String createdAt;
  final String updatedAt;
  final String syncStatus;
  const Sample({
    required this.id,
    required this.labId,
    required this.orderId,
    required this.patientId,
    required this.sampleType,
    required this.barcode,
    required this.status,
    this.containerType,
    this.volume,
    this.collectedAt,
    this.collectedBy,
    this.receivedAt,
    this.receivedBy,
    this.processedAt,
    this.processedBy,
    this.storageLocation,
    this.rejectionReason,
    this.notes,
    required this.createdAt,
    required this.updatedAt,
    required this.syncStatus,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['lab_id'] = Variable<String>(labId);
    map['order_id'] = Variable<String>(orderId);
    map['patient_id'] = Variable<String>(patientId);
    map['sample_type'] = Variable<String>(sampleType);
    map['barcode'] = Variable<String>(barcode);
    map['status'] = Variable<String>(status);
    if (!nullToAbsent || containerType != null) {
      map['container_type'] = Variable<String>(containerType);
    }
    if (!nullToAbsent || volume != null) {
      map['volume'] = Variable<double>(volume);
    }
    if (!nullToAbsent || collectedAt != null) {
      map['collected_at'] = Variable<String>(collectedAt);
    }
    if (!nullToAbsent || collectedBy != null) {
      map['collected_by'] = Variable<String>(collectedBy);
    }
    if (!nullToAbsent || receivedAt != null) {
      map['received_at'] = Variable<String>(receivedAt);
    }
    if (!nullToAbsent || receivedBy != null) {
      map['received_by'] = Variable<String>(receivedBy);
    }
    if (!nullToAbsent || processedAt != null) {
      map['processed_at'] = Variable<String>(processedAt);
    }
    if (!nullToAbsent || processedBy != null) {
      map['processed_by'] = Variable<String>(processedBy);
    }
    if (!nullToAbsent || storageLocation != null) {
      map['storage_location'] = Variable<String>(storageLocation);
    }
    if (!nullToAbsent || rejectionReason != null) {
      map['rejection_reason'] = Variable<String>(rejectionReason);
    }
    if (!nullToAbsent || notes != null) {
      map['notes'] = Variable<String>(notes);
    }
    map['created_at'] = Variable<String>(createdAt);
    map['updated_at'] = Variable<String>(updatedAt);
    map['sync_status'] = Variable<String>(syncStatus);
    return map;
  }

  SamplesCompanion toCompanion(bool nullToAbsent) {
    return SamplesCompanion(
      id: Value(id),
      labId: Value(labId),
      orderId: Value(orderId),
      patientId: Value(patientId),
      sampleType: Value(sampleType),
      barcode: Value(barcode),
      status: Value(status),
      containerType: containerType == null && nullToAbsent
          ? const Value.absent()
          : Value(containerType),
      volume: volume == null && nullToAbsent
          ? const Value.absent()
          : Value(volume),
      collectedAt: collectedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(collectedAt),
      collectedBy: collectedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(collectedBy),
      receivedAt: receivedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(receivedAt),
      receivedBy: receivedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(receivedBy),
      processedAt: processedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(processedAt),
      processedBy: processedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(processedBy),
      storageLocation: storageLocation == null && nullToAbsent
          ? const Value.absent()
          : Value(storageLocation),
      rejectionReason: rejectionReason == null && nullToAbsent
          ? const Value.absent()
          : Value(rejectionReason),
      notes: notes == null && nullToAbsent
          ? const Value.absent()
          : Value(notes),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
      syncStatus: Value(syncStatus),
    );
  }

  factory Sample.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Sample(
      id: serializer.fromJson<String>(json['id']),
      labId: serializer.fromJson<String>(json['labId']),
      orderId: serializer.fromJson<String>(json['orderId']),
      patientId: serializer.fromJson<String>(json['patientId']),
      sampleType: serializer.fromJson<String>(json['sampleType']),
      barcode: serializer.fromJson<String>(json['barcode']),
      status: serializer.fromJson<String>(json['status']),
      containerType: serializer.fromJson<String?>(json['containerType']),
      volume: serializer.fromJson<double?>(json['volume']),
      collectedAt: serializer.fromJson<String?>(json['collectedAt']),
      collectedBy: serializer.fromJson<String?>(json['collectedBy']),
      receivedAt: serializer.fromJson<String?>(json['receivedAt']),
      receivedBy: serializer.fromJson<String?>(json['receivedBy']),
      processedAt: serializer.fromJson<String?>(json['processedAt']),
      processedBy: serializer.fromJson<String?>(json['processedBy']),
      storageLocation: serializer.fromJson<String?>(json['storageLocation']),
      rejectionReason: serializer.fromJson<String?>(json['rejectionReason']),
      notes: serializer.fromJson<String?>(json['notes']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'labId': serializer.toJson<String>(labId),
      'orderId': serializer.toJson<String>(orderId),
      'patientId': serializer.toJson<String>(patientId),
      'sampleType': serializer.toJson<String>(sampleType),
      'barcode': serializer.toJson<String>(barcode),
      'status': serializer.toJson<String>(status),
      'containerType': serializer.toJson<String?>(containerType),
      'volume': serializer.toJson<double?>(volume),
      'collectedAt': serializer.toJson<String?>(collectedAt),
      'collectedBy': serializer.toJson<String?>(collectedBy),
      'receivedAt': serializer.toJson<String?>(receivedAt),
      'receivedBy': serializer.toJson<String?>(receivedBy),
      'processedAt': serializer.toJson<String?>(processedAt),
      'processedBy': serializer.toJson<String?>(processedBy),
      'storageLocation': serializer.toJson<String?>(storageLocation),
      'rejectionReason': serializer.toJson<String?>(rejectionReason),
      'notes': serializer.toJson<String?>(notes),
      'createdAt': serializer.toJson<String>(createdAt),
      'updatedAt': serializer.toJson<String>(updatedAt),
      'syncStatus': serializer.toJson<String>(syncStatus),
    };
  }

  Sample copyWith({
    String? id,
    String? labId,
    String? orderId,
    String? patientId,
    String? sampleType,
    String? barcode,
    String? status,
    Value<String?> containerType = const Value.absent(),
    Value<double?> volume = const Value.absent(),
    Value<String?> collectedAt = const Value.absent(),
    Value<String?> collectedBy = const Value.absent(),
    Value<String?> receivedAt = const Value.absent(),
    Value<String?> receivedBy = const Value.absent(),
    Value<String?> processedAt = const Value.absent(),
    Value<String?> processedBy = const Value.absent(),
    Value<String?> storageLocation = const Value.absent(),
    Value<String?> rejectionReason = const Value.absent(),
    Value<String?> notes = const Value.absent(),
    String? createdAt,
    String? updatedAt,
    String? syncStatus,
  }) => Sample(
    id: id ?? this.id,
    labId: labId ?? this.labId,
    orderId: orderId ?? this.orderId,
    patientId: patientId ?? this.patientId,
    sampleType: sampleType ?? this.sampleType,
    barcode: barcode ?? this.barcode,
    status: status ?? this.status,
    containerType: containerType.present
        ? containerType.value
        : this.containerType,
    volume: volume.present ? volume.value : this.volume,
    collectedAt: collectedAt.present ? collectedAt.value : this.collectedAt,
    collectedBy: collectedBy.present ? collectedBy.value : this.collectedBy,
    receivedAt: receivedAt.present ? receivedAt.value : this.receivedAt,
    receivedBy: receivedBy.present ? receivedBy.value : this.receivedBy,
    processedAt: processedAt.present ? processedAt.value : this.processedAt,
    processedBy: processedBy.present ? processedBy.value : this.processedBy,
    storageLocation: storageLocation.present
        ? storageLocation.value
        : this.storageLocation,
    rejectionReason: rejectionReason.present
        ? rejectionReason.value
        : this.rejectionReason,
    notes: notes.present ? notes.value : this.notes,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
    syncStatus: syncStatus ?? this.syncStatus,
  );
  Sample copyWithCompanion(SamplesCompanion data) {
    return Sample(
      id: data.id.present ? data.id.value : this.id,
      labId: data.labId.present ? data.labId.value : this.labId,
      orderId: data.orderId.present ? data.orderId.value : this.orderId,
      patientId: data.patientId.present ? data.patientId.value : this.patientId,
      sampleType: data.sampleType.present
          ? data.sampleType.value
          : this.sampleType,
      barcode: data.barcode.present ? data.barcode.value : this.barcode,
      status: data.status.present ? data.status.value : this.status,
      containerType: data.containerType.present
          ? data.containerType.value
          : this.containerType,
      volume: data.volume.present ? data.volume.value : this.volume,
      collectedAt: data.collectedAt.present
          ? data.collectedAt.value
          : this.collectedAt,
      collectedBy: data.collectedBy.present
          ? data.collectedBy.value
          : this.collectedBy,
      receivedAt: data.receivedAt.present
          ? data.receivedAt.value
          : this.receivedAt,
      receivedBy: data.receivedBy.present
          ? data.receivedBy.value
          : this.receivedBy,
      processedAt: data.processedAt.present
          ? data.processedAt.value
          : this.processedAt,
      processedBy: data.processedBy.present
          ? data.processedBy.value
          : this.processedBy,
      storageLocation: data.storageLocation.present
          ? data.storageLocation.value
          : this.storageLocation,
      rejectionReason: data.rejectionReason.present
          ? data.rejectionReason.value
          : this.rejectionReason,
      notes: data.notes.present ? data.notes.value : this.notes,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Sample(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('orderId: $orderId, ')
          ..write('patientId: $patientId, ')
          ..write('sampleType: $sampleType, ')
          ..write('barcode: $barcode, ')
          ..write('status: $status, ')
          ..write('containerType: $containerType, ')
          ..write('volume: $volume, ')
          ..write('collectedAt: $collectedAt, ')
          ..write('collectedBy: $collectedBy, ')
          ..write('receivedAt: $receivedAt, ')
          ..write('receivedBy: $receivedBy, ')
          ..write('processedAt: $processedAt, ')
          ..write('processedBy: $processedBy, ')
          ..write('storageLocation: $storageLocation, ')
          ..write('rejectionReason: $rejectionReason, ')
          ..write('notes: $notes, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('syncStatus: $syncStatus')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
    id,
    labId,
    orderId,
    patientId,
    sampleType,
    barcode,
    status,
    containerType,
    volume,
    collectedAt,
    collectedBy,
    receivedAt,
    receivedBy,
    processedAt,
    processedBy,
    storageLocation,
    rejectionReason,
    notes,
    createdAt,
    updatedAt,
    syncStatus,
  ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Sample &&
          other.id == this.id &&
          other.labId == this.labId &&
          other.orderId == this.orderId &&
          other.patientId == this.patientId &&
          other.sampleType == this.sampleType &&
          other.barcode == this.barcode &&
          other.status == this.status &&
          other.containerType == this.containerType &&
          other.volume == this.volume &&
          other.collectedAt == this.collectedAt &&
          other.collectedBy == this.collectedBy &&
          other.receivedAt == this.receivedAt &&
          other.receivedBy == this.receivedBy &&
          other.processedAt == this.processedAt &&
          other.processedBy == this.processedBy &&
          other.storageLocation == this.storageLocation &&
          other.rejectionReason == this.rejectionReason &&
          other.notes == this.notes &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt &&
          other.syncStatus == this.syncStatus);
}

class SamplesCompanion extends UpdateCompanion<Sample> {
  final Value<String> id;
  final Value<String> labId;
  final Value<String> orderId;
  final Value<String> patientId;
  final Value<String> sampleType;
  final Value<String> barcode;
  final Value<String> status;
  final Value<String?> containerType;
  final Value<double?> volume;
  final Value<String?> collectedAt;
  final Value<String?> collectedBy;
  final Value<String?> receivedAt;
  final Value<String?> receivedBy;
  final Value<String?> processedAt;
  final Value<String?> processedBy;
  final Value<String?> storageLocation;
  final Value<String?> rejectionReason;
  final Value<String?> notes;
  final Value<String> createdAt;
  final Value<String> updatedAt;
  final Value<String> syncStatus;
  final Value<int> rowid;
  const SamplesCompanion({
    this.id = const Value.absent(),
    this.labId = const Value.absent(),
    this.orderId = const Value.absent(),
    this.patientId = const Value.absent(),
    this.sampleType = const Value.absent(),
    this.barcode = const Value.absent(),
    this.status = const Value.absent(),
    this.containerType = const Value.absent(),
    this.volume = const Value.absent(),
    this.collectedAt = const Value.absent(),
    this.collectedBy = const Value.absent(),
    this.receivedAt = const Value.absent(),
    this.receivedBy = const Value.absent(),
    this.processedAt = const Value.absent(),
    this.processedBy = const Value.absent(),
    this.storageLocation = const Value.absent(),
    this.rejectionReason = const Value.absent(),
    this.notes = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SamplesCompanion.insert({
    required String id,
    required String labId,
    required String orderId,
    required String patientId,
    required String sampleType,
    required String barcode,
    required String status,
    this.containerType = const Value.absent(),
    this.volume = const Value.absent(),
    this.collectedAt = const Value.absent(),
    this.collectedBy = const Value.absent(),
    this.receivedAt = const Value.absent(),
    this.receivedBy = const Value.absent(),
    this.processedAt = const Value.absent(),
    this.processedBy = const Value.absent(),
    this.storageLocation = const Value.absent(),
    this.rejectionReason = const Value.absent(),
    this.notes = const Value.absent(),
    required String createdAt,
    required String updatedAt,
    required String syncStatus,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       labId = Value(labId),
       orderId = Value(orderId),
       patientId = Value(patientId),
       sampleType = Value(sampleType),
       barcode = Value(barcode),
       status = Value(status),
       createdAt = Value(createdAt),
       updatedAt = Value(updatedAt),
       syncStatus = Value(syncStatus);
  static Insertable<Sample> custom({
    Expression<String>? id,
    Expression<String>? labId,
    Expression<String>? orderId,
    Expression<String>? patientId,
    Expression<String>? sampleType,
    Expression<String>? barcode,
    Expression<String>? status,
    Expression<String>? containerType,
    Expression<double>? volume,
    Expression<String>? collectedAt,
    Expression<String>? collectedBy,
    Expression<String>? receivedAt,
    Expression<String>? receivedBy,
    Expression<String>? processedAt,
    Expression<String>? processedBy,
    Expression<String>? storageLocation,
    Expression<String>? rejectionReason,
    Expression<String>? notes,
    Expression<String>? createdAt,
    Expression<String>? updatedAt,
    Expression<String>? syncStatus,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (labId != null) 'lab_id': labId,
      if (orderId != null) 'order_id': orderId,
      if (patientId != null) 'patient_id': patientId,
      if (sampleType != null) 'sample_type': sampleType,
      if (barcode != null) 'barcode': barcode,
      if (status != null) 'status': status,
      if (containerType != null) 'container_type': containerType,
      if (volume != null) 'volume': volume,
      if (collectedAt != null) 'collected_at': collectedAt,
      if (collectedBy != null) 'collected_by': collectedBy,
      if (receivedAt != null) 'received_at': receivedAt,
      if (receivedBy != null) 'received_by': receivedBy,
      if (processedAt != null) 'processed_at': processedAt,
      if (processedBy != null) 'processed_by': processedBy,
      if (storageLocation != null) 'storage_location': storageLocation,
      if (rejectionReason != null) 'rejection_reason': rejectionReason,
      if (notes != null) 'notes': notes,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SamplesCompanion copyWith({
    Value<String>? id,
    Value<String>? labId,
    Value<String>? orderId,
    Value<String>? patientId,
    Value<String>? sampleType,
    Value<String>? barcode,
    Value<String>? status,
    Value<String?>? containerType,
    Value<double?>? volume,
    Value<String?>? collectedAt,
    Value<String?>? collectedBy,
    Value<String?>? receivedAt,
    Value<String?>? receivedBy,
    Value<String?>? processedAt,
    Value<String?>? processedBy,
    Value<String?>? storageLocation,
    Value<String?>? rejectionReason,
    Value<String?>? notes,
    Value<String>? createdAt,
    Value<String>? updatedAt,
    Value<String>? syncStatus,
    Value<int>? rowid,
  }) {
    return SamplesCompanion(
      id: id ?? this.id,
      labId: labId ?? this.labId,
      orderId: orderId ?? this.orderId,
      patientId: patientId ?? this.patientId,
      sampleType: sampleType ?? this.sampleType,
      barcode: barcode ?? this.barcode,
      status: status ?? this.status,
      containerType: containerType ?? this.containerType,
      volume: volume ?? this.volume,
      collectedAt: collectedAt ?? this.collectedAt,
      collectedBy: collectedBy ?? this.collectedBy,
      receivedAt: receivedAt ?? this.receivedAt,
      receivedBy: receivedBy ?? this.receivedBy,
      processedAt: processedAt ?? this.processedAt,
      processedBy: processedBy ?? this.processedBy,
      storageLocation: storageLocation ?? this.storageLocation,
      rejectionReason: rejectionReason ?? this.rejectionReason,
      notes: notes ?? this.notes,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      syncStatus: syncStatus ?? this.syncStatus,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (labId.present) {
      map['lab_id'] = Variable<String>(labId.value);
    }
    if (orderId.present) {
      map['order_id'] = Variable<String>(orderId.value);
    }
    if (patientId.present) {
      map['patient_id'] = Variable<String>(patientId.value);
    }
    if (sampleType.present) {
      map['sample_type'] = Variable<String>(sampleType.value);
    }
    if (barcode.present) {
      map['barcode'] = Variable<String>(barcode.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (containerType.present) {
      map['container_type'] = Variable<String>(containerType.value);
    }
    if (volume.present) {
      map['volume'] = Variable<double>(volume.value);
    }
    if (collectedAt.present) {
      map['collected_at'] = Variable<String>(collectedAt.value);
    }
    if (collectedBy.present) {
      map['collected_by'] = Variable<String>(collectedBy.value);
    }
    if (receivedAt.present) {
      map['received_at'] = Variable<String>(receivedAt.value);
    }
    if (receivedBy.present) {
      map['received_by'] = Variable<String>(receivedBy.value);
    }
    if (processedAt.present) {
      map['processed_at'] = Variable<String>(processedAt.value);
    }
    if (processedBy.present) {
      map['processed_by'] = Variable<String>(processedBy.value);
    }
    if (storageLocation.present) {
      map['storage_location'] = Variable<String>(storageLocation.value);
    }
    if (rejectionReason.present) {
      map['rejection_reason'] = Variable<String>(rejectionReason.value);
    }
    if (notes.present) {
      map['notes'] = Variable<String>(notes.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SamplesCompanion(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('orderId: $orderId, ')
          ..write('patientId: $patientId, ')
          ..write('sampleType: $sampleType, ')
          ..write('barcode: $barcode, ')
          ..write('status: $status, ')
          ..write('containerType: $containerType, ')
          ..write('volume: $volume, ')
          ..write('collectedAt: $collectedAt, ')
          ..write('collectedBy: $collectedBy, ')
          ..write('receivedAt: $receivedAt, ')
          ..write('receivedBy: $receivedBy, ')
          ..write('processedAt: $processedAt, ')
          ..write('processedBy: $processedBy, ')
          ..write('storageLocation: $storageLocation, ')
          ..write('rejectionReason: $rejectionReason, ')
          ..write('notes: $notes, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ResultsTable extends Results with TableInfo<$ResultsTable, Result> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ResultsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _labIdMeta = const VerificationMeta('labId');
  @override
  late final GeneratedColumn<String> labId = GeneratedColumn<String>(
    'lab_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _orderIdMeta = const VerificationMeta(
    'orderId',
  );
  @override
  late final GeneratedColumn<String> orderId = GeneratedColumn<String>(
    'order_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _sampleIdMeta = const VerificationMeta(
    'sampleId',
  );
  @override
  late final GeneratedColumn<String> sampleId = GeneratedColumn<String>(
    'sample_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _patientIdMeta = const VerificationMeta(
    'patientId',
  );
  @override
  late final GeneratedColumn<String> patientId = GeneratedColumn<String>(
    'patient_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _testCodeMeta = const VerificationMeta(
    'testCode',
  );
  @override
  late final GeneratedColumn<String> testCode = GeneratedColumn<String>(
    'test_code',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _testNameMeta = const VerificationMeta(
    'testName',
  );
  @override
  late final GeneratedColumn<String> testName = GeneratedColumn<String>(
    'test_name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _resultMeta = const VerificationMeta('result');
  @override
  late final GeneratedColumn<String> result = GeneratedColumn<String>(
    'result',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _unitMeta = const VerificationMeta('unit');
  @override
  late final GeneratedColumn<String> unit = GeneratedColumn<String>(
    'unit',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _referenceRangeMeta = const VerificationMeta(
    'referenceRange',
  );
  @override
  late final GeneratedColumn<String> referenceRange = GeneratedColumn<String>(
    'reference_range',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _flagMeta = const VerificationMeta('flag');
  @override
  late final GeneratedColumn<String> flag = GeneratedColumn<String>(
    'flag',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _isAbnormalMeta = const VerificationMeta(
    'isAbnormal',
  );
  @override
  late final GeneratedColumn<int> isAbnormal = GeneratedColumn<int>(
    'is_abnormal',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _isCriticalMeta = const VerificationMeta(
    'isCritical',
  );
  @override
  late final GeneratedColumn<int> isCritical = GeneratedColumn<int>(
    'is_critical',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _validatedByMeta = const VerificationMeta(
    'validatedBy',
  );
  @override
  late final GeneratedColumn<String> validatedBy = GeneratedColumn<String>(
    'validated_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _validatedAtMeta = const VerificationMeta(
    'validatedAt',
  );
  @override
  late final GeneratedColumn<String> validatedAt = GeneratedColumn<String>(
    'validated_at',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _performedByMeta = const VerificationMeta(
    'performedBy',
  );
  @override
  late final GeneratedColumn<String> performedBy = GeneratedColumn<String>(
    'performed_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _instrumentIdMeta = const VerificationMeta(
    'instrumentId',
  );
  @override
  late final GeneratedColumn<String> instrumentId = GeneratedColumn<String>(
    'instrument_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _notesMeta = const VerificationMeta('notes');
  @override
  late final GeneratedColumn<String> notes = GeneratedColumn<String>(
    'notes',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    labId,
    orderId,
    sampleId,
    patientId,
    testCode,
    testName,
    result,
    unit,
    referenceRange,
    flag,
    isAbnormal,
    isCritical,
    validatedBy,
    validatedAt,
    performedBy,
    instrumentId,
    notes,
    status,
    createdAt,
    updatedAt,
    syncStatus,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'results';
  @override
  VerificationContext validateIntegrity(
    Insertable<Result> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('lab_id')) {
      context.handle(
        _labIdMeta,
        labId.isAcceptableOrUnknown(data['lab_id']!, _labIdMeta),
      );
    } else if (isInserting) {
      context.missing(_labIdMeta);
    }
    if (data.containsKey('order_id')) {
      context.handle(
        _orderIdMeta,
        orderId.isAcceptableOrUnknown(data['order_id']!, _orderIdMeta),
      );
    } else if (isInserting) {
      context.missing(_orderIdMeta);
    }
    if (data.containsKey('sample_id')) {
      context.handle(
        _sampleIdMeta,
        sampleId.isAcceptableOrUnknown(data['sample_id']!, _sampleIdMeta),
      );
    }
    if (data.containsKey('patient_id')) {
      context.handle(
        _patientIdMeta,
        patientId.isAcceptableOrUnknown(data['patient_id']!, _patientIdMeta),
      );
    } else if (isInserting) {
      context.missing(_patientIdMeta);
    }
    if (data.containsKey('test_code')) {
      context.handle(
        _testCodeMeta,
        testCode.isAcceptableOrUnknown(data['test_code']!, _testCodeMeta),
      );
    } else if (isInserting) {
      context.missing(_testCodeMeta);
    }
    if (data.containsKey('test_name')) {
      context.handle(
        _testNameMeta,
        testName.isAcceptableOrUnknown(data['test_name']!, _testNameMeta),
      );
    } else if (isInserting) {
      context.missing(_testNameMeta);
    }
    if (data.containsKey('result')) {
      context.handle(
        _resultMeta,
        result.isAcceptableOrUnknown(data['result']!, _resultMeta),
      );
    } else if (isInserting) {
      context.missing(_resultMeta);
    }
    if (data.containsKey('unit')) {
      context.handle(
        _unitMeta,
        unit.isAcceptableOrUnknown(data['unit']!, _unitMeta),
      );
    }
    if (data.containsKey('reference_range')) {
      context.handle(
        _referenceRangeMeta,
        referenceRange.isAcceptableOrUnknown(
          data['reference_range']!,
          _referenceRangeMeta,
        ),
      );
    }
    if (data.containsKey('flag')) {
      context.handle(
        _flagMeta,
        flag.isAcceptableOrUnknown(data['flag']!, _flagMeta),
      );
    }
    if (data.containsKey('is_abnormal')) {
      context.handle(
        _isAbnormalMeta,
        isAbnormal.isAcceptableOrUnknown(data['is_abnormal']!, _isAbnormalMeta),
      );
    } else if (isInserting) {
      context.missing(_isAbnormalMeta);
    }
    if (data.containsKey('is_critical')) {
      context.handle(
        _isCriticalMeta,
        isCritical.isAcceptableOrUnknown(data['is_critical']!, _isCriticalMeta),
      );
    } else if (isInserting) {
      context.missing(_isCriticalMeta);
    }
    if (data.containsKey('validated_by')) {
      context.handle(
        _validatedByMeta,
        validatedBy.isAcceptableOrUnknown(
          data['validated_by']!,
          _validatedByMeta,
        ),
      );
    }
    if (data.containsKey('validated_at')) {
      context.handle(
        _validatedAtMeta,
        validatedAt.isAcceptableOrUnknown(
          data['validated_at']!,
          _validatedAtMeta,
        ),
      );
    }
    if (data.containsKey('performed_by')) {
      context.handle(
        _performedByMeta,
        performedBy.isAcceptableOrUnknown(
          data['performed_by']!,
          _performedByMeta,
        ),
      );
    }
    if (data.containsKey('instrument_id')) {
      context.handle(
        _instrumentIdMeta,
        instrumentId.isAcceptableOrUnknown(
          data['instrument_id']!,
          _instrumentIdMeta,
        ),
      );
    }
    if (data.containsKey('notes')) {
      context.handle(
        _notesMeta,
        notes.isAcceptableOrUnknown(data['notes']!, _notesMeta),
      );
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    } else if (isInserting) {
      context.missing(_syncStatusMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Result map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Result(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      labId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}lab_id'],
      )!,
      orderId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}order_id'],
      )!,
      sampleId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sample_id'],
      ),
      patientId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}patient_id'],
      )!,
      testCode: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}test_code'],
      )!,
      testName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}test_name'],
      )!,
      result: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}result'],
      )!,
      unit: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}unit'],
      ),
      referenceRange: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}reference_range'],
      ),
      flag: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}flag'],
      ),
      isAbnormal: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}is_abnormal'],
      )!,
      isCritical: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}is_critical'],
      )!,
      validatedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}validated_by'],
      ),
      validatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}validated_at'],
      ),
      performedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}performed_by'],
      ),
      instrumentId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}instrument_id'],
      ),
      notes: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}notes'],
      ),
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
    );
  }

  @override
  $ResultsTable createAlias(String alias) {
    return $ResultsTable(attachedDatabase, alias);
  }
}

class Result extends DataClass implements Insertable<Result> {
  final String id;
  final String labId;
  final String orderId;
  final String? sampleId;
  final String patientId;
  final String testCode;
  final String testName;
  final String result;
  final String? unit;
  final String? referenceRange;
  final String? flag;
  final int isAbnormal;
  final int isCritical;
  final String? validatedBy;
  final String? validatedAt;
  final String? performedBy;
  final String? instrumentId;
  final String? notes;
  final String status;
  final String createdAt;
  final String updatedAt;
  final String syncStatus;
  const Result({
    required this.id,
    required this.labId,
    required this.orderId,
    this.sampleId,
    required this.patientId,
    required this.testCode,
    required this.testName,
    required this.result,
    this.unit,
    this.referenceRange,
    this.flag,
    required this.isAbnormal,
    required this.isCritical,
    this.validatedBy,
    this.validatedAt,
    this.performedBy,
    this.instrumentId,
    this.notes,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    required this.syncStatus,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['lab_id'] = Variable<String>(labId);
    map['order_id'] = Variable<String>(orderId);
    if (!nullToAbsent || sampleId != null) {
      map['sample_id'] = Variable<String>(sampleId);
    }
    map['patient_id'] = Variable<String>(patientId);
    map['test_code'] = Variable<String>(testCode);
    map['test_name'] = Variable<String>(testName);
    map['result'] = Variable<String>(result);
    if (!nullToAbsent || unit != null) {
      map['unit'] = Variable<String>(unit);
    }
    if (!nullToAbsent || referenceRange != null) {
      map['reference_range'] = Variable<String>(referenceRange);
    }
    if (!nullToAbsent || flag != null) {
      map['flag'] = Variable<String>(flag);
    }
    map['is_abnormal'] = Variable<int>(isAbnormal);
    map['is_critical'] = Variable<int>(isCritical);
    if (!nullToAbsent || validatedBy != null) {
      map['validated_by'] = Variable<String>(validatedBy);
    }
    if (!nullToAbsent || validatedAt != null) {
      map['validated_at'] = Variable<String>(validatedAt);
    }
    if (!nullToAbsent || performedBy != null) {
      map['performed_by'] = Variable<String>(performedBy);
    }
    if (!nullToAbsent || instrumentId != null) {
      map['instrument_id'] = Variable<String>(instrumentId);
    }
    if (!nullToAbsent || notes != null) {
      map['notes'] = Variable<String>(notes);
    }
    map['status'] = Variable<String>(status);
    map['created_at'] = Variable<String>(createdAt);
    map['updated_at'] = Variable<String>(updatedAt);
    map['sync_status'] = Variable<String>(syncStatus);
    return map;
  }

  ResultsCompanion toCompanion(bool nullToAbsent) {
    return ResultsCompanion(
      id: Value(id),
      labId: Value(labId),
      orderId: Value(orderId),
      sampleId: sampleId == null && nullToAbsent
          ? const Value.absent()
          : Value(sampleId),
      patientId: Value(patientId),
      testCode: Value(testCode),
      testName: Value(testName),
      result: Value(result),
      unit: unit == null && nullToAbsent ? const Value.absent() : Value(unit),
      referenceRange: referenceRange == null && nullToAbsent
          ? const Value.absent()
          : Value(referenceRange),
      flag: flag == null && nullToAbsent ? const Value.absent() : Value(flag),
      isAbnormal: Value(isAbnormal),
      isCritical: Value(isCritical),
      validatedBy: validatedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(validatedBy),
      validatedAt: validatedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(validatedAt),
      performedBy: performedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(performedBy),
      instrumentId: instrumentId == null && nullToAbsent
          ? const Value.absent()
          : Value(instrumentId),
      notes: notes == null && nullToAbsent
          ? const Value.absent()
          : Value(notes),
      status: Value(status),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
      syncStatus: Value(syncStatus),
    );
  }

  factory Result.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Result(
      id: serializer.fromJson<String>(json['id']),
      labId: serializer.fromJson<String>(json['labId']),
      orderId: serializer.fromJson<String>(json['orderId']),
      sampleId: serializer.fromJson<String?>(json['sampleId']),
      patientId: serializer.fromJson<String>(json['patientId']),
      testCode: serializer.fromJson<String>(json['testCode']),
      testName: serializer.fromJson<String>(json['testName']),
      result: serializer.fromJson<String>(json['result']),
      unit: serializer.fromJson<String?>(json['unit']),
      referenceRange: serializer.fromJson<String?>(json['referenceRange']),
      flag: serializer.fromJson<String?>(json['flag']),
      isAbnormal: serializer.fromJson<int>(json['isAbnormal']),
      isCritical: serializer.fromJson<int>(json['isCritical']),
      validatedBy: serializer.fromJson<String?>(json['validatedBy']),
      validatedAt: serializer.fromJson<String?>(json['validatedAt']),
      performedBy: serializer.fromJson<String?>(json['performedBy']),
      instrumentId: serializer.fromJson<String?>(json['instrumentId']),
      notes: serializer.fromJson<String?>(json['notes']),
      status: serializer.fromJson<String>(json['status']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'labId': serializer.toJson<String>(labId),
      'orderId': serializer.toJson<String>(orderId),
      'sampleId': serializer.toJson<String?>(sampleId),
      'patientId': serializer.toJson<String>(patientId),
      'testCode': serializer.toJson<String>(testCode),
      'testName': serializer.toJson<String>(testName),
      'result': serializer.toJson<String>(result),
      'unit': serializer.toJson<String?>(unit),
      'referenceRange': serializer.toJson<String?>(referenceRange),
      'flag': serializer.toJson<String?>(flag),
      'isAbnormal': serializer.toJson<int>(isAbnormal),
      'isCritical': serializer.toJson<int>(isCritical),
      'validatedBy': serializer.toJson<String?>(validatedBy),
      'validatedAt': serializer.toJson<String?>(validatedAt),
      'performedBy': serializer.toJson<String?>(performedBy),
      'instrumentId': serializer.toJson<String?>(instrumentId),
      'notes': serializer.toJson<String?>(notes),
      'status': serializer.toJson<String>(status),
      'createdAt': serializer.toJson<String>(createdAt),
      'updatedAt': serializer.toJson<String>(updatedAt),
      'syncStatus': serializer.toJson<String>(syncStatus),
    };
  }

  Result copyWith({
    String? id,
    String? labId,
    String? orderId,
    Value<String?> sampleId = const Value.absent(),
    String? patientId,
    String? testCode,
    String? testName,
    String? result,
    Value<String?> unit = const Value.absent(),
    Value<String?> referenceRange = const Value.absent(),
    Value<String?> flag = const Value.absent(),
    int? isAbnormal,
    int? isCritical,
    Value<String?> validatedBy = const Value.absent(),
    Value<String?> validatedAt = const Value.absent(),
    Value<String?> performedBy = const Value.absent(),
    Value<String?> instrumentId = const Value.absent(),
    Value<String?> notes = const Value.absent(),
    String? status,
    String? createdAt,
    String? updatedAt,
    String? syncStatus,
  }) => Result(
    id: id ?? this.id,
    labId: labId ?? this.labId,
    orderId: orderId ?? this.orderId,
    sampleId: sampleId.present ? sampleId.value : this.sampleId,
    patientId: patientId ?? this.patientId,
    testCode: testCode ?? this.testCode,
    testName: testName ?? this.testName,
    result: result ?? this.result,
    unit: unit.present ? unit.value : this.unit,
    referenceRange: referenceRange.present
        ? referenceRange.value
        : this.referenceRange,
    flag: flag.present ? flag.value : this.flag,
    isAbnormal: isAbnormal ?? this.isAbnormal,
    isCritical: isCritical ?? this.isCritical,
    validatedBy: validatedBy.present ? validatedBy.value : this.validatedBy,
    validatedAt: validatedAt.present ? validatedAt.value : this.validatedAt,
    performedBy: performedBy.present ? performedBy.value : this.performedBy,
    instrumentId: instrumentId.present ? instrumentId.value : this.instrumentId,
    notes: notes.present ? notes.value : this.notes,
    status: status ?? this.status,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
    syncStatus: syncStatus ?? this.syncStatus,
  );
  Result copyWithCompanion(ResultsCompanion data) {
    return Result(
      id: data.id.present ? data.id.value : this.id,
      labId: data.labId.present ? data.labId.value : this.labId,
      orderId: data.orderId.present ? data.orderId.value : this.orderId,
      sampleId: data.sampleId.present ? data.sampleId.value : this.sampleId,
      patientId: data.patientId.present ? data.patientId.value : this.patientId,
      testCode: data.testCode.present ? data.testCode.value : this.testCode,
      testName: data.testName.present ? data.testName.value : this.testName,
      result: data.result.present ? data.result.value : this.result,
      unit: data.unit.present ? data.unit.value : this.unit,
      referenceRange: data.referenceRange.present
          ? data.referenceRange.value
          : this.referenceRange,
      flag: data.flag.present ? data.flag.value : this.flag,
      isAbnormal: data.isAbnormal.present
          ? data.isAbnormal.value
          : this.isAbnormal,
      isCritical: data.isCritical.present
          ? data.isCritical.value
          : this.isCritical,
      validatedBy: data.validatedBy.present
          ? data.validatedBy.value
          : this.validatedBy,
      validatedAt: data.validatedAt.present
          ? data.validatedAt.value
          : this.validatedAt,
      performedBy: data.performedBy.present
          ? data.performedBy.value
          : this.performedBy,
      instrumentId: data.instrumentId.present
          ? data.instrumentId.value
          : this.instrumentId,
      notes: data.notes.present ? data.notes.value : this.notes,
      status: data.status.present ? data.status.value : this.status,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Result(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('orderId: $orderId, ')
          ..write('sampleId: $sampleId, ')
          ..write('patientId: $patientId, ')
          ..write('testCode: $testCode, ')
          ..write('testName: $testName, ')
          ..write('result: $result, ')
          ..write('unit: $unit, ')
          ..write('referenceRange: $referenceRange, ')
          ..write('flag: $flag, ')
          ..write('isAbnormal: $isAbnormal, ')
          ..write('isCritical: $isCritical, ')
          ..write('validatedBy: $validatedBy, ')
          ..write('validatedAt: $validatedAt, ')
          ..write('performedBy: $performedBy, ')
          ..write('instrumentId: $instrumentId, ')
          ..write('notes: $notes, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('syncStatus: $syncStatus')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
    id,
    labId,
    orderId,
    sampleId,
    patientId,
    testCode,
    testName,
    result,
    unit,
    referenceRange,
    flag,
    isAbnormal,
    isCritical,
    validatedBy,
    validatedAt,
    performedBy,
    instrumentId,
    notes,
    status,
    createdAt,
    updatedAt,
    syncStatus,
  ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Result &&
          other.id == this.id &&
          other.labId == this.labId &&
          other.orderId == this.orderId &&
          other.sampleId == this.sampleId &&
          other.patientId == this.patientId &&
          other.testCode == this.testCode &&
          other.testName == this.testName &&
          other.result == this.result &&
          other.unit == this.unit &&
          other.referenceRange == this.referenceRange &&
          other.flag == this.flag &&
          other.isAbnormal == this.isAbnormal &&
          other.isCritical == this.isCritical &&
          other.validatedBy == this.validatedBy &&
          other.validatedAt == this.validatedAt &&
          other.performedBy == this.performedBy &&
          other.instrumentId == this.instrumentId &&
          other.notes == this.notes &&
          other.status == this.status &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt &&
          other.syncStatus == this.syncStatus);
}

class ResultsCompanion extends UpdateCompanion<Result> {
  final Value<String> id;
  final Value<String> labId;
  final Value<String> orderId;
  final Value<String?> sampleId;
  final Value<String> patientId;
  final Value<String> testCode;
  final Value<String> testName;
  final Value<String> result;
  final Value<String?> unit;
  final Value<String?> referenceRange;
  final Value<String?> flag;
  final Value<int> isAbnormal;
  final Value<int> isCritical;
  final Value<String?> validatedBy;
  final Value<String?> validatedAt;
  final Value<String?> performedBy;
  final Value<String?> instrumentId;
  final Value<String?> notes;
  final Value<String> status;
  final Value<String> createdAt;
  final Value<String> updatedAt;
  final Value<String> syncStatus;
  final Value<int> rowid;
  const ResultsCompanion({
    this.id = const Value.absent(),
    this.labId = const Value.absent(),
    this.orderId = const Value.absent(),
    this.sampleId = const Value.absent(),
    this.patientId = const Value.absent(),
    this.testCode = const Value.absent(),
    this.testName = const Value.absent(),
    this.result = const Value.absent(),
    this.unit = const Value.absent(),
    this.referenceRange = const Value.absent(),
    this.flag = const Value.absent(),
    this.isAbnormal = const Value.absent(),
    this.isCritical = const Value.absent(),
    this.validatedBy = const Value.absent(),
    this.validatedAt = const Value.absent(),
    this.performedBy = const Value.absent(),
    this.instrumentId = const Value.absent(),
    this.notes = const Value.absent(),
    this.status = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ResultsCompanion.insert({
    required String id,
    required String labId,
    required String orderId,
    this.sampleId = const Value.absent(),
    required String patientId,
    required String testCode,
    required String testName,
    required String result,
    this.unit = const Value.absent(),
    this.referenceRange = const Value.absent(),
    this.flag = const Value.absent(),
    required int isAbnormal,
    required int isCritical,
    this.validatedBy = const Value.absent(),
    this.validatedAt = const Value.absent(),
    this.performedBy = const Value.absent(),
    this.instrumentId = const Value.absent(),
    this.notes = const Value.absent(),
    required String status,
    required String createdAt,
    required String updatedAt,
    required String syncStatus,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       labId = Value(labId),
       orderId = Value(orderId),
       patientId = Value(patientId),
       testCode = Value(testCode),
       testName = Value(testName),
       result = Value(result),
       isAbnormal = Value(isAbnormal),
       isCritical = Value(isCritical),
       status = Value(status),
       createdAt = Value(createdAt),
       updatedAt = Value(updatedAt),
       syncStatus = Value(syncStatus);
  static Insertable<Result> custom({
    Expression<String>? id,
    Expression<String>? labId,
    Expression<String>? orderId,
    Expression<String>? sampleId,
    Expression<String>? patientId,
    Expression<String>? testCode,
    Expression<String>? testName,
    Expression<String>? result,
    Expression<String>? unit,
    Expression<String>? referenceRange,
    Expression<String>? flag,
    Expression<int>? isAbnormal,
    Expression<int>? isCritical,
    Expression<String>? validatedBy,
    Expression<String>? validatedAt,
    Expression<String>? performedBy,
    Expression<String>? instrumentId,
    Expression<String>? notes,
    Expression<String>? status,
    Expression<String>? createdAt,
    Expression<String>? updatedAt,
    Expression<String>? syncStatus,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (labId != null) 'lab_id': labId,
      if (orderId != null) 'order_id': orderId,
      if (sampleId != null) 'sample_id': sampleId,
      if (patientId != null) 'patient_id': patientId,
      if (testCode != null) 'test_code': testCode,
      if (testName != null) 'test_name': testName,
      if (result != null) 'result': result,
      if (unit != null) 'unit': unit,
      if (referenceRange != null) 'reference_range': referenceRange,
      if (flag != null) 'flag': flag,
      if (isAbnormal != null) 'is_abnormal': isAbnormal,
      if (isCritical != null) 'is_critical': isCritical,
      if (validatedBy != null) 'validated_by': validatedBy,
      if (validatedAt != null) 'validated_at': validatedAt,
      if (performedBy != null) 'performed_by': performedBy,
      if (instrumentId != null) 'instrument_id': instrumentId,
      if (notes != null) 'notes': notes,
      if (status != null) 'status': status,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ResultsCompanion copyWith({
    Value<String>? id,
    Value<String>? labId,
    Value<String>? orderId,
    Value<String?>? sampleId,
    Value<String>? patientId,
    Value<String>? testCode,
    Value<String>? testName,
    Value<String>? result,
    Value<String?>? unit,
    Value<String?>? referenceRange,
    Value<String?>? flag,
    Value<int>? isAbnormal,
    Value<int>? isCritical,
    Value<String?>? validatedBy,
    Value<String?>? validatedAt,
    Value<String?>? performedBy,
    Value<String?>? instrumentId,
    Value<String?>? notes,
    Value<String>? status,
    Value<String>? createdAt,
    Value<String>? updatedAt,
    Value<String>? syncStatus,
    Value<int>? rowid,
  }) {
    return ResultsCompanion(
      id: id ?? this.id,
      labId: labId ?? this.labId,
      orderId: orderId ?? this.orderId,
      sampleId: sampleId ?? this.sampleId,
      patientId: patientId ?? this.patientId,
      testCode: testCode ?? this.testCode,
      testName: testName ?? this.testName,
      result: result ?? this.result,
      unit: unit ?? this.unit,
      referenceRange: referenceRange ?? this.referenceRange,
      flag: flag ?? this.flag,
      isAbnormal: isAbnormal ?? this.isAbnormal,
      isCritical: isCritical ?? this.isCritical,
      validatedBy: validatedBy ?? this.validatedBy,
      validatedAt: validatedAt ?? this.validatedAt,
      performedBy: performedBy ?? this.performedBy,
      instrumentId: instrumentId ?? this.instrumentId,
      notes: notes ?? this.notes,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      syncStatus: syncStatus ?? this.syncStatus,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (labId.present) {
      map['lab_id'] = Variable<String>(labId.value);
    }
    if (orderId.present) {
      map['order_id'] = Variable<String>(orderId.value);
    }
    if (sampleId.present) {
      map['sample_id'] = Variable<String>(sampleId.value);
    }
    if (patientId.present) {
      map['patient_id'] = Variable<String>(patientId.value);
    }
    if (testCode.present) {
      map['test_code'] = Variable<String>(testCode.value);
    }
    if (testName.present) {
      map['test_name'] = Variable<String>(testName.value);
    }
    if (result.present) {
      map['result'] = Variable<String>(result.value);
    }
    if (unit.present) {
      map['unit'] = Variable<String>(unit.value);
    }
    if (referenceRange.present) {
      map['reference_range'] = Variable<String>(referenceRange.value);
    }
    if (flag.present) {
      map['flag'] = Variable<String>(flag.value);
    }
    if (isAbnormal.present) {
      map['is_abnormal'] = Variable<int>(isAbnormal.value);
    }
    if (isCritical.present) {
      map['is_critical'] = Variable<int>(isCritical.value);
    }
    if (validatedBy.present) {
      map['validated_by'] = Variable<String>(validatedBy.value);
    }
    if (validatedAt.present) {
      map['validated_at'] = Variable<String>(validatedAt.value);
    }
    if (performedBy.present) {
      map['performed_by'] = Variable<String>(performedBy.value);
    }
    if (instrumentId.present) {
      map['instrument_id'] = Variable<String>(instrumentId.value);
    }
    if (notes.present) {
      map['notes'] = Variable<String>(notes.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ResultsCompanion(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('orderId: $orderId, ')
          ..write('sampleId: $sampleId, ')
          ..write('patientId: $patientId, ')
          ..write('testCode: $testCode, ')
          ..write('testName: $testName, ')
          ..write('result: $result, ')
          ..write('unit: $unit, ')
          ..write('referenceRange: $referenceRange, ')
          ..write('flag: $flag, ')
          ..write('isAbnormal: $isAbnormal, ')
          ..write('isCritical: $isCritical, ')
          ..write('validatedBy: $validatedBy, ')
          ..write('validatedAt: $validatedAt, ')
          ..write('performedBy: $performedBy, ')
          ..write('instrumentId: $instrumentId, ')
          ..write('notes: $notes, ')
          ..write('status: $status, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $NotificationsTable extends Notifications
    with TableInfo<$NotificationsTable, Notification> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $NotificationsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _labIdMeta = const VerificationMeta('labId');
  @override
  late final GeneratedColumn<String> labId = GeneratedColumn<String>(
    'lab_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
    'title',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _bodyMeta = const VerificationMeta('body');
  @override
  late final GeneratedColumn<String> body = GeneratedColumn<String>(
    'body',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _typeMeta = const VerificationMeta('type');
  @override
  late final GeneratedColumn<String> type = GeneratedColumn<String>(
    'type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _severityMeta = const VerificationMeta(
    'severity',
  );
  @override
  late final GeneratedColumn<String> severity = GeneratedColumn<String>(
    'severity',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _entityTypeMeta = const VerificationMeta(
    'entityType',
  );
  @override
  late final GeneratedColumn<String> entityType = GeneratedColumn<String>(
    'entity_type',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _entityIdMeta = const VerificationMeta(
    'entityId',
  );
  @override
  late final GeneratedColumn<String> entityId = GeneratedColumn<String>(
    'entity_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _isReadMeta = const VerificationMeta('isRead');
  @override
  late final GeneratedColumn<int> isRead = GeneratedColumn<int>(
    'is_read',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _isActionedMeta = const VerificationMeta(
    'isActioned',
  );
  @override
  late final GeneratedColumn<int> isActioned = GeneratedColumn<int>(
    'is_actioned',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    labId,
    title,
    body,
    type,
    severity,
    entityType,
    entityId,
    isRead,
    isActioned,
    createdAt,
    syncStatus,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'notifications';
  @override
  VerificationContext validateIntegrity(
    Insertable<Notification> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('lab_id')) {
      context.handle(
        _labIdMeta,
        labId.isAcceptableOrUnknown(data['lab_id']!, _labIdMeta),
      );
    }
    if (data.containsKey('title')) {
      context.handle(
        _titleMeta,
        title.isAcceptableOrUnknown(data['title']!, _titleMeta),
      );
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('body')) {
      context.handle(
        _bodyMeta,
        body.isAcceptableOrUnknown(data['body']!, _bodyMeta),
      );
    } else if (isInserting) {
      context.missing(_bodyMeta);
    }
    if (data.containsKey('type')) {
      context.handle(
        _typeMeta,
        type.isAcceptableOrUnknown(data['type']!, _typeMeta),
      );
    } else if (isInserting) {
      context.missing(_typeMeta);
    }
    if (data.containsKey('severity')) {
      context.handle(
        _severityMeta,
        severity.isAcceptableOrUnknown(data['severity']!, _severityMeta),
      );
    } else if (isInserting) {
      context.missing(_severityMeta);
    }
    if (data.containsKey('entity_type')) {
      context.handle(
        _entityTypeMeta,
        entityType.isAcceptableOrUnknown(data['entity_type']!, _entityTypeMeta),
      );
    }
    if (data.containsKey('entity_id')) {
      context.handle(
        _entityIdMeta,
        entityId.isAcceptableOrUnknown(data['entity_id']!, _entityIdMeta),
      );
    }
    if (data.containsKey('is_read')) {
      context.handle(
        _isReadMeta,
        isRead.isAcceptableOrUnknown(data['is_read']!, _isReadMeta),
      );
    } else if (isInserting) {
      context.missing(_isReadMeta);
    }
    if (data.containsKey('is_actioned')) {
      context.handle(
        _isActionedMeta,
        isActioned.isAcceptableOrUnknown(data['is_actioned']!, _isActionedMeta),
      );
    } else if (isInserting) {
      context.missing(_isActionedMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    } else if (isInserting) {
      context.missing(_syncStatusMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Notification map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Notification(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      labId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}lab_id'],
      ),
      title: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title'],
      )!,
      body: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}body'],
      )!,
      type: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}type'],
      )!,
      severity: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}severity'],
      )!,
      entityType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_type'],
      ),
      entityId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_id'],
      ),
      isRead: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}is_read'],
      )!,
      isActioned: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}is_actioned'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
    );
  }

  @override
  $NotificationsTable createAlias(String alias) {
    return $NotificationsTable(attachedDatabase, alias);
  }
}

class Notification extends DataClass implements Insertable<Notification> {
  final String id;
  final String? labId;
  final String title;
  final String body;
  final String type;
  final String severity;
  final String? entityType;
  final String? entityId;
  final int isRead;
  final int isActioned;
  final String createdAt;
  final String syncStatus;
  const Notification({
    required this.id,
    this.labId,
    required this.title,
    required this.body,
    required this.type,
    required this.severity,
    this.entityType,
    this.entityId,
    required this.isRead,
    required this.isActioned,
    required this.createdAt,
    required this.syncStatus,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    if (!nullToAbsent || labId != null) {
      map['lab_id'] = Variable<String>(labId);
    }
    map['title'] = Variable<String>(title);
    map['body'] = Variable<String>(body);
    map['type'] = Variable<String>(type);
    map['severity'] = Variable<String>(severity);
    if (!nullToAbsent || entityType != null) {
      map['entity_type'] = Variable<String>(entityType);
    }
    if (!nullToAbsent || entityId != null) {
      map['entity_id'] = Variable<String>(entityId);
    }
    map['is_read'] = Variable<int>(isRead);
    map['is_actioned'] = Variable<int>(isActioned);
    map['created_at'] = Variable<String>(createdAt);
    map['sync_status'] = Variable<String>(syncStatus);
    return map;
  }

  NotificationsCompanion toCompanion(bool nullToAbsent) {
    return NotificationsCompanion(
      id: Value(id),
      labId: labId == null && nullToAbsent
          ? const Value.absent()
          : Value(labId),
      title: Value(title),
      body: Value(body),
      type: Value(type),
      severity: Value(severity),
      entityType: entityType == null && nullToAbsent
          ? const Value.absent()
          : Value(entityType),
      entityId: entityId == null && nullToAbsent
          ? const Value.absent()
          : Value(entityId),
      isRead: Value(isRead),
      isActioned: Value(isActioned),
      createdAt: Value(createdAt),
      syncStatus: Value(syncStatus),
    );
  }

  factory Notification.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Notification(
      id: serializer.fromJson<String>(json['id']),
      labId: serializer.fromJson<String?>(json['labId']),
      title: serializer.fromJson<String>(json['title']),
      body: serializer.fromJson<String>(json['body']),
      type: serializer.fromJson<String>(json['type']),
      severity: serializer.fromJson<String>(json['severity']),
      entityType: serializer.fromJson<String?>(json['entityType']),
      entityId: serializer.fromJson<String?>(json['entityId']),
      isRead: serializer.fromJson<int>(json['isRead']),
      isActioned: serializer.fromJson<int>(json['isActioned']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'labId': serializer.toJson<String?>(labId),
      'title': serializer.toJson<String>(title),
      'body': serializer.toJson<String>(body),
      'type': serializer.toJson<String>(type),
      'severity': serializer.toJson<String>(severity),
      'entityType': serializer.toJson<String?>(entityType),
      'entityId': serializer.toJson<String?>(entityId),
      'isRead': serializer.toJson<int>(isRead),
      'isActioned': serializer.toJson<int>(isActioned),
      'createdAt': serializer.toJson<String>(createdAt),
      'syncStatus': serializer.toJson<String>(syncStatus),
    };
  }

  Notification copyWith({
    String? id,
    Value<String?> labId = const Value.absent(),
    String? title,
    String? body,
    String? type,
    String? severity,
    Value<String?> entityType = const Value.absent(),
    Value<String?> entityId = const Value.absent(),
    int? isRead,
    int? isActioned,
    String? createdAt,
    String? syncStatus,
  }) => Notification(
    id: id ?? this.id,
    labId: labId.present ? labId.value : this.labId,
    title: title ?? this.title,
    body: body ?? this.body,
    type: type ?? this.type,
    severity: severity ?? this.severity,
    entityType: entityType.present ? entityType.value : this.entityType,
    entityId: entityId.present ? entityId.value : this.entityId,
    isRead: isRead ?? this.isRead,
    isActioned: isActioned ?? this.isActioned,
    createdAt: createdAt ?? this.createdAt,
    syncStatus: syncStatus ?? this.syncStatus,
  );
  Notification copyWithCompanion(NotificationsCompanion data) {
    return Notification(
      id: data.id.present ? data.id.value : this.id,
      labId: data.labId.present ? data.labId.value : this.labId,
      title: data.title.present ? data.title.value : this.title,
      body: data.body.present ? data.body.value : this.body,
      type: data.type.present ? data.type.value : this.type,
      severity: data.severity.present ? data.severity.value : this.severity,
      entityType: data.entityType.present
          ? data.entityType.value
          : this.entityType,
      entityId: data.entityId.present ? data.entityId.value : this.entityId,
      isRead: data.isRead.present ? data.isRead.value : this.isRead,
      isActioned: data.isActioned.present
          ? data.isActioned.value
          : this.isActioned,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Notification(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('title: $title, ')
          ..write('body: $body, ')
          ..write('type: $type, ')
          ..write('severity: $severity, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('isRead: $isRead, ')
          ..write('isActioned: $isActioned, ')
          ..write('createdAt: $createdAt, ')
          ..write('syncStatus: $syncStatus')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    labId,
    title,
    body,
    type,
    severity,
    entityType,
    entityId,
    isRead,
    isActioned,
    createdAt,
    syncStatus,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Notification &&
          other.id == this.id &&
          other.labId == this.labId &&
          other.title == this.title &&
          other.body == this.body &&
          other.type == this.type &&
          other.severity == this.severity &&
          other.entityType == this.entityType &&
          other.entityId == this.entityId &&
          other.isRead == this.isRead &&
          other.isActioned == this.isActioned &&
          other.createdAt == this.createdAt &&
          other.syncStatus == this.syncStatus);
}

class NotificationsCompanion extends UpdateCompanion<Notification> {
  final Value<String> id;
  final Value<String?> labId;
  final Value<String> title;
  final Value<String> body;
  final Value<String> type;
  final Value<String> severity;
  final Value<String?> entityType;
  final Value<String?> entityId;
  final Value<int> isRead;
  final Value<int> isActioned;
  final Value<String> createdAt;
  final Value<String> syncStatus;
  final Value<int> rowid;
  const NotificationsCompanion({
    this.id = const Value.absent(),
    this.labId = const Value.absent(),
    this.title = const Value.absent(),
    this.body = const Value.absent(),
    this.type = const Value.absent(),
    this.severity = const Value.absent(),
    this.entityType = const Value.absent(),
    this.entityId = const Value.absent(),
    this.isRead = const Value.absent(),
    this.isActioned = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  NotificationsCompanion.insert({
    required String id,
    this.labId = const Value.absent(),
    required String title,
    required String body,
    required String type,
    required String severity,
    this.entityType = const Value.absent(),
    this.entityId = const Value.absent(),
    required int isRead,
    required int isActioned,
    required String createdAt,
    required String syncStatus,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       title = Value(title),
       body = Value(body),
       type = Value(type),
       severity = Value(severity),
       isRead = Value(isRead),
       isActioned = Value(isActioned),
       createdAt = Value(createdAt),
       syncStatus = Value(syncStatus);
  static Insertable<Notification> custom({
    Expression<String>? id,
    Expression<String>? labId,
    Expression<String>? title,
    Expression<String>? body,
    Expression<String>? type,
    Expression<String>? severity,
    Expression<String>? entityType,
    Expression<String>? entityId,
    Expression<int>? isRead,
    Expression<int>? isActioned,
    Expression<String>? createdAt,
    Expression<String>? syncStatus,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (labId != null) 'lab_id': labId,
      if (title != null) 'title': title,
      if (body != null) 'body': body,
      if (type != null) 'type': type,
      if (severity != null) 'severity': severity,
      if (entityType != null) 'entity_type': entityType,
      if (entityId != null) 'entity_id': entityId,
      if (isRead != null) 'is_read': isRead,
      if (isActioned != null) 'is_actioned': isActioned,
      if (createdAt != null) 'created_at': createdAt,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (rowid != null) 'rowid': rowid,
    });
  }

  NotificationsCompanion copyWith({
    Value<String>? id,
    Value<String?>? labId,
    Value<String>? title,
    Value<String>? body,
    Value<String>? type,
    Value<String>? severity,
    Value<String?>? entityType,
    Value<String?>? entityId,
    Value<int>? isRead,
    Value<int>? isActioned,
    Value<String>? createdAt,
    Value<String>? syncStatus,
    Value<int>? rowid,
  }) {
    return NotificationsCompanion(
      id: id ?? this.id,
      labId: labId ?? this.labId,
      title: title ?? this.title,
      body: body ?? this.body,
      type: type ?? this.type,
      severity: severity ?? this.severity,
      entityType: entityType ?? this.entityType,
      entityId: entityId ?? this.entityId,
      isRead: isRead ?? this.isRead,
      isActioned: isActioned ?? this.isActioned,
      createdAt: createdAt ?? this.createdAt,
      syncStatus: syncStatus ?? this.syncStatus,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (labId.present) {
      map['lab_id'] = Variable<String>(labId.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (body.present) {
      map['body'] = Variable<String>(body.value);
    }
    if (type.present) {
      map['type'] = Variable<String>(type.value);
    }
    if (severity.present) {
      map['severity'] = Variable<String>(severity.value);
    }
    if (entityType.present) {
      map['entity_type'] = Variable<String>(entityType.value);
    }
    if (entityId.present) {
      map['entity_id'] = Variable<String>(entityId.value);
    }
    if (isRead.present) {
      map['is_read'] = Variable<int>(isRead.value);
    }
    if (isActioned.present) {
      map['is_actioned'] = Variable<int>(isActioned.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('NotificationsCompanion(')
          ..write('id: $id, ')
          ..write('labId: $labId, ')
          ..write('title: $title, ')
          ..write('body: $body, ')
          ..write('type: $type, ')
          ..write('severity: $severity, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('isRead: $isRead, ')
          ..write('isActioned: $isActioned, ')
          ..write('createdAt: $createdAt, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncQueueTable extends SyncQueue
    with TableInfo<$SyncQueueTable, SyncQueueData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncQueueTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _entityTypeMeta = const VerificationMeta(
    'entityType',
  );
  @override
  late final GeneratedColumn<String> entityType = GeneratedColumn<String>(
    'entity_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _entityIdMeta = const VerificationMeta(
    'entityId',
  );
  @override
  late final GeneratedColumn<String> entityId = GeneratedColumn<String>(
    'entity_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _operationMeta = const VerificationMeta(
    'operation',
  );
  @override
  late final GeneratedColumn<String> operation = GeneratedColumn<String>(
    'operation',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _payloadMeta = const VerificationMeta(
    'payload',
  );
  @override
  late final GeneratedColumn<String> payload = GeneratedColumn<String>(
    'payload',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _retryCountMeta = const VerificationMeta(
    'retryCount',
  );
  @override
  late final GeneratedColumn<int> retryCount = GeneratedColumn<int>(
    'retry_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _maxRetriesMeta = const VerificationMeta(
    'maxRetries',
  );
  @override
  late final GeneratedColumn<int> maxRetries = GeneratedColumn<int>(
    'max_retries',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<String> updatedAt = GeneratedColumn<String>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    entityType,
    entityId,
    operation,
    payload,
    status,
    retryCount,
    maxRetries,
    createdAt,
    updatedAt,
    lastError,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_queue';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncQueueData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('entity_type')) {
      context.handle(
        _entityTypeMeta,
        entityType.isAcceptableOrUnknown(data['entity_type']!, _entityTypeMeta),
      );
    } else if (isInserting) {
      context.missing(_entityTypeMeta);
    }
    if (data.containsKey('entity_id')) {
      context.handle(
        _entityIdMeta,
        entityId.isAcceptableOrUnknown(data['entity_id']!, _entityIdMeta),
      );
    } else if (isInserting) {
      context.missing(_entityIdMeta);
    }
    if (data.containsKey('operation')) {
      context.handle(
        _operationMeta,
        operation.isAcceptableOrUnknown(data['operation']!, _operationMeta),
      );
    } else if (isInserting) {
      context.missing(_operationMeta);
    }
    if (data.containsKey('payload')) {
      context.handle(
        _payloadMeta,
        payload.isAcceptableOrUnknown(data['payload']!, _payloadMeta),
      );
    } else if (isInserting) {
      context.missing(_payloadMeta);
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    } else if (isInserting) {
      context.missing(_statusMeta);
    }
    if (data.containsKey('retry_count')) {
      context.handle(
        _retryCountMeta,
        retryCount.isAcceptableOrUnknown(data['retry_count']!, _retryCountMeta),
      );
    } else if (isInserting) {
      context.missing(_retryCountMeta);
    }
    if (data.containsKey('max_retries')) {
      context.handle(
        _maxRetriesMeta,
        maxRetries.isAcceptableOrUnknown(data['max_retries']!, _maxRetriesMeta),
      );
    } else if (isInserting) {
      context.missing(_maxRetriesMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  SyncQueueData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncQueueData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      entityType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_type'],
      )!,
      entityId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_id'],
      )!,
      operation: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}operation'],
      )!,
      payload: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}payload'],
      )!,
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      retryCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}retry_count'],
      )!,
      maxRetries: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}max_retries'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}updated_at'],
      )!,
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
    );
  }

  @override
  $SyncQueueTable createAlias(String alias) {
    return $SyncQueueTable(attachedDatabase, alias);
  }
}

class SyncQueueData extends DataClass implements Insertable<SyncQueueData> {
  final int id;
  final String entityType;
  final String entityId;
  final String operation;
  final String payload;
  final String status;
  final int retryCount;
  final int maxRetries;
  final String createdAt;
  final String updatedAt;
  final String? lastError;
  const SyncQueueData({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.operation,
    required this.payload,
    required this.status,
    required this.retryCount,
    required this.maxRetries,
    required this.createdAt,
    required this.updatedAt,
    this.lastError,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['entity_type'] = Variable<String>(entityType);
    map['entity_id'] = Variable<String>(entityId);
    map['operation'] = Variable<String>(operation);
    map['payload'] = Variable<String>(payload);
    map['status'] = Variable<String>(status);
    map['retry_count'] = Variable<int>(retryCount);
    map['max_retries'] = Variable<int>(maxRetries);
    map['created_at'] = Variable<String>(createdAt);
    map['updated_at'] = Variable<String>(updatedAt);
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    return map;
  }

  SyncQueueCompanion toCompanion(bool nullToAbsent) {
    return SyncQueueCompanion(
      id: Value(id),
      entityType: Value(entityType),
      entityId: Value(entityId),
      operation: Value(operation),
      payload: Value(payload),
      status: Value(status),
      retryCount: Value(retryCount),
      maxRetries: Value(maxRetries),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
    );
  }

  factory SyncQueueData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncQueueData(
      id: serializer.fromJson<int>(json['id']),
      entityType: serializer.fromJson<String>(json['entityType']),
      entityId: serializer.fromJson<String>(json['entityId']),
      operation: serializer.fromJson<String>(json['operation']),
      payload: serializer.fromJson<String>(json['payload']),
      status: serializer.fromJson<String>(json['status']),
      retryCount: serializer.fromJson<int>(json['retryCount']),
      maxRetries: serializer.fromJson<int>(json['maxRetries']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
      updatedAt: serializer.fromJson<String>(json['updatedAt']),
      lastError: serializer.fromJson<String?>(json['lastError']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'entityType': serializer.toJson<String>(entityType),
      'entityId': serializer.toJson<String>(entityId),
      'operation': serializer.toJson<String>(operation),
      'payload': serializer.toJson<String>(payload),
      'status': serializer.toJson<String>(status),
      'retryCount': serializer.toJson<int>(retryCount),
      'maxRetries': serializer.toJson<int>(maxRetries),
      'createdAt': serializer.toJson<String>(createdAt),
      'updatedAt': serializer.toJson<String>(updatedAt),
      'lastError': serializer.toJson<String?>(lastError),
    };
  }

  SyncQueueData copyWith({
    int? id,
    String? entityType,
    String? entityId,
    String? operation,
    String? payload,
    String? status,
    int? retryCount,
    int? maxRetries,
    String? createdAt,
    String? updatedAt,
    Value<String?> lastError = const Value.absent(),
  }) => SyncQueueData(
    id: id ?? this.id,
    entityType: entityType ?? this.entityType,
    entityId: entityId ?? this.entityId,
    operation: operation ?? this.operation,
    payload: payload ?? this.payload,
    status: status ?? this.status,
    retryCount: retryCount ?? this.retryCount,
    maxRetries: maxRetries ?? this.maxRetries,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
    lastError: lastError.present ? lastError.value : this.lastError,
  );
  SyncQueueData copyWithCompanion(SyncQueueCompanion data) {
    return SyncQueueData(
      id: data.id.present ? data.id.value : this.id,
      entityType: data.entityType.present
          ? data.entityType.value
          : this.entityType,
      entityId: data.entityId.present ? data.entityId.value : this.entityId,
      operation: data.operation.present ? data.operation.value : this.operation,
      payload: data.payload.present ? data.payload.value : this.payload,
      status: data.status.present ? data.status.value : this.status,
      retryCount: data.retryCount.present
          ? data.retryCount.value
          : this.retryCount,
      maxRetries: data.maxRetries.present
          ? data.maxRetries.value
          : this.maxRetries,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncQueueData(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('operation: $operation, ')
          ..write('payload: $payload, ')
          ..write('status: $status, ')
          ..write('retryCount: $retryCount, ')
          ..write('maxRetries: $maxRetries, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    entityType,
    entityId,
    operation,
    payload,
    status,
    retryCount,
    maxRetries,
    createdAt,
    updatedAt,
    lastError,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncQueueData &&
          other.id == this.id &&
          other.entityType == this.entityType &&
          other.entityId == this.entityId &&
          other.operation == this.operation &&
          other.payload == this.payload &&
          other.status == this.status &&
          other.retryCount == this.retryCount &&
          other.maxRetries == this.maxRetries &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt &&
          other.lastError == this.lastError);
}

class SyncQueueCompanion extends UpdateCompanion<SyncQueueData> {
  final Value<int> id;
  final Value<String> entityType;
  final Value<String> entityId;
  final Value<String> operation;
  final Value<String> payload;
  final Value<String> status;
  final Value<int> retryCount;
  final Value<int> maxRetries;
  final Value<String> createdAt;
  final Value<String> updatedAt;
  final Value<String?> lastError;
  const SyncQueueCompanion({
    this.id = const Value.absent(),
    this.entityType = const Value.absent(),
    this.entityId = const Value.absent(),
    this.operation = const Value.absent(),
    this.payload = const Value.absent(),
    this.status = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.maxRetries = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.lastError = const Value.absent(),
  });
  SyncQueueCompanion.insert({
    this.id = const Value.absent(),
    required String entityType,
    required String entityId,
    required String operation,
    required String payload,
    required String status,
    required int retryCount,
    required int maxRetries,
    required String createdAt,
    required String updatedAt,
    this.lastError = const Value.absent(),
  }) : entityType = Value(entityType),
       entityId = Value(entityId),
       operation = Value(operation),
       payload = Value(payload),
       status = Value(status),
       retryCount = Value(retryCount),
       maxRetries = Value(maxRetries),
       createdAt = Value(createdAt),
       updatedAt = Value(updatedAt);
  static Insertable<SyncQueueData> custom({
    Expression<int>? id,
    Expression<String>? entityType,
    Expression<String>? entityId,
    Expression<String>? operation,
    Expression<String>? payload,
    Expression<String>? status,
    Expression<int>? retryCount,
    Expression<int>? maxRetries,
    Expression<String>? createdAt,
    Expression<String>? updatedAt,
    Expression<String>? lastError,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (entityType != null) 'entity_type': entityType,
      if (entityId != null) 'entity_id': entityId,
      if (operation != null) 'operation': operation,
      if (payload != null) 'payload': payload,
      if (status != null) 'status': status,
      if (retryCount != null) 'retry_count': retryCount,
      if (maxRetries != null) 'max_retries': maxRetries,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (lastError != null) 'last_error': lastError,
    });
  }

  SyncQueueCompanion copyWith({
    Value<int>? id,
    Value<String>? entityType,
    Value<String>? entityId,
    Value<String>? operation,
    Value<String>? payload,
    Value<String>? status,
    Value<int>? retryCount,
    Value<int>? maxRetries,
    Value<String>? createdAt,
    Value<String>? updatedAt,
    Value<String?>? lastError,
  }) {
    return SyncQueueCompanion(
      id: id ?? this.id,
      entityType: entityType ?? this.entityType,
      entityId: entityId ?? this.entityId,
      operation: operation ?? this.operation,
      payload: payload ?? this.payload,
      status: status ?? this.status,
      retryCount: retryCount ?? this.retryCount,
      maxRetries: maxRetries ?? this.maxRetries,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      lastError: lastError ?? this.lastError,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (entityType.present) {
      map['entity_type'] = Variable<String>(entityType.value);
    }
    if (entityId.present) {
      map['entity_id'] = Variable<String>(entityId.value);
    }
    if (operation.present) {
      map['operation'] = Variable<String>(operation.value);
    }
    if (payload.present) {
      map['payload'] = Variable<String>(payload.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (retryCount.present) {
      map['retry_count'] = Variable<int>(retryCount.value);
    }
    if (maxRetries.present) {
      map['max_retries'] = Variable<int>(maxRetries.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<String>(updatedAt.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncQueueCompanion(')
          ..write('id: $id, ')
          ..write('entityType: $entityType, ')
          ..write('entityId: $entityId, ')
          ..write('operation: $operation, ')
          ..write('payload: $payload, ')
          ..write('status: $status, ')
          ..write('retryCount: $retryCount, ')
          ..write('maxRetries: $maxRetries, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }
}

class $CacheEntriesTable extends CacheEntries
    with TableInfo<$CacheEntriesTable, CacheEntry> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $CacheEntriesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _keyMeta = const VerificationMeta('key');
  @override
  late final GeneratedColumn<String> key = GeneratedColumn<String>(
    'key',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _valueMeta = const VerificationMeta('value');
  @override
  late final GeneratedColumn<String> value = GeneratedColumn<String>(
    'value',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _expiresAtMeta = const VerificationMeta(
    'expiresAt',
  );
  @override
  late final GeneratedColumn<String> expiresAt = GeneratedColumn<String>(
    'expires_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<String> createdAt = GeneratedColumn<String>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [key, value, expiresAt, createdAt];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'cache_entries';
  @override
  VerificationContext validateIntegrity(
    Insertable<CacheEntry> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('key')) {
      context.handle(
        _keyMeta,
        key.isAcceptableOrUnknown(data['key']!, _keyMeta),
      );
    } else if (isInserting) {
      context.missing(_keyMeta);
    }
    if (data.containsKey('value')) {
      context.handle(
        _valueMeta,
        value.isAcceptableOrUnknown(data['value']!, _valueMeta),
      );
    } else if (isInserting) {
      context.missing(_valueMeta);
    }
    if (data.containsKey('expires_at')) {
      context.handle(
        _expiresAtMeta,
        expiresAt.isAcceptableOrUnknown(data['expires_at']!, _expiresAtMeta),
      );
    } else if (isInserting) {
      context.missing(_expiresAtMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  CacheEntry map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return CacheEntry(
      key: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}key'],
      )!,
      value: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}value'],
      )!,
      expiresAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}expires_at'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $CacheEntriesTable createAlias(String alias) {
    return $CacheEntriesTable(attachedDatabase, alias);
  }
}

class CacheEntry extends DataClass implements Insertable<CacheEntry> {
  final String key;
  final String value;
  final String expiresAt;
  final String createdAt;
  const CacheEntry({
    required this.key,
    required this.value,
    required this.expiresAt,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['key'] = Variable<String>(key);
    map['value'] = Variable<String>(value);
    map['expires_at'] = Variable<String>(expiresAt);
    map['created_at'] = Variable<String>(createdAt);
    return map;
  }

  CacheEntriesCompanion toCompanion(bool nullToAbsent) {
    return CacheEntriesCompanion(
      key: Value(key),
      value: Value(value),
      expiresAt: Value(expiresAt),
      createdAt: Value(createdAt),
    );
  }

  factory CacheEntry.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return CacheEntry(
      key: serializer.fromJson<String>(json['key']),
      value: serializer.fromJson<String>(json['value']),
      expiresAt: serializer.fromJson<String>(json['expiresAt']),
      createdAt: serializer.fromJson<String>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'key': serializer.toJson<String>(key),
      'value': serializer.toJson<String>(value),
      'expiresAt': serializer.toJson<String>(expiresAt),
      'createdAt': serializer.toJson<String>(createdAt),
    };
  }

  CacheEntry copyWith({
    String? key,
    String? value,
    String? expiresAt,
    String? createdAt,
  }) => CacheEntry(
    key: key ?? this.key,
    value: value ?? this.value,
    expiresAt: expiresAt ?? this.expiresAt,
    createdAt: createdAt ?? this.createdAt,
  );
  CacheEntry copyWithCompanion(CacheEntriesCompanion data) {
    return CacheEntry(
      key: data.key.present ? data.key.value : this.key,
      value: data.value.present ? data.value.value : this.value,
      expiresAt: data.expiresAt.present ? data.expiresAt.value : this.expiresAt,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('CacheEntry(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('expiresAt: $expiresAt, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(key, value, expiresAt, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is CacheEntry &&
          other.key == this.key &&
          other.value == this.value &&
          other.expiresAt == this.expiresAt &&
          other.createdAt == this.createdAt);
}

class CacheEntriesCompanion extends UpdateCompanion<CacheEntry> {
  final Value<String> key;
  final Value<String> value;
  final Value<String> expiresAt;
  final Value<String> createdAt;
  final Value<int> rowid;
  const CacheEntriesCompanion({
    this.key = const Value.absent(),
    this.value = const Value.absent(),
    this.expiresAt = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  CacheEntriesCompanion.insert({
    required String key,
    required String value,
    required String expiresAt,
    required String createdAt,
    this.rowid = const Value.absent(),
  }) : key = Value(key),
       value = Value(value),
       expiresAt = Value(expiresAt),
       createdAt = Value(createdAt);
  static Insertable<CacheEntry> custom({
    Expression<String>? key,
    Expression<String>? value,
    Expression<String>? expiresAt,
    Expression<String>? createdAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (key != null) 'key': key,
      if (value != null) 'value': value,
      if (expiresAt != null) 'expires_at': expiresAt,
      if (createdAt != null) 'created_at': createdAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  CacheEntriesCompanion copyWith({
    Value<String>? key,
    Value<String>? value,
    Value<String>? expiresAt,
    Value<String>? createdAt,
    Value<int>? rowid,
  }) {
    return CacheEntriesCompanion(
      key: key ?? this.key,
      value: value ?? this.value,
      expiresAt: expiresAt ?? this.expiresAt,
      createdAt: createdAt ?? this.createdAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) {
      map['key'] = Variable<String>(key.value);
    }
    if (value.present) {
      map['value'] = Variable<String>(value.value);
    }
    if (expiresAt.present) {
      map['expires_at'] = Variable<String>(expiresAt.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<String>(createdAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('CacheEntriesCompanion(')
          ..write('key: $key, ')
          ..write('value: $value, ')
          ..write('expiresAt: $expiresAt, ')
          ..write('createdAt: $createdAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $PatientsTable patients = $PatientsTable(this);
  late final $OrdersTable orders = $OrdersTable(this);
  late final $SamplesTable samples = $SamplesTable(this);
  late final $ResultsTable results = $ResultsTable(this);
  late final $NotificationsTable notifications = $NotificationsTable(this);
  late final $SyncQueueTable syncQueue = $SyncQueueTable(this);
  late final $CacheEntriesTable cacheEntries = $CacheEntriesTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    patients,
    orders,
    samples,
    results,
    notifications,
    syncQueue,
    cacheEntries,
  ];
}

typedef $$PatientsTableCreateCompanionBuilder =
    PatientsCompanion Function({
      required String id,
      Value<String?> labId,
      Value<String?> nationalId,
      Value<String?> sndhsHealthId,
      required String firstName,
      Value<String?> fatherName,
      Value<String?> grandFatherName,
      Value<String?> lastName,
      required String fullName,
      Value<String?> motherName,
      required String gender,
      Value<String?> dateOfBirth,
      Value<String?> phone,
      Value<String?> email,
      Value<String?> address,
      Value<String?> city,
      Value<String?> bloodGroup,
      Value<String?> maritalStatus,
      Value<String?> occupation,
      Value<String?> photoUrl,
      Value<String?> insuranceProvider,
      Value<String?> insuranceNumber,
      Value<String?> notes,
      Value<String?> tags,
      Value<String?> qrToken,
      required String createdAt,
      required String updatedAt,
      Value<String?> deletedAt,
      required String syncStatus,
      Value<int> rowid,
    });
typedef $$PatientsTableUpdateCompanionBuilder =
    PatientsCompanion Function({
      Value<String> id,
      Value<String?> labId,
      Value<String?> nationalId,
      Value<String?> sndhsHealthId,
      Value<String> firstName,
      Value<String?> fatherName,
      Value<String?> grandFatherName,
      Value<String?> lastName,
      Value<String> fullName,
      Value<String?> motherName,
      Value<String> gender,
      Value<String?> dateOfBirth,
      Value<String?> phone,
      Value<String?> email,
      Value<String?> address,
      Value<String?> city,
      Value<String?> bloodGroup,
      Value<String?> maritalStatus,
      Value<String?> occupation,
      Value<String?> photoUrl,
      Value<String?> insuranceProvider,
      Value<String?> insuranceNumber,
      Value<String?> notes,
      Value<String?> tags,
      Value<String?> qrToken,
      Value<String> createdAt,
      Value<String> updatedAt,
      Value<String?> deletedAt,
      Value<String> syncStatus,
      Value<int> rowid,
    });

class $$PatientsTableFilterComposer
    extends Composer<_$AppDatabase, $PatientsTable> {
  $$PatientsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get nationalId => $composableBuilder(
    column: $table.nationalId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sndhsHealthId => $composableBuilder(
    column: $table.sndhsHealthId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get firstName => $composableBuilder(
    column: $table.firstName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get fatherName => $composableBuilder(
    column: $table.fatherName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get grandFatherName => $composableBuilder(
    column: $table.grandFatherName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastName => $composableBuilder(
    column: $table.lastName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get fullName => $composableBuilder(
    column: $table.fullName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get motherName => $composableBuilder(
    column: $table.motherName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get gender => $composableBuilder(
    column: $table.gender,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get dateOfBirth => $composableBuilder(
    column: $table.dateOfBirth,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get phone => $composableBuilder(
    column: $table.phone,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get email => $composableBuilder(
    column: $table.email,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get address => $composableBuilder(
    column: $table.address,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get city => $composableBuilder(
    column: $table.city,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get bloodGroup => $composableBuilder(
    column: $table.bloodGroup,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get maritalStatus => $composableBuilder(
    column: $table.maritalStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get occupation => $composableBuilder(
    column: $table.occupation,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get photoUrl => $composableBuilder(
    column: $table.photoUrl,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get insuranceProvider => $composableBuilder(
    column: $table.insuranceProvider,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get insuranceNumber => $composableBuilder(
    column: $table.insuranceNumber,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get tags => $composableBuilder(
    column: $table.tags,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get qrToken => $composableBuilder(
    column: $table.qrToken,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get deletedAt => $composableBuilder(
    column: $table.deletedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );
}

class $$PatientsTableOrderingComposer
    extends Composer<_$AppDatabase, $PatientsTable> {
  $$PatientsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get nationalId => $composableBuilder(
    column: $table.nationalId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sndhsHealthId => $composableBuilder(
    column: $table.sndhsHealthId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get firstName => $composableBuilder(
    column: $table.firstName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get fatherName => $composableBuilder(
    column: $table.fatherName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get grandFatherName => $composableBuilder(
    column: $table.grandFatherName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastName => $composableBuilder(
    column: $table.lastName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get fullName => $composableBuilder(
    column: $table.fullName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get motherName => $composableBuilder(
    column: $table.motherName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get gender => $composableBuilder(
    column: $table.gender,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get dateOfBirth => $composableBuilder(
    column: $table.dateOfBirth,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get phone => $composableBuilder(
    column: $table.phone,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get email => $composableBuilder(
    column: $table.email,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get address => $composableBuilder(
    column: $table.address,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get city => $composableBuilder(
    column: $table.city,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get bloodGroup => $composableBuilder(
    column: $table.bloodGroup,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get maritalStatus => $composableBuilder(
    column: $table.maritalStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get occupation => $composableBuilder(
    column: $table.occupation,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get photoUrl => $composableBuilder(
    column: $table.photoUrl,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get insuranceProvider => $composableBuilder(
    column: $table.insuranceProvider,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get insuranceNumber => $composableBuilder(
    column: $table.insuranceNumber,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get tags => $composableBuilder(
    column: $table.tags,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get qrToken => $composableBuilder(
    column: $table.qrToken,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get deletedAt => $composableBuilder(
    column: $table.deletedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$PatientsTableAnnotationComposer
    extends Composer<_$AppDatabase, $PatientsTable> {
  $$PatientsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get labId =>
      $composableBuilder(column: $table.labId, builder: (column) => column);

  GeneratedColumn<String> get nationalId => $composableBuilder(
    column: $table.nationalId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get sndhsHealthId => $composableBuilder(
    column: $table.sndhsHealthId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get firstName =>
      $composableBuilder(column: $table.firstName, builder: (column) => column);

  GeneratedColumn<String> get fatherName => $composableBuilder(
    column: $table.fatherName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get grandFatherName => $composableBuilder(
    column: $table.grandFatherName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get lastName =>
      $composableBuilder(column: $table.lastName, builder: (column) => column);

  GeneratedColumn<String> get fullName =>
      $composableBuilder(column: $table.fullName, builder: (column) => column);

  GeneratedColumn<String> get motherName => $composableBuilder(
    column: $table.motherName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get gender =>
      $composableBuilder(column: $table.gender, builder: (column) => column);

  GeneratedColumn<String> get dateOfBirth => $composableBuilder(
    column: $table.dateOfBirth,
    builder: (column) => column,
  );

  GeneratedColumn<String> get phone =>
      $composableBuilder(column: $table.phone, builder: (column) => column);

  GeneratedColumn<String> get email =>
      $composableBuilder(column: $table.email, builder: (column) => column);

  GeneratedColumn<String> get address =>
      $composableBuilder(column: $table.address, builder: (column) => column);

  GeneratedColumn<String> get city =>
      $composableBuilder(column: $table.city, builder: (column) => column);

  GeneratedColumn<String> get bloodGroup => $composableBuilder(
    column: $table.bloodGroup,
    builder: (column) => column,
  );

  GeneratedColumn<String> get maritalStatus => $composableBuilder(
    column: $table.maritalStatus,
    builder: (column) => column,
  );

  GeneratedColumn<String> get occupation => $composableBuilder(
    column: $table.occupation,
    builder: (column) => column,
  );

  GeneratedColumn<String> get photoUrl =>
      $composableBuilder(column: $table.photoUrl, builder: (column) => column);

  GeneratedColumn<String> get insuranceProvider => $composableBuilder(
    column: $table.insuranceProvider,
    builder: (column) => column,
  );

  GeneratedColumn<String> get insuranceNumber => $composableBuilder(
    column: $table.insuranceNumber,
    builder: (column) => column,
  );

  GeneratedColumn<String> get notes =>
      $composableBuilder(column: $table.notes, builder: (column) => column);

  GeneratedColumn<String> get tags =>
      $composableBuilder(column: $table.tags, builder: (column) => column);

  GeneratedColumn<String> get qrToken =>
      $composableBuilder(column: $table.qrToken, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumn<String> get deletedAt =>
      $composableBuilder(column: $table.deletedAt, builder: (column) => column);

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );
}

class $$PatientsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $PatientsTable,
          Patient,
          $$PatientsTableFilterComposer,
          $$PatientsTableOrderingComposer,
          $$PatientsTableAnnotationComposer,
          $$PatientsTableCreateCompanionBuilder,
          $$PatientsTableUpdateCompanionBuilder,
          (Patient, BaseReferences<_$AppDatabase, $PatientsTable, Patient>),
          Patient,
          PrefetchHooks Function()
        > {
  $$PatientsTableTableManager(_$AppDatabase db, $PatientsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PatientsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PatientsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PatientsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String?> labId = const Value.absent(),
                Value<String?> nationalId = const Value.absent(),
                Value<String?> sndhsHealthId = const Value.absent(),
                Value<String> firstName = const Value.absent(),
                Value<String?> fatherName = const Value.absent(),
                Value<String?> grandFatherName = const Value.absent(),
                Value<String?> lastName = const Value.absent(),
                Value<String> fullName = const Value.absent(),
                Value<String?> motherName = const Value.absent(),
                Value<String> gender = const Value.absent(),
                Value<String?> dateOfBirth = const Value.absent(),
                Value<String?> phone = const Value.absent(),
                Value<String?> email = const Value.absent(),
                Value<String?> address = const Value.absent(),
                Value<String?> city = const Value.absent(),
                Value<String?> bloodGroup = const Value.absent(),
                Value<String?> maritalStatus = const Value.absent(),
                Value<String?> occupation = const Value.absent(),
                Value<String?> photoUrl = const Value.absent(),
                Value<String?> insuranceProvider = const Value.absent(),
                Value<String?> insuranceNumber = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<String?> tags = const Value.absent(),
                Value<String?> qrToken = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
                Value<String?> deletedAt = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => PatientsCompanion(
                id: id,
                labId: labId,
                nationalId: nationalId,
                sndhsHealthId: sndhsHealthId,
                firstName: firstName,
                fatherName: fatherName,
                grandFatherName: grandFatherName,
                lastName: lastName,
                fullName: fullName,
                motherName: motherName,
                gender: gender,
                dateOfBirth: dateOfBirth,
                phone: phone,
                email: email,
                address: address,
                city: city,
                bloodGroup: bloodGroup,
                maritalStatus: maritalStatus,
                occupation: occupation,
                photoUrl: photoUrl,
                insuranceProvider: insuranceProvider,
                insuranceNumber: insuranceNumber,
                notes: notes,
                tags: tags,
                qrToken: qrToken,
                createdAt: createdAt,
                updatedAt: updatedAt,
                deletedAt: deletedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                Value<String?> labId = const Value.absent(),
                Value<String?> nationalId = const Value.absent(),
                Value<String?> sndhsHealthId = const Value.absent(),
                required String firstName,
                Value<String?> fatherName = const Value.absent(),
                Value<String?> grandFatherName = const Value.absent(),
                Value<String?> lastName = const Value.absent(),
                required String fullName,
                Value<String?> motherName = const Value.absent(),
                required String gender,
                Value<String?> dateOfBirth = const Value.absent(),
                Value<String?> phone = const Value.absent(),
                Value<String?> email = const Value.absent(),
                Value<String?> address = const Value.absent(),
                Value<String?> city = const Value.absent(),
                Value<String?> bloodGroup = const Value.absent(),
                Value<String?> maritalStatus = const Value.absent(),
                Value<String?> occupation = const Value.absent(),
                Value<String?> photoUrl = const Value.absent(),
                Value<String?> insuranceProvider = const Value.absent(),
                Value<String?> insuranceNumber = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<String?> tags = const Value.absent(),
                Value<String?> qrToken = const Value.absent(),
                required String createdAt,
                required String updatedAt,
                Value<String?> deletedAt = const Value.absent(),
                required String syncStatus,
                Value<int> rowid = const Value.absent(),
              }) => PatientsCompanion.insert(
                id: id,
                labId: labId,
                nationalId: nationalId,
                sndhsHealthId: sndhsHealthId,
                firstName: firstName,
                fatherName: fatherName,
                grandFatherName: grandFatherName,
                lastName: lastName,
                fullName: fullName,
                motherName: motherName,
                gender: gender,
                dateOfBirth: dateOfBirth,
                phone: phone,
                email: email,
                address: address,
                city: city,
                bloodGroup: bloodGroup,
                maritalStatus: maritalStatus,
                occupation: occupation,
                photoUrl: photoUrl,
                insuranceProvider: insuranceProvider,
                insuranceNumber: insuranceNumber,
                notes: notes,
                tags: tags,
                qrToken: qrToken,
                createdAt: createdAt,
                updatedAt: updatedAt,
                deletedAt: deletedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$PatientsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $PatientsTable,
      Patient,
      $$PatientsTableFilterComposer,
      $$PatientsTableOrderingComposer,
      $$PatientsTableAnnotationComposer,
      $$PatientsTableCreateCompanionBuilder,
      $$PatientsTableUpdateCompanionBuilder,
      (Patient, BaseReferences<_$AppDatabase, $PatientsTable, Patient>),
      Patient,
      PrefetchHooks Function()
    >;
typedef $$OrdersTableCreateCompanionBuilder =
    OrdersCompanion Function({
      required String id,
      required String labId,
      required String patientId,
      required String patientName,
      required String orderNumber,
      required String status,
      Value<String?> priority,
      required String testTypes,
      Value<String?> doctorName,
      Value<String?> doctorId,
      Value<String?> diagnosis,
      Value<String?> notes,
      Value<String?> requestedBy,
      Value<String?> collectedBy,
      Value<String?> collectionDate,
      Value<String?> receivedDate,
      Value<String?> completedDate,
      required String createdAt,
      required String updatedAt,
      required String syncStatus,
      Value<int> rowid,
    });
typedef $$OrdersTableUpdateCompanionBuilder =
    OrdersCompanion Function({
      Value<String> id,
      Value<String> labId,
      Value<String> patientId,
      Value<String> patientName,
      Value<String> orderNumber,
      Value<String> status,
      Value<String?> priority,
      Value<String> testTypes,
      Value<String?> doctorName,
      Value<String?> doctorId,
      Value<String?> diagnosis,
      Value<String?> notes,
      Value<String?> requestedBy,
      Value<String?> collectedBy,
      Value<String?> collectionDate,
      Value<String?> receivedDate,
      Value<String?> completedDate,
      Value<String> createdAt,
      Value<String> updatedAt,
      Value<String> syncStatus,
      Value<int> rowid,
    });

class $$OrdersTableFilterComposer
    extends Composer<_$AppDatabase, $OrdersTable> {
  $$OrdersTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get patientId => $composableBuilder(
    column: $table.patientId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get patientName => $composableBuilder(
    column: $table.patientName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get orderNumber => $composableBuilder(
    column: $table.orderNumber,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get priority => $composableBuilder(
    column: $table.priority,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get testTypes => $composableBuilder(
    column: $table.testTypes,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get doctorName => $composableBuilder(
    column: $table.doctorName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get doctorId => $composableBuilder(
    column: $table.doctorId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get diagnosis => $composableBuilder(
    column: $table.diagnosis,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get requestedBy => $composableBuilder(
    column: $table.requestedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get collectedBy => $composableBuilder(
    column: $table.collectedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get collectionDate => $composableBuilder(
    column: $table.collectionDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get receivedDate => $composableBuilder(
    column: $table.receivedDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get completedDate => $composableBuilder(
    column: $table.completedDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );
}

class $$OrdersTableOrderingComposer
    extends Composer<_$AppDatabase, $OrdersTable> {
  $$OrdersTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get patientId => $composableBuilder(
    column: $table.patientId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get patientName => $composableBuilder(
    column: $table.patientName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get orderNumber => $composableBuilder(
    column: $table.orderNumber,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get priority => $composableBuilder(
    column: $table.priority,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get testTypes => $composableBuilder(
    column: $table.testTypes,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get doctorName => $composableBuilder(
    column: $table.doctorName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get doctorId => $composableBuilder(
    column: $table.doctorId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get diagnosis => $composableBuilder(
    column: $table.diagnosis,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get requestedBy => $composableBuilder(
    column: $table.requestedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get collectedBy => $composableBuilder(
    column: $table.collectedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get collectionDate => $composableBuilder(
    column: $table.collectionDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get receivedDate => $composableBuilder(
    column: $table.receivedDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get completedDate => $composableBuilder(
    column: $table.completedDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$OrdersTableAnnotationComposer
    extends Composer<_$AppDatabase, $OrdersTable> {
  $$OrdersTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get labId =>
      $composableBuilder(column: $table.labId, builder: (column) => column);

  GeneratedColumn<String> get patientId =>
      $composableBuilder(column: $table.patientId, builder: (column) => column);

  GeneratedColumn<String> get patientName => $composableBuilder(
    column: $table.patientName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get orderNumber => $composableBuilder(
    column: $table.orderNumber,
    builder: (column) => column,
  );

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get priority =>
      $composableBuilder(column: $table.priority, builder: (column) => column);

  GeneratedColumn<String> get testTypes =>
      $composableBuilder(column: $table.testTypes, builder: (column) => column);

  GeneratedColumn<String> get doctorName => $composableBuilder(
    column: $table.doctorName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get doctorId =>
      $composableBuilder(column: $table.doctorId, builder: (column) => column);

  GeneratedColumn<String> get diagnosis =>
      $composableBuilder(column: $table.diagnosis, builder: (column) => column);

  GeneratedColumn<String> get notes =>
      $composableBuilder(column: $table.notes, builder: (column) => column);

  GeneratedColumn<String> get requestedBy => $composableBuilder(
    column: $table.requestedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get collectedBy => $composableBuilder(
    column: $table.collectedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get collectionDate => $composableBuilder(
    column: $table.collectionDate,
    builder: (column) => column,
  );

  GeneratedColumn<String> get receivedDate => $composableBuilder(
    column: $table.receivedDate,
    builder: (column) => column,
  );

  GeneratedColumn<String> get completedDate => $composableBuilder(
    column: $table.completedDate,
    builder: (column) => column,
  );

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );
}

class $$OrdersTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $OrdersTable,
          Order,
          $$OrdersTableFilterComposer,
          $$OrdersTableOrderingComposer,
          $$OrdersTableAnnotationComposer,
          $$OrdersTableCreateCompanionBuilder,
          $$OrdersTableUpdateCompanionBuilder,
          (Order, BaseReferences<_$AppDatabase, $OrdersTable, Order>),
          Order,
          PrefetchHooks Function()
        > {
  $$OrdersTableTableManager(_$AppDatabase db, $OrdersTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$OrdersTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$OrdersTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$OrdersTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> labId = const Value.absent(),
                Value<String> patientId = const Value.absent(),
                Value<String> patientName = const Value.absent(),
                Value<String> orderNumber = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String?> priority = const Value.absent(),
                Value<String> testTypes = const Value.absent(),
                Value<String?> doctorName = const Value.absent(),
                Value<String?> doctorId = const Value.absent(),
                Value<String?> diagnosis = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<String?> requestedBy = const Value.absent(),
                Value<String?> collectedBy = const Value.absent(),
                Value<String?> collectionDate = const Value.absent(),
                Value<String?> receivedDate = const Value.absent(),
                Value<String?> completedDate = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => OrdersCompanion(
                id: id,
                labId: labId,
                patientId: patientId,
                patientName: patientName,
                orderNumber: orderNumber,
                status: status,
                priority: priority,
                testTypes: testTypes,
                doctorName: doctorName,
                doctorId: doctorId,
                diagnosis: diagnosis,
                notes: notes,
                requestedBy: requestedBy,
                collectedBy: collectedBy,
                collectionDate: collectionDate,
                receivedDate: receivedDate,
                completedDate: completedDate,
                createdAt: createdAt,
                updatedAt: updatedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String labId,
                required String patientId,
                required String patientName,
                required String orderNumber,
                required String status,
                Value<String?> priority = const Value.absent(),
                required String testTypes,
                Value<String?> doctorName = const Value.absent(),
                Value<String?> doctorId = const Value.absent(),
                Value<String?> diagnosis = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<String?> requestedBy = const Value.absent(),
                Value<String?> collectedBy = const Value.absent(),
                Value<String?> collectionDate = const Value.absent(),
                Value<String?> receivedDate = const Value.absent(),
                Value<String?> completedDate = const Value.absent(),
                required String createdAt,
                required String updatedAt,
                required String syncStatus,
                Value<int> rowid = const Value.absent(),
              }) => OrdersCompanion.insert(
                id: id,
                labId: labId,
                patientId: patientId,
                patientName: patientName,
                orderNumber: orderNumber,
                status: status,
                priority: priority,
                testTypes: testTypes,
                doctorName: doctorName,
                doctorId: doctorId,
                diagnosis: diagnosis,
                notes: notes,
                requestedBy: requestedBy,
                collectedBy: collectedBy,
                collectionDate: collectionDate,
                receivedDate: receivedDate,
                completedDate: completedDate,
                createdAt: createdAt,
                updatedAt: updatedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$OrdersTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $OrdersTable,
      Order,
      $$OrdersTableFilterComposer,
      $$OrdersTableOrderingComposer,
      $$OrdersTableAnnotationComposer,
      $$OrdersTableCreateCompanionBuilder,
      $$OrdersTableUpdateCompanionBuilder,
      (Order, BaseReferences<_$AppDatabase, $OrdersTable, Order>),
      Order,
      PrefetchHooks Function()
    >;
typedef $$SamplesTableCreateCompanionBuilder =
    SamplesCompanion Function({
      required String id,
      required String labId,
      required String orderId,
      required String patientId,
      required String sampleType,
      required String barcode,
      required String status,
      Value<String?> containerType,
      Value<double?> volume,
      Value<String?> collectedAt,
      Value<String?> collectedBy,
      Value<String?> receivedAt,
      Value<String?> receivedBy,
      Value<String?> processedAt,
      Value<String?> processedBy,
      Value<String?> storageLocation,
      Value<String?> rejectionReason,
      Value<String?> notes,
      required String createdAt,
      required String updatedAt,
      required String syncStatus,
      Value<int> rowid,
    });
typedef $$SamplesTableUpdateCompanionBuilder =
    SamplesCompanion Function({
      Value<String> id,
      Value<String> labId,
      Value<String> orderId,
      Value<String> patientId,
      Value<String> sampleType,
      Value<String> barcode,
      Value<String> status,
      Value<String?> containerType,
      Value<double?> volume,
      Value<String?> collectedAt,
      Value<String?> collectedBy,
      Value<String?> receivedAt,
      Value<String?> receivedBy,
      Value<String?> processedAt,
      Value<String?> processedBy,
      Value<String?> storageLocation,
      Value<String?> rejectionReason,
      Value<String?> notes,
      Value<String> createdAt,
      Value<String> updatedAt,
      Value<String> syncStatus,
      Value<int> rowid,
    });

class $$SamplesTableFilterComposer
    extends Composer<_$AppDatabase, $SamplesTable> {
  $$SamplesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get orderId => $composableBuilder(
    column: $table.orderId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get patientId => $composableBuilder(
    column: $table.patientId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sampleType => $composableBuilder(
    column: $table.sampleType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get barcode => $composableBuilder(
    column: $table.barcode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get containerType => $composableBuilder(
    column: $table.containerType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get volume => $composableBuilder(
    column: $table.volume,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get collectedAt => $composableBuilder(
    column: $table.collectedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get collectedBy => $composableBuilder(
    column: $table.collectedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get receivedAt => $composableBuilder(
    column: $table.receivedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get receivedBy => $composableBuilder(
    column: $table.receivedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get processedAt => $composableBuilder(
    column: $table.processedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get processedBy => $composableBuilder(
    column: $table.processedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get storageLocation => $composableBuilder(
    column: $table.storageLocation,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get rejectionReason => $composableBuilder(
    column: $table.rejectionReason,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SamplesTableOrderingComposer
    extends Composer<_$AppDatabase, $SamplesTable> {
  $$SamplesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get orderId => $composableBuilder(
    column: $table.orderId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get patientId => $composableBuilder(
    column: $table.patientId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sampleType => $composableBuilder(
    column: $table.sampleType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get barcode => $composableBuilder(
    column: $table.barcode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get containerType => $composableBuilder(
    column: $table.containerType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get volume => $composableBuilder(
    column: $table.volume,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get collectedAt => $composableBuilder(
    column: $table.collectedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get collectedBy => $composableBuilder(
    column: $table.collectedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get receivedAt => $composableBuilder(
    column: $table.receivedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get receivedBy => $composableBuilder(
    column: $table.receivedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get processedAt => $composableBuilder(
    column: $table.processedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get processedBy => $composableBuilder(
    column: $table.processedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get storageLocation => $composableBuilder(
    column: $table.storageLocation,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get rejectionReason => $composableBuilder(
    column: $table.rejectionReason,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SamplesTableAnnotationComposer
    extends Composer<_$AppDatabase, $SamplesTable> {
  $$SamplesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get labId =>
      $composableBuilder(column: $table.labId, builder: (column) => column);

  GeneratedColumn<String> get orderId =>
      $composableBuilder(column: $table.orderId, builder: (column) => column);

  GeneratedColumn<String> get patientId =>
      $composableBuilder(column: $table.patientId, builder: (column) => column);

  GeneratedColumn<String> get sampleType => $composableBuilder(
    column: $table.sampleType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get barcode =>
      $composableBuilder(column: $table.barcode, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get containerType => $composableBuilder(
    column: $table.containerType,
    builder: (column) => column,
  );

  GeneratedColumn<double> get volume =>
      $composableBuilder(column: $table.volume, builder: (column) => column);

  GeneratedColumn<String> get collectedAt => $composableBuilder(
    column: $table.collectedAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get collectedBy => $composableBuilder(
    column: $table.collectedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get receivedAt => $composableBuilder(
    column: $table.receivedAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get receivedBy => $composableBuilder(
    column: $table.receivedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get processedAt => $composableBuilder(
    column: $table.processedAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get processedBy => $composableBuilder(
    column: $table.processedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get storageLocation => $composableBuilder(
    column: $table.storageLocation,
    builder: (column) => column,
  );

  GeneratedColumn<String> get rejectionReason => $composableBuilder(
    column: $table.rejectionReason,
    builder: (column) => column,
  );

  GeneratedColumn<String> get notes =>
      $composableBuilder(column: $table.notes, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );
}

class $$SamplesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SamplesTable,
          Sample,
          $$SamplesTableFilterComposer,
          $$SamplesTableOrderingComposer,
          $$SamplesTableAnnotationComposer,
          $$SamplesTableCreateCompanionBuilder,
          $$SamplesTableUpdateCompanionBuilder,
          (Sample, BaseReferences<_$AppDatabase, $SamplesTable, Sample>),
          Sample,
          PrefetchHooks Function()
        > {
  $$SamplesTableTableManager(_$AppDatabase db, $SamplesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SamplesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SamplesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SamplesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> labId = const Value.absent(),
                Value<String> orderId = const Value.absent(),
                Value<String> patientId = const Value.absent(),
                Value<String> sampleType = const Value.absent(),
                Value<String> barcode = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String?> containerType = const Value.absent(),
                Value<double?> volume = const Value.absent(),
                Value<String?> collectedAt = const Value.absent(),
                Value<String?> collectedBy = const Value.absent(),
                Value<String?> receivedAt = const Value.absent(),
                Value<String?> receivedBy = const Value.absent(),
                Value<String?> processedAt = const Value.absent(),
                Value<String?> processedBy = const Value.absent(),
                Value<String?> storageLocation = const Value.absent(),
                Value<String?> rejectionReason = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SamplesCompanion(
                id: id,
                labId: labId,
                orderId: orderId,
                patientId: patientId,
                sampleType: sampleType,
                barcode: barcode,
                status: status,
                containerType: containerType,
                volume: volume,
                collectedAt: collectedAt,
                collectedBy: collectedBy,
                receivedAt: receivedAt,
                receivedBy: receivedBy,
                processedAt: processedAt,
                processedBy: processedBy,
                storageLocation: storageLocation,
                rejectionReason: rejectionReason,
                notes: notes,
                createdAt: createdAt,
                updatedAt: updatedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String labId,
                required String orderId,
                required String patientId,
                required String sampleType,
                required String barcode,
                required String status,
                Value<String?> containerType = const Value.absent(),
                Value<double?> volume = const Value.absent(),
                Value<String?> collectedAt = const Value.absent(),
                Value<String?> collectedBy = const Value.absent(),
                Value<String?> receivedAt = const Value.absent(),
                Value<String?> receivedBy = const Value.absent(),
                Value<String?> processedAt = const Value.absent(),
                Value<String?> processedBy = const Value.absent(),
                Value<String?> storageLocation = const Value.absent(),
                Value<String?> rejectionReason = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                required String createdAt,
                required String updatedAt,
                required String syncStatus,
                Value<int> rowid = const Value.absent(),
              }) => SamplesCompanion.insert(
                id: id,
                labId: labId,
                orderId: orderId,
                patientId: patientId,
                sampleType: sampleType,
                barcode: barcode,
                status: status,
                containerType: containerType,
                volume: volume,
                collectedAt: collectedAt,
                collectedBy: collectedBy,
                receivedAt: receivedAt,
                receivedBy: receivedBy,
                processedAt: processedAt,
                processedBy: processedBy,
                storageLocation: storageLocation,
                rejectionReason: rejectionReason,
                notes: notes,
                createdAt: createdAt,
                updatedAt: updatedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SamplesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SamplesTable,
      Sample,
      $$SamplesTableFilterComposer,
      $$SamplesTableOrderingComposer,
      $$SamplesTableAnnotationComposer,
      $$SamplesTableCreateCompanionBuilder,
      $$SamplesTableUpdateCompanionBuilder,
      (Sample, BaseReferences<_$AppDatabase, $SamplesTable, Sample>),
      Sample,
      PrefetchHooks Function()
    >;
typedef $$ResultsTableCreateCompanionBuilder =
    ResultsCompanion Function({
      required String id,
      required String labId,
      required String orderId,
      Value<String?> sampleId,
      required String patientId,
      required String testCode,
      required String testName,
      required String result,
      Value<String?> unit,
      Value<String?> referenceRange,
      Value<String?> flag,
      required int isAbnormal,
      required int isCritical,
      Value<String?> validatedBy,
      Value<String?> validatedAt,
      Value<String?> performedBy,
      Value<String?> instrumentId,
      Value<String?> notes,
      required String status,
      required String createdAt,
      required String updatedAt,
      required String syncStatus,
      Value<int> rowid,
    });
typedef $$ResultsTableUpdateCompanionBuilder =
    ResultsCompanion Function({
      Value<String> id,
      Value<String> labId,
      Value<String> orderId,
      Value<String?> sampleId,
      Value<String> patientId,
      Value<String> testCode,
      Value<String> testName,
      Value<String> result,
      Value<String?> unit,
      Value<String?> referenceRange,
      Value<String?> flag,
      Value<int> isAbnormal,
      Value<int> isCritical,
      Value<String?> validatedBy,
      Value<String?> validatedAt,
      Value<String?> performedBy,
      Value<String?> instrumentId,
      Value<String?> notes,
      Value<String> status,
      Value<String> createdAt,
      Value<String> updatedAt,
      Value<String> syncStatus,
      Value<int> rowid,
    });

class $$ResultsTableFilterComposer
    extends Composer<_$AppDatabase, $ResultsTable> {
  $$ResultsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get orderId => $composableBuilder(
    column: $table.orderId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get sampleId => $composableBuilder(
    column: $table.sampleId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get patientId => $composableBuilder(
    column: $table.patientId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get testCode => $composableBuilder(
    column: $table.testCode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get testName => $composableBuilder(
    column: $table.testName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get result => $composableBuilder(
    column: $table.result,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get unit => $composableBuilder(
    column: $table.unit,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get referenceRange => $composableBuilder(
    column: $table.referenceRange,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get flag => $composableBuilder(
    column: $table.flag,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get isAbnormal => $composableBuilder(
    column: $table.isAbnormal,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get isCritical => $composableBuilder(
    column: $table.isCritical,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get validatedBy => $composableBuilder(
    column: $table.validatedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get validatedAt => $composableBuilder(
    column: $table.validatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get performedBy => $composableBuilder(
    column: $table.performedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get instrumentId => $composableBuilder(
    column: $table.instrumentId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ResultsTableOrderingComposer
    extends Composer<_$AppDatabase, $ResultsTable> {
  $$ResultsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get orderId => $composableBuilder(
    column: $table.orderId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get sampleId => $composableBuilder(
    column: $table.sampleId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get patientId => $composableBuilder(
    column: $table.patientId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get testCode => $composableBuilder(
    column: $table.testCode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get testName => $composableBuilder(
    column: $table.testName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get result => $composableBuilder(
    column: $table.result,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get unit => $composableBuilder(
    column: $table.unit,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get referenceRange => $composableBuilder(
    column: $table.referenceRange,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get flag => $composableBuilder(
    column: $table.flag,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get isAbnormal => $composableBuilder(
    column: $table.isAbnormal,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get isCritical => $composableBuilder(
    column: $table.isCritical,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get validatedBy => $composableBuilder(
    column: $table.validatedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get validatedAt => $composableBuilder(
    column: $table.validatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get performedBy => $composableBuilder(
    column: $table.performedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get instrumentId => $composableBuilder(
    column: $table.instrumentId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get notes => $composableBuilder(
    column: $table.notes,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ResultsTableAnnotationComposer
    extends Composer<_$AppDatabase, $ResultsTable> {
  $$ResultsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get labId =>
      $composableBuilder(column: $table.labId, builder: (column) => column);

  GeneratedColumn<String> get orderId =>
      $composableBuilder(column: $table.orderId, builder: (column) => column);

  GeneratedColumn<String> get sampleId =>
      $composableBuilder(column: $table.sampleId, builder: (column) => column);

  GeneratedColumn<String> get patientId =>
      $composableBuilder(column: $table.patientId, builder: (column) => column);

  GeneratedColumn<String> get testCode =>
      $composableBuilder(column: $table.testCode, builder: (column) => column);

  GeneratedColumn<String> get testName =>
      $composableBuilder(column: $table.testName, builder: (column) => column);

  GeneratedColumn<String> get result =>
      $composableBuilder(column: $table.result, builder: (column) => column);

  GeneratedColumn<String> get unit =>
      $composableBuilder(column: $table.unit, builder: (column) => column);

  GeneratedColumn<String> get referenceRange => $composableBuilder(
    column: $table.referenceRange,
    builder: (column) => column,
  );

  GeneratedColumn<String> get flag =>
      $composableBuilder(column: $table.flag, builder: (column) => column);

  GeneratedColumn<int> get isAbnormal => $composableBuilder(
    column: $table.isAbnormal,
    builder: (column) => column,
  );

  GeneratedColumn<int> get isCritical => $composableBuilder(
    column: $table.isCritical,
    builder: (column) => column,
  );

  GeneratedColumn<String> get validatedBy => $composableBuilder(
    column: $table.validatedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get validatedAt => $composableBuilder(
    column: $table.validatedAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get performedBy => $composableBuilder(
    column: $table.performedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get instrumentId => $composableBuilder(
    column: $table.instrumentId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get notes =>
      $composableBuilder(column: $table.notes, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );
}

class $$ResultsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ResultsTable,
          Result,
          $$ResultsTableFilterComposer,
          $$ResultsTableOrderingComposer,
          $$ResultsTableAnnotationComposer,
          $$ResultsTableCreateCompanionBuilder,
          $$ResultsTableUpdateCompanionBuilder,
          (Result, BaseReferences<_$AppDatabase, $ResultsTable, Result>),
          Result,
          PrefetchHooks Function()
        > {
  $$ResultsTableTableManager(_$AppDatabase db, $ResultsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ResultsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ResultsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ResultsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> labId = const Value.absent(),
                Value<String> orderId = const Value.absent(),
                Value<String?> sampleId = const Value.absent(),
                Value<String> patientId = const Value.absent(),
                Value<String> testCode = const Value.absent(),
                Value<String> testName = const Value.absent(),
                Value<String> result = const Value.absent(),
                Value<String?> unit = const Value.absent(),
                Value<String?> referenceRange = const Value.absent(),
                Value<String?> flag = const Value.absent(),
                Value<int> isAbnormal = const Value.absent(),
                Value<int> isCritical = const Value.absent(),
                Value<String?> validatedBy = const Value.absent(),
                Value<String?> validatedAt = const Value.absent(),
                Value<String?> performedBy = const Value.absent(),
                Value<String?> instrumentId = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ResultsCompanion(
                id: id,
                labId: labId,
                orderId: orderId,
                sampleId: sampleId,
                patientId: patientId,
                testCode: testCode,
                testName: testName,
                result: result,
                unit: unit,
                referenceRange: referenceRange,
                flag: flag,
                isAbnormal: isAbnormal,
                isCritical: isCritical,
                validatedBy: validatedBy,
                validatedAt: validatedAt,
                performedBy: performedBy,
                instrumentId: instrumentId,
                notes: notes,
                status: status,
                createdAt: createdAt,
                updatedAt: updatedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String labId,
                required String orderId,
                Value<String?> sampleId = const Value.absent(),
                required String patientId,
                required String testCode,
                required String testName,
                required String result,
                Value<String?> unit = const Value.absent(),
                Value<String?> referenceRange = const Value.absent(),
                Value<String?> flag = const Value.absent(),
                required int isAbnormal,
                required int isCritical,
                Value<String?> validatedBy = const Value.absent(),
                Value<String?> validatedAt = const Value.absent(),
                Value<String?> performedBy = const Value.absent(),
                Value<String?> instrumentId = const Value.absent(),
                Value<String?> notes = const Value.absent(),
                required String status,
                required String createdAt,
                required String updatedAt,
                required String syncStatus,
                Value<int> rowid = const Value.absent(),
              }) => ResultsCompanion.insert(
                id: id,
                labId: labId,
                orderId: orderId,
                sampleId: sampleId,
                patientId: patientId,
                testCode: testCode,
                testName: testName,
                result: result,
                unit: unit,
                referenceRange: referenceRange,
                flag: flag,
                isAbnormal: isAbnormal,
                isCritical: isCritical,
                validatedBy: validatedBy,
                validatedAt: validatedAt,
                performedBy: performedBy,
                instrumentId: instrumentId,
                notes: notes,
                status: status,
                createdAt: createdAt,
                updatedAt: updatedAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ResultsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ResultsTable,
      Result,
      $$ResultsTableFilterComposer,
      $$ResultsTableOrderingComposer,
      $$ResultsTableAnnotationComposer,
      $$ResultsTableCreateCompanionBuilder,
      $$ResultsTableUpdateCompanionBuilder,
      (Result, BaseReferences<_$AppDatabase, $ResultsTable, Result>),
      Result,
      PrefetchHooks Function()
    >;
typedef $$NotificationsTableCreateCompanionBuilder =
    NotificationsCompanion Function({
      required String id,
      Value<String?> labId,
      required String title,
      required String body,
      required String type,
      required String severity,
      Value<String?> entityType,
      Value<String?> entityId,
      required int isRead,
      required int isActioned,
      required String createdAt,
      required String syncStatus,
      Value<int> rowid,
    });
typedef $$NotificationsTableUpdateCompanionBuilder =
    NotificationsCompanion Function({
      Value<String> id,
      Value<String?> labId,
      Value<String> title,
      Value<String> body,
      Value<String> type,
      Value<String> severity,
      Value<String?> entityType,
      Value<String?> entityId,
      Value<int> isRead,
      Value<int> isActioned,
      Value<String> createdAt,
      Value<String> syncStatus,
      Value<int> rowid,
    });

class $$NotificationsTableFilterComposer
    extends Composer<_$AppDatabase, $NotificationsTable> {
  $$NotificationsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get body => $composableBuilder(
    column: $table.body,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get type => $composableBuilder(
    column: $table.type,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get severity => $composableBuilder(
    column: $table.severity,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityId => $composableBuilder(
    column: $table.entityId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get isRead => $composableBuilder(
    column: $table.isRead,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get isActioned => $composableBuilder(
    column: $table.isActioned,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );
}

class $$NotificationsTableOrderingComposer
    extends Composer<_$AppDatabase, $NotificationsTable> {
  $$NotificationsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get labId => $composableBuilder(
    column: $table.labId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get body => $composableBuilder(
    column: $table.body,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get type => $composableBuilder(
    column: $table.type,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get severity => $composableBuilder(
    column: $table.severity,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityId => $composableBuilder(
    column: $table.entityId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get isRead => $composableBuilder(
    column: $table.isRead,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get isActioned => $composableBuilder(
    column: $table.isActioned,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$NotificationsTableAnnotationComposer
    extends Composer<_$AppDatabase, $NotificationsTable> {
  $$NotificationsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get labId =>
      $composableBuilder(column: $table.labId, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get body =>
      $composableBuilder(column: $table.body, builder: (column) => column);

  GeneratedColumn<String> get type =>
      $composableBuilder(column: $table.type, builder: (column) => column);

  GeneratedColumn<String> get severity =>
      $composableBuilder(column: $table.severity, builder: (column) => column);

  GeneratedColumn<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get entityId =>
      $composableBuilder(column: $table.entityId, builder: (column) => column);

  GeneratedColumn<int> get isRead =>
      $composableBuilder(column: $table.isRead, builder: (column) => column);

  GeneratedColumn<int> get isActioned => $composableBuilder(
    column: $table.isActioned,
    builder: (column) => column,
  );

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );
}

class $$NotificationsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $NotificationsTable,
          Notification,
          $$NotificationsTableFilterComposer,
          $$NotificationsTableOrderingComposer,
          $$NotificationsTableAnnotationComposer,
          $$NotificationsTableCreateCompanionBuilder,
          $$NotificationsTableUpdateCompanionBuilder,
          (
            Notification,
            BaseReferences<_$AppDatabase, $NotificationsTable, Notification>,
          ),
          Notification,
          PrefetchHooks Function()
        > {
  $$NotificationsTableTableManager(_$AppDatabase db, $NotificationsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$NotificationsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$NotificationsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$NotificationsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String?> labId = const Value.absent(),
                Value<String> title = const Value.absent(),
                Value<String> body = const Value.absent(),
                Value<String> type = const Value.absent(),
                Value<String> severity = const Value.absent(),
                Value<String?> entityType = const Value.absent(),
                Value<String?> entityId = const Value.absent(),
                Value<int> isRead = const Value.absent(),
                Value<int> isActioned = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => NotificationsCompanion(
                id: id,
                labId: labId,
                title: title,
                body: body,
                type: type,
                severity: severity,
                entityType: entityType,
                entityId: entityId,
                isRead: isRead,
                isActioned: isActioned,
                createdAt: createdAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                Value<String?> labId = const Value.absent(),
                required String title,
                required String body,
                required String type,
                required String severity,
                Value<String?> entityType = const Value.absent(),
                Value<String?> entityId = const Value.absent(),
                required int isRead,
                required int isActioned,
                required String createdAt,
                required String syncStatus,
                Value<int> rowid = const Value.absent(),
              }) => NotificationsCompanion.insert(
                id: id,
                labId: labId,
                title: title,
                body: body,
                type: type,
                severity: severity,
                entityType: entityType,
                entityId: entityId,
                isRead: isRead,
                isActioned: isActioned,
                createdAt: createdAt,
                syncStatus: syncStatus,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$NotificationsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $NotificationsTable,
      Notification,
      $$NotificationsTableFilterComposer,
      $$NotificationsTableOrderingComposer,
      $$NotificationsTableAnnotationComposer,
      $$NotificationsTableCreateCompanionBuilder,
      $$NotificationsTableUpdateCompanionBuilder,
      (
        Notification,
        BaseReferences<_$AppDatabase, $NotificationsTable, Notification>,
      ),
      Notification,
      PrefetchHooks Function()
    >;
typedef $$SyncQueueTableCreateCompanionBuilder =
    SyncQueueCompanion Function({
      Value<int> id,
      required String entityType,
      required String entityId,
      required String operation,
      required String payload,
      required String status,
      required int retryCount,
      required int maxRetries,
      required String createdAt,
      required String updatedAt,
      Value<String?> lastError,
    });
typedef $$SyncQueueTableUpdateCompanionBuilder =
    SyncQueueCompanion Function({
      Value<int> id,
      Value<String> entityType,
      Value<String> entityId,
      Value<String> operation,
      Value<String> payload,
      Value<String> status,
      Value<int> retryCount,
      Value<int> maxRetries,
      Value<String> createdAt,
      Value<String> updatedAt,
      Value<String?> lastError,
    });

class $$SyncQueueTableFilterComposer
    extends Composer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityId => $composableBuilder(
    column: $table.entityId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get operation => $composableBuilder(
    column: $table.operation,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get payload => $composableBuilder(
    column: $table.payload,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get maxRetries => $composableBuilder(
    column: $table.maxRetries,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncQueueTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityId => $composableBuilder(
    column: $table.entityId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get operation => $composableBuilder(
    column: $table.operation,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get payload => $composableBuilder(
    column: $table.payload,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get maxRetries => $composableBuilder(
    column: $table.maxRetries,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncQueueTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncQueueTable> {
  $$SyncQueueTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get entityId =>
      $composableBuilder(column: $table.entityId, builder: (column) => column);

  GeneratedColumn<String> get operation =>
      $composableBuilder(column: $table.operation, builder: (column) => column);

  GeneratedColumn<String> get payload =>
      $composableBuilder(column: $table.payload, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => column,
  );

  GeneratedColumn<int> get maxRetries => $composableBuilder(
    column: $table.maxRetries,
    builder: (column) => column,
  );

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);
}

class $$SyncQueueTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncQueueTable,
          SyncQueueData,
          $$SyncQueueTableFilterComposer,
          $$SyncQueueTableOrderingComposer,
          $$SyncQueueTableAnnotationComposer,
          $$SyncQueueTableCreateCompanionBuilder,
          $$SyncQueueTableUpdateCompanionBuilder,
          (
            SyncQueueData,
            BaseReferences<_$AppDatabase, $SyncQueueTable, SyncQueueData>,
          ),
          SyncQueueData,
          PrefetchHooks Function()
        > {
  $$SyncQueueTableTableManager(_$AppDatabase db, $SyncQueueTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncQueueTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncQueueTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncQueueTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> entityType = const Value.absent(),
                Value<String> entityId = const Value.absent(),
                Value<String> operation = const Value.absent(),
                Value<String> payload = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<int> retryCount = const Value.absent(),
                Value<int> maxRetries = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<String> updatedAt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
              }) => SyncQueueCompanion(
                id: id,
                entityType: entityType,
                entityId: entityId,
                operation: operation,
                payload: payload,
                status: status,
                retryCount: retryCount,
                maxRetries: maxRetries,
                createdAt: createdAt,
                updatedAt: updatedAt,
                lastError: lastError,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String entityType,
                required String entityId,
                required String operation,
                required String payload,
                required String status,
                required int retryCount,
                required int maxRetries,
                required String createdAt,
                required String updatedAt,
                Value<String?> lastError = const Value.absent(),
              }) => SyncQueueCompanion.insert(
                id: id,
                entityType: entityType,
                entityId: entityId,
                operation: operation,
                payload: payload,
                status: status,
                retryCount: retryCount,
                maxRetries: maxRetries,
                createdAt: createdAt,
                updatedAt: updatedAt,
                lastError: lastError,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncQueueTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncQueueTable,
      SyncQueueData,
      $$SyncQueueTableFilterComposer,
      $$SyncQueueTableOrderingComposer,
      $$SyncQueueTableAnnotationComposer,
      $$SyncQueueTableCreateCompanionBuilder,
      $$SyncQueueTableUpdateCompanionBuilder,
      (
        SyncQueueData,
        BaseReferences<_$AppDatabase, $SyncQueueTable, SyncQueueData>,
      ),
      SyncQueueData,
      PrefetchHooks Function()
    >;
typedef $$CacheEntriesTableCreateCompanionBuilder =
    CacheEntriesCompanion Function({
      required String key,
      required String value,
      required String expiresAt,
      required String createdAt,
      Value<int> rowid,
    });
typedef $$CacheEntriesTableUpdateCompanionBuilder =
    CacheEntriesCompanion Function({
      Value<String> key,
      Value<String> value,
      Value<String> expiresAt,
      Value<String> createdAt,
      Value<int> rowid,
    });

class $$CacheEntriesTableFilterComposer
    extends Composer<_$AppDatabase, $CacheEntriesTable> {
  $$CacheEntriesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get expiresAt => $composableBuilder(
    column: $table.expiresAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$CacheEntriesTableOrderingComposer
    extends Composer<_$AppDatabase, $CacheEntriesTable> {
  $$CacheEntriesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get key => $composableBuilder(
    column: $table.key,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get value => $composableBuilder(
    column: $table.value,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get expiresAt => $composableBuilder(
    column: $table.expiresAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$CacheEntriesTableAnnotationComposer
    extends Composer<_$AppDatabase, $CacheEntriesTable> {
  $$CacheEntriesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get key =>
      $composableBuilder(column: $table.key, builder: (column) => column);

  GeneratedColumn<String> get value =>
      $composableBuilder(column: $table.value, builder: (column) => column);

  GeneratedColumn<String> get expiresAt =>
      $composableBuilder(column: $table.expiresAt, builder: (column) => column);

  GeneratedColumn<String> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$CacheEntriesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $CacheEntriesTable,
          CacheEntry,
          $$CacheEntriesTableFilterComposer,
          $$CacheEntriesTableOrderingComposer,
          $$CacheEntriesTableAnnotationComposer,
          $$CacheEntriesTableCreateCompanionBuilder,
          $$CacheEntriesTableUpdateCompanionBuilder,
          (
            CacheEntry,
            BaseReferences<_$AppDatabase, $CacheEntriesTable, CacheEntry>,
          ),
          CacheEntry,
          PrefetchHooks Function()
        > {
  $$CacheEntriesTableTableManager(_$AppDatabase db, $CacheEntriesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$CacheEntriesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$CacheEntriesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$CacheEntriesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> key = const Value.absent(),
                Value<String> value = const Value.absent(),
                Value<String> expiresAt = const Value.absent(),
                Value<String> createdAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => CacheEntriesCompanion(
                key: key,
                value: value,
                expiresAt: expiresAt,
                createdAt: createdAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String key,
                required String value,
                required String expiresAt,
                required String createdAt,
                Value<int> rowid = const Value.absent(),
              }) => CacheEntriesCompanion.insert(
                key: key,
                value: value,
                expiresAt: expiresAt,
                createdAt: createdAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$CacheEntriesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $CacheEntriesTable,
      CacheEntry,
      $$CacheEntriesTableFilterComposer,
      $$CacheEntriesTableOrderingComposer,
      $$CacheEntriesTableAnnotationComposer,
      $$CacheEntriesTableCreateCompanionBuilder,
      $$CacheEntriesTableUpdateCompanionBuilder,
      (
        CacheEntry,
        BaseReferences<_$AppDatabase, $CacheEntriesTable, CacheEntry>,
      ),
      CacheEntry,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$PatientsTableTableManager get patients =>
      $$PatientsTableTableManager(_db, _db.patients);
  $$OrdersTableTableManager get orders =>
      $$OrdersTableTableManager(_db, _db.orders);
  $$SamplesTableTableManager get samples =>
      $$SamplesTableTableManager(_db, _db.samples);
  $$ResultsTableTableManager get results =>
      $$ResultsTableTableManager(_db, _db.results);
  $$NotificationsTableTableManager get notifications =>
      $$NotificationsTableTableManager(_db, _db.notifications);
  $$SyncQueueTableTableManager get syncQueue =>
      $$SyncQueueTableTableManager(_db, _db.syncQueue);
  $$CacheEntriesTableTableManager get cacheEntries =>
      $$CacheEntriesTableTableManager(_db, _db.cacheEntries);
}
