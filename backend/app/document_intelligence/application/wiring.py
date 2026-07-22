from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import sessionmaker

from ..domain.enums import OcrEngine
from ..domain.repository import (
    ClassificationResultRepository,
    DocumentRepository,
    EntityRepository,
    FieldRepository,
    OcrResultRepository,
    PipelineResultRepository,
    StorageRepository,
    TableRepository,
)
from ..infrastructure.repository import (
    LocalStorageRepository,
    SqlClassificationResultRepository,
    SqlDocumentRepository,
    SqlEntityRepository,
    SqlFieldRepository,
    SqlOcrResultRepository,
    SqlPipelineResultRepository,
    SqlTableRepository,
)
from ..providers import (
    EasyOcrProvider,
    OcrProviderManager,
    PaddleOcrProvider,
    TesseractProvider,
)
from .interfaces import (
    AuditService,
    DocumentClassifier,
    DocumentParser,
    EncryptionService,
    EntityExtractor,
    FhirMapper,
    ImagePreprocessor,
    KnowledgeExtractor,
    LayoutDetector,
    MedicalParser,
    PipelineEventPublisher,
    ProviderBenchmark,
    RemediationService,
    SearchIndexer,
)
from .service import (
    DefaultClassifierService,
    DefaultEntityExtractionService,
    DefaultFhirMappingService,
    DefaultIngestionService,
    DefaultKnowledgePipelineService,
    DefaultOcrPipelineService,
    DefaultSearchService,
    DocumentIntelligenceOrchestrator,
)

logger = logging.getLogger("gula.document_intelligence.wiring")

_orchestrator: DocumentIntelligenceOrchestrator | None = None
_provider_manager: OcrProviderManager | None = None
_document_repo: DocumentRepository | None = None


class DefaultAuditService(AuditService):
    async def log_event(self, event_type: str, document_id: Any, details: dict) -> None:
        logger.info("AUDIT: %s [%s] %s", event_type, document_id, details)

    async def get_document_history(self, document_id: Any) -> list[dict]:
        return []


class DefaultEncryptionService(EncryptionService):
    async def encrypt(self, data: bytes, key_id: str = "default") -> bytes:
        return data

    async def decrypt(self, data: bytes, key_id: str = "default") -> bytes:
        return data

    async def hash_document(self, data: bytes) -> str:
        import hashlib
        return hashlib.sha256(data).hexdigest()

    async def verify_hash(self, data: bytes, expected_hash: str) -> bool:
        actual = await self.hash_document(data)
        return actual == expected_hash

    async def generate_watermark(self, document_id: Any, tenant_id: Any) -> bytes:
        return b""

    async def verify_digital_signature(
        self, data: bytes, signature: bytes, certificate: bytes | None = None
    ) -> bool:
        return False


class DefaultPipelineEventPublisher(PipelineEventPublisher):
    async def publish(self, event: Any) -> None:
        logger.debug("Event published: %s", type(event).__name__)

    async def subscribe(self, event_type: type, handler: Any) -> None:
        pass


