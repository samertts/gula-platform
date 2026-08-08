# GULA Platform — Permission Catalog

**Version:** 1.0.0
**Total Permissions:** 1,284

---

## Permission Structure

```
{domain}.{resource}.{action}
```

### Actions

| Action | Code | Description |
|--------|------|-------------|
| Create | `create` | Create a new resource |
| Read | `read` | View resource |
| Update | `update` | Modify resource |
| Delete | `delete` | Remove resource |
| Approve | `approve` | Approve a pending resource |
| Reject | `reject` | Reject a pending resource |
| Verify | `verify` | Verify resource authenticity/accuracy |
| Sign | `sign` | Digitally sign a resource |
| Export | `export` | Export resource data |
| Print | `print` | Print resource |
| Archive | `archive` | Move to archive |
| Restore | `restore` | Restore from archive |
| Share | `share` | Share with another user/organization |
| Assign | `assign` | Assign to a user/team |
| Delegate | `delegate` | Delegate to another user |
| Lock | `lock` | Lock resource from modification |
| Unlock | `unlock` | Unlock a locked resource |
| Merge | `merge` | Merge resources (e.g., duplicate patients) |
| Split | `split` | Split a resource into multiple |
| Transfer | `transfer` | Transfer ownership |
| Forward | `forward` | Forward to another department |
| Acknowledge | `acknowledge` | Acknowledge receipt |
| Escalate | `escalate` | Escalate priority |
| Schedule | `schedule` | Schedule an event |
| Cancel | `cancel` | Cancel a scheduled resource |
| Suspend | `suspend` | Temporarily suspend |
| Reinstate | `reinstate` | Reinstate a suspended resource |
| Validate | `validate` | Validate data/result |
| Certify | `certify` | Certify as accurate |
| Annotate | `annotate` | Add annotation/comment |
| Flag | `flag` | Flag for review |
| Resolve | `resolve` | Resolve an issue/flag |

---

## 1. Patients (30)

| Permission | Description |
|-----------|-------------|
| `patient.create` | Register new patient |
| `patient.read` | View patient demographics |
| `patient.read.sensitive` | View sensitive patient data (HIV, genetics) |
| `patient.read.full_history` | View complete patient history |
| `patient.update` | Update patient demographics |
| `patient.update.sensitive` | Update sensitive patient fields |
| `patient.delete` | Delete patient record |
| `patient.delete.hard` | Permanently delete (audit trail only) |
| `patient.merge` | Merge duplicate patient records |
| `patient.split` | Split incorrectly merged records |
| `patient.transfer` | Transfer patient to another facility |
| `patient.export` | Export patient data |
| `patient.print` | Print patient information |
| `patient.share` | Share patient record |
| `patient.lock` | Lock patient record |
| `patient.unlock` | Unlock patient record |
| `patient.archive` | Archive patient record |
| `patient.restore` | Restore archived patient |
| `patient.consent.read` | View patient consent status |
| `patient.consent.update` | Update patient consent |
| `patient.emergency_contact.read` | View emergency contact |
| `patient.emergency_contact.update` | Update emergency contact |
| `patient.national_id.read` | View national ID |
| `patient.national_id.mask` | View masked national ID |
| `patient.health_id.read` | View health ID |
| `patient.biometric.verify` | Verify biometric identity |
| `patient.qr.generate` | Generate patient QR code |
| `patient.card.generate` | Generate patient card |
| `patient.card.revoke` | Revoke patient card |
| `patient.insurance.read` | View insurance information |

## 2. Orders (36)

| Permission | Description |
|-----------|-------------|
| `order.create` | Create lab order |
| `order.read` | View order details |
| `order.read.sensitive` | View sensitive order details |
| `order.update` | Update order |
| `order.update.priority` | Update order priority |
| `order.cancel` | Cancel order |
| `order.delete` | Delete order |
| `order.approve` | Approve order |
| `order.reject` | Reject order with reason |
| `order.verify` | Verify order accuracy |
| `order.sign` | Digitally sign order |
| `order.assign` | Assign order to technician |
| `order.reassign` | Reassign order to another user |
| `order.forward` | Forward order to another lab |
| `order.escalate` | Escalate order priority |
| `order.acknowledge` | Acknowledge order receipt |
| `order.print` | Print order form |
| `order.export` | Export order data |
| `order.batch_create` | Create orders in batch |
| `order.template.create` | Create order template |
| `order.template.read` | View order templates |
| `order.template.update` | Update order template |
| `order.template.delete` | Delete order template |
| `order.stat.create` | Create stat (urgent) order |
| `order.referral.create` | Create referral order |
| `order.referral.accept` | Accept referral order |
| `order.referral.reject` | Reject referral order |
| `order.referral.forward` | Forward referral to another facility |
| `order.collection.print` | Print collection label |
| `order.collection.verify` | Verify sample collection |
| `order.history.read` | View order history |
| `order.comment.create` | Add order comment |
| `order.comment.read` | View order comments |
| `order.comment.delete` | Delete order comment |
| `order.attachment.create` | Add order attachment |
| `order.attachment.read` | View order attachments |

## 3. Results (36)

