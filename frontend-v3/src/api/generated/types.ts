// AUTO-GENERATED — DO NOT EDIT
// Generated from backend/ models
// Run: python scripts/generate_frontend_client.py

// =============================================================================
// Domain Enums
// =============================================================================

// backend model: ScannedDocumentModel  (table: docint_documents)
export interface ScannedDocumentModel {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  labId?: unknown;
  filename?: unknown;
  mimeType?: unknown;
  sizeBytes?: unknown;
  pageCount?: unknown;
  source?: unknown;
  sourceReference?: unknown;
  storageBackend?: unknown;
  storagePath?: unknown;
  storageUri?: unknown;
  checksumSha256?: unknown;
  status?: unknown;
  priority?: unknown;
  language?: unknown;
  errorMessage?: unknown;
  retryCount?: unknown;
  metadataJson?: unknown;
  tags?: unknown;
  processedAt?: unknown;
}

// backend model: OcrResultModel  (table: docint_ocr_results)
export interface OcrResultModel {
  uuid: string;
  documentId?: unknown;
  fullText?: unknown;
  ocrEngine?: unknown;
  confidence?: unknown;
  processingTimeMs?: unknown;
  language?: unknown;
  pageCount?: unknown;
  success?: unknown;
  errorMessage?: unknown;
  metadataJson?: unknown;
}

// backend model: ExtractedEntityModel  (table: docint_entities)
export interface ExtractedEntityModel {
  uuid: string;
  documentId?: unknown;
  entityType?: unknown;
  value?: unknown;
  confidence?: unknown;
  normalizedValue?: unknown;
  sourceText?: unknown;
  pageNumber?: unknown;
  fieldName?: unknown;
  loincCode?: unknown;
  snomedCode?: unknown;
  icdCode?: unknown;
  metadataJson?: unknown;
}

// backend model: ExtractedFieldModel  (table: docint_fields)
export interface ExtractedFieldModel {
  uuid: string;
  documentId?: unknown;
  name?: unknown;
  value?: unknown;
  fieldType?: unknown;
  confidence?: unknown;
  pageNumber?: unknown;
  normalizedValue?: unknown;
  originalText?: unknown;
  language?: unknown;
  metadataJson?: unknown;
}

// backend model: ExtractedTableModel  (table: docint_tables)
export interface ExtractedTableModel {
  uuid: string;
  documentId?: unknown;
  pageNumber?: unknown;
  headers?: unknown;
  rows?: unknown;
  confidence?: unknown;
  caption?: unknown;
  metadataJson?: unknown;
}

// backend model: ClassificationResultModel  (table: docint_classifications)
export interface ClassificationResultModel {
  uuid: string;
  documentId?: unknown;
  category?: unknown;
  confidence?: unknown;
  confidenceScore?: unknown;
  subcategory?: unknown;
  alternatives?: unknown;
  method?: unknown;
  features?: unknown;
  processingTimeMs?: unknown;
  metadataJson?: unknown;
}

// backend model: PipelineResultModel  (table: docint_pipeline_results)
export interface PipelineResultModel {
  uuid: string;
  documentId?: unknown;
  phasesCompleted?: unknown;
  fhirResources?: unknown;
  knowledgeGraphEntries?: unknown;
  vectorEmbeddings?: unknown;
  searchIndexEntries?: unknown;
  totalProcessingTimeMs?: unknown;
  success?: unknown;
  errorMessage?: unknown;
  metadataJson?: unknown;
}

// backend model: DocumentVersionModel  (table: docint_versions)
export interface DocumentVersionModel {
  uuid: string;
  documentId?: unknown;
  versionNumber?: unknown;
  storagePath?: unknown;
  checksumSha256?: unknown;
  sizeBytes?: unknown;
  createdBy?: unknown;
  changeSummary?: unknown;
}

// backend model: GovernmentDocumentModel  (table: docint_government_documents)
export interface GovernmentDocumentModel {
  uuid: string;
  documentId?: unknown;
  referenceNumber?: unknown;
  issuingAuthority?: unknown;
  recipientAuthority?: unknown;
  subject?: unknown;
  classification?: unknown;
  decisionNumber?: unknown;
  committeeName?: unknown;
  contractNumber?: unknown;
  procurementNumber?: unknown;
  legalBasis?: unknown;
  signatoryName?: unknown;
  signatoryTitle?: unknown;
  effectiveDate?: unknown;
  expiryDate?: unknown;
  metadataJson?: unknown;
}

// backend model: DocumentReviewModel  (table: docint_reviews)
export interface DocumentReviewModel {
  uuid: string;
  documentId?: unknown;
  reviewerId?: unknown;
  reviewerName?: unknown;
  role?: unknown;
  decision?: unknown;
  comments?: unknown;
  suggestedChanges?: unknown;
  assignedAt?: unknown;
  completedAt?: unknown;
  metadataJson?: unknown;
}

// backend model: DocumentAnnotationModel  (table: docint_annotations)
export interface DocumentAnnotationModel {
  uuid: string;
  documentId?: unknown;
  pageNumber?: unknown;
  authorId?: unknown;
  authorName?: unknown;
  content?: unknown;
  annotationType?: unknown;
  resolved?: unknown;
  metadataJson?: unknown;
}

// backend model: DigitalPreservationRecordModel  (table: docint_preservation)
export interface DigitalPreservationRecordModel {
  uuid: string;
  documentId?: unknown;
  standard?: unknown;
  preservationLevel?: unknown;
  originalFormat?: unknown;
  preservationFormat?: unknown;
  originalChecksum?: unknown;
  preservationChecksum?: unknown;
  checksumMethod?: unknown;
  preservationLocation?: unknown;
  coldStorageLocation?: unknown;
  integrityLog?: unknown;
  preservationDate?: unknown;
  nextIntegrityCheck?: unknown;
  metadataJson?: unknown;
}

// backend model: GovernancePolicyModel  (table: docint_governance_policies)
export interface GovernancePolicyModel {
  uuid: string;
  name?: unknown;
  description?: unknown;
  domain?: unknown;
  severity?: unknown;
  action?: unknown;
  conditions?: unknown;
  enabled?: unknown;
}

// backend model: GovernanceEventModel  (table: docint_governance_events)
export interface GovernanceEventModel {
  uuid: string;
  documentId?: unknown;
  policyId?: unknown;
  domain?: unknown;
  severity?: unknown;
  message?: unknown;
  actionTaken?: unknown;
  details?: unknown;
}

// backend model: DocumentEventModel  (table: docint_events)
export interface DocumentEventModel {
  uuid: string;
  documentId?: unknown;
  channel?: unknown;
  actorId?: unknown;
  actorName?: unknown;
  payload?: unknown;
}

// backend model: DocumentLifecycleModel  (table: docint_lifecycle)
export interface DocumentLifecycleModel {
  uuid: string;
  documentId?: unknown;
  eventType?: unknown;
  previousStatus?: unknown;
  newStatus?: unknown;
  actor?: unknown;
  reason?: unknown;
  metadataJson?: unknown;
}

// backend model: WebhookRegistrationModel  (table: docint_webhooks)
export interface WebhookRegistrationModel {
  uuid: string;
  url?: unknown;
  events?: unknown;
  secret?: unknown;
  active?: unknown;
  lastSuccess?: unknown;
  lastFailure?: unknown;
  failureCount?: unknown;
}

// backend model: KnowledgeGraphEdgeModel  (table: docint_knowledge_graph_edges)
export interface KnowledgeGraphEdgeModel {
  uuid: string;
  sourceDocumentId?: unknown;
  targetDocumentId?: unknown;
  sourceEntity?: unknown;
  targetEntity?: unknown;
  relation?: unknown;
  confidence?: unknown;
  weight?: unknown;
  metadataJson?: unknown;
}

// backend model: PipelineHealthModel  (table: docint_pipeline_health)
export interface PipelineHealthModel {
  uuid: string;
  pipelineName?: unknown;
  phase?: unknown;
  status?: unknown;
  documentsProcessed?: unknown;
  documentsFailed?: unknown;
  avgProcessingTimeMs?: unknown;
  p95ProcessingTimeMs?: unknown;
  errorRate?: unknown;
  throughputPerMinute?: unknown;
  lastError?: unknown;
  lastErrorAt?: unknown;
}

// backend model: AccessControlModel  (table: docint_access_control)
export interface AccessControlModel {
  uuid: string;
  documentId?: unknown;
  userId?: unknown;
  role?: unknown;
  delegatedFrom?: unknown;
  delegatedExpiry?: unknown;
}

// backend model: DocumentRetentionModel  (table: docint_retention)
export interface DocumentRetentionModel {
  uuid: string;
  documentId?: unknown;
  policy?: unknown;
  archiveStatus?: unknown;
  retentionStart?: unknown;
  retentionEnd?: unknown;
  legalHold?: unknown;
  legalHoldReason?: unknown;
  purgeScheduledAt?: unknown;
}

// backend model: Citizen  (table: citizens)
export interface Citizen {
  uuid: string;
  citizenUlid?: unknown;
  nidHash?: unknown;
  nidVerified?: unknown;
  phoneLast10?: unknown;
  birthYear?: unknown;
  birthMonth?: unknown;
  birthDay?: unknown;
  gender?: unknown;
  nameCanonical?: unknown;
  nameBlockingKey?: unknown;
  familyIdHash?: unknown;
  mergedIntoId?: unknown;
  status?: unknown;
  version?: unknown;
}

// backend model: IdentityClaim  (table: identity_claims)
export interface IdentityClaim {
  uuid: string;
  citizenId?: unknown;
  labId?: unknown;
  localPatientId?: unknown;
  matchMethod?: unknown;
  matchScore?: unknown;
  matchFeatures?: unknown;
  claimedByUserId?: unknown;
}

// backend model: MergeAudit  (table: mpi_merge_audit)
export interface MergeAudit {
  uuid: string;
  eventType?: unknown;
  primaryCitizenId?: unknown;
  secondaryCitizenId?: unknown;
  matchScore?: unknown;
  matchFeatures?: unknown;
  decisionReason?: unknown;
  decidedByUserId?: unknown;
  occurredAt?: unknown;
  prevHash?: unknown;
  entryHash?: unknown;
}

// backend model: CanonicalDocument
export interface CanonicalDocument {
  uuid: string;
  documentId?: string;
  source?: string;
  documentType?: string;
  title?: string | null;
  contentSummary?: string | null;
  patientId?: string;
  citizenId?: string | null;
  encounterId?: string | null;
  practitionerId?: string | null;
  labId?: number | null;
  fileUrl?: string | null;
  mimeType?: string | null;
}

// backend model: CanonicalEncounter
export interface CanonicalEncounter {
  uuid: string;
  encounterType?: string | null;
  status?: string | null;
  patientId?: string | null;
  citizenId?: string | null;
  organizationId?: string | null;
  facilityId?: string | null;
  practitionerId?: string | null;
  periodStart?: string | null;
  periodEnd?: string | null;
  reasonCode?: string | null;
  reasonDescription?: string | null;
  diagnosisCode?: string | null;
  icd10Code?: string | null;
  labId?: number | null;
  labOrderId?: number | null;
}

// backend model: CanonicalMedication
export interface CanonicalMedication {
  uuid: string;
  source?: string;
  medicationId?: string;
  patientId?: string;
  citizenId?: string | null;
  encounterId?: string | null;
  practitionerId?: string | null;
  medicationCode?: string | null;
  medicationName?: string;
  medicationNameAr?: string | null;
  status?: string;
  dosageText?: string | null;
  route?: string | null;
  frequency?: string | null;
  reasonCode?: string | null;
  startedAt?: string | null;
  endedAt?: string | null;
  recordedAt?: string | null;
  labId?: number | null;
}

// backend model: CanonicalObservation
export interface CanonicalObservation {
  uuid: string;
  labId?: number;
  patientId?: number;
  orderId?: number;
  testName?: string;
  testCode?: string | null;
  value?: string | null;
  valueText?: string | null;
  valueNumeric?: number | null;
  unit?: string | null;
  flag?: string | null;
  referenceRange?: string | null;
  normalRangeLow?: string | null;
  normalRangeHigh?: string | null;
  resultStatus?: string | null;
  observedAt?: string | null;
  encounterId?: string | null;
  practitionerId?: string | null;
  facilityId?: string | null;
  nationalPatientId?: string | null;
  citizenId?: string | null;
}

// backend model: CanonicalPatient
export interface CanonicalPatient {
  uuid: string;
  labId?: number;
  healthId?: string | null;
  nationalIdHash?: string | null;
  familyIdHash?: string | null;
  fullName?: string;
  phone?: string;
  birthDate?: string | null;
  gender?: string | null;
  email?: string | null;
  guardianId?: number | null;
  nationalPatientId?: string | null;
  citizenId?: string | null;
  firstName?: string | null;
  fatherName?: string | null;
  grandfatherName?: string | null;
  lastName?: string | null;
  motherName?: string | null;
  fullNameAr?: string | null;
  dateOfBirth?: string | null;
  bloodGroup?: string | null;
  governorate?: string | null;
  district?: string | null;
  nationality?: string | null;
}

// backend model: CanonicalProcedure
export interface CanonicalProcedure {
  uuid: string;
  procedureId?: number;
  labId?: number;
  patientId?: number;
  orderId?: number;
  procedureName?: string;
  procedureCode?: string | null;
  status?: string;
  performedAt?: string | null;
  doctorName?: string | null;
  encounterId?: string | null;
  facilityId?: string | null;
  nationalPatientId?: string | null;
  citizenId?: string | null;
}

// backend model: EventRetentionPolicy  (table: dp_event_retention_policies)
export interface EventRetentionPolicy {
  uuid: string;
  eventType?: unknown;
  retentionDays?: unknown;
  maxSnapshots?: unknown;
  allowArchive?: unknown;
  archiveAfterDays?: unknown;
  compressionEnabled?: unknown;
  description?: unknown;
}

// backend model: EventSnapshot  (table: dp_event_snapshots)
export interface EventSnapshot {
  uuid: string;
  aggregateType?: unknown;
  aggregateId?: unknown;
  snapshotData?: unknown;
  version?: unknown;
  snapshotType?: unknown;
  createdBy?: unknown;
  snapshotAt?: unknown;
}

// backend model: StoredEvent  (table: dp_stored_events)
export interface StoredEvent {
  uuid: string;
  eventType?: unknown;
  aggregateType?: unknown;
  aggregateId?: unknown;
  eventData?: unknown;
  metadata?: unknown;
  version?: unknown;
  partitionKey?: unknown;
  occurredAt?: unknown;
  recordedAt?: unknown;
  causationId?: unknown;
  correlationId?: unknown;
  recordedBy?: unknown;
}

// backend model: ConsentDirective  (table: dp_consent_directives)
export interface ConsentDirective {
  uuid: string;
  consentId?: unknown;
  patientId?: unknown;
  citizenId?: unknown;
  consentType?: unknown;
  consentStatus?: unknown;
  dataUsePurpose?: unknown;
  dataCategories?: unknown;
  authorizedParty?: unknown;
  grantedAt?: unknown;
  expiresAt?: unknown;
  revokedAt?: unknown;
  revocationReason?: unknown;
  jurisdiction?: unknown;
}

// backend model: DataCatalogEntry  (table: dp_data_catalog)
export interface DataCatalogEntry {
  uuid: string;
  entryName?: unknown;
  entryType?: unknown;
  schemaName?: unknown;
  tableName?: unknown;
  columnName?: unknown;
  description?: unknown;
  classification?: unknown;
  sensitivityLevel?: unknown;
  sourceSystem?: unknown;
  owner?: unknown;
  steward?: unknown;
  isSensitive?: unknown;
  isPii?: unknown;
  isPhi?: unknown;
  retentionDays?: unknown;
  dataQualityScore?: unknown;
  tags?: unknown;
}

// backend model: DataClassification  (table: dp_data_classifications)
export interface DataClassification {
  uuid: string;
  entityName?: unknown;
  fieldName?: unknown;
  classificationLevel?: unknown;
  classificationCategory?: unknown;
  sensitivity?: unknown;
  isPii?: unknown;
  isPhi?: unknown;
  isFinancial?: unknown;
  isConfidential?: unknown;
  accessRestrictions?: unknown;
  encryptionRequired?: unknown;
  maskingRequired?: unknown;
  retentionGuideline?: unknown;
  notes?: unknown;
}

// backend model: DataLineageEntry  (table: dp_data_lineage)
export interface DataLineageEntry {
  uuid: string;
  sourceEntity?: unknown;
  sourceEntityId?: unknown;
  targetEntity?: unknown;
  targetEntityId?: unknown;
  transformationType?: unknown;
  transformationDescription?: unknown;
  transformationDetails?: unknown;
  pipelineName?: unknown;
  pipelineRunId?: unknown;
  pipelineVersion?: unknown;
  processedAt?: unknown;
  processingDurationMs?: unknown;
  status?: unknown;
  errorMessage?: unknown;
  labId?: unknown;
}

// backend model: DataQualityCheck  (table: dp_data_quality_checks)
export interface DataQualityCheck {
  uuid: string;
  ruleId?: unknown;
  checkRunId?: unknown;
  entityType?: unknown;
  entityId?: unknown;
  fieldName?: unknown;
  resultStatus?: unknown;
  resultValue?: unknown;
  resultDetails?: unknown;
  errorMessage?: unknown;
  recordsChecked?: unknown;
  recordsFailed?: unknown;
  score?: unknown;
  checkedAt?: unknown;
  checkedBy?: unknown;
  labId?: unknown;
}

// backend model: DataQualityRule  (table: dp_data_quality_rules)
export interface DataQualityRule {
  uuid: string;
  ruleName?: unknown;
  ruleType?: unknown;
  ruleCategory?: unknown;
  entityType?: unknown;
  fieldName?: unknown;
  conditionExpression?: unknown;
  severity?: unknown;
  description?: unknown;
  remediationSql?: unknown;
  isAutoRemediable?: unknown;
  thresholdWarning?: unknown;
  thresholdError?: unknown;
}

// backend model: DataSteward  (table: dp_data_stewards)
export interface DataSteward {
  uuid: string;
  userId?: unknown;
  domain?: unknown;
  entityType?: unknown;
  stewardRole?: unknown;
  fullName?: unknown;
  email?: unknown;
  phone?: unknown;
  isPrimary?: unknown;
  notes?: unknown;
}

// backend model: MetadataEntry  (table: dp_metadata_registry)
export interface MetadataEntry {
  uuid: string;
  entityName?: unknown;
  entityType?: unknown;
  fieldName?: unknown;
  metadataKey?: unknown;
  metadataValue?: unknown;
  metadataJson?: unknown;
  metadataType?: unknown;
  source?: unknown;
  version?: unknown;
}

// backend model: RetentionPolicy  (table: dp_retention_policies)
export interface RetentionPolicy {
  uuid: string;
  policyName?: unknown;
  entityType?: unknown;
  retentionDays?: unknown;
  archiveAfterDays?: unknown;
  purgeAfterDays?: unknown;
  actionOnExpiry?: unknown;
  allowsExtension?: unknown;
  maxExtensionDays?: unknown;
  legalHoldEnabled?: unknown;
  legalHoldReason?: unknown;
  notes?: unknown;
}

// backend model: DeviceRegistry  (table: dp_device_registry)
export interface DeviceRegistry {
  uuid: string;
  deviceBridgeId?: unknown;
  labId?: unknown;
  deviceName?: unknown;
  deviceModel?: unknown;
  serialNumber?: unknown;
  manufacturer?: unknown;
  deviceType?: unknown;
  deviceClass?: unknown;
  isCalibrated?: unknown;
  lastCalibrationDate?: unknown;
  nextCalibrationDate?: unknown;
  firmwareVersion?: unknown;
  softwareVersion?: unknown;
  connectivityProtocol?: unknown;
  location?: unknown;
  facilityId?: unknown;
}

// backend model: DuplicateRecord  (table: dp_duplicate_records)
export interface DuplicateRecord {
  uuid: string;
  goldenRecordId?: unknown;
  sourcePatientId?: unknown;
  sourceNationalPatientId?: unknown;
  sourceSystem?: unknown;
  duplicateProbability?: unknown;
  matchingAlgorithm?: unknown;
  matchedFields?: unknown;
  matchDetails?: unknown;
  status?: unknown;
  resolution?: unknown;
}

// backend model: GoldenRecord  (table: dp_golden_records)
export interface GoldenRecord {
  uuid: string;
  patientId?: unknown;
  nationalPatientId?: unknown;
  citizenId?: unknown;
  confidenceScore?: unknown;
  matchingAlgorithm?: unknown;
  matchedFields?: unknown;
  mergeHistory?: unknown;
  isActiveGolden?: unknown;
  activatedAt?: unknown;
  deactivatedAt?: unknown;
  notes?: unknown;
}

// backend model: LocationRegistry  (table: dp_location_registry)
export interface LocationRegistry {
  uuid: string;
  facilityId?: unknown;
  labId?: unknown;
  locationCode?: unknown;
  locationName?: unknown;
  locationNameAr?: unknown;
  locationType?: unknown;
  addressLine?: unknown;
  city?: unknown;
  governorate?: unknown;
  district?: unknown;
  subdistrict?: unknown;
  latitude?: unknown;
  longitude?: unknown;
  operatingHours?: unknown;
  contactPhone?: unknown;
  contactEmail?: unknown;
}

// backend model: MergeAction  (table: dp_merge_actions)
export interface MergeAction {
  uuid: string;
  goldenRecordId?: unknown;
  sourcePatientId?: unknown;
  targetPatientId?: unknown;
  mergeType?: unknown;
  mergeReason?: unknown;
  mergeFields?: unknown;
  conflictResolution?: unknown;
  mergedBy?: unknown;
  mergedAt?: unknown;
  rollbackAt?: unknown;
  rollbackReason?: unknown;
}

// backend model: ProviderRegistry  (table: dp_provider_registry)
export interface ProviderRegistry {
  uuid: string;
  practitionerId?: unknown;
  labUserId?: unknown;
  nationalIdHash?: unknown;
  licenseNumber?: unknown;
  fullName?: unknown;
  fullNameAr?: unknown;
  specialty?: unknown;
  subSpecialty?: unknown;
  providerType?: unknown;
  isVerified?: unknown;
  verificationSource?: unknown;
  phone?: unknown;
  email?: unknown;
  facilityId?: unknown;
  organizationId?: unknown;
  digitalSignatureKey?: unknown;
}

// backend model: SourceSystem  (table: dp_source_systems)
export interface SourceSystem {
  uuid: string;
  name?: unknown;
  code?: unknown;
  systemType?: unknown;
  description?: unknown;
  baseUrl?: unknown;
  apiKeyHash?: unknown;
  priority?: unknown;
  dataQualityScore?: unknown;
  contactInfo?: unknown;
}

// backend model: TerminologyRegistry  (table: dp_terminology_registry)
export interface TerminologyRegistry {
  uuid: string;
  systemName?: unknown;
  systemCode?: unknown;
  systemUri?: unknown;
  oid?: unknown;
  version?: unknown;
  description?: unknown;
  publisher?: unknown;
  totalCodes?: unknown;
  isCaseSensitive?: unknown;
  hierarchyType?: unknown;
  releaseDate?: unknown;
  license?: unknown;
  usageNotes?: unknown;
}

// backend model: DeidentificationJob  (table: dp_deidentification_jobs)
export interface DeidentificationJob {
  uuid: string;
  jobName?: unknown;
  entityType?: unknown;
  entityIds?: unknown;
  techniques?: unknown;
  fieldsToDeidentify?: unknown;
  fieldsToKeep?: unknown;
  status?: unknown;
  progress?: unknown;
  inputDatasetId?: unknown;
  outputDatasetId?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  errorMessage?: unknown;
  requestedBy?: unknown;
  approvedBy?: unknown;
  complianceRef?: unknown;
}

// backend model: FeatureStore  (table: dp_feature_store)
export interface FeatureStore {
  uuid: string;
  featureName?: unknown;
  featureType?: unknown;
  featureVersion?: unknown;
  entityType?: unknown;
  description?: unknown;
  sourceQuery?: unknown;
  transformation?: unknown;
  dataType?: unknown;
  defaultValue?: unknown;
  valueRangeMin?: unknown;
  valueRangeMax?: unknown;
  isRequired?: unknown;
  imputationStrategy?: unknown;
  tags?: unknown;
  owner?: unknown;
}

// backend model: FeatureValue  (table: dp_feature_values)
export interface FeatureValue {
  uuid: string;
  featureId?: unknown;
  entityType?: unknown;
  entityId?: unknown;
  valueNumeric?: unknown;
  valueText?: unknown;
  valueJson?: unknown;
  effectiveAt?: unknown;
  recordedAt?: unknown;
  labId?: unknown;
  source?: unknown;
}

// backend model: KnowledgeGraphEdge  (table: dp_knowledge_graph_edges)
export interface KnowledgeGraphEdge {
  uuid: string;
  sourceNodeId?: unknown;
  targetNodeId?: unknown;
  edgeType?: unknown;
  edgeLabel?: unknown;
  edgeLabelAr?: unknown;
  weight?: unknown;
  properties?: unknown;
  sourceEvidence?: unknown;
}

// backend model: KnowledgeGraphNode  (table: dp_knowledge_graph_nodes)
export interface KnowledgeGraphNode {
  uuid: string;
  nodeType?: unknown;
  nodeLabel?: unknown;
  nodeLabelAr?: unknown;
  nodeSourceId?: unknown;
  nodeSourceSystem?: unknown;
  description?: unknown;
  properties?: unknown;
  externalUri?: unknown;
  ontologyClass?: unknown;
  ontologyCode?: unknown;
}

// backend model: SyntheticDataJob  (table: dp_synthetic_data_jobs)
export interface SyntheticDataJob {
  uuid: string;
  jobName?: unknown;
  sourceDatasetId?: unknown;
  modelType?: unknown;
  targetRecords?: unknown;
  parameters?: unknown;
  columnConfig?: unknown;
  privacyBudget?: unknown;
  status?: unknown;
  outputPath?: unknown;
  outputRecords?: unknown;
  qualityScore?: unknown;
  errorMessage?: unknown;
  requestedBy?: unknown;
}

// backend model: TrainingDataset  (table: dp_training_datasets)
export interface TrainingDataset {
  uuid: string;
  datasetName?: unknown;
  datasetVersion?: unknown;
  datasetType?: unknown;
  description?: unknown;
  featureList?: unknown;
  targetVariable?: unknown;
  totalRecords?: unknown;
  trainingRecords?: unknown;
  validationRecords?: unknown;
  testRecords?: unknown;
  filePath?: unknown;
  fileFormat?: unknown;
  fileSizeBytes?: unknown;
  createdBy?: unknown;
  status?: unknown;
  tags?: unknown;
}

// backend model: VectorEmbedding  (table: dp_vector_embeddings)
export interface VectorEmbedding {
  uuid: string;
  entityType?: unknown;
  entityId?: unknown;
  embeddingModel?: unknown;
  embeddingDimension?: unknown;
  embeddingText?: unknown;
  embeddingSource?: unknown;
  chunkIndex?: unknown;
  chunkText?: unknown;
  metadata?: unknown;
  labId?: unknown;
}

// backend model: DimDate  (table: dw_dim_date)
export interface DimDate {
  uuid: string;
  dateValue?: unknown;
  year?: unknown;
  quarter?: unknown;
  month?: unknown;
  monthName?: unknown;
  monthNameAr?: unknown;
  week?: unknown;
  day?: unknown;
  dayOfWeek?: unknown;
  dayName?: unknown;
  dayNameAr?: unknown;
  isWeekend?: unknown;
  isHoliday?: unknown;
  fiscalYear?: unknown;
  fiscalQuarter?: unknown;
}

// backend model: DimDiagnosis  (table: dw_dim_diagnosis)
export interface DimDiagnosis {
  uuid: string;
  icd10Code?: unknown;
  icd10Description?: unknown;
  icd11Code?: unknown;
  snomedCode?: unknown;
  diagnosisText?: unknown;
  diagnosisTextAr?: unknown;
  category?: unknown;
  isChronic?: unknown;
  isBillable?: unknown;
}

// backend model: DimFacility  (table: dw_dim_facility)
export interface DimFacility {
  uuid: string;
  sourceFacilityId?: unknown;
  labId?: unknown;
  facilityCode?: unknown;
  facilityName?: unknown;
  facilityNameAr?: unknown;
  facilityType?: unknown;
  governorate?: unknown;
  district?: unknown;
  city?: unknown;
}

// backend model: DimPatient  (table: dw_dim_patient)
export interface DimPatient {
  uuid: string;
  sourcePatientId?: unknown;
  nationalPatientId?: unknown;
  citizenId?: unknown;
  fullName?: unknown;
  phone?: unknown;
  gender?: unknown;
  birthDate?: unknown;
  ageGroup?: unknown;
  governorate?: unknown;
  district?: unknown;
  nationality?: unknown;
  bloodGroup?: unknown;
  labId?: unknown;
}

// backend model: DimProvider  (table: dw_dim_provider)
export interface DimProvider {
  uuid: string;
  sourcePractitionerId?: unknown;
  labUserId?: unknown;
  fullName?: unknown;
  fullNameAr?: unknown;
  licenseNumber?: unknown;
  specialty?: unknown;
  providerType?: unknown;
  isVerified?: unknown;
}

// backend model: FactDiagnosis  (table: dw_fact_diagnoses)
export interface FactDiagnosis {
  uuid: string;
  dimPatientId?: unknown;
  dimDateId?: unknown;
  dimDiagnosisId?: unknown;
  dimFacilityId?: unknown;
  dimProviderId?: unknown;
  diagnosisType?: unknown;
  isChronic?: unknown;
  certainty?: unknown;
  encounterType?: unknown;
  labId?: unknown;
  diagnosisSourceId?: unknown;
  diagnosisDate?: unknown;
}

// backend model: FactLabResult  (table: dw_fact_lab_results)
export interface FactLabResult {
  uuid: string;
  dimPatientId?: unknown;
  dimDateId?: unknown;
  dimFacilityId?: unknown;
  dimProviderId?: unknown;
  testName?: unknown;
  testCode?: unknown;
  resultValueNumeric?: unknown;
  resultValueText?: unknown;
  resultUnit?: unknown;
  resultFlag?: unknown;
  normalRangeLow?: unknown;
  normalRangeHigh?: unknown;
  isAbnormal?: unknown;
  isCritical?: unknown;
  labId?: unknown;
  resultSourceId?: unknown;
  resultDate?: unknown;
}

// backend model: FactPatientVisit  (table: dw_fact_patient_visits)
export interface FactPatientVisit {
  uuid: string;
  dimPatientId?: unknown;
  dimDateId?: unknown;
  dimFacilityId?: unknown;
  dimProviderId?: unknown;
  dimDiagnosisId?: unknown;
  encounterType?: unknown;
  visitStatus?: unknown;
  durationMinutes?: unknown;
  isEmergency?: unknown;
  labId?: unknown;
  encounterSourceId?: unknown;
  visitDate?: unknown;
}

// backend model: IdentityAuthority  (table: niam_gov_authorities)
export interface IdentityAuthority {
  uuid: string;
  authorityId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  authorityType?: unknown;
  jurisdiction?: unknown;
  parentAuthorityId?: unknown;
  contactEmail?: unknown;
  status?: unknown;
  establishedDate?: unknown;
  accreditedBy?: unknown;
  accreditationExpires?: unknown;
}

// backend model: DigitalIdentityCouncil  (table: niam_gov_councils)
export interface DigitalIdentityCouncil {
  uuid: string;
  councilId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  councilType?: unknown;
  authorityId?: unknown;
  chairpersonId?: unknown;
  members?: unknown;
  meetingFrequency?: unknown;
  lastMeeting?: unknown;
  nextMeeting?: unknown;
  status?: unknown;
}

// backend model: PolicyApprovalWorkflow  (table: niam_gov_policy_approvals)
export interface PolicyApprovalWorkflow {
  uuid: string;
  workflowId?: unknown;
  policyId?: unknown;
  submittedBy?: unknown;
  submittedAt?: unknown;
  status?: unknown;
  reviewers?: unknown;
  reviewComments?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  rejectedBy?: unknown;
  rejectedAt?: unknown;
  rejectionReason?: unknown;
  version?: unknown;
}

// backend model: IdentityAppeal  (table: niam_gov_appeals)
export interface IdentityAppeal {
  uuid: string;
  appealId?: unknown;
  appellantPersonId?: unknown;
  identityId?: unknown;
  appealType?: unknown;
  reason?: unknown;
  supportingDocuments?: unknown;
  status?: unknown;
  assignedTo?: unknown;
  councilId?: unknown;
  decision?: unknown;
  decisionAt?: unknown;
  decisionBy?: unknown;
  notes?: unknown;
}

// backend model: IdentitySuspension  (table: niam_gov_suspensions)
export interface IdentitySuspension {
  uuid: string;
  suspensionId?: unknown;
  personId?: unknown;
  identityId?: unknown;
  accountId?: unknown;
  reason?: unknown;
  severity?: unknown;
  suspendedBy?: unknown;
  suspendedAt?: unknown;
  durationHours?: unknown;
  expiresAt?: unknown;
  liftedBy?: unknown;
  liftedAt?: unknown;
  liftReason?: unknown;
  status?: unknown;
  notificationSent?: unknown;
}

// backend model: IdentityRestoration  (table: niam_gov_restorations)
export interface IdentityRestoration {
  uuid: string;
  restorationId?: unknown;
  personId?: unknown;
  identityId?: unknown;
  suspensionId?: unknown;
  requestReason?: unknown;
  requestedBy?: unknown;
  reviewedBy?: unknown;
  reviewedAt?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  status?: unknown;
  restorationType?: unknown;
  postRestorationActions?: unknown;
  notes?: unknown;
}

// backend model: NationalIdentityRegistry  (table: niam_gov_registry)
export interface NationalIdentityRegistry {
  uuid: string;
  registryId?: unknown;
  personId?: unknown;
  identityId?: unknown;
  registryType?: unknown;
  registrationNumber?: unknown;
  registeredAt?: unknown;
  registeredBy?: unknown;
  verifiedAt?: unknown;
  verifiedBy?: unknown;
  certificateId?: unknown;
  expiryDate?: unknown;
  status?: unknown;
  dataQualityScore?: unknown;
  lastVerified?: unknown;
}

// backend model: IdentityCertificationRegistry  (table: niam_gov_certifications)
export interface IdentityCertificationRegistry {
  uuid: string;
  certificationId?: unknown;
  personId?: unknown;
  organizationId?: unknown;
  certifyingAuthorityId?: unknown;
  certificationType?: unknown;
  certificationNumber?: unknown;
  issueDate?: unknown;
  expiryDate?: unknown;
  status?: unknown;
  verifiedBy?: unknown;
  verificationMethod?: unknown;
  digitalSignature?: unknown;
  revocationReason?: unknown;
}

// backend model: IdentityReviewBoard  (table: niam_gov_review_boards)
export interface IdentityReviewBoard {
  uuid: string;
  boardId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  boardType?: unknown;
  authorityId?: unknown;
  chairpersonId?: unknown;
  members?: unknown;
  quorumSize?: unknown;
  meetingSchedule?: unknown;
  caseLoad?: unknown;
  status?: unknown;
}

// backend model: RiskEvent  (table: niam_adaptive_risk_events)
export interface RiskEvent {
  uuid: string;
  eventId?: unknown;
  personId?: unknown;
  accountId?: unknown;
  sessionId?: unknown;
  eventType?: unknown;
  severity?: unknown;
  riskScore?: unknown;
  details?: unknown;
  ipAddress?: unknown;
  userAgent?: unknown;
  locationCity?: unknown;
  locationCountry?: unknown;
  locationLat?: unknown;
  locationLng?: unknown;
  timestamp?: unknown;
  mitigated?: unknown;
  mitigationAction?: unknown;
}

// backend model: RiskPolicy  (table: niam_adaptive_risk_policies)
export interface RiskPolicy {
  uuid: string;
  policyId?: unknown;
  name?: unknown;
  description?: unknown;
  riskThresholdLow?: unknown;
  riskThresholdMedium?: unknown;
  riskThresholdHigh?: unknown;
  riskThresholdCritical?: unknown;
  actions?: unknown;
  scope?: unknown;
  enabled?: unknown;
}

// backend model: AdaptiveMFASession  (table: niam_adaptive_mfa_sessions)
export interface AdaptiveMFASession {
  uuid: string;
  mfaId?: unknown;
  accountId?: unknown;
  sessionId?: unknown;
  mfaType?: unknown;
  challenge?: unknown;
  challengeExpiresAt?: unknown;
  verified?: unknown;
  verifiedAt?: unknown;
  attempts?: unknown;
  maxAttempts?: unknown;
  status?: unknown;
}

// backend model: ImpossibleTravelEvent  (table: niam_adaptive_travel_events)
export interface ImpossibleTravelEvent {
  uuid: string;
  travelId?: unknown;
  accountId?: unknown;
  sessionId?: unknown;
  previousIp?: unknown;
  previousLocationCity?: unknown;
  previousLocationCountry?: unknown;
  previousLat?: unknown;
  previousLng?: unknown;
  previousTimestamp?: unknown;
  currentIp?: unknown;
  currentLocationCity?: unknown;
  currentLocationCountry?: unknown;
  currentLat?: unknown;
  currentLng?: unknown;
  currentTimestamp?: unknown;
  distanceKm?: unknown;
  timeDeltaMinutes?: unknown;
  speedKmh?: unknown;
  impossible?: unknown;
  riskScore?: unknown;
}

// backend model: SessionPolicy  (table: niam_adaptive_session_policies)
export interface SessionPolicy {
  uuid: string;
  policyId?: unknown;
  name?: unknown;
  appliesTo?: unknown;
  maxSessions?: unknown;
  allowConcurrent?: unknown;
  requireMfa?: unknown;
  sessionTimeoutMinutes?: unknown;
  inactivityTimeoutMinutes?: unknown;
  notifyPreviousDevice?: unknown;
  terminatePreviousOnNewLogin?: unknown;
  enforceGeoRestriction?: unknown;
  allowedGeo?: unknown;
  enforceIpRestriction?: unknown;
  allowedIps?: unknown;
}

// backend model: EnterprisePortal  (table: niam_admin_portals)
export interface EnterprisePortal {
  uuid: string;
  portalId?: unknown;
  organizationId?: unknown;
  name?: unknown;
  portalType?: unknown;
  features?: unknown;
  status?: unknown;
  createdBy?: unknown;
  activatedAt?: unknown;
  lastAccessAt?: unknown;
  settings?: unknown;
}

// backend model: PortalBranch  (table: niam_admin_branches)
export interface PortalBranch {
  uuid: string;
  branchId?: unknown;
  portalId?: unknown;
  organizationId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  address?: unknown;
  phone?: unknown;
  email?: unknown;
  managerPersonId?: unknown;
  status?: unknown;
}

// backend model: PortalFacility  (table: niam_admin_facilities)
export interface PortalFacility {
  uuid: string;
  facilityId?: unknown;
  branchId?: unknown;
  organizationId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  facilityType?: unknown;
  licenseNumber?: unknown;
  accreditation?: unknown;
  status?: unknown;
  contact?: unknown;
  address?: unknown;
}

// backend model: PortalDepartment  (table: niam_admin_departments)
export interface PortalDepartment {
  uuid: string;
  deptId?: unknown;
  facilityId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  deptType?: unknown;
  headPersonId?: unknown;
  status?: unknown;
}

// backend model: PortalSubscription  (table: niam_admin_subscriptions)
export interface PortalSubscription {
  uuid: string;
  subId?: unknown;
  organizationId?: unknown;
  planType?: unknown;
  features?: unknown;
  userLimit?: unknown;
  storageLimit?: unknown;
  apiCallLimit?: unknown;
  startDate?: unknown;
  renewalDate?: unknown;
  expiryDate?: unknown;
  status?: unknown;
  billingCycle?: unknown;
  billingAmount?: unknown;
  currency?: unknown;
  paymentMethod?: unknown;
  autoRenew?: unknown;
}

// backend model: PortalAuditLog  (table: niam_admin_audit_logs)
export interface PortalAuditLog {
  uuid: string;
  logId?: unknown;
  organizationId?: unknown;
  portalId?: unknown;
  action?: unknown;
  performedBy?: unknown;
  targetType?: unknown;
  targetId?: unknown;
  details?: unknown;
  ipAddress?: unknown;
  userAgent?: unknown;
  timestamp?: unknown;
  outcome?: unknown;
}

// backend model: FHIRConnection  (table: niam_admin_fhir_connections)
export interface FHIRConnection {
  uuid: string;
  connId?: unknown;
  organizationId?: unknown;
  name?: unknown;
  fhirVersion?: unknown;
  baseUrl?: unknown;
  authType?: unknown;
  credentialsEncrypted?: unknown;
  status?: unknown;
  lastTestAt?: unknown;
  lastTestResult?: unknown;
}

// backend model: ComplianceFramework  (table: niam_comp_frameworks)
export interface ComplianceFramework {
  uuid: string;
  frameworkId?: unknown;
  name?: unknown;
  frameworkType?: unknown;
  version?: unknown;
  requirements?: unknown;
  status?: unknown;
}

// backend model: ComplianceCheck  (table: niam_comp_checks)
export interface ComplianceCheck {
  uuid: string;
  checkId?: unknown;
  frameworkId?: unknown;
  requirementId?: unknown;
  targetType?: unknown;
  targetId?: unknown;
  checkType?: unknown;
  status?: unknown;
  checkedBy?: unknown;
  checkedAt?: unknown;
  evidence?: unknown;
  finding?: unknown;
  recommendation?: unknown;
}

// backend model: ComplianceReport  (table: niam_comp_reports)
export interface ComplianceReport {
  uuid: string;
  reportId?: unknown;
  organizationId?: unknown;
  frameworkId?: unknown;
  reportType?: unknown;
  overallScore?: unknown;
  passedCount?: unknown;
  failedCount?: unknown;
  warningCount?: unknown;
  notApplicableCount?: unknown;
  findings?: unknown;
  recommendations?: unknown;
  generatedBy?: unknown;
  generatedAt?: unknown;
  validUntil?: unknown;
  status?: unknown;
}

// backend model: TrustFramework  (table: niam_trust_frameworks)
export interface TrustFramework {
  uuid: string;
  frameworkId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  version?: unknown;
  status?: unknown;
  effectiveDate?: unknown;
  supersedesFrameworkId?: unknown;
  authorityId?: unknown;
  scope?: unknown;
  assurancePolicies?: unknown;
}

// backend model: IdentityAssuranceProfile  (table: niam_trust_assurance_profiles)
export interface IdentityAssuranceProfile {
  uuid: string;
  personId?: unknown;
  identityId?: unknown;
  ial?: unknown;
  aal?: unknown;
  fal?: unknown;
  overallAssurance?: unknown;
  profileVersion?: unknown;
  assessedBy?: unknown;
  assessedAt?: unknown;
  expiresAt?: unknown;
  lastReviewed?: unknown;
  nextReview?: unknown;
  status?: unknown;
  evidence?: unknown;
}

// backend model: TrustAnchor  (table: niam_trust_anchors)
export interface TrustAnchor {
  uuid: string;
  anchorId?: unknown;
  name?: unknown;
  anchorType?: unknown;
  publicKeyHash?: unknown;
  certificateChain?: unknown;
  issuer?: unknown;
  subject?: unknown;
  validFrom?: unknown;
  validTo?: unknown;
  status?: unknown;
  revokedAt?: unknown;
  revocationReason?: unknown;
  signedBy?: unknown;
}

// backend model: FederationTrust  (table: niam_trust_federation)
export interface FederationTrust {
  uuid: string;
  trustId?: unknown;
  sourceOrgId?: unknown;
  targetOrgId?: unknown;
  trustType?: unknown;
  trustLevel?: unknown;
  scope?: unknown;
  agreementId?: unknown;
  establishedAt?: unknown;
  expiresAt?: unknown;
  lastReviewed?: unknown;
  status?: unknown;
  terms?: unknown;
}

// backend model: IdentityProofing  (table: niam_trust_proofing)
export interface IdentityProofing {
  uuid: string;
  proofingId?: unknown;
  personId?: unknown;
  identityId?: unknown;
  proofingLevel?: unknown;
  method?: unknown;
  evidenceType?: unknown;
  evidenceDocuments?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  authorityId?: unknown;
  status?: unknown;
  rejectionReason?: unknown;
  validFrom?: unknown;
  validTo?: unknown;
}

// backend model: TrustEvaluation  (table: niam_trust_evaluations)
export interface TrustEvaluation {
  uuid: string;
  evaluationId?: unknown;
  targetType?: unknown;
  targetId?: unknown;
  evaluatedBy?: unknown;
  evaluatedAt?: unknown;
  assuranceScore?: unknown;
  confidenceScore?: unknown;
  riskScore?: unknown;
  evaluationMethod?: unknown;
  findings?: unknown;
  recommendations?: unknown;
  nextEvaluationAt?: unknown;
  status?: unknown;
}

// backend model: EnterpriseRegistration  (table: niam_lifecycle_enterprise_reg)
export interface EnterpriseRegistration {
  uuid: string;
  regId?: unknown;
  organizationId?: unknown;
  status?: unknown;
  submittedBy?: unknown;
  submittedAt?: unknown;
  licenseDocument?: unknown;
  licenseValidatedAt?: unknown;
  licenseValidatedBy?: unknown;
  inspectionReport?: unknown;
  inspectedAt?: unknown;
  inspectedBy?: unknown;
  riskAssessment?: unknown;
  riskScore?: unknown;
  riskAssessedAt?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  certificateId?: unknown;
  rejectionReason?: unknown;
  currentStep?: unknown;
}

// backend model: EnterpriseRegistrationStep  (table: niam_lifecycle_enterprise_steps)
export interface EnterpriseRegistrationStep {
  uuid: string;
  stepId?: unknown;
  regId?: unknown;
  stepName?: unknown;
  status?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  performedBy?: unknown;
  notes?: unknown;
  output?: unknown;
}

// backend model: WorkforceRequest  (table: niam_lifecycle_workforce_requests)
export interface WorkforceRequest {
  uuid: string;
  requestId?: unknown;
  requestType?: unknown;
  requestingOrgId?: unknown;
  requestedBy?: unknown;
  personId?: unknown;
  status?: unknown;
  nationalIdHash?: unknown;
  licenseNumber?: unknown;
  boardRegistration?: unknown;
  employmentRulesCheck?: unknown;
  conflictReport?: unknown;
  restrictions?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  activatedAt?: unknown;
  suspensionReason?: unknown;
  terminationReason?: unknown;
  historicalPreserved?: unknown;
}

// backend model: GovernmentAppointment  (table: niam_lifecycle_gov_appointments)
export interface GovernmentAppointment {
  uuid: string;
  appointmentId?: unknown;
  personId?: unknown;
  organizationId?: unknown;
  hrReference?: unknown;
  appointmentType?: unknown;
  position?: unknown;
  grade?: unknown;
  salaryScale?: unknown;
  department?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  hrApprovedBy?: unknown;
  hrApprovedAt?: unknown;
  identityCreated?: unknown;
  credentialIssued?: unknown;
  accountActivated?: unknown;
  permissionsAssigned?: unknown;
  status?: unknown;
  promotionHistory?: unknown;
  transferHistory?: unknown;
}

// backend model: CitizenLifecycle  (table: niam_lifecycle_citizen)
export interface CitizenLifecycle {
  uuid: string;
  citizenId?: unknown;
  personId?: unknown;
  identityId?: unknown;
  status?: unknown;
  registrationDate?: unknown;
  otpSentAt?: unknown;
  otpVerifiedAt?: unknown;
  identityVerifiedAt?: unknown;
  healthId?: unknown;
  guardianPersonId?: unknown;
  familyTree?: unknown;
  consentRecords?: unknown;
  emergencyContacts?: unknown;
  addressHistory?: unknown;
  documentVerification?: unknown;
  selfServiceEnabled?: unknown;
  lastRecoveryAt?: unknown;
  deactivatedAt?: unknown;
  deactivationReason?: unknown;
  deceasedAt?: unknown;
  deathCertificateId?: unknown;
}

// backend model: GuardianAccount  (table: niam_lifecycle_guardians)
export interface GuardianAccount {
  uuid: string;
  guardianId?: unknown;
  guardianPersonId?: unknown;
  dependentPersonId?: unknown;
  relationship?: unknown;
  guardianType?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  delegatedAccess?: unknown;
  consentInheritance?: unknown;
  status?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  documents?: unknown;
}

// backend model: FamilyLink  (table: niam_lifecycle_family_links)
export interface FamilyLink {
  uuid: string;
  linkId?: unknown;
  personId?: unknown;
  relativePersonId?: unknown;
  relationship?: unknown;
  emergencyContact?: unknown;
  consentSharing?: unknown;
}

// backend model: ConsentRecord  (table: niam_lifecycle_consents)
export interface ConsentRecord {
  uuid: string;
  consentId?: unknown;
  personId?: unknown;
  consentType?: unknown;
  grantedTo?: unknown;
  grantedAt?: unknown;
  expiresAt?: unknown;
  revokedAt?: unknown;
  scope?: unknown;
  terms?: unknown;
  status?: unknown;
}

// backend model: NotificationTemplate  (table: niam_notif_templates)
export interface NotificationTemplate {
  uuid: string;
  templateId?: unknown;
  name?: unknown;
  notificationType?: unknown;
  subject?: unknown;
  body?: unknown;
  variables?: unknown;
  locale?: unknown;
  version?: unknown;
}

// backend model: NotificationQueue  (table: niam_notif_queue)
export interface NotificationQueue {
  uuid: string;
  queueId?: unknown;
  recipientId?: unknown;
  recipientType?: unknown;
  notificationType?: unknown;
  channel?: unknown;
  templateId?: unknown;
  subject?: unknown;
  body?: unknown;
  context?: unknown;
  priority?: unknown;
  status?: unknown;
  sentAt?: unknown;
  deliveredAt?: unknown;
  readAt?: unknown;
  errorCount?: unknown;
  maxRetries?: unknown;
  lastError?: unknown;
  scheduledAt?: unknown;
}

// backend model: NotificationPreference  (table: niam_notif_preferences)
export interface NotificationPreference {
  uuid: string;
  preferenceId?: unknown;
  recipientId?: unknown;
  recipientType?: unknown;
  category?: unknown;
  channel?: unknown;
  enabled?: unknown;
  quietHoursStart?: unknown;
  quietHoursEnd?: unknown;
}

// backend model: FederatedProvider  (table: niam_fed_providers)
export interface FederatedProvider {
  uuid: string;
  providerId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  providerType?: unknown;
  issuerUrl?: unknown;
  authorizationEndpoint?: unknown;
  tokenEndpoint?: unknown;
  jwksUri?: unknown;
  userinfoEndpoint?: unknown;
  clientId?: unknown;
  clientSecretEncrypted?: unknown;
  scopes?: unknown;
  redirectUris?: unknown;
  certificate?: unknown;
  signatureAlgorithm?: unknown;
  status?: unknown;
  trustAnchorId?: unknown;
  metadataUrl?: unknown;
  lastSyncAt?: unknown;
}

// backend model: FederatedIdentity  (table: niam_fed_identities)
export interface FederatedIdentity {
  uuid: string;
  fedId?: unknown;
  personId?: unknown;
  identityId?: unknown;
  providerId?: unknown;
  externalSubjectId?: unknown;
  externalAttributes?: unknown;
  linkedAt?: unknown;
  lastLoginAt?: unknown;
  status?: unknown;
  unlinkedAt?: unknown;
  unlinkReason?: unknown;
}

// backend model: IdentityLink  (table: niam_fed_links)
export interface IdentityLink {
  uuid: string;
  linkId?: unknown;
  personId?: unknown;
  sourceOrgId?: unknown;
  targetOrgId?: unknown;
  linkType?: unknown;
  externalPersonId?: unknown;
  externalIdentityId?: unknown;
  linkedAt?: unknown;
  linkedBy?: unknown;
  verifiedAt?: unknown;
  verifiedBy?: unknown;
  status?: unknown;
  expiry?: unknown;
}

// backend model: FederatedSession  (table: niam_fed_sessions)
export interface FederatedSession {
  uuid: string;
  sessionId?: unknown;
  accountId?: unknown;
  providerId?: unknown;
  fedIdentityId?: unknown;
  idToken?: unknown;
  accessTokenHash?: unknown;
  refreshTokenHash?: unknown;
  tokenType?: unknown;
  scope?: unknown;
  sessionAttributes?: unknown;
  startedAt?: unknown;
  expiresAt?: unknown;
  terminatedAt?: unknown;
}

// backend model: CrossOrganizationTrust  (table: niam_fed_cross_org_trust)
export interface CrossOrganizationTrust {
  uuid: string;
  trustId?: unknown;
  sourceOrgId?: unknown;
  targetOrgId?: unknown;
  trustType?: unknown;
  trustLevel?: unknown;
  attributeSharingAgreement?: unknown;
  permissionMapping?: unknown;
  roleMapping?: unknown;
  establishedAt?: unknown;
  establishedBy?: unknown;
  expiresAt?: unknown;
  lastReviewed?: unknown;
  status?: unknown;
}

// backend model: FederationAgreement  (table: niam_fed_agreements)
export interface FederationAgreement {
  uuid: string;
  agreementId?: unknown;
  name?: unknown;
  parties?: unknown;
  agreementType?: unknown;
  scope?: unknown;
  terms?: unknown;
  securityRequirements?: unknown;
  signedBy?: unknown;
  signedAt?: unknown;
  effectiveDate?: unknown;
  expiryDate?: unknown;
  status?: unknown;
  governingLaw?: unknown;
}

// backend model: AccountType  (table: niam_accounts)
export interface AccountType {
  uuid: string;
}

// backend model: AccountStatus  (table: niam_accounts)
export interface AccountStatus {
  uuid: string;
}

// backend model: Account  (table: niam_accounts)
export interface Account {
  uuid: string;
}

// backend model: AssignmentStatus  (table: niam_assignments)
export interface AssignmentStatus {
  uuid: string;
}

// backend model: Assignment  (table: niam_assignments)
export interface Assignment {
  uuid: string;
}

// backend model: AuditAction  (table: niam_audit_entries)
export interface AuditAction {
  uuid: string;
}

// backend model: IdentityAuditEntry  (table: niam_audit_entries)
export interface IdentityAuditEntry {
  uuid: string;
  action?: unknown;
  actorId?: unknown;
  actorType?: unknown;
  targetType?: unknown;
  targetId?: unknown;
  changes?: unknown;
  extraData?: unknown;
  context?: unknown;
  ipAddress?: unknown;
  userAgent?: unknown;
  sessionId?: unknown;
  occurredAt?: unknown;
  organizationId?: unknown;
  entryHash?: unknown;
  previousHash?: unknown;
  outcome?: unknown;
  errorMessage?: unknown;
}

// backend model: CredentialType  (table: niam_credentials)
export interface CredentialType {
  uuid: string;
}

// backend model: Credential  (table: niam_credentials)
export interface Credential {
  uuid: string;
}

// backend model: Device  (table: niam_devices)
export interface Device {
  uuid: string;
  personId?: unknown;
  accountId?: unknown;
  deviceName?: unknown;
  deviceType?: unknown;
  manufacturer?: unknown;
  model?: unknown;
  os?: unknown;
  osVersion?: unknown;
  browser?: unknown;
  browserVersion?: unknown;
  deviceFingerprint?: unknown;
  deviceId?: unknown;
  publicKey?: unknown;
  trusted?: unknown;
  trustedAt?: unknown;
  lastIp?: unknown;
  firstSeenAt?: unknown;
  lastSeenAt?: unknown;
  isLocked?: unknown;
}

// backend model: EmploymentStatus  (table: niam_employments)
export interface EmploymentStatus {
  uuid: string;
}

// backend model: Employment  (table: niam_employments)
export interface Employment {
  uuid: string;
}

// backend model: EnterpriseAccount  (table: niam_enterprise_accounts)
export interface EnterpriseAccount {
  uuid: string;
  organizationId?: unknown;
  displayName?: unknown;
  apiKeyPrefix?: unknown;
  apiKeyHash?: unknown;
  apiKeyRotatedAt?: unknown;
  oauth2ClientId?: unknown;
  oauth2ClientSecretHash?: unknown;
  certificate?: unknown;
  certificateThumbprint?: unknown;
  certificateExpires?: unknown;
  digitalSignatureKey?: unknown;
  fhirEndpoint?: unknown;
  scopes?: unknown;
  lastUsedAt?: unknown;
  notes?: unknown;
}

// backend model: IdentityType  (table: niam_identities)
export interface IdentityType {
  uuid: string;
}

// backend model: IdentityRecord  (table: niam_identities)
export interface IdentityRecord {
  uuid: string;
  personId?: unknown;
  identityType?: unknown;
  status?: unknown;
  verifiedAt?: unknown;
  verifiedBy?: unknown;
  verificationMethod?: unknown;
  issuedAt?: unknown;
  expiresAt?: unknown;
  issuedByOrganization?: unknown;
  notes?: unknown;
}

// backend model: LicenseStatus  (table: niam_licenses)
export interface LicenseStatus {
  uuid: string;
}

// backend model: ProfessionalLicense  (table: niam_licenses)
export interface ProfessionalLicense {
  uuid: string;
  personId?: unknown;
  licenseType?: unknown;
  licenseNumber?: unknown;
  licenseName?: unknown;
  issuingAuthority?: unknown;
  issuingCountry?: unknown;
  issueDate?: unknown;
  expiryDate?: unknown;
  verificationDate?: unknown;
  status?: unknown;
  statusReason?: unknown;
  boardCertification?: unknown;
  boardName?: unknown;
  boardCertifiedAt?: unknown;
  degreeType?: unknown;
  degreeName?: unknown;
  degreeInstitution?: unknown;
  degreeYear?: unknown;
  degreeCountry?: unknown;
  continuingEducationHours?: unknown;
  continuingEducationExpires?: unknown;
  verified?: unknown;
  verifiedBy?: unknown;
  attachments?: unknown;
  notes?: unknown;
}

// backend model: MachineIdentity  (table: niam_machine_identities)
export interface MachineIdentity {
  uuid: string;
  organizationId?: unknown;
  machineName?: unknown;
  machineType?: unknown;
  serialNumber?: unknown;
  ipAddress?: unknown;
  macAddress?: unknown;
  hostname?: unknown;
  os?: unknown;
  osVersion?: unknown;
  agentVersion?: unknown;
  publicKey?: unknown;
  certificateSn?: unknown;
  certificate?: unknown;
  certificateExpires?: unknown;
  assignedToPerson?: unknown;
  assignedAt?: unknown;
  location?: unknown;
  lastHeartbeat?: unknown;
  isCompromised?: unknown;
  compromisedAt?: unknown;
  notes?: unknown;
  iotDeviceType?: unknown;
  robotType?: unknown;
  aiAgentId?: unknown;
  deviceAttestation?: unknown;
  attestedAt?: unknown;
  healthStatus?: unknown;
  lastHealthCheck?: unknown;
  firmwareVersion?: unknown;
  analyzerType?: unknown;
  riskScore?: unknown;
}

// backend model: NIAMOrganization  (table: niam_organizations)
export interface NIAMOrganization {
  uuid: string;
  orgId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  orgType?: unknown;
  parentOrgId?: unknown;
  licenseNumber?: unknown;
  accreditation?: unknown;
  accreditationExpires?: unknown;
  status?: unknown;
  fhirEndpoint?: unknown;
  digitalCertificate?: unknown;
  certificateExpires?: unknown;
  contactEmail?: unknown;
  contactPhone?: unknown;
  address?: unknown;
  website?: unknown;
  governorate?: unknown;
  district?: unknown;
  subscriptions?: unknown;
  settings?: unknown;
  tags?: unknown;
}

// backend model: Person  (table: niam_persons)
export interface Person {
  uuid: string;
  nationalIdHash?: unknown;
  healthId?: unknown;
  passportNumber?: unknown;
  givenName?: unknown;
  middleName?: unknown;
  familyName?: unknown;
  fullNameAr?: unknown;
  gender?: unknown;
  birthDate?: unknown;
  nationality?: unknown;
  email?: unknown;
  phone?: unknown;
  address?: unknown;
  emergencyContactName?: unknown;
  emergencyContactPhone?: unknown;
  emergencyContactRelation?: unknown;
  isDeceased?: unknown;
  deceasedAt?: unknown;
  tags?: unknown;
  extraMetadata?: unknown;
}

// backend model: IdentityPolicy  (table: niam_policies)
export interface IdentityPolicy {
  uuid: string;
  policyId?: unknown;
  name?: unknown;
  description?: unknown;
  policyType?: unknown;
  category?: unknown;
  effect?: unknown;
  actions?: unknown;
  resources?: unknown;
  subjects?: unknown;
  conditions?: unknown;
  priority?: unknown;
  version?: unknown;
  appliesToOrgTypes?: unknown;
  startAt?: unknown;
  endAt?: unknown;
  createdBy?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  isEnabled?: unknown;
  tags?: unknown;
}

// backend model: UserSession  (table: niam_sessions)
export interface UserSession {
  uuid: string;
  accountId?: unknown;
  tokenJti?: unknown;
  refreshTokenJti?: unknown;
  sessionType?: unknown;
  ipAddress?: unknown;
  userAgent?: unknown;
  deviceId?: unknown;
  locationCity?: unknown;
  locationCountry?: unknown;
  locationLat?: unknown;
  locationLng?: unknown;
  startedAt?: unknown;
  lastActivityAt?: unknown;
  expiresAt?: unknown;
  terminatedAt?: unknown;
  terminationReason?: unknown;
  terminatedBy?: unknown;
  authMethod?: unknown;
  mfaUsed?: unknown;
  riskScore?: unknown;
  policyId?: unknown;
  governanceAction?: unknown;
  riskScoreAtLogin?: unknown;
  riskLevelAtLogin?: unknown;
}

// backend model: DigitalCertificate  (table: niam_cert_certificates)
export interface DigitalCertificate {
  uuid: string;
  certificateId?: unknown;
  serialNumber?: unknown;
  subject?: unknown;
  issuer?: unknown;
  certificateType?: unknown;
  organizationId?: unknown;
  personId?: unknown;
  machineId?: unknown;
  publicKey?: unknown;
  privateKeyEncrypted?: unknown;
  certificatePem?: unknown;
  certificateChain?: unknown;
  signatureAlgorithm?: unknown;
  keySize?: unknown;
  thumbprint?: unknown;
  issuedAt?: unknown;
  expiresAt?: unknown;
  revokedAt?: unknown;
  revocationReason?: unknown;
  revocationDate?: unknown;
  status?: unknown;
  lastRotatedAt?: unknown;
  rotationPeriodDays?: unknown;
  issuerCaId?: unknown;
}

// backend model: CertificateAuthority  (table: niam_cert_authorities)
export interface CertificateAuthority {
  uuid: string;
  caId?: unknown;
  name?: unknown;
  caType?: unknown;
  organizationId?: unknown;
  certificate?: unknown;
  privateKeyEncrypted?: unknown;
  publicKey?: unknown;
  serialNumber?: unknown;
  thumbprint?: unknown;
  validFrom?: unknown;
  validTo?: unknown;
  status?: unknown;
  signingAlgorithm?: unknown;
  keySize?: unknown;
  pathLengthConstraint?: unknown;
  issuedCertificateCount?: unknown;
  revokedCertificateCount?: unknown;
  parentCaId?: unknown;
}

// backend model: CertificateRevocationList  (table: niam_cert_crls)
export interface CertificateRevocationList {
  uuid: string;
  crlId?: unknown;
  caId?: unknown;
  crlNumber?: unknown;
  thisUpdate?: unknown;
  nextUpdate?: unknown;
  revokedCertificates?: unknown;
  crlPem?: unknown;
  signature?: unknown;
}

// backend model: APIKey  (table: niam_cert_api_keys)
export interface APIKey {
  uuid: string;
  apiKeyId?: unknown;
  keyPrefix?: unknown;
  keyHash?: unknown;
  name?: unknown;
  organizationId?: unknown;
  enterpriseAccountId?: unknown;
  personId?: unknown;
  scopes?: unknown;
  permissions?: unknown;
  allowedIps?: unknown;
  allowedReferrers?: unknown;
  rateLimit?: unknown;
  createdBy?: unknown;
  expiresAt?: unknown;
  lastUsedAt?: unknown;
  rotatedAt?: unknown;
  status?: unknown;
}

// backend model: WorkflowDefinition  (table: niam_wf_definitions)
export interface WorkflowDefinition {
  uuid: string;
  defId?: unknown;
  name?: unknown;
  description?: unknown;
  workflowType?: unknown;
  version?: unknown;
  status?: unknown;
  steps?: unknown;
  timeoutHours?: unknown;
  escalationStep?: unknown;
  retryPolicy?: unknown;
  notificationTriggers?: unknown;
}

// backend model: WorkflowInstance  (table: niam_wf_instances)
export interface WorkflowInstance {
  uuid: string;
  instanceId?: unknown;
  defId?: unknown;
  triggerType?: unknown;
  triggerId?: unknown;
  initiatorId?: unknown;
  status?: unknown;
  currentStep?: unknown;
  state?: unknown;
  context?: unknown;
  assignedTo?: unknown;
  startedAt?: unknown;
  lastActionAt?: unknown;
  completedAt?: unknown;
  slaDeadline?: unknown;
}

// backend model: WorkflowApproval  (table: niam_wf_approvals)
export interface WorkflowApproval {
  uuid: string;
  approvalId?: unknown;
  instanceId?: unknown;
  stepName?: unknown;
  approverId?: unknown;
  status?: unknown;
  comments?: unknown;
  assignedAt?: unknown;
  actionAt?: unknown;
  delegatedTo?: unknown;
  escalationReason?: unknown;
}

// backend model: WorkflowNotification  (table: niam_wf_notifications)
export interface WorkflowNotification {
  uuid: string;
  notificationId?: unknown;
  instanceId?: unknown;
  recipientId?: unknown;
  notificationType?: unknown;
  channel?: unknown;
  templateId?: unknown;
  subject?: unknown;
  body?: unknown;
  status?: unknown;
  sentAt?: unknown;
  deliveredAt?: unknown;
  readAt?: unknown;
  errorMessage?: unknown;
}

// backend model: NationalAppointment  (table: national_scheduling_appointments)
export interface NationalAppointment {
  uuid: string;
  patientId?: unknown;
  practitionerId?: unknown;
  facilityId?: unknown;
  resourceId?: unknown;
  title?: unknown;
  description?: unknown;
  startAt?: unknown;
  endAt?: unknown;
  status?: unknown;
  appointmentType?: unknown;
  recurrencePattern?: unknown;
  recurrenceEnd?: unknown;
  reminderEnabled?: unknown;
  reminderMinutesBefore?: unknown;
  notes?: unknown;
  metadata?: unknown;
  createdBy?: unknown;
  version?: unknown;
}

// backend model: NationalResource  (table: national_scheduling_resources)
export interface NationalResource {
  uuid: string;
  name?: unknown;
  type?: unknown;
  description?: unknown;
  capacity?: unknown;
  location?: unknown;
  calendarId?: unknown;
  metadata?: unknown;
}

// backend model: NationalSchedule  (table: national_scheduling_schedules)
export interface NationalSchedule {
  uuid: string;
  resourceId?: unknown;
  date?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  isAvailable?: unknown;
  slotDurationMinutes?: unknown;
}

// backend model: NationalTimeSlot  (table: national_scheduling_time_slots)
export interface NationalTimeSlot {
  uuid: string;
  scheduleId?: unknown;
  startAt?: unknown;
  endAt?: unknown;
  status?: unknown;
  bookedBy?: unknown;
  purpose?: unknown;
}

// backend model: NationalWaitingList  (table: national_scheduling_waiting_list)
export interface NationalWaitingList {
  uuid: string;
  patientId?: unknown;
  resourceId?: unknown;
  preferredDateFrom?: unknown;
  preferredDateTo?: unknown;
  preferredTimeFrom?: unknown;
  preferredTimeTo?: unknown;
  priority?: unknown;
  status?: unknown;
  notes?: unknown;
}

// backend model: NationalCalendar  (table: national_scheduling_calendars)
export interface NationalCalendar {
  uuid: string;
  name?: unknown;
  description?: unknown;
  timezone?: unknown;
  businessHours?: unknown;
  holidays?: unknown;
}

// backend model: NationalAppointmentReminder  (table: national_scheduling_appointment_reminders)
export interface NationalAppointmentReminder {
  uuid: string;
  appointmentId?: unknown;
  channel?: unknown;
  sentAt?: unknown;
  status?: unknown;
  error?: unknown;
}

// backend model: NationalMetricPoint  (table: national_observability_metrics)
export interface NationalMetricPoint {
  uuid: string;
  name?: unknown;
  type?: unknown;
  value?: unknown;
  tags?: unknown;
  timestamp?: unknown;
  resourceAttributes?: unknown;
}

// backend model: NationalTraceSpan  (table: national_observability_trace_spans)
export interface NationalTraceSpan {
  uuid: string;
  traceId?: unknown;
  parentSpanId?: unknown;
  name?: unknown;
  service?: unknown;
  operation?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  durationMs?: unknown;
  status?: unknown;
  attributes?: unknown;
  events?: unknown;
}

// backend model: NationalHealthCheck  (table: national_observability_health_checks)
export interface NationalHealthCheck {
  uuid: string;
  name?: unknown;
  component?: unknown;
  status?: unknown;
  lastCheckedAt?: unknown;
  lastSuccessAt?: unknown;
  lastFailureAt?: unknown;
  failureCount?: unknown;
  successCount?: unknown;
  details?: unknown;
  tags?: unknown;
}

// backend model: NationalAlertRule  (table: national_observability_alert_rules)
export interface NationalAlertRule {
  uuid: string;
  name?: unknown;
  metricName?: unknown;
  condition?: unknown;
  threshold?: unknown;
  durationSeconds?: unknown;
  severity?: unknown;
  channels?: unknown;
  enabled?: unknown;
}

// backend model: NationalAlertEvent  (table: national_observability_alert_events)
export interface NationalAlertEvent {
  uuid: string;
  ruleId?: unknown;
  metricValue?: unknown;
  severity?: unknown;
  status?: unknown;
  firedAt?: unknown;
  resolvedAt?: unknown;
  acknowledgedBy?: unknown;
  acknowledgedAt?: unknown;
  message?: unknown;
}

// backend model: NationalDashboard  (table: national_observability_dashboards)
export interface NationalDashboard {
  uuid: string;
  name?: unknown;
  description?: unknown;
  refreshInterval?: unknown;
  createdBy?: unknown;
}

// backend model: NationalDashboardPanel  (table: national_observability_dashboard_panels)
export interface NationalDashboardPanel {
  uuid: string;
  dashboardId?: unknown;
  title?: unknown;
  metricNames?: unknown;
  chartType?: unknown;
  width?: unknown;
  height?: unknown;
  position?: unknown;
}

// backend model: NationalServiceGraph  (table: national_observability_service_graphs)
export interface NationalServiceGraph {
  uuid: string;
  serviceName?: unknown;
  dependencies?: unknown;
  metrics?: unknown;
  health?: unknown;
}

// backend model: NationalTaskModel  (table: national_tasks)
export interface NationalTaskModel {
  uuid: string;
  title?: unknown;
  description?: unknown;
  status?: unknown;
  priority?: unknown;
  category?: unknown;
  taskType?: unknown;
  assignedTo?: unknown;
  assignedBy?: unknown;
  queueId?: unknown;
  workflowId?: unknown;
  workflowExecutionId?: unknown;
  parentTaskId?: unknown;
  slaDueAt?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  escalationLevel?: unknown;
  tags?: unknown;
  extraMetadata?: unknown;
  correlationId?: unknown;
  createdBy?: unknown;
  version?: unknown;
}

// backend model: NationalTaskQueueModel  (table: national_task_queues)
export interface NationalTaskQueueModel {
  uuid: string;
  name?: unknown;
  description?: unknown;
  assignmentStrategy?: unknown;
  maxConcurrent?: unknown;
  maxWaitingTimeS?: unknown;
  allowedRoles?: unknown;
  allowedCategories?: unknown;
}

// backend model: NationalTaskAssignmentModel  (table: national_task_assignments)
export interface NationalTaskAssignmentModel {
  uuid: string;
  taskId?: unknown;
  assigneeId?: unknown;
  assignedBy?: unknown;
  assignedAt?: unknown;
  assignmentStrategy?: unknown;
  acceptedAt?: unknown;
  completedAt?: unknown;
  status?: unknown;
}

// backend model: NationalTaskEscalationModel  (table: national_task_escalations)
export interface NationalTaskEscalationModel {
  uuid: string;
  taskId?: unknown;
  level?: unknown;
  escalatedTo?: unknown;
  escalatedBy?: unknown;
  reason?: unknown;
  escalatedAt?: unknown;
  resolvedAt?: unknown;
  status?: unknown;
}

// backend model: NationalTaskSLAModel  (table: national_task_sla_definitions)
export interface NationalTaskSLAModel {
  uuid: string;
  taskCategory?: unknown;
  taskType?: unknown;
  priority?: unknown;
  warningThresholdS?: unknown;
  breachThresholdS?: unknown;
  notificationEnabled?: unknown;
  escalationEnabled?: unknown;
}

// backend model: NationalTaskCommentModel  (table: national_task_comments)
export interface NationalTaskCommentModel {
  uuid: string;
  taskId?: unknown;
  authorId?: unknown;
  authorName?: unknown;
  content?: unknown;
}

// backend model: NationalTaskAuditLogModel  (table: national_task_audit_logs)
export interface NationalTaskAuditLogModel {
  uuid: string;
  taskId?: unknown;
  action?: unknown;
  actorId?: unknown;
  previousStatus?: unknown;
  newStatus?: unknown;
  details?: unknown;
}

// backend model: NationalDocumentModel  (table: national_documents)
export interface NationalDocumentModel {
  uuid: string;
  filename?: unknown;
  originalName?: unknown;
  mimeType?: unknown;
  format?: unknown;
  sizeBytes?: unknown;
  hashSha256?: unknown;
  version?: unknown;
  category?: unknown;
  status?: unknown;
  tags?: unknown;
  metadata?: unknown;
  retentionPolicy?: unknown;
  expiresAt?: unknown;
  createdBy?: unknown;
}

// backend model: NationalDocumentVersionModel  (table: national_document_versions)
export interface NationalDocumentVersionModel {
  uuid: string;
  documentId?: unknown;
  versionNumber?: unknown;
  filename?: unknown;
  sizeBytes?: unknown;
  hashSha256?: unknown;
  createdBy?: unknown;
  changeSummary?: unknown;
}

// backend model: NationalElectronicSignatureModel  (table: national_electronic_signatures)
export interface NationalElectronicSignatureModel {
  uuid: string;
  documentId?: unknown;
  signerId?: unknown;
  signerName?: unknown;
  signerRole?: unknown;
  signatureType?: unknown;
  certificateId?: unknown;
  signedAt?: unknown;
  expiresAt?: unknown;
  verificationUrl?: unknown;
  signatureValue?: unknown;
  status?: unknown;
  hashChainPrevious?: unknown;
  hashChainCurrent?: unknown;
}

// backend model: NationalDocumentQRCodeModel  (table: national_document_qr_codes)
export interface NationalDocumentQRCodeModel {
  uuid: string;
  documentId?: unknown;
  qrData?: unknown;
  verificationUrl?: unknown;
  generatedAt?: unknown;
  expiresAt?: unknown;
  scannedCount?: unknown;
}

// backend model: NationalDocumentAttachmentModel  (table: national_document_attachments)
export interface NationalDocumentAttachmentModel {
  uuid: string;
  documentId?: unknown;
  filename?: unknown;
  sizeBytes?: unknown;
  mimeType?: unknown;
  storagePath?: unknown;
}

// backend model: NationalRetentionRuleModel  (table: national_retention_rules)
export interface NationalRetentionRuleModel {
  uuid: string;
  category?: unknown;
  policy?: unknown;
  retentionDays?: unknown;
  actionAt?: unknown;
  archiveRequired?: unknown;
}

// backend model: RuleModel  (table: national_rules)
export interface RuleModel {
  uuid: string;
  name?: unknown;
  description?: unknown;
  category?: unknown;
  severity?: unknown;
  status?: unknown;
  conditions?: unknown;
  actions?: unknown;
  priority?: unknown;
  version?: unknown;
  tags?: unknown;
  effectiveFrom?: unknown;
  effectiveTo?: unknown;
  metadata?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
}

// backend model: RuleEvaluationLog  (table: national_rule_evaluation_logs)
export interface RuleEvaluationLog {
  uuid: string;
  ruleId?: unknown;
  ruleName?: unknown;
  category?: unknown;
  outcome?: unknown;
  severity?: unknown;
  trigger?: unknown;
  resourceType?: unknown;
  resourceId?: unknown;
  context?: unknown;
  result?: unknown;
  executionTimeMs?: unknown;
  triggeredAt?: unknown;
}

// backend model: NationalWorkflowDefinition  (table: national_workflow_definitions)
export interface NationalWorkflowDefinition {
  uuid: string;
  name?: unknown;
  description?: unknown;
  type?: unknown;
  version?: unknown;
  steps?: unknown;
  inputSchema?: unknown;
  outputSchema?: unknown;
  tags?: unknown;
  extraMetadata?: unknown;
  status?: unknown;
  timeoutPolicy?: unknown;
  compensationStrategy?: unknown;
  isTemplate?: unknown;
  createdBy?: unknown;
}

// backend model: NationalWorkflowExecution  (table: national_workflow_executions)
export interface NationalWorkflowExecution {
  uuid: string;
  workflowId?: unknown;
  workflowVersion?: unknown;
  status?: unknown;
  trigger?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  context?: unknown;
  inputData?: unknown;
  outputData?: unknown;
  currentStep?: unknown;
  error?: unknown;
  correlationId?: unknown;
  createdBy?: unknown;
}

// backend model: NationalWorkflowExecutionStep  (table: national_workflow_execution_steps)
export interface NationalWorkflowExecutionStep {
  uuid: string;
  executionId?: unknown;
  stepId?: unknown;
  stepName?: unknown;
  status?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  result?: unknown;
  error?: unknown;
  attempt?: unknown;
  assignedTo?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  durationMs?: unknown;
}

// backend model: NationalWorkflowApproval  (table: national_workflow_approvals)
export interface NationalWorkflowApproval {
  uuid: string;
  executionId?: unknown;
  stepId?: unknown;
  approverId?: unknown;
  approverName?: unknown;
  status?: unknown;
  comments?: unknown;
  assignedAt?: unknown;
  respondedAt?: unknown;
}

// backend model: NationalWorkflowCompensation  (table: national_workflow_compensations)
export interface NationalWorkflowCompensation {
  uuid: string;
  executionId?: unknown;
  stepId?: unknown;
  status?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  error?: unknown;
}

// backend model: NationalWorkflowTimer  (table: national_workflow_timers)
export interface NationalWorkflowTimer {
  uuid: string;
  executionId?: unknown;
  stepId?: unknown;
  fireAt?: unknown;
  action?: unknown;
  status?: unknown;
}

// backend model: NationalSagaLog  (table: national_saga_logs)
export interface NationalSagaLog {
  uuid: string;
  sagaId?: unknown;
  stepId?: unknown;
  stepType?: unknown;
  action?: unknown;
  status?: unknown;
  data?: unknown;
  error?: unknown;
}

// backend model: NationalWorkflowTemplate  (table: national_workflow_templates)
export interface NationalWorkflowTemplate {
  uuid: string;
  name?: unknown;
  description?: unknown;
  definition?: unknown;
  parameters?: unknown;
  category?: unknown;
  tags?: unknown;
  createdBy?: unknown;
}

// backend model: Partner  (table: ecosystem_partners)
export interface Partner {
  uuid: string;
  name?: unknown;
  orgType?: unknown;
  contactName?: unknown;
  contactEmail?: unknown;
  contactPhone?: unknown;
  status?: unknown;
  tier?: unknown;
  agreementDate?: unknown;
  agreementVersion?: unknown;
  apiQuota?: unknown;
  rateLimit?: unknown;
  createdBy?: unknown;
  metadata?: unknown;
}

// backend model: PartnerCredential  (table: ecosystem_partner_credentials)
export interface PartnerCredential {
  uuid: string;
  partnerId?: unknown;
  credentialType?: unknown;
  credentialName?: unknown;
  credentialValue?: unknown;
  expiresAt?: unknown;
  status?: unknown;
  lastUsedAt?: unknown;
}

// backend model: PartnerCertificate  (table: ecosystem_partner_certificates)
export interface PartnerCertificate {
  uuid: string;
  partnerId?: unknown;
  certificatePem?: unknown;
  certificateSerial?: unknown;
  issuer?: unknown;
  validFrom?: unknown;
  validTo?: unknown;
  status?: unknown;
  fingerprint?: unknown;
}

// backend model: PartnerRateLimit  (table: ecosystem_partner_rate_limits)
export interface PartnerRateLimit {
  uuid: string;
  partnerId?: unknown;
  endpointPattern?: unknown;
  requestsPerMinute?: unknown;
  requestsPerHour?: unknown;
  requestsPerDay?: unknown;
  concurrentLimit?: unknown;
}

// backend model: PartnerAuditLog  (table: ecosystem_partner_audit_logs)
export interface PartnerAuditLog {
  uuid: string;
  partnerId?: unknown;
  action?: unknown;
  resource?: unknown;
  details?: unknown;
  ipAddress?: unknown;
  userAgent?: unknown;
  status?: unknown;
}

// backend model: PartnerAgreement  (table: ecosystem_partner_agreements)
export interface PartnerAgreement {
  uuid: string;
  partnerId?: unknown;
  agreementType?: unknown;
  version?: unknown;
  content?: unknown;
  acceptedAt?: unknown;
  acceptedBy?: unknown;
  expiresAt?: unknown;
}

// backend model: NationalNotificationModel
export interface NationalNotificationModel {
  uuid: string;
  channel?: unknown;
  recipient?: unknown;
  recipients?: unknown;
  subject?: unknown;
  body?: unknown;
  templateId?: unknown;
  templateData?: unknown;
  priority?: unknown;
  category?: unknown;
  status?: unknown;
  scheduledAt?: unknown;
  sentAt?: unknown;
  deliveredAt?: unknown;
  readAt?: unknown;
  failedAt?: unknown;
  errorMessage?: unknown;
  extraMetadata?: unknown;
  correlationId?: unknown;
  createdBy?: unknown;
  batchId?: unknown;
}

// backend model: NationalNotificationTemplateModel
export interface NationalNotificationTemplateModel {
  uuid: string;
  name?: unknown;
  description?: unknown;
  channel?: unknown;
  language?: unknown;
  subjectTemplate?: unknown;
  bodyTemplate?: unknown;
  templateEngine?: unknown;
  variables?: unknown;
  category?: unknown;
  createdBy?: unknown;
  version?: unknown;
}

// backend model: NationalDeliveryReportModel
export interface NationalDeliveryReportModel {
  uuid: string;
  notificationId?: unknown;
  providerStatus?: unknown;
  providerMessageId?: unknown;
  providerResponse?: unknown;
  status?: unknown;
  attemptedAt?: unknown;
  deliveredAt?: unknown;
  errorMessage?: unknown;
  attempt?: unknown;
}

// backend model: NationalNotificationPreferenceModel
export interface NationalNotificationPreferenceModel {
  uuid: string;
  userId?: unknown;
  channel?: unknown;
  enabled?: unknown;
  quietHoursStart?: unknown;
  quietHoursEnd?: unknown;
  maxDaily?: unknown;
  categoriesOptIn?: unknown;
  categoriesOptOut?: unknown;
}

// backend model: NationalNotificationBatchModel
export interface NationalNotificationBatchModel {
  uuid: string;
  batchKey?: unknown;
  notificationIds?: unknown;
  status?: unknown;
  totalCount?: unknown;
  successCount?: unknown;
  failureCount?: unknown;
  createdBy?: unknown;
  completedAt?: unknown;
}

// backend model: NationalSavedSearch  (table: national_search_saved_searches)
export interface NationalSavedSearch {
  uuid: string;
  name?: unknown;
  description?: unknown;
  query?: unknown;
  indexTypes?: unknown;
  createdBy?: unknown;
  scheduled?: unknown;
  scheduleCron?: unknown;
}

// backend model: NationalSearchResult  (table: national_search_results)
export interface NationalSearchResult {
  uuid: string;
  queryId?: unknown;
  indexType?: unknown;
  resourceId?: unknown;
  resourceType?: unknown;
  score?: unknown;
  title?: unknown;
  description?: unknown;
  highlights?: unknown;
  matchedFields?: unknown;
  metadata?: unknown;
  url?: unknown;
}

// backend model: NationalJob  (table: national_background_jobs)
export interface NationalJob {
  uuid: string;
  name?: unknown;
  description?: unknown;
  type?: unknown;
  priority?: unknown;
  category?: unknown;
  maxRetries?: unknown;
  timeoutS?: unknown;
  tags?: unknown;
  metadata?: unknown;
  version?: unknown;
  status?: unknown;
  createdBy?: unknown;
}

// backend model: NationalJobSchedule  (table: national_background_job_schedules)
export interface NationalJobSchedule {
  uuid: string;
  jobId?: unknown;
  scheduleType?: unknown;
  cronExpression?: unknown;
  intervalSeconds?: unknown;
  startAt?: unknown;
  endAt?: unknown;
  lastRunAt?: unknown;
  nextRunAt?: unknown;
  timezone?: unknown;
  enabled?: unknown;
}

// backend model: NationalJobExecution  (table: national_background_job_executions)
export interface NationalJobExecution {
  uuid: string;
  jobId?: unknown;
  scheduledStart?: unknown;
  actualStart?: unknown;
  completedAt?: unknown;
  status?: unknown;
  workerId?: unknown;
  attempt?: unknown;
  result?: unknown;
  error?: unknown;
  durationMs?: unknown;
}

// backend model: NationalJobDependency  (table: national_background_job_dependencies)
export interface NationalJobDependency {
  uuid: string;
  jobId?: unknown;
  dependsOnJobId?: unknown;
  dependencyType?: unknown;
}

// backend model: DiseaseCaseModel  (table: ph_disease_cases)
export interface DiseaseCaseModel {
  uuid: string;
  diseaseCode?: unknown;
  diseaseName?: unknown;
  category?: unknown;
  region?: unknown;
  district?: unknown;
  locationLat?: unknown;
  locationLng?: unknown;
  patientAge?: unknown;
  patientGender?: unknown;
  patientNationalId?: unknown;
  isConfirmed?: unknown;
  confirmationMethod?: unknown;
  confirmationDate?: unknown;
  source?: unknown;
  reportedBy?: unknown;
  reportedAt?: unknown;
  outcome?: unknown;
  severity?: unknown;
  symptoms?: unknown;
  riskFactors?: unknown;
  exposureHistory?: unknown;
  travelHistory?: unknown;
  contactTracingCompleted?: unknown;
  contactCount?: unknown;
  notes?: unknown;
}

// backend model: OutbreakAlertModel  (table: ph_outbreak_alerts)
export interface OutbreakAlertModel {
  uuid: string;
  disease?: unknown;
  diseaseCode?: unknown;
  region?: unknown;
  district?: unknown;
  confirmedCases?: unknown;
  suspectedCases?: unknown;
  recoveredCases?: unknown;
  fatalities?: unknown;
  attackRate?: unknown;
  transmissionType?: unknown;
  alertLevel?: unknown;
  status?: unknown;
  firstDetected?: unknown;
  lastUpdated?: unknown;
  investigationNotes?: unknown;
  recommendations?: unknown;
  controlMeasures?: unknown;
  declaredBy?: unknown;
  declaredOverAt?: unknown;
  labConfirmed?: unknown;
}

// backend model: ImmunizationRecordModel  (table: ph_immunization_records)
export interface ImmunizationRecordModel {
  uuid: string;
  patientId?: unknown;
  patientName?: unknown;
  vaccine?: unknown;
  vaccineCode?: unknown;
  doseNumber?: unknown;
  totalDoses?: unknown;
  administrationDate?: unknown;
  administeredBy?: unknown;
  facilityId?: unknown;
  lotNumber?: unknown;
  expiryDate?: unknown;
  route?: unknown;
  site?: unknown;
  batchNumber?: unknown;
  manufacturer?: unknown;
  isBoosted?: unknown;
  adverseEvent?: unknown;
  consentObtained?: unknown;
  notes?: unknown;
}

// backend model: PublicHealthReportModel  (table: ph_reports)
export interface PublicHealthReportModel {
  uuid: string;
  reportType?: unknown;
  periodStart?: unknown;
  periodEnd?: unknown;
  region?: unknown;
  totalCases?: unknown;
  totalDeaths?: unknown;
  diseasesReported?: unknown;
  outbreaksActive?: unknown;
  alertsRaised?: unknown;
  vaccinationCoveragePct?: unknown;
  keyFindings?: unknown;
  recommendations?: unknown;
  publishedBy?: unknown;
  publishedAt?: unknown;
  status?: unknown;
}

// backend model: SurveillanceSignalModel  (table: ph_surveillance_signals)
export interface SurveillanceSignalModel {
  uuid: string;
  disease?: unknown;
  diseaseCode?: unknown;
  region?: unknown;
  caseCount?: unknown;
  expectedCount?: unknown;
  baselinePeriodDays?: unknown;
  zScore?: unknown;
  alertLevel?: unknown;
  detectedAt?: unknown;
  recommendation?: unknown;
  acknowledgedBy?: unknown;
  acknowledgedAt?: unknown;
}

// backend model: EnvironmentalHealthModel  (table: ph_environmental_health)
export interface EnvironmentalHealthModel {
  uuid: string;
  sampleType?: unknown;
  locationLat?: unknown;
  locationLng?: unknown;
  region?: unknown;
  district?: unknown;
  collectionDate?: unknown;
  testedFor?: unknown;
  result?: unknown;
  value?: unknown;
  unit?: unknown;
  laboratory?: unknown;
  notes?: unknown;
}

// backend model: CareJourney  (table: cc_care_journeys)
export interface CareJourney {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  episodeOfCareId?: unknown;
  careCoordinatorId?: unknown;
  organizationId?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  status?: unknown;
  journeyType?: unknown;
  diagnosisCode?: unknown;
  icd10Code?: unknown;
  diagnosisDescription?: unknown;
  milestones?: unknown;
  careTeam?: unknown;
  goals?: unknown;
  outcomes?: unknown;
  barriersToCare?: unknown;
  socialDeterminants?: unknown;
  patientFeedback?: unknown;
  patientSatisfactionScore?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: FollowUpPlan  (table: cc_follow_up_plans)
export interface FollowUpPlan {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  careJourneyId?: unknown;
  practitionerId?: unknown;
  facilityId?: unknown;
  planDate?: unknown;
  followUpDate?: unknown;
  followUpType?: unknown;
  status?: unknown;
  priority?: unknown;
  instructions?: unknown;
  clinicalChecksRequired?: unknown;
  medicationsToReview?: unknown;
  testsRequired?: unknown;
  referralsRequired?: unknown;
  reminderSent?: unknown;
  reminderSentAt?: unknown;
  reminderChannel?: unknown;
  completedAt?: unknown;
  completionNotes?: unknown;
  outcome?: unknown;
  cancelledAt?: unknown;
  cancellationReason?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: CareCoordination  (table: cc_care_coordination)
export interface CareCoordination {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  careJourneyId?: unknown;
  coordinatorId?: unknown;
  organizationId?: unknown;
  coordinationType?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  status?: unknown;
  involvedProviders?: unknown;
  involvedFacilities?: unknown;
  communicationLog?: unknown;
  sharedCarePlan?: unknown;
  appointmentsBooked?: unknown;
  referralsPlaced?: unknown;
  testsCoordinated?: unknown;
  barriersIdentified?: unknown;
  interventionsDone?: unknown;
  outcomes?: unknown;
  nextReviewDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: TransitionsOfCare  (table: cc_transitions_of_care)
export interface TransitionsOfCare {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  admissionId?: unknown;
  dischargeId?: unknown;
  encounterId?: unknown;
  transitionType?: unknown;
  transitionDate?: unknown;
  status?: unknown;
  fromFacilityId?: unknown;
  fromDepartmentId?: unknown;
  fromPractitionerId?: unknown;
  toFacilityId?: unknown;
  toDepartmentId?: unknown;
  toPractitionerId?: unknown;
  dischargeSummaryId?: unknown;
  medicationReconciliationDone?: unknown;
  followUpAppointmentMade?: unknown;
  followUpAppointmentId?: unknown;
  handoverDocuments?: unknown;
  carePlanTransferred?: unknown;
  equipmentNeedsAssessed?: unknown;
  homeCareArranged?: unknown;
  completedAt?: unknown;
  outcome?: unknown;
  issuesEncountered?: unknown;
  readmissionRiskScore?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ClinicalHandover  (table: cc_clinical_handovers)
export interface ClinicalHandover {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  transitionId?: unknown;
  handoverDate?: unknown;
  handoverType?: unknown;
  fromPractitionerId?: unknown;
  toPractitionerId?: unknown;
  clinicalSummary?: unknown;
  medications?: unknown;
  pendingResults?: unknown;
  tasksPending?: unknown;
  contingencyPlans?: unknown;
  codeStatus?: unknown;
  allergies?: unknown;
  isVerified?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  durationMinutes?: unknown;
  isEmergencyHandover?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: HomeCarePlan  (table: cc_home_care_plans)
export interface HomeCarePlan {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  careJourneyId?: unknown;
  practitionerId?: unknown;
  facilityId?: unknown;
  planDate?: unknown;
  status?: unknown;
  careType?: unknown;
  diagnosisCode?: unknown;
  icd10Code?: unknown;
  visitFrequency?: unknown;
  visitingPractitionerId?: unknown;
  caregiverInstructions?: unknown;
  medications?: unknown;
  woundCare?: unknown;
  mobilityAssistance?: unknown;
  equipmentProvided?: unknown;
  nursingProcedures?: unknown;
  rehabilitationExercises?: unknown;
  emergencyContactName?: unknown;
  emergencyContactPhone?: unknown;
  primaryCaregiverName?: unknown;
  primaryCaregiverRelation?: unknown;
  nextVisitDate?: unknown;
  reviewDate?: unknown;
  completedAt?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: CommunityCareRecord  (table: cc_community_care_records)
export interface CommunityCareRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  visitDate?: unknown;
  visitType?: unknown;
  locationLatitude?: unknown;
  locationLongitude?: unknown;
  locationAddress?: unknown;
  communityName?: unknown;
  catchmentArea?: unknown;
  householdVisit?: unknown;
  householdId?: unknown;
  servicesProvided?: unknown;
  healthEducationProvided?: unknown;
  screeningDone?: unknown;
  referralsMade?: unknown;
  environmentalObservations?: unknown;
  socialConcerns?: unknown;
  followUpRequired?: unknown;
  followUpDate?: unknown;
  outcome?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ChronicDiseaseRegistry  (table: cc_chronic_disease_registry)
export interface ChronicDiseaseRegistry {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  episodeOfCareId?: unknown;
  diseaseType?: unknown;
  severity?: unknown;
  status?: unknown;
  diagnosedBy?: unknown;
  diagnosedAt?: unknown;
  diagnosingFacilityId?: unknown;
  icd10Code?: unknown;
  diagnosisDescription?: unknown;
  onsetDate?: unknown;
  durationYears?: unknown;
  complications?: unknown;
  comorbidities?: unknown;
  riskFactors?: unknown;
  lastReviewDate?: unknown;
  nextReviewDate?: unknown;
  reviewIntervalDays?: unknown;
  careManagerId?: unknown;
  isControlled?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: DiseaseManagementPlan  (table: cc_disease_management_plans)
export interface DiseaseManagementPlan {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  registryId?: unknown;
  diseaseType?: unknown;
  severity?: unknown;
  planDate?: unknown;
  reviewDate?: unknown;
  status?: unknown;
  createdBy?: unknown;
  facilityId?: unknown;
  treatmentGoals?: unknown;
  medications?: unknown;
  lifestyleModifications?: unknown;
  monitoringParameters?: unknown;
  targetValues?: unknown;
  followUpSchedule?: unknown;
  selfManagementEducation?: unknown;
  dietaryPlan?: unknown;
  exercisePlan?: unknown;
  smokingCessation?: unknown;
  specialistReferrals?: unknown;
  alliedHealthReferrals?: unknown;
  communitySupportServices?: unknown;
  patientGoals?: unknown;
  barriersToAdherence?: unknown;
  outcomes?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ClinicalPathwayEnrollment  (table: cc_clinical_pathway_enrollments)
export interface ClinicalPathwayEnrollment {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  registryId?: unknown;
  pathwayCode?: unknown;
  pathwayName?: unknown;
  pathwayVersion?: unknown;
  enrolledBy?: unknown;
  enrolledAt?: unknown;
  facilityId?: unknown;
  status?: unknown;
  currentStep?: unknown;
  stepProgress?: unknown;
  milestones?: unknown;
  expectedDurationDays?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  completedBy?: unknown;
  outcomes?: unknown;
  deviationReason?: unknown;
  adverseEvents?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: RiskStratification  (table: cc_risk_stratification)
export interface RiskStratification {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  registryId?: unknown;
  assessmentDate?: unknown;
  stratificationType?: unknown;
  riskModel?: unknown;
  riskScore?: unknown;
  riskCategory?: unknown;
  assessedBy?: unknown;
  facilityId?: unknown;
  riskFactors?: unknown;
  protectiveFactors?: unknown;
  biometricData?: unknown;
  labResults?: unknown;
  medicationAdherence?: unknown;
  edVisitsLast6mo?: unknown;
  hospitalizationsLast6mo?: unknown;
  missedAppointmentsLast6mo?: unknown;
  recommendedInterventions?: unknown;
  careIntensity?: unknown;
  reviewDate?: unknown;
  nextAssessmentDate?: unknown;
  isHighRisk?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: SelfMonitoringRecord  (table: cc_self_monitoring_records)
export interface SelfMonitoringRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  registryId?: unknown;
  carePlanId?: unknown;
  recordedAt?: unknown;
  recordingMethod?: unknown;
  metricType?: unknown;
  metricValue?: unknown;
  metricUnit?: unknown;
  metricCategory?: unknown;
  bloodGlucoseMgdl?: unknown;
  bloodPressureSystolic?: unknown;
  bloodPressureDiastolic?: unknown;
  heartRate?: unknown;
  weightKg?: unknown;
  temperatureCelsius?: unknown;
  oxygenSaturation?: unknown;
  peakFlow?: unknown;
  painLevel?: unknown;
  symptoms?: unknown;
  medicationTaken?: unknown;
  medicationDose?: unknown;
  exerciseMinutes?: unknown;
  caloriesConsumed?: unknown;
  sleepHours?: unknown;
  mood?: unknown;
  notes?: unknown;
  deviceId?: unknown;
  deviceReadingRaw?: unknown;
  isFlagged?: unknown;
  flagReason?: unknown;
  reviewedBy?: unknown;
  reviewedAt?: unknown;
  metadata?: unknown;
}

// backend model: ImmunizationSchedule  (table: cc_immunization_schedules)
export interface ImmunizationSchedule {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  vaccineName?: unknown;
  vaccineCode?: unknown;
  scheduleType?: unknown;
  doseNumber?: unknown;
  totalDoses?: unknown;
  ageRequiredMonths?: unknown;
  ageMaxMonths?: unknown;
  dueDate?: unknown;
  status?: unknown;
  contraindicationId?: unknown;
  contraindicationNote?: unknown;
  administeredAt?: unknown;
  administeredBy?: unknown;
  administrationFacilityId?: unknown;
  lotNumber?: unknown;
  manufacturer?: unknown;
  expiryDate?: unknown;
  route?: unknown;
  site?: unknown;
  dosageMl?: unknown;
  adverseEvent?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: VaccinationRecord  (table: cc_vaccination_records)
export interface VaccinationRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  scheduleId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  administeredBy?: unknown;
  vaccineName?: unknown;
  vaccineCode?: unknown;
  doseNumber?: unknown;
  administrationDate?: unknown;
  lotNumber?: unknown;
  manufacturer?: unknown;
  expiryDate?: unknown;
  route?: unknown;
  site?: unknown;
  dosageMl?: unknown;
  isBooster?: unknown;
  isCatchup?: unknown;
  isEmergency?: unknown;
  informedConsentObtained?: unknown;
  contraindicationsScreened?: unknown;
  contraindicationFound?: unknown;
  contraindicationDetails?: unknown;
  adverseEvent?: unknown;
  adverseEventReported?: unknown;
  anaphylaxisObserved?: unknown;
  observationPeriodMinutes?: unknown;
  vaccineStockId?: unknown;
  status?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: Contraindication  (table: cc_contraindications)
export interface Contraindication {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  vaccineCode?: unknown;
  vaccineName?: unknown;
  contraindicationType?: unknown;
  isPermanent?: unknown;
  severity?: unknown;
  recordedBy?: unknown;
  recordedAt?: unknown;
  facilityId?: unknown;
  condition?: unknown;
  icd10Code?: unknown;
  details?: unknown;
  resolvedAt?: unknown;
  resolvedBy?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: VaccineInventory  (table: cc_vaccine_inventory)
export interface VaccineInventory {
  uuid: string;
  vaccineCode?: unknown;
  vaccineName?: unknown;
  manufacturer?: unknown;
  lotNumber?: unknown;
  expiryDate?: unknown;
  quantityReceived?: unknown;
  quantityAvailable?: unknown;
  quantityAdministered?: unknown;
  quantityWasted?: unknown;
  quantityExpired?: unknown;
  quantityReturns?: unknown;
  unit?: unknown;
  facilityId?: unknown;
  storageLocation?: unknown;
  receivedDate?: unknown;
  lastInventoryDate?: unknown;
  reorderLevel?: unknown;
  reorderQuantity?: unknown;
  isAvailable?: unknown;
  isQuarantined?: unknown;
  quarantineReason?: unknown;
  coldChainMonitorId?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ColdChainMonitor  (table: cc_cold_chain_monitors)
export interface ColdChainMonitor {
  uuid: string;
  facilityId?: unknown;
  equipmentType?: unknown;
  equipmentName?: unknown;
  equipmentIdentifier?: unknown;
  temperatureCelsius?: unknown;
  minTemperatureCelsius?: unknown;
  maxTemperatureCelsius?: unknown;
  humidityPercent?: unknown;
  readingTime?: unknown;
  recordedBy?: unknown;
  isWithinRange?: unknown;
  breachAlert?: unknown;
  breachDurationMinutes?: unknown;
  breachActionTaken?: unknown;
  powerOutage?: unknown;
  generatorRunning?: unknown;
  alarmTriggered?: unknown;
  vaccineCodesAffected?: unknown;
  stockAffected?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ReminderSchedule  (table: cc_reminder_schedules)
export interface ReminderSchedule {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  vaccineCode?: unknown;
  dueDate?: unknown;
  reminderType?: unknown;
  channel?: unknown;
  recipientPhone?: unknown;
  recipientEmail?: unknown;
  reminderSent?: unknown;
  sentAt?: unknown;
  sentStatus?: unknown;
  errorMessage?: unknown;
  acknowledged?: unknown;
  acknowledgedAt?: unknown;
  reminderNumber?: unknown;
  maxReminders?: unknown;
  nextReminderDate?: unknown;
  wasCompleted?: unknown;
  completedAt?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PregnancyRecord  (table: cc_pregnancy_records)
export interface PregnancyRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  status?: unknown;
  parity?: unknown;
  gravida?: unknown;
  liveBirths?: unknown;
  stillbirths?: unknown;
  miscarriages?: unknown;
  previousCSections?: unknown;
  lastMenstrualPeriod?: unknown;
  estimatedDeliveryDate?: unknown;
  gestationalAgeWeeks?: unknown;
  gestationalAgeDays?: unknown;
  bloodGroup?: unknown;
  rhFactor?: unknown;
  hbLevel?: unknown;
  highRisk?: unknown;
  riskFactors?: unknown;
  complications?: unknown;
  chronicConditions?: unknown;
  registrationDate?: unknown;
  bookedForDelivery?: unknown;
  deliveryFacilityId?: unknown;
  expectedDeliveryPlace?: unknown;
  birthPlan?: unknown;
  partnerName?: unknown;
  partnerPhone?: unknown;
  emergencyContact?: unknown;
  ancVisitsCompleted?: unknown;
  ancVisitsRequired?: unknown;
  isCompleted?: unknown;
  deliveryDate?: unknown;
  outcome?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: AntenatalCareVisit  (table: cc_antenatal_care_visits)
export interface AntenatalCareVisit {
  uuid: string;
  pregnancyId?: unknown;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  visitNumber?: unknown;
  visitDate?: unknown;
  gestationalAgeWeeks?: unknown;
  weightKg?: unknown;
  heightCm?: unknown;
  bmi?: unknown;
  bloodPressureSystolic?: unknown;
  bloodPressureDiastolic?: unknown;
  fundalHeightCm?: unknown;
  fetalHeartRate?: unknown;
  fetalPresentation?: unknown;
  uterineContractions?: unknown;
  urineTestDone?: unknown;
  urineProtein?: unknown;
  urineGlucose?: unknown;
  hemoglobinGdl?: unknown;
  bloodGlucose?: unknown;
  syphilisTest?: unknown;
  hivTest?: unknown;
  hepatitisBTest?: unknown;
  ultrasoundDone?: unknown;
  ultrasoundFindings?: unknown;
  tetanusToxoidDose?: unknown;
  ironSupplementation?: unknown;
  folicAcid?: unknown;
  calciumSupplementation?: unknown;
  dangerSignsScreened?: unknown;
  dangerSignsPresent?: unknown;
  healthEducationGiven?: unknown;
  complaints?: unknown;
  examinationFindings?: unknown;
  diagnosis?: unknown;
  treatment?: unknown;
  referralMade?: unknown;
  referralReason?: unknown;
  nextVisitDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: DeliveryRecord  (table: cc_delivery_records)
export interface DeliveryRecord {
  uuid: string;
  pregnancyId?: unknown;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  attendingPractitionerId?: unknown;
  midwifeId?: unknown;
  deliveryDate?: unknown;
  deliveryType?: unknown;
  laborDurationHours?: unknown;
  induction?: unknown;
  inductionMethod?: unknown;
  analgesiaUsed?: unknown;
  episiotomy?: unknown;
  perinealTearDegree?: unknown;
  bloodLossMl?: unknown;
  placentaComplete?: unknown;
  cordClampingDelayed?: unknown;
  skinToSkin?: unknown;
  complications?: unknown;
  maternalOutcome?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PostnatalCareVisit  (table: cc_postnatal_care_visits)
export interface PostnatalCareVisit {
  uuid: string;
  pregnancyId?: unknown;
  deliveryId?: unknown;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  visitNumber?: unknown;
  visitDate?: unknown;
  daysPostpartum?: unknown;
  maternalWeightKg?: unknown;
  bloodPressureSystolic?: unknown;
  bloodPressureDiastolic?: unknown;
  temperatureCelsius?: unknown;
  pulseRate?: unknown;
  uterineInvolution?: unknown;
  lochiaDescription?: unknown;
  perinealWoundHealing?: unknown;
  cSectionWoundHealing?: unknown;
  breastExamFindings?: unknown;
  breastFeedingEstablished?: unknown;
  breastfeedingDifficulties?: unknown;
  familyPlanningDiscussed?: unknown;
  familyPlanningMethod?: unknown;
  contraceptionProvided?: unknown;
  contraceptionMethod?: unknown;
  dangerSignsScreened?: unknown;
  dangerSignsPresent?: unknown;
  mentalHealthScreened?: unknown;
  postpartumDepressionScore?: unknown;
  complaints?: unknown;
  examinationFindings?: unknown;
  treatment?: unknown;
  referralMade?: unknown;
  referralReason?: unknown;
  nextVisitDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: GrowthMonitoring  (table: cc_growth_monitoring)
export interface GrowthMonitoring {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  measurementDate?: unknown;
  ageMonths?: unknown;
  weightKg?: unknown;
  heightCm?: unknown;
  headCircumferenceCm?: unknown;
  midUpperArmCircumferenceCm?: unknown;
  bmi?: unknown;
  weightForAgeZScore?: unknown;
  heightForAgeZScore?: unknown;
  weightForHeightZScore?: unknown;
  bmiForAgeZScore?: unknown;
  headCircumferenceZScore?: unknown;
  nutritionalStatus?: unknown;
  stunting?: unknown;
  wasting?: unknown;
  underweight?: unknown;
  overweight?: unknown;
  obesity?: unknown;
  whoGrowthPercentile?: unknown;
  growthTrend?: unknown;
  feedingType?: unknown;
  dewormingGiven?: unknown;
  vitaminASupplement?: unknown;
  ironSupplement?: unknown;
  concerns?: unknown;
  intervention?: unknown;
  referralMade?: unknown;
  followUpDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: BreastfeedingRecord  (table: cc_breastfeeding_records)
export interface BreastfeedingRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  pregnancyId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  assessmentDate?: unknown;
  isCurrentlyBreastfeeding?: unknown;
  initiationTimeHours?: unknown;
  exclusiveBreastfeeding?: unknown;
  durationWeeks?: unknown;
  frequencyPerDay?: unknown;
  bottleFeeding?: unknown;
  formulaFeeding?: unknown;
  complementaryFeedingStarted?: unknown;
  complementaryFeedingAgeMonths?: unknown;
  latchAssessment?: unknown;
  milkSupplyAdequate?: unknown;
  soreNipples?: unknown;
  mastitis?: unknown;
  engorgement?: unknown;
  tongueTie?: unknown;
  maternalNutritionAdvice?: unknown;
  breastfeedingEducation?: unknown;
  supportReferral?: unknown;
  difficulties?: unknown;
  plan?: unknown;
  nextFollowUp?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ChildDevelopmentRecord  (table: cc_child_development_records)
export interface ChildDevelopmentRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  pregnancyId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  assessmentDate?: unknown;
  ageMonths?: unknown;
  grossMotor?: unknown;
  fineMotor?: unknown;
  language?: unknown;
  socialEmotional?: unknown;
  cognitive?: unknown;
  developmentalAgeMonths?: unknown;
  developmentalQuotient?: unknown;
  developmentalScreeningTool?: unknown;
  screeningScore?: unknown;
  screeningResult?: unknown;
  developmentalDelaySuspected?: unknown;
  delayDomain?: unknown;
  hearingScreeningDone?: unknown;
  hearingScreeningResult?: unknown;
  visionScreeningDone?: unknown;
  visionScreeningResult?: unknown;
  autismScreeningDone?: unknown;
  autismScreeningScore?: unknown;
  autismScreeningResult?: unknown;
  earlyInterventionReferral?: unknown;
  earlyInterventionServices?: unknown;
  parentGuidanceProvided?: unknown;
  concerns?: unknown;
  plan?: unknown;
  followUpDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PatientTask  (table: cc_patient_tasks)
export interface PatientTask {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  careJourneyId?: unknown;
  assignedBy?: unknown;
  facilityId?: unknown;
  title?: unknown;
  description?: unknown;
  taskType?: unknown;
  category?: unknown;
  status?: unknown;
  priority?: unknown;
  dueDate?: unknown;
  completedAt?: unknown;
  completedBy?: unknown;
  completionNotes?: unknown;
  outcome?: unknown;
  cancelledAt?: unknown;
  cancellationReason?: unknown;
  reminderSent?: unknown;
  reminderSentAt?: unknown;
  reminderChannel?: unknown;
  acknowledged?: unknown;
  acknowledgedAt?: unknown;
  isPatientFacing?: unknown;
  requiresVerification?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  parentTaskId?: unknown;
  relatedTaskIds?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: EducationalMaterialAssignment  (table: cc_educational_material_assignments)
export interface EducationalMaterialAssignment {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  taskId?: unknown;
  assignedBy?: unknown;
  facilityId?: unknown;
  materialTitle?: unknown;
  materialType?: unknown;
  materialUrl?: unknown;
  language?: unknown;
  contentSummary?: unknown;
  topics?: unknown;
  assignedDate?: unknown;
  dueDate?: unknown;
  status?: unknown;
  deliveryChannel?: unknown;
  format?: unknown;
  estimatedReadTimeMinutes?: unknown;
  viewed?: unknown;
  viewedAt?: unknown;
  timeSpentSeconds?: unknown;
  comprehensionQuizScore?: unknown;
  quizPassed?: unknown;
  feedback?: unknown;
  discussedWithPractitioner?: unknown;
  discussedAt?: unknown;
  followUpNeeded?: unknown;
  completedAt?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: SelfFollowUpTask  (table: cc_self_follow_up_tasks)
export interface SelfFollowUpTask {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  parentTaskId?: unknown;
  createdBy?: unknown;
  facilityId?: unknown;
  title?: unknown;
  description?: unknown;
  taskType?: unknown;
  category?: unknown;
  status?: unknown;
  scheduledDate?: unknown;
  completedAt?: unknown;
  completionNotes?: unknown;
  outcome?: unknown;
  selfReportedData?: unknown;
  adherenceLevel?: unknown;
  barriersEncountered?: unknown;
  patientFeedback?: unknown;
  needsFollowUp?: unknown;
  followUpScheduled?: unknown;
  followUpDate?: unknown;
  reminderChannel?: unknown;
  reminderFrequency?: unknown;
  reminderCount?: unknown;
  isRecurring?: unknown;
  recurrencePattern?: unknown;
  recurrenceEndDate?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  verificationNotes?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PrimaryCareEncounter  (table: cc_primary_care_encounters)
export interface PrimaryCareEncounter {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  clinicId?: unknown;
  departmentId?: unknown;
  practitionerId?: unknown;
  encounterType?: unknown;
  encounterDate?: unknown;
  durationMinutes?: unknown;
  chiefComplaint?: unknown;
  presentingComplaint?: unknown;
  historyOfPresentingIllness?: unknown;
  vitalSigns?: unknown;
  findings?: unknown;
  assessment?: unknown;
  diagnosisCode?: unknown;
  icd10Code?: unknown;
  diagnosisDescription?: unknown;
  treatmentPlan?: unknown;
  medicationsPrescribed?: unknown;
  proceduresDone?: unknown;
  labOrders?: unknown;
  imagingOrders?: unknown;
  isTelehealth?: unknown;
  isEmergency?: unknown;
  followUpRequired?: unknown;
  followUpDate?: unknown;
  followUpStatus?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: FamilyMedicineRecord  (table: cc_family_medicine_records)
export interface FamilyMedicineRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  familyId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  facilityId?: unknown;
  recordDate?: unknown;
  familyHistory?: unknown;
  socialHistory?: unknown;
  lifestyleFactors?: unknown;
  occupationalExposures?: unknown;
  isIndexPatientForFamily?: unknown;
  relationshipToHead?: unknown;
  householdSize?: unknown;
  housingConditions?: unknown;
  waterSource?: unknown;
  sanitationType?: unknown;
  chronicDiseaseScreening?: unknown;
  riskFactors?: unknown;
  healthEducationProvided?: unknown;
  referralsMade?: unknown;
  followUpPlan?: unknown;
  nextVisitDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: CommunityClinicRecord  (table: cc_community_clinic_records)
export interface CommunityClinicRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  clinicId?: unknown;
  practitionerId?: unknown;
  visitDate?: unknown;
  visitReason?: unknown;
  complaint?: unknown;
  examinationFindings?: unknown;
  diagnosis?: unknown;
  treatmentGiven?: unknown;
  medicationsPrescribed?: unknown;
  vaccinationsGiven?: unknown;
  healthEducation?: unknown;
  isFirstVisit?: unknown;
  isFollowUp?: unknown;
  isReferralFromHospital?: unknown;
  referralSource?: unknown;
  followUpDate?: unknown;
  outcome?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PreventiveCareRecord  (table: cc_preventive_care_records)
export interface PreventiveCareRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  practitionerId?: unknown;
  facilityId?: unknown;
  serviceDate?: unknown;
  serviceType?: unknown;
  isAgeAppropriate?: unknown;
  isRiskBased?: unknown;
  riskFactor?: unknown;
  screeningType?: unknown;
  screeningResult?: unknown;
  screeningDetails?: unknown;
  counselingProvided?: unknown;
  immunizationUpdated?: unknown;
  chemoprophylaxisGiven?: unknown;
  chemoprophylaxisDetails?: unknown;
  dueDateForNext?: unknown;
  intervalMonths?: unknown;
  isCompleted?: unknown;
  outcome?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: HealthAssessment  (table: cc_health_assessments)
export interface HealthAssessment {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  facilityId?: unknown;
  assessmentDate?: unknown;
  assessmentType?: unknown;
  heightCm?: unknown;
  weightKg?: unknown;
  bmi?: unknown;
  bmiPercentile?: unknown;
  waistCircumferenceCm?: unknown;
  headCircumferenceCm?: unknown;
  bloodPressureSystolic?: unknown;
  bloodPressureDiastolic?: unknown;
  heartRate?: unknown;
  respiratoryRate?: unknown;
  temperatureCelsius?: unknown;
  oxygenSaturation?: unknown;
  bloodGlucose?: unknown;
  nutritionalStatus?: unknown;
  developmentalScreening?: unknown;
  mentalHealthScreening?: unknown;
  functionalStatus?: unknown;
  fallRisk?: unknown;
  painAssessment?: unknown;
  overallHealthScore?: unknown;
  riskCategory?: unknown;
  recommendations?: unknown;
  carePlanRecommended?: unknown;
  followUpDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: HealthProgram  (table: cc_health_programs)
export interface HealthProgram {
  uuid: string;
  programType?: unknown;
  name?: unknown;
  nameAr?: unknown;
  code?: unknown;
  description?: unknown;
  organizationId?: unknown;
  facilityId?: unknown;
  coordinatorId?: unknown;
  status?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  targetPopulation?: unknown;
  targetGeographicArea?: unknown;
  targetAgeGroupMin?: unknown;
  targetAgeGroupMax?: unknown;
  targetGender?: unknown;
  fundingSource?: unknown;
  budgetAmount?: unknown;
  budgetCurrency?: unknown;
  kpis?: unknown;
  milestones?: unknown;
  outcomes?: unknown;
  evaluationReport?: unknown;
  isNationalProgram?: unknown;
  parentProgramId?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ScreeningCampaign  (table: cc_screening_campaigns)
export interface ScreeningCampaign {
  uuid: string;
  programId?: unknown;
  organizationId?: unknown;
  facilityId?: unknown;
  coordinatorId?: unknown;
  campaignName?: unknown;
  campaignType?: unknown;
  screeningType?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  status?: unknown;
  targetCondition?: unknown;
  icd10Code?: unknown;
  screeningTool?: unknown;
  targetPopulation?: unknown;
  totalScreened?: unknown;
  totalPositive?: unknown;
  totalReferred?: unknown;
  totalConfirmed?: unknown;
  locations?: unknown;
  teams?: unknown;
  equipmentUsed?: unknown;
  resultsSummary?: unknown;
  followUpPlan?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: SchoolHealthVisit  (table: cc_school_health_visits)
export interface SchoolHealthVisit {
  uuid: string;
  programId?: unknown;
  organizationId?: unknown;
  facilityId?: unknown;
  teamLeadId?: unknown;
  schoolName?: unknown;
  schoolCode?: unknown;
  schoolAddress?: unknown;
  schoolGovernorate?: unknown;
  schoolDistrict?: unknown;
  schoolType?: unknown;
  gradeLevelsCovered?: unknown;
  visitDate?: unknown;
  visitType?: unknown;
  totalStudentsScreened?: unknown;
  totalMale?: unknown;
  totalFemale?: unknown;
  screeningTypesDone?: unknown;
  screeningsByType?: unknown;
  positiveScreens?: unknown;
  referralsMade?: unknown;
  referralsByCondition?: unknown;
  vaccinationsGiven?: unknown;
  healthEducationTopics?: unknown;
  dewormingGiven?: unknown;
  dewormingCount?: unknown;
  vitaminSupplementGiven?: unknown;
  vitaminSupplementCount?: unknown;
  environmentalAssessment?: unknown;
  waterSanitationIssues?: unknown;
  findingsSummary?: unknown;
  recommendations?: unknown;
  followUpDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: OccupationalHealthRecord  (table: cc_occupational_health_records)
export interface OccupationalHealthRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  employerName?: unknown;
  employerAddress?: unknown;
  occupation?: unknown;
  industry?: unknown;
  yearsInOccupation?: unknown;
  employmentStatus?: unknown;
  workSchedule?: unknown;
  assessmentDate?: unknown;
  assessmentType?: unknown;
  workplaceHazards?: unknown;
  exposureType?: unknown;
  exposureDurationYears?: unknown;
  ppeUsed?: unknown;
  ppeTypes?: unknown;
  physicalExamFindings?: unknown;
  hearingTestResult?: unknown;
  visionTestResult?: unknown;
  lungFunctionTest?: unknown;
  bloodTestResults?: unknown;
  dermatologicalFindings?: unknown;
  occupationalInjury?: unknown;
  injuryType?: unknown;
  injuryDate?: unknown;
  injuryDescription?: unknown;
  lostWorkDays?: unknown;
  fitnessForWork?: unknown;
  restrictions?: unknown;
  accommodationsRecommended?: unknown;
  followUpRequired?: unknown;
  nextAssessmentDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: CommunityVisit  (table: cc_community_visits)
export interface CommunityVisit {
  uuid: string;
  programId?: unknown;
  organizationId?: unknown;
  facilityId?: unknown;
  visitLeadId?: unknown;
  visitDate?: unknown;
  visitType?: unknown;
  communityName?: unknown;
  catchmentArea?: unknown;
  locationLatitude?: unknown;
  locationLongitude?: unknown;
  locationAddress?: unknown;
  totalHouseholdsVisited?: unknown;
  totalIndividualsScreened?: unknown;
  totalMale?: unknown;
  totalFemale?: unknown;
  totalChildrenUnder5?: unknown;
  totalPregnantWomen?: unknown;
  totalElderly?: unknown;
  servicesProvided?: unknown;
  healthEducationTopics?: unknown;
  screeningsDone?: unknown;
  vaccinationsGiven?: unknown;
  treatmentsGiven?: unknown;
  referralsMade?: unknown;
  referralsDetails?: unknown;
  environmentalObservations?: unknown;
  socialConcernsIdentified?: unknown;
  communityHealthIssues?: unknown;
  findingsSummary?: unknown;
  recommendations?: unknown;
  followUpRequired?: unknown;
  nextVisitDate?: unknown;
  teamMembers?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: HealthPromotionActivity  (table: cc_health_promotion_activities)
export interface HealthPromotionActivity {
  uuid: string;
  programId?: unknown;
  organizationId?: unknown;
  facilityId?: unknown;
  activityDate?: unknown;
  activityType?: unknown;
  topic?: unknown;
  description?: unknown;
  facilitatorId?: unknown;
  location?: unknown;
  venueType?: unknown;
  targetAudience?: unknown;
  totalParticipants?: unknown;
  totalMale?: unknown;
  totalFemale?: unknown;
  ageGroupChildren?: unknown;
  ageGroupAdults?: unknown;
  ageGroupElderly?: unknown;
  materialsDistributed?: unknown;
  topicsCovered?: unknown;
  keyMessages?: unknown;
  interactiveSessions?: unknown;
  demonstrationDone?: unknown;
  qAndASession?: unknown;
  feedbackReceived?: unknown;
  participantSatisfaction?: unknown;
  effectivenessRating?: unknown;
  outcomes?: unknown;
  followUpPlanned?: unknown;
  nextActivityDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ProgramEnrollment  (table: cc_program_enrollments)
export interface ProgramEnrollment {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  programId?: unknown;
  screeningCampaignId?: unknown;
  enrolledBy?: unknown;
  enrolledAt?: unknown;
  facilityId?: unknown;
  status?: unknown;
  enrollmentReason?: unknown;
  eligibilityCriteriaMet?: unknown;
  consented?: unknown;
  consentId?: unknown;
  withdrawnAt?: unknown;
  withdrawalReason?: unknown;
  baselineAssessment?: unknown;
  progressNotes?: unknown;
  outcomes?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  completedBy?: unknown;
  graduationCriteriaMet?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ReferralRequest  (table: cc_referral_requests)
export interface ReferralRequest {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  nationalReferralId?: unknown;
  encounterId?: unknown;
  direction?: unknown;
  status?: unknown;
  priority?: unknown;
  referringPractitionerId?: unknown;
  referringFacilityId?: unknown;
  referringDepartmentId?: unknown;
  receivingPractitionerId?: unknown;
  receivingFacilityId?: unknown;
  receivingDepartmentId?: unknown;
  referralReason?: unknown;
  clinicalSummary?: unknown;
  diagnosisCode?: unknown;
  icd10Code?: unknown;
  additionalNotes?: unknown;
  isCrossOrg?: unknown;
  crossOrgStatus?: unknown;
  sentAt?: unknown;
  acceptedAt?: unknown;
  completedAt?: unknown;
  cancelledAt?: unknown;
  cancellationReason?: unknown;
  metadata?: unknown;
}

// backend model: ReferralResponse  (table: cc_referral_responses)
export interface ReferralResponse {
  uuid: string;
  referralRequestId?: unknown;
  nationalReferralId?: unknown;
  respondingPractitionerId?: unknown;
  respondingFacilityId?: unknown;
  responseDate?: unknown;
  decision?: unknown;
  decisionReason?: unknown;
  responseNotes?: unknown;
  clinicalImpression?: unknown;
  recommendations?: unknown;
  followUpActions?: unknown;
  attachments?: unknown;
  metadata?: unknown;
}

// backend model: CrossOrgReferral  (table: cc_cross_org_referrals)
export interface CrossOrgReferral {
  uuid: string;
  referralRequestId?: unknown;
  nationalReferralId?: unknown;
  patientId?: unknown;
  citizenId?: unknown;
  sourceOrganizationId?: unknown;
  sourceFacilityId?: unknown;
  targetOrganizationId?: unknown;
  targetFacilityId?: unknown;
  exchangeProtocol?: unknown;
  exchangeId?: unknown;
  exchangedAt?: unknown;
  acknowledgementReceived?: unknown;
  acknowledgementAt?: unknown;
  acknowledgementStatus?: unknown;
  clinicalData?: unknown;
  attachments?: unknown;
  consentVerified?: unknown;
  consentId?: unknown;
  status?: unknown;
  errorDetails?: unknown;
  retryCount?: unknown;
  metadata?: unknown;
}

// backend model: ReferralAttachment  (table: cc_referral_attachments)
export interface ReferralAttachment {
  uuid: string;
  referralRequestId?: unknown;
  referralResponseId?: unknown;
  fileName?: unknown;
  fileType?: unknown;
  fileUrl?: unknown;
  fileSizeBytes?: unknown;
  contentHash?: unknown;
  documentType?: unknown;
  description?: unknown;
  isClinical?: unknown;
  isConfidential?: unknown;
  uploadedByPractitionerId?: unknown;
  metadata?: unknown;
}

// backend model: ReferralTimeline  (table: cc_referral_timelines)
export interface ReferralTimeline {
  uuid: string;
  referralRequestId?: unknown;
  eventType?: unknown;
  eventDate?: unknown;
  description?: unknown;
  actorPractitionerId?: unknown;
  actorFacilityId?: unknown;
  previousStatus?: unknown;
  newStatus?: unknown;
  durationHours?: unknown;
  details?: unknown;
  metadata?: unknown;
}

// backend model: AIGuardrail  (table: gov_ai_guardrails)
export interface AIGuardrail {
  uuid: string;
  guardrailCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  guardrailType?: unknown;
  description?: unknown;
  rules?: unknown;
  severity?: unknown;
  actionOnViolation?: unknown;
  metadataJson?: unknown;
}

// backend model: LLMGovernancePolicy  (table: gov_llm_policies)
export interface LLMGovernancePolicy {
  uuid: string;
  policyCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  llmProvider?: unknown;
  modelName?: unknown;
  allowedUseCases?: unknown;
  prohibitedUseCases?: unknown;
  maxTokens?: unknown;
  temperatureMax?: unknown;
  requiresHumanReview?: unknown;
  requiresApproval?: unknown;
  auditLevel?: unknown;
}

// backend model: PromptPolicy  (table: gov_prompt_policies)
export interface PromptPolicy {
  uuid: string;
  policyCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  promptTemplate?: unknown;
  allowedVariables?: unknown;
  prohibitedContent?: unknown;
  maxLength?: unknown;
  requiresSanitization?: unknown;
}

// backend model: AIAuditEvent  (table: gov_ai_audit_events)
export interface AIAuditEvent {
  uuid: string;
  action?: unknown;
  modelName?: unknown;
  modelVersion?: unknown;
  inputHash?: unknown;
  outputHash?: unknown;
  prompt?: unknown;
  response?: unknown;
  latencyMs?: unknown;
  riskLevel?: unknown;
  guardrailTriggered?: unknown;
  guardrailCodes?: unknown;
  requiresHumanReview?: unknown;
  reviewedBy?: unknown;
  reviewedAt?: unknown;
  humanApproved?: unknown;
  nodeId?: unknown;
  metadataJson?: unknown;
}

// backend model: AIRiskClassification  (table: gov_ai_risk_classifications)
export interface AIRiskClassification {
  uuid: string;
  modelName?: unknown;
  modelVersion?: unknown;
  riskLevel?: unknown;
  riskFactors?: unknown;
  clinicalImpact?: unknown;
  safetyAssessment?: unknown;
  classificationDate?: unknown;
  classifiedBy?: unknown;
  reviewDate?: unknown;
}

// backend model: AIModelValidationRecord  (table: gov_ai_model_validations)
export interface AIModelValidationRecord {
  uuid: string;
  modelName?: unknown;
  modelVersion?: unknown;
  validationType?: unknown;
  validationDate?: unknown;
  accuracy?: unknown;
  precision?: unknown;
  recall?: unknown;
  f1Score?: unknown;
  datasetUsed?: unknown;
  sampleSize?: unknown;
  passed?: unknown;
  validator?: unknown;
  reportUrl?: unknown;
  notes?: unknown;
}

// backend model: QRCodeRecord  (table: gov_qr_codes)
export interface QRCodeRecord {
  uuid: string;
  citizenId?: unknown;
  token?: unknown;
  expiresAt?: unknown;
  deactivatedAt?: unknown;
  version?: unknown;
}

// backend model: RecoveryRequestRecord  (table: gov_recovery_requests)
export interface RecoveryRequestRecord {
  uuid: string;
  citizenId?: unknown;
  method?: unknown;
  status?: unknown;
  verificationToken?: unknown;
  resolvedAt?: unknown;
  version?: unknown;
}

// backend model: GuardianRecord  (table: gov_guardians)
export interface GuardianRecord {
  uuid: string;
  citizenId?: unknown;
  guardianId?: unknown;
  guardianType?: unknown;
  relationship?: unknown;
  assignedAt?: unknown;
  revokedAt?: unknown;
  version?: unknown;
}

// backend model: ClinicalPolicy  (table: gov_clinical_policies)
export interface ClinicalPolicy {
  uuid: string;
  policyCode?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  policyType?: unknown;
  status?: unknown;
  version?: unknown;
  contentAr?: unknown;
  contentEn?: unknown;
  scope?: unknown;
  effectiveDate?: unknown;
  reviewDate?: unknown;
  approvedBy?: unknown;
  supersedesPolicyCode?: unknown;
  metadataJson?: unknown;
}

// backend model: MedicalGuideline  (table: gov_medical_guidelines)
export interface MedicalGuideline {
  uuid: string;
  guidelineCode?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  specialty?: unknown;
  issuingBody?: unknown;
  status?: unknown;
  version?: unknown;
  summaryAr?: unknown;
  summaryEn?: unknown;
  contentUrl?: unknown;
  evidenceLevel?: unknown;
  effectiveDate?: unknown;
  reviewDate?: unknown;
  metadataJson?: unknown;
}

// backend model: NationalProtocol  (table: gov_national_protocols)
export interface NationalProtocol {
  uuid: string;
  protocolCode?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  condition?: unknown;
  icd10Code?: unknown;
  status?: unknown;
  version?: unknown;
  contentAr?: unknown;
  contentEn?: unknown;
  steps?: unknown;
  decisionTree?: unknown;
  effectiveDate?: unknown;
  reviewDate?: unknown;
  metadataJson?: unknown;
}

// backend model: CriticalResultPolicy  (table: gov_critical_result_policies)
export interface CriticalResultPolicy {
  uuid: string;
  testCode?: unknown;
  testNameAr?: unknown;
  testNameEn?: unknown;
  criticalLow?: unknown;
  criticalHigh?: unknown;
  unit?: unknown;
  notifyWithinMinutes?: unknown;
  notifyRoles?: unknown;
  escalationRoles?: unknown;
  metadataJson?: unknown;
}

// backend model: RepeatTestingPolicy  (table: gov_repeat_testing_policies)
export interface RepeatTestingPolicy {
  uuid: string;
  testCode?: unknown;
  condition?: unknown;
  repeatAfterMinutes?: unknown;
  maxRepeatsPerDay?: unknown;
  requiresApproval?: unknown;
}

// backend model: DeltaCheckPolicy  (table: gov_delta_check_policies)
export interface DeltaCheckPolicy {
  uuid: string;
  testCode?: unknown;
  deltaPercent?: unknown;
  deltaAbsolute?: unknown;
  timeWindowHours?: unknown;
  action?: unknown;
}

// backend model: WestgardPolicy  (table: gov_westgard_policies)
export interface WestgardPolicy {
  uuid: string;
  testCode?: unknown;
  rules?: unknown;
  multiRuleCombinations?: unknown;
  numControlMeasurements?: unknown;
}

// backend model: ReferenceRangePolicy  (table: gov_reference_range_policies)
export interface ReferenceRangePolicy {
  uuid: string;
  testCode?: unknown;
  gender?: unknown;
  ageMinYears?: unknown;
  ageMaxYears?: unknown;
  low?: unknown;
  high?: unknown;
  unit?: unknown;
  source?: unknown;
}

// backend model: ApprovalPolicy  (table: gov_approval_policies)
export interface ApprovalPolicy {
  uuid: string;
  policyCode?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  context?: unknown;
  requiresApproval?: unknown;
  approverRole?: unknown;
  escalationRole?: unknown;
  approvalTimeoutHours?: unknown;
  autoApprove?: unknown;
}

// backend model: ConsultationPolicy  (table: gov_consultation_policies)
export interface ConsultationPolicy {
  uuid: string;
  policyCode?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  context?: unknown;
  requiresConsultation?: unknown;
  consultantSpecialty?: unknown;
  responseTimeoutHours?: unknown;
  escalationRole?: unknown;
}

// backend model: HealthNumberRecord  (table: gov_health_numbers)
export interface HealthNumberRecord {
  uuid: string;
  healthNumber?: unknown;
  citizenUlid?: unknown;
  nationalIdHash?: unknown;
  status?: unknown;
  issuedAt?: unknown;
  activatedAt?: unknown;
  lastVerifiedAt?: unknown;
  isPublic?: unknown;
  isPrinted?: unknown;
  barcodeData?: unknown;
  qrCodeData?: unknown;
  previousHealthNumber?: unknown;
  mergedIntoHealthNumber?: unknown;
  metadataJson?: unknown;
}

// backend model: HealthNumberAudit  (table: gov_health_number_audit)
export interface HealthNumberAudit {
  uuid: string;
  healthNumber?: unknown;
  event?: unknown;
  previousStatus?: unknown;
  newStatus?: unknown;
  changedBy?: unknown;
  reason?: unknown;
  ipAddress?: unknown;
}

// backend model: HealthCardLifecycle  (table: gov_health_cards)
export interface HealthCardLifecycle {
  uuid: string;
  healthNumber?: unknown;
  citizenUlid?: unknown;
  cardType?: unknown;
  cardNumber?: unknown;
  event?: unknown;
  previousCardNumber?: unknown;
  reason?: unknown;
  issuedBy?: unknown;
  issuedAt?: unknown;
  metadataJson?: unknown;
}

// backend model: MergedIdentityRecord  (table: gov_merged_identities)
export interface MergedIdentityRecord {
  uuid: string;
  primaryHealthNumber?: unknown;
  secondaryHealthNumber?: unknown;
  primaryCitizenUlid?: unknown;
  secondaryCitizenUlid?: unknown;
  action?: unknown;
  reason?: unknown;
  decisionBy?: unknown;
  occurredAt?: unknown;
  historicalDataJson?: unknown;
  isHistoricalLink?: unknown;
}

// backend model: GovernanceNode  (table: gov_hierarchy_nodes)
export interface GovernanceNode {
  uuid: string;
  nodeType?: unknown;
  code?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  parentId?: unknown;
  rootId?: unknown;
  governorate?: unknown;
  district?: unknown;
  metadataJson?: unknown;
}

// backend model: GovernanceRole  (table: gov_roles)
export interface GovernanceRole {
  uuid: string;
  nodeId?: unknown;
  roleNameAr?: unknown;
  roleNameEn?: unknown;
  permissions?: unknown;
}

// backend model: Delegation  (table: gov_delegations)
export interface Delegation {
  uuid: string;
  delegatorNodeId?: unknown;
  delegateNodeId?: unknown;
  delegationType?: unknown;
  status?: unknown;
  scope?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  reason?: unknown;
  createdBy?: unknown;
}

// backend model: ActingAppointment  (table: gov_acting_appointments)
export interface ActingAppointment {
  uuid: string;
  nodeId?: unknown;
  actingNodeId?: unknown;
  status?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  reason?: unknown;
  approvedBy?: unknown;
}

// backend model: EmergencyAdministration  (table: gov_emergency_admin)
export interface EmergencyAdministration {
  uuid: string;
  nodeId?: unknown;
  administrationType?: unknown;
  administeringNodeId?: unknown;
  status?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  declarationReason?: unknown;
  declarationOrder?: unknown;
  declaredBy?: unknown;
}

// backend model: TemporaryAdministration  (table: gov_temporary_admin)
export interface TemporaryAdministration {
  uuid: string;
  originalNodeId?: unknown;
  temporaryNodeId?: unknown;
  status?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  reason?: unknown;
  approvedBy?: unknown;
}

// backend model: GovernanceIdentityRecord  (table: gov_identity_records)
export interface GovernanceIdentityRecord {
  uuid: string;
  healthNumber?: unknown;
  nationalIdHash?: unknown;
  fullName?: unknown;
  dateOfBirth?: unknown;
  gender?: unknown;
  phone?: unknown;
  email?: unknown;
  address?: unknown;
  identityType?: unknown;
  identityStatus?: unknown;
  documentsJson?: unknown;
  relationshipsJson?: unknown;
  historyJson?: unknown;
  metadataJson?: unknown;
  version?: unknown;
}

// backend model: GovernanceBreakGlassAccess  (table: gov_break_glass_accesses)
export interface GovernanceBreakGlassAccess {
  uuid: string;
  userId?: unknown;
  userName?: unknown;
  userRole?: unknown;
  reason?: unknown;
  reasonDetail?: unknown;
  resourceType?: unknown;
  resourceId?: unknown;
  patientId?: unknown;
  accessedAt?: unknown;
  expiresAt?: unknown;
  reviewedBy?: unknown;
  reviewedAt?: unknown;
  reviewNotes?: unknown;
  version?: unknown;
}

// backend model: MergeProposal  (table: gov_merge_proposals)
export interface MergeProposal {
  uuid: string;
  proposalKey?: unknown;
  primaryHn?: unknown;
  duplicateHn?: unknown;
  confidenceScore?: unknown;
  matchedFields?: unknown;
  status?: unknown;
  reviewedBy?: unknown;
  notes?: unknown;
  version?: unknown;
  resolvedAt?: unknown;
}

// backend model: InteropProtocol  (table: gov_interop_protocols)
export interface InteropProtocol {
  uuid: string;
  protocolCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  protocolType?: unknown;
  version?: unknown;
  status?: unknown;
  specificationUrl?: unknown;
  profile?: unknown;
  implementationGuide?: unknown;
  securityProfile?: unknown;
  isMandatory?: unknown;
  effectiveDate?: unknown;
  reviewDate?: unknown;
  metadataJson?: unknown;
}

// backend model: MasterDataAgreement  (table: gov_master_data_agreements)
export interface MasterDataAgreement {
  uuid: string;
  agreementCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  domain?: unknown;
  sourceSystem?: unknown;
  targetSystem?: unknown;
  status?: unknown;
  version?: unknown;
  mappingRules?: unknown;
  syncFrequency?: unknown;
  conflictResolution?: unknown;
  effectiveDate?: unknown;
  metadataJson?: unknown;
}

// backend model: TerminologyMapping  (table: gov_terminology_mappings)
export interface TerminologyMapping {
  uuid: string;
  sourceSystem?: unknown;
  sourceCode?: unknown;
  sourceDisplay?: unknown;
  targetSystem?: unknown;
  targetCode?: unknown;
  targetDisplay?: unknown;
  mappingType?: unknown;
  equivalence?: unknown;
}

// backend model: CanonicalMapping  (table: gov_canonical_mappings)
export interface CanonicalMapping {
  uuid: string;
  canonicalType?: unknown;
  sourceSystem?: unknown;
  sourceField?: unknown;
  canonicalField?: unknown;
  transformation?: unknown;
  isRequired?: unknown;
  dataType?: unknown;
  validationRules?: unknown;
}

// backend model: LaboratoryRegistry  (table: gov_laboratory_registry)
export interface LaboratoryRegistry {
  uuid: string;
  labCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  labType?: unknown;
  organizationNodeId?: unknown;
  licenseNumber?: unknown;
  directorName?: unknown;
  address?: unknown;
  governorate?: unknown;
  district?: unknown;
  phone?: unknown;
  email?: unknown;
  accreditationBody?: unknown;
  accreditationExpiry?: unknown;
  nhopLabCode?: unknown;
  externalLabId?: unknown;
  metadataJson?: unknown;
}

// backend model: EquipmentRegistry  (table: gov_equipment_registry)
export interface EquipmentRegistry {
  uuid: string;
  labId?: unknown;
  equipmentCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  manufacturer?: unknown;
  model?: unknown;
  serialNumber?: unknown;
  category?: unknown;
  status?: unknown;
  installationDate?: unknown;
  lastMaintenanceDate?: unknown;
  nextMaintenanceDate?: unknown;
  warrantyExpiry?: unknown;
  location?: unknown;
  metadataJson?: unknown;
}

// backend model: AnalyzerRegistry  (table: gov_analyzer_registry)
export interface AnalyzerRegistry {
  uuid: string;
  labId?: unknown;
  analyzerCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  manufacturer?: unknown;
  model?: unknown;
  serialNumber?: unknown;
  analyzerType?: unknown;
  testMenu?: unknown;
  status?: unknown;
  softwareVersion?: unknown;
  interfaceType?: unknown;
  installationDate?: unknown;
  lastQcDate?: unknown;
  nextCalibrationDate?: unknown;
  metadataJson?: unknown;
}

// backend model: MaintenanceRecord  (table: gov_maintenance_records)
export interface MaintenanceRecord {
  uuid: string;
  equipmentId?: unknown;
  maintenanceType?: unknown;
  description?: unknown;
  performedBy?: unknown;
  performedDate?: unknown;
  nextMaintenanceDate?: unknown;
  cost?: unknown;
  partsReplaced?: unknown;
  status?: unknown;
  notes?: unknown;
}

// backend model: CalibrationRecord  (table: gov_calibration_records)
export interface CalibrationRecord {
  uuid: string;
  analyzerId?: unknown;
  calibrationType?: unknown;
  performedBy?: unknown;
  performedDate?: unknown;
  nextCalibrationDate?: unknown;
  calibratorLot?: unknown;
  results?: unknown;
  passed?: unknown;
  notes?: unknown;
}

// backend model: QCModRecord  (table: gov_qc_records)
export interface QCModRecord {
  uuid: string;
  labId?: unknown;
  analyzerId?: unknown;
  testCode?: unknown;
  controlLevel?: unknown;
  controlLot?: unknown;
  resultValue?: unknown;
  mean?: unknown;
  sd?: unknown;
  status?: unknown;
  westgardRulesViolated?: unknown;
  performedBy?: unknown;
  performedDate?: unknown;
  notes?: unknown;
}

// backend model: EQARecord  (table: gov_eqa_records)
export interface EQARecord {
  uuid: string;
  labId?: unknown;
  testCode?: unknown;
  schemeName?: unknown;
  roundNumber?: unknown;
  sampleId?: unknown;
  submittedResult?: unknown;
  targetValue?: unknown;
  acceptableRange?: unknown;
  zScore?: unknown;
  deviationPercent?: unknown;
  result?: unknown;
  submittedBy?: unknown;
  submittedDate?: unknown;
  reviewedBy?: unknown;
  reviewedDate?: unknown;
  correctiveAction?: unknown;
}

// backend model: ReagentInventory  (table: gov_reagent_inventory)
export interface ReagentInventory {
  uuid: string;
  labId?: unknown;
  reagentCode?: unknown;
  reagentNameAr?: unknown;
  reagentNameEn?: unknown;
  lotNumber?: unknown;
  manufacturer?: unknown;
  quantity?: unknown;
  unit?: unknown;
  receivedDate?: unknown;
  expiryDate?: unknown;
  storageCondition?: unknown;
  minimumStockLevel?: unknown;
  batchNumber?: unknown;
  metadataJson?: unknown;
}

// backend model: NationalTestDefinition  (table: gov_national_tests)
export interface NationalTestDefinition {
  uuid: string;
  testCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  category?: unknown;
  department?: unknown;
  specimenType?: unknown;
  loincCode?: unknown;
  cptCode?: unknown;
  isNationalEssential?: unknown;
  tatTargetMinutes?: unknown;
  referenceRangeSource?: unknown;
  criticalLow?: unknown;
  criticalHigh?: unknown;
  metadataJson?: unknown;
}

// backend model: NationalPanelDefinition  (table: gov_national_panels)
export interface NationalPanelDefinition {
  uuid: string;
  panelCode?: unknown;
  nameAr?: unknown;
  nameEn?: unknown;
  tests?: unknown;
  category?: unknown;
}

// backend model: NationalReferenceLab  (table: gov_national_reference_labs)
export interface NationalReferenceLab {
  uuid: string;
  labId?: unknown;
  referenceDomain?: unknown;
  isNational?: unknown;
  isRegional?: unknown;
  designationDate?: unknown;
  designationOrder?: unknown;
  accreditedStandards?: unknown;
}

// backend model: NationalAuditEvent  (table: gov_national_audit_events)
export interface NationalAuditEvent {
  uuid: string;
  eventType?: unknown;
  severity?: unknown;
  source?: unknown;
  actorId?: unknown;
  actorRole?: unknown;
  resourceType?: unknown;
  resourceId?: unknown;
  action?: unknown;
  status?: unknown;
  ipAddress?: unknown;
  userAgent?: unknown;
  details?: unknown;
  nodeId?: unknown;
}

// backend model: SecurityPolicy  (table: gov_security_policies)
export interface SecurityPolicy {
  uuid: string;
  policyCode?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  category?: unknown;
  version?: unknown;
  contentAr?: unknown;
  contentEn?: unknown;
  status?: unknown;
  effectiveDate?: unknown;
  reviewDate?: unknown;
  approvedBy?: unknown;
  metadataJson?: unknown;
}

// backend model: BreakGlassPolicy  (table: gov_break_glass_policies)
export interface BreakGlassPolicy {
  uuid: string;
  policyCode?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  allowedReasons?: unknown;
  autoApproveRoles?: unknown;
  requireApprovalRoles?: unknown;
  maxDurationMinutes?: unknown;
  notifyRoles?: unknown;
  auditRequired?: unknown;
  requireJustification?: unknown;
}

// backend model: ThreatIntelligenceEvent  (table: gov_threat_intel)
export interface ThreatIntelligenceEvent {
  uuid: string;
  threatId?: unknown;
  title?: unknown;
  description?: unknown;
  severity?: unknown;
  source?: unknown;
  affectedSystems?: unknown;
  indicators?: unknown;
  mitreAttackId?: unknown;
  detectedAt?: unknown;
  mitigatedAt?: unknown;
  status?: unknown;
}

// backend model: IncidentRecord  (table: gov_incidents)
export interface IncidentRecord {
  uuid: string;
  incidentId?: unknown;
  title?: unknown;
  description?: unknown;
  severity?: unknown;
  status?: unknown;
  category?: unknown;
  affectedNodeId?: unknown;
  detectedAt?: unknown;
  containedAt?: unknown;
  resolvedAt?: unknown;
  assignedTo?: unknown;
  resolution?: unknown;
  lessonsLearned?: unknown;
  metadataJson?: unknown;
}

// backend model: RiskRegistryItem  (table: gov_risk_registry)
export interface RiskRegistryItem {
  uuid: string;
  riskId?: unknown;
  titleAr?: unknown;
  titleEn?: unknown;
  description?: unknown;
  category?: unknown;
  likelihood?: unknown;
  impact?: unknown;
  riskScore?: unknown;
  owner?: unknown;
  mitigation?: unknown;
  contingency?: unknown;
  status?: unknown;
  targetDate?: unknown;
  reviewDate?: unknown;
  metadataJson?: unknown;
}

// backend model: HealthcareWorker  (table: gov_healthcare_workers)
export interface HealthcareWorker {
  uuid: string;
  employeeCode?: unknown;
  fullNameAr?: unknown;
  fullNameEn?: unknown;
  nationalIdHash?: unknown;
  profession?: unknown;
  specialization?: unknown;
  organizationNodeId?: unknown;
  department?: unknown;
  unit?: unknown;
  employmentDate?: unknown;
  contactPhone?: unknown;
  contactEmail?: unknown;
  metadataJson?: unknown;
}

// backend model: BoardCertification  (table: gov_board_certifications)
export interface BoardCertification {
  uuid: string;
  workerId?: unknown;
  boardName?: unknown;
  specialty?: unknown;
  certificateNumber?: unknown;
  issuingBody?: unknown;
  status?: unknown;
  issuedDate?: unknown;
  expiryDate?: unknown;
  verifiedAt?: unknown;
}

// backend model: TrainingRecord  (table: gov_training_records)
export interface TrainingRecord {
  uuid: string;
  workerId?: unknown;
  trainingName?: unknown;
  trainingType?: unknown;
  provider?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  hours?: unknown;
  certificateObtained?: unknown;
  certificateNumber?: unknown;
  completed?: unknown;
  metadataJson?: unknown;
}

// backend model: CompetencyAssessment  (table: gov_competency_assessments)
export interface CompetencyAssessment {
  uuid: string;
  workerId?: unknown;
  competencyName?: unknown;
  level?: unknown;
  assessedBy?: unknown;
  assessmentDate?: unknown;
  nextAssessmentDate?: unknown;
  score?: unknown;
  notes?: unknown;
}

// backend model: WorkerPrivilege  (table: gov_worker_privileges)
export interface WorkerPrivilege {
  uuid: string;
  workerId?: unknown;
  privilegeName?: unknown;
  scope?: unknown;
  grantedBy?: unknown;
  grantedDate?: unknown;
  expiryDate?: unknown;
}

// backend model: RotationRecord  (table: gov_rotation_records)
export interface RotationRecord {
  uuid: string;
  workerId?: unknown;
  fromDepartment?: unknown;
  toDepartment?: unknown;
  fromNodeId?: unknown;
  toNodeId?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  reason?: unknown;
  approvedBy?: unknown;
}

// backend model: AttendanceRecord  (table: gov_attendance_records)
export interface AttendanceRecord {
  uuid: string;
  workerId?: unknown;
  date?: unknown;
  checkIn?: unknown;
  checkOut?: unknown;
  status?: unknown;
  notes?: unknown;
  recordedBy?: unknown;
}

// backend model: ProductivityRecord  (table: gov_productivity_records)
export interface ProductivityRecord {
  uuid: string;
  workerId?: unknown;
  period?: unknown;
  periodStart?: unknown;
  periodEnd?: unknown;
  testsPerformed?: unknown;
  samplesProcessed?: unknown;
  reportsGenerated?: unknown;
  errorsCount?: unknown;
  tatAverageMinutes?: unknown;
  qualityScore?: unknown;
  metricsJson?: unknown;
  nationalRank?: unknown;
  governorateRank?: unknown;
  labRank?: unknown;
}

// backend model: ComponentRegistryModel  (table: lc_component_registry)
export interface ComponentRegistryModel {
  uuid: string;
  name?: unknown;
  componentType?: unknown;
  currentVersion?: unknown;
  latestVersion?: unknown;
  stage?: unknown;
  owner?: unknown;
  description?: unknown;
  repository?: unknown;
  documentationUrl?: unknown;
  dependencies?: unknown;
  tags?: unknown;
}

// backend model: ReleaseModel  (table: lc_releases)
export interface ReleaseModel {
  uuid: string;
  componentId?: unknown;
  version?: unknown;
  channel?: unknown;
  status?: unknown;
  releaseNotes?: unknown;
  changelog?: unknown;
  breakingChanges?: unknown;
  certificationLevel?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  deployedAt?: unknown;
  deployedBy?: unknown;
  artifactUrl?: unknown;
  checksum?: unknown;
  sbomUrl?: unknown;
}

// backend model: CompatibilityMatrixModel  (table: lc_compatibility_matrix)
export interface CompatibilityMatrixModel {
  uuid: string;
  componentA?: unknown;
  componentB?: unknown;
  versionA?: unknown;
  versionB?: unknown;
  level?: unknown;
  testedAt?: unknown;
  notes?: unknown;
}

// backend model: UpgradePathModel  (table: lc_upgrade_paths)
export interface UpgradePathModel {
  uuid: string;
  component?: unknown;
  fromVersion?: unknown;
  toVersion?: unknown;
  severity?: unknown;
  steps?: unknown;
  prerequisites?: unknown;
  breakingChanges?: unknown;
  estimatedDurationMinutes?: unknown;
  rollbackPlan?: unknown;
}

// backend model: DeprecationNoticeModel  (table: lc_deprecation_notices)
export interface DeprecationNoticeModel {
  uuid: string;
  componentId?: unknown;
  componentName?: unknown;
  currentVersion?: unknown;
  deprecationPolicy?: unknown;
  sunsetDate?: unknown;
  replacementComponent?: unknown;
  migrationGuide?: unknown;
  announcedAt?: unknown;
  announcedBy?: unknown;
  rescindedAt?: unknown;
}

// backend model: EmergencyDeclarationModel  (table: cc_emergency_declarations)
export interface EmergencyDeclarationModel {
  uuid: string;
  emergencyType?: unknown;
  level?: unknown;
  status?: unknown;
  region?: unknown;
  district?: unknown;
  description?: unknown;
  affectedPopulation?: unknown;
  declaredBy?: unknown;
  declaredAt?: unknown;
  resolvedAt?: unknown;
  resolvedBy?: unknown;
  activationProtocol?: unknown;
  icName?: unknown;
  icTitle?: unknown;
  icPhone?: unknown;
  commandPostLocation?: unknown;
  operationalPeriod?: unknown;
  objectives?: unknown;
  situationSummary?: unknown;
}

// backend model: ResourceRequestModel  (table: cc_resource_requests)
export interface ResourceRequestModel {
  uuid: string;
  emergencyId?: unknown;
  resourceType?: unknown;
  quantity?: unknown;
  priority?: unknown;
  status?: unknown;
  requestingFacility?: unknown;
  destinationLocation?: unknown;
  requestedBy?: unknown;
  requestedAt?: unknown;
  fulfilledQuantity?: unknown;
  fulfilledBy?: unknown;
  fulfilledAt?: unknown;
  source?: unknown;
  notes?: unknown;
}

// backend model: SituationReportModel  (table: cc_situation_reports)
export interface SituationReportModel {
  uuid: string;
  emergencyId?: unknown;
  reportNumber?: unknown;
  operationalPeriod?: unknown;
  summary?: unknown;
  keyActions?: unknown;
  resourcesDeployed?: unknown;
  casualties?: unknown;
  challenges?: unknown;
  nextSteps?: unknown;
  publishedBy?: unknown;
  publishedAt?: unknown;
}

// backend model: AfterActionReportModel  (table: cc_after_action_reports)
export interface AfterActionReportModel {
  uuid: string;
  emergencyId?: unknown;
  emergencyType?: unknown;
  region?: unknown;
  incidentDurationHours?: unknown;
  overallRating?: unknown;
  strengths?: unknown;
  weaknesses?: unknown;
  recommendations?: unknown;
  responseTimeMinutes?: unknown;
  livesSaved?: unknown;
  resourcesUsed?: unknown;
  completedBy?: unknown;
  completedAt?: unknown;
}

// backend model: DataRetentionPolicy  (table: trust_retention_policies)
export interface DataRetentionPolicy {
  uuid: string;
  dataCategory?: unknown;
  retentionPeriod?: unknown;
  retentionDays?: unknown;
  actionOnExpiry?: unknown;
  policyVersion?: unknown;
}

// backend model: SovereigntyRule  (table: trust_sovereignty_rules)
export interface SovereigntyRule {
  uuid: string;
  dataCategory?: unknown;
  sovereigntyLevel?: unknown;
  allowsCrossBorder?: unknown;
  requiresEncryption?: unknown;
  requiresConsent?: unknown;
  encryptionAlgorithm?: unknown;
  keyOwnership?: unknown;
  dataResidency?: unknown;
  ruleVersion?: unknown;
}

// backend model: TrustServiceLog  (table: trust_service_logs)
export interface TrustServiceLog {
  uuid: string;
  serviceType?: unknown;
  requestId?: unknown;
  userId?: unknown;
  labId?: unknown;
  patientId?: unknown;
  documentHash?: unknown;
  signatureValue?: unknown;
  certificateSerial?: unknown;
  timestampToken?: unknown;
  status?: unknown;
  resultHash?: unknown;
  metadataJson?: unknown;
}

// backend model: ComplianceEvidence  (table: trust_compliance_evidence)
export interface ComplianceEvidence {
  uuid: string;
  evidenceType?: unknown;
  evidenceId?: unknown;
  source?: unknown;
  collectedAt?: unknown;
  collectedBy?: unknown;
  status?: unknown;
  evidenceHash?: unknown;
  evidenceData?: unknown;
  retentionUntil?: unknown;
  chainOfCustody?: unknown;
}

// backend model: TwinType  (table: digital_twins)
export interface TwinType {
  uuid: string;
}

// backend model: SimulationStatus  (table: digital_twins)
export interface SimulationStatus {
  uuid: string;
}

// backend model: DigitalTwin  (table: digital_twins)
export interface DigitalTwin {
  uuid: string;
  twinType?: unknown;
  entityId?: unknown;
  entityType?: unknown;
  name?: unknown;
  config?: unknown;
  state?: unknown;
  metrics?: unknown;
  version?: unknown;
}

// backend model: Simulation  (table: digital_twins)
export interface Simulation {
  uuid: string;
}

// backend model: SimulationSnapshot  (table: simulation_snapshots)
export interface SimulationSnapshot {
  uuid: string;
  simulationId?: unknown;
  timestamp?: unknown;
  stateSnapshot?: unknown;
  metricsSnapshot?: unknown;
}

// backend model: Prediction  (table: predictions)
export interface Prediction {
  uuid: string;
  twinId?: unknown;
  predictionType?: unknown;
  targetDate?: unknown;
  predictedValue?: unknown;
  confidence?: unknown;
  modelName?: unknown;
  featuresUsed?: unknown;
  actualValue?: unknown;
}

// backend model: CapacityPlan  (table: capacity_plans)
export interface CapacityPlan {
  uuid: string;
  twinId?: unknown;
  planDate?: unknown;
  metric?: unknown;
  predictedDemand?: unknown;
  currentCapacity?: unknown;
  recommendedCapacity?: unknown;
  priority?: unknown;
}

// backend model: MedicalDeviceModel  (table: biomed_devices)
export interface MedicalDeviceModel {
  uuid: string;
  deviceName?: unknown;
  model?: unknown;
  manufacturer?: unknown;
  serialNumber?: unknown;
  udiDi?: unknown;
  udiPi?: unknown;
  udiFull?: unknown;
  assetTag?: unknown;
  category?: unknown;
  riskClass?: unknown;
  status?: unknown;
  locationFacilityId?: unknown;
  locationDepartment?: unknown;
  locationRoom?: unknown;
  owningDepartment?: unknown;
  responsiblePerson?: unknown;
  acquisitionDate?: unknown;
  installationDate?: unknown;
  commissioningDate?: unknown;
  warrantyStart?: unknown;
  warrantyEnd?: unknown;
  warrantyStatus?: unknown;
  expectedLifetimeYears?: unknown;
  purchaseCost?: unknown;
  currentValue?: unknown;
  requiresCalibration?: unknown;
  calibrationFrequencyDays?: unknown;
  lastCalibrationDate?: unknown;
  nextCalibrationDue?: unknown;
  requiresPm?: unknown;
  pmFrequencyDays?: unknown;
  lastPmDate?: unknown;
  nextPmDue?: unknown;
  lifecycleStage?: unknown;
  vendorId?: unknown;
  vendorName?: unknown;
  contractId?: unknown;
  powerRating?: unknown;
  dimensions?: unknown;
  weightKg?: unknown;
  softwareVersion?: unknown;
  firmwareVersion?: unknown;
  networkAddress?: unknown;
  notes?: unknown;
}

// backend model: WorkOrderModel  (table: biomed_work_orders)
export interface WorkOrderModel {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  workOrderNumber?: unknown;
  maintenanceType?: unknown;
  priority?: unknown;
  status?: unknown;
  title?: unknown;
  description?: unknown;
  reportedBy?: unknown;
  reportedDate?: unknown;
  assignedTo?: unknown;
  assignedDate?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  downtimeHours?: unknown;
  laborHours?: unknown;
  problemFound?: unknown;
  actionTaken?: unknown;
  partsUsed?: unknown;
  costParts?: unknown;
  costLabor?: unknown;
  costTotal?: unknown;
  result?: unknown;
  resultVerified?: unknown;
  notes?: unknown;
}

// backend model: CalibrationRecordModel  (table: biomed_calibrations)
export interface CalibrationRecordModel {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  calibrationNumber?: unknown;
  calibrationType?: unknown;
  status?: unknown;
  calibrationDate?: unknown;
  calibratedBy?: unknown;
  dueDate?: unknown;
  standardUsed?: unknown;
  standardId?: unknown;
  standardTraceability?: unknown;
  ambientTemperature?: unknown;
  ambientHumidity?: unknown;
  results?: unknown;
  deviations?: unknown;
  overallResult?: unknown;
  passed?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  notes?: unknown;
}

// backend model: SafetyInspectionModel  (table: biomed_safety_inspections)
export interface SafetyInspectionModel {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  inspectionDate?: unknown;
  inspectedBy?: unknown;
  inspectionType?: unknown;
  electricalSafetyPass?: unknown;
  earthLeakage?: unknown;
  groundResistance?: unknown;
  insulationResistance?: unknown;
  functionalTestPass?: unknown;
  visualInspectionPass?: unknown;
  overallResult?: unknown;
  findings?: unknown;
  recommendations?: unknown;
  nextInspectionDue?: unknown;
}

// backend model: PerformanceVerificationModel  (table: biomed_performance_verifications)
export interface PerformanceVerificationModel {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  verificationDate?: unknown;
  verifiedBy?: unknown;
  parameters?: unknown;
  results?: unknown;
  overallResult?: unknown;
  deviations?: unknown;
  notes?: unknown;
}

// backend model: DeviceIncidentModel  (table: biomed_incidents)
export interface DeviceIncidentModel {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  incidentDate?: unknown;
  reportedBy?: unknown;
  incidentType?: unknown;
  severity?: unknown;
  description?: unknown;
  patientInvolved?: unknown;
  patientImpact?: unknown;
  operatorInvolved?: unknown;
  operatorImpact?: unknown;
  immediateAction?: unknown;
  rootCause?: unknown;
  correctiveAction?: unknown;
  fdaReportable?: unknown;
  manufacturerNotified?: unknown;
  manufacturerResponse?: unknown;
  closedAt?: unknown;
  status?: unknown;
}

// backend model: DeviceRecallModel  (table: biomed_recalls)
export interface DeviceRecallModel {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  model?: unknown;
  manufacturer?: unknown;
  recallDate?: unknown;
  recallClass?: unknown;
  recallReason?: unknown;
  recallNumber?: unknown;
  fdaRecallId?: unknown;
  affectedSerialNumbers?: unknown;
  correctiveAction?: unknown;
  status?: unknown;
  completedAt?: unknown;
  notes?: unknown;
}

// backend model: TechnicianModel  (table: biomed_technicians)
export interface TechnicianModel {
  uuid: string;
  userId?: unknown;
  fullName?: unknown;
  specialization?: unknown;
  certifications?: unknown;
  phone?: unknown;
  email?: unknown;
  facilityId?: unknown;
  isAvailable?: unknown;
  maxWorkOrders?: unknown;
  skills?: unknown;
}

// backend model: SparePartModel  (table: biomed_spare_parts)
export interface SparePartModel {
  uuid: string;
  partNumber?: unknown;
  partName?: unknown;
  manufacturer?: unknown;
  compatibleModels?: unknown;
  quantityInStock?: unknown;
  minimumStock?: unknown;
  unitCost?: unknown;
  storageLocation?: unknown;
  supplierId?: unknown;
  leadTimeDays?: unknown;
}

// backend model: VendorModel  (table: biomed_vendors)
export interface VendorModel {
  uuid: string;
  vendorName?: unknown;
  vendorType?: unknown;
  contactPerson?: unknown;
  phone?: unknown;
  email?: unknown;
  address?: unknown;
  website?: unknown;
  serviceCoverage?: unknown;
  isApproved?: unknown;
  rating?: unknown;
  notes?: unknown;
}

// backend model: ServiceContractModel  (table: biomed_service_contracts)
export interface ServiceContractModel {
  uuid: string;
  deviceId?: unknown;
  vendorId?: unknown;
  contractNumber?: unknown;
  contractType?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  coverageDetails?: unknown;
  responseTimeHours?: unknown;
  annualCost?: unknown;
  includesParts?: unknown;
  includesLabor?: unknown;
  includesCalibration?: unknown;
  notes?: unknown;
}

// backend model: MaintenanceScheduleModel  (table: biomed_maintenance_schedules)
export interface MaintenanceScheduleModel {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  maintenanceType?: unknown;
  frequencyDays?: unknown;
  lastDueDate?: unknown;
  nextDueDate?: unknown;
  estimatedDurationMinutes?: unknown;
  requiredSkills?: unknown;
  checklistItems?: unknown;
}

// backend model: EmergencyIncidentModel  (table: ems_incidents)
export interface EmergencyIncidentModel {
  uuid: string;
  callerName?: unknown;
  callerPhone?: unknown;
  callerRelationship?: unknown;
  locationLat?: unknown;
  locationLng?: unknown;
  locationAddress?: unknown;
  locationDescription?: unknown;
  category?: unknown;
  priority?: unknown;
  status?: unknown;
  description?: unknown;
  symptoms?: unknown;
  patientCount?: unknown;
  patientAge?: unknown;
  patientGender?: unknown;
  patientName?: unknown;
  patientPhone?: unknown;
  patientCondition?: unknown;
  isConscious?: unknown;
  isBreathing?: unknown;
  hasPulse?: unknown;
  hasAllergies?: unknown;
  hasBleeding?: unknown;
  hasChestPain?: unknown;
  hasDifficultyBreathing?: unknown;
  isPregnant?: unknown;
  isDiabetic?: unknown;
  hasSeizure?: unknown;
  dispatcherNotes?: unknown;
  dispatchTime?: unknown;
  sceneArrivalTime?: unknown;
  sceneDepartureTime?: unknown;
  destinationArrivalTime?: unknown;
  completionTime?: unknown;
  destinationFacilityId?: unknown;
  destinationFacilityName?: unknown;
  destinationType?: unknown;
  incidentCommandId?: unknown;
  disasterEventId?: unknown;
  massCasualtyId?: unknown;
  createdBy?: unknown;
}

// backend model: DispatchAssignmentModel  (table: ems_dispatch_assignments)
export interface DispatchAssignmentModel {
  uuid: string;
  incidentId?: unknown;
  ambulanceId?: unknown;
  status?: unknown;
  assignedAt?: unknown;
  acknowledgedAt?: unknown;
  enRouteAt?: unknown;
  onSceneAt?: unknown;
  transportingAt?: unknown;
  completedAt?: unknown;
  cancelledAt?: unknown;
  cancellationReason?: unknown;
  notes?: unknown;
  createdBy?: unknown;
}

// backend model: AmbulanceModel  (table: ems_ambulances)
export interface AmbulanceModel {
  uuid: string;
  vehicleId?: unknown;
  registrationNumber?: unknown;
  callSign?: unknown;
  type?: unknown;
  status?: unknown;
  statusReason?: unknown;
  currentLocationLat?: unknown;
  currentLocationLng?: unknown;
  currentLocationUpdated?: unknown;
  stationId?: unknown;
  stationName?: unknown;
  facilityId?: unknown;
  isGpsEnabled?: unknown;
  fuelLevel?: unknown;
  mileageKm?: unknown;
  lastMaintenanceDate?: unknown;
  nextMaintenanceDue?: unknown;
  vehicleStatus?: unknown;
  equipmentInventory?: unknown;
}

// backend model: AmbulanceCrewModel  (table: ems_ambulance_crew)
export interface AmbulanceCrewModel {
  uuid: string;
  userId?: unknown;
  fullName?: unknown;
  role?: unknown;
  isAvailable?: unknown;
  stationId?: unknown;
  facilityId?: unknown;
  certifications?: unknown;
  phone?: unknown;
}

// backend model: CrewShiftModel  (table: ems_crew_shifts)
export interface CrewShiftModel {
  uuid: string;
  crewId?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  status?: unknown;
  stationId?: unknown;
  notes?: unknown;
}

// backend model: TriageAssessmentModel  (table: ems_triage_assessments)
export interface TriageAssessmentModel {
  uuid: string;
  incidentId?: unknown;
  patientId?: unknown;
  patientName?: unknown;
  patientAge?: unknown;
  patientGender?: unknown;
  category?: unknown;
  system?: unknown;
  respiratoryRate?: unknown;
  capillaryRefill?: unknown;
  heartRate?: unknown;
  systolicBp?: unknown;
  mentalStatus?: unknown;
  ambulatory?: unknown;
  externalBleeding?: unknown;
  burnsPercentage?: unknown;
  traumaScore?: unknown;
  glasgowComaScale?: unknown;
  priorityScore?: unknown;
  assessedBy?: unknown;
  assessedAt?: unknown;
  notes?: unknown;
}

// backend model: ePCRModel  (table: ems_epcr)
export interface ePCRModel {
  uuid: string;
  incidentId?: unknown;
  patientId?: unknown;
  patientName?: unknown;
  patientDob?: unknown;
  patientGender?: unknown;
  patientAddress?: unknown;
  patientPhone?: unknown;
  patientBloodGroup?: unknown;
  patientAllergies?: unknown;
  patientMedications?: unknown;
  patientMedicalHistory?: unknown;
  dispatchCallTime?: unknown;
  sceneArrivalTime?: unknown;
  patientAssessmentTime?: unknown;
  sceneDepartureTime?: unknown;
  destinationArrivalTime?: unknown;
  transferOfCareTime?: unknown;
  incidentDescription?: unknown;
  chiefComplaint?: unknown;
  historyOfPresentIllness?: unknown;
  mechanismOfInjury?: unknown;
  injuryType?: unknown;
  injuryLocation?: unknown;
  initialVitalSigns?: unknown;
  serialVitals?: unknown;
  physicalExamFindings?: unknown;
  neurologicalAssessment?: unknown;
  painAssessment?: unknown;
  painScale?: unknown;
  interventions?: unknown;
  medicationsAdministered?: unknown;
  proceduresPerformed?: unknown;
  ecgInterpretation?: unknown;
  cardiacRhythm?: unknown;
  oxygenSaturation?: unknown;
  endTidalCo2?: unknown;
  bloodGlucose?: unknown;
  etco2?: unknown;
  strokeScale?: unknown;
  traumaScore?: unknown;
  glasgowComaScale?: unknown;
  revisedTraumaScore?: unknown;
  prehospitalIndex?: unknown;
  destinationFacility?: unknown;
  destinationReason?: unknown;
  transportMode?: unknown;
  crewMembers?: unknown;
  submittingCrewMember?: unknown;
  signatures?: unknown;
  narrative?: unknown;
  notes?: unknown;
  status?: unknown;
}

// backend model: DisasterEventModel  (table: ems_disaster_events)
export interface DisasterEventModel {
  uuid: string;
  eventName?: unknown;
  disasterType?: unknown;
  phase?: unknown;
  severityLevel?: unknown;
  locationLat?: unknown;
  locationLng?: unknown;
  locationAddress?: unknown;
  region?: unknown;
  governorate?: unknown;
  description?: unknown;
  casualtiesCount?: unknown;
  fatalitiesCount?: unknown;
  missingCount?: unknown;
  displacedCount?: unknown;
  affectedPopulation?: unknown;
  incidentCommandId?: unknown;
  declaredStateOfEmergency?: unknown;
  declaredAt?: unknown;
  closedAt?: unknown;
  createdBy?: unknown;
}

// backend model: IncidentCommandModel  (table: ems_incident_commands)
export interface IncidentCommandModel {
  uuid: string;
  disasterEventId?: unknown;
  incidentName?: unknown;
  incidentNumber?: unknown;
  location?: unknown;
  commandPostLocation?: unknown;
  operationalPeriod?: unknown;
  missionStatement?: unknown;
  objectives?: unknown;
  commandStaff?: unknown;
  status?: unknown;
}

// backend model: MassCasualtyIncidentModel  (table: ems_mass_casualty_incidents)
export interface MassCasualtyIncidentModel {
  uuid: string;
  disasterEventId?: unknown;
  incidentLocation?: unknown;
  incidentType?: unknown;
  totalPatients?: unknown;
  immediateCount?: unknown;
  delayedCount?: unknown;
  minorCount?: unknown;
  expectantCount?: unknown;
  deceasedCount?: unknown;
  transportedCount?: unknown;
  hospitalsNotified?: unknown;
  resourcesDeployed?: unknown;
  triageOfficer?: unknown;
  status?: unknown;
}

// backend model: ShelterModel  (table: ems_shelters)
export interface ShelterModel {
  uuid: string;
  name?: unknown;
  disasterEventId?: unknown;
  locationLat?: unknown;
  locationLng?: unknown;
  address?: unknown;
  capacity?: unknown;
  currentOccupants?: unknown;
  shelterType?: unknown;
  contactName?: unknown;
  contactPhone?: unknown;
  suppliesLevel?: unknown;
  status?: unknown;
}

// backend model: HospitalStatusModel  (table: ems_hospital_status)
export interface HospitalStatusModel {
  uuid: string;
  facilityId?: unknown;
  facilityName?: unknown;
  capabilities?: unknown;
  totalBeds?: unknown;
  availableBeds?: unknown;
  icuBeds?: unknown;
  availableIcuBeds?: unknown;
  ventilatorsTotal?: unknown;
  ventilatorsAvailable?: unknown;
  emergencyRoomStatus?: unknown;
  traumaBaysAvailable?: unknown;
  operatingRoomsAvailable?: unknown;
  diversionStatus?: unknown;
  diversionReason?: unknown;
  lastUpdated?: unknown;
}

export type SpecimenType =
  | "WHOLE_BLOOD"
  | "SERUM"
  | "PLASMA"
  | "URINE"
  | "STOOL"
  | "CSF"
  | "SPUTUM"
  | "SWAB"
  | "TISSUE"
  | "BONE_MARROW"
  | "AMNIOTIC"
  | "PLEURAL"
  | "PERICARDIAL"
  | "PERITONEAL"
  | "SYNOVIAL"
  | "SALIVA"
  | "HAIR"
  | "NAIL"
  | "OTHER"

export const SpecimenTypeValues = [
  "WHOLE_BLOOD",
  "SERUM",
  "PLASMA",
  "URINE",
  "STOOL",
  "CSF",
  "SPUTUM",
  "SWAB",
  "TISSUE",
  "BONE_MARROW",
  "AMNIOTIC",
  "PLEURAL",
  "PERICARDIAL",
  "PERITONEAL",
  "SYNOVIAL",
  "SALIVA",
  "HAIR",
  "NAIL",
  "OTHER",
] as const;

export type SpecimenStatus =
  | "ORDERED"
  | "REGISTERED"
  | "COLLECTED"
  | "TRANSPORTING"
  | "RECEIVED"
  | "ACCEPTED"
  | "REJECTED"
  | "ALIQUOTED"
  | "PROCESSING"
  | "ANALYZING"
  | "ANALYZED"
  | "VERIFIED"
  | "VALIDATED"
  | "RELEASED"
  | "ARCHIVED"
  | "DISPOSED"

export const SpecimenStatusValues = [
  "ORDERED",
  "REGISTERED",
  "COLLECTED",
  "TRANSPORTING",
  "RECEIVED",
  "ACCEPTED",
  "REJECTED",
  "ALIQUOTED",
  "PROCESSING",
  "ANALYZING",
  "ANALYZED",
  "VERIFIED",
  "VALIDATED",
  "RELEASED",
  "ARCHIVED",
  "DISPOSED",
] as const;

export type OrderStatus =
  | "PENDING"
  | "ACCESSIONED"
  | "COLLECTING"
  | "COLLECTED"
  | "IN_TRANSPORT"
  | "RECEIVED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "VALIDATED"
  | "RELEASED"
  | "CANCELLED"
  | "CORRECTED"

export const OrderStatusValues = [
  "PENDING",
  "ACCESSIONED",
  "COLLECTING",
  "COLLECTED",
  "IN_TRANSPORT",
  "RECEIVED",
  "IN_PROGRESS",
  "COMPLETED",
  "VALIDATED",
  "RELEASED",
  "CANCELLED",
  "CORRECTED",
] as const;

export type AnalyzerStatus =
  | "ONLINE"
  | "OFFLINE"
  | "MAINTENANCE"
  | "CALIBRATING"
  | "QC_FAILED"
  | "ERROR"
  | "DISABLED"

export const AnalyzerStatusValues = [
  "ONLINE",
  "OFFLINE",
  "MAINTENANCE",
  "CALIBRATING",
  "QC_FAILED",
  "ERROR",
  "DISABLED",
] as const;

export type QCStatus =
  | "IN_CONTROL"
  | "WARNING"
  | "OUT_OF_CONTROL"
  | "NOT_RUN"

export const QCStatusValues = [
  "IN_CONTROL",
  "WARNING",
  "OUT_OF_CONTROL",
  "NOT_RUN",
] as const;

export type WestgardViolation =
  | "ONE_2S"
  | "ONE_3S"
  | "TWO_2S"
  | "R_4S"
  | "FOUR_1S"
  | "TEN_X"
  | "TWELVE_X"
  | "EIGHT_X"

export const WestgardViolationValues = [
  "ONE_2S",
  "ONE_3S",
  "TWO_2S",
  "R_4S",
  "FOUR_1S",
  "TEN_X",
  "TWELVE_X",
  "EIGHT_X",
] as const;

export type ResultFlag =
  | "NORMAL"
  | "HIGH"
  | "LOW"
  | "CRITICAL_HIGH"
  | "CRITICAL_LOW"
  | "PANIC"
  | "DELTA_FAIL"
  | "INVALID"

export const ResultFlagValues = [
  "NORMAL",
  "HIGH",
  "LOW",
  "CRITICAL_HIGH",
  "CRITICAL_LOW",
  "PANIC",
  "DELTA_FAIL",
  "INVALID",
] as const;

export type ValidationAction =
  | "AUTO_VALIDATED"
  | "MANUAL_VALIDATED"
  | "REJECTED"
  | "FLAGGED"
  | "DELTA_CHECK_FAILED"

export const ValidationActionValues = [
  "AUTO_VALIDATED",
  "MANUAL_VALIDATED",
  "REJECTED",
  "FLAGGED",
  "DELTA_CHECK_FAILED",
] as const;

export type MaintenanceType =
  | "PREVENTIVE"
  | "CORRECTIVE"
  | "PREDICTIVE"
  | "EMERGENCY"
  | "CALIBRATION"
  | "QUALIFICATION"

export const MaintenanceTypeValues = [
  "PREVENTIVE",
  "CORRECTIVE",
  "PREDICTIVE",
  "EMERGENCY",
  "CALIBRATION",
  "QUALIFICATION",
] as const;

export type CalibrationType =
  | "STANDARD"
  | "FULL"
  | "VERIFICATION"
  | "LOT_CHANGE"
  | "SCHEDULED"

export const CalibrationTypeValues = [
  "STANDARD",
  "FULL",
  "VERIFICATION",
  "LOT_CHANGE",
  "SCHEDULED",
] as const;

export type AssayCategory =
  | "CHEMISTRY"
  | "HEMATOLOGY"
  | "IMMUNOLOGY"
  | "MICROBIOLOGY"
  | "MOLECULAR"
  | "SEROLOGY"
  | "TOXICOLOGY"
  | "ENDOCRINOLOGY"
  | "COAGULATION"
  | "URINALYSIS"
  | "HISTOPATHOLOGY"
  | "CYTOLOGY"
  | "GENETICS"
  | "BLOOD_BANK"
  | "POINT_OF_CARE"
  | "OTHER"

export const AssayCategoryValues = [
  "CHEMISTRY",
  "HEMATOLOGY",
  "IMMUNOLOGY",
  "MICROBIOLOGY",
  "MOLECULAR",
  "SEROLOGY",
  "TOXICOLOGY",
  "ENDOCRINOLOGY",
  "COAGULATION",
  "URINALYSIS",
  "HISTOPATHOLOGY",
  "CYTOLOGY",
  "GENETICS",
  "BLOOD_BANK",
  "POINT_OF_CARE",
  "OTHER",
] as const;

export type TransportationCondition =
  | "AMBIENT"
  | "REFRIGERATED"
  | "FROZEN"
  | "CRYOGENIC"
  | "TEMPERATURE_CONTROLLED"

export const TransportationConditionValues = [
  "AMBIENT",
  "REFRIGERATED",
  "FROZEN",
  "CRYOGENIC",
  "TEMPERATURE_CONTROLLED",
] as const;

export type ContainerType =
  | "SST"
  | "PST"
  | "EDTA"
  | "CITRATE"
  | "HEPARIN"
  | "FLUORIDE"
  | "PLAIN"
  | "STERILE"
  | "URINE_CUP"
  | "STOOL_CUP"
  | "SWAB_RED"
  | "CULTURE_BOTTLE"
  | "BONE_MARROW"
  | "OTHER"

export const ContainerTypeValues = [
  "SST",
  "PST",
  "EDTA",
  "CITRATE",
  "HEPARIN",
  "FLUORIDE",
  "PLAIN",
  "STERILE",
  "URINE_CUP",
  "STOOL_CUP",
  "SWAB_RED",
  "CULTURE_BOTTLE",
  "BONE_MARROW",
  "OTHER",
] as const;

export type ReportStatus =
  | "DRAFT"
  | "FINAL"
  | "AMENDED"
  | "CORRECTED"
  | "CANCELLED"

export const ReportStatusValues = [
  "DRAFT",
  "FINAL",
  "AMENDED",
  "CORRECTED",
  "CANCELLED",
] as const;

// backend model: Department  (table: lims_departments)
export interface Department {
  uuid: string;
  labId?: unknown;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  description?: unknown;
  sortOrder?: unknown;
  syncId?: unknown;
  fhirId?: unknown;
  fhirResourceType?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Section  (table: lims_sections)
export interface Section {
  uuid: string;
  departmentId?: unknown;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  description?: unknown;
  syncId?: unknown;
  fhirId?: unknown;
  fhirResourceType?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Workstation  (table: lims_workstations)
export interface Workstation {
  uuid: string;
  sectionId?: unknown;
  code?: unknown;
  name?: unknown;
  workstationType?: unknown;
  syncId?: unknown;
  fhirId?: unknown;
  fhirResourceType?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Manufacturer  (table: lims_manufacturers)
export interface Manufacturer {
  uuid: string;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  website?: unknown;
  supportPhone?: unknown;
  supportEmail?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: InstrumentModel  (table: lims_instrument_models)
export interface InstrumentModel {
  uuid: string;
  manufacturerId?: unknown;
  modelCode?: unknown;
  modelName?: unknown;
  category?: unknown;
  interfaceType?: unknown;
  supportsAstm?: unknown;
  supportsHl7?: unknown;
  supportsFhir?: unknown;
  testMenuCapacity?: unknown;
  throughputPerHour?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Instrument  (table: lims_instrument_models)
export interface Instrument {
  uuid: string;
  manufacturerId?: unknown;
  modelCode?: unknown;
  modelName?: unknown;
  category?: unknown;
  interfaceType?: unknown;
  supportsAstm?: unknown;
  supportsHl7?: unknown;
  supportsFhir?: unknown;
  testMenuCapacity?: unknown;
  throughputPerHour?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Maintenance  (table: lims_departments)
export interface Maintenance {
  uuid: string;
}

// backend model: Calibration  (table: lims_departments)
export interface Calibration {
  uuid: string;
}

// backend model: QCProgram  (table: lims_qc_programs)
export interface QCProgram {
  uuid: string;
  labId?: unknown;
  code?: unknown;
  name?: unknown;
  programType?: unknown;
  testCode?: unknown;
  instrumentId?: unknown;
  ruleSet?: unknown;
  rules?: unknown;
  frequency?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: IQC  (table: lims_iqc)
export interface IQC {
  uuid: string;
  labId?: unknown;
  programId?: unknown;
  instrumentId?: unknown;
  testCode?: unknown;
  lotNumber?: unknown;
  level?: unknown;
  measuredValue?: unknown;
  expectedValue?: unknown;
  sd?: unknown;
  mean?: unknown;
  unit?: unknown;
  status?: unknown;
  violation?: unknown;
  performedBy?: unknown;
  performedAt?: unknown;
  notes?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: EQA  (table: lims_eqa)
export interface EQA {
  uuid: string;
  labId?: unknown;
  programId?: unknown;
  testCode?: unknown;
  schemeName?: unknown;
  roundNumber?: unknown;
  sampleId?: unknown;
  submittedValue?: unknown;
  targetValue?: unknown;
  acceptableRange?: unknown;
  zScore?: unknown;
  deviationPercent?: unknown;
  result?: unknown;
  submittedBy?: unknown;
  submittedAt?: unknown;
  reviewedBy?: unknown;
  reviewedAt?: unknown;
  correctiveAction?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Lot  (table: lims_lots)
export interface Lot {
  uuid: string;
  labId?: unknown;
  lotNumber?: unknown;
  itemType?: unknown;
  itemCode?: unknown;
  itemName?: unknown;
  manufacturerId?: unknown;
  quantity?: unknown;
  unit?: unknown;
  receivedAt?: unknown;
  expiryAt?: unknown;
  openedAt?: unknown;
  openedBy?: unknown;
  storageCondition?: unknown;
  certificate?: unknown;
  isConsumed?: unknown;
  consumedAt?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Reagent  (table: lims_reagents)
export interface Reagent {
  uuid: string;
  labId?: unknown;
  reagentCode?: unknown;
  reagentName?: unknown;
  reagentNameAr?: unknown;
  lotId?: unknown;
  manufacturerId?: unknown;
  supplierId?: unknown;
  category?: unknown;
  currentQuantity?: unknown;
  unit?: unknown;
  minimumQuantity?: unknown;
  maximumQuantity?: unknown;
  storageLocation?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Supplier  (table: lims_suppliers)
export interface Supplier {
  uuid: string;
  labId?: unknown;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  contactPerson?: unknown;
  phone?: unknown;
  email?: unknown;
  address?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Consumable  (table: lims_consumables)
export interface Consumable {
  uuid: string;
  labId?: unknown;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  lotId?: unknown;
  supplierId?: unknown;
  category?: unknown;
  currentQuantity?: unknown;
  unit?: unknown;
  minimumQuantity?: unknown;
  storageLocation?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: Storage  (table: lims_storage)
export interface Storage {
  uuid: string;
  labId?: unknown;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  storageType?: unknown;
  temperatureMin?: unknown;
  temperatureMax?: unknown;
  location?: unknown;
  capacity?: unknown;
  parentId?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: TemperatureLog  (table: lims_temperature_logs)
export interface TemperatureLog {
  uuid: string;
  labId?: unknown;
  storageId?: unknown;
  temperature?: unknown;
  unit?: unknown;
  recordedAt?: unknown;
  recordedBy?: unknown;
  isBreach?: unknown;
  breachNotes?: unknown;
  syncId?: unknown;
}

// backend model: EquipmentLog  (table: lims_equipment_logs)
export interface EquipmentLog {
  uuid: string;
  instrumentId?: unknown;
  eventType?: unknown;
  description?: unknown;
  loggedBy?: unknown;
  loggedAt?: unknown;
  metadataJson?: unknown;
  syncId?: unknown;
  version?: unknown;
}

// backend model: SpecimenCatalog  (table: lims_specimen_catalog)
export interface SpecimenCatalog {
  uuid: string;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  description?: unknown;
  defaultContainerType?: unknown;
  defaultVolumeMl?: unknown;
  storageCondition?: unknown;
  stabilityHours?: unknown;
  loincCode?: unknown;
  snomedCode?: unknown;
  syncId?: unknown;
  version?: unknown;
}

// backend model: Container  (table: lims_departments)
export interface Container {
  uuid: string;
}

// backend model: Specimen  (table: lims_departments)
export interface Specimen {
  uuid: string;
}

// backend model: Transportation  (table: lims_departments)
export interface Transportation {
  uuid: string;
}

// backend model: ChainOfCustody  (table: lims_chain_of_custody)
export interface ChainOfCustody {
  uuid: string;
  specimenId?: unknown;
  eventType?: unknown;
  fromPerson?: unknown;
  toPerson?: unknown;
  timestamp?: unknown;
  reason?: unknown;
  signature?: unknown;
  previousHash?: unknown;
  currentHash?: unknown;
  syncId?: unknown;
  createdBy?: unknown;
  version?: unknown;
}

// backend model: Order  (table: lims_departments)
export interface Order {
  uuid: string;
}

// backend model: Panel  (table: lims_panels)
export interface Panel {
  uuid: string;
  labId?: unknown;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  category?: unknown;
  description?: unknown;
  tatTargetMinutes?: unknown;
  isNationalEssential?: unknown;
  departmentId?: unknown;
  syncId?: unknown;
  fhirId?: unknown;
  fhirResourceType?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: PanelTest  (table: lims_panel_tests)
export interface PanelTest {
  uuid: string;
  panelId?: unknown;
  testCode?: unknown;
  displayOrder?: unknown;
  isRequired?: unknown;
}

// backend model: Result  (table: lims_departments)
export interface Result {
  uuid: string;
}

// backend model: ReferenceRangeDef  (table: lims_reference_ranges)
export interface ReferenceRangeDef {
  uuid: string;
  testCode?: unknown;
  labId?: unknown;
  instrumentId?: unknown;
  method?: unknown;
  gender?: unknown;
  ageMinYears?: unknown;
  ageMaxYears?: unknown;
  ageMinDays?: unknown;
  ageMaxDays?: unknown;
  refRangeLow?: unknown;
  refRangeHigh?: unknown;
  refRangeText?: unknown;
  criticalLow?: unknown;
  criticalHigh?: unknown;
  panicLow?: unknown;
  panicHigh?: unknown;
  unit?: unknown;
  source?: unknown;
  effectiveFrom?: unknown;
  effectiveUntil?: unknown;
  syncId?: unknown;
  version?: unknown;
  isDeleted?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
}

// backend model: AutoValidationRule  (table: lims_auto_validation_rules)
export interface AutoValidationRule {
  uuid: string;
  labId?: unknown;
  ruleName?: unknown;
  testCode?: unknown;
  ruleType?: unknown;
  conditions?: unknown;
  action?: unknown;
  priority?: unknown;
  syncId?: unknown;
  version?: unknown;
  isDeleted?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
}

// backend model: DeltaCheckRule  (table: lims_delta_check_rules)
export interface DeltaCheckRule {
  uuid: string;
  labId?: unknown;
  testCode?: unknown;
  testName?: unknown;
  deltaPercent?: unknown;
  deltaAbsolute?: unknown;
  windowDays?: unknown;
  appliesTo?: unknown;
  action?: unknown;
  syncId?: unknown;
  version?: unknown;
  isDeleted?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
}

// backend model: ResultValidation  (table: lims_result_validations)
export interface ResultValidation {
  uuid: string;
  resultId?: unknown;
  action?: unknown;
  validatedBy?: unknown;
  validatedAt?: unknown;
  notes?: unknown;
  isElectronicSignature?: unknown;
  signatureData?: unknown;
  syncId?: unknown;
  version?: unknown;
}

// backend model: ResultRelease  (table: lims_result_releases)
export interface ResultRelease {
  uuid: string;
  labId?: unknown;
  orderId?: unknown;
  releasedBy?: unknown;
  releasedAt?: unknown;
  releaseChannel?: unknown;
  isPatientNotified?: unknown;
  notifiedAt?: unknown;
  syncId?: unknown;
  version?: unknown;
}

// backend model: ElectronicSignature  (table: lims_electronic_signatures)
export interface ElectronicSignature {
  uuid: string;
  labId?: unknown;
  userId?: unknown;
  signatureType?: unknown;
  resourceType?: unknown;
  resourceId?: unknown;
  signatureHash?: unknown;
  signedAt?: unknown;
  expiresAt?: unknown;
  isRevoked?: unknown;
  revokedAt?: unknown;
  syncId?: unknown;
  version?: unknown;
}

// backend model: LabReport  (table: lims_reports)
export interface LabReport {
  uuid: string;
  labId?: unknown;
  orderId?: unknown;
  reportNumber?: unknown;
  status?: unknown;
  title?: unknown;
  titleAr?: unknown;
  reportFormat?: unknown;
  generatedBy?: unknown;
  generatedAt?: unknown;
  finalizedBy?: unknown;
  finalizedAt?: unknown;
  correctedBy?: unknown;
  correctedAt?: unknown;
  correctionReason?: unknown;
  isElectronic?: unknown;
  isPrinted?: unknown;
  printedAt?: unknown;
  printedBy?: unknown;
  watermark?: unknown;
  locale?: unknown;
  syncId?: unknown;
  fhirId?: unknown;
  fhirResourceType?: unknown;
  createdBy?: unknown;
  updatedBy?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: ReportAttachment  (table: lims_report_attachments)
export interface ReportAttachment {
  uuid: string;
  reportId?: unknown;
  fileName?: unknown;
  fileType?: unknown;
  fileSizeBytes?: unknown;
  storagePath?: unknown;
  isWatermarked?: unknown;
  uploadedBy?: unknown;
  uploadedAt?: unknown;
  syncId?: unknown;
  version?: unknown;
  isDeleted?: unknown;
}

// backend model: SituationRoomStatus  (table: situation_rooms)
export interface SituationRoomStatus {
  uuid: string;
}

// backend model: SituationRoom  (table: situation_rooms)
export interface SituationRoom {
  uuid: string;
}

// backend model: NationalKPI  (table: national_kpis)
export interface NationalKPI {
  uuid: string;
  kpiName?: unknown;
  kpiCategory?: unknown;
  kpiValue?: unknown;
  targetValue?: unknown;
  unit?: unknown;
  region?: unknown;
  labId?: unknown;
  measuredAt?: unknown;
}

// backend model: IncidentIntelligence  (table: incident_intelligence)
export interface IncidentIntelligence {
  uuid: string;
  incidentType?: unknown;
  severity?: unknown;
  title?: unknown;
  description?: unknown;
  affectedEntities?: unknown;
  rootCause?: unknown;
  impactAnalysis?: unknown;
  recommendation?: unknown;
  status?: unknown;
  detectedAt?: unknown;
  resolvedAt?: unknown;
}

// backend model: CapacityIntelligence  (table: capacity_intelligence)
export interface CapacityIntelligence {
  uuid: string;
  entityType?: unknown;
  entityId?: unknown;
  metric?: unknown;
  currentValue?: unknown;
  threshold?: unknown;
  trend?: unknown;
  forecast?: unknown;
  recommendation?: unknown;
  generatedAt?: unknown;
}

// backend model: AIRecommendation  (table: ai_recommendations)
export interface AIRecommendation {
  uuid: string;
  recommendationType?: unknown;
  priority?: unknown;
  title?: unknown;
  description?: unknown;
  expectedImpact?: unknown;
  riskAssessment?: unknown;
  status?: unknown;
  createdBy?: unknown;
  reviewedBy?: unknown;
  implementedAt?: unknown;
}

// backend model: BloodDonorModel  (table: blood_bank_donors)
export interface BloodDonorModel {
  uuid: string;
  citizenId?: unknown;
  nationalId?: unknown;
  fullName?: unknown;
  phone?: unknown;
  email?: unknown;
  dateOfBirth?: unknown;
  gender?: unknown;
  bloodGroup?: unknown;
  rhFactor?: unknown;
  weightKg?: unknown;
  heightCm?: unknown;
  hemoglobinGDl?: unknown;
  status?: unknown;
  totalDonations?: unknown;
  totalVolumeMl?: unknown;
  lastDonationDate?: unknown;
  nextEligibleDate?: unknown;
  isRegularDonor?: unknown;
  consentSigned?: unknown;
  consentDate?: unknown;
  emergencyContact?: unknown;
  emergencyPhone?: unknown;
  notes?: unknown;
  createdBy?: unknown;
}

// backend model: DonorDeferralModel  (table: blood_bank_donor_deferrals)
export interface DonorDeferralModel {
  uuid: string;
  donorId?: unknown;
  deferralType?: unknown;
  reason?: unknown;
  reasonDetail?: unknown;
  deferralDays?: unknown;
  deferredFrom?: unknown;
  deferredUntil?: unknown;
  deferredBy?: unknown;
  notes?: unknown;
}

// backend model: BloodDonationModel  (table: blood_bank_donations)
export interface BloodDonationModel {
  uuid: string;
  donorId?: unknown;
  donationType?: unknown;
  collectionMethod?: unknown;
  status?: unknown;
  volumeMl?: unknown;
  collectionSite?: unknown;
  collectionDate?: unknown;
  phlebotomistId?: unknown;
  pulseBefore?: unknown;
  bpSystolicBefore?: unknown;
  bpDiastolicBefore?: unknown;
  temperatureBefore?: unknown;
  hemoglobinPre?: unknown;
  pulseAfter?: unknown;
  bpSystolicAfter?: unknown;
  bpDiastolicAfter?: unknown;
  adverseEvent?: unknown;
  bagIdentifier?: unknown;
  isbt128Code?: unknown;
  barcode?: unknown;
  notes?: unknown;
  createdBy?: unknown;
}

// backend model: ScreeningResultModel  (table: blood_bank_screening_results)
export interface ScreeningResultModel {
  uuid: string;
  donationId?: unknown;
  test?: unknown;
  result?: unknown;
  resultValue?: unknown;
  analyzerId?: unknown;
  operatorId?: unknown;
  testDate?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  kitLotNumber?: unknown;
  kitExpiry?: unknown;
  notes?: unknown;
}

// backend model: BloodComponentModel  (table: blood_bank_components)
export interface BloodComponentModel {
  uuid: string;
  donationId?: unknown;
  component?: unknown;
  status?: unknown;
  volumeMl?: unknown;
  parentComponentId?: unknown;
  bagIdentifier?: unknown;
  isbt128Code?: unknown;
  barcode?: unknown;
  storageCondition?: unknown;
  expiryDate?: unknown;
  processingDate?: unknown;
  processedBy?: unknown;
  leukocyteReduced?: unknown;
  irradiated?: unknown;
  washed?: unknown;
  pathogenReduced?: unknown;
  notes?: unknown;
}

// backend model: BloodInventoryModel  (table: blood_bank_inventory)
export interface BloodInventoryModel {
  uuid: string;
  facilityId?: unknown;
  bloodGroup?: unknown;
  rhFactor?: unknown;
  component?: unknown;
  quantity?: unknown;
  reservedQuantity?: unknown;
  minimumStock?: unknown;
  criticalThreshold?: unknown;
  storageLocation?: unknown;
  storageCondition?: unknown;
  lastUpdated?: unknown;
}

// backend model: BloodUnitModel  (table: blood_bank_units)
export interface BloodUnitModel {
  uuid: string;
  componentId?: unknown;
  facilityId?: unknown;
  bloodGroup?: unknown;
  rhFactor?: unknown;
  component?: unknown;
  bagIdentifier?: unknown;
  isbt128Code?: unknown;
  barcode?: unknown;
  volumeMl?: unknown;
  collectionDate?: unknown;
  expiryDate?: unknown;
  donorId?: unknown;
  donorName?: unknown;
  status?: unknown;
  storageLocation?: unknown;
  locationFacilityId?: unknown;
  screeningComplete?: unknown;
  processingComplete?: unknown;
  crossmatchCompatible?: unknown;
  issuedTo?: unknown;
  issuedAt?: unknown;
  transfusedAt?: unknown;
  discardedAt?: unknown;
  discardReason?: unknown;
  recalled?: unknown;
  recallReason?: unknown;
}

// backend model: CrossmatchModel  (table: blood_bank_crossmatches)
export interface CrossmatchModel {
  uuid: string;
  patientId?: unknown;
  patientName?: unknown;
  patientBloodGroup?: unknown;
  patientRhFactor?: unknown;
  unitId?: unknown;
  unitIdentifier?: unknown;
  bloodGroup?: unknown;
  crossmatchType?: unknown;
  status?: unknown;
  aboCompatible?: unknown;
  rhCompatible?: unknown;
  crossmatchResult?: unknown;
  performedBy?: unknown;
  performedAt?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  expiresAt?: unknown;
  notes?: unknown;
}

// backend model: TransfusionModel  (table: blood_bank_transfusions)
export interface TransfusionModel {
  uuid: string;
  patientId?: unknown;
  patientName?: unknown;
  patientBloodGroup?: unknown;
  patientRhFactor?: unknown;
  medicalRecordNumber?: unknown;
  unitId?: unknown;
  unitIdentifier?: unknown;
  bloodGroup?: unknown;
  component?: unknown;
  volumeMl?: unknown;
  crossmatchId?: unknown;
  orderedBy?: unknown;
  orderDatetime?: unknown;
  administeredBy?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  preVitals?: unknown;
  postVitals?: unknown;
  status?: unknown;
  verificationMethod?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  patientVerified?: unknown;
  unitVerified?: unknown;
  consentVerified?: unknown;
  rateMlPerHour?: unknown;
  infusionPumpId?: unknown;
  bedsideVerificationComplete?: unknown;
  reactionOccurred?: unknown;
  reactionType?: unknown;
  reactionSeverity?: unknown;
  reactionTime?: unknown;
  reactionDescription?: unknown;
  reactionIntervention?: unknown;
  outcome?: unknown;
  notes?: unknown;
}

// backend model: BloodRequestModel  (table: blood_bank_requests)
export interface BloodRequestModel {
  uuid: string;
  patientId?: unknown;
  patientName?: unknown;
  medicalRecordNumber?: unknown;
  facilityId?: unknown;
  department?: unknown;
  requestedBy?: unknown;
  physicianName?: unknown;
  bloodGroup?: unknown;
  rhFactor?: unknown;
  component?: unknown;
  unitsRequested?: unknown;
  urgency?: unknown;
  indication?: unknown;
  crossmatchRequired?: unknown;
  status?: unknown;
  approvedBy?: unknown;
  approvedAt?: unknown;
  fulfilledUnits?: unknown;
}

// backend model: InventoryMovementModel  (table: blood_bank_inventory_movements)
export interface InventoryMovementModel {
  uuid: string;
  unitId?: unknown;
  facilityId?: unknown;
  fromLocation?: unknown;
  toLocation?: unknown;
  movementType?: unknown;
  performedBy?: unknown;
  performedAt?: unknown;
  notes?: unknown;
}

// backend model: RadiologyOrder  (table: radiology_orders)
export interface RadiologyOrder {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  orderingProviderId?: unknown;
  orderNumber?: unknown;
  modality?: unknown;
  bodyPart?: unknown;
  clinicalIndication?: unknown;
  diagnosisCode?: unknown;
  diagnosisSystem?: unknown;
  priority?: unknown;
  status?: unknown;
  requestedDate?: unknown;
  scheduledDate?: unknown;
  orderingDepartmentId?: unknown;
  notes?: unknown;
  extraMetadata?: unknown;
}

// backend model: RadiologyAppointment  (table: radiology_appointments)
export interface RadiologyAppointment {
  uuid: string;
  orderId?: unknown;
  patientId?: unknown;
  scheduledDate?: unknown;
  scheduledTime?: unknown;
  durationMinutes?: unknown;
  modality?: unknown;
  room?: unknown;
  technologistId?: unknown;
  status?: unknown;
  preparationInstructions?: unknown;
  contrastRequired?: unknown;
  contrastDetails?: unknown;
  arrivalTime?: unknown;
  checkInTime?: unknown;
  notes?: unknown;
  extraMetadata?: unknown;
}

// backend model: Protocol  (table: radiology_protocols)
export interface Protocol {
  uuid: string;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  modality?: unknown;
  bodyPart?: unknown;
  protocolType?: unknown;
  contrastProtocol?: unknown;
  typicalDuration?: unknown;
  typicalDose?: unknown;
  preparationInstructions?: unknown;
  positioningInstructions?: unknown;
  seriesParameters?: unknown;
  extraMetadata?: unknown;
}

// backend model: RadiologyExam  (table: radiology_exams)
export interface RadiologyExam {
  uuid: string;
  orderId?: unknown;
  appointmentId?: unknown;
  patientId?: unknown;
  accessionNumber?: unknown;
  modality?: unknown;
  bodyPart?: unknown;
  laterality?: unknown;
  protocolId?: unknown;
  status?: unknown;
  examCode?: unknown;
  examName?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  technologistId?: unknown;
  radiologistId?: unknown;
  contrastUsed?: unknown;
  contrastType?: unknown;
  contrastAmountMl?: unknown;
  contrastBatch?: unknown;
  totalDose?: unknown;
  doseUnit?: unknown;
  imagesCount?: unknown;
  seriesCount?: unknown;
  imageQuality?: unknown;
  notes?: unknown;
  extraMetadata?: unknown;
}

// backend model: RadiologySeries  (table: radiology_series)
export interface RadiologySeries {
  uuid: string;
  examId?: unknown;
  seriesInstanceUid?: unknown;
  seriesNumber?: unknown;
  seriesDescription?: unknown;
  modality?: unknown;
  bodyPart?: unknown;
  laterality?: unknown;
  protocolName?: unknown;
  imageCount?: unknown;
  manufacturer?: unknown;
  deviceModel?: unknown;
  acquisitionDate?: unknown;
  kvp?: unknown;
  mas?: unknown;
  sliceThickness?: unknown;
  fov?: unknown;
  matrixSize?: unknown;
  extraMetadata?: unknown;
}

// backend model: RadiologyImage  (table: radiology_images)
export interface RadiologyImage {
  uuid: string;
  seriesId?: unknown;
  sopInstanceUid?: unknown;
  instanceNumber?: unknown;
  imageType?: unknown;
  laterality?: unknown;
  viewPosition?: unknown;
  acquisitionDate?: unknown;
  fileSizeBytes?: unknown;
  fileFormat?: unknown;
  storagePath?: unknown;
  storageTier?: unknown;
  checksum?: unknown;
  extraMetadata?: unknown;
}

// backend model: ImageAnnotation  (table: radiology_image_annotations)
export interface ImageAnnotation {
  uuid: string;
  imageId?: unknown;
  examId?: unknown;
  annotatedBy?: unknown;
  annotationType?: unknown;
  annotationData?: unknown;
  extraMetadata?: unknown;
}

// backend model: ImageMeasurement  (table: radiology_image_measurements)
export interface ImageMeasurement {
  uuid: string;
  imageId?: unknown;
  examId?: unknown;
  measuredBy?: unknown;
  measurementType?: unknown;
  value?: unknown;
  unit?: unknown;
  location?: unknown;
  findingCode?: unknown;
  findingDescription?: unknown;
  extraMetadata?: unknown;
}

// backend model: RadiologyReport  (table: radiology_reports)
export interface RadiologyReport {
  uuid: string;
  examId?: unknown;
  accessionNumber?: unknown;
  patientId?: unknown;
  orderingProviderId?: unknown;
  radiologistId?: unknown;
  status?: unknown;
  clinicalIndication?: unknown;
  technique?: unknown;
  comparison?: unknown;
  findings?: unknown;
  impression?: unknown;
  conclusion?: unknown;
  recommendation?: unknown;
  bodyText?: unknown;
  criticalFinding?: unknown;
  criticalFindingType?: unknown;
  criticalNotification?: unknown;
  transcribedBy?: unknown;
  draftAt?: unknown;
  preliminaryAt?: unknown;
  completedAt?: unknown;
  verifiedAt?: unknown;
  amendedAt?: unknown;
  version?: unknown;
  priorReportId?: unknown;
  dictationFile?: unknown;
  extraMetadata?: unknown;
}

// backend model: CriticalFinding  (table: radiology_critical_findings)
export interface CriticalFinding {
  uuid: string;
  examId?: unknown;
  reportId?: unknown;
  findingType?: unknown;
  findingDescription?: unknown;
  notifiedBy?: unknown;
  notifiedTo?: unknown;
  notificationTime?: unknown;
  acknowledgementTime?: unknown;
  acknowledgedBy?: unknown;
  status?: unknown;
  notes?: unknown;
  extraMetadata?: unknown;
}

// backend model: ReportTemplate  (table: radiology_report_templates)
export interface ReportTemplate {
  uuid: string;
  templateCode?: unknown;
  templateName?: unknown;
  templateNameAr?: unknown;
  modality?: unknown;
  bodyPart?: unknown;
  structuredTemplate?: unknown;
  extraMetadata?: unknown;
}

// backend model: ModalityDevice  (table: radiology_modality_devices)
export interface ModalityDevice {
  uuid: string;
  deviceId?: unknown;
  deviceName?: unknown;
  deviceModel?: unknown;
  manufacturer?: unknown;
  modalityType?: unknown;
  siteName?: unknown;
  departmentId?: unknown;
  ipAddress?: unknown;
  aeTitle?: unknown;
  port?: unknown;
  dicomProtocol?: unknown;
  lastConnection?: unknown;
  status?: unknown;
  softwareVersion?: unknown;
  serialNumber?: unknown;
  extraMetadata?: unknown;
}

// backend model: WorklistEntry  (table: radiology_worklist_entries)
export interface WorklistEntry {
  uuid: string;
  modalityDeviceId?: unknown;
  examId?: unknown;
  accessionNumber?: unknown;
  patientId?: unknown;
  patientName?: unknown;
  patientSex?: unknown;
  patientDob?: unknown;
  requestedProcedure?: unknown;
  modality?: unknown;
  scheduledStep?: unknown;
  scheduledDatetime?: unknown;
  status?: unknown;
  extraMetadata?: unknown;
}

// backend model: MPPS  (table: radiology_mpps)
export interface MPPS {
  uuid: string;
  worklistEntryId?: unknown;
  examId?: unknown;
  status?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
  performedSteps?: unknown;
  notes?: unknown;
  extraMetadata?: unknown;
}

// backend model: DICOMStorage  (table: radiology_dicom_storage)
export interface DICOMStorage {
  uuid: string;
  sopInstanceUid?: unknown;
  studyInstanceUid?: unknown;
  seriesInstanceUid?: unknown;
  patientId?: unknown;
  studyId?: unknown;
  modality?: unknown;
  bodyPart?: unknown;
  filePath?: unknown;
  fileSize?: unknown;
  checksum?: unknown;
  storageDate?: unknown;
  storageTier?: unknown;
  compressionType?: unknown;
  retentionDays?: unknown;
  isArchived?: unknown;
  extraMetadata?: unknown;
}

// backend model: DICOMStudy  (table: radiology_dicom_studies)
export interface DICOMStudy {
  uuid: string;
  studyInstanceUid?: unknown;
  patientId?: unknown;
  accessionNumber?: unknown;
  studyDate?: unknown;
  studyDescription?: unknown;
  modality?: unknown;
  referringPhysician?: unknown;
  numberOfSeries?: unknown;
  numberOfImages?: unknown;
  storageSizeBytes?: unknown;
  storageTier?: unknown;
  isArchived?: unknown;
  extraMetadata?: unknown;
}

// backend model: ImageShare  (table: radiology_image_shares)
export interface ImageShare {
  uuid: string;
  studyUid?: unknown;
  sharedBy?: unknown;
  sharedWith?: unknown;
  shareType?: unknown;
  accessCode?: unknown;
  expiresAt?: unknown;
  isRevoked?: unknown;
  accessCount?: unknown;
  extraMetadata?: unknown;
}

// backend model: ContractFormat
export interface ContractFormat {
  uuid: string;
}

// backend model: ContractStatus
export interface ContractStatus {
  uuid: string;
}

// backend model: ContractVersion
export interface ContractVersion {
  uuid: string;
  version?: string;
  description?: string;
  status?: ContractStatus;
  format?: ContractFormat;
  generatedAt?: string;
  source?: string;
}

// backend model: ContractMetadata
export interface ContractMetadata {
  uuid: string;
  name?: string;
  version?: ContractVersion;
  tags?: string[];
  labels?: Record<string, string>;
}

// backend model: OpenAPISpec
export interface OpenAPISpec {
  uuid: string;
  openapi?: string;
  info?: Record<string, unknown>;
  servers?: Record<string, unknown>[];
  paths?: Record<string, unknown>;
  components?: Record<string, unknown>;
  tags?: Record<string, unknown>[];
}

// backend model: AsyncAPISpec
export interface AsyncAPISpec {
  uuid: string;
  asyncapi?: string;
  info?: Record<string, unknown>;
  servers?: Record<string, unknown>;
  channels?: Record<string, unknown>;
  components?: Record<string, unknown>;
}

// backend model: JSONSchema
export interface JSONSchema {
  uuid: string;
  schema?: string;
  type?: string;
  title?: string | null;
  description?: string | null;
  properties?: Record<string, unknown>;
  required?: string[];
  definitions?: Record<string, unknown>;
}

// backend model: FHIRProfile
export interface FHIRProfile {
  uuid: string;
  resourceType?: string;
  url?: string;
  version?: string;
  name?: string;
  status?: string;
  description?: string;
  fhirVersion?: string;
  kind?: string;
  abstract?: boolean;
  type?: string;
  baseDefinition?: string;
  derivation?: string;
  differential?: Record<string, unknown>;
}

// backend model: GraphQLSchema
export interface GraphQLSchema {
  uuid: string;
  schema?: string;
  query?: string;
  mutation?: string | null;
  subscription?: string | null;
  types?: Record<string, unknown>;
}

// backend model: ContractExport
export interface ContractExport {
  uuid: string;
  outputDir?: string;
  formats?: ContractFormat[];
  includeMetadata?: boolean;
  pretty?: boolean;
}

// backend model: FinProvider  (table: fin_providers)
export interface FinProvider {
  uuid: string;
  labId?: unknown;
  name?: unknown;
  providerType?: unknown;
  status?: unknown;
  contactEmail?: unknown;
  phone?: unknown;
  qualityScore?: unknown;
  accredited?: unknown;
}

// backend model: FinSubscription  (table: fin_subscriptions)
export interface FinSubscription {
  uuid: string;
  providerId?: unknown;
  plan?: unknown;
  status?: unknown;
  billingCycle?: unknown;
  amount?: unknown;
  currency?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  autoRenew?: unknown;
}

// backend model: FinTransaction  (table: fin_transactions)
export interface FinTransaction {
  uuid: string;
  providerId?: unknown;
  subscriptionId?: unknown;
  transactionType?: unknown;
  amount?: unknown;
  currency?: unknown;
  status?: unknown;
  description?: unknown;
  referenceId?: unknown;
  referenceType?: unknown;
  settledAt?: unknown;
}

// backend model: FinInvoice  (table: fin_invoices)
export interface FinInvoice {
  uuid: string;
  labId?: unknown;
  invoiceNumber?: unknown;
  subscriptionId?: unknown;
  status?: unknown;
  amount?: unknown;
  paidAmount?: unknown;
  currency?: unknown;
  dueDate?: unknown;
  issuedAt?: unknown;
  paidAt?: unknown;
  notes?: unknown;
}

// backend model: FinInvoiceItem  (table: fin_invoice_items)
export interface FinInvoiceItem {
  uuid: string;
  invoiceId?: unknown;
  lineNumber?: unknown;
  description?: unknown;
  quantity?: unknown;
  unitPrice?: unknown;
  totalPrice?: unknown;
}

// backend model: FinPayment  (table: fin_payments)
export interface FinPayment {
  uuid: string;
  invoiceId?: unknown;
  labId?: unknown;
  amount?: unknown;
  currency?: unknown;
  method?: unknown;
  status?: unknown;
  reference?: unknown;
  processedAt?: unknown;
  notes?: unknown;
}

// backend model: FinReceivable  (table: fin_receivables)
export interface FinReceivable {
  uuid: string;
  labId?: unknown;
  invoiceId?: unknown;
  amount?: unknown;
  currency?: unknown;
  status?: unknown;
  dueDate?: unknown;
}

// backend model: FinPayable  (table: fin_payables)
export interface FinPayable {
  uuid: string;
  providerId?: unknown;
  amount?: unknown;
  currency?: unknown;
  status?: unknown;
  dueDate?: unknown;
}

// backend model: FinPricingRule  (table: fin_pricing_rules)
export interface FinPricingRule {
  uuid: string;
  name?: unknown;
  testType?: unknown;
  basePrice?: unknown;
  currency?: unknown;
  qualityDiscountPct?: unknown;
  volumeDiscountPct?: unknown;
  active?: unknown;
}

// backend model: Gender
export interface Gender {
  uuid: string;
}

// backend model: Priority
export interface Priority {
  uuid: string;
}

// backend model: NursingShift  (table: nursing_shifts)
export interface NursingShift {
  uuid: string;
  nurseId?: unknown;
  departmentId?: unknown;
  shiftType?: unknown;
  shiftDate?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  patientCount?: unknown;
  assignedPatients?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PatientAssignment  (table: nursing_patient_assignments)
export interface PatientAssignment {
  uuid: string;
  nurseId?: unknown;
  patientId?: unknown;
  encounterId?: unknown;
  departmentId?: unknown;
  assignmentType?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  notes?: unknown;
}

// backend model: NursingTask  (table: nursing_tasks)
export interface NursingTask {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  assignedBy?: unknown;
  assignedTo?: unknown;
  taskType?: unknown;
  description?: unknown;
  priority?: unknown;
  status?: unknown;
  scheduledTime?: unknown;
  dueTime?: unknown;
  completedAt?: unknown;
  completedBy?: unknown;
  isRecurring?: unknown;
  recurrenceRule?: unknown;
  clinicalInstruction?: unknown;
  patientResponse?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: VitalSignsRecord  (table: nursing_vital_signs)
export interface VitalSignsRecord {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  recordedBy?: unknown;
  recordedAt?: unknown;
  bpSystolic?: unknown;
  bpDiastolic?: unknown;
  heartRate?: unknown;
  respiratoryRate?: unknown;
  temperature?: unknown;
  temperatureSite?: unknown;
  oxygenSaturation?: unknown;
  oxygenDevice?: unknown;
  oxygenFlowRate?: unknown;
  heightCm?: unknown;
  weightKg?: unknown;
  bmi?: unknown;
  headCircumferenceCm?: unknown;
  painScore?: unknown;
  consciousnessLevel?: unknown;
  gcsEye?: unknown;
  gcsVerbal?: unknown;
  gcsMotor?: unknown;
  gcsTotal?: unknown;
  pupilLeftSize?: unknown;
  pupilLeftReaction?: unknown;
  pupilRightSize?: unknown;
  pupilRightReaction?: unknown;
  bloodGlucose?: unknown;
  glucoseContext?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: FluidBalance  (table: nursing_fluid_balance)
export interface FluidBalance {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  recordedBy?: unknown;
  recordedAt?: unknown;
  balanceType?: unknown;
  category?: unknown;
  fluidName?: unknown;
  amountMl?: unknown;
  route?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  infusionRate?: unknown;
  bagVolume?: unknown;
  bagNumber?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PainAssessment  (table: nursing_pain_assessments)
export interface PainAssessment {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  assessedBy?: unknown;
  assessedAt?: unknown;
  painScore?: unknown;
  painLevel?: unknown;
  painLocation?: unknown;
  painQuality?: unknown;
  painPattern?: unknown;
  onset?: unknown;
  duration?: unknown;
  aggravatingFactors?: unknown;
  relievingFactors?: unknown;
  painGoal?: unknown;
  interventionsTried?: unknown;
  effectiveness?: unknown;
  nonVerbalIndicators?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: FallRiskAssessment  (table: nursing_fall_risk_assessments)
export interface FallRiskAssessment {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  assessedBy?: unknown;
  assessedAt?: unknown;
  totalScore?: unknown;
  riskLevel?: unknown;
  ageGe65?: unknown;
  fallHistory12mo?: unknown;
  secondaryCondition?: unknown;
  assistiveDevice?: unknown;
  ivOrHeparinLock?: unknown;
  gaitImpaired?: unknown;
  mentalStatus?: unknown;
  elimination?: unknown;
  medications?: unknown;
  interventionsOrdered?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PressureInjuryAssessment  (table: nursing_pressure_injury_assessments)
export interface PressureInjuryAssessment {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  assessedBy?: unknown;
  assessedAt?: unknown;
  stage?: unknown;
  anatomicalLocation?: unknown;
  lengthCm?: unknown;
  widthCm?: unknown;
  depthCm?: unknown;
  woundBed?: unknown;
  exudateType?: unknown;
  exudateAmount?: unknown;
  woundEdges?: unknown;
  periwoundSkin?: unknown;
  infectionSigns?: unknown;
  woundCulture?: unknown;
  dressingType?: unknown;
  dressingFrequency?: unknown;
  treatmentPlan?: unknown;
  photographs?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: NutritionAssessment  (table: nursing_nutrition_assessments)
export interface NutritionAssessment {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  assessedBy?: unknown;
  assessedAt?: unknown;
  nutritionStatus?: unknown;
  weightKg?: unknown;
  heightCm?: unknown;
  bmi?: unknown;
  usualWeightKg?: unknown;
  weightChange1moKg?: unknown;
  appetite?: unknown;
  dietaryRestrictions?: unknown;
  chewingDifficulty?: unknown;
  swallowingDifficulty?: unknown;
  dysphagiaRisk?: unknown;
  fluidRestrictionMl?: unknown;
  calorieTargetKcal?: unknown;
  proteinTargetG?: unknown;
  feedingMethod?: unknown;
  supplements?: unknown;
  dietType?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: NursingCarePlan  (table: nursing_care_plans)
export interface NursingCarePlan {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  nursingDiagnosis?: unknown;
  goals?: unknown;
  interventions?: unknown;
  evaluation?: unknown;
  startDate?: unknown;
  reviewDate?: unknown;
  nextReview?: unknown;
  status?: unknown;
  createdBy?: unknown;
  approvedBy?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: NursingNote  (table: nursing_notes)
export interface NursingNote {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  shiftId?: unknown;
  documentedBy?: unknown;
  documentationTime?: unknown;
  noteType?: unknown;
  subjective?: unknown;
  objective?: unknown;
  assessment?: unknown;
  intervention?: unknown;
  response?: unknown;
  evaluation?: unknown;
  plan?: unknown;
  attachments?: unknown;
  patientEducation?: unknown;
  isConfidential?: unknown;
  metadata?: unknown;
}

// backend model: ShiftHandover  (table: nursing_shift_handovers)
export interface ShiftHandover {
  uuid: string;
  fromShiftId?: unknown;
  toShiftId?: unknown;
  fromNurseId?: unknown;
  toNurseId?: unknown;
  handoverType?: unknown;
  shiftDate?: unknown;
  patientSummaries?: unknown;
  pendingTasks?: unknown;
  criticalAlerts?: unknown;
  medicationChanges?: unknown;
  equipmentIssues?: unknown;
  staffingIssues?: unknown;
  notes?: unknown;
  isCompleted?: unknown;
  completedAt?: unknown;
  metadata?: unknown;
}

// backend model: ClinicalChecklist  (table: nursing_checklists)
export interface ClinicalChecklist {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  checklistType?: unknown;
  items?: unknown;
  status?: unknown;
  createdBy?: unknown;
  verifiedBy?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: EscalationRecord  (table: nursing_escalations)
export interface EscalationRecord {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  escalatedBy?: unknown;
  escalatedTo?: unknown;
  escalationTime?: unknown;
  reason?: unknown;
  severity?: unknown;
  category?: unknown;
  status?: unknown;
  resolvedAt?: unknown;
  resolvedBy?: unknown;
  resolution?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: AIEmbedding  (table: ai_embeddings)
export interface AIEmbedding {
  uuid: string;
  labId?: unknown;
  contentType?: unknown;
  contentId?: unknown;
  contentHash?: unknown;
  text?: unknown;
  model?: unknown;
  dimensions?: unknown;
  extraMetadata?: unknown;
}

// backend model: AIConversation  (table: ai_conversations)
export interface AIConversation {
  uuid: string;
  labId?: unknown;
  userId?: unknown;
  sessionId?: unknown;
  title?: unknown;
  extraMetadata?: unknown;
}

// backend model: AIConversationMessage  (table: ai_conversation_messages)
export interface AIConversationMessage {
  uuid: string;
  conversationId?: unknown;
  role?: unknown;
  content?: unknown;
  extraMetadata?: unknown;
  tokenCount?: unknown;
}

// backend model: AIAgentExecution  (table: ai_agent_executions)
export interface AIAgentExecution {
  uuid: string;
  labId?: unknown;
  userId?: unknown;
  sessionId?: unknown;
  agentName?: unknown;
  task?: unknown;
  status?: unknown;
  result?: unknown;
  error?: unknown;
  durationMs?: unknown;
  tokenCount?: unknown;
  costUsd?: unknown;
  approvalId?: unknown;
  extraMetadata?: unknown;
  completedAt?: unknown;
}

// backend model: AIKnowledgeNode  (table: ai_knowledge_nodes)
export interface AIKnowledgeNode {
  uuid: string;
  nodeType?: unknown;
  externalId?: unknown;
  label?: unknown;
  description?: unknown;
  aliases?: unknown;
  properties?: unknown;
}

// backend model: AIKnowledgeEdge  (table: ai_knowledge_edges)
export interface AIKnowledgeEdge {
  uuid: string;
  sourceId?: unknown;
  targetId?: unknown;
  relationship?: unknown;
  weight?: unknown;
  properties?: unknown;
}

// backend model: AIModelRegistry  (table: ai_model_registry)
export interface AIModelRegistry {
  uuid: string;
  name?: unknown;
  provider?: unknown;
  modelType?: unknown;
  version?: unknown;
  capabilities?: unknown;
  config?: unknown;
  maxTokens?: unknown;
  costPer1kInput?: unknown;
  costPer1kOutput?: unknown;
}

// backend model: AIEvaluation  (table: ai_evaluations)
export interface AIEvaluation {
  uuid: string;
  labId?: unknown;
  evalType?: unknown;
  prompt?: unknown;
  response?: unknown;
  score?: unknown;
  metrics?: unknown;
  model?: unknown;
  durationMs?: unknown;
}

// backend model: AIInteraction  (table: ai_interactions)
export interface AIInteraction {
  uuid: string;
  labId?: unknown;
  anonymousSessionId?: unknown;
  language?: unknown;
  region?: unknown;
  intent?: unknown;
  prompt?: unknown;
  promptRedacted?: unknown;
  response?: unknown;
  responseModel?: unknown;
  retrievalStrategy?: unknown;
  retrievalCount?: unknown;
  biomarkers?: unknown;
  latencyMs?: unknown;
  status?: unknown;
  errorCode?: unknown;
  confidenceScore?: unknown;
  riskLevel?: unknown;
  escalationRecommended?: unknown;
  retrievalUsed?: unknown;
  sourceQuality?: unknown;
  unsupportedClaims?: unknown;
  fallbackGeneration?: unknown;
  safetyFlags?: unknown;
}

// backend model: AIRetrievalRef  (table: ai_retrieval_refs)
export interface AIRetrievalRef {
  uuid: string;
  interactionId?: unknown;
  source?: unknown;
  docId?: unknown;
  docTitle?: unknown;
  chunkText?: unknown;
  similarity?: unknown;
  rank?: unknown;
}

// backend model: AIFeedback  (table: ai_feedback)
export interface AIFeedback {
  uuid: string;
  interactionId?: unknown;
  labId?: unknown;
  anonymousSessionId?: unknown;
  signal?: unknown;
  notes?: unknown;
}

// backend model: AIUnresolvedQuestion  (table: ai_unresolved_questions)
export interface AIUnresolvedQuestion {
  uuid: string;
  interactionId?: unknown;
  labId?: unknown;
  anonymousSessionId?: unknown;
  question?: unknown;
  language?: unknown;
  category?: unknown;
  status?: unknown;
  resolvedAt?: unknown;
}

// backend model: MedicalTerminologyNormalized  (table: medical_terminology_normalized)
export interface MedicalTerminologyNormalized {
  uuid: string;
  termEn?: unknown;
  termAr?: unknown;
  termArIq?: unknown;
  code?: unknown;
  codeSystem?: unknown;
  category?: unknown;
  synonyms?: unknown;
  notes?: unknown;
}

// backend model: AuditLog  (table: audit_logs)
export interface AuditLog {
  uuid: string;
  userId?: unknown;
  userRole?: unknown;
  action?: unknown;
  resourceType?: unknown;
  resourceId?: unknown;
  details?: unknown;
  ipAddress?: unknown;
  chainHash?: unknown;
}

// backend model: UserTypeEnum  (table: permissions)
export interface UserTypeEnum {
  uuid: string;
}

// backend model: Permission  (table: permissions)
export interface Permission {
  uuid: string;
  permissionId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  description?: unknown;
  domain?: unknown;
  resource?: unknown;
  action?: unknown;
  riskLevel?: unknown;
  isSensitive?: unknown;
  requiresMfa?: unknown;
  requiresJustification?: unknown;
  isAudited?: unknown;
}

// backend model: Role  (table: roles)
export interface Role {
  uuid: string;
  roleId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  description?: unknown;
  level?: unknown;
  parentRoleId?: unknown;
  roleGroupId?: unknown;
  isTemporary?: unknown;
  isDelegatable?: unknown;
  requiresMfa?: unknown;
  maxDurationHours?: unknown;
  version?: unknown;
}

// backend model: RolePermission  (table: role_permissions)
export interface RolePermission {
  uuid: string;
  roleId?: unknown;
  permissionId?: unknown;
}

// backend model: RoleAssignment  (table: role_assignments)
export interface RoleAssignment {
  uuid: string;
  userId?: unknown;
  roleId?: unknown;
  organizationId?: unknown;
  facilityId?: unknown;
  departmentId?: unknown;
  assignedBy?: unknown;
  assignedAt?: unknown;
  expiresAt?: unknown;
  isPrimary?: unknown;
  isDelegated?: unknown;
  delegationId?: unknown;
  status?: unknown;
}

// backend model: RoleGroup  (table: role_groups)
export interface RoleGroup {
  uuid: string;
  groupId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  description?: unknown;
  isTemplate?: unknown;
}

// backend model: RoleGroupMember  (table: role_group_members)
export interface RoleGroupMember {
  uuid: string;
  groupId?: unknown;
  roleId?: unknown;
}

// backend model: Policy  (table: abac_policies)
export interface Policy {
  uuid: string;
  policyId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  description?: unknown;
  version?: unknown;
  status?: unknown;
  effect?: unknown;
  priority?: unknown;
  category?: unknown;
  target?: unknown;
  conditions?: unknown;
  obligations?: unknown;
  validityStart?: unknown;
  validityEnd?: unknown;
  signature?: unknown;
  createdBy?: unknown;
  approvedBy?: unknown;
  publishedAt?: unknown;
  tags?: unknown;
}

// backend model: FieldSecurity  (table: field_security)
export interface FieldSecurity {
  uuid: string;
  resourceType?: unknown;
  fieldName?: unknown;
  defaultLevel?: unknown;
  consentRequired?: unknown;
  encryptionRequired?: unknown;
  maskingPattern?: unknown;
  auditAccess?: unknown;
  purposeRestricted?: unknown;
  levelsByRole?: unknown;
  levelsByOrgType?: unknown;
}

// backend model: BreakGlassSession  (table: break_glass_sessions)
export interface BreakGlassSession {
  uuid: string;
  userId?: unknown;
  emergencyCategory?: unknown;
  justification?: unknown;
  patientId?: unknown;
  startedAt?: unknown;
  expiresAt?: unknown;
  deactivatedAt?: unknown;
  status?: unknown;
  reviewedBy?: unknown;
  reviewStatus?: unknown;
  reviewNotes?: unknown;
}

// backend model: AuthorizationAudit  (table: authorization_audit)
export interface AuthorizationAudit {
  uuid: string;
  decisionId?: unknown;
  userId?: unknown;
  userRole?: unknown;
  action?: unknown;
  resourceType?: unknown;
  resourceId?: unknown;
  decision?: unknown;
  policiesApplied?: unknown;
  policyEngine?: unknown;
  context?: unknown;
  riskScore?: unknown;
  justification?: unknown;
  isEmergency?: unknown;
  delegationId?: unknown;
}

// backend model: PatientLink  (table: patient_links)
export interface PatientLink {
  uuid: string;
  patientId?: unknown;
  canonicalId?: unknown;
  linkageMethod?: unknown;
  confidence?: unknown;
}

// backend model: CitizenLink  (table: citizen_links)
export interface CitizenLink {
  uuid: string;
  citizenId?: unknown;
  canonicalId?: unknown;
  linkageMethod?: unknown;
  confidence?: unknown;
}

// backend model: Claim  (table: claims)
export interface Claim {
  uuid: string;
  labId?: unknown;
  patientId?: unknown;
  orderId?: unknown;
  status?: unknown;
  totalAmount?: unknown;
  currency?: unknown;
  idempotencyKey?: unknown;
  externalRef?: unknown;
  submittedAt?: unknown;
}

// backend model: ClaimItem  (table: claim_items)
export interface ClaimItem {
  uuid: string;
  claimId?: unknown;
  testCode?: unknown;
  description?: unknown;
  quantity?: unknown;
  unitPrice?: unknown;
  amount?: unknown;
}

// backend model: Consent  (table: consents)
export interface Consent {
  uuid: string;
  gpid?: unknown;
  granteeId?: unknown;
  scope?: unknown;
  status?: unknown;
  expiresAt?: unknown;
  revokedAt?: unknown;
  createdByUserId?: unknown;
}

// backend model: EdgeDevice  (table: edge_devices)
export interface EdgeDevice {
  uuid: string;
  deviceId?: unknown;
  labId?: unknown;
  ownerUserId?: unknown;
  displayName?: unknown;
  roleMode?: unknown;
  status?: unknown;
  trustScore?: unknown;
  publicKeyPem?: unknown;
  certFingerprint?: unknown;
  attestationBlob?: unknown;
  agentVersion?: unknown;
  osPlatform?: unknown;
  capabilities?: unknown;
  lastSeenAt?: unknown;
  registeredAt?: unknown;
  revokedAt?: unknown;
  quarantinedAt?: unknown;
  killSwitched?: unknown;
  notes?: unknown;
}

// backend model: EdgeTask  (table: edge_tasks)
export interface EdgeTask {
  uuid: string;
  taskUid?: unknown;
  idempotencyKey?: unknown;
  labId?: unknown;
  deviceId?: unknown;
  kind?: unknown;
  priority?: unknown;
  status?: unknown;
  privacyLevel?: unknown;
  payload?: unknown;
  payloadSig?: unknown;
  requiredCaps?: unknown;
  minTrust?: unknown;
  attempts?: unknown;
  maxAttempts?: unknown;
  timeoutS?: unknown;
  dispatchedAt?: unknown;
  completedAt?: unknown;
  expiresAt?: unknown;
  result?: unknown;
  error?: unknown;
  submittedByUserId?: unknown;
}

// backend model: EdgeTelemetry  (table: edge_telemetry)
export interface EdgeTelemetry {
  uuid: string;
  deviceId?: unknown;
  labId?: unknown;
  ts?: unknown;
  cpuPct?: unknown;
  memMb?: unknown;
  memTotalMb?: unknown;
  gpuPct?: unknown;
  batteryPct?: unknown;
  onBattery?: unknown;
  idleS?: unknown;
  netUpKbps?: unknown;
  netDownKbps?: unknown;
  loadedModels?: unknown;
  queueDepth?: unknown;
  agentUptimeS?: unknown;
  taskCompletedTotal?: unknown;
  taskFailedTotal?: unknown;
}

// backend model: EdgeModel  (table: edge_models)
export interface EdgeModel {
  uuid: string;
  modelUid?: unknown;
  name?: unknown;
  version?: unknown;
  runtime?: unknown;
  format?: unknown;
  quantization?: unknown;
  sizeMb?: unknown;
  minRamMb?: unknown;
  minVramMb?: unknown;
  sha256?: unknown;
  sourceUrl?: unknown;
  status?: unknown;
  rolloutPct?: unknown;
  retiredAt?: unknown;
  metadataJson?: unknown;
}

// backend model: EdgeModelAssignment  (table: edge_model_assignments)
export interface EdgeModelAssignment {
  uuid: string;
  modelUid?: unknown;
  labId?: unknown;
  deviceId?: unknown;
  active?: unknown;
  assignedAt?: unknown;
  retiredAt?: unknown;
}

// backend model: EdgePolicy  (table: edge_policies)
export interface EdgePolicy {
  uuid: string;
  labId?: unknown;
  maxConcurrentPerDevice?: unknown;
  maxDevicesPerLab?: unknown;
  idleOnly?: unknown;
  batteryFloorPct?: unknown;
  cpuCapPct?: unknown;
  ramCapMb?: unknown;
  allowKinds?: unknown;
  denyKinds?: unknown;
  minTrustScore?: unknown;
  offlineQueueMax?: unknown;
  killSwitch?: unknown;
  updatedByUserId?: unknown;
}

// backend model: EdgeEvent  (table: edge_events)
export interface EdgeEvent {
  uuid: string;
  ts?: unknown;
  labId?: unknown;
  deviceId?: unknown;
  eventType?: unknown;
  severity?: unknown;
  actorUserId?: unknown;
  details?: unknown;
}

// backend model: Lab  (table: labs)
export interface Lab {
  uuid: string;
  name?: unknown;
  licenseNumber?: unknown;
  labType?: unknown;
  directorName?: unknown;
  website?: unknown;
  city?: unknown;
  address?: unknown;
  phone?: unknown;
}

// backend model: LabOrder  (table: lab_orders)
export interface LabOrder {
  uuid: string;
  patientId?: unknown;
  labId?: unknown;
  doctorName?: unknown;
  doctorUserId?: unknown;
  status?: unknown;
  validatedBy?: unknown;
  validatedAt?: unknown;
  lockedAt?: unknown;
  version?: unknown;
}

// backend model: LabResult  (table: lab_results)
export interface LabResult {
  uuid: string;
  orderId?: unknown;
  testTypeId?: unknown;
  testName?: unknown;
  value?: unknown;
  valueText?: unknown;
  unit?: unknown;
  normalRangeLow?: unknown;
  normalRangeHigh?: unknown;
  flag?: unknown;
  token?: unknown;
  tokenHash?: unknown;
  expiresAt?: unknown;
  clinicalEngineVersion?: unknown;
  version?: unknown;
}

// backend model: LabUser  (table: lab_users)
export interface LabUser {
  uuid: string;
  labId?: unknown;
  name?: unknown;
  email?: unknown;
  passwordHash?: unknown;
  role?: unknown;
  permVersion?: unknown;
  nationalIdHash?: unknown;
  provinceId?: unknown;
  createdBy?: unknown;
  resetToken?: unknown;
  resetTokenExpires?: unknown;
}

// backend model: MFADevice  (table: mfa_devices)
export interface MFADevice {
  uuid: string;
  userId?: unknown;
  deviceType?: unknown;
  deviceName?: unknown;
  secret?: unknown;
  credentialId?: unknown;
  publicKey?: unknown;
  signCount?: unknown;
  transports?: unknown;
  backupCodes?: unknown;
  isPrimary?: unknown;
  lastUsedAt?: unknown;
}

// backend model: MFASession  (table: mfa_sessions)
export interface MFASession {
  uuid: string;
  userId?: unknown;
  sessionToken?: unknown;
  mfaMethod?: unknown;
  isVerified?: unknown;
  expiresAt?: unknown;
}

// backend model: OAuth2Client  (table: oauth2_clients)
export interface OAuth2Client {
  uuid: string;
  clientId?: unknown;
  clientSecretHash?: unknown;
  redirectUris?: unknown;
  allowedScopes?: unknown;
  grantTypes?: unknown;
  responseTypes?: unknown;
  isConfidential?: unknown;
  tokenEndpointAuthMethod?: unknown;
}

// backend model: OAuth2Token  (table: oauth2_tokens)
export interface OAuth2Token {
  uuid: string;
  clientId?: unknown;
  userId?: unknown;
  tokenType?: unknown;
  tokenHash?: unknown;
  scope?: unknown;
  expiresAt?: unknown;
  codeChallenge?: unknown;
  codeChallengeMethod?: unknown;
  isRevoked?: unknown;
}

// backend model: Organization  (table: organizations)
export interface Organization {
  uuid: string;
  orgId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  orgType?: unknown;
  parentOrgId?: unknown;
  governorateId?: unknown;
  directorateId?: unknown;
  contactEmail?: unknown;
  contactPhone?: unknown;
  address?: unknown;
  extraMetadata?: unknown;
}

// backend model: Facility  (table: facilities)
export interface Facility {
  uuid: string;
  facilityId?: unknown;
  nameEn?: unknown;
  nameAr?: unknown;
  facilityType?: unknown;
  organizationId?: unknown;
  contactEmail?: unknown;
  contactPhone?: unknown;
  address?: unknown;
}

// backend model: OutboxEvent  (table: outbox_events)
export interface OutboxEvent {
  uuid: string;
  eventType?: unknown;
  aggregateType?: unknown;
  aggregateId?: unknown;
  payload?: unknown;
  status?: unknown;
  attempts?: unknown;
  lastError?: unknown;
  processedAt?: unknown;
}

// backend model: Patient  (table: patients)
export interface Patient {
  uuid: string;
  labId?: unknown;
  healthId?: unknown;
  nationalIdHash?: unknown;
  familyIdHash?: unknown;
  guardianId?: unknown;
  fullName?: unknown;
  phone?: unknown;
  birthDate?: unknown;
  gender?: unknown;
  email?: unknown;
}

// backend model: QualityControl  (table: quality_controls)
export interface QualityControl {
  uuid: string;
  labId?: unknown;
  testCode?: unknown;
  instrumentName?: unknown;
  lotNumber?: unknown;
  level?: unknown;
  expectedValue?: unknown;
  measuredValue?: unknown;
  sd?: unknown;
  unit?: unknown;
  status?: unknown;
  violation?: unknown;
  notes?: unknown;
  performedBy?: unknown;
}

// backend model: Sample  (table: samples)
export interface Sample {
  uuid: string;
  orderId?: unknown;
  barcode?: unknown;
  sampleType?: unknown;
  collectionTime?: unknown;
  collectedBy?: unknown;
  status?: unknown;
  rejectionReason?: unknown;
  notes?: unknown;
  storageLocation?: unknown;
}

// backend model: ServiceAccount  (table: service_accounts)
export interface ServiceAccount {
  uuid: string;
  name?: unknown;
  description?: unknown;
  apiKeyHash?: unknown;
  roles?: unknown;
  scopes?: unknown;
  lastUsedAt?: unknown;
  createdBy?: unknown;
  expiresAt?: unknown;
}

// backend model: LabSubscription  (table: lab_subscriptions)
export interface LabSubscription {
  uuid: string;
  labId?: unknown;
  tier?: unknown;
  deploymentMode?: unknown;
  securityLevel?: unknown;
  trialEndsAt?: unknown;
  billingCycle?: unknown;
  monthlyPriceUsd?: unknown;
  maxPatients?: unknown;
  maxStaff?: unknown;
  maxBranches?: unknown;
  maxOrdersPerDay?: unknown;
  maxAiCallsPerDay?: unknown;
  notes?: unknown;
  activatedAt?: unknown;
  expiresAt?: unknown;
}

// backend model: UpgradeRequest  (table: upgrade_requests)
export interface UpgradeRequest {
  uuid: string;
  labId?: unknown;
  requesterId?: unknown;
  targetTier?: unknown;
  targetDeploymentMode?: unknown;
  targetSecurityLevel?: unknown;
  reason?: unknown;
  status?: unknown;
  weight?: unknown;
  reviewedBy?: unknown;
  reviewedAt?: unknown;
  reviewNote?: unknown;
}

// backend model: UpgradeDemandScore  (table: upgrade_demand_scores)
export interface UpgradeDemandScore {
  uuid: string;
  labId?: unknown;
  rawScore?: unknown;
  uniqueRequesters?: unknown;
  weightedScore?: unknown;
  lastRequestAt?: unknown;
}

// backend model: FeatureFlag  (table: feature_flags)
export interface FeatureFlag {
  uuid: string;
  labId?: unknown;
  featureKey?: unknown;
  isEnabled?: unknown;
  reason?: unknown;
  setBy?: unknown;
  expiresAt?: unknown;
}

// backend model: Tenant  (table: tenants)
export interface Tenant {
  uuid: string;
  nameEn?: unknown;
  nameAr?: unknown;
  domain?: unknown;
  tenantType?: unknown;
  parentTenantId?: unknown;
  phone?: unknown;
  address?: unknown;
  maxUsers?: unknown;
  featureFlags?: unknown;
  settings?: unknown;
}

// backend model: TestResult  (table: test_results)
export interface TestResult {
  uuid: string;
  citizenId?: unknown;
  labId?: unknown;
  deviceId?: unknown;
  testCode?: unknown;
  testNameEn?: unknown;
  testNameAr?: unknown;
  category?: unknown;
  resultValue?: unknown;
  resultText?: unknown;
  unit?: unknown;
  referenceMin?: unknown;
  referenceMax?: unknown;
  status?: unknown;
  isCritical?: unknown;
  isAbnormal?: unknown;
  abnormalityDirection?: unknown;
  sampleCollectedAt?: unknown;
  resultCompletedAt?: unknown;
  verifiedAt?: unknown;
  verifiedBy?: unknown;
  sampleBarcode?: unknown;
  orderingPhysician?: unknown;
  clinicalNotes?: unknown;
}

// backend model: TestResultCreate
export interface TestResultCreate {
  uuid: string;
  citizenId?: number;
  labId?: number;
  deviceId?: number | null;
  testCode?: string;
  testNameEn?: string;
  testNameAr?: string;
  category?: string | null;
  resultValue?: number | null;
  resultText?: string | null;
  unit?: string | null;
  referenceMin?: number | null;
  referenceMax?: number | null;
  status?: string;
  isCritical?: boolean;
  isAbnormal?: boolean;
  abnormalityDirection?: string | null;
  sampleCollectedAt?: string;
  sampleBarcode?: string;
  orderingPhysician?: string | null;
  clinicalNotes?: string | null;
}

// backend model: TestResultRead
export interface TestResultRead {
  uuid: string;
  citizenId?: number;
  labId?: number;
  deviceId?: number | null;
  testCode?: string;
  testNameEn?: string;
  testNameAr?: string;
  category?: string | null;
  resultValue?: number | null;
  resultText?: string | null;
  unit?: string | null;
  referenceMin?: number | null;
  referenceMax?: number | null;
  status?: string;
  isCritical?: boolean;
  isAbnormal?: boolean;
  abnormalityDirection?: string | null;
  sampleCollectedAt?: string;
  resultCompletedAt?: string | null;
  verifiedAt?: string | null;
  verifiedBy?: string | null;
  sampleBarcode?: string;
  orderingPhysician?: string | null;
  clinicalNotes?: string | null;
}

// backend model: TestResultBrief
export interface TestResultBrief {
  uuid: string;
  testCode?: string;
  testNameEn?: string;
  testNameAr?: string;
  resultValue?: number | null;
  resultText?: string | null;
  unit?: string | null;
  status?: string;
  isAbnormal?: boolean;
  isCritical?: boolean;
  sampleCollectedAt?: string;
}

// backend model: TestResultForCitizen
export interface TestResultForCitizen {
  uuid: string;
  testNameAr?: string;
  resultValue?: number | null;
  resultText?: string | null;
  unit?: string | null;
  referenceMin?: number | null;
  referenceMax?: number | null;
  status?: string;
  isAbnormal?: boolean;
  isCritical?: boolean;
  abnormalityDirection?: string | null;
  sampleCollectedAt?: string;
  resultCompletedAt?: string | null;
}

// backend model: TestType  (table: test_types)
export interface TestType {
  uuid: string;
  testCode?: unknown;
  testName?: unknown;
  testNameAr?: unknown;
  category?: unknown;
  unit?: unknown;
  normalRangeLow?: unknown;
  normalRangeHigh?: unknown;
  interpretationLow?: unknown;
  interpretationNormal?: unknown;
  interpretationHigh?: unknown;
  interpretationLowAr?: unknown;
  interpretationNormalAr?: unknown;
  interpretationHighAr?: unknown;
}

// backend model: User  (table: users)
export interface User {
  uuid: string;
  email?: unknown;
  phone?: unknown;
  passwordHash?: unknown;
  fullName?: unknown;
  role?: unknown;
  labId?: unknown;
  userType?: unknown;
  organizationId?: unknown;
  facilityId?: unknown;
  governorateId?: unknown;
  directorateId?: unknown;
  departmentId?: unknown;
  specialty?: unknown;
  licenseNumber?: unknown;
  nationalIdHash?: unknown;
  isVerified?: unknown;
  mfaEnabled?: unknown;
  permVersion?: unknown;
  preferences?: unknown;
  lastLogin?: unknown;
}

// backend model: ProgramStatus  (table: roadmap_programs)
export interface ProgramStatus {
  uuid: string;
}

// backend model: MissionStatus  (table: roadmap_programs)
export interface MissionStatus {
  uuid: string;
}

// backend model: EpicStatus  (table: roadmap_programs)
export interface EpicStatus {
  uuid: string;
}

// backend model: TaskStatus  (table: roadmap_programs)
export interface TaskStatus {
  uuid: string;
}

// backend model: RiskLevel  (table: roadmap_programs)
export interface RiskLevel {
  uuid: string;
}

// backend model: Program  (table: roadmap_programs)
export interface Program {
  uuid: string;
}

// backend model: Mission  (table: roadmap_programs)
export interface Mission {
  uuid: string;
}

// backend model: Epic  (table: roadmap_programs)
export interface Epic {
  uuid: string;
}

// backend model: RoadmapTask  (table: roadmap_tasks)
export interface RoadmapTask {
  uuid: string;
  epicId?: unknown;
  name?: unknown;
  description?: unknown;
  status?: unknown;
  priority?: unknown;
  assignee?: unknown;
  estimatedHours?: unknown;
  actualHours?: unknown;
  dependencies?: unknown;
  metadataJson?: unknown;
  startedAt?: unknown;
  completedAt?: unknown;
}

// backend model: Milestone  (table: roadmap_milestones)
export interface Milestone {
  uuid: string;
  missionId?: unknown;
  name?: unknown;
  description?: unknown;
  targetDate?: unknown;
  achievedDate?: unknown;
  status?: unknown;
  metadataJson?: unknown;
}

// backend model: Risk  (table: roadmap_programs)
export interface Risk {
  uuid: string;
}

// backend model: TechnicalDebt  (table: roadmap_technical_debt)
export interface TechnicalDebt {
  uuid: string;
  component?: unknown;
  description?: unknown;
  severity?: unknown;
  estimatedEffortHours?: unknown;
  status?: unknown;
  identifiedBy?: unknown;
  resolvedAt?: unknown;
  metadataJson?: unknown;
}

// backend model: ArchitectureDecision  (table: roadmap_architecture_decisions)
export interface ArchitectureDecision {
  uuid: string;
  title?: unknown;
  context?: unknown;
  decision?: unknown;
  consequences?: unknown;
  status?: unknown;
  domain?: unknown;
  createdBy?: unknown;
  approvedBy?: unknown;
  supersededBy?: unknown;
}

// backend model: NodeType  (table: knowledge_nodes)
export interface NodeType {
  uuid: string;
}

// backend model: EdgeType  (table: knowledge_nodes)
export interface EdgeType {
  uuid: string;
}

// backend model: KnowledgeNode  (table: knowledge_nodes)
export interface KnowledgeNode {
  uuid: string;
  nodeType?: unknown;
  name?: unknown;
  qualifiedName?: unknown;
  description?: unknown;
  extraMetadata?: unknown;
  sourcePath?: unknown;
  tags?: unknown;
  version?: unknown;
}

// backend model: KnowledgeEdge  (table: knowledge_edges)
export interface KnowledgeEdge {
  uuid: string;
  sourceNodeId?: unknown;
  targetNodeId?: unknown;
  edgeType?: unknown;
  extraMetadata?: unknown;
  weight?: unknown;
}

// backend model: KnowledgeGraphSnapshot  (table: knowledge_graph_snapshots)
export interface KnowledgeGraphSnapshot {
  uuid: string;
  version?: unknown;
  nodeCount?: unknown;
  edgeCount?: unknown;
  graphHash?: unknown;
  extraMetadata?: unknown;
}

// backend model: DrugCatalog  (table: pharmacy_drug_catalog)
export interface DrugCatalog {
  uuid: string;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  genericName?: unknown;
  brandName?: unknown;
  manufacturer?: unknown;
  manufacturerCode?: unknown;
  form?: unknown;
  strengthValue?: unknown;
  strengthUnit?: unknown;
  route?: unknown;
  category?: unknown;
  therapeuticClass?: unknown;
  atcCode?: unknown;
  atcDescription?: unknown;
  isControlled?: unknown;
  isNarcotic?: unknown;
  requiresPrescription?: unknown;
  maxDailyDose?: unknown;
  minAge?: unknown;
  pregnancyCategory?: unknown;
  lactationCategory?: unknown;
  ingredients?: unknown;
  sideEffects?: unknown;
  drugImages?: unknown;
  barcodeGs1?: unknown;
  barcodeType?: unknown;
  metadata?: unknown;
}

// backend model: DrugBatch  (table: pharmacy_drug_batches)
export interface DrugBatch {
  uuid: string;
  drugCatalogId?: unknown;
  batchNumber?: unknown;
  manufacturerBatch?: unknown;
  expiryDate?: unknown;
  manufacturingDate?: unknown;
  quantityInitial?: unknown;
  quantityRemaining?: unknown;
  storageCondition?: unknown;
  location?: unknown;
  receivedDate?: unknown;
  receivedBy?: unknown;
  supplier?: unknown;
  costPrice?: unknown;
  sellingPrice?: unknown;
  isQuarantined?: unknown;
  metadata?: unknown;
}

// backend model: DrugSupplier  (table: pharmacy_drug_suppliers)
export interface DrugSupplier {
  uuid: string;
  name?: unknown;
  nameAr?: unknown;
  code?: unknown;
  contactPerson?: unknown;
  phone?: unknown;
  email?: unknown;
  address?: unknown;
  licenseNumber?: unknown;
  paymentTerms?: unknown;
  metadata?: unknown;
}

// backend model: Prescription  (table: pharmacy_prescriptions)
export interface Prescription {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  prescriberId?: unknown;
  prescriptionNumber?: unknown;
  status?: unknown;
  intent?: unknown;
  priority?: unknown;
  diagnosis?: unknown;
  diagnosisCode?: unknown;
  diagnosisSystem?: unknown;
  authoredOn?: unknown;
  validFrom?: unknown;
  validTo?: unknown;
  dispenseInterval?: unknown;
  substitutionAllowed?: unknown;
  note?: unknown;
  metadata?: unknown;
  signedBy?: unknown;
  signedAt?: unknown;
}

// backend model: PrescriptionItem  (table: pharmacy_prescription_items)
export interface PrescriptionItem {
  uuid: string;
  prescriptionId?: unknown;
  drugCatalogId?: unknown;
  drugBatchId?: unknown;
  medicationCode?: unknown;
  medicationName?: unknown;
  strengthValue?: unknown;
  strengthUnit?: unknown;
  form?: unknown;
  route?: unknown;
  doseQuantity?: unknown;
  doseUnit?: unknown;
  frequency?: unknown;
  duration?: unknown;
  durationUnit?: unknown;
  quantity?: unknown;
  quantityUnit?: unknown;
  refills?: unknown;
  refillsUsed?: unknown;
  instructions?: unknown;
  substitutionAllowed?: unknown;
  status?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: DispenseRecord  (table: pharmacy_dispense_records)
export interface DispenseRecord {
  uuid: string;
  prescriptionId?: unknown;
  prescriptionItemId?: unknown;
  patientId?: unknown;
  dispensedBy?: unknown;
  verifiedBy?: unknown;
  dispensedAt?: unknown;
  status?: unknown;
  quantityDispensed?: unknown;
  quantityUnit?: unknown;
  daysSupply?: unknown;
  batchId?: unknown;
  lotNumber?: unknown;
  expiryDate?: unknown;
  costPrice?: unknown;
  sellingPrice?: unknown;
  discount?: unknown;
  totalAmount?: unknown;
  patientSignature?: unknown;
  pharmacistNotes?: unknown;
  counselingProvided?: unknown;
  metadata?: unknown;
}

// backend model: DispenseQueue  (table: pharmacy_dispense_queue)
export interface DispenseQueue {
  uuid: string;
  prescriptionId?: unknown;
  priority?: unknown;
  queuedAt?: unknown;
  status?: unknown;
  assignedTo?: unknown;
  pickupTime?: unknown;
  readyTime?: unknown;
  completionTime?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: Warehouse  (table: pharmacy_warehouses)
export interface Warehouse {
  uuid: string;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  location?: unknown;
  address?: unknown;
  contactPerson?: unknown;
  phone?: unknown;
  metadata?: unknown;
}

// backend model: Store  (table: pharmacy_stores)
export interface Store {
  uuid: string;
  warehouseId?: unknown;
  code?: unknown;
  name?: unknown;
  nameAr?: unknown;
  location?: unknown;
  storeType?: unknown;
  metadata?: unknown;
}

// backend model: StockLevel  (table: pharmacy_stock_levels)
export interface StockLevel {
  uuid: string;
  drugCatalogId?: unknown;
  batchId?: unknown;
  warehouseId?: unknown;
  storeId?: unknown;
  quantity?: unknown;
  reservedQuantity?: unknown;
  availableQuantity?: unknown;
  reorderPoint?: unknown;
  reorderQuantity?: unknown;
  maxLevel?: unknown;
  storageCondition?: unknown;
  lastCountDate?: unknown;
  metadata?: unknown;
}

// backend model: StockMovement  (table: pharmacy_stock_movements)
export interface StockMovement {
  uuid: string;
  drugCatalogId?: unknown;
  batchId?: unknown;
  warehouseId?: unknown;
  storeId?: unknown;
  movementType?: unknown;
  quantity?: unknown;
  referenceType?: unknown;
  referenceId?: unknown;
  reason?: unknown;
  performedBy?: unknown;
  movementDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: InventoryTransfer  (table: pharmacy_inventory_transfers)
export interface InventoryTransfer {
  uuid: string;
  fromWarehouseId?: unknown;
  toWarehouseId?: unknown;
  fromStoreId?: unknown;
  toStoreId?: unknown;
  status?: unknown;
  initiatedBy?: unknown;
  approvedBy?: unknown;
  dispatchDate?: unknown;
  receivedDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: InventoryTransferItem  (table: pharmacy_inventory_transfer_items)
export interface InventoryTransferItem {
  uuid: string;
  transferId?: unknown;
  drugCatalogId?: unknown;
  batchId?: unknown;
  quantityRequested?: unknown;
  quantityShipped?: unknown;
  quantityReceived?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: DrugReturn  (table: pharmacy_drug_returns)
export interface DrugReturn {
  uuid: string;
  patientId?: unknown;
  prescriptionId?: unknown;
  drugCatalogId?: unknown;
  batchId?: unknown;
  returnReason?: unknown;
  quantity?: unknown;
  returnedBy?: unknown;
  returnedAt?: unknown;
  disposition?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: WasteRecord  (table: pharmacy_waste_records)
export interface WasteRecord {
  uuid: string;
  drugCatalogId?: unknown;
  batchId?: unknown;
  quantity?: unknown;
  wasteReason?: unknown;
  witnessBy?: unknown;
  disposalMethod?: unknown;
  disposalDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: Recall  (table: pharmacy_recalls)
export interface Recall {
  uuid: string;
  drugCatalogId?: unknown;
  batchId?: unknown;
  recallReason?: unknown;
  recallDate?: unknown;
  initiatedBy?: unknown;
  severity?: unknown;
  status?: unknown;
  affectedPatients?: unknown;
  actionsTaken?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: InventoryForecast  (table: pharmacy_inventory_forecasts)
export interface InventoryForecast {
  uuid: string;
  drugCatalogId?: unknown;
  periodStart?: unknown;
  periodEnd?: unknown;
  predictedConsumption?: unknown;
  actualConsumption?: unknown;
  reorderRecommendation?: unknown;
  recommendationQuantity?: unknown;
  confidenceScore?: unknown;
  metadata?: unknown;
}

// backend model: DrugInteractionRule  (table: pharmacy_drug_interaction_rules)
export interface DrugInteractionRule {
  uuid: string;
  drugACode?: unknown;
  drugBCode?: unknown;
  severity?: unknown;
  mechanism?: unknown;
  description?: unknown;
  recommendation?: unknown;
  evidenceLevel?: unknown;
  reference?: unknown;
  metadata?: unknown;
}

// backend model: ContraindicationRule  (table: pharmacy_contraindication_rules)
export interface ContraindicationRule {
  uuid: string;
  drugCode?: unknown;
  conditionCode?: unknown;
  conditionSystem?: unknown;
  severity?: unknown;
  description?: unknown;
  recommendation?: unknown;
  metadata?: unknown;
}

// backend model: AllergyRule  (table: pharmacy_allergy_rules)
export interface AllergyRule {
  uuid: string;
  allergenCode?: unknown;
  allergenSystem?: unknown;
  drugCode?: unknown;
  severity?: unknown;
  reaction?: unknown;
  recommendation?: unknown;
  metadata?: unknown;
}

// backend model: DoseGuideline  (table: pharmacy_dose_guidelines)
export interface DoseGuideline {
  uuid: string;
  drugCode?: unknown;
  indicationCode?: unknown;
  ageMinMonths?: unknown;
  ageMaxMonths?: unknown;
  weightMinKg?: unknown;
  weightMaxKg?: unknown;
  doseMin?: unknown;
  doseMax?: unknown;
  doseUnit?: unknown;
  frequency?: unknown;
  maxDailyDose?: unknown;
  route?: unknown;
  renalAdjustment?: unknown;
  hepaticAdjustment?: unknown;
  pediatricNote?: unknown;
  pregnancyNote?: unknown;
  breastfeedingNote?: unknown;
  metadata?: unknown;
}

// backend model: DrugMonitoring  (table: pharmacy_drug_monitoring)
export interface DrugMonitoring {
  uuid: string;
  drugCode?: unknown;
  requiredTests?: unknown;
  monitoringFrequency?: unknown;
  therapeuticRange?: unknown;
  toxicLevel?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ClinicalGuideline  (table: pharmacy_clinical_guidelines)
export interface ClinicalGuideline {
  uuid: string;
  guidelineCode?: unknown;
  title?: unknown;
  titleAr?: unknown;
  drugCodes?: unknown;
  conditionCodes?: unknown;
  summary?: unknown;
  recommendations?: unknown;
  evidenceLevel?: unknown;
  source?: unknown;
  version?: unknown;
  metadata?: unknown;
}

// backend model: SourceReference  (table: hd_mdm_source_references)
export interface SourceReference {
  uuid: string;
  goldenRecordId?: unknown;
  sourceSystem?: unknown;
  sourceId?: unknown;
  sourceUrl?: unknown;
  confidence?: unknown;
  isPrimary?: unknown;
  rawData?: unknown;
}

// backend model: MasterPatientIndex  (table: hd_mdm_patient_index)
export interface MasterPatientIndex {
  uuid: string;
  firstName?: unknown;
  lastName?: unknown;
  fullName?: unknown;
  dateOfBirth?: unknown;
  gender?: unknown;
  phone?: unknown;
  email?: unknown;
  nationalIdHash?: unknown;
  healthNumber?: unknown;
  addressLine?: unknown;
  city?: unknown;
  state?: unknown;
  postalCode?: unknown;
  country?: unknown;
  confidenceScore?: unknown;
  quality?: unknown;
  isGolden?: unknown;
  mergedIntoId?: unknown;
  mergeReason?: unknown;
  sourceSystems?: unknown;
  tags?: unknown;
  extension?: unknown;
}

// backend model: MasterProviderIndex  (table: hd_mdm_provider_index)
export interface MasterProviderIndex {
  uuid: string;
  firstName?: unknown;
  lastName?: unknown;
  fullName?: unknown;
  specialty?: unknown;
  licenseNumber?: unknown;
  nationalIdHash?: unknown;
  phone?: unknown;
  email?: unknown;
  confidenceScore?: unknown;
  quality?: unknown;
  isGolden?: unknown;
  mergedIntoId?: unknown;
  sourceSystems?: unknown;
  extension?: unknown;
}

// backend model: MasterOrganizationIndex  (table: hd_mdm_organization_index)
export interface MasterOrganizationIndex {
  uuid: string;
  name?: unknown;
  nameAr?: unknown;
  organizationType?: unknown;
  taxId?: unknown;
  registrationNumber?: unknown;
  phone?: unknown;
  email?: unknown;
  website?: unknown;
  addressLine?: unknown;
  city?: unknown;
  state?: unknown;
  postalCode?: unknown;
  country?: unknown;
  confidenceScore?: unknown;
  quality?: unknown;
  isGolden?: unknown;
  mergedIntoId?: unknown;
  sourceSystems?: unknown;
  extension?: unknown;
}

// backend model: MasterFacilityIndex  (table: hd_mdm_facility_index)
export interface MasterFacilityIndex {
  uuid: string;
  name?: unknown;
  nameAr?: unknown;
  facilityType?: unknown;
  facilityCode?: unknown;
  organizationId?: unknown;
  phone?: unknown;
  email?: unknown;
  addressLine?: unknown;
  city?: unknown;
  state?: unknown;
  postalCode?: unknown;
  country?: unknown;
  coordinates?: unknown;
  confidenceScore?: unknown;
  quality?: unknown;
  isGolden?: unknown;
  mergedIntoId?: unknown;
  sourceSystems?: unknown;
  extension?: unknown;
}

// backend model: PatientSummary  (table: hd_ods_patient_summary)
export interface PatientSummary {
  uuid: string;
  patientId?: unknown;
  patientUlid?: unknown;
  fullName?: unknown;
  gender?: unknown;
  age?: unknown;
  dateOfBirth?: unknown;
  totalEncounters?: unknown;
  totalOrders?: unknown;
  totalResults?: unknown;
  lastEncounterDate?: unknown;
  lastOrderDate?: unknown;
  lastResultDate?: unknown;
  activeOrders?: unknown;
  criticalResults?: unknown;
  summaryData?: unknown;
  refreshedAt?: unknown;
}

// backend model: EncounterSummary  (table: hd_ods_encounter_summary)
export interface EncounterSummary {
  uuid: string;
  encounterId?: unknown;
  patientId?: unknown;
  encounterType?: unknown;
  status?: unknown;
  periodStart?: unknown;
  periodEnd?: unknown;
  durationMinutes?: unknown;
  diagnosisCount?: unknown;
  procedureCount?: unknown;
  medicationCount?: unknown;
  labOrderCount?: unknown;
  hasCriticalResults?: unknown;
  summaryData?: unknown;
  refreshedAt?: unknown;
}

// backend model: LabResultSummary  (table: hd_ods_lab_result_summary)
export interface LabResultSummary {
  uuid: string;
  resultId?: unknown;
  orderId?: unknown;
  patientId?: unknown;
  testCode?: unknown;
  testName?: unknown;
  value?: unknown;
  unit?: unknown;
  flag?: unknown;
  isCritical?: unknown;
  isAbnormal?: unknown;
  referenceRangeLow?: unknown;
  referenceRangeHigh?: unknown;
  performedAt?: unknown;
  verifiedAt?: unknown;
  summaryData?: unknown;
  refreshedAt?: unknown;
}

// backend model: OrderSummary  (table: hd_ods_order_summary)
export interface OrderSummary {
  uuid: string;
  orderId?: unknown;
  patientId?: unknown;
  orderType?: unknown;
  status?: unknown;
  priority?: unknown;
  testCount?: unknown;
  completedTestCount?: unknown;
  pendingTestCount?: unknown;
  hasCritical?: unknown;
  hasAbnormal?: unknown;
  orderedAt?: unknown;
  collectedAt?: unknown;
  completedAt?: unknown;
  turnaroundHours?: unknown;
  summaryData?: unknown;
  refreshedAt?: unknown;
}

// backend model: DimLabTest  (table: hd_wh_dim_lab_test)
export interface DimLabTest {
  uuid: string;
  testCode?: unknown;
  testName?: unknown;
  testNameAr?: unknown;
  category?: unknown;
  department?: unknown;
  unit?: unknown;
  loincCode?: unknown;
}

// backend model: FactEncounter  (table: hd_wh_fact_encounter)
export interface FactEncounter {
  uuid: string;
  encounterUlid?: unknown;
  patientKey?: unknown;
  dateKey?: unknown;
  facilityKey?: unknown;
  providerKey?: unknown;
  labId?: unknown;
  encounterType?: unknown;
  status?: unknown;
  durationMinutes?: unknown;
  diagnosisCount?: unknown;
  procedureCount?: unknown;
  medicationCount?: unknown;
  labOrderCount?: unknown;
  isEmergency?: unknown;
  isReadmission?: unknown;
}

// backend model: FactOrder  (table: hd_wh_fact_order)
export interface FactOrder {
  uuid: string;
  orderUlid?: unknown;
  patientKey?: unknown;
  dateKey?: unknown;
  facilityKey?: unknown;
  providerKey?: unknown;
  labId?: unknown;
  orderType?: unknown;
  status?: unknown;
  priority?: unknown;
  testCount?: unknown;
  completedTestCount?: unknown;
  turnaroundHours?: unknown;
  hasCritical?: unknown;
  hasAbnormal?: unknown;
  orderedAt?: unknown;
  collectedAt?: unknown;
  completedAt?: unknown;
}

// backend model: ICUAdmissionModel  (table: critical_care_admissions)
export interface ICUAdmissionModel {
  uuid: string;
  patientId?: unknown;
  patientName?: unknown;
  medicalRecordNumber?: unknown;
  icuType?: unknown;
  admissionType?: unknown;
  admissionSource?: unknown;
  admissionDiagnosis?: unknown;
  admittingPhysician?: unknown;
  bedId?: unknown;
  roomId?: unknown;
  unitId?: unknown;
  facilityId?: unknown;
  status?: unknown;
  isolationType?: unknown;
  isolationReason?: unknown;
  admittingNotes?: unknown;
  primaryProblemList?: unknown;
  allergies?: unknown;
  codeStatus?: unknown;
  organDonorStatus?: unknown;
  expectedDischargeDate?: unknown;
  dischargedAt?: unknown;
  dischargeSummary?: unknown;
  dischargeDestination?: unknown;
  dischargeReason?: unknown;
  readmissionWithin48h?: unknown;
}

// backend model: ICUBedModel  (table: critical_care_beds)
export interface ICUBedModel {
  uuid: string;
  bedLabel?: unknown;
  roomId?: unknown;
  unitId?: unknown;
  facilityId?: unknown;
  icuType?: unknown;
  isOccupied?: unknown;
  currentPatientId?: unknown;
  currentAdmissionId?: unknown;
  hasVentilator?: unknown;
  hasMonitor?: unknown;
  hasInfusionPump?: unknown;
  hasDialysis?: unknown;
  supportedVentilatorTypes?: unknown;
  lastCleanedAt?: unknown;
}

// backend model: ICUAssessmentModel  (table: critical_care_assessments)
export interface ICUAssessmentModel {
  uuid: string;
  admissionId?: unknown;
  patientId?: unknown;
  assessmentDate?: unknown;
  assessedBy?: unknown;
  clinicalAssessment?: unknown;
  respiratoryAssessment?: unknown;
  cardiovascularAssessment?: unknown;
  neurologicalAssessment?: unknown;
  renalAssessment?: unknown;
  giAssessment?: unknown;
  skinAssessment?: unknown;
  painAssessment?: unknown;
  sedationAssessment?: unknown;
  deliriumAssessment?: unknown;
  mobilityAssessment?: unknown;
  plan?: unknown;
}

// backend model: VitalSignsRecordModel  (table: critical_care_vital_signs)
export interface VitalSignsRecordModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  recordedAt?: unknown;
  recordedBy?: unknown;
  heartRate?: unknown;
  respiratoryRate?: unknown;
  systolicBp?: unknown;
  diastolicBp?: unknown;
  meanArterialPressure?: unknown;
  temperature?: unknown;
  oxygenSaturation?: unknown;
  fiO2?: unknown;
  pao2?: unknown;
  paco2?: unknown;
  ph?: unknown;
  hco3?: unknown;
  lactate?: unknown;
  glucose?: unknown;
  cvp?: unknown;
  cardiacOutput?: unknown;
  cardiacIndex?: unknown;
  svr?: unknown;
  pvr?: unknown;
  svO2?: unknown;
  gcsTotal?: unknown;
  gcsEye?: unknown;
  gcsVerbal?: unknown;
  gcsMotor?: unknown;
  pupilRight?: unknown;
  pupilLeft?: unknown;
  painScore?: unknown;
  sedationScore?: unknown;
  sedationScale?: unknown;
  ricamIcu?: unknown;
  notes?: unknown;
}

// backend model: VentilatorSettingModel  (table: critical_care_ventilator_settings)
export interface VentilatorSettingModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  settingTime?: unknown;
  setBy?: unknown;
  mode?: unknown;
  ventilatorType?: unknown;
  tidalVolumeMl?: unknown;
  respiratoryRateSet?: unknown;
  respiratoryRateTotal?: unknown;
  peepCmh2o?: unknown;
  pressureSupport?: unknown;
  peakInspiratoryPressure?: unknown;
  plateauPressure?: unknown;
  meanAirwayPressure?: unknown;
  fiO2?: unknown;
  inspiratoryTime?: unknown;
  ieRatio?: unknown;
  minuteVentilation?: unknown;
  staticCompliance?: unknown;
  drivingPressure?: unknown;
  rsbi?: unknown;
  etco2?: unknown;
  spontaneousBreathingTrials?: unknown;
  weaningProtocol?: unknown;
  sedationHold?: unknown;
  notes?: unknown;
}

// backend model: ContinuousInfusionModel  (table: critical_care_infusions)
export interface ContinuousInfusionModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  medication?: unknown;
  medicationDose?: unknown;
  rate?: unknown;
  rateUnits?: unknown;
  route?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  initiatedBy?: unknown;
  pumpId?: unknown;
  titratedTo?: unknown;
  titrationHistory?: unknown;
  compatibleWith?: unknown;
  incompatibleWith?: unknown;
  bagVolumeMl?: unknown;
  bagRemainingMl?: unknown;
  lineType?: unknown;
  lineSite?: unknown;
  siteAssessment?: unknown;
  isPca?: unknown;
  notes?: unknown;
  status?: unknown;
}

// backend model: FluidBalanceModel  (table: critical_care_fluid_balance)
export interface FluidBalanceModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  recordedAt?: unknown;
  recordedBy?: unknown;
  totalIntakeMl?: unknown;
  totalOutputMl?: unknown;
  netBalanceMl?: unknown;
  cumulativeBalanceMl?: unknown;
  ivFluidsMl?: unknown;
  enteralFeedingMl?: unknown;
  oralIntakeMl?: unknown;
  bloodProductsMl?: unknown;
  urineOutputMl?: unknown;
  stoolOutputMl?: unknown;
  ngOutputMl?: unknown;
  drainOutputMl?: unknown;
  estimatedBloodLossMl?: unknown;
  insensibleLossesMl?: unknown;
  notes?: unknown;
}

// backend model: EarlyWarningScoreModel  (table: critical_care_early_warning_scores)
export interface EarlyWarningScoreModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  scoreTime?: unknown;
  scoreSystem?: unknown;
  scoreValue?: unknown;
  heartRateScore?: unknown;
  respiratoryRateScore?: unknown;
  systolicBpScore?: unknown;
  temperatureScore?: unknown;
  consciousnessScore?: unknown;
  oxygenScore?: unknown;
  supplementalOxygen?: unknown;
  riskCategory?: unknown;
  recommendedFrequency?: unknown;
  triggersEscalation?: unknown;
  calculatedBy?: unknown;
}

// backend model: ICUScoreModel  (table: critical_care_scores)
export interface ICUScoreModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  scoreTime?: unknown;
  scoreType?: unknown;
  scoreValue?: unknown;
  scoreComponents?: unknown;
  mortalityPrediction?: unknown;
  calculatedBy?: unknown;
}

// backend model: CriticalAlertModel  (table: critical_care_alerts)
export interface CriticalAlertModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  alertType?: unknown;
  severity?: unknown;
  alertMessage?: unknown;
  alertTime?: unknown;
  triggeredBy?: unknown;
  parameter?: unknown;
  value?: unknown;
  threshold?: unknown;
  acknowledgedBy?: unknown;
  acknowledgedAt?: unknown;
  resolvedBy?: unknown;
  resolvedAt?: unknown;
  actionTaken?: unknown;
}

// backend model: DeviceIntegrationModel  (table: critical_care_device_integrations)
export interface DeviceIntegrationModel {
  uuid: string;
  patientId?: unknown;
  admissionId?: unknown;
  deviceType?: unknown;
  deviceId?: unknown;
  deviceName?: unknown;
  vendor?: unknown;
  model?: unknown;
  connectivity?: unknown;
  isConnected?: unknown;
  lastDataReceived?: unknown;
  parameters?: unknown;
  settings?: unknown;
  alerts?: unknown;
}

// backend model: DailyChecklistModel  (table: critical_care_daily_checklists)
export interface DailyChecklistModel {
  uuid: string;
  admissionId?: unknown;
  patientId?: unknown;
  checklistDate?: unknown;
  completedBy?: unknown;
  ventilatorBundle?: unknown;
  centralLineBundle?: unknown;
  catheterBundle?: unknown;
  vteProphylaxis?: unknown;
  stressUlcerProphylaxis?: unknown;
  sedationVacation?: unknown;
  spontaneousBreathingTrial?: unknown;
  spontaneousAwakeningTrial?: unknown;
  glucoseControl?: unknown;
  nutritionAssessment?: unknown;
  mobilization?: unknown;
  familyCommunication?: unknown;
  goalsOfCare?: unknown;
  planForDay?: unknown;
  issues?: unknown;
}

// backend model: RoundRecordModel  (table: critical_care_rounds)
export interface RoundRecordModel {
  uuid: string;
  admissionId?: unknown;
  patientId?: unknown;
  roundDate?: unknown;
  attendingPhysician?: unknown;
  teamMembers?: unknown;
  overnightEvents?: unknown;
  reviewOfSystems?: unknown;
  assessment?: unknown;
  plan?: unknown;
  medicationsReviewed?: unknown;
  imagingReviewed?: unknown;
  labsReviewed?: unknown;
  microbiologyReviewed?: unknown;
  followUpItems?: unknown;
}

// backend model: AllergyIntolerance  (table: ehr_allergies)
export interface AllergyIntolerance {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  allergyType?: unknown;
  category?: unknown;
  criticality?: unknown;
  code?: unknown;
  codeSystem?: unknown;
  codeDisplay?: unknown;
  codeDisplayAr?: unknown;
  severity?: unknown;
  status?: unknown;
  verificationStatus?: unknown;
  reaction?: unknown;
  reactionDetails?: unknown;
  onsetDate?: unknown;
  recordedDate?: unknown;
  lastOccurrenceDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ClinicalAttachment  (table: ehr_clinical_attachments)
export interface ClinicalAttachment {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  uploadedBy?: unknown;
  sourceType?: unknown;
  sourceId?: unknown;
  fileName?: unknown;
  fileType?: unknown;
  fileSizeBytes?: unknown;
  storagePath?: unknown;
  storageBucket?: unknown;
  contentHash?: unknown;
  mimeType?: unknown;
  caption?: unknown;
  captionAr?: unknown;
  description?: unknown;
  isWatermarked?: unknown;
  isEncrypted?: unknown;
  isConfidential?: unknown;
  isArchived?: unknown;
  category?: unknown;
  sortOrder?: unknown;
  uploadedAt?: unknown;
  facilityId?: unknown;
}

// backend model: CarePlan  (table: ehr_care_plans)
export interface CarePlan {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  status?: unknown;
  intent?: unknown;
  title?: unknown;
  titleAr?: unknown;
  description?: unknown;
  periodStart?: unknown;
  periodEnd?: unknown;
  category?: unknown;
  contributor?: unknown;
  supportingInfo?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: CarePlanGoal  (table: ehr_care_plan_goals)
export interface CarePlanGoal {
  uuid: string;
  carePlanId?: unknown;
  description?: unknown;
  descriptionAr?: unknown;
  status?: unknown;
  priority?: unknown;
  targetDate?: unknown;
  achievementDate?: unknown;
  achievementNotes?: unknown;
  outcome?: unknown;
  measuredBy?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: CarePlanActivity  (table: ehr_care_plan_activities)
export interface CarePlanActivity {
  uuid: string;
  carePlanId?: unknown;
  goalId?: unknown;
  activityCode?: unknown;
  activityCodeSystem?: unknown;
  description?: unknown;
  descriptionAr?: unknown;
  status?: unknown;
  scheduledStart?: unknown;
  scheduledEnd?: unknown;
  actualStart?: unknown;
  actualEnd?: unknown;
  performer?: unknown;
  performerId?: unknown;
  location?: unknown;
  outcome?: unknown;
  progressNotes?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ClinicalNote  (table: ehr_clinical_notes)
export interface ClinicalNote {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  authorId?: unknown;
  noteType?: unknown;
  title?: unknown;
  titleAr?: unknown;
  content?: unknown;
  contentFormat?: unknown;
  version?: unknown;
  priorVersionId?: unknown;
  supersededById?: unknown;
  isFinal?: unknown;
  isSigned?: unknown;
  isAmended?: unknown;
  amendmentReason?: unknown;
  signedBy?: unknown;
  signedAt?: unknown;
  cosignedBy?: unknown;
  cosignedAt?: unknown;
  witnessedBy?: unknown;
  witnessedAt?: unknown;
  electronicSignature?: unknown;
  signatureHash?: unknown;
  authoredAt?: unknown;
  facilityId?: unknown;
  departmentId?: unknown;
  tags?: unknown;
  metadata?: unknown;
}

// backend model: ProblemListItem  (table: ehr_problem_list_items)
export interface ProblemListItem {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  status?: unknown;
  code?: unknown;
  codeSystem?: unknown;
  display?: unknown;
  displayAr?: unknown;
  clinicalStatus?: unknown;
  verificationStatus?: unknown;
  category?: unknown;
  severity?: unknown;
  onsetDate?: unknown;
  resolutionDate?: unknown;
  recordedDate?: unknown;
  bodySite?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ConditionRecord  (table: ehr_conditions)
export interface ConditionRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  clinicalStatus?: unknown;
  verificationStatus?: unknown;
  category?: unknown;
  severity?: unknown;
  code?: unknown;
  codeSystem?: unknown;
  codeDisplay?: unknown;
  codeDisplayAr?: unknown;
  icd10Code?: unknown;
  icd10Description?: unknown;
  bodySite?: unknown;
  laterality?: unknown;
  onsetDate?: unknown;
  abatementDate?: unknown;
  recordedDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: DiagnosisRecord  (table: ehr_diagnoses)
export interface DiagnosisRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  diagnosisType?: unknown;
  rank?: unknown;
  icd10Code?: unknown;
  icd10Description?: unknown;
  snomedCode?: unknown;
  snomedDescription?: unknown;
  diagnosisText?: unknown;
  diagnosisTextAr?: unknown;
  diagnosisDate?: unknown;
  resolutionDate?: unknown;
  isChronic?: unknown;
  certainty?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: FamilyHistoryRecord  (table: ehr_family_history)
export interface FamilyHistoryRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  practitionerId?: unknown;
  relationship?: unknown;
  relationshipDetail?: unknown;
  relativeName?: unknown;
  relativeCitizenId?: unknown;
  conditionCode?: unknown;
  conditionCodeSystem?: unknown;
  conditionDisplay?: unknown;
  conditionDisplayAr?: unknown;
  icd10Code?: unknown;
  icd10Description?: unknown;
  ageAtOnset?: unknown;
  ageAtOnsetUnit?: unknown;
  onsetAgeYears?: unknown;
  isDeceasedDueTo?: unknown;
  notes?: unknown;
  recordedDate?: unknown;
}

// backend model: ImmunizationRecord  (table: ehr_immunizations)
export interface ImmunizationRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  administratorId?: unknown;
  vaccineCode?: unknown;
  vaccineCodeSystem?: unknown;
  vaccineName?: unknown;
  vaccineNameAr?: unknown;
  administrationDate?: unknown;
  recordedDate?: unknown;
  manufacturer?: unknown;
  lotNumber?: unknown;
  expiryDate?: unknown;
  doseNumber?: unknown;
  doseSeries?: unknown;
  totalDoses?: unknown;
  route?: unknown;
  site?: unknown;
  doseQuantity?: unknown;
  doseUnit?: unknown;
  isCompleted?: unknown;
  status?: unknown;
  reasonNotGiven?: unknown;
  adverseEvent?: unknown;
  adverseEventReported?: unknown;
  facilityId?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: MedicationStatement  (table: ehr_medication_statements)
export interface MedicationStatement {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  medicationCode?: unknown;
  medicationCodeSystem?: unknown;
  medicationName?: unknown;
  medicationNameAr?: unknown;
  medicationBrand?: unknown;
  medicationForm?: unknown;
  strengthValue?: unknown;
  strengthUnit?: unknown;
  dosageText?: unknown;
  route?: unknown;
  frequency?: unknown;
  timing?: unknown;
  status?: unknown;
  category?: unknown;
  dateStarted?: unknown;
  dateEnded?: unknown;
  dateRecorded?: unknown;
  reasonCode?: unknown;
  reasonDescription?: unknown;
  note?: unknown;
  metadata?: unknown;
}

// backend model: MedicationRequest  (table: ehr_medication_requests)
export interface MedicationRequest {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  prescriberId?: unknown;
  medicationCode?: unknown;
  medicationCodeSystem?: unknown;
  medicationName?: unknown;
  medicationNameAr?: unknown;
  medicationBrand?: unknown;
  medicationForm?: unknown;
  status?: unknown;
  intent?: unknown;
  priority?: unknown;
  category?: unknown;
  dosageInstruction?: unknown;
  dosageInstructions?: unknown;
  route?: unknown;
  frequency?: unknown;
  quantity?: unknown;
  quantityUnit?: unknown;
  refills?: unknown;
  durationDays?: unknown;
  reasonCode?: unknown;
  reasonDescription?: unknown;
  clinicalIndication?: unknown;
  authoredOn?: unknown;
  validFrom?: unknown;
  validTo?: unknown;
  dispenseIntervalDays?: unknown;
  substitutionAllowed?: unknown;
  note?: unknown;
  metadata?: unknown;
}

// backend model: MedicationDispense  (table: ehr_medication_dispenses)
export interface MedicationDispense {
  uuid: string;
  medicationRequestId?: unknown;
  patientId?: unknown;
  citizenId?: unknown;
  dispenserId?: unknown;
  medicationCode?: unknown;
  medicationCodeSystem?: unknown;
  medicationName?: unknown;
  medicationNameAr?: unknown;
  medicationBrand?: unknown;
  medicationForm?: unknown;
  status?: unknown;
  category?: unknown;
  quantity?: unknown;
  quantityUnit?: unknown;
  daysSupply?: unknown;
  dosageInstruction?: unknown;
  route?: unknown;
  frequency?: unknown;
  preparedBy?: unknown;
  preparedAt?: unknown;
  verifiedBy?: unknown;
  verifiedAt?: unknown;
  dispensedAt?: unknown;
  lotNumber?: unknown;
  expiryDate?: unknown;
  note?: unknown;
  metadata?: unknown;
}

// backend model: MedicationAdministration  (table: ehr_medication_administrations)
export interface MedicationAdministration {
  uuid: string;
  medicationRequestId?: unknown;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  administratorId?: unknown;
  medicationCode?: unknown;
  medicationCodeSystem?: unknown;
  medicationName?: unknown;
  medicationNameAr?: unknown;
  status?: unknown;
  category?: unknown;
  doseValue?: unknown;
  doseUnit?: unknown;
  route?: unknown;
  site?: unknown;
  method?: unknown;
  administrationTime?: unknown;
  recordedTime?: unknown;
  reasonNotGiven?: unknown;
  note?: unknown;
  metadata?: unknown;
}

// backend model: RiskFactorRecord  (table: ehr_risk_factors)
export interface RiskFactorRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  riskType?: unknown;
  riskLevel?: unknown;
  scoreName?: unknown;
  scoreValue?: unknown;
  scoreMaximum?: unknown;
  scorePercent?: unknown;
  scoreVersion?: unknown;
  factors?: unknown;
  recommendations?: unknown;
  assessmentDate?: unknown;
  nextAssessmentDate?: unknown;
  isHighRisk?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: SocialHistoryRecord  (table: ehr_social_history)
export interface SocialHistoryRecord {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  encounterId?: unknown;
  practitionerId?: unknown;
  smokingStatus?: unknown;
  smokingPackYears?: unknown;
  smokingQuitDate?: unknown;
  smokingStartAge?: unknown;
  smokingFrequency?: unknown;
  alcoholStatus?: unknown;
  alcoholFrequency?: unknown;
  alcoholQuitDate?: unknown;
  alcoholStartAge?: unknown;
  occupation?: unknown;
  occupationHistory?: unknown;
  occupationalHazards?: unknown;
  disabilityType?: unknown;
  disabilityDetail?: unknown;
  disabilitySince?: unknown;
  exerciseFrequency?: unknown;
  dietNotes?: unknown;
  lifestyleFactors?: unknown;
  recordedDate?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: PatientTimelineEvent  (table: ehr_patient_timeline)
export interface PatientTimelineEvent {
  uuid: string;
  patientId?: unknown;
  citizenId?: unknown;
  eventType?: unknown;
  eventDate?: unknown;
  sourceType?: unknown;
  sourceId?: unknown;
  title?: unknown;
  titleAr?: unknown;
  description?: unknown;
  facilityId?: unknown;
  practitionerId?: unknown;
  encounterId?: unknown;
  severity?: unknown;
  isHighlighted?: unknown;
  isCritical?: unknown;
  icon?: unknown;
  color?: unknown;
  metadata?: unknown;
}

// backend model: PilotProgramModel  (table: pilot_programs)
export interface PilotProgramModel {
  uuid: string;
  moduleName?: unknown;
  modulePath?: unknown;
  version?: unknown;
  currentPhase?: unknown;
  status?: unknown;
  strategy?: unknown;
  pilotLead?: unknown;
  technicalLead?: unknown;
  clinicalLead?: unknown;
  startDate?: unknown;
  targetCompletion?: unknown;
  completedAt?: unknown;
  description?: unknown;
  phases?: unknown;
  facilities?: unknown;
}

// backend model: PilotFacilityModel  (table: pilot_facilities)
export interface PilotFacilityModel {
  uuid: string;
  pilotId?: unknown;
  facilityId?: unknown;
  facilityName?: unknown;
  phase?: unknown;
  readinessLevel?: unknown;
  readinessScore?: unknown;
  enrolledAt?: unknown;
  completedAt?: unknown;
  goNoGoApproved?: unknown;
  issues?: unknown;
}

// backend model: ReadinessChecklistModel  (table: pilot_readiness_checklists)
export interface ReadinessChecklistModel {
  uuid: string;
  pilotId?: unknown;
  facilityId?: unknown;
  items?: unknown;
  overallScore?: unknown;
  level?: unknown;
  assessedBy?: unknown;
  assessedAt?: unknown;
}

// backend model: GoNoGoGateModel  (table: pilot_go_no_go_gates)
export interface GoNoGoGateModel {
  uuid: string;
  pilotId?: unknown;
  facilityId?: unknown;
  gateName?: unknown;
  result?: unknown;
  certificationLevel?: unknown;
  metrics?: unknown;
  approver?: unknown;
  decidedAt?: unknown;
  comments?: unknown;
}

// backend model: DeploymentRecordModel  (table: pilot_deployment_records)
export interface DeploymentRecordModel {
  uuid: string;
  pilotId?: unknown;
  module?: unknown;
  version?: unknown;
  facilityId?: unknown;
  strategy?: unknown;
  status?: unknown;
  deployedAt?: unknown;
  deployedBy?: unknown;
  healthCheckPassed?: unknown;
  rollbackAt?: unknown;
  rollbackReason?: unknown;
  notes?: unknown;
}

// backend model: Admission  (table: nhdw_admissions)
export interface Admission {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  hospitalId?: unknown;
  departmentId?: unknown;
  roomId?: unknown;
  bedId?: unknown;
  admissionType?: unknown;
  admissionDate?: unknown;
  expectedDischargeDate?: unknown;
  dischargeDate?: unknown;
  dischargeType?: unknown;
  diagnosis?: unknown;
  diagnosisCode?: unknown;
  diagnosisSystem?: unknown;
  admittingDoctorId?: unknown;
  referringDoctorId?: unknown;
  insuranceId?: unknown;
  insurancePolicy?: unknown;
  isEmergency?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: Discharge  (table: nhdw_discharges)
export interface Discharge {
  uuid: string;
  admissionId?: unknown;
  patientId?: unknown;
  encounterId?: unknown;
  dischargeDate?: unknown;
  dischargeType?: unknown;
  dischargeDestination?: unknown;
  dischargeSummary?: unknown;
  medicationsAtDischarge?: unknown;
  followUpInstructions?: unknown;
  followUpDate?: unknown;
  followUpProviderId?: unknown;
  dischargedBy?: unknown;
  mortalityReview?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: Transfer  (table: nhdw_transfers)
export interface Transfer {
  uuid: string;
  patientId?: unknown;
  fromDepartmentId?: unknown;
  toDepartmentId?: unknown;
  fromRoomId?: unknown;
  toRoomId?: unknown;
  fromBedId?: unknown;
  toBedId?: unknown;
  fromDoctorId?: unknown;
  toDoctorId?: unknown;
  reason?: unknown;
  clinicalSummary?: unknown;
  transferredBy?: unknown;
  transferDate?: unknown;
  transferType?: unknown;
  status?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: QueueEntry  (table: nhdw_queue_entries)
export interface QueueEntry {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  departmentId?: unknown;
  clinicId?: unknown;
  priority?: unknown;
  queueDate?: unknown;
  checkInTime?: unknown;
  seenTime?: unknown;
  completedTime?: unknown;
  totalWaitMinutes?: unknown;
  status?: unknown;
  visitReason?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: WaitingListEntry  (table: nhdw_waiting_list_entries)
export interface WaitingListEntry {
  uuid: string;
  patientId?: unknown;
  departmentId?: unknown;
  procedureCode?: unknown;
  procedureName?: unknown;
  priority?: unknown;
  listedDate?: unknown;
  clinicalUrgency?: unknown;
  status?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ClinicalTask  (table: nhdw_clinical_tasks)
export interface ClinicalTask {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  assignedTo?: unknown;
  assignedBy?: unknown;
  taskType?: unknown;
  description?: unknown;
  priority?: unknown;
  status?: unknown;
  dueDate?: unknown;
  scheduledTime?: unknown;
  completedAt?: unknown;
  completedBy?: unknown;
  notes?: unknown;
  metadata?: unknown;
  isRecurring?: unknown;
  recurrenceRule?: unknown;
}

// backend model: WardRound  (table: nhdw_ward_rounds)
export interface WardRound {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  departmentId?: unknown;
  leadDoctorId?: unknown;
  roundDate?: unknown;
  participants?: unknown;
  clinicalSummary?: unknown;
  assessment?: unknown;
  plan?: unknown;
  medicationsReviewed?: unknown;
  investigationsOrdered?: unknown;
  followUpPlan?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: HospitalAlert  (table: nhdw_hospital_alerts)
export interface HospitalAlert {
  uuid: string;
  alertType?: unknown;
  severity?: unknown;
  title?: unknown;
  titleAr?: unknown;
  description?: unknown;
  sourceDepartmentId?: unknown;
  triggeredBy?: unknown;
  patientId?: unknown;
  isResolved?: unknown;
  resolvedAt?: unknown;
  resolvedBy?: unknown;
  acknowledgedBy?: unknown;
  metadata?: unknown;
}

// backend model: HospitalMessage  (table: nhdw_hospital_messages)
export interface HospitalMessage {
  uuid: string;
  senderId?: unknown;
  recipientId?: unknown;
  subject?: unknown;
  body?: unknown;
  priority?: unknown;
  isRead?: unknown;
  readAt?: unknown;
  departmentId?: unknown;
  parentMessageId?: unknown;
  hasAttachments?: unknown;
  metadata?: unknown;
}

// backend model: TelemedicineSession  (table: nhdw_telemedicine_sessions)
export interface TelemedicineSession {
  uuid: string;
  patientId?: unknown;
  providerId?: unknown;
  scheduledAt?: unknown;
  startedAt?: unknown;
  endedAt?: unknown;
  sessionType?: unknown;
  platform?: unknown;
  meetingUrl?: unknown;
  recordingUrl?: unknown;
  status?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: ResourceSchedule  (table: nhdw_resource_schedules)
export interface ResourceSchedule {
  uuid: string;
  resourceType?: unknown;
  resourceId?: unknown;
  scheduledDate?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  status?: unknown;
  bookedBy?: unknown;
  bookedForPatientId?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: DashboardConfiguration  (table: nhdw_dashboard_configurations)
export interface DashboardConfiguration {
  uuid: string;
  userId?: unknown;
  role?: unknown;
  departmentId?: unknown;
  configJson?: unknown;
  isDefault?: unknown;
}

// backend model: ShiftReport  (table: nhdw_shift_reports)
export interface ShiftReport {
  uuid: string;
  departmentId?: unknown;
  shiftType?: unknown;
  shiftDate?: unknown;
  startTime?: unknown;
  endTime?: unknown;
  reportAuthor?: unknown;
  patientCount?: unknown;
  admissionsCount?: unknown;
  dischargesCount?: unknown;
  transfersCount?: unknown;
  criticalEvents?: unknown;
  staffing?: unknown;
  issues?: unknown;
  notes?: unknown;
  metadata?: unknown;
}

// backend model: OrderSet  (table: clinical_order_sets)
export interface OrderSet {
  uuid: string;
  name?: unknown;
  description?: unknown;
  department?: unknown;
  condition?: unknown;
  version?: unknown;
  isEmergency?: unknown;
  priority?: unknown;
  requiredJustification?: unknown;
  guidelineId?: unknown;
  effectiveStart?: unknown;
  effectiveEnd?: unknown;
}

// backend model: OrderSetItem  (table: clinical_order_set_items)
export interface OrderSetItem {
  uuid: string;
  orderSetId?: unknown;
  itemType?: unknown;
  itemCode?: unknown;
  itemDisplay?: unknown;
  sequence?: unknown;
  isOptional?: unknown;
  isRequired?: unknown;
  defaultValue?: unknown;
  instructions?: unknown;
  frequency?: unknown;
}

// backend model: CareBundle  (table: clinical_care_bundles)
export interface CareBundle {
  uuid: string;
  name?: unknown;
  description?: unknown;
  condition?: unknown;
  version?: unknown;
  evidenceLevel?: unknown;
  complianceThreshold?: unknown;
  elementsSummary?: unknown;
  rationale?: unknown;
  guidelineId?: unknown;
}

// backend model: CareBundleElement  (table: clinical_care_bundle_elements)
export interface CareBundleElement {
  uuid: string;
  careBundleId?: unknown;
  elementCode?: unknown;
  elementName?: unknown;
  description?: unknown;
  sequence?: unknown;
  isAllOrNone?: unknown;
  timeWindow?: unknown;
  numerator?: unknown;
  denominator?: unknown;
}

// backend model: ClinicalAlert  (table: clinical_alerts)
export interface ClinicalAlert {
  uuid: string;
  alertType?: unknown;
  severity?: unknown;
  patientId?: unknown;
  encounterId?: unknown;
  providerId?: unknown;
  title?: unknown;
  message?: unknown;
  detail?: unknown;
  triggerCode?: unknown;
  triggerSystem?: unknown;
  triggerValue?: unknown;
  isActionable?: unknown;
  acknowledged?: unknown;
  acknowledgedBy?: unknown;
  acknowledgedAt?: unknown;
  resolved?: unknown;
  resolvedBy?: unknown;
  resolvedAt?: unknown;
  sourceRuleId?: unknown;
}

// backend model: ClinicalAlertAction  (table: clinical_alert_actions)
export interface ClinicalAlertAction {
  uuid: string;
  alertId?: unknown;
  action?: unknown;
  description?: unknown;
  parameters?: unknown;
  executed?: unknown;
  executedBy?: unknown;
  executedAt?: unknown;
  outcome?: unknown;
}

// backend model: DuplicateOrderRule  (table: clinical_duplicate_order_rules)
export interface DuplicateOrderRule {
  uuid: string;
  orderCode?: unknown;
  orderSystem?: unknown;
  ruleName?: unknown;
  description?: unknown;
  timeWindowHours?: unknown;
  sameEncounterOnly?: unknown;
  sameProviderOnly?: unknown;
  action?: unknown;
  severity?: unknown;
  notificationMessage?: unknown;
  overrideRequiresApproval?: unknown;
  overrideReasonRequired?: unknown;
}

// backend model: ReminderRule  (table: clinical_reminder_rules)
export interface ReminderRule {
  uuid: string;
  name?: unknown;
  description?: unknown;
  triggerEvent?: unknown;
  conditionExpression?: unknown;
  actionType?: unknown;
  actionConfig?: unknown;
  priority?: unknown;
  frequency?: unknown;
  maxReminders?: unknown;
  escalationAfterHours?: unknown;
  escalationAction?: unknown;
  effectiveStart?: unknown;
  effectiveEnd?: unknown;
  targetRole?: unknown;
}

// backend model: PreventiveRecommendation  (table: clinical_preventive_recommendations)
export interface PreventiveRecommendation {
  uuid: string;
  title?: unknown;
  condition?: unknown;
  description?: unknown;
  recommendationType?: unknown;
  intervention?: unknown;
  interventionCode?: unknown;
  interventionSystem?: unknown;
  frequency?: unknown;
  ageMin?: unknown;
  ageMax?: unknown;
  gender?: unknown;
  riskFactors?: unknown;
  evidenceLevel?: unknown;
  guidelineId?: unknown;
  effectiveStart?: unknown;
  effectiveEnd?: unknown;
  priority?: unknown;
  source?: unknown;
}

// backend model: QualityIndicator  (table: clinical_quality_indicators)
export interface QualityIndicator {
  uuid: string;
  name?: unknown;
  code?: unknown;
  indicatorType?: unknown;
  description?: unknown;
  department?: unknown;
  numerator?: unknown;
  denominator?: unknown;
  targetValue?: unknown;
  benchmarkValue?: unknown;
  unit?: unknown;
  frequency?: unknown;
  direction?: unknown;
  isNational?: unknown;
  steward?: unknown;
  source?: unknown;
  effectiveStart?: unknown;
  effectiveEnd?: unknown;
}

// backend model: IndicatorMeasurement  (table: clinical_indicator_measurements)
export interface IndicatorMeasurement {
  uuid: string;
  indicatorId?: unknown;
  measurementDate?: unknown;
  periodStart?: unknown;
  periodEnd?: unknown;
  numeratorValue?: unknown;
  denominatorValue?: unknown;
  resultValue?: unknown;
  percentage?: unknown;
  metTarget?: unknown;
  notes?: unknown;
  measuredBy?: unknown;
}

// backend model: ClinicalAuditRecord  (table: clinical_audit_records)
export interface ClinicalAuditRecord {
  uuid: string;
  auditType?: unknown;
  patientId?: unknown;
  encounterId?: unknown;
  providerId?: unknown;
  department?: unknown;
  auditDate?: unknown;
  criteria?: unknown;
  finding?: unknown;
  compliance?: unknown;
  score?: unknown;
  severity?: unknown;
  recommendations?: unknown;
  correctiveAction?: unknown;
  correctiveDeadline?: unknown;
  correctiveCompleted?: unknown;
  correctiveCompletedAt?: unknown;
  auditedBy?: unknown;
  reviewedBy?: unknown;
}

// backend model: BenchmarkValue  (table: clinical_benchmark_values)
export interface BenchmarkValue {
  uuid: string;
  indicatorId?: unknown;
  benchmarkName?: unknown;
  source?: unknown;
  value?: unknown;
  percentile?: unknown;
  year?: unknown;
  region?: unknown;
  setting?: unknown;
  population?: unknown;
  isNational?: unknown;
}

// backend model: MortalityReview  (table: clinical_mortality_reviews)
export interface MortalityReview {
  uuid: string;
  patientId?: unknown;
  encounterId?: unknown;
  dateOfDeath?: unknown;
  causeOfDeath?: unknown;
  causeCode?: unknown;
  causeSystem?: unknown;
  location?: unknown;
  department?: unknown;
  reviewDate?: unknown;
  reviewer?: unknown;
  classification?: unknown;
  preventability?: unknown;
  contributingFactors?: unknown;
  summary?: unknown;
  recommendations?: unknown;
  isAutopsyPerformed?: unknown;
  autopsyFindings?: unknown;
  isCompleted?: unknown;
}

// backend model: IncidentReport  (table: clinical_incident_reports)
export interface IncidentReport {
  uuid: string;
  incidentType?: unknown;
  incidentDate?: unknown;
  severity?: unknown;
  location?: unknown;
  department?: unknown;
  patientId?: unknown;
  encounterId?: unknown;
  reporterId?: unknown;
  description?: unknown;
  immediateAction?: unknown;
  contributingFactors?: unknown;
  rootCause?: unknown;
  outcome?: unknown;
  actionsTaken?: unknown;
  status?: unknown;
  reviewedBy?: unknown;
  reviewComments?: unknown;
  isNotifiable?: unknown;
  notifiedAuthority?: unknown;
  notifiedAt?: unknown;
}

// backend model: PatientSafetyEvent  (table: clinical_patient_safety_events)
export interface PatientSafetyEvent {
  uuid: string;
  category?: unknown;
  eventType?: unknown;
  patientId?: unknown;
  encounterId?: unknown;
  providerId?: unknown;
  eventDate?: unknown;
  severity?: unknown;
  description?: unknown;
  harmLevel?: unknown;
  preventability?: unknown;
  contributingFactors?: unknown;
  mitigatingFactors?: unknown;
  actionsTaken?: unknown;
  outcome?: unknown;
  reportedBy?: unknown;
  reviewedBy?: unknown;
  reviewDate?: unknown;
  status?: unknown;
  isSentinel?: unknown;
  sentinelReviewCompleted?: unknown;
}

// backend model: ClinicalProtocol  (table: clinical_protocols)
export interface ClinicalProtocol {
  uuid: string;
  title?: unknown;
  protocolId?: unknown;
  version?: unknown;
  status?: unknown;
  guidelineId?: unknown;
  department?: unknown;
  procedureCategory?: unknown;
  description?: unknown;
  inclusionCriteria?: unknown;
  exclusionCriteria?: unknown;
  prerequisites?: unknown;
  steps?: unknown;
  durationExpected?: unknown;
  requiredEquipment?: unknown;
  requiredPersonnel?: unknown;
  complications?: unknown;
  outcomeMeasures?: unknown;
  effectiveDate?: unknown;
  expirationDate?: unknown;
  isEmergency?: unknown;
  isSurgical?: unknown;
}

// backend model: ClinicalPathway  (table: clinical_pathways)
export interface ClinicalPathway {
  uuid: string;
  name?: unknown;
  version?: unknown;
  status?: unknown;
  condition?: unknown;
  description?: unknown;
  durationDays?: unknown;
  phases?: unknown;
  milestones?: unknown;
  expectedOutcomes?: unknown;
  inclusionCriteria?: unknown;
  exclusionCriteria?: unknown;
  targetPopulation?: unknown;
  setting?: unknown;
  effectiveDate?: unknown;
  expirationDate?: unknown;
  owner?: unknown;
}

// backend model: PathwayPhase  (table: clinical_pathway_phases)
export interface PathwayPhase {
  uuid: string;
  pathwayId?: unknown;
  phaseNumber?: unknown;
  name?: unknown;
  description?: unknown;
  duration?: unknown;
  criteria?: unknown;
  interventions?: unknown;
  expectedOutcome?: unknown;
  escalationTriggers?: unknown;
}

// backend model: StandingOrder  (table: clinical_standing_orders)
export interface StandingOrder {
  uuid: string;
  title?: unknown;
  orderId?: unknown;
  description?: unknown;
  department?: unknown;
  orderType?: unknown;
  orderDetails?: unknown;
  indication?: unknown;
  contraindications?: unknown;
  frequency?: unknown;
  duration?: unknown;
  priority?: unknown;
  requiresApproval?: unknown;
  effectiveStart?: unknown;
  effectiveEnd?: unknown;
  approverRole?: unknown;
  protocolId?: unknown;
}

// backend model: ClinicalRecommendation  (table: clinical_recommendations)
export interface ClinicalRecommendation {
  uuid: string;
  guidelineId?: unknown;
  recommendationNumber?: unknown;
  title?: unknown;
  text?: unknown;
  rationale?: unknown;
  evidenceLevel?: unknown;
  strength?: unknown;
  grade?: unknown;
  population?: unknown;
  action?: unknown;
  condition?: unknown;
  exceptions?: unknown;
  references?: unknown;
  isConditional?: unknown;
}

// backend model: GuidelineApproval  (table: clinical_guideline_approvals)
export interface GuidelineApproval {
  uuid: string;
  guidelineId?: unknown;
  approverId?: unknown;
  approverName?: unknown;
  approverRole?: unknown;
  organization?: unknown;
  decision?: unknown;
  comments?: unknown;
  approvedAt?: unknown;
  effectiveFrom?: unknown;
  effectiveUntil?: unknown;
}

// backend model: TerminologyCode  (table: clinical_terminology_codes)
export interface TerminologyCode {
  uuid: string;
  code?: unknown;
  display?: unknown;
  system?: unknown;
  versionId?: unknown;
  parentId?: unknown;
  definition?: unknown;
  isLeaf?: unknown;
  effectiveDate?: unknown;
  status?: unknown;
}

// backend model: TerminologyVersion  (table: clinical_terminology_versions)
export interface TerminologyVersion {
  uuid: string;
  system?: unknown;
  version?: unknown;
  releaseDate?: unknown;
  description?: unknown;
  isCurrent?: unknown;
  codesCount?: unknown;
  importedAt?: unknown;
}

// backend model: ValueSet  (table: clinical_value_sets)
export interface ValueSet {
  uuid: string;
  name?: unknown;
  oid?: unknown;
  description?: unknown;
  purpose?: unknown;
  isExtensible?: unknown;
  isExperimental?: unknown;
  steward?: unknown;
  source?: unknown;
  version?: unknown;
  effectiveStart?: unknown;
  effectiveEnd?: unknown;
}

// backend model: ValueSetMember  (table: clinical_value_set_members)
export interface ValueSetMember {
  uuid: string;
  valueSetId?: unknown;
  codeId?: unknown;
  inclusion?: unknown;
  order?: unknown;
}

// backend model: CodeSystem  (table: clinical_code_systems)
export interface CodeSystem {
  uuid: string;
  name?: unknown;
  system?: unknown;
  uri?: unknown;
  oid?: unknown;
  description?: unknown;
  publisher?: unknown;
  contact?: unknown;
  copyright?: unknown;
  version?: unknown;
  totalCodes?: unknown;
  isCaseSensitive?: unknown;
  hierarchyMeaning?: unknown;
}

// backend model: ICD10Code  (table: clinical_icd10_codes)
export interface ICD10Code {
  uuid: string;
  code?: unknown;
  shortDescription?: unknown;
  longDescription?: unknown;
  chapter?: unknown;
  chapterDescription?: unknown;
  block?: unknown;
  blockDescription?: unknown;
  category?: unknown;
  isBillable?: unknown;
  isPrincipalDiagnosis?: unknown;
  sexSpecific?: unknown;
  manifestationCode?: unknown;
  validFrom?: unknown;
  validUntil?: unknown;
}

// backend model: ICD11Code  (table: clinical_icd11_codes)
export interface ICD11Code {
  uuid: string;
  code?: unknown;
  title?: unknown;
  definition?: unknown;
  chapter?: unknown;
  chapterTitle?: unknown;
  block?: unknown;
  isLeaf?: unknown;
  parentCode?: unknown;
  codingNote?: unknown;
  postCoordination?: unknown;
  validFrom?: unknown;
}

// backend model: SNOMEDCTCode  (table: clinical_snomed_ct_codes)
export interface SNOMEDCTCode {
  uuid: string;
  conceptId?: unknown;
  fullySpecifiedName?: unknown;
  preferredTerm?: unknown;
  definitionStatus?: unknown;
  moduleId?: unknown;
  effectiveTime?: unknown;
  semanticTag?: unknown;
}

// backend model: LOINCCode  (table: clinical_loinc_codes)
export interface LOINCCode {
  uuid: string;
  loincNum?: unknown;
  component?: unknown;
  property?: unknown;
  timing?: unknown;
  system?: unknown;
  scale?: unknown;
  method?: unknown;
  className?: unknown;
  versionLastChanged?: unknown;
  definitionDescription?: unknown;
  status?: unknown;
  consumerName?: unknown;
  exampleUnits?: unknown;
  relatedNames?: unknown;
  shortName?: unknown;
  longCommonName?: unknown;
}

// backend model: UCUMCode  (table: clinical_ucum_codes)
export interface UCUMCode {
  uuid: string;
  code?: unknown;
  name?: unknown;
  description?: unknown;
  property?: unknown;
  isMetric?: unknown;
  isSi?: unknown;
  conversionFactor?: unknown;
}

// backend model: ATCCode  (table: clinical_atc_codes)
export interface ATCCode {
  uuid: string;
  code?: unknown;
  name?: unknown;
  level?: unknown;
  parentCode?: unknown;
  dddValue?: unknown;
  dddUnit?: unknown;
  anatomicalGroup?: unknown;
  therapeuticGroup?: unknown;
}

// backend model: RxNormCode  (table: clinical_rxnorm_codes)
export interface RxNormCode {
  uuid: string;
  rxcui?: unknown;
  name?: unknown;
  synonym?: unknown;
  tty?: unknown;
  language?: unknown;
  suppress?: unknown;
  umlscui?: unknown;
  atomId?: unknown;
}

// backend model: CPTCode  (table: clinical_cpt_codes)
export interface CPTCode {
  uuid: string;
  code?: unknown;
  shortDescription?: unknown;
  mediumDescription?: unknown;
  longDescription?: unknown;
  category?: unknown;
  categoryDescription?: unknown;
  section?: unknown;
  isImaging?: unknown;
  isLab?: unknown;
  isSurgical?: unknown;
  effectiveDate?: unknown;
  status?: unknown;
}

// backend model: InsuranceProvider  (table: ins_providers)
export interface InsuranceProvider {
  uuid: string;
  labId?: unknown;
  insuranceType?: unknown;
  name?: unknown;
  nameAr?: unknown;
  code?: unknown;
  licenseNumber?: unknown;
  taxId?: unknown;
  isGovernment?: unknown;
  phone?: unknown;
  email?: unknown;
  website?: unknown;
  addressLine?: unknown;
  city?: unknown;
  governorate?: unknown;
  country?: unknown;
  contactPerson?: unknown;
  contactPhone?: unknown;
  coverageNotes?: unknown;
  extraMetadata?: unknown;
}

// backend model: InsurancePolicy  (table: ins_policies)
export interface InsurancePolicy {
  uuid: string;
  labId?: unknown;
  providerId?: unknown;
  policyNumber?: unknown;
  groupNumber?: unknown;
  status?: unknown;
  policyHolderId?: unknown;
  subscriberId?: unknown;
  subscriberName?: unknown;
  subscriberRelation?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  gracePeriodDays?: unknown;
  premiumAmount?: unknown;
  premiumCurrency?: unknown;
  premiumFrequency?: unknown;
  copayPercentage?: unknown;
  deductibleAmount?: unknown;
  maxOutOfPocket?: unknown;
  maxLifetimeBenefit?: unknown;
  termsText?: unknown;
  exclusionsText?: unknown;
  extraMetadata?: unknown;
  signedAt?: unknown;
  cancelledAt?: unknown;
  cancellationReason?: unknown;
}

// backend model: Coverage  (table: ins_coverages)
export interface Coverage {
  uuid: string;
  labId?: unknown;
  policyId?: unknown;
  patientId?: unknown;
  dependentId?: unknown;
  status?: unknown;
  subscriberRelation?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  verificationDate?: unknown;
  copayPercentage?: unknown;
  deductibleRemaining?: unknown;
  deductibleTotal?: unknown;
  maxOutOfPocketRemaining?: unknown;
  maxOutOfPocketTotal?: unknown;
  benefitRemaining?: unknown;
  benefitTotal?: unknown;
  networkStatus?: unknown;
  authorizationRequired?: unknown;
  referralRequired?: unknown;
  preExistingWaitPeriod?: unknown;
  extraMetadata?: unknown;
  notes?: unknown;
}

// backend model: BenefitPackage  (table: ins_benefit_packages)
export interface BenefitPackage {
  uuid: string;
  labId?: unknown;
  providerId?: unknown;
  policyId?: unknown;
  name?: unknown;
  nameAr?: unknown;
  code?: unknown;
  description?: unknown;
  serviceCategory?: unknown;
  isMandatory?: unknown;
  coveragePercentage?: unknown;
  copayPercentage?: unknown;
  deductibleApplies?: unknown;
  maxBenefitPerClaim?: unknown;
  maxBenefitPerYear?: unknown;
  maxBenefitLifetime?: unknown;
  maxVisitsPerYear?: unknown;
  ageMin?: unknown;
  ageMax?: unknown;
  genderRestriction?: unknown;
  requiresPreAuth?: unknown;
  requiresReferral?: unknown;
  clinicalRules?: unknown;
  exclusions?: unknown;
  extraMetadata?: unknown;
}

// backend model: FeeScheduleItem  (table: ins_fee_schedule)
export interface FeeScheduleItem {
  uuid: string;
  labId?: unknown;
  providerId?: unknown;
  serviceCode?: unknown;
  serviceName?: unknown;
  serviceNameAr?: unknown;
  serviceCategory?: unknown;
  loincCode?: unknown;
  cptCode?: unknown;
  icd10Code?: unknown;
  negotiatedPrice?: unknown;
  currency?: unknown;
  allowedAmount?: unknown;
  patientResponsibility?: unknown;
  copayAmount?: unknown;
  coinsurancePercentage?: unknown;
  deductibleApplies?: unknown;
  effectiveFrom?: unknown;
  effectiveUntil?: unknown;
  extraMetadata?: unknown;
}

// backend model: Authorization  (table: ins_authorizations)
export interface Authorization {
  uuid: string;
  labId?: unknown;
  coverageId?: unknown;
  patientId?: unknown;
  providerId?: unknown;
  requestingPractitionerId?: unknown;
  authorizationNumber?: unknown;
  status?: unknown;
  serviceCategory?: unknown;
  serviceCode?: unknown;
  serviceDescription?: unknown;
  quantityRequested?: unknown;
  quantityApproved?: unknown;
  estimatedCost?: unknown;
  approvedCost?: unknown;
  currency?: unknown;
  clinicalJustification?: unknown;
  diagnosisCode?: unknown;
  diagnosisDescription?: unknown;
  icd10Code?: unknown;
  requestedDate?: unknown;
  decisionDate?: unknown;
  effectiveFrom?: unknown;
  effectiveUntil?: unknown;
  decisionNotes?: unknown;
  reviewedBy?: unknown;
  attachments?: unknown;
  extraMetadata?: unknown;
}

// backend model: InsuranceClaim  (table: ins_claims)
export interface InsuranceClaim {
  uuid: string;
  labId?: unknown;
  coverageId?: unknown;
  patientId?: unknown;
  providerId?: unknown;
  orderId?: unknown;
  authorizationId?: unknown;
  referralId?: unknown;
  claimNumber?: unknown;
  claimType?: unknown;
  status?: unknown;
  serviceStartDate?: unknown;
  serviceEndDate?: unknown;
  submittedDate?: unknown;
  adjudicatedDate?: unknown;
  paidDate?: unknown;
  totalBilled?: unknown;
  totalAllowed?: unknown;
  totalPaid?: unknown;
  totalDeductible?: unknown;
  totalCopay?: unknown;
  totalPatientResponsibility?: unknown;
  currency?: unknown;
  diagnosisCodePrimary?: unknown;
  diagnosisCodeSecondary?: unknown;
  icd10Code?: unknown;
  adjudicationCode?: unknown;
  adjudicationNotes?: unknown;
  rejectionReason?: unknown;
  adjustmentReason?: unknown;
  idempotencyKey?: unknown;
  externalRef?: unknown;
  extraMetadata?: unknown;
  submittedAt?: unknown;
}

// backend model: InsuranceClaimItem  (table: ins_claim_items)
export interface InsuranceClaimItem {
  uuid: string;
  claimId?: unknown;
  serviceCode?: unknown;
  serviceName?: unknown;
  serviceCategory?: unknown;
  loincCode?: unknown;
  cptCode?: unknown;
  quantity?: unknown;
  unitPrice?: unknown;
  billedAmount?: unknown;
  allowedAmount?: unknown;
  paidAmount?: unknown;
  copayAmount?: unknown;
  deductibleAmount?: unknown;
  patientResponsibility?: unknown;
  currency?: unknown;
  diagnosisCode?: unknown;
  modifier?: unknown;
  revenueCode?: unknown;
  placeOfService?: unknown;
  adjudicationStatus?: unknown;
  adjudicationReason?: unknown;
  adjustmentCode?: unknown;
  adjustmentReason?: unknown;
  extraMetadata?: unknown;
}

// backend model: InsurancePayment  (table: ins_payments)
export interface InsurancePayment {
  uuid: string;
  labId?: unknown;
  claimId?: unknown;
  payerId?: unknown;
  paymentNumber?: unknown;
  status?: unknown;
  amount?: unknown;
  currency?: unknown;
  paymentMethod?: unknown;
  paymentDate?: unknown;
  referenceNumber?: unknown;
  adjustmentAmount?: unknown;
  adjustmentReason?: unknown;
  notes?: unknown;
  extraMetadata?: unknown;
  processedAt?: unknown;
}

// backend model: Settlement  (table: ins_settlements)
export interface Settlement {
  uuid: string;
  labId?: unknown;
  providerId?: unknown;
  periodStart?: unknown;
  periodEnd?: unknown;
  status?: unknown;
  settlementNumber?: unknown;
  totalClaims?: unknown;
  totalBilled?: unknown;
  totalAllowed?: unknown;
  totalPaid?: unknown;
  totalAdjustments?: unknown;
  totalDeductible?: unknown;
  totalCopay?: unknown;
  netAmount?: unknown;
  currency?: unknown;
  reconciledAt?: unknown;
  paidAt?: unknown;
  notes?: unknown;
  extraMetadata?: unknown;
}

// backend model: Appeal  (table: ins_appeals)
export interface Appeal {
  uuid: string;
  labId?: unknown;
  claimId?: unknown;
  submittedBy?: unknown;
  appealNumber?: unknown;
  status?: unknown;
  reason?: unknown;
  details?: unknown;
  requestedAmount?: unknown;
  supportingDocuments?: unknown;
  reviewedBy?: unknown;
  reviewNotes?: unknown;
  decision?: unknown;
  decisionAmount?: unknown;
  decisionDate?: unknown;
  escalationLevel?: unknown;
  filedDate?: unknown;
  resolvedDate?: unknown;
  extraMetadata?: unknown;
}

// backend model: FraudAlert  (table: ins_fraud_alerts)
export interface FraudAlert {
  uuid: string;
  labId?: unknown;
  claimId?: unknown;
  patientId?: unknown;
  providerId?: unknown;
  alertType?: unknown;
  severity?: unknown;
  status?: unknown;
  title?: unknown;
  description?: unknown;
  riskScore?: unknown;
  detectionMethod?: unknown;
  detectionRule?: unknown;
  evidence?: unknown;
  extraMetadata?: unknown;
  assignedTo?: unknown;
  investigationNotes?: unknown;
  resolvedAt?: unknown;
  resolution?: unknown;
}

// backend model: ProviderContract  (table: ins_provider_contracts)
export interface ProviderContract {
  uuid: string;
  labId?: unknown;
  insuranceProviderId?: unknown;
  facilityId?: unknown;
  facilityType?: unknown;
  contractNumber?: unknown;
  status?: unknown;
  startDate?: unknown;
  endDate?: unknown;
  terminationNoticeDays?: unknown;
  contractType?: unknown;
  networkType?: unknown;
  isExclusive?: unknown;
  feeScheduleId?: unknown;
  discountPercentage?: unknown;
  stopLossThreshold?: unknown;
  riskSharing?: unknown;
  termsText?: unknown;
  specialTerms?: unknown;
  extraMetadata?: unknown;
  signedAt?: unknown;
  terminatedAt?: unknown;
  terminationReason?: unknown;
}