class DefaultImagePreprocessor(ImagePreprocessor):
    def __init__(self) -> None:
        self._cv2 = None
        self._numpy = None

    async def _lazy_init(self) -> None:
        if self._cv2 is None:
            try:
                import cv2
                self._cv2 = cv2
            except ImportError:
                pass
        if self._numpy is None:
            try:
                import numpy
                self._numpy = numpy
            except ImportError:
                pass

    async def _to_array(self, image_data: bytes):
        await self._lazy_init()
        if self._cv2 and self._numpy:
            arr = self._numpy.frombuffer(image_data, self._numpy.uint8)
            return self._cv2.imdecode(arr, self._cv2.IMREAD_COLOR)
        return None

    async def deskew(self, image_data: bytes) -> bytes:
        img = await self._to_array(image_data)
        if img is None:
            return image_data
        gray = self._cv2.cvtColor(img, self._cv2.COLOR_BGR2GRAY)
        coords = self._numpy.column_stack(self._numpy.where(gray > 0))
        if len(coords) == 0:
            return image_data
        angle = self._cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        h, w = img.shape[:2]
        matrix = self._cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        rotated = self._cv2.warpAffine(
            img, matrix, (w, h),
            flags=self._cv2.INTER_CUBIC,
            borderMode=self._cv2.BORDER_REPLICATE,
        )
        _, encoded = self._cv2.imencode(".png", rotated)
        return encoded.tobytes()

    async def denoise(self, image_data: bytes) -> bytes:
        img = await self._to_array(image_data)
        if img is None:
            return image_data
        denoised = self._cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        _, encoded = self._cv2.imencode(".png", denoised)
        return encoded.tobytes()

    async def correct_rotation(self, image_data: bytes) -> bytes:
        return image_data

    async def enhance_quality(self, image_data: bytes) -> bytes:
        img = await self._to_array(image_data)
        if img is None:
            return image_data
        enhanced = self._cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)
        _, encoded = self._cv2.imencode(".png", enhanced)
        return encoded.tobytes()

    async def crop(self, image_data: bytes, box: tuple[int, int, int, int]) -> bytes:
        img = await self._to_array(image_data)
        if img is None:
            return image_data
        x, y, w, h = box
        cropped = img[y : y + h, x : x + w]
        _, encoded = self._cv2.imencode(".png", cropped)
        return encoded.tobytes()

    async def to_grayscale(self, image_data: bytes) -> bytes:
        await self._lazy_init()
        if self._cv2:
            arr = self._numpy.frombuffer(image_data, self._numpy.uint8)
            img = self._cv2.imdecode(arr, self._cv2.IMREAD_GRAYSCALE)
            _, encoded = self._cv2.imencode(".png", img)
            return encoded.tobytes()
        return image_data

    async def resize(self, image_data: bytes, max_width: int = 2048) -> bytes:
        img = await self._to_array(image_data)
        if img is None:
            return image_data
        h, w = img.shape[:2]
        if w <= max_width:
            return image_data
        ratio = max_width / w
        new_size = (max_width, int(h * ratio))
        resized = self._cv2.resize(img, new_size, interpolation=self._cv2.INTER_AREA)
        _, encoded = self._cv2.imencode(".png", resized)
        return encoded.tobytes()

    async def binarize(self, image_data: bytes) -> bytes:
        await self._lazy_init()
        if self._cv2:
            arr = self._numpy.frombuffer(image_data, self._numpy.uint8)
            img = self._cv2.imdecode(arr, self._cv2.IMREAD_GRAYSCALE)
            _, binary = self._cv2.threshold(img, 0, 255, self._cv2.THRESH_BINARY + self._cv2.THRESH_OTSU)
            _, encoded = self._cv2.imencode(".png", binary)
            return encoded.tobytes()
        return image_data

    async def remove_borders(self, image_data: bytes) -> bytes:
        img = await self._to_array(image_data)
        if img is None:
            return image_data
        gray = self._cv2.cvtColor(img, self._cv2.COLOR_BGR2GRAY)
        _, thresh = self._cv2.threshold(gray, 1, 255, self._cv2.THRESH_BINARY)
        coords = self._numpy.column_stack(self._numpy.where(thresh > 0))
        if len(coords) == 0:
            return image_data
        x, y, w, h = self._cv2.boundingRect(coords)
        cropped = img[y : y + h, x : x + w]
        _, encoded = self._cv2.imencode(".png", cropped)
        return encoded.tobytes()

    async def auto_preprocess(self, image_data: bytes) -> bytes:
        result = await self.deskew(image_data)
        result = await self.denoise(result)
        result = await self.remove_borders(result)
        return await self.resize(result)