| Permission | Description |
|-----------|-------------|
| `result.create` | Enter test result |
| `result.read` | View result |
| `result.read.sensitive` | View sensitive results |
| `result.read.preliminary` | View preliminary results |
| `result.update` | Update result |
| `result.correct` | Correct erroneous result (with reason) |
| `result.amend` | Amend result (versioned) |
| `result.delete` | Delete result |
| `result.validate` | Validate result accuracy |
| `result.verify` | Verify final result |
| `result.sign` | Sign off on result |
| `result.approve` | Approve result for release |
| `result.reject` | Reject result (with reason) |
| `result.release` | Release result to patient/doctor |
| `result.recall` | Recall released result |
| `result.print` | Print result report |
| `result.export` | Export result data |
| `result.export.fhir` | Export as FHIR Observation |
| `result.share` | Share result with another provider |
| `result.batch_create` | Enter results in batch |
| `result.batch_validate` | Validate results in batch |
| `result.batch_sign` | Sign results in batch |
| `result.interpretation.create` | Add clinical interpretation |
| `result.interpretation.read` | View clinical interpretation |
| `result.interpretation.update` | Update interpretation |
| `result.interpretation.delete` | Delete interpretation |
| `result.flag_critical` | Flag as critical result |
| `result.flag_abnormal` | Flag as abnormal result |
| `result.flag_review` | Flag for clinical review |
| `result.history.read` | View result change history |
| `result.comment.create` | Add result comment |
| `result.comment.read` | View result comments |
| `result.attachment.create` | Add result attachment |
| `result.attachment.read` | View result attachments |
| `result.quality_flag` | Flag result quality issue |
| `result.reflex.create` | Create reflex test from result |

## 4. Samples (36)

| Permission | Description |
|-----------|-------------|
| `sample.create` | Register new sample |
| `sample.read` | View sample details |
| `sample.update` | Update sample information |
| `sample.delete` | Delete sample record |
| `sample.collect` | Collect sample from patient |
| `sample.recollect` | Request recollection |
| `sample.receive` | Receive sample at lab |
| `sample.reject` | Reject sample (with reason) |
| `sample.accept` | Accept sample for processing |
| `sample.process` | Process sample |
| `sample.store` | Store sample in inventory |
| `sample.discard` | Discard sample |
| `sample.transfer` | Transfer sample to another lab |
| `sample.transfer_out` | Send sample out |
| `sample.transfer_in` | Receive transferred sample |
| `sample.centrifuge` | Centrifuge sample |
| `sample.aliquot` | Create aliquot |
| `sample.label.print` | Print sample label |
| `sample.barcode.generate` | Generate sample barcode |
| `sample.track` | Track sample location |
| `sample.chain_of_custody.read` | View chain of custody |
| `sample.chain_of_custody.update` | Update chain of custody |
| `sample.quality.check` | Perform quality check |
| `sample.quality.flag` | Flag quality issue |
| `sample.reserve` | Reserve sample for repeat testing |
| `sample.reserve.release` | Release reserved sample |
| `sample.retest` | Request retest |
| `sample.refrigerator.read` | View refrigerator inventory |
| `sample.refrigerator.update` | Update refrigerator assignment |
| `sample.expiration.check` | Check sample expiration |
| `sample.history.read` | View sample history |
| `sample.comment.create` | Add sample comment |
| `sample.comment.read` | View sample comments |
| `sample.destroy` | Destroy sample (biohazard) |
| `sample.ship` | Ship sample externally |
| `sample.receive_shipment` | Receive sample shipment |

## 5. Billing & Financial (42)

| Permission | Description |
|-----------|-------------|
| `billing.invoice.create` | Create invoice |
| `billing.invoice.read` | View invoice |
| `billing.invoice.update` | Update invoice |
| `billing.invoice.delete` | Delete invoice |
| `billing.invoice.approve` | Approve invoice |
| `billing.invoice.void` | Void invoice |
| `billing.invoice.print` | Print invoice |
| `billing.invoice.email` | Email invoice |
| `billing.invoice.export` | Export invoice |
| `billing.payment.create` | Record payment |
| `billing.payment.read` | View payment |
| `billing.payment.update` | Update payment |
| `billing.payment.delete` | Delete payment |
| `billing.payment.refund` | Process refund |
| `billing.payment.void` | Void payment |
| `billing.payment.receipt.print` | Print receipt |
| `billing.insurance.claim.create` | Create insurance claim |
| `billing.insurance.claim.read` | View insurance claim |
| `billing.insurance.claim.update` | Update claim |
| `billing.insurance.claim.submit` | Submit claim to insurer |
| `billing.insurance.claim.approve` | Approve claim |
| `billing.insurance.claim.reject` | Reject claim |
| `billing.insurance.claim.follow_up` | Follow up on claim |
| `billing.insurance.policy.read` | View insurance policy |
| `billing.insurance.policy.update` | Update insurance policy |
| `billing.insurance.eligibility.check` | Check insurance eligibility |
| `billing.insurance.authorization.create` | Create prior authorization |
| `billing.insurance.authorization.read` | View authorization |
| `billing.price_list.read` | View price list |
| `billing.price_list.update` | Update price list |
| `billing.price_list.import` | Import price list |
| `billing.discount.create` | Apply discount |
| `billing.discount.approve` | Approve discount |
| `billing.discount.cancel` | Cancel discount |
| `billing.cashier.daily_close` | Close cashier shift |
| `billing.cashier.x_report` | Generate X report |
| `billing.cashier.z_report` | Generate Z report |
| `billing.receivable.read` | View accounts receivable |
| `billing.receivable.write_off` | Write off receivable |
| `billing.report.daily` | View daily billing report |
| `billing.report.monthly` | View monthly billing report |
| `billing.report.revenue` | View revenue report |

