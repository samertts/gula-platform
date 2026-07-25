from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from ..domain.entities import (
    CollaborationSession,
    DigitalPreservationRecord,
    DocumentAnnotation,
    DocumentEvent,
    DocumentLifecycleRecord,
    DocumentReview,
    GovernanceEvent,
    GovernancePolicy,
    GovernmentDocument,
    KnowledgeGraphEdge,
    PipelineHealth,
    ScannedDocument,
    SemanticQuery,
    SemanticSearchResult,
)
from ..domain.enums import (
    CollaborationRole,
    DigitalPreservationStandard,
    DocumentStatus,
    EventChannel,
    GovernanceDomain,
    GovernancePolicyAction,
    GovernanceRuleSeverity,
    RetentionPolicy,
    ReviewDecision,
)
from ..domain.repository import (
    AccessControlRepository,
    AnnotationRepository,
    DocumentEventRepository,
    DocumentRepository,
    DocumentVersionRepository,
    GovernanceEventRepository,
    GovernancePolicyRepository,
    GovernmentDocumentRepository,
    GraphEdgeRepository,
    LifecycleRepository,
    PipelineHealthRepository,
    PreservationRepository,
    RetentionRepository,
    ReviewRepository,
    WebhookRepository,
)
from ..exceptions import DocumentIntelligenceError

logger = logging.getLogger("gula.document_intelligence.services")


class InfrastructureVersioningService:
    def __init__(
        self,
        version_repo: DocumentVersionRepository,
        doc_repo: DocumentRepository,
        storage_repo: Any,
    ) -> None:
        self._version_repo = version_repo
        self._doc_repo = doc_repo
        self._storage = storage_repo

    async def create_version(self, document_id: UUID, data: bytes) -> int:
        version_number = await self._version_repo.get_latest_version(document_id) + 1
        checksum = str(hash(data))
        storage_path = f"versions/{document_id}/v{version_number}"
        await self._storage.save(data, storage_path, encrypt=True)
        await self._version_repo.save_version(
            document_id, version_number, storage_path, checksum, "system",
        )
        return version_number

    async def get_version(self, document_id: UUID, version: int) -> bytes | None:
        versions = await self._version_repo.list_versions(document_id)
        for v in versions:
            if v.get("version_number") == version:
                return await self._storage.read(v["storage_path"])
        return None

    async def list_versions(self, document_id: UUID) -> list[dict[str, Any]]:
        return await self._version_repo.list_versions(document_id)

    async def restore_version(self, document_id: UUID, version: int) -> ScannedDocument:
        data = await self.get_version(document_id, version)
        if data is None:
            raise DocumentIntelligenceError(f"Version {version} not found")
        doc = await self._doc_repo.get(document_id)
        if doc is None:
            raise DocumentIntelligenceError(f"Document {document_id} not found")
        str(hash(data))
        await self._storage.save(data, doc.storage_path, encrypt=True)
        return doc


class InfrastructureDocumentLifecycleManager:
    def __init__(
        self,
        doc_repo: DocumentRepository,
        retention_repo: RetentionRepository,
        lifecycle_repo: LifecycleRepository,
        preservation_repo: PreservationRepository,
    ) -> None:
        self._doc_repo = doc_repo
        self._retention = retention_repo
        self._lifecycle = lifecycle_repo
        self._preservation = preservation_repo

    async def apply_retention_policy(self, document_id: UUID) -> None:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            raise DocumentIntelligenceError("Document not found")
        start = datetime.now(UTC)
        start + timedelta(days=365 * 7)
        await self._retention.save(document_id, RetentionPolicy.standard_7y)
        await self._lifecycle.save(
            DocumentLifecycleRecord(
                document_id=document_id,
                event_type="retention_applied",
                actor="system",
                reason="Retention policy applied",
            ),
        )

    async def archive_document(self, document_id: UUID) -> None:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            raise DocumentIntelligenceError("Document not found")
        doc.status = DocumentStatus.archived
        await self._doc_repo.save(doc)

    async def restore_document(self, document_id: UUID) -> ScannedDocument:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            raise DocumentIntelligenceError("Document not found")
        doc.status = DocumentStatus.knowledge_indexed
        await self._doc_repo.save(doc)
        return doc

    async def apply_legal_hold(self, document_id: UUID) -> None:
        await self._lifecycle.save(
            DocumentLifecycleRecord(
                document_id=document_id,
                event_type="legal_hold_applied",
                actor="system",
                reason="Legal hold applied",
            ),
        )

    async def release_legal_hold(self, document_id: UUID) -> None:
        await self._lifecycle.save(
            DocumentLifecycleRecord(
                document_id=document_id,
                event_type="legal_hold_released",
                actor="system",
                reason="Legal hold released",
            ),
        )

    async def deduplicate(self, document_id: UUID) -> list[UUID]:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            return []
        return await self._doc_repo.find_duplicates(doc.checksum_sha256)

    async def compress(self, document_id: UUID) -> None:
        pass

    async def schedule_deletion(self, document_id: UUID, days: int) -> None:
        await self._lifecycle.save(
            DocumentLifecycleRecord(
                document_id=document_id,
                event_type="deletion_scheduled",
                actor="system",
                reason=f"Deletion scheduled in {days} days",
            ),
        )


