# NIAM — Glossary

## Terms

### A

**Account (حساب)**
The authentication principal — what a person uses to log in. Linked to exactly one Identity. Stores credentials, MFA settings, lockout state, and login tracking. Types: human, machine, service, system. Statuses: active, locked, suspended, deactivated, pending_verification.

**Account Lockout (قفل الحساب)**
Automatic security measure that locks an account after 5 consecutive failed login attempts for 30 minutes. Prevents brute-force password attacks.

**Account Type (نوع الحساب)**
Classification of an account: `human` (natural person), `machine` (automated system), `service` (service account), `system` (infrastructure account).

**API Key (مفتاح API)**
A credential type used by Enterprise Accounts for system-to-system API authentication. Stored as a hash, identified by a key prefix.

**Assignment (تعيين)**
A record linking a Person to a specific Role within an organizational scope (organization, facility, department, committee, or task force). The mechanism for RBAC — permissions are derived from a person's active assignments. Can be temporary, emergency, or delegated.

**Assignment Status (حالة التعيين)**
`active` — currently effective. `completed` — naturally ended. `cancelled` — revoked before end date. `expired` — passed end date.

**Audit Event (حدث التدقيق)**
An immutable record of an identity-related action. Captures who did what, when, where, and the outcome. See 38 defined AuditAction values.

**Audit Trail (مسار التدقيق)**
The complete ordered collection of all identity audit events. Provides non-repudiation and compliance evidence.

### B

**Bootstrap (الإقلاع)**
The initial seed process that creates the root ministry organization and master admin accounts. Generates bootstrap_started and bootstrap_completed audit events.

**Break-Glass (كسر الزجاج)**
Emergency access procedure that bypasses normal access controls in critical situations. All break-glass actions are audited with elevated priority.

### C

**Citizen Identity (هوية المواطن)**
An IdentityRecord with type `citizen`. Represents a general population identity verified through national ID or civil registry.

**Credential (معتمد)**
An authentication factor stored for an account. Types: password, passkey, FIDO2, OTP secret, authenticator app, API key, certificate, smart card, biometric, OAuth2 token, SAML assertion.

**Credential Type (نوع المعتمد)**
The kind of authentication credential. See CredentialType enum with 11 values.

### D

**Device (جهاز)**
A known physical or virtual device (browser, mobile, workstation) associated with a Person. Identified by a unique device fingerprint. Supports trust lifecycle and remote locking.

**Device Fingerprint (بصمة الجهاز)**
A unique identifier derived from device characteristics (CPU, GPU, RAM, OS, display, browser). Used to recognize known devices without cookies.

**Device Trust (ثقة الجهاز)**
Trust level assigned to a device. Trusted devices may have reduced MFA requirements. Unknown devices trigger additional verification.

### E

**Emergency Assignment (تعيين طارئ)**
An assignment created during an emergency situation. Has a limited duration and may bypass normal MFA requirements.

**Employment (توظيف)**
A work relationship between a Person and an Organization. Tracks position, department, start/end dates, contract type, supervisor, and transfer history. A person can have multiple concurrent employments.

**Employment Status (حالة التوظيف)**
`active` — currently employed. `on_leave` — temporarily absent. `suspended` — administrative suspension. `terminated` — employment ended. `retired` — retired. `transferred` — moved to another organization.

**Enterprise Account (حساب المؤسسة)**
An organization-level credential for system-to-system integration. Supports API keys, OAuth2 client credentials, digital certificates, and digital signatures. Belongs to an Organization, not to a Person.

**External Federation (اتحاد خارجي)**
An IdentityType for identities verified through an external identity provider (e.g., WHO, other national health systems).

### G

**Government Workforce Identity (هوية القوى العاملة الحكومية)**
An IdentityRecord with type `government_workforce`. Represents a government employee identity, typically verified through HR systems.

**Guest Identity (هوية ضيف)**
An IdentityRecord with type `guest`. Represents temporary external visitors, auditors, or researchers.

### H

**Health ID (معرف صحي)**
A national health identifier assigned by the SNDHS system. Stored on Person and indexed for lookup.

### I

**Identity (هوية)**
A set of verifiable claims about a Person in a specific context. One Person can have multiple Identities (citizen, government workforce, private workforce, etc.). Each Identity has a type, status, issuance date, and optional expiry.

**Identity Type (نوع الهوية)**
Classification of an identity claim: `citizen`, `government_workforce`, `private_workforce`, `enterprise`, `machine`, `temporary`, `guest`, `external_federation`.

**Identity Verification (التحقق من الهوية)**
The process of confirming that an identity claim is genuine. Methods: in_person, nid_check, biometric, federation, OTP, video_call.

**Impossible Travel (سفر مستحيل)**
A security detection mechanism that flags logins from geographically distant locations within impossibly short timeframes. Detects credential theft.

### J

**JTI (JWT ID)**
Unique identifier for each JWT token. Used for token blacklisting, session correlation, and refresh token rotation. Generated as UUID v4.

**JWT (JSON Web Token)**
Token format used for access and refresh tokens. Signed with HS256 (HMAC-SHA256). Access tokens expire in 15 minutes, refresh tokens in 7 days.

### L

**License (ترخيص)**
A professional license or certification (medical, laboratory, pharmacy, nursing, etc.). Tracks license number, issuing authority, board certification, degree information, and continuing education credits.

**License Status (حالة الترخيص)**
`active` — valid. `expired` — past expiry date. `suspended` — temporarily invalid. `revoked` — permanently invalid. `pending` — awaiting verification.

### M

**Machine Identity (هوية الآلة)**
A non-human identity for servers, lab instruments, IoT devices, and workstations. Tracks machine type, serial number, MAC address, certificates, and heartbeat status.