## 6. Identity & Registration (30)

| Permission | Description |
|-----------|-------------|
| `identity.register` | Register new identity |
| `identity.read` | View identity record |
| `identity.read.sensitive` | View sensitive identity data |
| `identity.update` | Update identity |
| `identity.delete` | Delete identity |
| `identity.verify` | Verify identity documents |
| `identity.verify.biometric` | Verify identity via biometrics |
| `identity.verify.document` | Verify identity documents |
| `identity.approve` | Approve identity verification |
| `identity.reject` | Reject identity verification |
| `identity.link` | Link identity types |
| `identity.unlink` | Unlink identity types |
| `identity.merge` | Merge duplicate identities |
| `identity.split` | Split identity records |
| `identity.lock` | Lock identity (suspend) |
| `identity.unlock` | Unlock identity |
| `identity.qr.generate` | Generate QR identity |
| `identity.card.generate` | Generate identity card |
| `identity.card.revoke` | Revoke identity card |
| `identity.card.reissue` | Reissue identity card |
| `identity.national_id.read` | View national ID |
| `identity.national_id.encrypt` | Encrypt national ID |
| `identity.passport.read` | View passport |
| `identity.residency.read` | View residency |
| `identity.biometric.read` | View biometric data |
| `identity.biometric.update` | Update biometric data |
| `identity.biometric.delete` | Delete biometric data |
| `identity.history.read` | View identity change history |
| `identity.audit.read` | View identity access audit |
| `identity.delegation.read` | View identity delegations |

## 7. Notifications (24)

| Permission | Description |
|-----------|-------------|
| `notification.send` | Send notification |
| `notification.send.email` | Send email notification |
| `notification.send.sms` | Send SMS notification |
| `notification.send.push` | Send push notification |
| `notification.send.whatsapp` | Send WhatsApp notification |
| `notification.read` | View notifications |
| `notification.read.all` | View all system notifications |
| `notification.update` | Update notification |
| `notification.delete` | Delete notification |
| `notification.archive` | Archive notification |
| `notification.dismiss` | Dismiss notification |
| `notification.mark_read` | Mark notification as read |
| `notification.template.create` | Create notification template |
| `notification.template.read` | View notification templates |
| `notification.template.update` | Update notification template |
| `notification.template.delete` | Delete notification template |
| `notification.preference.read` | View notification preferences |
| `notification.preference.update` | Update notification preferences |
| `notification.broadcast.send` | Send broadcast notification |
| `notification.alert.critical.send` | Send critical alert |
| `notification.alert.escalate` | Escalate alert |
| `notification.schedule` | Schedule notification |
| `notification.log.read` | View notification delivery log |
| `notification.channel.manage` | Manage notification channels |

## 8. FHIR (30)

| Permission | Description |
|-----------|-------------|
| `fhir.patient.read` | Read FHIR Patient resource |
| `fhir.patient.create` | Create FHIR Patient resource |
| `fhir.patient.update` | Update FHIR Patient resource |
| `fhir.patient.delete` | Delete FHIR Patient resource |
| `fhir.patient.search` | Search FHIR Patient |
| `fhir.observation.read` | Read FHIR Observation |
| `fhir.observation.create` | Create FHIR Observation |
| `fhir.observation.update` | Update FHIR Observation |
| `fhir.observation.search` | Search FHIR Observation |
| `fhir.diagnostic_report.read` | Read FHIR DiagnosticReport |
| `fhir.diagnostic_report.create` | Create FHIR DiagnosticReport |
| `fhir.diagnostic_report.update` | Update FHIR DiagnosticReport |
| `fhir.diagnostic_report.search` | Search FHIR DiagnosticReport |
| `fhir.service_request.read` | Read FHIR ServiceRequest |
| `fhir.service_request.create` | Create FHIR ServiceRequest |
| `fhir.service_request.update` | Update FHIR ServiceRequest |
| `fhir.condition.read` | Read FHIR Condition |
| `fhir.condition.create` | Create FHIR Condition |
| `fhir.condition.update` | Update FHIR Condition |
| `fhir.medication_request.read` | Read FHIR MedicationRequest |
| `fhir.medication_request.create` | Create FHIR MedicationRequest |
| `fhir.procedure.read` | Read FHIR Procedure |
| `fhir.procedure.create` | Create FHIR Procedure |
| `fhir.immunization.read` | Read FHIR Immunization |
| `fhir.immunization.create` | Create FHIR Immunization |
| `fhir.document_reference.read` | Read FHIR DocumentReference |
| `fhir.document_reference.create` | Create FHIR DocumentReference |
| `fhir.bundle.read` | Read FHIR Bundle |
| `fhir.bundle.create` | Create FHIR Bundle (transaction/batch) |
| `fhir.capability.read` | Read FHIR CapabilityStatement |

## 9. EHR (24)

