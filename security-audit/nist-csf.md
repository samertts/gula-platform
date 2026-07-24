# NIST Cybersecurity Framework (CSF) 2.0 Assessment

## GOVERN (GV) — Establish cybersecurity oversight

| Subcategory | Status | Evidence |
|-------------|--------|----------|
| GV.OC-01: Organizational context | ✅ Partial | Architecture docs exist but no threat model |
| GV.RM-01: Risk management | ❌ Missing | No formal risk register |
| GV.SC-01: Supply chain | ❌ Missing | No supplier security assessment |
| GV.SC-02: Third-party dependencies | ❌ Missing | Dependencies tracked but no risk assessment |

## IDENTIFY (ID) — Understand current cybersecurity risks

| Subcategory | Status | Evidence |
|-------------|--------|----------|
| ID.AM-01: Physical devices | ✅ Partial | Docker/K8s inventory exists |
| ID.AM-02: Software platforms | ✅ Partial | Dependency lists exist |
| ID.AM-03: Business processes | ❌ Missing | No critical process mapping |
| ID.AM-04: Information assets | ❌ Missing | No data flow diagrams |
| ID.AM-05: Data classifications | ✅ Present | Data classification labels exist |
| ID.AM-07: Third-party services | ❌ Missing | No third-party inventory |
| ID.RA-01: Vulnerability management | ❌ Missing | No formal vulnerability scanning |
| ID.RA-02: Threat intelligence | ❌ Missing | No threat feed integration |
| ID.RA-03: Risk assessment | ❌ Missing | No risk assessment process |

## PROTECT (PR) — Implement safeguards

| Subcategory | Status | Evidence |
|-------------|--------|----------|
| PR.AA-01: Identities and credentials | ✅ Partial | JWT, OAuth2, SAML, WebAuthn |
| PR.AA-02: Physical access | ✅ Partial | Docker network isolation |
| PR.AA-03: Remote access | ❌ Missing | No VPN requirement documented |
| PR.AA-04: Access permissions | ✅ Good | RBAC + ABAC + Consent enforcement |
| PR.AA-05: Privileged accounts | ❌ Missing | No PAM integration |
| PR.AA-06: Identity proofing | ❌ Missing | No identity verification |
| PR.AT-01: Awareness training | ❌ Missing | No training program |
| PR.DS-01: Data-at-rest protection | ❌ Missing | No encryption at rest |
| PR.DS-02: Data-in-transit protection | ✅ Partial | TLS configured (not in Terraform ALB) |
| PR.DS-08: Data integrity | ✅ Partial | Audit anchors for tamper detection |
| PR.DS-09: Data backup | ✅ Partial | Backup configuration exists |
| PR.PS-01: Configuration management | ❌ Missing | No CMDB |
| PR.PS-02: Software integrity | ❌ Missing | No image signing |
| PR.PS-03: Technical vulnerabilities | ❌ Missing | No vulnerability scanning pipeline |
| PR.PS-05: Log management | ✅ Partial | Structured logging exists |

## DETECT (DE) — Find cybersecurity events

| Subcategory | Status | Evidence |
|-------------|--------|----------|
| DE.AE-01: Baseline of network ops | ❌ Missing | No network baseline |
| DE.AE-02: Event detection | ✅ Partial | Alertmanager configured |
| DE.AE-03: Event correlation | ❌ Missing | No SIEM |
| DE.AE-05: Incident alert thresholds | ✅ Partial | Alert rules exist |
| DE.CM-01: Network monitoring | ❌ Missing | No NIDS |
| DE.CM-02: Physical monitoring | ❌ Missing | No physical security |
| DE.CM-03: Personnel monitoring | ❌ Missing | No UEBA |
| DE.CM-04: Malware detection | ❌ Missing | No antivirus/EDR |
| DE.CM-05: Unauthorized connections | ❌ Missing | No network ACLs |
| DE.CM-06: Application monitoring | ✅ Partial | Health endpoints |
| DE.CM-07: Cloud monitoring | ❌ Missing | No cloud security monitoring |
| DE.CM-08: Vulnerability scans | ❌ Missing | No automated scanning |

## RESPOND (RS) — Take action

| Subcategory | Status | Evidence |
|-------------|--------|----------|
| RS.MA-01: Incident response plan | ❌ Missing | No IR plan found |
| RS.MA-02: Incident handling | ❌ Missing | No incident playbooks |
| RS.MA-03: Incident reporting | ❌ Missing | No reporting process |
| RS.MA-04: Incident coordination | ❌ Missing | No coordination process |
| RS.AN-01: Incident analysis | ❌ Missing | No forensic capability |
| RS.AN-03: Incident classification | ❌ Missing | No classification taxonomy |
| RS.CO-01: Internal communications | ✅ Partial | Alerting configured |
| RS.CO-02: External communications | ❌ Missing | No breach notification process |
| RS.CO-03: Stakeholder reporting | ❌ Missing | No stakeholder plan |
| RS.IM-01: Incident improvement | ❌ Missing | No lessons-learned process |
| RS.IM-02: Incident response updates | ❌ Missing | No update process |

## RECOVER (RC) — Restore capabilities

| Subcategory | Status | Evidence |
|-------------|--------|----------|
| RC.RP-01: Recovery plan | ❌ Missing | No DR plan found |
| RC.IM-01: Recovery improvements | ❌ Missing | No recovery exercises |
| RC.IM-02: Communication updates | ❌ Missing | No communication plan |
| RC.CO-01: Internal communications | ❌ Missing | No recovery communication |
| RC.CO-02: External communications | ❌ Missing | No external comms plan |
| RC.CO-03: Recovery coordination | ❌ Missing | No coordination plan |

## Overall NIST CSF Score: ~25%
