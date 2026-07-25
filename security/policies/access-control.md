# Access Control Policy

## 1. Purpose

Establish access control requirements for the GULA National Healthcare Platform
to protect patient health information (PHI) and ensure compliance with Iraqi
healthcare regulations, HIPAA, and ISO 27001.

## 2. Scope

This policy applies to all users, systems, and data within the GULA platform
including healthcare providers, administrators, patients, third-party
integrators, and system components.

## 3. Policy

### 3.1 RBAC Roles and Permissions

All access must be governed by Role-Based Access Control (RBAC) with the
following predefined roles:

- **Super Admin**: Full system access, configuration, audit review
- **Security Admin**: Security configuration, incident response, audit access
- **System Admin**: System configuration, user management, monitoring
- **Hospital Admin**: Hospital-level user and resource management
- **Laboratory Manager**: Laboratory operations, analyzer configuration
- **Physician**: Patient record read/write within assigned department
- **Nurse**: Patient record read/write within assigned ward
- **Pharmacist**: Medication order processing
- **Radiologist**: Imaging data access and reporting
- **Lab Technician**: Laboratory results entry and verification
- **Patient**: Own record access, consent management
- **Auditor**: Read-only audit log access
- **Third-party Integrator**: API access with limited scope

### 3.2 ABAC Rules

Attribute-Based Access Control (ABAC) supplements RBAC with contextual rules:

- **Department scoping**: users can only access records in their department
- **Time-based restrictions**: sensitive operations restricted to business hours
- **Location-based access**: physical location must match record jurisdiction
- **Emergency override**: break-glass procedure for emergency access (logged)
- **Consent validation**: patient consent required for non-treatment access
- **Data classification**: access level must match data classification

### 3.3 Principle of Least Privilege

- Users are granted the minimum permissions required for their role
- Permissions are reviewed quarterly and revoked when no longer needed
- Temporary privileges expire automatically after 24 hours
- Service accounts have narrowly scoped permissions with no human login

### 3.4 Separation of Duties

The following duties must be separated across different users:

- Security administration and audit review
- User creation and privilege assignment
- Patient care and system administration
- Code deployment and code review
- Financial transactions and reconciliation

### 3.5 Access Review Requirements

- User access reviews conducted quarterly
- Privileged access reviews conducted monthly
- Emergency access reviews conducted weekly
- Third-party access reviews conducted semi-annually
- All reviews documented and retained for 7 years

### 3.6 Emergency Access Procedures

1. User activates break-glass mechanism with justification
2. System generates immediate alert to security team
3. Emergency access automatically expires after 4 hours
4. Post-emergency review required within 24 hours
5. All emergency actions recorded in immutable audit log

### 3.7 Third-Party Access Controls

- Third-party access requires signed BAA (Business Associate Agreement)
- API access uses OAuth 2.0 with scoped tokens
- Third-party access reviewed semi-annually
- Access revoked immediately upon contract termination
- Third-party security assessment required annually

## 4. Enforcement

Violations of this policy are reported to the CISO and may result in:
- Access revocation
- Disciplinary action
- Legal action for unauthorized PHI access

## 5. Review

This policy is reviewed annually or after any security incident involving
access control failures.