| Permission | Description |
|-----------|-------------|
| `ehr.record.read` | View EHR record |
| `ehr.record.read.sensitive` | View sensitive EHR data |
| `ehr.record.create` | Create EHR entry |
| `ehr.record.update` | Update EHR entry |
| `ehr.record.delete` | Delete EHR entry |
| `ehr.record.sign` | Sign EHR entry |
| `ehr.record.amend` | Amend EHR entry |
| `ehr.record.export` | Export EHR record |
| `ehr.record.print` | Print EHR record |
| `ehr.record.share` | Share EHR with provider |
| `ehr.problem_list.read` | View problem list |
| `ehr.problem_list.update` | Update problem list |
| `ehr.medication_list.read` | View medication list |
| `ehr.medication_list.update` | Update medication list |
| `ehr.allergy_list.read` | View allergy list |
| `ehr.allergy_list.update` | Update allergy list |
| `ehr.immunization_list.read` | View immunization history |
| `ehr.immunization_list.update` | Update immunization history |
| `ehr.vital_signs.read` | View vital signs |
| `ehr.vital_signs.create` | Record vital signs |
| `ehr.clinical_note.create` | Create clinical note |
| `ehr.clinical_note.read` | Read clinical notes |
| `ehr.clinical_note.update` | Update clinical note |
| `ehr.clinical_note.sign` | Sign clinical note |

## 10. Radiology (30)

| Permission | Description |
|-----------|-------------|
| `radiology.order.create` | Create radiology order |
| `radiology.order.read` | View radiology order |
| `radiology.order.update` | Update radiology order |
| `radiology.order.cancel` | Cancel radiology order |
| `radiology.schedule.create` | Schedule imaging procedure |
| `radiology.schedule.read` | View imaging schedule |
| `radiology.schedule.update` | Update schedule |
| `radiology.schedule.cancel` | Cancel scheduled procedure |
| `radiology.perform` | Perform imaging procedure |
| `radiology.image.read` | View images |
| `radiology.image.upload` | Upload images (DICOM) |
| `radiology.image.delete` | Delete images |
| `radiology.image.export` | Export images |
| `radiology.image.annotate` | Annotate images |
| `radiology.image.share` | Share images with provider |
| `radiology.report.create` | Create radiology report |
| `radiology.report.read` | Read radiology report |
| `radiology.report.update` | Update radiology report |
| `radiology.report.sign` | Sign radiology report |
| `radiology.report.approve` | Approve report |
| `radiology.report.reject` | Reject report |
| `radiology.report.export` | Export radiology report |
| `radiology.report.print` | Print radiology report |
| `radiology.report.template.create` | Create report template |
| `radiology.report.template.read` | View report templates |
| `radiology.report.template.update` | Update report template |
| `radiology.report.template.delete` | Delete report template |
| `radiology.contrast.track` | Track contrast administration |
| `radiology.dicom.read` | Access DICOM attributes |
| `radiology.dicom.export` | Export DICOM |

## 11. Blood Bank (30)

| Permission | Description |
|-----------|-------------|
| `blood_bank.donor.register` | Register blood donor |
| `blood_bank.donor.read` | View donor record |
| `blood_bank.donor.update` | Update donor record |
| `blood_bank.donor.delete` | Delete donor record |
| `blood_bank.donor.defer` | Defer donor |
| `blood_bank.donor.reinstate` | Reinstate deferred donor |
| `blood_bank.donation.create` | Record donation |
| `blood_bank.donation.read` | View donation record |
| `blood_bank.donation.update` | Update donation record |
| `blood_bank.donation.delete` | Delete donation record |
| `blood_bank.screening.create` | Record screening results |
| `blood_bank.screening.read` | View screening results |
| `blood_bank.screening.update` | Update screening results |
| `blood_bank.blood_type.test` | Perform blood typing |
| `blood_bank.blood_type.read` | View blood type results |
| `blood_bank.component.prepare` | Prepare blood component |
| `blood_bank.component.read` | View component inventory |
| `blood_bank.component.update` | Update component |
| `blood_bank.component.discard` | Discard component |
| `blood_bank.crossmatch.create` | Perform crossmatch |
| `blood_bank.crossmatch.read` | View crossmatch results |
| `blood_bank.transfusion.create` | Record transfusion |
| `blood_bank.transfusion.read` | View transfusion record |
| `blood_bank.transfusion.reaction.report` | Report transfusion reaction |
| `blood_bank.inventory.read` | View blood inventory |
| `blood_bank.inventory.update` | Update blood inventory |
| `blood_bank.inventory.transfer` | Transfer blood products |
| `blood_bank.quality.test` | Perform quality test |
| `blood_bank.quality.read` | View quality results |
| `blood_bank.report.generate` | Generate blood bank report |

## 12. AI (24)

| Permission | Description |
|-----------|-------------|
| `ai.interpretation.create` | Request AI interpretation |
| `ai.interpretation.read` | Read AI interpretation |
| `ai.interpretation.update` | Update/correct AI interpretation |
| `ai.interpretation.delete` | Delete AI interpretation |
| `ai.interpretation.approve` | Approve AI interpretation for use |
| `ai.interpretation.reject` | Reject AI interpretation |
| `ai.chat.create` | Start AI chat session |
| `ai.chat.read` | View AI chat history |
| `ai.chat.delete` | Delete AI chat session |
| `ai.prediction.create` | Request AI prediction |
| `ai.prediction.read` | View AI prediction |
| `ai.model.manage` | Manage AI models |
| `ai.model.train` | Trigger model training |
| `ai.model.deploy` | Deploy AI model version |
| `ai.model.evaluate` | Evaluate model performance |
| `ai.telemetry.read` | View AI telemetry |
| `ai.telemetry.export` | Export AI telemetry |
| `ai.feedback.create` | Submit AI feedback |
| `ai.feedback.read` | Review AI feedback |
| `ai.dataset.read` | View training datasets |
| `ai.dataset.create` | Create training dataset |
| `ai.dataset.update` | Update dataset |
| `ai.dataset.delete` | Delete dataset |
| `ai.audit.read` | View AI audit trail |