class InfrastructureGovernmentRecordsService:
    def __init__(
        self, gov_repo: GovernmentDocumentRepository, doc_repo: DocumentRepository,
    ) -> None:
        self._gov_repo = gov_repo
        self._doc_repo = doc_repo

    async def register_government_document(
        self, document_id: UUID, gov_record: GovernmentDocument,
    ) -> GovernmentDocument:
        if not gov_record.reference_number:
            gov_record.reference_number = await self.generate_reference_number(
                gov_record.issuing_authority,
                "GOV",
            )
        return await self._gov_repo.save(gov_record)

    async def get_government_document(self, document_id: UUID) -> GovernmentDocument | None:
        return await self._gov_repo.get(document_id)

    async def search_government_documents(
        self, query: str, filters: dict | None = None,
    ) -> list[GovernmentDocument]:
        return await self._gov_repo.search(query, filters)

    async def track_order_lifecycle(self, document_id: UUID) -> list[dict[str, Any]]:
        items = []
        for status_name in (
            "draft",
            "submitted",
            "under_review",
            "approved",
            "implemented",
            "completed",
        ):
            items.append({"status": status_name, "timestamp": datetime.now(UTC).isoformat()})
        return items

    async def validate_government_format(self, doc: GovernmentDocument) -> dict[str, Any]:
        issues = []
        if not doc.reference_number:
            issues.append("Missing reference number")
        if not doc.issuing_authority:
            issues.append("Missing issuing authority")
        return {"valid": len(issues) == 0, "issues": issues}

    async def generate_reference_number(self, authority: str, category: str) -> str:
        prefix = "".join(w[0].upper() for w in authority.split() if w)[:4]
        seq = int(datetime.now(UTC).timestamp() * 1000) % 100000
        return f"{prefix}-{category}-{seq:05d}-{datetime.now(UTC).year}"


class InfrastructureCollaborationService:
    def __init__(
        self, review_repo: ReviewRepository, annotation_repo: AnnotationRepository,
    ) -> None:
        self._review_repo = review_repo
        self._annotation_repo = annotation_repo
        self._sessions: dict[UUID, CollaborationSession] = {}

    async def assign_reviewer(
        self,
        document_id: UUID,
        reviewer_id: str,
        role: CollaborationRole = CollaborationRole.reviewer,
    ) -> DocumentReview:
        review = DocumentReview(
            document_id=document_id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_id,
            role=role,
        )
        return await self._review_repo.save(review)

    async def submit_review(
        self,
        review_id: UUID,
        decision: ReviewDecision,
        comments: str = "",
        changes: list[str] | None = None,
    ) -> DocumentReview:
        review = await self._review_repo.get(review_id)
        if not review:
            raise DocumentIntelligenceError(f"Review {review_id} not found")
        review.decision = decision
        review.comments = comments
        if changes:
            review.suggested_changes = changes
        review.completed_at = datetime.now(UTC)
        return await self._review_repo.update(review)

    async def get_reviews(self, document_id: UUID) -> list[DocumentReview]:
        return await self._review_repo.get_by_document(document_id)

    async def add_annotation(self, annotation: DocumentAnnotation) -> DocumentAnnotation:
        return await self._annotation_repo.save(annotation)

    async def get_annotations(self, document_id: UUID) -> list[DocumentAnnotation]:
        return await self._annotation_repo.get_by_document(document_id)

    async def resolve_annotation(self, annotation_id: UUID) -> DocumentAnnotation:
        ann = await self._annotation_repo.get(annotation_id)
        if not ann:
            raise DocumentIntelligenceError(f"Annotation {annotation_id} not found")
        ann.resolved = True
        return await self._annotation_repo.update(ann)

    async def create_session(self, document_id: UUID) -> CollaborationSession:
        session = CollaborationSession(document_id=document_id)
        self._sessions[session.id] = session
        return session

    async def join_session(self, session_id: UUID, user_id: str) -> CollaborationSession:
        session = self._sessions.get(session_id)
        if not session:
            raise DocumentIntelligenceError(f"Session {session_id} not found")
        session.participants.append(
            {"user_id": user_id, "joined_at": datetime.now(UTC).isoformat()},
        )
        return session

    async def get_session(self, session_id: UUID) -> CollaborationSession | None:
        return self._sessions.get(session_id)


