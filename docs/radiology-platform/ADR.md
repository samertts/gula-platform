# Architecture Decision Records — National Radiology Information System Platform (NRISP)

---

## ADR-001: DICOM Native Storage with FHIR Mapping Layer

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, Radiology Product Manager

### Context

Radiology images and metadata must be stored in a way that supports both PACS operations (DICOM-native) and EHR interoperability (FHIR). Two approaches exist: store natively in DICOM and map to FHIR for exchange, or store in FHIR format and convert to DICOM for modality communication.

### Decision

Store images and metadata **natively in DICOM** format and provide a **FHIR mapping layer** on top for EHR and interoperability use cases.

### Rationale

1. **Modality compatibility** — Medical imaging modalities (CT, MRI, X-ray) communicate exclusively via DICOM protocols. Native DICOM storage eliminates conversion latency and data loss risk when communicating with modalities.
2. **DICOM richness** — DICOM contains modality-specific metadata (acquisition parameters, reconstruction kernels, protocol names) that do not have FHIR equivalents. Native storage preserves this data.
3. **PACS operations** — Query/retrieve, storage commitment, and modality worklist are DICOM-native operations. A FHIR-native store would require DICOM-to-FHIR conversion for every modality interaction.
4. **FHIR for exchange** — EHR systems consume FHIR `ImagingStudy` and `DiagnosticReport` resources. The mapping layer (DICOM → FHIR) is a defined transformation that runs on-demand for EHR consumers.
5. **Existing infrastructure** — The GULA platform has invested in DICOM connector libraries for device integration (ADR-007). Native DICOM storage leverages this investment.

### Consequences

- **Positive**: Modality-native, no conversion latency, preserves rich metadata, leverages existing DICOM libraries
- **Negative**: Dual storage model (DICOM for modalities, FHIR for EHR); FHIR mapping layer must be maintained as both standards evolve; additional storage space for redundant metadata

---

## ADR-002: Three-Tier Storage (Hot/Warm/Cold Archive)

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, Operations Lead

### Context

DICOM studies consume significant storage (a single CT study is 100-500 MB, MRI 200-1000 MB). A hospital performing 100+ exams/day generates 10-100 GB of imaging data daily. Single-tier storage is cost-prohibitive.

### Decision

Implement a **three-tier storage architecture** (hot/warm/cold) with automatic data migration based on configurable archive rules.

### Rationale

1. **Cost optimisation** — Hot storage (NVMe SSD, <$0.20/GB) for active studies, warm storage (S3 Standard, <$0.023/GB) for recent studies, cold storage (S3 Glacier, <$0.004/GB) for archival studies. Estimated 70% cost reduction vs all-hot storage.
2. **Performance by access pattern** — Active studies (in reporting) need sub-second retrieval. Archived studies (medico-legal, research) can tolerate 5-15 minute retrieval times.
3. **Regulatory retention** — Iraqi MOH requires radiology image retention for 10+ years. Cold storage makes long-term retention economically viable.
4. **Auto-archiving** — Configurable rules (age-based, status-based, modality-based) automate data migration without manual intervention.
5. **Scalability** — Each tier can scale independently. Hot storage scales with active patient volume; cold storage scales with archive duration.

### Consequences

- **Positive**: Significant cost savings, appropriate performance per tier, long-term retention feasible, automated migration
- **Negative**: Retrieval latency for cold data; archive rule misconfiguration can cause premature cold archiving; user education needed on retrieval time expectations; cold storage costs accumulate over decades

---

## ADR-003: AI as Abstraction Layer (Not Integrated AI)

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, AI Product Manager

### Context

AI imaging models are evolving rapidly with new vendors, improved versions, and novel use cases appearing frequently. Integrating AI tightly (vendor-specific connectors, hardwired model pipelines) would create maintenance burden and lock the platform to specific vendors.

### Decision

Implement AI as an **abstraction layer** with a model registry, standardised input/output contracts, and vendor-independent inference pipeline rather than integrating specific AI vendors directly.

### Rationale