class DefaultDocumentParser(DocumentParser):
    def __init__(self) -> None:
        self._pdf2image = None
        self._pymupdf = None
        self._docx = None
        self._PIL = None

    async def _lazy_init_pdf(self) -> None:
        if self._pdf2image is None:
            try:
                from pdf2image import convert_from_bytes
                self._pdf2image = convert_from_bytes
            except ImportError:
                pass
        if self._pymupdf is None:
            try:
                import fitz
                self._pymupdf = fitz
            except ImportError:
                pass

    async def _lazy_init_docx(self) -> None:
        if self._docx is None:
            try:
                from docx import Document
                self._docx = Document
            except ImportError:
                pass

    async def _to_pil(self) -> Any:
        if self._PIL is None:
            from PIL import Image
            self._PIL = Image
        return self._PIL

    async def parse_pdf(self, data: bytes) -> list[bytes]:
        await self._lazy_init_pdf()
        images: list[bytes] = []

        if self._pymupdf:
            doc = self._pymupdf.open(stream=data, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
            doc.close()
            return images

        if self._pdf2image:
            pil_images = self._pdf2image(data, dpi=300)
            for img in pil_images:
                import io
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                images.append(buf.getvalue())
            return images

        logger.warning("No PDF parser available (install pdf2image or PyMuPDF)")
        return images

    async def parse_image(self, data: bytes) -> bytes:
        return data

    async def parse_docx(self, data: bytes) -> str:
        await self._lazy_init_docx()
        if self._docx:
            import io
            doc = self._docx(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
        return ""

    async def parse_tiff(self, data: bytes) -> list[bytes]:
        PIL = await self._to_pil()
        import io

        tiff = PIL.open(io.BytesIO(data))
        images: list[bytes] = []
        for page in range(tiff.n_frames):
            tiff.seek(page)
            buf = io.BytesIO()
            tiff.save(buf, format="PNG")
            images.append(buf.getvalue())
        return images

    async def get_page_count(self, data: bytes, mime_type: str) -> int:
        if mime_type == "application/pdf":
            await self._lazy_init_pdf()
            if self._pymupdf:
                doc = self._pymupdf.open(stream=data, filetype="pdf")
                count = len(doc)
                doc.close()
                return count
            if self._pdf2image:
                return len(await self.parse_pdf(data))
            return 0
        if mime_type == "image/tiff":
            return len(await self.parse_tiff(data))
        if mime_type.startswith("image/"):
            return 1
        return 0

    async def extract_metadata(self, data: bytes, mime_type: str) -> dict[str, Any]:
        return {}

    async def _read_storage(self, document: Any) -> bytes:
        return b""


class DefaultDocumentClassifier(DocumentClassifier):
    def __init__(self) -> None:
        self._custom_classes: dict[str, list[str]] = {}
        self._patterns: dict[str, list[str]] = {
            "laboratory_report": [
                "hemoglobin", "glucose", "wbc", "rbc", "platelet", "hba1c",
                "cholesterol", "creatinine", "bun", "alt", "ast", "lab result",
                "نتيجة مختبر", "تحليل", "فحص", "مخبري",
            ],
            "radiology_report": [
                "x-ray", "xray", "mri", "ct scan", "ultrasound", "radiology",
                "radiologist", "imaging", "chest xray", "echo",
                "أشعة", "رنين", "مقطعي", "تصوير", "سونار",
            ],
            "prescription": [
                "take", "tablet", "capsule", "dose", "mg", "prescription",
                "doctor", "pharmacy", "medication", "rx",
                "روشتة", "وصفة", "دواء", "جرعة", "علاج",
            ],
            "national_id": [
                "national id", "civil id", "identity card", "رقم وطني",
                "هوية", "بطاقة", "جنسية", "رقم مدني",
            ],
            "medical_certificate": [
                "medical certificate", "fit to work", "sick leave",
                "شهادة طبية", "تقرير طبي", "إجازة مرضية",
            ],
            "referral": [
                "referral", "refer", "consultation", "تحويل", "إحالة",
            ],
        }

    async def classify(
        self, text: str, pages: list[Any] | None = None
    ) -> Any:
        from ..domain.entities import ClassificationResult
        from ..domain.enums import ClassificationConfidence, DocumentCategory

        text_lower = text.lower()
        scores: dict[DocumentCategory, float] = {}

        for category_str, keywords in self._patterns.items():
            score = 0.0
            for kw in keywords:
                if kw.lower() in text_lower:
                    score += 1.0
            if score > 0:
                category = DocumentCategory(category_str)
                scores[category] = score

        for name, examples in self._custom_classes.items():
            score = 0.0
            for ex in examples:
                if ex.lower() in text_lower:
                    score += 1.0
            if score > 0:
                try:
                    category = DocumentCategory(name)
                    scores[category] = scores.get(category, 0) + score
                except ValueError:
                    pass

        if not scores:
            return ClassificationResult(
                category=DocumentCategory.unknown,
                confidence=ClassificationConfidence.very_low,
                confidence_score=0.0,
                method="keyword_match",
            )

        total = sum(scores.values())
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category] / max(len(self._patterns.get(str(best_category), [])) * 2, total)

        alt = [(cat, score / max(total, 1)) for cat, score in scores.items() if cat != best_category]
        alt.sort(key=lambda x: x[1], reverse=True)
        alt = alt[:3]

        if best_score >= 0.8:
            conf = ClassificationConfidence.very_high
        elif best_score >= 0.6:
            conf = ClassificationConfidence.high
        elif best_score >= 0.4:
            conf = ClassificationConfidence.medium
        elif best_score >= 0.2:
            conf = ClassificationConfidence.low
        else:
            conf = ClassificationConfidence.very_low

        return ClassificationResult(
            category=best_category,
            confidence=conf,
            confidence_score=best_score,
            alternatives=[(c, s) for c, s in alt],
            method="keyword_match",
            features=scores,
        )

    async def classify_batch(
        self, documents: list[tuple[str, list | None]]
    ) -> list[Any]:
        return [await self.classify(text) for text, _ in documents]

    async def get_custom_classes(self) -> list[str]:
        return list(self._custom_classes.keys())

    async def add_custom_class(self, name: str, examples: list[str]) -> None:
        self._custom_classes[name] = examples


class DefaultEntityExtractor(EntityExtractor):
    def __init__(self) -> None:
        self._patterns: dict[str, str] = {
            "health_id": r"(HN-\d{4,10}|HN\d{4,10}|ID:\s*\d{6,12})",
            "national_id": r"\b\d{12,16}\b",
            "phone_number": r"(0(7[3-9]\d{7}|1\d{7}))",
            "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "date": r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
            "loinc_code": r"\b\d{4,5}-\d\b",
            "snomed_code": r"\b\d{6,10}\b(?!-\d)",
            "icd_code": r"[A-Z]\d{2}(\.\d{1,2})?",
        }

    async def extract(
        self, text: str, category: Any | None = None
    ) -> tuple[list, list, list]:
        import re

        from ..domain.entities import ExtractedEntity, ExtractedField, ExtractedTable
        from ..domain.enums import EntityType

        entities: list[ExtractedEntity] = []
        fields: list[ExtractedField] = []
        tables: list[ExtractedTable] = []

        seen = set()
        for field_name, pattern in self._patterns.items():
            for match in re.finditer(pattern, text):
                value = match.group(0)
                if value not in seen:
                    seen.add(value)
                    try:
                        entity_type = EntityType(field_name)
                    except ValueError:
                        entity_type = EntityType.custom
                    entities.append(
                        ExtractedEntity(
                            entity_type=entity_type,
                            value=value,
                            confidence=0.9,
                            source_text=text[
                                max(0, match.start() - 30) : match.end() + 30
                            ],
                        )
                    )

        lab_test_patterns = [
            (r"(Hemoglobin|Hb)\s*:?\s*(\d+\.?\d*)", "Hemoglobin", "g/dL"),
            (r"(Glucose|FBS|RBG)\s*:?\s*(\d+\.?\d*)", "Glucose", "mg/dL"),
            (r"(WBC|White Blood Cells)\s*:?\s*(\d+\.?\d*)", "WBC", "x10^3/uL"),
            (r"(RBC|Red Blood Cells)\s*:?\s*(\d+\.?\d*)", "RBC", "x10^6/uL"),
            (r"(Platelet|PLT)\s*:?\s*(\d+\.?\d*)", "Platelet", "x10^3/uL"),
            (r"(HbA1c|A1C)\s*:?\s*(\d+\.?\d*)", "HbA1c", "%"),
            (r"(Creatinine|Cr)\s*:?\s*(\d+\.?\d*)", "Creatinine", "mg/dL"),
            (r"(Cholesterol|Total Cholesterol)\s*:?\s*(\d+\.?\d*)", "Cholesterol", "mg/dL"),
        ]
        for pattern, name, _unit in lab_test_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                fields.append(
                    ExtractedField(
                        name=name,
                        value=match.group(2),
                        confidence=0.85,
                        normalized_value=match.group(2),
                        original_text=match.group(0),
                    )
                )

        return entities, fields, tables

    async def extract_from_pages(
        self, pages: list, category: Any | None = None
    ) -> tuple[list, list, list]:
        full_text = "\n\n".join(p.text for p in pages if hasattr(p, "text") and p.text)
        return await self.extract(full_text, category)

    async def extract_entities_of_type(
        self, text: str, entity_types: list
    ) -> list:
        all_entities, _, _ = await self.extract(text)
        return [e for e in all_entities if e.entity_type in entity_types]


class DefaultFhirMapper(FhirMapper):
    async def to_document_reference(self, document, ocr_result) -> dict:
        return {
            "resourceType": "DocumentReference",
            "id": str(document.id),
            "status": "current",
            "docStatus": "final",
            "type": {"text": document.mime_type},
            "subject": {"reference": f"Patient/{document.patient_id}"} if document.patient_id else None,
            "content": [{
                "attachment": {
                    "contentType": document.mime_type,
                    "size": document.size_bytes,
                    "title": document.filename,
                    "creation": document.created_at.isoformat(),
                }
            }],
            "context": {
                "period": {"start": document.created_at.isoformat()},
            },
        }

    async def to_patient(self, entities) -> dict | None:
        names = [e.value for e in entities if e.entity_type.name == "patient_name"]
        ids = [e.value for e in entities if e.entity_type.name == "health_id"]
        if not names and not ids:
            return None
        return {
            "resourceType": "Patient",
            "id": ids[0] if ids else None,
            "name": [{"text": names[0]}] if names else [],
            "identifier": [{"value": i, "system": "urn:gula:health-id"} for i in ids],
        }

    async def to_practitioner(self, entities) -> dict | None:
        names = [e.value for e in entities if e.entity_type.name == "doctor_name"]
        if not names:
            return None
        return {
            "resourceType": "Practitioner",
            "name": [{"text": names[0]}],
        }

    async def to_organization(self, entities) -> dict | None:
        labs = [e.value for e in entities if e.entity_type.name == "laboratory_name"]
        hospitals = [e.value for e in entities if e.entity_type.name == "hospital_name"]
        name = labs[0] if labs else (hospitals[0] if hospitals else None)
        if not name:
            return None
        return {
            "resourceType": "Organization",
            "name": name,
        }

    async def to_observation(self, entities, fields) -> list[dict]:
        observations = []
        for field in fields:
            obs = {
                "resourceType": "Observation",
                "status": "final",
                "code": {"text": field.name},
                "valueQuantity": {
                    "value": float(field.normalized_value) if field.normalized_value.replace(".", "", 1).isdigit() else 0,
                    "unit": field.metadata.get("unit", ""),
                } if field.normalized_value else None,
            }
            loinc = next((e.loinc_code for e in entities if e.field_name == field.name and e.loinc_code), None)
            if loinc:
                obs["code"]["coding"] = [{"system": "http://loinc.org", "code": loinc}]
            observations.append(obs)
        return observations

    async def to_diagnostic_report(self, entities, fields) -> dict | None:
        obs = await self.to_observation(entities, fields)
        if not obs:
            return None
        return {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "code": {"text": "Laboratory Report"},
            "result": [{"reference": f"Observation/{o.get('id', '')}"} for o in obs],
        }

    async def to_medication_request(self, entities) -> dict | None:
        meds = [e.value for e in entities if e.entity_type.name == "medication_name"]
        if not meds:
            return None
        return {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": meds[0]},
        }

    async def to_encounter(self, entities) -> dict | None:
        return None

    async def to_condition(self, entities) -> list[dict]:
        conditions = []
        for e in entities:
            if e.entity_type.name == "diagnosis":
                condition = {
                    "resourceType": "Condition",
                    "code": {"text": e.value},
                }
                if e.icd_code:
                    condition["code"]["coding"] = [{"system": "http://hl7.org/fhir/sid/icd-10", "code": e.icd_code}]
                conditions.append(condition)
        return conditions

    async def to_procedure(self, entities) -> list[dict]:
        return []

    async def to_specimen(self, entities) -> dict | None:
        specimens = [e.value for e in entities if e.entity_type.name == "specimen_type"]
        if not specimens:
            return None
        return {
            "resourceType": "Specimen",
            "type": {"text": specimens[0]},
            "status": "available",
        }

    async def map_all(self, entities, fields, document=None, ocr_result=None) -> dict:
        resources = {}
        if document:
            resources["DocumentReference"] = await self.to_document_reference(document, ocr_result)
        patient = await self.to_patient(entities)
        if patient:
            resources["Patient"] = patient
        practitioner = await self.to_practitioner(entities)
        if practitioner:
            resources["Practitioner"] = practitioner
        org = await self.to_organization(entities)
        if org:
            resources["Organization"] = org
        obs = await self.to_observation(entities, fields)
        if obs:
            resources["Observations"] = obs
        diag = await self.to_diagnostic_report(entities, fields)
        if diag:
            resources["DiagnosticReport"] = diag
        med = await self.to_medication_request(entities)
        if med:
            resources["MedicationRequest"] = med
        conditions = await self.to_condition(entities)
        if conditions:
            resources["Conditions"] = conditions
        specimen = await self.to_specimen(entities)
        if specimen:
            resources["Specimen"] = specimen
        return resources


class DefaultKnowledgeExtractor(KnowledgeExtractor):
    async def extract_concepts(self, text: str, entities) -> list[dict]:
        concepts = []
        for entity in entities:
            concepts.append({
                "name": entity.value,
                "type": str(entity.entity_type),
                "confidence": entity.confidence,
            })
        return concepts

    async def build_knowledge_graph(self, concepts: list[dict]) -> dict:
        return {
            "nodes": [{"id": i, "name": c["name"], "type": c["type"]} for i, c in enumerate(concepts)],
            "edges": [],
        }

    async def generate_embeddings(self, text: str) -> list[float]:
        import hashlib
        digest = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in digest[:64]]

    async def build_semantic_index(self, text: str, document_id: Any) -> dict:
        return {"document_id": str(document_id), "text_length": len(text)}

    async def extract_clinical_timeline(self, entities) -> list[dict]:
        timeline = []
        for entity in entities:
            if entity.entity_type.name in ("date", "diagnosis", "test_result"):
                timeline.append({
                    "type": str(entity.entity_type),
                    "value": entity.value,
                    "date": entity.metadata.get("date", ""),
                })
        return timeline