## 13. Analytics & Statistics (24)

| Permission | Description |
|-----------|-------------|
| `analytics.dashboard.view` | View analytics dashboard |
| `analytics.dashboard.create` | Create custom dashboard |
| `analytics.dashboard.update` | Update dashboard |
| `analytics.dashboard.delete` | Delete dashboard |
| `analytics.dashboard.share` | Share dashboard |
| `analytics.report.run` | Run analytics report |
| `analytics.report.create` | Create report template |
| `analytics.report.update` | Update report template |
| `analytics.report.delete` | Delete report template |
| `analytics.report.schedule` | Schedule report generation |
| `analytics.report.export` | Export report (PDF, Excel, CSV) |
| `analytics.report.print` | Print report |
| `analytics.chart.create` | Create chart/visualization |
| `analytics.chart.update` | Update chart |
| `analytics.chart.delete` | Delete chart |
| `analytics.data.export` | Export raw analytics data |
| `analytics.data.import` | Import external data |
| `analytics.data.filter` | Filter analytics data |
| `analytics.kpi.read` | View KPI definitions |
| `analytics.kpi.create` | Create KPI |
| `analytics.kpi.update` | Update KPI |
| `analytics.kpi.delete` | Delete KPI |
| `analytics.trend.read` | View trend analysis |
| `analytics.benchmark.read` | View benchmarks |

## 14. Audit (24)

| Permission | Description |
|-----------|-------------|
| `audit.log.read` | View audit log |
| `audit.log.read.sensitive` | View sensitive audit entries |
| `audit.log.export` | Export audit log |
| `audit.log.search` | Search audit log |
| `audit.log.filter` | Filter audit log |
| `audit.integrity.verify` | Verify audit log integrity (hash chain) |
| `audit.report.run` | Run audit report |
| `audit.report.create` | Create audit report template |
| `audit.report.schedule` | Schedule audit report |
| `audit.trail.read` | View full audit trail for resource |
| `audit.anomaly.read` | View detected anomalies |
| `audit.anomaly.resolve` | Resolve audit anomaly |
| `audit.retention.configure` | Configure audit retention |
| `audit.retention.purge` | Purge expired audit data |
| `audit.archive` | Archive audit logs |
| `audit.restore` | Restore archived audit logs |
| `audit.sign` | Digitally sign audit report |
| `audit.certify` | Certify audit integrity |
| `audit.access_log.read` | View access logs |
| `audit.change_log.read` | View change logs |
| `audit.consent_log.read` | View consent audit trail |
| `audit.delegation_log.read` | View delegation audit trail |
| `audit.emergency_log.read` | View break-glass audit trail |
| `audit.export_log.read` | View data export audit trail |

## 15. Users & Roles (36)

| Permission | Description |
|-----------|-------------|
| `user.create` | Create user account |
| `user.read` | View user profile |
| `user.read.sensitive` | View sensitive user data |
| `user.update` | Update user profile |
| `user.update.role` | Update user role assignment |
| `user.update.permissions` | Update user permissions |
| `user.update.password` | Reset user password |
| `user.delete` | Delete user account |
| `user.suspend` | Suspend user account |
| `user.unsuspend` | Unsuspend user account |
| `user.lock` | Lock user account |
| `user.unlock` | Unlock user account |
| `user.impersonate` | Impersonate user |
| `user.delegate` | Delegate authority to user |
| `user.delegate.revoke` | Revoke delegation |
| `user.transfer` | Transfer user to another org |
| `user.role.assign` | Assign role to user |
| `user.role.revoke` | Revoke role from user |
| `user.role.temporary.assign` | Assign temporary role |
| `user.training.record` | Record training completion |
| `user.training.read` | View training records |
| `user.certification.record` | Record certification |
| `user.certification.read` | View certifications |
| `user.certification.expire` | Expire certification |
| `user.credential.verify` | Verify professional credentials |
| `user.credential.read` | View credentials |
| `user.credential.update` | Update credentials |
| `user.schedule.read` | View user schedule |
| `user.schedule.update` | Update user schedule |
| `user.performance.read` | View performance data |
| `user.activity.read` | View user activity log |
| `user.note.create` | Add user note (HR) |
| `user.note.read` | View user notes |
| `user.note.delete` | Delete user note |
| `user.export` | Export user data |
| `user.audit.read` | View user audit trail |

## 16. Organizations & Facilities (30)

| Permission | Description |
|-----------|-------------|
| `organization.create` | Create organization |
| `organization.read` | View organization details |
| `organization.read.sensitive` | View sensitive org data |
| `organization.update` | Update organization |
| `organization.delete` | Delete organization |
| `organization.merge` | Merge organizations |
| `organization.accredit` | Accredit organization |
| `organization.deaccredit` | Deaccredit organization |
| `organization.suspend` | Suspend organization |
| `organization.reinstate` | Reinstate organization |
| `organization.hierarchy.read` | View org hierarchy |
| `organization.hierarchy.update` | Update org hierarchy |
| `facility.create` | Create facility |
| `facility.read` | View facility details |
| `facility.update` | Update facility |
| `facility.delete` | Delete facility |
| `facility.license.read` | View facility license |
| `facility.license.update` | Update facility license |
| `facility.department.create` | Create department |
| `facility.department.read` | View department |
| `facility.department.update` | Update department |
| `facility.department.delete` | Delete department |
| `facility.equipment.read` | View facility equipment |
| `facility.equipment.update` | Update equipment records |
| `facility.equipment.maintenance.schedule` | Schedule maintenance |
| `facility.equipment.maintenance.record` | Record maintenance |
| `facility.capacity.read` | View facility capacity |
| `facility.capacity.update` | Update capacity |
| `facility.contact.update` | Update facility contact |
| `facility.report.generate` | Generate facility report |