**MFA (المصادقة متعددة العوامل)**
Multi-Factor Authentication. Supported via TOTP authenticator apps, with architecture support for FIDO2, passkeys, and smart cards through the Credential model.

### N

**National ID (الرقم الوطني)**
Iraqi national identification number. Never stored in plaintext — stored as HMAC-SHA256 hash in `national_id_hash`.

**NIAM (NIAM Is Access Management)**
National Identity & Access Management Platform. The sovereign identity provider for the GULA National Digital Health Platform.

**NIAMOrganization (منظمة NIAM)**
The organization model representing any entity in the national healthcare hierarchy. Supports tree structure via parent_org_id, 19 organization types, bilingual names, geographic scoping, and FHIR integration.

### O

**Organization (منظمة)**
An entity in the national healthcare hierarchy. Types include ministry, directorate, hospital, laboratory, health center, blood bank, university, pharmacy, and more. Forms a tree via parent-child relationships.

**Organization Type (نوع المنظمة)**
One of 19 defined types: ministry, directorate, government_hospital, private_hospital, primary_healthcare_sector, health_center, government_laboratory, private_laboratory, blood_bank, forensic_medicine, university, research_center, insurance_company, ngo, supplier, vendor, medical_company, pharmacy, external_authority.

### P

**Password Expiry (انتهاء صلاحية كلمة المرور)**
Passwords automatically expire after 90 days (`PASSWORD_EXPIRY_DAYS`). Expired passwords require change on next login.

**Person (شخص)**
The fundamental entity — a natural human being. Contains biographical data (name, birth date, nationality), contact information, emergency contacts, and unique identifiers (national ID hash, health ID, passport number). A Person exists once in the system.

**Policy (سياسة)**
A set of ABAC (Attribute-Based Access Control) rules defining who can perform which actions on which resources under what conditions. Stored as JSON conditions. Supports allow/deny with priority-based resolution.

**Policy Effect (تأثير السياسة)**
The outcome of a policy evaluation: `allow` (permit the action) or `deny` (block the action).

**Private Workforce Identity (هوية القوى العاملة الخاصة)**
An IdentityRecord with type `private_workforce`. Represents private sector healthcare workers.

**Professional License (الترخيص المهني)**
See License.

### R

**RBAC (التحكم في الوصول على أساس الدور)**
Role-Based Access Control. Implemented through the Assignment model — each assignment grants a role_id to a person at a specific organizational scope.

**Refresh Token Rotation (تدوير رمز التحديث)**
On every token refresh, the old session is soft-deleted and a new session with new tokens is created. Old refresh tokens cannot be reused.

**Role (دور)**
A named set of permissions. Assigned to persons through Assignment records. Examples: lab_director, lab_technician, pharmacist, clinician, admin.

### S

**Session (جلسة)**
An authenticated login session. Created on successful login, terminated on logout or expiry. Tracks token JTIs, IP, user agent, device, location, and risk score.

**Session Termination (إنهاء الجلسة)**
Ending a session with a recorded reason and terminator. Reasons: user_logout, user_logout_all, session_expired, password_changed, account_locked, account_deactivated, admin_terminated, security_breach.

**Soft Delete (الحذف الناعم)**
A deletion pattern where records are marked as inactive (`is_active=False`) rather than physically deleted. All NIAM queries filter `is_active=True` by default. Provides data recovery and audit trail.

**SNDHS (النظام الصحي الرقمي الوطني)**
Iraqi National Health Data System. NIAM integrates with SNDHS for health IDs and national identity verification.

### T

**Temporary Identity (هوية مؤقتة)**
An IdentityRecord with type `temporary`. Short-term identity with an expiry date.

**Timing-Safe Login (تسجيل الدخول الآمن زمنيًا)**
Login mechanism that uses a pre-computed dummy bcrypt hash to prevent user enumeration through timing side-channel attacks.

**TOTP (كلمة المرور لمرة واحدة المستندة إلى الوقت)**
Time-based One-Time Password. Used for MFA via authenticator apps.

### U

**ULID**
Universally Unique Lexicographically Sortable Identifier. NIAM uses 26-character uppercase hex ULIDs as primary keys (derived from UUID v4, no hyphens). Example: `01ARZ3NDEKTSV4RRFFQ69G5FAV`.

**UserSession (جلسة المستخدم)**
See Session.

---

## Arabic-English Term Mapping

| العربية | English |
|---|---|
| إدارة الهوية والوصول الوطنية | NIAM (National Identity & Access Management) |
| شخص | Person |
| هوية | Identity |
| حساب | Account |
| منظمة | Organization |
| توظيف | Employment |
| تعيين | Assignment |
| جلسة | Session |
| جهاز | Device |
| معتمد | Credential |
| ترخيص | License |
| هوية الآلة | Machine Identity |
| سياسة | Policy |
| حدث التدقيق | Audit Event |
| حساب المؤسسة | Enterprise Account |
| مفتاح API | API Key |
| بصمة الجهاز | Device Fingerprint |
| قفل الحساب | Account Lockout |
| المصادقة متعددة العوامل | MFA (Multi-Factor Authentication) |
| التحقق من الهوية | Identity Verification |
| الحذف الناعم | Soft Delete |
| دور | Role |
| كسر الزجاج | Break-Glass |
| الرقم الوطني | National ID |
| معرف صحي | Health ID |
| النظام الصحي الرقمي الوطني | SNDHS |
| المفتاح العام | Public Key |
| الشهادة الرقمية | Digital Certificate |
| التوقيع الرقمي | Digital Signature |