class DefaultSearchIndexer(SearchIndexer):
    def __init__(self) -> None:
        self._index: dict[str, dict] = {}
        self._text_index: list[dict] = []

    async def index_document(self, document, text: str, entities) -> str:
        doc_id = str(document.id)
        self._index[doc_id] = {
            "document_id": doc_id,
            "filename": document.filename,
            "text": text[:10000],
            "mime_type": document.mime_type,
            "page_count": document.page_count,
            "created_at": document.created_at.isoformat(),
            "entities": [
                {"type": str(e.entity_type), "value": e.value, "confidence": e.confidence}
                for e in entities[:50]
            ],
            "metadata": document.metadata,
            "tags": document.tags,
        }
        self._text_index.append({
            "id": doc_id,
            "text": text,
            "filename": document.filename,
        })
        return doc_id

    async def search(self, query: str, filters: dict | None = None) -> list[dict]:
        query_lower = query.lower()
        results = []
        for _doc_id, entry in self._index.items():
            if query_lower in entry["text"].lower() or query_lower in entry["filename"].lower():
                if filters:
                    if "category" in filters and entry.get("category") != filters["category"]:
                        continue
                    if "patient_id" in filters:
                        meta_patient = entry.get("metadata", {}).get("patient_id", "")
                        if meta_patient != filters["patient_id"]:
                            continue
                results.append(entry)

        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        limit = (filters or {}).get("limit", 50)
        return results[:limit]

    async def hybrid_search(self, query: str, query_vector: list | None = None, limit: int = 50) -> list[dict]:
        return await self.search(query, {"limit": limit})

    async def semantic_search(self, query: str, limit: int = 50) -> list[dict]:
        return await self.search(query, {"limit": limit})

    async def delete_index(self, document_id: Any) -> None:
        self._index.pop(str(document_id), None)
        self._text_index = [e for e in self._text_index if e["id"] != str(document_id)]

    async def rebuild_index(self) -> None:
        self._index.clear()
        self._text_index.clear()