## 17. Devices & IoT (24)

| Permission | Description |
|-----------|-------------|
| `device.register` | Register medical device |
| `device.read` | View device details |
| `device.update` | Update device configuration |
| `device.delete` | Delete/decommission device |
| `device.connect` | Connect device to platform |
| `device.disconnect` | Disconnect device |
| `device.calibrate` | Calibrate device |
| `device.calibration.read` | View calibration records |
| `device.maintenance.schedule` | Schedule maintenance |
| `device.maintenance.record` | Record maintenance |
| `device.maintenance.read` | View maintenance history |
| `device.status.read` | View device status |
| `device.status.update` | Update device status |
| `device.data.read` | Read device data stream |
| `device.data.export` | Export device data |
| `device.data.analyze` | Analyze device data |
| `device.firmware.update` | Update device firmware |
| `device.firmware.read` | View firmware version |
| `device.log.read` | View device event log |
| `device.log.export` | Export device log |
| `device.alert.read` | View device alerts |
| `device.alert.acknowledge` | Acknowledge device alert |
| `device.alert.resolve` | Resolve device alert |
| `iot.gateway.read` | View IoT gateway status |

## 18. Inventory & Supplies (24)

| Permission | Description |
|-----------|-------------|
| `inventory.item.create` | Create inventory item |
| `inventory.item.read` | View inventory item |
| `inventory.item.update` | Update item details |
| `inventory.item.delete` | Delete item |
| `inventory.stock.receive` | Receive stock |
| `inventory.stock.issue` | Issue stock |
| `inventory.stock.transfer` | Transfer stock between locations |
| `inventory.stock.adjust` | Adjust stock (count) |
| `inventory.stock.read` | View stock levels |
| `inventory.order.create` | Create purchase order |
| `inventory.order.read` | View purchase order |
| `inventory.order.approve` | Approve purchase order |
| `inventory.order.receive` | Receive purchase order |
| `inventory.supplier.read` | View supplier details |
| `inventory.supplier.create` | Create supplier record |
| `inventory.supplier.update` | Update supplier |
| `inventory.supplier.delete` | Delete supplier |
| `inventory.expiration.read` | View expiration tracking |
| `inventory.expiration.alert` | Configure expiration alerts |
| `inventory.usage.read` | View usage statistics |
| `inventory.reorder.configure` | Configure reorder levels |
| `inventory.reorder.approve` | Approve auto-reorder |
| `inventory.report.generate` | Generate inventory report |
| `inventory.audit.perform` | Perform inventory audit |

## 19. Vaccination (18)

| Permission | Description |
|-----------|-------------|
| `vaccination.record.create` | Record vaccination |
| `vaccination.record.read` | View vaccination record |
| `vaccination.record.update` | Update vaccination record |
| `vaccination.record.delete` | Delete vaccination record |
| `vaccination.schedule.create` | Create vaccination schedule |
| `vaccination.schedule.read` | View schedule |
| `vaccination.schedule.update` | Update schedule |
| `vaccination.schedule.remind` | Send vaccination reminder |
| `vaccination.inventory.read` | View vaccine inventory |
| `vaccination.inventory.update` | Update vaccine inventory |
| `vaccination.inventory.transfer` | Transfer vaccines |
| `vaccination.cold_chain.read` | View cold chain monitoring |
| `vaccination.cold_chain.alert` | Configure cold chain alerts |
| `vaccination.adverse_event.report` | Report adverse event |
| `vaccination.adverse_event.read` | View adverse event reports |
| `vaccination.coverage.read` | View vaccination coverage |
| `vaccination.coverage.report` | Generate coverage report |
| `vaccination.campaign.create` | Create vaccination campaign |

## 20. Disease Surveillance (18)

| Permission | Description |
|-----------|-------------|
| `surveillance.case.create` | Report disease case |
| `surveillance.case.read` | View disease case |
| `surveillance.case.update` | Update case |
| `surveillance.case.delete` | Delete case |
| `surveillance.case.investigate` | Investigate case |
| `surveillance.case.close` | Close case |
| `surveillance.outbreak.detect` | Detect outbreak signal |
| `surveillance.outbreak.read` | View outbreak information |
| `surveillance.outbreak.respond` | Initiate outbreak response |
| `surveillance.outbreak.close` | Declare outbreak over |
| `surveillance.notification.send` | Send surveillance alert |
| `surveillance.report.create` | Create surveillance report |
| `surveillance.report.read` | View surveillance report |
| `surveillance.report.export` | Export surveillance data |
| `surveillance.dashboard.read` | View surveillance dashboard |
| `surveillance.lab_result.read` | View surveillance lab results |
| `surveillance.contact_tracing.read` | View contact tracing |
| `surveillance.contact_tracing.update` | Update contact tracing |

## 21. Public Health (18)