1. **Vendor independence** — The model registry abstracts away vendor-specific APIs. Models can be swapped, upgraded, or replaced without code changes.
2. **Future-proofing** — AI models improve rapidly. An abstraction layer allows new models to be registered without modifying the inference pipeline.
3. **Multi-model support** — Different clinical use cases benefit from different models (triage, detection, quantification, quality). The abstraction layer supports multiple models for different purposes.
4. **Local inference support** — The abstraction layer supports both cloud API models and locally deployed models (ONNX, TensorRT), critical for facilities with limited internet connectivity.
5. **Performance monitoring** — The registry tracks model performance metrics, enabling data-driven decisions about model selection and retirement.

### Consequences

- **Positive**: Vendor independence, future-proof, multi-model support, local inference capability, performance monitoring
- **Negative**: Abstraction layer adds development overhead; standardised output contracts must accommodate diverse model outputs; model-specific features may not fit the abstraction

---

## ADR-004: Modality Worklist via DICOM Standard

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Radiology Product Manager

### Context

Radiology modalities need to retrieve scheduled exams. The MWL service could be implemented as a proprietary web API (REST/JSON) or using the standard DICOM MWL SCP service (C-FIND based).

### Decision

Implement the Modality Worklist **using the standard DICOM MWL SCP** protocol (C-FIND) rather than a proprietary REST API.

### Rationale

1. **Modality compatibility** — All DICOM-compliant modalities natively support C-FIND MWL queries. No modality-side software changes or adapters needed.
2. **Standard compliance** — DICOM MWL is a well-defined, stable standard (PS3.4). Proprietary APIs would need per-modality adapters.
3. **Zero-configuration** — Modalities are configured with NRISP's AE title and port, exactly as they would be for any other PACS MWL server.
4. **Workflow reliability** — The MWL C-FIND protocol includes error handling, timeout management, and retry logic that modalities already implement. A proprietary API would need to reimplement these.
5. **Multi-vendor support** — Siemens, GE, Philips, Canon, and all other modality vendors support DICOM MWL. A single implementation works for all.

### Consequences

- **Positive**: Universal modality compatibility, standard compliance, zero-configuration, reliable, multi-vendor
- **Negative**: DICOM MWL has limitations (limited query keys, complex string matching); worklist updates may not propagate immediately to modalities (modalities poll on their own schedule); specialised radiography modalities may have MWL implementation variations

---

## ADR-005: Lossless Compression for Primary Storage

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Clinical Lead, Platform Architect

### Context

DICOM images can be stored with lossless or lossy compression. Lossless preserves full diagnostic quality but requires more storage. Lossy reduces storage but may degrade diagnostic quality for certain modalities.

### Decision

Use **lossless compression** (JPEG Lossless, JPEG 2000 Lossless, or RLE) for all primary DICOM storage. Lossy compression is used only for thumbnails, viewer previews, and cold-tier archival with clinical approval.

### Rationale

1. **Diagnostic integrity** — Lossless compression preserves every bit of the original image. Lossy compression introduces irreversible artifacts that could affect diagnostic accuracy, particularly for subtle findings (microcalcifications, ground-glass opacities, early ischaemic changes).
2. **Medico-legal requirement** — Original image data must be preserved for medico-legal purposes. Lossy compression creates a derivative image, not the original.
3. **Clinical confidence** — Radiologists must have confidence that the image they are reading is diagnostically identical to the original acquisition. Lossless compression provides this guarantee.
4. **Storage cost vs clinical risk** — The storage cost savings from lossy compression (typically 50-70%) do not justify the clinical risk of missed findings. Three-tier architecture already reduces storage cost sufficiently.
5. **Standard compliance** — DICOM supports lossless compression natively in the standard. Modalities can transfer images in lossless format without conversion.

### Consequences

- **Positive**: Diagnostic integrity, medico-legal compliance, clinical confidence, DICOM standard compliant
- **Negative**: Higher storage requirements (lossy could save 50-70%); longer network transfer times for studies reviewed remotely; cold-tier archival may use lossy with explicit clinical approval for very large studies