class DefaultMedicalParser(MedicalParser):
    async def parse_lab_report(self, text: str) -> dict[str, Any]:
        import re
        result: dict[str, Any] = {"tests": []}
        test_patterns = [
            (r"(Hemoglobin|Hb)\s*:?\s*(\d+\.?\d*)\s*(g/dL|g/L)?", "hematology"),
            (r"(WBC|White Blood)\s*:?\s*(\d+\.?\d*)", "hematology"),
            (r"(Platelet|PLT)\s*:?\s*(\d+\.?\d*)", "hematology"),
            (r"(Glucose|FBS|RBG)\s*:?\s*(\d+\.?\d*)", "chemistry"),
            (r"(Creatinine|Cr)\s*:?\s*(\d+\.?\d*)", "chemistry"),
            (r"(BUN|Urea)\s*:?\s*(\d+\.?\d*)", "chemistry"),
        ]
        for pattern, category in test_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                result["tests"].append({
                    "name": match.group(1),
                    "value": match.group(2),
                    "unit": match.group(3) if match.lastindex and match.lastindex >= 3 else "",
                    "category": category,
                })
        return result

    async def parse_radiology_report(self, text: str) -> dict[str, Any]:
        return {"impression": "", "findings": text[:500]}

    async def parse_prescription(self, text: str) -> dict[str, Any]:
        import re
        medications = []
        med_pattern = re.findall(r"([\u0600-\u06FF\w\s]+?)\s*(\d+)\s*(mg|g|ml|mcg|tablet|capsule)?", text)
        for name, dose, unit in med_pattern:
            medications.append({"name": name.strip(), "dose": dose, "unit": unit})
        return {"medications": medications}

    async def parse_referral(self, text: str) -> dict[str, Any]:
        return {"referral_text": text[:500]}

    async def normalize_medication(self, medication_name: str) -> dict[str, Any]:
        return {"original": medication_name, "normalized": medication_name.lower()}

    async def normalize_test_name(self, test_name: str) -> dict[str, Any]:
        return {"original": test_name, "normalized": test_name.lower()}

    async def map_to_loinc(self, test_name: str) -> str:
        mapping = {
            "hemoglobin": "718-7",
            "glucose": "2345-7",
            "wbc": "26464-8",
            "creatinine": "2160-0",
            "hba1c": "4548-4",
            "cholesterol": "2093-3",
        }
        return mapping.get(test_name.lower(), "")

    async def map_to_snomed(self, concept: str) -> str:
        return ""

    async def map_to_icd(self, diagnosis: str) -> str:
        return ""