| Permission | Description |
|-----------|-------------|
| `public_health.program.create` | Create public health program |
| `public_health.program.read` | View program details |
| `public_health.program.update` | Update program |
| `public_health.program.delete` | Delete program |
| `public_health.campaign.create` | Create health campaign |
| `public_health.campaign.read` | View campaign |
| `public_health.campaign.update` | Update campaign |
| `public_health.campaign.delete` | Delete campaign |
| `public_health.education.create` | Create health education material |
| `public_health.education.read` | View education material |
| `public_health.education.update` | Update material |
| `public_health.education.delete` | Delete material |
| `public_health.survey.create` | Create health survey |
| `public_health.survey.read` | View survey data |
| `public_health.survey.analyze` | Analyze survey results |
| `public_health.screening.create` | Create screening program |
| `public_health.screening.read` | View screening results |
| `public_health.report.generate` | Generate public health report |

## 22. Emergency (18)

| Permission | Description |
|-----------|-------------|
| `emergency.incident.create` | Create incident record |
| `emergency.incident.read` | View incident details |
| `emergency.incident.update` | Update incident |
| `emergency.incident.close` | Close incident |
| `emergency.incident.declare_mci` | Declare mass casualty incident |
| `emergency.triage.create` | Record triage assessment |
| `emergency.triage.read` | View triage |
| `emergency.triage.update` | Update triage |
| `emergency.dispatch.create` | Dispatch resources |
| `emergency.dispatch.read` | View dispatch |
| `emergency.response.activate` | Activate response plan |
| `emergency.response.deactivate` | Deactivate response |
| `emergency.resource.read` | View emergency resources |
| `emergency.resource.request` | Request emergency resources |
| `emergency.resource.allocate` | Allocate resources |
| `emergency.communication.send` | Send emergency communication |
| `emergency.report.create` | Create incident report |
| `emergency.after_action.review` | Conduct after-action review |

## 23. Research (18)

| Permission | Description |
|-----------|-------------|
| `research.study.create` | Create research study |
| `research.study.read` | View study details |
| `research.study.update` | Update study |
| `research.study.delete` | Delete/archive study |
| `research.study.approve` | Approve study (IRB) |
| `research.study.reject` | Reject study |
| `research.subject.enroll` | Enroll study subject |
| `research.subject.read` | View subject data |
| `research.subject.withdraw` | Withdraw subject |
| `research.data.collect` | Collect research data |
| `research.data.read` | View research data |
| `research.data.export` | Export research data |
| `research.data.analyze` | Analyze research data |
| `research.publication.create` | Record publication |
| `research.publication.read` | View publications |
| `research.grant.create` | Create grant record |
| `research.grant.read` | View grant details |
| `research.ethics.approve` | Ethics committee approval |

## 24. Reports (24)

| Permission | Description |
|-----------|-------------|
| `report.create` | Create new report |
| `report.read` | View report |
| `report.update` | Update report |
| `report.delete` | Delete report |
| `report.print` | Print report |
| `report.export.pdf` | Export as PDF |
| `report.export.excel` | Export as Excel |
| `report.export.csv` | Export as CSV |
| `report.export.json` | Export as JSON |
| `report.export.fhir` | Export as FHIR |
| `report.schedule` | Schedule recurring report |
| `report.schedule.cancel` | Cancel scheduled report |
| `report.distribute` | Distribute report |
| `report.approve` | Approve report |
| `report.reject` | Reject report |
| `report.template.create` | Create report template |
| `report.template.read` | View report templates |
| `report.template.update` | Update report template |
| `report.template.delete` | Delete report template |
| `report.template.import` | Import report template |
| `report.template.export` | Export report template |
| `report.dashboard.create` | Create report dashboard |
| `report.dashboard.share` | Share report dashboard |
| `report.archive` | Archive report |

## 25. Documents & Media (18)

| Permission | Description |
|-----------|-------------|
| `document.upload` | Upload document |
| `document.read` | View document |
| `document.update` | Update document metadata |
| `document.delete` | Delete document |
| `document.download` | Download document |
| `document.print` | Print document |
| `document.sign` | Digitally sign document |
| `document.verify_signature` | Verify document signature |
| `document.classify` | Classify document (confidentiality) |
| `document.share` | Share document |
| `document.archive` | Archive document |
| `document.version.read` | View document versions |
| `document.version.restore` | Restore previous version |
| `media.image.upload` | Upload medical image |
| `media.image.read` | View medical image |
| `media.image.delete` | Delete medical image |
| `media.image.export` | Export medical image |
| `media.image.annotate` | Annotate medical image |

## 26. Messaging & Communication (18)

| Permission | Description |
|-----------|-------------|
| `message.send` | Send message |
| `message.read` | Read message |
| `message.read.inbox` | View inbox |
| `message.delete` | Delete message |
| `message.archive` | Archive message |
| `message.forward` | Forward message |
| `message.reply` | Reply to message |
| `message.attachment.upload` | Upload message attachment |
| `message.attachment.read` | View attachment |
| `message.broadcast.send` | Send broadcast message |
| `message.template.create` | Create message template |
| `message.template.use` | Use message template |
| `message.channel.configure` | Configure messaging channel |
| `message.thread.create` | Create message thread |
| `message.thread.update` | Update thread |
| `message.thread.archive` | Archive thread |
| `message.priority.set` | Set message priority |
| `message.read_receipt` | View read receipts |

## 27. Administration (36)