class InfrastructureGovernanceService:
    def __init__(
        self,
        policy_repo: GovernancePolicyRepository,
        event_repo: GovernanceEventRepository,
        doc_repo: DocumentRepository,
    ) -> None:
        self._policy_repo = policy_repo
        self._event_repo = event_repo
        self._doc_repo = doc_repo

    async def create_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        return await self._policy_repo.save(policy)

    async def update_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        return await self._policy_repo.save(policy)

    async def delete_policy(self, policy_id: UUID) -> None:
        await self._policy_repo.delete(policy_id)

    async def get_policy(self, policy_id: UUID) -> GovernancePolicy | None:
        return await self._policy_repo.get(policy_id)

    async def list_policies(self, domain: GovernanceDomain | None = None) -> list[GovernancePolicy]:
        return await self._policy_repo.list(domain)

    async def evaluate_document(self, document_id: UUID) -> list[GovernanceEvent]:
        policies = await self._policy_repo.list()
        events: list[GovernanceEvent] = []
        for policy in policies:
            if not policy.enabled:
                continue
            event = GovernanceEvent(
                document_id=document_id,
                policy_id=policy.id,
                domain=policy.domain,
                severity=policy.severity,
                message=f"Policy {policy.name} evaluated",
                action_taken=policy.action,
            )
            await self._event_repo.save(event)
            events.append(event)
        return events

    async def evaluate_all(self) -> list[GovernanceEvent]:
        return []

    async def get_governance_events(
        self, document_id: UUID | None = None, severity: GovernanceRuleSeverity | None = None,
    ) -> list[GovernanceEvent]:
        return await self._event_repo.list(document_id, severity)

    async def apply_policy_action(self, event: GovernanceEvent) -> None:
        if event.action_taken == GovernancePolicyAction.quarantine:
            doc = await self._doc_repo.get(event.document_id)
            if doc:
                doc.status = DocumentStatus.classification_failed
                await self._doc_repo.save(doc)