class DefaultLayoutDetector(LayoutDetector):
    async def detect_layout(self, image_data: bytes) -> dict:
        return {}

    async def detect_tables(self, image_data: bytes) -> list[dict]:
        return []

    async def detect_forms(self, image_data: bytes) -> list[dict]:
        return []

    async def detect_handwriting(self, image_data: bytes) -> list[dict]:
        return []

    async def detect_qr_codes(self, image_data: bytes) -> list[dict]:
        return []

    async def detect_barcodes(self, image_data: bytes) -> list[dict]:
        return []

    async def detect_signatures(self, image_data: bytes) -> list[dict]:
        return []


class DefaultVersioningService:
    pass


class DefaultDocumentLifecycleManager:
    pass


class DefaultProviderBenchmark(ProviderBenchmark):
    def __init__(self) -> None:
        self._history: dict[str, list[dict]] = {}

    async def benchmark_provider(self, provider) -> dict:
        return await provider.get_benchmark_score()

    async def benchmark_all_providers(self) -> dict:
        return {}

    async def get_best_provider(self, language: Any) -> Any:
        return None

    async def record_result(self, engine: Any, metrics: dict) -> None:
        key = str(engine)
        if key not in self._history:
            self._history[key] = []
        self._history[key].append(metrics)


class DefaultRemediationService(RemediationService):
    def __init__(
        self,
        doc_repo: DocumentRepository,
        orchestrator: DocumentIntelligenceOrchestrator | None = None,
    ) -> None:
        self._doc_repo = doc_repo
        self._orchestrator = orchestrator

    async def detect_and_fix_ocr_failures(self) -> list[dict]:
        pending = await self._doc_repo.get_pending_processing(limit=50)
        fixed = []
        for doc in pending:
            if doc.status.name == "ocr_failed" and doc.retry_count < 3:
                fixed.append({"document_id": str(doc.id), "action": "retry_ocr"})
        return fixed

    async def detect_and_fix_classification_failures(self) -> list[dict]:
        return []

    async def detect_and_fix_extraction_failures(self) -> list[dict]:
        return []

    async def detect_and_fix_fhir_mapping_failures(self) -> list[dict]:
        return []

    async def detect_and_fix_indexing_failures(self) -> list[dict]:
        return []

    async def auto_remediate(self) -> dict:
        results = {
            "ocr": await self.detect_and_fix_ocr_failures(),
            "classification": await self.detect_and_fix_classification_failures(),
            "extraction": await self.detect_and_fix_extraction_failures(),
            "fhir": await self.detect_and_fix_fhir_mapping_failures(),
            "indexing": await self.detect_and_fix_indexing_failures(),
        }
        total = sum(len(v) for v in results.values())
        return {"actions_taken": total, "details": results, "success": True}