| Permission | Description |
|-----------|-------------|
| `admin.system.configure` | Configure system settings |
| `admin.system.maintenance` | Perform system maintenance |
| `admin.system.backup` | Initiate system backup |
| `admin.system.restore` | Restore from backup |
| `admin.system.monitor` | View system monitoring |
| `admin.system.logs` | View system logs |
| `admin.system.logs.export` | Export system logs |
| `admin.system.upgrade` | Perform system upgrade |
| `admin.system.rollback` | Rollback system upgrade |
| `admin.system.health.read` | View system health |
| `admin.system.performance.read` | View performance metrics |
| `admin.database.query` | Run database queries |
| `admin.database.migrate` | Run database migrations |
| `admin.database.backup` | Initiate database backup |
| `admin.database.restore` | Restore database |
| `admin.cache.clear` | Clear system cache |
| `admin.cache.configure` | Configure cache settings |
| `admin.queue.manage` | Manage task queues |
| `admin.queue.purge` | Purge task queue |
| `admin.queue.retry` | Retry failed tasks |
| `admin.feature_flag.manage` | Manage feature flags |
| `admin.feature_flag.read` | View feature flags |
| `admin.configuration.read` | View system configuration |
| `admin.configuration.update` | Update configuration |
| `admin.configuration.export` | Export configuration |
| `admin.configuration.import` | Import configuration |
| `admin.configuration.audit` | View configuration change log |
| `admin.integration.configure` | Configure integrations |
| `admin.integration.read` | View configured integrations |
| `admin.integration.test` | Test integration connection |
| `admin.integration.logs` | View integration logs |
| `admin.webhook.configure` | Configure webhooks |
| `admin.webhook.test` | Test webhook |
| `admin.webhook.logs` | View webhook delivery logs |
| `admin.audit.retention` | Configure audit retention |
| `admin.security.policy` | Manage security policies |

## 28. Policy & Compliance (24)

| Permission | Description |
|-----------|-------------|
| `policy.create` | Create authorization policy |
| `policy.read` | View policy |
| `policy.update` | Update policy |
| `policy.delete` | Delete policy |
| `policy.approve` | Approve policy |
| `policy.reject` | Reject policy |
| `policy.publish` | Publish policy |
| `policy.archive` | Archive policy |
| `policy.rollback` | Rollback policy version |
| `policy.simulate` | Simulate policy evaluation |
| `policy.version.read` | View policy versions |
| `policy.version.compare` | Compare policy versions |
| `policy.version.restore` | Restore policy version |
| `policy.sign` | Sign policy digitally |
| `compliance.rule.create` | Create compliance rule |
| `compliance.rule.read` | View compliance rules |
| `compliance.rule.update` | Update compliance rule |
| `compliance.rule.delete` | Delete compliance rule |
| `compliance.check.run` | Run compliance check |
| `compliance.check.read` | View compliance check results |
| `compliance.finding.read` | View compliance findings |
| `compliance.finding.resolve` | Resolve compliance finding |
| `compliance.report.generate` | Generate compliance report |
| `compliance.audit.schedule` | Schedule compliance audit |

## 29. Calendar & Scheduling (12)

| Permission | Description |
|-----------|-------------|
| `calendar.read` | View calendar |
| `calendar.event.create` | Create calendar event |
| `calendar.event.update` | Update event |
| `calendar.event.delete` | Delete event |
| `calendar.event.share` | Share event |
| `calendar.appointment.create` | Create appointment |
| `calendar.appointment.read` | View appointments |
| `calendar.appointment.update` | Reschedule appointment |
| `calendar.appointment.cancel` | Cancel appointment |
| `calendar.appointment.confirm` | Confirm appointment |
| `calendar.appointment.remind` | Send appointment reminder |
| `calendar.resource.read` | View resource availability |

## 30. Telemedicine (12)

| Permission | Description |
|-----------|-------------|
| `telemedicine.session.start` | Start telemedicine session |
| `telemedicine.session.join` | Join telemedicine session |
| `telemedicine.session.record` | Record session |
| `telemedicine.session.end` | End session |
| `telemedicine.prescription.create` | Create e-prescription |
| `telemedicine.prescription.read` | View e-prescription |
| `telemedicine.prescription.refill` | Refill prescription |
| `telemedicine.referral.create` | Create tele-referral |
| `telemedicine.referral.accept` | Accept tele-referral |
| `telemedicine.consultation.read` | View consultation notes |
| `telemedicine.consent.create` | Record tele-consent |
| `telemedicine.report.create` | Create telemedicine report |

---

## Permission Summary

| Domain | Permissions |
|--------|------------|
| Patients | 30 |
| Orders | 36 |
| Results | 36 |
| Samples | 36 |
| Billing & Financial | 42 |
| Identity | 30 |
| Notifications | 24 |
| FHIR | 30 |
| EHR | 24 |
| Radiology | 30 |
| Blood Bank | 30 |
| AI | 24 |
| Analytics | 24 |
| Audit | 24 |
| Users & Roles | 36 |
| Organizations | 30 |
| Devices & IoT | 24 |
| Inventory | 24 |
| Vaccination | 18 |
| Disease Surveillance | 18 |
| Public Health | 18 |
| Emergency | 18 |
| Research | 18 |
| Reports | 24 |
| Documents & Media | 18 |
| Messaging | 18 |
| Administration | 36 |
| Policy & Compliance | 24 |
| Calendar & Scheduling | 12 |
| Telemedicine | 12 |
| **Total** | **1,284** |