class InfrastructureNationalArchiveService:
    def __init__(
        self,
        preservation_repo: PreservationRepository,
        doc_repo: DocumentRepository,
        storage_repo: Any,
    ) -> None:
        self._preservation = preservation_repo
        self._doc_repo = doc_repo
        self._storage = storage_repo

    async def archive_document(
        self, document_id: UUID, policy: RetentionPolicy = RetentionPolicy.standard_7y,
    ) -> DigitalPreservationRecord:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            raise DocumentIntelligenceError("Document not found")
        doc.status = DocumentStatus.archived
        await self._doc_repo.save(doc)
        record = DigitalPreservationRecord(
            document_id=document_id,
            standard=DigitalPreservationStandard.oais,
            original_format=doc.mime_type,
            preservation_format=doc.mime_type,
            original_checksum=doc.checksum_sha256,
            preservation_checksum=doc.checksum_sha256,
            preservation_location=doc.storage_path,
        )
        return await self._preservation.save(record)

    async def preserve_document(
        self,
        document_id: UUID,
        standard: DigitalPreservationStandard = DigitalPreservationStandard.oais,
    ) -> DigitalPreservationRecord:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            raise DocumentIntelligenceError("Document not found")
        await self._doc_repo.save(doc)
        record = DigitalPreservationRecord(
            document_id=document_id,
            standard=standard,
            original_format=doc.mime_type,
            preservation_format=doc.mime_type,
            original_checksum=doc.checksum_sha256,
            preservation_checksum=doc.checksum_sha256,
            preservation_location=doc.storage_path,
            next_integrity_check=datetime.now(UTC) + timedelta(days=90),
        )
        return await self._preservation.save(record)

    async def check_integrity(self, document_id: UUID) -> dict[str, Any]:
        record = await self._preservation.get_by_document(document_id)
        if not record:
            raise DocumentIntelligenceError("No preservation record found")
        data = await self._storage.read(record.preservation_location, decrypt=True)
        current_checksum = str(hash(data))
        return {
            "document_id": str(document_id),
            "original_checksum": record.original_checksum,
            "current_checksum": current_checksum,
            "intact": current_checksum == record.original_checksum,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    async def restore_from_archive(self, document_id: UUID) -> ScannedDocument:
        doc = await self._doc_repo.get(document_id)
        if not doc:
            raise DocumentIntelligenceError("Document not found")
        doc.status = DocumentStatus.knowledge_indexed
        await self._doc_repo.save(doc)
        return doc

    async def get_preservation_record(self, document_id: UUID) -> DigitalPreservationRecord | None:
        return await self._preservation.get_by_document(document_id)

    async def schedule_integrity_checks(self) -> list[dict[str, Any]]:
        return []

    async def apply_retention(self, document_id: UUID) -> None:
        pass

    async def purge_expired(self) -> list[UUID]:
        return []


class InfrastructureWebhookService:
    def __init__(
        self, webhook_repo: WebhookRepository, event_repo: DocumentEventRepository,
    ) -> None:
        self._webhook_repo = webhook_repo
        self._event_repo = event_repo

    async def register_webhook(
        self, url: str, events: list[EventChannel], secret: str | None = None,
    ) -> dict[str, Any]:
        return await self._webhook_repo.register(url, events, secret)

    async def unregister_webhook(self, webhook_id: UUID) -> None:
        await self._webhook_repo.unregister(webhook_id)

    async def dispatch_event(self, event: DocumentEvent) -> None:
        await self._event_repo.save(event)
        targets = await self._webhook_repo.get_by_event(event.channel)
        for target in targets:
            logger.debug("Dispatching event %s to %s", event.channel, target.get("url"))

    async def get_webhook_log(self, webhook_id: UUID) -> list[dict[str, Any]]:
        return []

    async def retry_failed(self, webhook_id: UUID) -> None:
        pass


class InfrastructureKnowledgeGraphService:
    def __init__(self, edge_repo: GraphEdgeRepository) -> None:
        self._edge_repo = edge_repo

    async def add_edge(self, edge: KnowledgeGraphEdge) -> KnowledgeGraphEdge:
        return await self._edge_repo.save(edge)

    async def find_related_documents(
        self, document_id: UUID, max_depth: int = 3,
    ) -> list[dict[str, Any]]:
        return await self._edge_repo.find_related(document_id, max_depth)

    async def get_entity_network(self, entity_name: str) -> dict[str, Any]:
        edges = await self._edge_repo.get_entity_network(entity_name)
        return {"entity": entity_name, "edges": edges}

    async def get_document_subgraph(self, document_id: UUID) -> dict[str, Any]:
        edges = await self._edge_repo.get_by_document(document_id)
        return {"document_id": str(document_id), "edges": [str(e.source_entity) for e in edges]}

    async def query_graph(self, query: str) -> list[dict[str, Any]]:
        return []

    async def rebuild_graph(self) -> None:
        pass


class InfrastructureObservabilityService:
    def __init__(self, health_repo: PipelineHealthRepository) -> None:
        self._health_repo = health_repo

    async def get_pipeline_health(self) -> list[PipelineHealth]:
        return await self._health_repo.get_all_pipelines()

    async def get_dashboard_data(self) -> dict[str, Any]:
        health = await self._health_repo.get_all_pipelines()
        return {
            "pipelines": [str(h.pipeline_name) for h in health],
            "total_documents_processed": sum(h.documents_processed for h in health),
            "total_failed": sum(h.documents_failed for h in health),
            "average_processing_time_ms": (
                sum(h.avg_processing_time_ms for h in health) / max(len(health), 1)
            ),
        }

    async def get_document_statistics(self) -> dict[str, Any]:
        return await self.get_dashboard_data()

    async def get_throughput_metrics(self) -> dict[str, Any]:
        health = await self._health_repo.get_all_pipelines()
        return {
            "total_throughput": sum(h.throughput_per_minute for h in health),
        }

    async def record_pipeline_metrics(self, health: PipelineHealth) -> None:
        await self._health_repo.save(health)

    async def get_ocr_statistics(self) -> dict[str, Any]:
        return {}

    async def get_processing_times(self) -> dict[str, Any]:
        return {}

    async def get_error_rates(self) -> dict[str, Any]:
        return {}

    async def get_knowledge_graph_statistics(self) -> dict[str, Any]:
        return {}

    async def get_governance_summary(self) -> dict[str, Any]:
        return {}


class InfrastructureDocumentLifecycleService:
    def __init__(self, lifecycle_repo: LifecycleRepository) -> None:
        self._lifecycle_repo = lifecycle_repo

    async def get_lifecycle(self, document_id: UUID) -> list[DocumentLifecycleRecord]:
        return await self._lifecycle_repo.get_by_document(document_id)

    async def record_event(
        self,
        document_id: UUID,
        event_type: str,
        actor: str,
        reason: str = "",
        metadata: dict | None = None,
    ) -> DocumentLifecycleRecord:
        record = DocumentLifecycleRecord(
            document_id=document_id,
            event_type=event_type,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
        )
        return await self._lifecycle_repo.save(record)

    async def get_active_documents(self) -> list[DocumentLifecycleRecord]:
        return []

    async def get_expiring_documents(self, days: int = 30) -> list[DocumentLifecycleRecord]:
        return []


class InfrastructureAccessControlService:
    def __init__(self, access_repo: AccessControlRepository) -> None:
        self._access_repo = access_repo

    async def check_access(
        self, document_id: UUID, user_id: str, permission: str = "viewer",
    ) -> bool:
        role = await self._access_repo.check(document_id, user_id)
        if role is None:
            return False
        hierarchy = {
            "viewer": 0,
            "commenter": 1,
            "reviewer": 2,
            "approver": 3,
            "editor": 4,
            "owner": 5,
        }
        required = hierarchy.get(permission, 0)
        actual = hierarchy.get(role.value if hasattr(role, "value") else str(role), -1)
        return actual >= required

    async def grant_access(self, document_id: UUID, user_id: str, role: CollaborationRole) -> None:
        await self._access_repo.grant(document_id, user_id, role)

    async def revoke_access(self, document_id: UUID, user_id: str) -> None:
        await self._access_repo.revoke(document_id, user_id)

    async def get_access_list(self, document_id: UUID) -> list[dict[str, Any]]:
        return []

    async def get_documents_for_user(self, user_id: str, permission: str = "viewer") -> list[UUID]:
        return await self._access_repo.get_by_user(user_id)

    async def delegate_access(
        self, document_id: UUID, from_user: str, to_user: str, expiry: datetime | None = None,
    ) -> None:
        await self._access_repo.grant(document_id, to_user, CollaborationRole.viewer)


class InfrastructureEventBusService:
    def __init__(self, event_repo: DocumentEventRepository) -> None:
        self._event_repo = event_repo
        self._handlers: dict[str, list[Any]] = {}

    async def publish(self, event: DocumentEvent) -> None:
        await self._event_repo.save(event)
        for handler in self._handlers.get(str(event.channel), []):
            try:
                await handler(event)
            except Exception:
                logger.exception("Event handler failed for %s", event.channel)

    async def subscribe(self, channel: EventChannel, handler: Any) -> None:
        key = str(channel)
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(handler)

    async def unsubscribe(self, channel: EventChannel, handler: Any) -> None:
        key = str(channel)
        if key in self._handlers:
            self._handlers[key] = [h for h in self._handlers[key] if h != handler]

    async def get_event_history(
        self, document_id: UUID | None = None, channel: EventChannel | None = None,
    ) -> list[DocumentEvent]:
        return await self._event_repo.list(document_id, channel)


class InfrastructureSemanticSearchService:
    def __init__(self, doc_repo: DocumentRepository) -> None:
        self._doc_repo = doc_repo

    async def search(self, query: SemanticQuery) -> list[SemanticSearchResult]:
        docs, _ = await self._doc_repo.search(query.query_text, limit=query.limit)
        return [
            SemanticSearchResult(document_id=d.id, score=1.0, text_snippet=d.filename) for d in docs
        ]

    async def hybrid_search(
        self, query_text: str, query_vector: list[float] | None = None,
    ) -> list[SemanticSearchResult]:
        docs, _ = await self._doc_repo.search(query_text, limit=20)
        return [
            SemanticSearchResult(document_id=d.id, score=1.0, text_snippet=d.filename) for d in docs
        ]

    async def arabic_search(self, query: str) -> list[SemanticSearchResult]:
        return await self.hybrid_search(query)

    async def natural_language_query(self, query: str) -> list[SemanticSearchResult]:
        return await self.hybrid_search(query)

    async def similar_documents(
        self, document_id: UUID, limit: int = 10,
    ) -> list[SemanticSearchResult]:
        return []

    async def search_by_entity(self, entity_type: Any, value: str) -> list[SemanticSearchResult]:
        return []

    async def suggest_queries(self, partial: str) -> list[str]:
        return [f"{partial}_1", f"{partial}_2"]