def build_orchestrator(
    session_factory: sessionmaker | None = None,
    storage_path: str = "/data/documents",
) -> DocumentIntelligenceOrchestrator:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    if session_factory is None:
        engine = create_engine("sqlite:///docint.db")
        session_factory = sessionmaker(bind=engine)

    from ..infrastructure.repository import (
        SqlAccessControlRepository,
        SqlAnnotationRepository,
        SqlDocumentEventRepository,
        SqlGovernanceEventRepository,
        SqlGovernancePolicyRepository,
        SqlGovernmentDocumentRepository,
        SqlGraphEdgeRepository,
        SqlLifecycleRepository,
        SqlPipelineHealthRepository,
        SqlPreservationRepository,
        SqlRetentionRepository,
        SqlReviewRepository,
        SqlVersionRepository,
        SqlWebhookRepository,
    )
    from ..infrastructure.services import (
        InfrastructureAccessControlService,
        InfrastructureCollaborationService,
        InfrastructureDocumentLifecycleManager,
        InfrastructureDocumentLifecycleService,
        InfrastructureEventBusService,
        InfrastructureGovernanceService,
        InfrastructureGovernmentRecordsService,
        InfrastructureKnowledgeGraphService,
        InfrastructureNationalArchiveService,
        InfrastructureObservabilityService,
        InfrastructureSemanticSearchService,
        InfrastructureWebhookService,
    )

    doc_repo: DocumentRepository = SqlDocumentRepository(session_factory)
    ocr_repo: OcrResultRepository = SqlOcrResultRepository(session_factory)
    entity_repo: EntityRepository = SqlEntityRepository(session_factory)
    field_repo: FieldRepository = SqlFieldRepository(session_factory)
    table_repo: TableRepository = SqlTableRepository(session_factory)
    classifier_repo: ClassificationResultRepository = SqlClassificationResultRepository(session_factory)
    pipeline_repo: PipelineResultRepository = SqlPipelineResultRepository(session_factory)
    storage: StorageRepository = LocalStorageRepository(storage_path)

    gov_doc_repo = SqlGovernmentDocumentRepository(session_factory)
    review_repo = SqlReviewRepository(session_factory)
    annotation_repo = SqlAnnotationRepository(session_factory)
    preservation_repo = SqlPreservationRepository(session_factory)
    policy_repo = SqlGovernancePolicyRepository(session_factory)
    gov_event_repo = SqlGovernanceEventRepository(session_factory)
    doc_event_repo = SqlDocumentEventRepository(session_factory)
    lifecycle_repo = SqlLifecycleRepository(session_factory)
    webhook_repo = SqlWebhookRepository(session_factory)
    edge_repo = SqlGraphEdgeRepository(session_factory)
    health_repo = SqlPipelineHealthRepository(session_factory)
    access_repo = SqlAccessControlRepository(session_factory)
    retention_repo = SqlRetentionRepository(session_factory)
    SqlVersionRepository(session_factory)

    encryptor = DefaultEncryptionService()
    audit = DefaultAuditService()
    events = DefaultPipelineEventPublisher()
    parser = DefaultDocumentParser()
    preprocessor = DefaultImagePreprocessor()
    layout = DefaultLayoutDetector()
    classifier = DefaultDocumentClassifier()
    extractor = DefaultEntityExtractor()
    fhir_mapper = DefaultFhirMapper()
    knowledge_extractor = DefaultKnowledgeExtractor()
    search_indexer = DefaultSearchIndexer()
    medical_parser = DefaultMedicalParser()
    benchmark = DefaultProviderBenchmark()

    provider_manager = OcrProviderManager()
    tesseract = TesseractProvider()
    provider_manager.register(OcrEngine.tesseract, tesseract)
    try:
        paddle = PaddleOcrProvider()
        provider_manager.register(OcrEngine.paddle_ocr, paddle)
    except Exception:
        pass
    try:
        easy = EasyOcrProvider()
        provider_manager.register(OcrEngine.easy_ocr, easy)
    except Exception:
        pass

    global _provider_manager
    _provider_manager = provider_manager

    ingestion = DefaultIngestionService(doc_repo, storage, parser, encryptor, events, audit)
    ocr_pipeline = DefaultOcrPipelineService(
        provider_manager.get_all(), parser, preprocessor, layout,
        benchmark, ocr_repo, doc_repo, events, audit,
    )
    classifier_service = DefaultClassifierService(classifier, classifier_repo, doc_repo, events, audit)
    entity_service = DefaultEntityExtractionService(extractor, entity_repo, field_repo, table_repo, medical_parser, events, audit)
    fhir_service = DefaultFhirMappingService(fhir_mapper, events, audit)
    knowledge_service = DefaultKnowledgePipelineService(knowledge_extractor, search_indexer, events, audit)
    search_service = DefaultSearchService(search_indexer)
    real_lifecycle = InfrastructureDocumentLifecycleManager(doc_repo, retention_repo, lifecycle_repo, preservation_repo)
    remediation = DefaultRemediationService(doc_repo)

    gov_service = InfrastructureGovernmentRecordsService(gov_doc_repo, doc_repo)
    collab_service = InfrastructureCollaborationService(review_repo, annotation_repo)
    gov_service_ = InfrastructureGovernanceService(policy_repo, gov_event_repo, doc_repo)
    archive_service = InfrastructureNationalArchiveService(preservation_repo, doc_repo, storage)
    kg_service = InfrastructureKnowledgeGraphService(edge_repo)
    webhook_service = InfrastructureWebhookService(webhook_repo, doc_event_repo)
    obs_service = InfrastructureObservabilityService(health_repo)
    access_service = InfrastructureAccessControlService(access_repo)
    semantic_service = InfrastructureSemanticSearchService(doc_repo)
    lifecycle_service = InfrastructureDocumentLifecycleService(lifecycle_repo)
    event_bus = InfrastructureEventBusService(doc_event_repo)

    orchestrator = DocumentIntelligenceOrchestrator(
        ingestion=ingestion,
        ocr_pipeline=ocr_pipeline,
        classifier=classifier_service,
        entity_extractor=entity_service,
        fhir_mapper=fhir_service,
        knowledge_pipeline=knowledge_service,
        search=search_service,
        lifecycle=real_lifecycle,
        remediation=remediation,
        doc_repo=doc_repo,
        pipeline_repo=pipeline_repo,
        event_publisher=events,
        audit=audit,
        gov_service=gov_service,
        collab_service=collab_service,
        gov_service_=gov_service_,
        archive_service=archive_service,
        kg_service=kg_service,
        webhook_service=webhook_service,
        obs_service=obs_service,
        access_service=access_service,
        semantic_service=semantic_service,
        lifecycle_service=lifecycle_service,
        event_bus=event_bus,
    )

    global _orchestrator, _document_repo
    _orchestrator = orchestrator
    _document_repo = doc_repo

    return orchestrator


def get_orchestrator() -> DocumentIntelligenceOrchestrator:
    if _orchestrator is None:
        raise RuntimeError("Document Intelligence Platform not initialized. Call build_orchestrator() first.")
    return _orchestrator


def get_provider_manager() -> OcrProviderManager:
    if _provider_manager is None:
        raise RuntimeError("Document Intelligence Platform not initialized.")
    return _provider_manager


def get_document_repo() -> DocumentRepository:
    if _document_repo is None:
        raise RuntimeError("Document Intelligence Platform not initialized.")
    return _document_repo
