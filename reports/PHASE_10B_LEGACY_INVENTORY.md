# Phase 10-B — Legacy Clinical Identity and Context Inventory

This inventory is generated from source files, not inherited reports. It records every matched source occurrence for `LabUser`, `lab_id`, and legacy identity/context terms under the scanned application roots. No source was deleted or migrated by this inventory step.

## Classification summary

| Classification | Occurrences | Meaning |
|---|---:|---|
| RETAIN | 4589 | Existing source remains authoritative only within its current legacy boundary until an approved adapter replaces it. |
| MIGRATE | 27 | Frontend or caller must move to the canonical gateway; it must not receive a legacy fallback. |
| ADAPTER | 121 | Existing reviewed identity/scope bridge may be reused only after canonical authorization. |
| DEPRECATE | 6 | Legacy frontend surface remains for compatibility but is not a new gateway authority. |
| REMOVE | 0 | No removal is authorized in Phase 10-B. |

## Rules

* `lab_id`, `organization_id`, `facility_id`, and `workspace_id` from a browser request are never authoritative.
* `get_current_user`/`LabUser` remains a legacy boundary only; the new gateway must resolve `NiamActor` and trusted workspace context first.
* Unmapped, ambiguous, inactive, or conflicting identities are blocked and audited.

## Occurrences

| File | Line | Match | Classification | Source evidence |
|---|---:|---|---|---|
| `backend/app/ai/agent_runtime.py` | 27 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/ai/agent_runtime.py` | 65 | `lab_id` | **RETAIN** | `async def _lookup_patient(query: str, lab_id: int \| None = None, **kwargs) -> dict[str, Any]:` |
| `backend/app/ai/agent_runtime.py` | 69 | `lab_id` | **RETAIN** | `text("SELECT id, name, phone, gender, birth_date FROM patients WHERE (name ILIKE :q OR phone = :q_exact OR cast(id as text) = :q_exact) AND (lab_id = :lab OR :lab IS NULL) LIMIT 1"),` |
| `backend/app/ai/agent_runtime.py` | 70 | `lab_id` | **RETAIN** | `{"q": f"%{query}%", "q_exact": query, "lab": lab_id},` |
| `backend/app/ai/agent_runtime.py` | 121 | `lab_id` | **RETAIN** | `async def _get_lab_info(lab_id: int \| None = None, **kwargs) -> dict[str, Any]:` |
| `backend/app/ai/agent_runtime.py` | 122 | `lab_id` | **RETAIN** | `if lab_id is None:` |
| `backend/app/ai/agent_runtime.py` | 123 | `lab_id` | **RETAIN** | `return {"error": "lab_id is required"}` |
| `backend/app/ai/agent_runtime.py` | 128 | `lab_id` | **RETAIN** | `{"lab": lab_id},` |
| `backend/app/ai/agent_runtime.py` | 175 | `lab_id` | **RETAIN** | `output = await tool.fn(**kwargs, lab_id=context.lab_id, user_id=context.user_id)` |
| `backend/app/ai/agent_runtime.py` | 175 | `lab_id` | **RETAIN** | `output = await tool.fn(**kwargs, lab_id=context.lab_id, user_id=context.user_id)` |
| `backend/app/ai/agent_runtime.py` | 214 | `lab_id` | **RETAIN** | `self, session_id: str, task: str, lab_id: int \| None = None, user_id: int \| None = None,` |
| `backend/app/ai/agent_runtime.py` | 218 | `lab_id` | **RETAIN** | `conv = await memory_store.create_session(lab_id=lab_id, user_id=user_id)` |
| `backend/app/ai/agent_runtime.py` | 218 | `lab_id` | **RETAIN** | `conv = await memory_store.create_session(lab_id=lab_id, user_id=user_id)` |
| `backend/app/ai/agent_runtime.py` | 221 | `lab_id` | **RETAIN** | `context = AgentContext(session_id=session_id, lab_id=lab_id, user_id=user_id, task=task)` |
| `backend/app/ai/agent_runtime.py` | 221 | `lab_id` | **RETAIN** | `context = AgentContext(session_id=session_id, lab_id=lab_id, user_id=user_id, task=task)` |
| `backend/app/ai/memory.py` | 29 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/ai/memory.py` | 43 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/ai/memory.py` | 51 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/ai/memory.py` | 51 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/ai/memory.py` | 62 | `lab_id` | **RETAIN** | `text("INSERT INTO ai_conversations (lab_id, user_id, session_id, title, metadata) VALUES (:lab, :uid, :sid, :title, :meta::jsonb) RETURNING id"),` |
| `backend/app/ai/memory.py` | 63 | `lab_id` | **RETAIN** | `{"lab": lab_id, "uid": user_id, "sid": session_id, "title": title, "meta": meta_json},` |
| `backend/app/ai/memory.py` | 124 | `lab_id` | **RETAIN** | `text("SELECT id, lab_id, user_id, session_id, title, metadata FROM ai_conversations WHERE session_id = :sid"),` |
| `backend/app/ai/memory.py` | 132 | `lab_id` | **RETAIN** | `lab_id=row.lab_id,` |
| `backend/app/ai/memory.py` | 132 | `lab_id` | **RETAIN** | `lab_id=row.lab_id,` |
| `backend/app/ai/memory.py` | 177 | `lab_id` | **RETAIN** | `def list_sessions(self, lab_id: int \| None = None, limit: int = 50) -> list[dict[str, Any]]:` |
| `backend/app/ai/memory.py` | 180 | `lab_id` | **RETAIN** | `if lab_id is not None and conv.lab_id != lab_id:` |
| `backend/app/ai/memory.py` | 180 | `lab_id` | **RETAIN** | `if lab_id is not None and conv.lab_id != lab_id:` |
| `backend/app/ai/memory.py` | 180 | `lab_id` | **RETAIN** | `if lab_id is not None and conv.lab_id != lab_id:` |
| `backend/app/ai/memory.py` | 184 | `lab_id` | **RETAIN** | `"lab_id": conv.lab_id,` |
| `backend/app/ai/memory.py` | 184 | `lab_id` | **RETAIN** | `"lab_id": conv.lab_id,` |
| `backend/app/ai/orchestrator.py` | 21 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/ai/orchestrator.py` | 40 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/ai/orchestrator.py` | 46 | `lab_id` | **RETAIN** | `task = OrchestrationTask(id=task_id, type=intent, query=query, lab_id=lab_id, user_id=user_id, session_id=session_id)` |
| `backend/app/ai/orchestrator.py` | 46 | `lab_id` | **RETAIN** | `task = OrchestrationTask(id=task_id, type=intent, query=query, lab_id=lab_id, user_id=user_id, session_id=session_id)` |
| `backend/app/ai/orchestrator.py` | 51 | `lab_id` | **RETAIN** | `result = await self._execute_by_intent(intent, query, lab_id, user_id, session_id)` |
| `backend/app/ai/orchestrator.py` | 90 | `lab_id` | **RETAIN** | `lab_id: int \| None,` |
| `backend/app/ai/orchestrator.py` | 95 | `lab_id` | **RETAIN** | `return await self._handle_clinical(query, lab_id)` |
| `backend/app/ai/orchestrator.py` | 97 | `lab_id` | **RETAIN** | `return await self._handle_patient(query, lab_id)` |
| `backend/app/ai/orchestrator.py` | 101 | `lab_id` | **RETAIN** | `return await self._handle_agent(query, lab_id, user_id, session_id)` |
| `backend/app/ai/orchestrator.py` | 104 | `lab_id` | **RETAIN** | `async def _handle_clinical(self, query: str, lab_id: int \| None) -> dict[str, Any]:` |
| `backend/app/ai/orchestrator.py` | 105 | `lab_id` | **RETAIN** | `rag_result = await rag.query(query, content_type="lab_result", lab_id=lab_id)` |
| `backend/app/ai/orchestrator.py` | 105 | `lab_id` | **RETAIN** | `rag_result = await rag.query(query, content_type="lab_result", lab_id=lab_id)` |
| `backend/app/ai/orchestrator.py` | 112 | `lab_id` | **RETAIN** | `async def _handle_patient(self, query: str, lab_id: int \| None) -> dict[str, Any]:` |
| `backend/app/ai/orchestrator.py` | 113 | `lab_id` | **RETAIN** | `context = AgentContext(session_id=str(uuid.uuid4()), lab_id=lab_id, task=query)` |
| `backend/app/ai/orchestrator.py` | 113 | `lab_id` | **RETAIN** | `context = AgentContext(session_id=str(uuid.uuid4()), lab_id=lab_id, task=query)` |
| `backend/app/ai/orchestrator.py` | 129 | `lab_id` | **RETAIN** | `self, query: str, lab_id: int \| None, user_id: int \| None, session_id: str \| None,` |
| `backend/app/ai/orchestrator.py` | 133 | `lab_id` | **RETAIN** | `results = await agent_runtime.run_session(session_id, query, lab_id, user_id)` |
| `backend/app/ai/rag_pipeline.py` | 55 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/ai/rag_pipeline.py` | 62 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/ai/rag_pipeline.py` | 62 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/ai/rag_pipeline.py` | 125 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/ai/rag_pipeline.py` | 128 | `lab_id` | **RETAIN** | `documents = await self.retrieve(question, content_type=content_type, lab_id=lab_id)` |
| `backend/app/ai/rag_pipeline.py` | 128 | `lab_id` | **RETAIN** | `documents = await self.retrieve(question, content_type=content_type, lab_id=lab_id)` |
| `backend/app/ai/vector_store.py` | 33 | `lab_id` | **RETAIN** | `def __init__(self, lab_id: int \| None = None):` |
| `backend/app/ai/vector_store.py` | 34 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/ai/vector_store.py` | 34 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/ai/vector_store.py` | 58 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/ai/vector_store.py` | 65 | `lab_id` | **RETAIN** | `lab = lab_id or self.lab_id` |
| `backend/app/ai/vector_store.py` | 65 | `lab_id` | **RETAIN** | `lab = lab_id or self.lab_id` |
| `backend/app/ai/vector_store.py` | 77 | `lab_id` | **RETAIN** | `def _index_pgvector(self, text, embedding, content_type, content_id, metadata, lab_id, content_hash):` |
| `backend/app/ai/vector_store.py` | 81 | `lab_id` | **RETAIN** | `text("SELECT id FROM ai_embeddings WHERE content_hash = :ch AND lab_id = :lab"),` |
| `backend/app/ai/vector_store.py` | 82 | `lab_id` | **RETAIN** | `{"ch": content_hash, "lab": lab_id},` |
| `backend/app/ai/vector_store.py` | 94 | `lab_id` | **RETAIN** | `text("INSERT INTO ai_embeddings (lab_id, content_type, content_id, content_hash, text, embedding, model, dimensions, metadata) VALUES (:lab, :ct, :cid, :ch, :txt, :vec::vector, :model, :dims, :meta::jsonb) RETURNING id"),` |
| `backend/app/ai/vector_store.py` | 95 | `lab_id` | **RETAIN** | `{"lab": lab_id, "ct": content_type, "cid": content_id, "ch": content_hash, "txt": text, "vec": vec_str, "model": "gemini-embedding-exp-03-07", "dims": len(embedding), "meta": meta_json},` |
| `backend/app/ai/vector_store.py` | 113 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/ai/vector_store.py` | 118 | `lab_id` | **RETAIN** | `return self._search_pgvector(query_embedding, content_type, limit, threshold, lab_id)` |
| `backend/app/ai/vector_store.py` | 120 | `lab_id` | **RETAIN** | `return self._search_in_memory(query_embedding, content_type, limit, threshold, lab_id)` |
| `backend/app/ai/vector_store.py` | 122 | `lab_id` | **RETAIN** | `def _search_pgvector(self, query_embedding, content_type, limit, threshold, lab_id):` |
| `backend/app/ai/vector_store.py` | 127 | `lab_id` | **RETAIN** | `lab = lab_id or self.lab_id` |
| `backend/app/ai/vector_store.py` | 127 | `lab_id` | **RETAIN** | `lab = lab_id or self.lab_id` |
| `backend/app/ai/vector_store.py` | 133 | `lab_id` | **RETAIN** | `sql = text("SELECT e.id, e.content_type, e.content_id, e.text, e.metadata, 1 - (e.embedding <=> :vec::vector) AS score FROM ai_embeddings e WHERE e.lab_id = :lab AND e.content_type = :ct ORDER BY score DESC LIMIT :limit")` |
| `backend/app/ai/vector_store.py` | 135 | `lab_id` | **RETAIN** | `sql = text("SELECT e.id, e.content_type, e.content_id, e.text, e.metadata, 1 - (e.embedding <=> :vec::vector) AS score FROM ai_embeddings e WHERE e.lab_id = :lab ORDER BY score DESC LIMIT :limit")` |
| `backend/app/ai/vector_store.py` | 158 | `lab_id` | **RETAIN** | `def _search_in_memory(self, query_embedding, content_type, limit, threshold, lab_id):` |
| `backend/app/ai/vector_store.py` | 164 | `lab_id` | **RETAIN** | `if lab_id or self.lab_id:` |
| `backend/app/ai/vector_store.py` | 164 | `lab_id` | **RETAIN** | `if lab_id or self.lab_id:` |
| `backend/app/ai/vector_store.py` | 165 | `lab_id` | **RETAIN** | `query = query.where(text("lab_id = :lab"))` |
| `backend/app/ai/vector_store.py` | 210 | `lab_id` | **RETAIN** | `if self.lab_id is not None:` |
| `backend/app/ai/vector_store.py` | 211 | `lab_id` | **RETAIN** | `params["lab"] = self.lab_id` |
| `backend/app/ai/vector_store.py` | 212 | `lab_id` | **RETAIN** | `sql = text("SELECT id, content_type, content_id, text, metadata FROM ai_embeddings WHERE metadata @> :filter_json::jsonb AND lab_id = :lab LIMIT :limit")` |
| `backend/app/ai_fabric/agents/base.py` | 70 | `lab_id` | **RETAIN** | `lab_id: str = ""` |
| `backend/app/ai_fabric/agents/base.py` | 80 | `lab_id` | **RETAIN** | `"lab_id": self.lab_id,` |
| `backend/app/ai_fabric/agents/base.py` | 80 | `lab_id` | **RETAIN** | `"lab_id": self.lab_id,` |
| `backend/app/ai_fabric/routes.py` | 327 | `lab_id` | **RETAIN** | `lab_id: str = "",` |
| `backend/app/ai_fabric/routes.py` | 331 | `lab_id` | **RETAIN** | `context = AgentContext(user_id=user_id, lab_id=lab_id)` |
| `backend/app/ai_fabric/routes.py` | 331 | `lab_id` | **RETAIN** | `context = AgentContext(user_id=user_id, lab_id=lab_id)` |
| `backend/app/ai_fabric/sdk.py` | 177 | `lab_id` | **RETAIN** | `def create_context(self, user_id: str = "", lab_id: str = "", **kwargs: str) -> AgentContext:` |
| `backend/app/ai_fabric/sdk.py` | 180 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/ai_fabric/sdk.py` | 180 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/audit/__init__.py` | 33 | `lab_id` | **RETAIN** | `lab_id = getattr(request.state, "lab_id", None) or 0` |
| `backend/app/audit/__init__.py` | 33 | `lab_id` | **RETAIN** | `lab_id = getattr(request.state, "lab_id", None) or 0` |
| `backend/app/audit/__init__.py` | 51 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/audit/__init__.py` | 51 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/certification/release_gates.py` | 148 | `lab_id` | **RETAIN** | `if "lab_id" in content and "filter" in content.lower():` |
| `backend/app/certification/release_gates.py` | 150 | `lab_id` | **RETAIN** | `self._add_evidence("Tenant isolation (lab_id filtering) found")` |
| `backend/app/certification/release_gates.py` | 155 | `lab_id` | **RETAIN** | `self._add_remediation("Ensure all patient queries filter by lab_id")` |
| `backend/app/citizen_platform/base.py` | 39 | `lab_id` | **RETAIN** | `def lab_id(self):` |
| `backend/app/citizen_platform/laboratory.py` | 17 | `lab_id` | **RETAIN** | `lab_id: str = ""` |
| `backend/app/citizen_platform/laboratory.py` | 39 | `lab_id` | **RETAIN** | `lab_id: str \| None = None,` |
| `backend/app/citizen_platform/laboratory.py` | 47 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/citizen_platform/laboratory.py` | 48 | `lab_id` | **RETAIN** | `results = [r for r in results if r.lab_id == lab_id]` |
| `backend/app/citizen_platform/laboratory.py` | 48 | `lab_id` | **RETAIN** | `results = [r for r in results if r.lab_id == lab_id]` |
| `backend/app/citizen_platform/laboratory.py` | 74 | `lab_id` | **RETAIN** | `if r.lab_id not in seen:` |
| `backend/app/citizen_platform/laboratory.py` | 75 | `lab_id` | **RETAIN** | `seen[r.lab_id] = {"lab_id": r.lab_id, "lab_name": r.lab_name, "result_count": 0}` |
| `backend/app/citizen_platform/laboratory.py` | 75 | `lab_id` | **RETAIN** | `seen[r.lab_id] = {"lab_id": r.lab_id, "lab_name": r.lab_name, "result_count": 0}` |
| `backend/app/citizen_platform/laboratory.py` | 75 | `lab_id` | **RETAIN** | `seen[r.lab_id] = {"lab_id": r.lab_id, "lab_name": r.lab_name, "result_count": 0}` |
| `backend/app/citizen_platform/laboratory.py` | 76 | `lab_id` | **RETAIN** | `seen[r.lab_id]["result_count"] += 1` |
| `backend/app/citizen_platform/routes.py` | 14 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/citizen_platform/routes.py` | 34 | `LabUser` | **RETAIN** | `def _source_filter(current_user: User \| LabUser):` |
| `backend/app/citizen_platform/routes.py` | 37 | `LabUser` | **RETAIN** | `if isinstance(current_user, LabUser):` |
| `backend/app/citizen_platform/routes.py` | 38 | `legacy_lab_user_id` | **RETAIN** | `return CitizenRelationship.legacy_lab_user_id == current_user.id` |
| `backend/app/citizen_platform/routes.py` | 45 | `LabUser` | **RETAIN** | `current_user: User \| LabUser,` |
| `backend/app/citizen_platform/routes.py` | 65 | `LabUser` | **RETAIN** | `current_user: User \| LabUser = Depends(get_current_user),` |
| `backend/app/citizen_platform/routes.py` | 193 | `lab_id` | **RETAIN** | `lab_id: str \| None = Query(None),` |
| `backend/app/citizen_platform/routes.py` | 202 | `lab_id` | **RETAIN** | `relationship.citizen_id, lab_id=lab_id, status=status, skip=skip, limit=limit,` |
| `backend/app/citizen_platform/routes.py` | 202 | `lab_id` | **RETAIN** | `relationship.citizen_id, lab_id=lab_id, status=status, skip=skip, limit=limit,` |
| `backend/app/citizen_platform/routes.py` | 294 | `lab_id` | **RETAIN** | `lab_id: str \| None = Query(None),` |
| `backend/app/citizen_platform/routes.py` | 302 | `lab_id` | **RETAIN** | `citizen_id, lab_id=lab_id, status=status, skip=skip, limit=limit,` |
| `backend/app/citizen_platform/routes.py` | 302 | `lab_id` | **RETAIN** | `citizen_id, lab_id=lab_id, status=status, skip=skip, limit=limit,` |
| `backend/app/command_intelligence/engine.py` | 98 | `lab_id` | **RETAIN** | `"lab_id": kpi.lab_id,` |
| `backend/app/command_intelligence/engine.py` | 98 | `lab_id` | **RETAIN** | `"lab_id": kpi.lab_id,` |
| `backend/app/command_intelligence/models.py` | 45 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)` |
| `backend/app/command_intelligence/models.py` | 105 | `LabUser` | **RETAIN** | `creator = relationship("LabUser", foreign_keys=[created_by])` |
| `backend/app/command_intelligence/models.py` | 106 | `LabUser` | **RETAIN** | `reviewer = relationship("LabUser", foreign_keys=[reviewed_by])` |
| `backend/app/command_intelligence/routes.py` | 13 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/command_intelligence/routes.py` | 43 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/command_intelligence/routes.py` | 52 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/command_intelligence/routes.py` | 70 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/command_intelligence/routes.py` | 87 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/command_intelligence/routes.py` | 100 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("system:admin")),` |
| `backend/app/command_intelligence/routes.py` | 134 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/command_intelligence/routes.py` | 147 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("system:admin")),` |
| `backend/app/command_intelligence/routes.py` | 157 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/command_intelligence/routes.py` | 181 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/contracts/events.py` | 9 | `lab_id` | **RETAIN** | `"required": ["patient_id", "lab_id", "full_name", "phone"],` |
| `backend/app/contracts/events.py` | 12 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer", "description": "Tenant lab ID"},` |
| `backend/app/contracts/events.py` | 33 | `lab_id` | **RETAIN** | `"required": ["patient_id", "lab_id"],` |
| `backend/app/contracts/events.py` | 36 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 53 | `lab_id` | **RETAIN** | `"required": ["survivor_patient_id", "merged_patient_ids", "lab_id"],` |
| `backend/app/contracts/events.py` | 57 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 70 | `lab_id` | **RETAIN** | `"required": ["order_id", "patient_id", "lab_id", "status"],` |
| `backend/app/contracts/events.py` | 74 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 95 | `lab_id` | **RETAIN** | `"required": ["order_id", "lab_id"],` |
| `backend/app/contracts/events.py` | 98 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 113 | `lab_id` | **RETAIN** | `"required": ["order_id", "lab_id", "completed_at"],` |
| `backend/app/contracts/events.py` | 116 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 130 | `lab_id` | **RETAIN** | `"required": ["order_id", "lab_id", "validated_by"],` |
| `backend/app/contracts/events.py` | 133 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 134 | `LabUser` | **RETAIN** | `"validated_by": {"type": "integer", "description": "LabUser ID who validated"},` |
| `backend/app/contracts/events.py` | 147 | `lab_id` | **RETAIN** | `"required": ["order_id", "lab_id", "cancelled_by"],` |
| `backend/app/contracts/events.py` | 150 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 165 | `lab_id` | **RETAIN** | `"required": ["result_id", "order_id", "test_name", "lab_id"],` |
| `backend/app/contracts/events.py` | 170 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 191 | `lab_id` | **RETAIN** | `"required": ["result_id", "order_id", "lab_id"],` |
| `backend/app/contracts/events.py` | 195 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 213 | `lab_id` | **RETAIN** | `"required": ["alert_id", "result_id", "order_id", "lab_id"],` |
| `backend/app/contracts/events.py` | 219 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 324 | `lab_id` | **RETAIN** | `"required": ["lab_id", "lab_name"],` |
| `backend/app/contracts/events.py` | 326 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 332 | `lab_id` | **RETAIN** | `"correlation_id": "lab_id",` |
| `backend/app/contracts/events.py` | 341 | `lab_id` | **RETAIN** | `"required": ["lab_id"],` |
| `backend/app/contracts/events.py` | 343 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 348 | `lab_id` | **RETAIN** | `"correlation_id": "lab_id",` |
| `backend/app/contracts/events.py` | 362 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/contracts/events.py` | 495 | `lab_id` | **RETAIN** | `"lab_id": {"type": "integer"},` |
| `backend/app/control_plane/audit.py` | 37 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/control_plane/audit.py` | 46 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/control_plane/audit.py` | 46 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/control_plane/audit.py` | 55 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/control_plane/audit.py` | 65 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/control_plane/audit.py` | 65 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/control_plane/digital_twin/engine.py` | 78 | `lab_id` | **RETAIN** | `def get_laboratory(self, lab_id: str) -> LaboratoryTwin \| None:` |
| `backend/app/control_plane/digital_twin/engine.py` | 79 | `lab_id` | **RETAIN** | `return self._laboratories.get(lab_id)` |
| `backend/app/control_plane/digital_twin/models.py` | 54 | `lab_id` | **RETAIN** | `lab_id: str = ""` |
| `backend/app/core/ai_dataset_flags.py` | 30 | `lab_id` | **RETAIN** | ```anonymous_session_id`` (a hashed token) and ``lab_id`` from the` |
| `backend/app/core/bootstrap/demo_data.py` | 17 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/core/bootstrap/demo_data.py` | 103 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/core/bootstrap/demo_data.py` | 116 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.email == td["email"]).first()` |
| `backend/app/core/bootstrap/demo_data.py` | 116 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.email == td["email"]).first()` |
| `backend/app/core/bootstrap/demo_data.py` | 118 | `LabUser` | **RETAIN** | `tech = LabUser(` |
| `backend/app/core/bootstrap/demo_data.py` | 119 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/core/bootstrap/demo_data.py` | 131 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.email == dd["email"]).first()` |
| `backend/app/core/bootstrap/demo_data.py` | 131 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.email == dd["email"]).first()` |
| `backend/app/core/bootstrap/demo_data.py` | 133 | `LabUser` | **RETAIN** | `doctor = LabUser(` |
| `backend/app/core/bootstrap/demo_data.py` | 134 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/core/bootstrap/demo_data.py` | 145 | `lab_id` | **RETAIN** | `patients = db.query(Patient).filter(Patient.lab_id == lab.id).all()` |
| `backend/app/core/bootstrap/demo_data.py` | 151 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab.id,` |
| `backend/app/core/bootstrap/demo_data.py` | 159 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/core/bootstrap/departments.py` | 51 | `lab_id` | **RETAIN** | `Department.lab_id == lab.id,` |
| `backend/app/core/bootstrap/departments.py` | 57 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/core/bootstrap/master_admin.py` | 12 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/core/bootstrap/master_admin.py` | 39 | `LabUser` | **RETAIN** | `def _ensure_master_admin(db: Session) -> LabUser \| None:` |
| `backend/app/core/bootstrap/master_admin.py` | 40 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.role == "master_admin").first()` |
| `backend/app/core/bootstrap/master_admin.py` | 40 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.role == "master_admin").first()` |
| `backend/app/core/bootstrap/master_admin.py` | 46 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/core/bootstrap/master_admin.py` | 47 | `LabUser` | **RETAIN** | `.filter(LabUser.national_id_hash == nid_hash, LabUser.id != existing.id)` |
| `backend/app/core/bootstrap/master_admin.py` | 47 | `LabUser` | **RETAIN** | `.filter(LabUser.national_id_hash == nid_hash, LabUser.id != existing.id)` |
| `backend/app/core/bootstrap/master_admin.py` | 77 | `LabUser` | **RETAIN** | `user = LabUser(` |
| `backend/app/core/bootstrap/master_admin.py` | 78 | `lab_id` | **RETAIN** | `lab_id=platform_lab.id,` |
| `backend/app/core/bootstrap/subscriptions.py` | 69 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab.id,` |
| `backend/app/core/bootstrap/subscriptions.py` | 76 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/core/bootstrap/subscriptions.py` | 109 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/core/bootstrap/subscriptions.py` | 119 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/core/bootstrap/subscriptions.py` | 119 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/core/bootstrap/subscriptions.py` | 130 | `lab_id` | **RETAIN** | `lab_id, sub.tier, tier,` |
| `backend/app/core/bootstrap/subscriptions.py` | 136 | `lab_id` | **RETAIN** | `logger.info("Upgraded lab %d to tier '%s'", lab_id, tier)` |
| `backend/app/core/bootstrap/subscriptions.py` | 139 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/core/bootstrap/subscriptions.py` | 139 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/core/bootstrap/subscriptions.py` | 146 | `lab_id` | **RETAIN** | `logger.info("Created %s subscription for lab %d", tier, lab_id)` |
| `backend/app/core/bootstrap/users.py` | 10 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/core/bootstrap/users.py` | 116 | `LabUser` | **RETAIN** | `master_admin = db.query(LabUser).filter(` |
| `backend/app/core/bootstrap/users.py` | 117 | `LabUser` | **RETAIN** | `LabUser.role == MASTER_ADMIN_ROLE,` |
| `backend/app/core/bootstrap/users.py` | 118 | `LabUser` | **RETAIN** | `LabUser.lab_id == platform_lab.id,` |
| `backend/app/core/bootstrap/users.py` | 118 | `lab_id` | **RETAIN** | `LabUser.lab_id == platform_lab.id,` |
| `backend/app/core/bootstrap/users.py` | 126 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(` |
| `backend/app/core/bootstrap/users.py` | 127 | `LabUser` | **RETAIN** | `LabUser.email == resolved["email"],` |
| `backend/app/core/bootstrap/users.py` | 136 | `LabUser` | **RETAIN** | `user = LabUser(` |
| `backend/app/core/bootstrap/users.py` | 137 | `lab_id` | **RETAIN** | `lab_id=platform_lab.id,` |
| `backend/app/core/bootstrap/validation.py` | 11 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/core/bootstrap/validation.py` | 129 | `LabUser` | **RETAIN** | `users = db.query(LabUser).count()` |
| `backend/app/core/bootstrap/validation.py` | 135 | `LabUser` | **RETAIN** | `master = db.query(LabUser).filter(LabUser.role == "master_admin").first()` |
| `backend/app/core/bootstrap/validation.py` | 135 | `LabUser` | **RETAIN** | `master = db.query(LabUser).filter(LabUser.role == "master_admin").first()` |
| `backend/app/core/bootstrap/validation.py` | 143 | `LabUser` | **RETAIN** | `count = db.query(LabUser).filter(LabUser.role == role).count()` |
| `backend/app/core/bootstrap/validation.py` | 143 | `LabUser` | **RETAIN** | `count = db.query(LabUser).filter(LabUser.role == role).count()` |
| `backend/app/core/bootstrap/validation.py` | 224 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/core/bootstrap/validation.py` | 225 | `LabUser` | **RETAIN** | `.filter(LabUser.lab_id.isnot(None))` |
| `backend/app/core/bootstrap/validation.py` | 225 | `lab_id` | **RETAIN** | `.filter(LabUser.lab_id.isnot(None))` |
| `backend/app/core/bootstrap/validation.py` | 235 | `lab_id` | **RETAIN** | `.filter(LabSubscription.lab_id.isnot(None))` |
| `backend/app/core/cache_manager.py` | 515 | `lab_id` | **RETAIN** | `@cached(ttl=600, key_fn=lambda lab_id, status: f"gula:lab:{lab_id}:orders:{status}")` |
| `backend/app/core/cache_manager.py` | 515 | `lab_id` | **RETAIN** | `@cached(ttl=600, key_fn=lambda lab_id, status: f"gula:lab:{lab_id}:orders:{status}")` |
| `backend/app/core/cache_manager.py` | 516 | `lab_id` | **RETAIN** | `async def get_orders(lab_id: int, status: str) -> list: ...` |
| `backend/app/core/feature_flags.py` | 174 | `lab_id` | **RETAIN** | `def resolve_lab_features(lab_id: int, db) -> frozenset[str]:` |
| `backend/app/core/feature_flags.py` | 189 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/core/feature_flags.py` | 189 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/core/feature_flags.py` | 207 | `lab_id` | **RETAIN** | `flags = db.query(FeatureFlag).filter(FeatureFlag.lab_id == lab_id).all()` |
| `backend/app/core/feature_flags.py` | 207 | `lab_id` | **RETAIN** | `flags = db.query(FeatureFlag).filter(FeatureFlag.lab_id == lab_id).all()` |
| `backend/app/core/feature_flags.py` | 220 | `lab_id` | **RETAIN** | `def require_feature(feature: str, lab_id: int, db):` |
| `backend/app/core/feature_flags.py` | 225 | `lab_id` | **RETAIN** | `require_feature("ai_interpretation", current_user.lab_id, db)` |
| `backend/app/core/feature_flags.py` | 229 | `lab_id` | **RETAIN** | `features = resolve_lab_features(lab_id, db)` |
| `backend/app/core/feature_flags.py` | 232 | `lab_id` | **RETAIN** | `"[FEATURE GATE] lab_id=%s blocked from feature '%s' (not in tier)",` |
| `backend/app/core/feature_flags.py` | 233 | `lab_id` | **RETAIN** | `lab_id,` |
| `backend/app/core/feature_flags.py` | 249 | `lab_id` | **RETAIN** | `def can_lab_access(feature: str, lab_id: int, db) -> bool:` |
| `backend/app/core/feature_flags.py` | 251 | `lab_id` | **RETAIN** | `return feature in resolve_lab_features(lab_id, db)` |
| `backend/app/core/feature_flags.py` | 254 | `lab_id` | **RETAIN** | `def get_lab_subscription_info(lab_id: int, db) -> dict:` |
| `backend/app/core/feature_flags.py` | 262 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/core/feature_flags.py` | 262 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/core/feature_flags.py` | 277 | `lab_id` | **RETAIN** | `features = resolve_lab_features(lab_id, db)` |
| `backend/app/core/idempotency.py` | 110 | `lab_id` | **RETAIN** | `_lab_id=getattr(current_user, "lab_id", None),` |
| `backend/app/core/idempotency.py` | 118 | `lab_id` | **RETAIN** | `lab_id = getattr(current_user, "lab_id", None)` |
| `backend/app/core/idempotency.py` | 118 | `lab_id` | **RETAIN** | `lab_id = getattr(current_user, "lab_id", None)` |
| `backend/app/core/idempotency.py` | 129 | `lab_id` | **RETAIN** | `AND (lab_id = :lab_id OR lab_id IS NULL)` |
| `backend/app/core/idempotency.py` | 129 | `lab_id` | **RETAIN** | `AND (lab_id = :lab_id OR lab_id IS NULL)` |
| `backend/app/core/idempotency.py` | 129 | `lab_id` | **RETAIN** | `AND (lab_id = :lab_id OR lab_id IS NULL)` |
| `backend/app/core/idempotency.py` | 132 | `lab_id` | **RETAIN** | `{"key": key, "lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/core/idempotency.py` | 132 | `lab_id` | **RETAIN** | `{"key": key, "lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/core/idempotency.py` | 138 | `lab_id` | **RETAIN** | `logger.info("[IDEMPOTENCY] duplicate request detected key=%s lab=%s", key, lab_id)` |
| `backend/app/core/idempotency.py` | 144 | `lab_id` | **RETAIN** | `_lab_id=lab_id,` |
| `backend/app/core/idempotency.py` | 152 | `lab_id` | **RETAIN** | `INSERT INTO idempotency_keys (key, lab_id, created_at)` |
| `backend/app/core/idempotency.py` | 153 | `lab_id` | **RETAIN** | `VALUES (:key, :lab_id, :now)` |
| `backend/app/core/idempotency.py` | 156 | `lab_id` | **RETAIN** | `{"key": key, "lab_id": lab_id, "now": datetime.now(UTC)},` |
| `backend/app/core/idempotency.py` | 156 | `lab_id` | **RETAIN** | `{"key": key, "lab_id": lab_id, "now": datetime.now(UTC)},` |
| `backend/app/core/idempotency.py` | 167 | `lab_id` | **RETAIN** | `_lab_id=lab_id,` |
| `backend/app/core/seeds.py` | 20 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/core/seeds.py` | 64 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.role == "master_admin").first()` |
| `backend/app/core/seeds.py` | 64 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.role == "master_admin").first()` |
| `backend/app/core/seeds.py` | 87 | `LabUser` | **RETAIN** | `existing = LabUser(` |
| `backend/app/core/seeds.py` | 88 | `lab_id` | **RETAIN** | `lab_id=platform_lab.id,` |
| `backend/app/core/seeds.py` | 104 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/core/seeds.py` | 106 | `LabUser` | **RETAIN** | `LabUser.national_id_hash == nid_hash,` |
| `backend/app/core/seeds.py` | 107 | `LabUser` | **RETAIN** | `LabUser.id != existing.id,` |
| `backend/app/core/seeds.py` | 143 | `lab_id` | **RETAIN** | `.outerjoin(LabSubscription, Lab.id == LabSubscription.lab_id)` |
| `backend/app/core/seeds.py` | 149 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/database.py` | 19 | `lab_id` | **RETAIN** | `#   user_id + lab_id        ← set by get_current_user dependency (authenticated routes)` |
| `backend/app/database.py` | 23 | `lab_id` | **RETAIN** | `_lab_id_var: contextvars.ContextVar[int \| None] = contextvars.ContextVar("lab_id", default=None)` |
| `backend/app/database.py` | 378 | `lab_id` | **RETAIN** | `# endpoint) and by get_current_user dependency (user_id, lab_id).` |
| `backend/app/database.py` | 382 | `lab_id` | **RETAIN** | `lab_id = _lab_id_var.get(None)` |
| `backend/app/database.py` | 397 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/database.py` | 397 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/document_intelligence/api/routes.py` | 59 | `lab_id` | **RETAIN** | `lab_id: str \| None = Query(None),` |
| `backend/app/document_intelligence/api/routes.py` | 71 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/document_intelligence/api/routes.py` | 72 | `lab_id` | **RETAIN** | `meta["lab_id"] = lab_id` |
| `backend/app/document_intelligence/api/routes.py` | 72 | `lab_id` | **RETAIN** | `meta["lab_id"] = lab_id` |
| `backend/app/document_intelligence/api/routes.py` | 181 | `lab_id` | **RETAIN** | `lab_id: UUID \| None = Query(None),` |
| `backend/app/document_intelligence/api/routes.py` | 194 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/document_intelligence/api/routes.py` | 194 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/document_intelligence/domain/entities.py` | 38 | `lab_id` | **RETAIN** | `lab_id: UUID \| None = None` |
| `backend/app/document_intelligence/domain/repository.py` | 57 | `lab_id` | **RETAIN** | `lab_id: UUID \| None = None,` |
| `backend/app/document_intelligence/infrastructure/models.py` | 74 | `lab_id` | **RETAIN** | `lab_id = Column(UUID(as_uuid=True), nullable=True, index=True)` |
| `backend/app/document_intelligence/infrastructure/models.py` | 116 | `lab_id` | **RETAIN** | `lab_id=self.lab_id,` |
| `backend/app/document_intelligence/infrastructure/models.py` | 116 | `lab_id` | **RETAIN** | `lab_id=self.lab_id,` |
| `backend/app/document_intelligence/infrastructure/models.py` | 146 | `lab_id` | **RETAIN** | `lab_id=doc.lab_id,` |
| `backend/app/document_intelligence/infrastructure/models.py` | 146 | `lab_id` | **RETAIN** | `lab_id=doc.lab_id,` |
| `backend/app/document_intelligence/infrastructure/repository.py` | 133 | `lab_id` | **RETAIN** | `lab_id: UUID \| None = None,` |
| `backend/app/document_intelligence/infrastructure/repository.py` | 145 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/document_intelligence/infrastructure/repository.py` | 146 | `lab_id` | **RETAIN** | `filters.append(ScannedDocumentModel.lab_id == lab_id)` |
| `backend/app/document_intelligence/infrastructure/repository.py` | 146 | `lab_id` | **RETAIN** | `filters.append(ScannedDocumentModel.lab_id == lab_id)` |
| `backend/app/document_intelligence/multitenancy.py` | 19 | `lab_id` | **RETAIN** | `lab_id: uuid.UUID \| None = None` |
| `backend/app/document_intelligence/multitenancy.py` | 39 | `lab_id` | **RETAIN** | `def set_lab_id(lab_id: uuid.UUID):` |
| `backend/app/document_intelligence/multitenancy.py` | 40 | `lab_id` | **RETAIN** | `current_lab_id.set(lab_id)` |
| `backend/app/edge/__init__.py` | 11 | `lab_id` | **RETAIN** | `- Tenant-isolated — every record is scoped to a lab_id` |
| `backend/app/edge/governance.py` | 9 | `lab_id` | **RETAIN** | `1. lab-scoped assignments (edge_model_assignments where lab_id == device.lab_id)` |
| `backend/app/edge/governance.py` | 9 | `lab_id` | **RETAIN** | `1. lab-scoped assignments (edge_model_assignments where lab_id == device.lab_id)` |
| `backend/app/edge/governance.py` | 10 | `lab_id` | **RETAIN** | `2. global assignments (lab_id IS NULL)` |
| `backend/app/edge/governance.py` | 130 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/edge/governance.py` | 134 | `lab_id` | **RETAIN** | `"""Pin a model to a lab or specific device. lab_id NULL = global.` |
| `backend/app/edge/governance.py` | 143 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/governance.py` | 143 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/governance.py` | 150 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/governance.py` | 150 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/governance.py` | 186 | `lab_id` | **RETAIN** | `EdgeModelAssignment.lab_id == device.lab_id,` |
| `backend/app/edge/governance.py` | 186 | `lab_id` | **RETAIN** | `EdgeModelAssignment.lab_id == device.lab_id,` |
| `backend/app/edge/governance.py` | 187 | `lab_id` | **RETAIN** | `EdgeModelAssignment.lab_id.is_(None),` |
| `backend/app/edge/maintenance.py` | 88 | `lab_id` | **RETAIN** | `lab_id=d.lab_id,` |
| `backend/app/edge/maintenance.py` | 88 | `lab_id` | **RETAIN** | `lab_id=d.lab_id,` |
| `backend/app/edge/policy.py` | 6 | `lab_id` | **RETAIN** | `3. Global default row (lab_id IS NULL)` |
| `backend/app/edge/policy.py` | 76 | `lab_id` | **RETAIN** | `def get_policy(db: Session, lab_id: int \| None) -> ResolvedPolicy:` |
| `backend/app/edge/policy.py` | 77 | `lab_id` | **RETAIN** | `"""Return the resolved policy for `lab_id` (None → global default row)."""` |
| `backend/app/edge/policy.py` | 79 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/edge/policy.py` | 80 | `lab_id` | **RETAIN** | `row = db.query(EdgePolicy).filter(EdgePolicy.lab_id == lab_id).first()` |
| `backend/app/edge/policy.py` | 80 | `lab_id` | **RETAIN** | `row = db.query(EdgePolicy).filter(EdgePolicy.lab_id == lab_id).first()` |
| `backend/app/edge/policy.py` | 82 | `lab_id` | **RETAIN** | `row = db.query(EdgePolicy).filter(EdgePolicy.lab_id.is_(None)).first()` |
| `backend/app/edge/policy.py` | 95 | `lab_id` | **RETAIN** | `lab_id: int \| None,` |
| `backend/app/edge/policy.py` | 104 | `lab_id` | **RETAIN** | `row = db.query(EdgePolicy).filter(EdgePolicy.lab_id == lab_id).first()` |
| `backend/app/edge/policy.py` | 104 | `lab_id` | **RETAIN** | `row = db.query(EdgePolicy).filter(EdgePolicy.lab_id == lab_id).first()` |
| `backend/app/edge/policy.py` | 106 | `lab_id` | **RETAIN** | `row = EdgePolicy(lab_id=lab_id)` |
| `backend/app/edge/policy.py` | 106 | `lab_id` | **RETAIN** | `row = EdgePolicy(lab_id=lab_id)` |
| `backend/app/edge/registry.py` | 34 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/edge/registry.py` | 51 | `lab_id` | **RETAIN** | `pol = policy_mod.get_policy(db, lab_id)` |
| `backend/app/edge/registry.py` | 58 | `lab_id` | **RETAIN** | `EdgeDevice.lab_id == lab_id, EdgeDevice.status.in_(("active", "pending", "quarantined")),` |
| `backend/app/edge/registry.py` | 58 | `lab_id` | **RETAIN** | `EdgeDevice.lab_id == lab_id, EdgeDevice.status.in_(("active", "pending", "quarantined")),` |
| `backend/app/edge/registry.py` | 72 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/registry.py` | 72 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/registry.py` | 91 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/registry.py` | 91 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/registry.py` | 141 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 141 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 159 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 159 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 174 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 174 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 192 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 192 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 207 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 207 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/registry.py` | 224 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/edge/registry.py` | 229 | `lab_id` | **RETAIN** | `.filter(EdgeDevice.device_id == device_id, EdgeDevice.lab_id == lab_id)` |
| `backend/app/edge/registry.py` | 229 | `lab_id` | **RETAIN** | `.filter(EdgeDevice.device_id == device_id, EdgeDevice.lab_id == lab_id)` |
| `backend/app/edge/scheduler.py` | 4 | `lab_id` | **RETAIN** | `- Tenant isolation:   task.lab_id == device.lab_id` |
| `backend/app/edge/scheduler.py` | 4 | `lab_id` | **RETAIN** | `- Tenant isolation:   task.lab_id == device.lab_id` |
| `backend/app/edge/scheduler.py` | 50 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/edge/scheduler.py` | 74 | `lab_id` | **RETAIN** | `pol = policy_mod.get_policy(db, lab_id)` |
| `backend/app/edge/scheduler.py` | 84 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == lab_id,` |
| `backend/app/edge/scheduler.py` | 84 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == lab_id,` |
| `backend/app/edge/scheduler.py` | 99 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/scheduler.py` | 99 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/scheduler.py` | 120 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/scheduler.py` | 120 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/scheduler.py` | 138 | `lab_id` | **RETAIN** | `if device.lab_id != task.lab_id:` |
| `backend/app/edge/scheduler.py` | 138 | `lab_id` | **RETAIN** | `if device.lab_id != task.lab_id:` |
| `backend/app/edge/scheduler.py` | 172 | `lab_id` | **RETAIN** | `pol = policy_mod.get_policy(db, device.lab_id)` |
| `backend/app/edge/scheduler.py` | 185 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == device.lab_id,` |
| `backend/app/edge/scheduler.py` | 185 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == device.lab_id,` |
| `backend/app/edge/scheduler.py` | 228 | `lab_id` | **RETAIN** | `lab_id=task.lab_id,` |
| `backend/app/edge/scheduler.py` | 228 | `lab_id` | **RETAIN** | `lab_id=task.lab_id,` |
| `backend/app/edge/scheduler.py` | 249 | `lab_id` | **RETAIN** | `lab_id=task.lab_id,` |
| `backend/app/edge/scheduler.py` | 249 | `lab_id` | **RETAIN** | `lab_id=task.lab_id,` |
| `backend/app/edge/scheduler.py` | 271 | `lab_id` | **RETAIN** | `lab_id=task.lab_id,` |
| `backend/app/edge/scheduler.py` | 271 | `lab_id` | **RETAIN** | `lab_id=task.lab_id,` |
| `backend/app/edge/telemetry.py` | 24 | `lab_id` | **RETAIN** | `def record(db: Session, *, lab_id: int, device_id: str, sample: dict[str, Any]) -> None:` |
| `backend/app/edge/telemetry.py` | 47 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/telemetry.py` | 47 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/edge/telemetry.py` | 55 | `lab_id` | **RETAIN** | `def latest(db: Session, *, device_id: str, lab_id: int) -> EdgeTelemetry \| None:` |
| `backend/app/edge/telemetry.py` | 58 | `lab_id` | **RETAIN** | `.filter(EdgeTelemetry.device_id == device_id, EdgeTelemetry.lab_id == lab_id)` |
| `backend/app/edge/telemetry.py` | 58 | `lab_id` | **RETAIN** | `.filter(EdgeTelemetry.device_id == device_id, EdgeTelemetry.lab_id == lab_id)` |
| `backend/app/edge/telemetry.py` | 68 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/edge/telemetry.py` | 77 | `lab_id` | **RETAIN** | `EdgeTelemetry.lab_id == lab_id,` |
| `backend/app/edge/telemetry.py` | 77 | `lab_id` | **RETAIN** | `EdgeTelemetry.lab_id == lab_id,` |
| `backend/app/edge/telemetry.py` | 86 | `lab_id` | **RETAIN** | `def fleet_summary(db: Session, *, lab_id: int) -> dict[str, Any]:` |
| `backend/app/edge/telemetry.py` | 91 | `lab_id` | **RETAIN** | `.filter(EdgeTelemetry.lab_id == lab_id, EdgeTelemetry.ts >= cutoff)` |
| `backend/app/edge/telemetry.py` | 91 | `lab_id` | **RETAIN** | `.filter(EdgeTelemetry.lab_id == lab_id, EdgeTelemetry.ts >= cutoff)` |
| `backend/app/edge/trust.py` | 61 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/trust.py` | 61 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/trust.py` | 83 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/trust.py` | 83 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/trust.py` | 94 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/edge/trust.py` | 94 | `lab_id` | **RETAIN** | `lab_id=device.lab_id,` |
| `backend/app/ehr/clinical_read_gate.py` | 13 | `LegacyAccountLink` | **RETAIN** | `from app.identity.models.legacy_account_link import LegacyAccountLink` |
| `backend/app/ehr/clinical_read_gate.py` | 32 | `legacy_lab_id` | **RETAIN** | `legacy_lab_id: int` |
| `backend/app/ehr/clinical_read_gate.py` | 60 | `LegacyAccountLink` | **RETAIN** | `db.query(LegacyAccountLink)` |
| `backend/app/ehr/clinical_read_gate.py` | 62 | `LegacyAccountLink` | **RETAIN** | `LegacyAccountLink.source_kind == "lab_user",` |
| `backend/app/ehr/clinical_read_gate.py` | 63 | `LegacyAccountLink` | **RETAIN** | `LegacyAccountLink.legacy_account_id == lab_user.id,` |
| `backend/app/ehr/clinical_read_gate.py` | 64 | `LegacyAccountLink` | **RETAIN** | `LegacyAccountLink.status == "migrated",` |
| `backend/app/ehr/clinical_read_gate.py` | 80 | `legacy_lab_id` | **RETAIN** | `ClinicalLabFacilityBinding.legacy_lab_id == lab_user.lab_id,` |
| `backend/app/ehr/clinical_read_gate.py` | 80 | `lab_id` | **RETAIN** | `ClinicalLabFacilityBinding.legacy_lab_id == lab_user.lab_id,` |
| `backend/app/ehr/clinical_read_gate.py` | 141 | `legacy_lab_id` | **RETAIN** | `legacy_lab_id=lab_user.lab_id,` |
| `backend/app/ehr/clinical_read_gate.py` | 141 | `lab_id` | **RETAIN** | `legacy_lab_id=lab_user.lab_id,` |
| `backend/app/ehr/clinical_read_gate.py` | 167 | `lab_id` | **RETAIN** | `"lab_id": getattr(lab_user, "lab_id", None),` |
| `backend/app/ehr/clinical_read_gate.py` | 167 | `lab_id` | **RETAIN** | `"lab_id": getattr(lab_user, "lab_id", None),` |
| `backend/app/factory.py` | 193 | `LabUser` | **RETAIN** | `LabUser,` |
| `backend/app/fhir/_capabilities.py` | 36 | `lab_id` | **RETAIN** | `"description": "All FHIR endpoints require JWT Bearer authentication. Tenant isolation enforced via lab_id claims.",` |
| `backend/app/fhir/_scorecard.py` | 21 | `lab_id` | **RETAIN** | `"evidence": "13 security modules (JWT, RBAC, ABAC, MFA, OAuth2, SAML, encryption, rate limit, session), security header middleware, startup guard with secret validation, CI runs safety+bandit+gitleaks, FHIR quality gate passes, tenant isola` |
| `backend/app/fhir/_scorecard.py` | 51 | `lab_id` | **RETAIN** | `"evidence": "Multi-tenant (lab_id), RBAC (9 roles, 13 permissions), ABAC, consent management, audit logging with hash chain, rate limiting, OAuth2/SAML/MFA, feature flags (per-tenant + deployment-wide), SNDHS national integration, FHIR R4 i` |
| `backend/app/fhir/_validation_report.py` | 47 | `lab_id` | **RETAIN** | `"Tenant isolation (lab_id filter) enforced on all resource queries",` |
| `backend/app/financial/models.py` | 27 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/financial/models.py` | 73 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/financial/models.py` | 101 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/financial/models.py` | 114 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/financial/ranking.py` | 13 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/financial/ranking.py` | 96 | `lab_id` | **RETAIN** | `owner_key = str(lab.lab_id // 1000)  # group by owner prefix` |
| `backend/app/financial/routes.py` | 15 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/financial/routes.py` | 44 | `lab_id` | **RETAIN** | `def _get_provider(db: Session, lab_id: int) -> FinProvider:` |
| `backend/app/financial/routes.py` | 45 | `lab_id` | **RETAIN** | `provider = db.query(FinProvider).filter(FinProvider.lab_id == lab_id).first()` |
| `backend/app/financial/routes.py` | 45 | `lab_id` | **RETAIN** | `provider = db.query(FinProvider).filter(FinProvider.lab_id == lab_id).first()` |
| `backend/app/financial/routes.py` | 56 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 60 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()` |
| `backend/app/financial/routes.py` | 61 | `lab_id` | **RETAIN** | `provider = db.query(FinProvider).filter(FinProvider.lab_id == current_user.lab_id).first()` |
| `backend/app/financial/routes.py` | 61 | `lab_id` | **RETAIN** | `provider = db.query(FinProvider).filter(FinProvider.lab_id == current_user.lab_id).first()` |
| `backend/app/financial/routes.py` | 63 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/financial/routes.py` | 63 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/financial/routes.py` | 76 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 97 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 101 | `lab_id` | **RETAIN** | `return InvoiceService.list_invoices(db, current_user.lab_id, status, limit, offset)` |
| `backend/app/financial/routes.py` | 107 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 111 | `lab_id` | **RETAIN** | `invoice = InvoiceService.get_invoice(db, invoice_id, current_user.lab_id)` |
| `backend/app/financial/routes.py` | 123 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 129 | `lab_id` | **RETAIN** | `provider = _get_provider(db, current_user.lab_id)` |
| `backend/app/financial/routes.py` | 133 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 133 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 155 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 165 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 165 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 182 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 186 | `lab_id` | **RETAIN** | `return PaymentService.list_payments(db, current_user.lab_id, limit, offset)` |
| `backend/app/financial/routes.py` | 194 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 198 | `lab_id` | **RETAIN** | `return ReceivableService.get_receivables(db, current_user.lab_id)` |
| `backend/app/financial/routes.py` | 203 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 207 | `lab_id` | **RETAIN** | `return ReceivableService.get_aging_summary(db, current_user.lab_id)` |
| `backend/app/financial/routes.py` | 215 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 219 | `lab_id` | **RETAIN** | `provider = _get_provider(db, current_user.lab_id)` |
| `backend/app/financial/routes.py` | 230 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 234 | `lab_id` | **RETAIN** | `return PricingService.get_price(db, test_name, current_user.lab_id, quantity)` |
| `backend/app/financial/routes.py` | 244 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 265 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 294 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 300 | `lab_id` | **RETAIN** | `provider = _get_provider(db, current_user.lab_id)` |
| `backend/app/financial/routes.py` | 318 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 318 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 329 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 333 | `lab_id` | **RETAIN** | `provider = _get_provider(db, current_user.lab_id)` |
| `backend/app/financial/routes.py` | 362 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 373 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 373 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 387 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 396 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 396 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/financial/routes.py` | 407 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/financial/routes.py` | 411 | `lab_id` | **RETAIN** | `provider = _get_provider(db, current_user.lab_id)` |
| `backend/app/financial/schemas.py` | 13 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/financial/schemas.py` | 31 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/financial/schemas.py` | 81 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/financial/schemas.py` | 119 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/financial/schemas.py` | 126 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/financial/schemas.py` | 133 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/financial/services.py` | 69 | `lab_id` | **RETAIN** | `lab_id=provider.lab_id,` |
| `backend/app/financial/services.py` | 69 | `lab_id` | **RETAIN** | `lab_id=provider.lab_id,` |
| `backend/app/financial/services.py` | 87 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/financial/services.py` | 99 | `lab_id` | **RETAIN** | `.filter(FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 99 | `lab_id` | **RETAIN** | `.filter(FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 103 | `lab_id` | **RETAIN** | `invoice_number = f"INV-{lab_id:04d}-{invoice_count + 1:06d}"` |
| `backend/app/financial/services.py` | 106 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/financial/services.py` | 106 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/financial/services.py` | 141 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/financial/services.py` | 141 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/financial/services.py` | 152 | `lab_id` | **RETAIN** | `def get_invoice(db: Session, invoice_id: int, lab_id: int) -> dict[str, Any] \| None:` |
| `backend/app/financial/services.py` | 155 | `lab_id` | **RETAIN** | `.filter(FinInvoice.id == invoice_id, FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 155 | `lab_id` | **RETAIN** | `.filter(FinInvoice.id == invoice_id, FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 162 | `lab_id` | **RETAIN** | `"lab_id": invoice.lab_id,` |
| `backend/app/financial/services.py` | 162 | `lab_id` | **RETAIN** | `"lab_id": invoice.lab_id,` |
| `backend/app/financial/services.py` | 176 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, status: str \| None = None, limit: int = 50, offset: int = 0,` |
| `backend/app/financial/services.py` | 178 | `lab_id` | **RETAIN** | `q = db.query(FinInvoice).filter(FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 178 | `lab_id` | **RETAIN** | `q = db.query(FinInvoice).filter(FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 185 | `lab_id` | **RETAIN** | `"lab_id": inv.lab_id,` |
| `backend/app/financial/services.py` | 185 | `lab_id` | **RETAIN** | `"lab_id": inv.lab_id,` |
| `backend/app/financial/services.py` | 206 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/financial/services.py` | 220 | `lab_id` | **RETAIN** | `.filter(FinInvoice.id == invoice_id, FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 220 | `lab_id` | **RETAIN** | `.filter(FinInvoice.id == invoice_id, FinInvoice.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 229 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/financial/services.py` | 229 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/financial/services.py` | 285 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, limit: int = 50, offset: int = 0,` |
| `backend/app/financial/services.py` | 289 | `lab_id` | **RETAIN** | `.filter(FinPayment.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 289 | `lab_id` | **RETAIN** | `.filter(FinPayment.lab_id == lab_id)` |
| `backend/app/financial/services.py` | 313 | `lab_id` | **RETAIN** | `def get_receivables(db: Session, lab_id: int) -> list[dict[str, Any]]:` |
| `backend/app/financial/services.py` | 317 | `lab_id` | **RETAIN** | `FinInvoice.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 317 | `lab_id` | **RETAIN** | `FinInvoice.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 330 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/financial/services.py` | 330 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/financial/services.py` | 341 | `lab_id` | **RETAIN** | `def get_aging_summary(db: Session, lab_id: int) -> dict[str, Decimal]:` |
| `backend/app/financial/services.py` | 345 | `lab_id` | **RETAIN** | `FinInvoice.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 345 | `lab_id` | **RETAIN** | `FinInvoice.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 398 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/financial/services.py` | 467 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/financial/services.py` | 475 | `lab_id` | **RETAIN** | `FinInvoice.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 475 | `lab_id` | **RETAIN** | `FinInvoice.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 484 | `lab_id` | **RETAIN** | `FinPayment.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 484 | `lab_id` | **RETAIN** | `FinPayment.lab_id == lab_id,` |
| `backend/app/financial/services.py` | 497 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/financial/services.py` | 497 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/governance/models/laboratory.py` | 53 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)` |
| `backend/app/governance/models/laboratory.py` | 76 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)` |
| `backend/app/governance/models/laboratory.py` | 133 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)` |
| `backend/app/governance/models/laboratory.py` | 153 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)` |
| `backend/app/governance/models/laboratory.py` | 176 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)` |
| `backend/app/governance/models/laboratory.py` | 235 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("gov_laboratory_registry.id"), nullable=False, index=True)` |
| `backend/app/governance/routes/analytics_routes.py` | 24 | `lab_id` | **RETAIN** | `@router.get("/laboratory/{lab_id}")` |
| `backend/app/governance/routes/analytics_routes.py` | 25 | `lab_id` | **RETAIN** | `def lab_dashboard(lab_id: int, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/analytics_routes.py` | 27 | `lab_id` | **RETAIN** | `return svc.lab_dashboard(lab_id)` |
| `backend/app/governance/routes/governance_routes.py` | 404 | `lab_id` | **RETAIN** | `@router.get("/laboratories/{lab_id}")` |
| `backend/app/governance/routes/governance_routes.py` | 405 | `lab_id` | **RETAIN** | `def get_lab(lab_id: int, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 407 | `lab_id` | **RETAIN** | `lab = svc.get_lab(lab_id)` |
| `backend/app/governance/routes/governance_routes.py` | 413 | `lab_id` | **RETAIN** | `@router.get("/laboratories/{lab_id}/stats")` |
| `backend/app/governance/routes/governance_routes.py` | 414 | `lab_id` | **RETAIN** | `def get_lab_stats(lab_id: int, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 416 | `lab_id` | **RETAIN** | `return svc.get_lab_stats(lab_id)` |
| `backend/app/governance/routes/governance_routes.py` | 419 | `lab_id` | **RETAIN** | `@router.post("/laboratories/{lab_id}/equipment", dependencies=[elevated_dep])` |
| `backend/app/governance/routes/governance_routes.py` | 420 | `lab_id` | **RETAIN** | `def register_equipment(lab_id: int, equipment_code: str, name_ar: str, category: str, manufacturer: str \| None = None, model: str \| None = None, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 422 | `lab_id` | **RETAIN** | `equip = svc.register_equipment(lab_id, equipment_code, name_ar, category, manufacturer=manufacturer, model=model)` |
| `backend/app/governance/routes/governance_routes.py` | 427 | `lab_id` | **RETAIN** | `@router.post("/laboratories/{lab_id}/analyzers", dependencies=[elevated_dep])` |
| `backend/app/governance/routes/governance_routes.py` | 428 | `lab_id` | **RETAIN** | `def register_analyzer(lab_id: int, analyzer_code: str, name_ar: str, analyzer_type: str, manufacturer: str \| None = None, model: str \| None = None, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 430 | `lab_id` | **RETAIN** | `analyzer = svc.register_analyzer(lab_id, analyzer_code, name_ar, analyzer_type, manufacturer=manufacturer, model=model)` |
| `backend/app/governance/routes/governance_routes.py` | 435 | `lab_id` | **RETAIN** | `@router.post("/laboratories/{lab_id}/qc", dependencies=[elevated_dep])` |
| `backend/app/governance/routes/governance_routes.py` | 436 | `lab_id` | **RETAIN** | `def record_qc(lab_id: int, test_code: str, control_level: str, result_value: float, mean: float, sd: float, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 438 | `lab_id` | **RETAIN** | `qc = svc.record_qc(lab_id, test_code, control_level, result_value, mean=mean, sd=sd)` |
| `backend/app/governance/routes/governance_routes.py` | 443 | `lab_id` | **RETAIN** | `@router.post("/laboratories/{lab_id}/eqa", dependencies=[elevated_dep])` |
| `backend/app/governance/routes/governance_routes.py` | 444 | `lab_id` | **RETAIN** | `def record_eqa(lab_id: int, test_code: str, scheme_name: str, round_number: str, target_value: float, submitted_result: float, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 446 | `lab_id` | **RETAIN** | `eqa = svc.record_eqa(lab_id, test_code, scheme_name, round_number, submitted_result=submitted_result, target_value=target_value)` |
| `backend/app/governance/routes/governance_routes.py` | 451 | `lab_id` | **RETAIN** | `@router.post("/laboratories/{lab_id}/reagents", dependencies=[elevated_dep])` |
| `backend/app/governance/routes/governance_routes.py` | 452 | `lab_id` | **RETAIN** | `def add_reagent(lab_id: int, reagent_code: str, reagent_name_ar: str, quantity: float, unit: str, lot_number: str \| None = None, minimum_stock_level: float \| None = None, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 454 | `lab_id` | **RETAIN** | `reagent = svc.manage_reagent(lab_id, reagent_code, reagent_name_ar, quantity, unit, lot_number=lot_number, minimum_stock_level=minimum_stock_level)` |
| `backend/app/governance/routes/governance_routes.py` | 459 | `lab_id` | **RETAIN** | `@router.get("/laboratories/{lab_id}/low-stock")` |
| `backend/app/governance/routes/governance_routes.py` | 460 | `lab_id` | **RETAIN** | `def get_low_stock(lab_id: int, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 462 | `lab_id` | **RETAIN** | `return svc.get_low_stock_reagents(lab_id)` |
| `backend/app/governance/routes/governance_routes.py` | 480 | `lab_id` | **RETAIN** | `def designate_reference_lab(lab_id: int, reference_domain: str, is_national: bool = False, db: Session = Depends(get_db)):` |
| `backend/app/governance/routes/governance_routes.py` | 483 | `lab_id` | **RETAIN** | `ref = svc.designate_reference_lab(lab_id, reference_domain, is_national=is_national)` |
| `backend/app/governance/services/analytics_service.py` | 64 | `lab_id` | **RETAIN** | `def equipment_utilization(self, lab_id: int \| None = None) -> dict[str, Any]:` |
| `backend/app/governance/services/analytics_service.py` | 69 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/governance/services/analytics_service.py` | 70 | `lab_id` | **RETAIN** | `q = q.filter(EquipmentRegistry.lab_id == lab_id)` |
| `backend/app/governance/services/analytics_service.py` | 70 | `lab_id` | **RETAIN** | `q = q.filter(EquipmentRegistry.lab_id == lab_id)` |
| `backend/app/governance/services/analytics_service.py` | 95 | `lab_id` | **RETAIN** | `self, lab_id: int \| None = None, period: ProductivityPeriod = ProductivityPeriod.DAILY,` |
| `backend/app/governance/services/analytics_service.py` | 102 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/governance/services/analytics_service.py` | 104 | `lab_id` | **RETAIN** | `HealthcareWorker.organization_node_id == lab_id,` |
| `backend/app/governance/services/analytics_service.py` | 113 | `lab_id` | **RETAIN** | `def quality_indicators(self, lab_id: int \| None = None) -> dict[str, Any]:` |
| `backend/app/governance/services/analytics_service.py` | 115 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/governance/services/analytics_service.py` | 116 | `lab_id` | **RETAIN** | `q = q.filter(QCModRecord.lab_id == lab_id)` |
| `backend/app/governance/services/analytics_service.py` | 116 | `lab_id` | **RETAIN** | `q = q.filter(QCModRecord.lab_id == lab_id)` |
| `backend/app/governance/services/analytics_service.py` | 122 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/governance/services/analytics_service.py` | 123 | `lab_id` | **RETAIN** | `eq = eq.filter(EQARecord.lab_id == lab_id)` |
| `backend/app/governance/services/analytics_service.py` | 123 | `lab_id` | **RETAIN** | `eq = eq.filter(EQARecord.lab_id == lab_id)` |
| `backend/app/governance/services/analytics_service.py` | 158 | `lab_id` | **RETAIN** | `def lab_dashboard(self, lab_id: int) -> dict[str, Any]:` |
| `backend/app/governance/services/analytics_service.py` | 159 | `lab_id` | **RETAIN** | `lab = self.db.query(LaboratoryRegistry).filter(LaboratoryRegistry.id == lab_id).first()` |
| `backend/app/governance/services/analytics_service.py` | 165 | `lab_id` | **RETAIN** | `"quality": self.quality_indicators(lab_id),` |
| `backend/app/governance/services/analytics_service.py` | 166 | `lab_id` | **RETAIN** | `"equipment": self.equipment_utilization(lab_id),` |
| `backend/app/governance/services/laboratory_service.py` | 59 | `lab_id` | **RETAIN** | `def get_lab(self, lab_id: int) -> LaboratoryRegistry \| None:` |
| `backend/app/governance/services/laboratory_service.py` | 60 | `lab_id` | **RETAIN** | `return self.db.query(LaboratoryRegistry).filter(LaboratoryRegistry.id == lab_id).first()` |
| `backend/app/governance/services/laboratory_service.py` | 86 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/governance/services/laboratory_service.py` | 98 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 98 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 115 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/governance/services/laboratory_service.py` | 128 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 128 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 196 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/governance/services/laboratory_service.py` | 217 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 217 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 236 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/governance/services/laboratory_service.py` | 260 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 260 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 279 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/governance/services/laboratory_service.py` | 293 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 293 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 363 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/governance/services/laboratory_service.py` | 372 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 372 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 383 | `lab_id` | **RETAIN** | `def get_lab_stats(self, lab_id: int) -> dict[str, Any]:` |
| `backend/app/governance/services/laboratory_service.py` | 385 | `lab_id` | **RETAIN** | `EquipmentRegistry.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 385 | `lab_id` | **RETAIN** | `EquipmentRegistry.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 389 | `lab_id` | **RETAIN** | `AnalyzerRegistry.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 389 | `lab_id` | **RETAIN** | `AnalyzerRegistry.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 393 | `lab_id` | **RETAIN** | `EQARecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 393 | `lab_id` | **RETAIN** | `EQARecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 397 | `lab_id` | **RETAIN** | `EQARecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 397 | `lab_id` | **RETAIN** | `EQARecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 400 | `lab_id` | **RETAIN** | `QCModRecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 400 | `lab_id` | **RETAIN** | `QCModRecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 404 | `lab_id` | **RETAIN** | `QCModRecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 404 | `lab_id` | **RETAIN** | `QCModRecord.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 407 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 407 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 412 | `lab_id` | **RETAIN** | `"reagent_count": self.db.query(ReagentInventory).filter(ReagentInventory.lab_id == lab_id).count(),` |
| `backend/app/governance/services/laboratory_service.py` | 412 | `lab_id` | **RETAIN** | `"reagent_count": self.db.query(ReagentInventory).filter(ReagentInventory.lab_id == lab_id).count(),` |
| `backend/app/governance/services/laboratory_service.py` | 415 | `lab_id` | **RETAIN** | `def get_low_stock_reagents(self, lab_id: int) -> list[ReagentInventory]:` |
| `backend/app/governance/services/laboratory_service.py` | 419 | `lab_id` | **RETAIN** | `ReagentInventory.lab_id == lab_id,` |
| `backend/app/governance/services/laboratory_service.py` | 419 | `lab_id` | **RETAIN** | `ReagentInventory.lab_id == lab_id,` |
| `backend/app/health_data/ods/models.py` | 42 | `lab_id` | **RETAIN** | `Index("ix_hd_ods_patient_summary_lab", "lab_id", "patient_id", unique=True),` |
| `backend/app/health_data/warehouse/models.py` | 81 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/health_data/warehouse/models.py` | 105 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/health_data/warehouse/models.py` | 150 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/health_data/warehouse/models.py` | 182 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/health_data/warehouse/models.py` | 217 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/identity/models/__init__.py` | 44 | `LegacyAccountLink` | **RETAIN** | `from .legacy_account_link import LegacyAccountLink, LegacyAccountLinkSource, LegacyAccountLinkStatus` |
| `backend/app/identity/models/__init__.py` | 44 | `LegacyAccountLink` | **RETAIN** | `from .legacy_account_link import LegacyAccountLink, LegacyAccountLinkSource, LegacyAccountLinkStatus` |
| `backend/app/identity/models/__init__.py` | 44 | `LegacyAccountLink` | **RETAIN** | `from .legacy_account_link import LegacyAccountLink, LegacyAccountLinkSource, LegacyAccountLinkStatus` |
| `backend/app/identity/models/__init__.py` | 99 | `LegacyAccountLink` | **RETAIN** | `"LegacyAccountLink",` |
| `backend/app/identity/models/__init__.py` | 100 | `LegacyAccountLink` | **RETAIN** | `"LegacyAccountLinkSource",` |
| `backend/app/identity/models/__init__.py` | 101 | `LegacyAccountLink` | **RETAIN** | `"LegacyAccountLinkStatus",` |
| `backend/app/identity/models/citizen_relationship.py` | 51 | `legacy_lab_user_id` | **RETAIN** | `legacy_lab_user_id = Column(` |
| `backend/app/identity/models/citizen_relationship.py` | 82 | `legacy_lab_user_id` | **RETAIN** | `"canonical_account_id IS NOT NULL OR legacy_user_id IS NOT NULL OR legacy_lab_user_id IS NOT NULL",` |
| `backend/app/identity/models/citizen_relationship.py` | 86 | `legacy_lab_user_id` | **RETAIN** | `"(source_kind = 'canonical_account' AND canonical_account_id IS NOT NULL AND legacy_user_id IS NULL AND legacy_lab_user_id IS NULL) OR "` |
| `backend/app/identity/models/citizen_relationship.py` | 87 | `legacy_lab_user_id` | **RETAIN** | `"(source_kind = 'legacy_user' AND legacy_user_id IS NOT NULL AND canonical_account_id IS NULL AND legacy_lab_user_id IS NULL) OR "` |
| `backend/app/identity/models/citizen_relationship.py` | 88 | `legacy_lab_user_id` | **RETAIN** | `"(source_kind = 'legacy_lab_user' AND legacy_lab_user_id IS NOT NULL AND canonical_account_id IS NULL AND legacy_user_id IS NULL)",` |
| `backend/app/identity/models/legacy_account_link.py` | 12 | `LegacyAccountLink` | **ADAPTER** | `class LegacyAccountLinkSource(StrEnum):` |
| `backend/app/identity/models/legacy_account_link.py` | 18 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountSource = LegacyAccountLinkSource` |
| `backend/app/identity/models/legacy_account_link.py` | 21 | `LegacyAccountLink` | **ADAPTER** | `class LegacyAccountLinkStatus(StrEnum):` |
| `backend/app/identity/models/legacy_account_link.py` | 30 | `LegacyAccountLink` | **ADAPTER** | `class LegacyAccountLink(IdentityBaseEntity):` |
| `backend/app/identity/models/legacy_account_link.py` | 45 | `LegacyAccountLink` | **ADAPTER** | `status = Column(String(20), nullable=False, default=LegacyAccountLinkStatus.pending.value, index=True)` |
| `backend/app/identity/models/legacy_account_link.py` | 53 | `LegacyAccountLink` | **ADAPTER** | `def transition(self, target: LegacyAccountLinkStatus, *, reason: str \| None = None) -> None:` |
| `backend/app/identity/models/legacy_account_link.py` | 55 | `LegacyAccountLink` | **ADAPTER** | `current = LegacyAccountLinkStatus(self.status)` |
| `backend/app/identity/models/legacy_account_link.py` | 56 | `LegacyAccountLink` | **ADAPTER** | `allowed: dict[LegacyAccountLinkStatus, set[LegacyAccountLinkStatus]] = {` |
| `backend/app/identity/models/legacy_account_link.py` | 56 | `LegacyAccountLink` | **ADAPTER** | `allowed: dict[LegacyAccountLinkStatus, set[LegacyAccountLinkStatus]] = {` |
| `backend/app/identity/models/legacy_account_link.py` | 57 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.pending: {` |
| `backend/app/identity/models/legacy_account_link.py` | 58 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.validated,` |
| `backend/app/identity/models/legacy_account_link.py` | 59 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.collision,` |
| `backend/app/identity/models/legacy_account_link.py` | 60 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.blocked,` |
| `backend/app/identity/models/legacy_account_link.py` | 62 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.validated: {` |
| `backend/app/identity/models/legacy_account_link.py` | 63 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.migrated,` |
| `backend/app/identity/models/legacy_account_link.py` | 64 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.collision,` |
| `backend/app/identity/models/legacy_account_link.py` | 65 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.blocked,` |
| `backend/app/identity/models/legacy_account_link.py` | 67 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.migrated: {LegacyAccountLinkStatus.rolled_back},` |
| `backend/app/identity/models/legacy_account_link.py` | 67 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.migrated: {LegacyAccountLinkStatus.rolled_back},` |
| `backend/app/identity/models/legacy_account_link.py` | 68 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.collision: {` |
| `backend/app/identity/models/legacy_account_link.py` | 69 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.pending,` |
| `backend/app/identity/models/legacy_account_link.py` | 70 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.blocked,` |
| `backend/app/identity/models/legacy_account_link.py` | 72 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.blocked: {LegacyAccountLinkStatus.pending},` |
| `backend/app/identity/models/legacy_account_link.py` | 72 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.blocked: {LegacyAccountLinkStatus.pending},` |
| `backend/app/identity/models/legacy_account_link.py` | 73 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.rolled_back: {LegacyAccountLinkStatus.pending},` |
| `backend/app/identity/models/legacy_account_link.py` | 73 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.rolled_back: {LegacyAccountLinkStatus.pending},` |
| `backend/app/identity/models/legacy_account_link.py` | 80 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.collision,` |
| `backend/app/identity/models/legacy_account_link.py` | 81 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.blocked,` |
| `backend/app/identity/models/legacy_account_link.py` | 84 | `LegacyAccountLink` | **ADAPTER** | `if target == LegacyAccountLinkStatus.rolled_back and not self.rollback_token:` |
| `backend/app/identity/models/legacy_account_link.py` | 90 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.collision,` |
| `backend/app/identity/models/legacy_account_link.py` | 91 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.blocked,` |
| `backend/app/identity/models/legacy_account_link.py` | 94 | `LegacyAccountLink` | **ADAPTER** | `elif target == LegacyAccountLinkStatus.pending:` |
| `backend/app/identity/models/legacy_account_link.py` | 97 | `LegacyAccountLink` | **ADAPTER** | `if target == LegacyAccountLinkStatus.validated:` |
| `backend/app/identity/models/legacy_account_link.py` | 99 | `LegacyAccountLink` | **ADAPTER** | `elif target == LegacyAccountLinkStatus.migrated:` |
| `backend/app/identity/models/legacy_account_link.py` | 101 | `LegacyAccountLink` | **ADAPTER** | `elif target == LegacyAccountLinkStatus.rolled_back:` |
| `backend/app/identity/services/citizen_relationship_service.py` | 20 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/identity/services/citizen_relationship_service.py` | 107 | `LabUser` | **RETAIN** | `def __init__(self, db: Session, actor: LabUser, request_ip: str \| None = None) -> None:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 13 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 14 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkSource,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 15 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 24 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalAuthorizationContextError(ValueError):` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 28 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalLegacyIdentityUnresolved(ClinicalAuthorizationContextError):` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 32 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalIdentityAssignmentMismatch(ClinicalAuthorizationContextError):` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 36 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalActiveAssignmentUnavailable(ClinicalAuthorizationContextError):` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 40 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalFacilityScopeMismatch(ClinicalAuthorizationContextError):` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 44 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalAuthorizationContextAmbiguous(ClinicalAuthorizationContextError):` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 44 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalAuthorizationContextAmbiguous(ClinicalAuthorizationContextError):` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 49 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalAuthorizationContext:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 52 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id: int` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 53 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id: int` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 64 | `ClinicalAuthorizationContext` | **ADAPTER** | `class ClinicalAuthorizationContextService:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 81 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id: int,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 82 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id: int,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 83 | `ClinicalAuthorizationContext` | **ADAPTER** | `) -> ClinicalAuthorizationContext:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 84 | `legacy_lab_user_id` | **ADAPTER** | `if legacy_lab_user_id <= 0 or legacy_lab_id <= 0:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 84 | `legacy_lab_id` | **ADAPTER** | `if legacy_lab_user_id <= 0 or legacy_lab_id <= 0:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 88 | `legacy_lab_user_id` | **ADAPTER** | `link = await self._get_migrated_link(legacy_lab_user_id)` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 90 | `legacy_lab_id` | **ADAPTER** | `binding = await self.scope_bridge.resolve_active_binding(legacy_lab_id)` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 97 | `ClinicalAuthorizationContext` | **ADAPTER** | `context = ClinicalAuthorizationContext(` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 98 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id=legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 98 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id=legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 99 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 99 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 109 | `ClinicalAuthorizationContext` | **ADAPTER** | `except ClinicalAuthorizationContextError as exc:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 112 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id=legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 112 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id=legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 113 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 113 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 121 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id=legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 121 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id=legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 122 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 122 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 132 | `legacy_lab_user_id` | **ADAPTER** | `async def _get_migrated_link(self, legacy_lab_user_id: int) -> LegacyAccountLink:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 132 | `LegacyAccountLink` | **ADAPTER** | `async def _get_migrated_link(self, legacy_lab_user_id: int) -> LegacyAccountLink:` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 133 | `LegacyAccountLink` | **ADAPTER** | `stmt = select(LegacyAccountLink).where(` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 134 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.source_kind == LegacyAccountLinkSource.lab_user.value,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 134 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.source_kind == LegacyAccountLinkSource.lab_user.value,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 135 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.legacy_account_id == legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 135 | `legacy_lab_user_id` | **ADAPTER** | `LegacyAccountLink.legacy_account_id == legacy_lab_user_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 136 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.status == LegacyAccountLinkStatus.migrated.value,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 136 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.status == LegacyAccountLinkStatus.migrated.value,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 137 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.canonical_account_id.isnot(None),` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 144 | `ClinicalAuthorizationContext` | **ADAPTER** | `raise ClinicalAuthorizationContextAmbiguous("More than one migrated canonical account link exists")` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 221 | `ClinicalAuthorizationContext` | **ADAPTER** | `raise ClinicalAuthorizationContextAmbiguous("More than one active clinical assignment matches this scope")` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 228 | `legacy_lab_user_id` | **ADAPTER** | `legacy_lab_user_id: int,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 229 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id: int,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 234 | `legacy_lab_id` | **ADAPTER** | `"legacy_lab_id": legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 234 | `legacy_lab_id` | **ADAPTER** | `"legacy_lab_id": legacy_lab_id,` |
| `backend/app/identity/services/clinical_authorization_context_service.py` | 240 | `legacy_lab_user_id` | **ADAPTER** | `target_id=str(legacy_lab_user_id),` |
| `backend/app/identity/services/legacy_mapping_service.py` | 12 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 13 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkSource,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 14 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 34 | `LegacyAccountLink` | **ADAPTER** | `source_kind: LegacyAccountLinkSource \| str,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 42 | `LegacyAccountLink` | **ADAPTER** | `kind = LegacyAccountLinkSource(source_kind).value` |
| `backend/app/identity/services/legacy_mapping_service.py` | 66 | `LegacyAccountLink` | **ADAPTER** | `source_kind: LegacyAccountLinkSource \| str,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 70 | `LegacyAccountLink` | **ADAPTER** | `) -> LegacyAccountLink \| None:` |
| `backend/app/identity/services/legacy_mapping_service.py` | 71 | `LegacyAccountLink` | **ADAPTER** | `kind = LegacyAccountLinkSource(source_kind).value` |
| `backend/app/identity/services/legacy_mapping_service.py` | 72 | `LegacyAccountLink` | **ADAPTER** | `stmt = select(LegacyAccountLink).where(` |
| `backend/app/identity/services/legacy_mapping_service.py` | 73 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.source_kind == kind,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 74 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLink.legacy_account_id == legacy_account_id,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 83 | `LegacyAccountLink` | **ADAPTER** | `source_kind: LegacyAccountLinkSource \| str,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 85 | `LegacyAccountLink` | **ADAPTER** | `) -> LegacyAccountLink:` |
| `backend/app/identity/services/legacy_mapping_service.py` | 87 | `LegacyAccountLink` | **ADAPTER** | `kind = LegacyAccountLinkSource(source_kind)` |
| `backend/app/identity/services/legacy_mapping_service.py` | 94 | `LegacyAccountLink` | **ADAPTER** | `link = LegacyAccountLink(` |
| `backend/app/identity/services/legacy_mapping_service.py` | 98 | `LegacyAccountLink` | **ADAPTER** | `status=LegacyAccountLinkStatus.pending.value,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 119 | `LegacyAccountLink` | **ADAPTER** | `target: LegacyAccountLinkStatus \| str,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 123 | `LegacyAccountLink` | **ADAPTER** | `) -> LegacyAccountLink:` |
| `backend/app/identity/services/legacy_mapping_service.py` | 126 | `LegacyAccountLink` | **ADAPTER** | `target_status = LegacyAccountLinkStatus(target)` |
| `backend/app/identity/services/legacy_mapping_service.py` | 151 | `LegacyAccountLink` | **ADAPTER** | `) -> LegacyAccountLink:` |
| `backend/app/identity/services/legacy_mapping_service.py` | 159 | `LegacyAccountLink` | **ADAPTER** | `LegacyAccountLinkStatus.rolled_back,` |
| `backend/app/identity/services/legacy_mapping_service.py` | 164 | `LegacyAccountLink` | **ADAPTER** | `async def _get_by_id(self, link_id: str, *, for_update: bool) -> LegacyAccountLink:` |
| `backend/app/identity/services/legacy_mapping_service.py` | 165 | `LegacyAccountLink` | **ADAPTER** | `stmt = select(LegacyAccountLink).where(LegacyAccountLink.id == link_id)` |
| `backend/app/identity/services/legacy_mapping_service.py` | 165 | `LegacyAccountLink` | **ADAPTER** | `stmt = select(LegacyAccountLink).where(LegacyAccountLink.id == link_id)` |
| `backend/app/insurance/api/claims.py` | 18 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/claims.py` | 91 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/claims.py` | 135 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/claims.py` | 159 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/claims.py` | 178 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/insurance/api/claims.py` | 178 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/insurance/api/claims.py` | 233 | `lab_id` | **RETAIN** | `def _generate_claim_number(db: Session, lab_id: int) -> str:` |
| `backend/app/insurance/api/claims.py` | 236 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == lab_id,` |
| `backend/app/insurance/api/claims.py` | 236 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == lab_id,` |
| `backend/app/insurance/api/claims.py` | 238 | `lab_id` | **RETAIN** | `return f"CLM-{lab_id}-{today.strftime('%Y%m%d')}-{count + 1:05d}"` |
| `backend/app/insurance/api/claims.py` | 241 | `lab_id` | **RETAIN** | `def _generate_appeal_number(db: Session, lab_id: int) -> str:` |
| `backend/app/insurance/api/claims.py` | 242 | `lab_id` | **RETAIN** | `count = db.query(Appeal).filter(Appeal.lab_id == lab_id).count()` |
| `backend/app/insurance/api/claims.py` | 242 | `lab_id` | **RETAIN** | `count = db.query(Appeal).filter(Appeal.lab_id == lab_id).count()` |
| `backend/app/insurance/api/claims.py` | 243 | `lab_id` | **RETAIN** | `return f"APL-{lab_id}-{count + 1:06d}"` |
| `backend/app/insurance/api/claims.py` | 256 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 259 | `lab_id` | **RETAIN** | `q = db.query(InsuranceClaim).filter(InsuranceClaim.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/claims.py` | 259 | `lab_id` | **RETAIN** | `q = db.query(InsuranceClaim).filter(InsuranceClaim.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/claims.py` | 280 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 286 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 286 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 293 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 293 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 300 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 300 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 308 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 308 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 309 | `lab_id` | **RETAIN** | `claim_number=_generate_claim_number(db, current_user.lab_id),` |
| `backend/app/insurance/api/claims.py` | 345 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 350 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 350 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 361 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 366 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 366 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 404 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 409 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 409 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 443 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 448 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 448 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 480 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 485 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 485 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 525 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 530 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 530 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 559 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 564 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 564 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 591 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 596 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 596 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 622 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 627 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 627 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 634 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 634 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 641 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 646 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 646 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 653 | `lab_id` | **RETAIN** | `Appeal.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 653 | `lab_id` | **RETAIN** | `Appeal.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 661 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 666 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 666 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 674 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 674 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 677 | `lab_id` | **RETAIN** | `appeal_number=_generate_appeal_number(db, current_user.lab_id),` |
| `backend/app/insurance/api/claims.py` | 702 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/claims.py` | 709 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/claims.py` | 709 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 17 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/coverage_check.py` | 140 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverage_check.py` | 145 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 145 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 159 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverage_check.py` | 164 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 164 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 197 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverage_check.py` | 203 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 203 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 249 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverage_check.py` | 253 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 253 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 277 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverage_check.py` | 283 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 283 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 351 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverage_check.py` | 356 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverage_check.py` | 356 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 18 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/coverages.py` | 63 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/coverages.py` | 96 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 99 | `lab_id` | **RETAIN** | `q = db.query(Coverage).filter(Coverage.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/coverages.py` | 99 | `lab_id` | **RETAIN** | `q = db.query(Coverage).filter(Coverage.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/coverages.py` | 116 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 121 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 121 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 129 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 129 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 159 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 164 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 164 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 175 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 180 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 180 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 209 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 214 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 214 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 240 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 245 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 245 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 263 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 268 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 268 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 320 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/coverages.py` | 325 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/coverages.py` | 325 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 17 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/network.py` | 51 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/network.py` | 83 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/network.py` | 114 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/network.py` | 135 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 138 | `lab_id` | **RETAIN** | `q = db.query(NetworkProvider).filter(NetworkProvider.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/network.py` | 138 | `lab_id` | **RETAIN** | `q = db.query(NetworkProvider).filter(NetworkProvider.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/network.py` | 153 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 158 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 158 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 164 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 164 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 172 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 172 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 196 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 201 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 201 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 229 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 234 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 234 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 257 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 262 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 262 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 269 | `lab_id` | **RETAIN** | `NetworkService.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 269 | `lab_id` | **RETAIN** | `NetworkService.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 280 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 285 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 285 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 291 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 291 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 316 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 321 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 321 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 328 | `lab_id` | **RETAIN** | `ProviderAvailability.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 328 | `lab_id` | **RETAIN** | `ProviderAvailability.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 339 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 344 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 344 | `lab_id` | **RETAIN** | `NetworkProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 353 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 353 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 372 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 375 | `lab_id` | **RETAIN** | `q = db.query(NetworkProvider).filter(NetworkProvider.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/network.py` | 375 | `lab_id` | **RETAIN** | `q = db.query(NetworkProvider).filter(NetworkProvider.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/network.py` | 404 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/network.py` | 408 | `lab_id` | **RETAIN** | `GeographicCoverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/network.py` | 408 | `lab_id` | **RETAIN** | `GeographicCoverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 17 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/payments.py` | 41 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/payments.py` | 69 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/payments.py` | 120 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 123 | `lab_id` | **RETAIN** | `q = db.query(InsurancePayment).filter(InsurancePayment.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/payments.py` | 123 | `lab_id` | **RETAIN** | `q = db.query(InsurancePayment).filter(InsurancePayment.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/payments.py` | 140 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 145 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 145 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 155 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 160 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 160 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 167 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 167 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 173 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 173 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 202 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 207 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 207 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 236 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 241 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 241 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 277 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 280 | `lab_id` | **RETAIN** | `q = db.query(Settlement).filter(Settlement.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/payments.py` | 280 | `lab_id` | **RETAIN** | `q = db.query(Settlement).filter(Settlement.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/payments.py` | 295 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 300 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 300 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 306 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 306 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 316 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 316 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 328 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 328 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 329 | `lab_id` | **RETAIN** | `settlement_number=_generate_settlement_number(db, current_user.lab_id),` |
| `backend/app/insurance/api/payments.py` | 358 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 363 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 363 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 369 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 369 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 401 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 406 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 406 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 434 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 439 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 439 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 466 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 471 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 471 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 477 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 477 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 525 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 537 | `lab_id` | **RETAIN** | `f"FROM ins_budgets WHERE lab_id = :lab_id"` |
| `backend/app/insurance/api/payments.py` | 537 | `lab_id` | **RETAIN** | `f"FROM ins_budgets WHERE lab_id = :lab_id"` |
| `backend/app/insurance/api/payments.py` | 542 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 542 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 569 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 574 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 574 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 580 | `lab_id` | **RETAIN** | `"SELECT id FROM ins_budgets WHERE lab_id = :lab_id AND provider_id = :pid AND fiscal_year = :fy",` |
| `backend/app/insurance/api/payments.py` | 580 | `lab_id` | **RETAIN** | `"SELECT id FROM ins_budgets WHERE lab_id = :lab_id AND provider_id = :pid AND fiscal_year = :fy",` |
| `backend/app/insurance/api/payments.py` | 581 | `lab_id` | **RETAIN** | `{"lab_id": current_user.lab_id, "pid": data.provider_id, "fy": data.fiscal_year},` |
| `backend/app/insurance/api/payments.py` | 581 | `lab_id` | **RETAIN** | `{"lab_id": current_user.lab_id, "pid": data.provider_id, "fy": data.fiscal_year},` |
| `backend/app/insurance/api/payments.py` | 590 | `lab_id` | **RETAIN** | `"INSERT INTO ins_budgets (lab_id, provider_id, fiscal_year, total_budget, currency, notes, spent, created_at) "` |
| `backend/app/insurance/api/payments.py` | 591 | `lab_id` | **RETAIN** | `"VALUES (:lab_id, :pid, :fy, :total, :cur, :notes, 0, NOW()) "` |
| `backend/app/insurance/api/payments.py` | 594 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 594 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 631 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 636 | `lab_id` | **RETAIN** | `"FROM ins_budgets WHERE id = :id AND lab_id = :lab_id",` |
| `backend/app/insurance/api/payments.py` | 636 | `lab_id` | **RETAIN** | `"FROM ins_budgets WHERE id = :id AND lab_id = :lab_id",` |
| `backend/app/insurance/api/payments.py` | 637 | `lab_id` | **RETAIN** | `{"id": budget_id, "lab_id": current_user.lab_id},` |
| `backend/app/insurance/api/payments.py` | 637 | `lab_id` | **RETAIN** | `{"id": budget_id, "lab_id": current_user.lab_id},` |
| `backend/app/insurance/api/payments.py` | 660 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 664 | `lab_id` | **RETAIN** | `"SELECT id, total_budget, spent FROM ins_budgets WHERE id = :id AND lab_id = :lab_id",` |
| `backend/app/insurance/api/payments.py` | 664 | `lab_id` | **RETAIN** | `"SELECT id, total_budget, spent FROM ins_budgets WHERE id = :id AND lab_id = :lab_id",` |
| `backend/app/insurance/api/payments.py` | 665 | `lab_id` | **RETAIN** | `{"id": budget_id, "lab_id": current_user.lab_id},` |
| `backend/app/insurance/api/payments.py` | 665 | `lab_id` | **RETAIN** | `{"id": budget_id, "lab_id": current_user.lab_id},` |
| `backend/app/insurance/api/payments.py` | 705 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 709 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 709 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 746 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 750 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 750 | `lab_id` | **RETAIN** | `InsurancePayment.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 756 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 756 | `lab_id` | **RETAIN** | `Settlement.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 783 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/payments.py` | 787 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/payments.py` | 787 | `lab_id` | **RETAIN** | `InsuranceClaim.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 11 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/policies.py` | 59 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/policies.py` | 114 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/policies.py` | 148 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 151 | `lab_id` | **RETAIN** | `q = db.query(InsurancePolicy).filter(InsurancePolicy.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/policies.py` | 151 | `lab_id` | **RETAIN** | `q = db.query(InsurancePolicy).filter(InsurancePolicy.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/policies.py` | 167 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 172 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 172 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 178 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 178 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 185 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 185 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 209 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 214 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 214 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 225 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 230 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 230 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 259 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 264 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 264 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 289 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 296 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 296 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 303 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 303 | `lab_id` | **RETAIN** | `Coverage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 313 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 321 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 321 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 327 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 327 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 354 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 359 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 359 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 366 | `lab_id` | **RETAIN** | `BenefitPackage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 366 | `lab_id` | **RETAIN** | `BenefitPackage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 374 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/policies.py` | 379 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 379 | `lab_id` | **RETAIN** | `InsurancePolicy.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 386 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 386 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 392 | `lab_id` | **RETAIN** | `BenefitPackage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 392 | `lab_id` | **RETAIN** | `BenefitPackage.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 399 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/policies.py` | 399 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 10 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/providers.py` | 62 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/providers.py` | 106 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/providers.py` | 135 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/providers.py` | 138 | `lab_id` | **RETAIN** | `q = db.query(InsuranceProvider).filter(InsuranceProvider.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/providers.py` | 138 | `lab_id` | **RETAIN** | `q = db.query(InsuranceProvider).filter(InsuranceProvider.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/providers.py` | 158 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/providers.py` | 162 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 162 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 169 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 169 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 192 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/providers.py` | 197 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 197 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 208 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/providers.py` | 213 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 213 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 242 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/providers.py` | 247 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 247 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 271 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/providers.py` | 276 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 276 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 283 | `lab_id` | **RETAIN** | `ProviderContract.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 283 | `lab_id` | **RETAIN** | `ProviderContract.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 294 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/providers.py` | 299 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 299 | `lab_id` | **RETAIN** | `InsuranceProvider.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 305 | `lab_id` | **RETAIN** | `ProviderContract.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 305 | `lab_id` | **RETAIN** | `ProviderContract.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 312 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/providers.py` | 312 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 19 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/insurance/api/referrals.py` | 68 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/insurance/api/referrals.py` | 114 | `lab_id` | **RETAIN** | `def _generate_referral_number(db: Session, lab_id: int) -> str:` |
| `backend/app/insurance/api/referrals.py` | 116 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == lab_id,` |
| `backend/app/insurance/api/referrals.py` | 116 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == lab_id,` |
| `backend/app/insurance/api/referrals.py` | 118 | `lab_id` | **RETAIN** | `return f"REF-{lab_id}-{count + 1:06d}"` |
| `backend/app/insurance/api/referrals.py` | 124 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/insurance/api/referrals.py` | 131 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/insurance/api/referrals.py` | 131 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/insurance/api/referrals.py` | 150 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 153 | `lab_id` | **RETAIN** | `q = db.query(InsuranceReferral).filter(InsuranceReferral.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/referrals.py` | 153 | `lab_id` | **RETAIN** | `q = db.query(InsuranceReferral).filter(InsuranceReferral.lab_id == current_user.lab_id)` |
| `backend/app/insurance/api/referrals.py` | 170 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 174 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 174 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 175 | `lab_id` | **RETAIN** | `referral_number=_generate_referral_number(db, current_user.lab_id),` |
| `backend/app/insurance/api/referrals.py` | 185 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 185 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 208 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 213 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 213 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 224 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 229 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 229 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 259 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 264 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 264 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 274 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 274 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 296 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 301 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 301 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 311 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 311 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 334 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 339 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 339 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 349 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 349 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 372 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 377 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 377 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 389 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 389 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 412 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 417 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 417 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 429 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 429 | `lab_id` | **RETAIN** | `db=db, referral_id=referral.id, lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 453 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 458 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 458 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 466 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 466 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 504 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 509 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 509 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 522 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/insurance/api/referrals.py` | 527 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/api/referrals.py` | 527 | `lab_id` | **RETAIN** | `InsuranceReferral.lab_id == current_user.lab_id,` |
| `backend/app/insurance/domain/members.py` | 51 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/members.py` | 92 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/members.py` | 137 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/members.py` | 181 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/members.py` | 222 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 4 | `lab_id` | **RETAIN** | `All entities are tenant-scoped via lab_id.` |
| `backend/app/insurance/domain/models.py` | 67 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 115 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 173 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 226 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 281 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 330 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 390 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 496 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 540 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 585 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 634 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/models.py` | 681 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/network.py` | 52 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/network.py` | 95 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/network.py` | 135 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/network.py` | 176 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/network.py` | 220 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/referral.py` | 54 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/referral.py` | 123 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/referral.py` | 155 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/services.py` | 51 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/services.py` | 96 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/services.py` | 141 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/domain/services.py` | 184 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/insurance/financial/engine.py` | 406 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/insurance/financial/engine.py` | 406 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/integration/government/moh.py` | 138 | `lab_id` | **RETAIN** | `"lab_id": data.get("lab_id", ""),` |
| `backend/app/integration/government/moh.py` | 138 | `lab_id` | **RETAIN** | `"lab_id": data.get("lab_id", ""),` |
| `backend/app/interoperability/adapter_base.py` | 43 | `lab_id` | **RETAIN** | `lab_id: str \| None = None` |
| `backend/app/interoperability/audit_event.py` | 43 | `lab_id` | **RETAIN** | `lab_id: str \| None = None` |
| `backend/app/interoperability/principal.py` | 28 | `lab_id` | **RETAIN** | ```lab_id`` is required for any operation whose data class includes` |
| `backend/app/interoperability/principal.py` | 29 | `lab_id` | **RETAIN** | `patient data. National-aggregator domains may set ``lab_id=None`` only` |
| `backend/app/interoperability/principal.py` | 39 | `lab_id` | **RETAIN** | `lab_id: str \| None = None` |
| `backend/app/knowledge_graph/routes.py` | 15 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/knowledge_graph/routes.py` | 58 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("admin")),` |
| `backend/app/knowledge_graph/routes.py` | 91 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("admin")),` |
| `backend/app/knowledge_graph/routes.py` | 126 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/knowledge_graph/routes.py` | 153 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/knowledge_graph/routes.py` | 174 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/knowledge_graph/routes.py` | 191 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/knowledge_graph/routes.py` | 208 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("admin")),` |
| `backend/app/knowledge_graph/routes.py` | 218 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("admin")),` |
| `backend/app/knowledge_graph/routes.py` | 228 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("admin")),` |
| `backend/app/knowledge_graph/routes.py` | 238 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("admin")),` |
| `backend/app/knowledge_graph/routes.py` | 262 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("admin")),` |
| `backend/app/knowledge_graph/routes.py` | 279 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/knowledge_graph/routes.py` | 289 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/__init__.py` | 14 | `lab_id` | **RETAIN** | `tenant isolation (lab_id), offline sync, events (outbox pattern), and FHIR mapping.` |
| `backend/app/lims/events.py` | 21 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/lims/models.py` | 13 | `lab_id` | **RETAIN** | `- Tenant Isolation (lab_id)` |
| `backend/app/lims/models.py` | 17 | `lab_id` | **RETAIN** | `- ABAC / RBAC (via lab_id + existing security layer)` |
| `backend/app/lims/models.py` | 238 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 257 | `lab_id` | **RETAIN** | `Index("ix_lims_dept_lab_code", "lab_id", "code", unique=True),` |
| `backend/app/lims/models.py` | 258 | `lab_id` | **RETAIN** | `Index("ix_lims_dept_not_deleted", "is_deleted", "lab_id"),` |
| `backend/app/lims/models.py` | 377 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 405 | `lab_id` | **RETAIN** | `Index("ix_lims_inst_lab_status", "lab_id", "status"),` |
| `backend/app/lims/models.py` | 473 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 493 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "code", name="uq_lims_qc_program_code"),` |
| `backend/app/lims/models.py` | 504 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 532 | `lab_id` | **RETAIN** | `Index("ix_lims_iqc_lab_test_date", "lab_id", "test_code", "performed_at"),` |
| `backend/app/lims/models.py` | 542 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 569 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "scheme_name", "round_number", "test_code", name="uq_lims_eqa_round"),` |
| `backend/app/lims/models.py` | 579 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 607 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "lot_number", "item_type", name="uq_lims_lot"),` |
| `backend/app/lims/models.py` | 618 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 645 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "reagent_code", name="uq_lims_reagent_code"),` |
| `backend/app/lims/models.py` | 646 | `lab_id` | **RETAIN** | `Index("ix_lims_reagent_stock", "lab_id", "current_quantity"),` |
| `backend/app/lims/models.py` | 656 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 675 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "code", name="uq_lims_supplier_lab_code"),` |
| `backend/app/lims/models.py` | 685 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 709 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "code", name="uq_lims_consumable_code"),` |
| `backend/app/lims/models.py` | 719 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 741 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "code", name="uq_lims_storage_lab_code"),` |
| `backend/app/lims/models.py` | 751 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 846 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 895 | `lab_id` | **RETAIN** | `Index("ix_lims_spec_lab_status", "lab_id", "status"),` |
| `backend/app/lims/models.py` | 906 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 965 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 995 | `lab_id` | **RETAIN** | `Index("ix_lims_order_lab_status", "lab_id", "order_status"),` |
| `backend/app/lims/models.py` | 1005 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 1028 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "code", name="uq_lims_panel_lab_code"),` |
| `backend/app/lims/models.py` | 1060 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 1132 | `lab_id` | **RETAIN** | `Index("ix_lims_result_lab_test", "lab_id", "test_code"),` |
| `backend/app/lims/models.py` | 1133 | `lab_id` | **RETAIN** | `Index("ix_lims_result_validation", "lab_id", "validation_status"),` |
| `backend/app/lims/models.py` | 1145 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=True, index=True)` |
| `backend/app/lims/models.py` | 1175 | `lab_id` | **RETAIN** | `Index("ix_lims_refrange_lookup", "test_code", "lab_id", "gender"),` |
| `backend/app/lims/models.py` | 1185 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 1203 | `lab_id` | **RETAIN** | `Index("ix_lims_autovalid_test", "test_code", "lab_id"),` |
| `backend/app/lims/models.py` | 1213 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 1232 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "test_code", name="uq_lims_delta_check"),` |
| `backend/app/lims/models.py` | 1262 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 1285 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 1312 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/lims/models.py` | 1344 | `lab_id` | **RETAIN** | `Index("ix_lims_report_lab_status", "lab_id", "status"),` |
| `backend/app/lims/routes.py` | 5 | `lab_id` | **RETAIN** | `- Tenant isolation via lab_id` |
| `backend/app/lims/routes.py` | 21 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/lims/routes.py` | 166 | `lab_id` | **RETAIN** | `# Helper: extract lab_id from current user` |
| `backend/app/lims/routes.py` | 170 | `LabUser` | **RETAIN** | `def _lab_id(current_user: LabUser) -> int:` |
| `backend/app/lims/routes.py` | 171 | `lab_id` | **RETAIN** | `return current_user.lab_id` |
| `backend/app/lims/routes.py` | 185 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 189 | `lab_id` | **RETAIN** | `lims_models.Department.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 198 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 203 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 221 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 233 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 250 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 254 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 275 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 279 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 286 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 304 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 309 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 319 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 323 | `lab_id` | **RETAIN** | `if not inst or inst.lab_id != _lab_id(current_user):` |
| `backend/app/lims/routes.py` | 332 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 336 | `lab_id` | **RETAIN** | `if not inst or inst.lab_id != _lab_id(current_user):` |
| `backend/app/lims/routes.py` | 346 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 352 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 373 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 378 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 398 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 403 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 417 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 429 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 447 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 473 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 499 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 503 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 519 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 524 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 535 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 540 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 563 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 568 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 583 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 589 | `lab_id` | **RETAIN** | `LabOrder.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 614 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 618 | `lab_id` | **RETAIN** | `lims_models.Order.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 632 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 637 | `lab_id` | **RETAIN** | `lims_models.Order.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 648 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 653 | `lab_id` | **RETAIN** | `lims_models.Order.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 673 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 678 | `lab_id` | **RETAIN** | `lims_models.Order.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 693 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 697 | `lab_id` | **RETAIN** | `lims_models.Panel.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 718 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 722 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 757 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 763 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 791 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 795 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 822 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 827 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 838 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 843 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 867 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 872 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 895 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 900 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 915 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 934 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 938 | `lab_id` | **RETAIN** | `lims_models.IQC.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 953 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 957 | `lab_id` | **RETAIN** | `lims_models.QCProgram.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 966 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 970 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 995 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1002 | `lab_id` | **RETAIN** | `lims_models.IQC.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1066 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1070 | `lab_id` | **RETAIN** | `lims_models.Reagent.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1083 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1087 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1108 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1113 | `lab_id` | **RETAIN** | `lims_models.Reagent.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1129 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1133 | `lab_id` | **RETAIN** | `lims_models.Consumable.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1145 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1150 | `lab_id` | **RETAIN** | `lims_models.Lot.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1164 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1168 | `lab_id` | **RETAIN** | `lims_models.Supplier.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1176 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1180 | `lab_id` | **RETAIN** | `lims_models.Storage.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1189 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1193 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1213 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1227 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1232 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1257 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1261 | `lab_id` | **RETAIN** | `lims_models.AutoValidationRule.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1272 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1276 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1293 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1297 | `lab_id` | **RETAIN** | `lims_models.DeltaCheckRule.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1311 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1328 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1332 | `lab_id` | **RETAIN** | `lims_models.LabReport.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1345 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1350 | `lab_id` | **RETAIN** | `lims_models.LabReport.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1360 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1365 | `lab_id` | **RETAIN** | `lims_models.LabReport.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1380 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1385 | `lab_id` | **RETAIN** | `lims_models.LabReport.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1399 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1404 | `lab_id` | **RETAIN** | `lims_models.LabReport.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1412 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1426 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1432 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1451 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1457 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1479 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1485 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1522 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1528 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == _lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1536 | `lab_id` | **RETAIN** | `lab_id=result.lab_id,` |
| `backend/app/lims/routes.py` | 1536 | `lab_id` | **RETAIN** | `lab_id=result.lab_id,` |
| `backend/app/lims/routes.py` | 1552 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1568 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1572 | `lab_id` | **RETAIN** | `lab_id=_lab_id(current_user),` |
| `backend/app/lims/routes.py` | 1594 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1620 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/lims/routes.py` | 1623 | `lab_id` | **RETAIN** | `lab_id = _lab_id(current_user)` |
| `backend/app/lims/routes.py` | 1626 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1626 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1633 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1633 | `lab_id` | **RETAIN** | `lims_models.Specimen.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1638 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1638 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1643 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1643 | `lab_id` | **RETAIN** | `lims_models.Result.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1648 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1648 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1653 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1653 | `lab_id` | **RETAIN** | `lims_models.Instrument.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1658 | `lab_id` | **RETAIN** | `lims_models.IQC.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1658 | `lab_id` | **RETAIN** | `lims_models.IQC.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1663 | `lab_id` | **RETAIN** | `lims_models.Reagent.lab_id == lab_id,` |
| `backend/app/lims/routes.py` | 1663 | `lab_id` | **RETAIN** | `lims_models.Reagent.lab_id == lab_id,` |
| `backend/app/lims/services.py` | 55 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/services.py` | 67 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 67 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 143 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/services.py` | 149 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 149 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 172 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/services.py` | 184 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 184 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 226 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/services.py` | 239 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 239 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 257 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 257 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 305 | `lab_id` | **RETAIN** | `lab_id=result.lab_id,` |
| `backend/app/lims/services.py` | 305 | `lab_id` | **RETAIN** | `lab_id=result.lab_id,` |
| `backend/app/lims/services.py` | 326 | `lab_id` | **RETAIN** | `lab_id=result.lab_id,` |
| `backend/app/lims/services.py` | 326 | `lab_id` | **RETAIN** | `lab_id=result.lab_id,` |
| `backend/app/lims/services.py` | 348 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/services.py` | 363 | `lab_id` | **RETAIN** | `IQC.lab_id == lab_id,` |
| `backend/app/lims/services.py` | 363 | `lab_id` | **RETAIN** | `IQC.lab_id == lab_id,` |
| `backend/app/lims/services.py` | 378 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 378 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 487 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/services.py` | 495 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/services.py` | 495 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/lims/workflows.py` | 27 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/lims/workflows.py` | 66 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/lims/workflows.py` | 68 | `lab_id` | **RETAIN** | `(ReferenceRangeDef.lab_id == lab_id) \| (ReferenceRangeDef.lab_id.is_(None)),` |
| `backend/app/lims/workflows.py` | 68 | `lab_id` | **RETAIN** | `(ReferenceRangeDef.lab_id == lab_id) \| (ReferenceRangeDef.lab_id.is_(None)),` |
| `backend/app/lims/workflows.py` | 68 | `lab_id` | **RETAIN** | `(ReferenceRangeDef.lab_id == lab_id) \| (ReferenceRangeDef.lab_id.is_(None)),` |
| `backend/app/lims/workflows.py` | 86 | `lab_id` | **RETAIN** | `ReferenceRangeDef.lab_id.desc().nulls_last(),` |
| `backend/app/lims/workflows.py` | 137 | `lab_id` | **RETAIN** | `AutoValidationRule.lab_id == lab_id,` |
| `backend/app/lims/workflows.py` | 137 | `lab_id` | **RETAIN** | `AutoValidationRule.lab_id == lab_id,` |
| `backend/app/lims/workflows.py` | 224 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/workflows.py` | 239 | `lab_id` | **RETAIN** | `Result.lab_id == lab_id,` |
| `backend/app/lims/workflows.py` | 239 | `lab_id` | **RETAIN** | `Result.lab_id == lab_id,` |
| `backend/app/lims/workflows.py` | 270 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/workflows.py` | 318 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/lims/workflows.py` | 329 | `lab_id` | **RETAIN** | `Result.lab_id == lab_id,` |
| `backend/app/lims/workflows.py` | 329 | `lab_id` | **RETAIN** | `Result.lab_id == lab_id,` |
| `backend/app/models/__init__.py` | 39 | `LabUser` | **RETAIN** | `from .lab_user import LabUser` |
| `backend/app/models/__init__.py` | 83 | `LabUser` | **RETAIN** | `"LabUser",` |
| `backend/app/models/ai.py` | 17 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)` |
| `backend/app/models/ai.py` | 36 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)` |
| `backend/app/models/ai.py` | 67 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)` |
| `backend/app/models/ai.py` | 135 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True)` |
| `backend/app/models/ai_interaction.py` | 48 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/ai_interaction.py` | 121 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/ai_interaction.py` | 135 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/audit_log.py` | 17 | `lab_id` | **RETAIN** | `# include lab_id so they can be safely scoped for compliance and FHIR provenance.` |
| `backend/app/models/audit_log.py` | 18 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True, index=True)` |
| `backend/app/models/canonical_patient.py` | 30 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)` |
| `backend/app/models/claim.py` | 8 | `lab_id` | **RETAIN** | `All queries MUST filter by lab_id (security invariant).` |
| `backend/app/models/claim.py` | 27 | `lab_id` | **RETAIN** | `Index("ix_claims_lab_id", "lab_id"),` |
| `backend/app/models/claim.py` | 33 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)` |
| `backend/app/models/clinical_scope.py` | 60 | `legacy_lab_id` | **ADAPTER** | `UniqueConstraint("legacy_lab_id", "facility_resource_id", name="uq_clinical_lab_facility_binding"),` |
| `backend/app/models/clinical_scope.py` | 64 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/edge.py` | 7 | `lab_id` | **RETAIN** | `Tenant isolation: every row is scoped by `lab_id`. Per the platform's` |
| `backend/app/models/edge.py` | 8 | `lab_id` | **RETAIN** | `security invariants, all queries must filter on `lab_id == current_user.lab_id`` |
| `backend/app/models/edge.py` | 8 | `lab_id` | **RETAIN** | `security invariants, all queries must filter on `lab_id == current_user.lab_id`` |
| `backend/app/models/edge.py` | 47 | `lab_id` | **RETAIN** | `Index("idx_edge_devices_lab", "lab_id", "status"),` |
| `backend/app/models/edge.py` | 53 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)` |
| `backend/app/models/edge.py` | 89 | `lab_id` | **RETAIN** | `Index("idx_edge_tasks_lab_status", "lab_id", "status", "created_at"),` |
| `backend/app/models/edge.py` | 90 | `lab_id` | **RETAIN** | `Index("idx_edge_tasks_idem", "lab_id", "idempotency_key"),` |
| `backend/app/models/edge.py` | 96 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)` |
| `backend/app/models/edge.py` | 129 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)` |
| `backend/app/models/edge.py` | 175 | `lab_id` | **RETAIN** | `__table_args__ = (Index("idx_edge_assignments_lookup", "lab_id", "device_id", "active"),)` |
| `backend/app/models/edge.py` | 179 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=True)` |
| `backend/app/models/edge.py` | 187 | `lab_id` | **RETAIN** | `"""Per-tenant edge policy. lab_id NULL means the global default."""` |
| `backend/app/models/edge.py` | 192 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=True, unique=True)` |
| `backend/app/models/edge.py` | 227 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True)` |
| `backend/app/models/lab.py` | 27 | `LabUser` | **RETAIN** | `users = relationship("LabUser", back_populates="lab", cascade="all, delete-orphan")` |
| `backend/app/models/lab_order.py` | 29 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/lab_order.py` | 31 | `LabUser` | **RETAIN** | `# doctor_user_id links to a LabUser with role='doctor' — enables data isolation` |
| `backend/app/models/lab_user.py` | 11 | `LabUser` | **RETAIN** | `class LabUser(Base):` |
| `backend/app/models/lab_user.py` | 15 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/patient.py` | 19 | `lab_id` | **RETAIN** | `# Composite indexes for multi-tenant queries (lab_id partitions all lookups)` |
| `backend/app/models/patient.py` | 21 | `lab_id` | **RETAIN** | `Index("ix_patients_lab_id", "lab_id"),` |
| `backend/app/models/patient.py` | 22 | `lab_id` | **RETAIN** | `Index("ix_patients_lab_phone", "lab_id", "phone"),` |
| `backend/app/models/patient.py` | 23 | `lab_id` | **RETAIN** | `Index("ix_patients_lab_nid", "lab_id", "national_id_hash"),` |
| `backend/app/models/patient.py` | 27 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)` |
| `backend/app/models/quality_control.py` | 17 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/subscription.py` | 27 | `lab_id` | **RETAIN** | `One subscription per lab (UNIQUE on lab_id).` |
| `backend/app/models/subscription.py` | 33 | `lab_id` | **RETAIN** | `lab_id = Column(` |
| `backend/app/models/subscription.py` | 85 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/subscription.py` | 110 | `lab_id` | **RETAIN** | `__table_args__ = (Index("ix_upgrade_requests_lab_status", "lab_id", "status"),)` |
| `backend/app/models/subscription.py` | 124 | `lab_id` | **RETAIN** | `lab_id = Column(` |
| `backend/app/models/subscription.py` | 151 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True)` |
| `backend/app/models/subscription.py` | 159 | `lab_id` | **RETAIN** | `__table_args__ = (Index("ix_feature_flags_lab_key", "lab_id", "feature_key", unique=True),)` |
| `backend/app/models/test_result.py` | 43 | `lab_id` | **RETAIN** | `Index("ix_test_results_citizen_lab", "citizen_id", "lab_id"),` |
| `backend/app/models/test_result.py` | 44 | `lab_id` | **RETAIN** | `Index("ix_test_results_lab_status", "lab_id", "status"),` |
| `backend/app/models/test_result.py` | 45 | `lab_id` | **RETAIN** | `Index("ix_test_results_lab_collected", "lab_id", "sample_collected_at"),` |
| `backend/app/models/test_result.py` | 58 | `lab_id` | **RETAIN** | `lab_id = Column(` |
| `backend/app/models/test_result.py` | 121 | `lab_id` | **RETAIN** | `lab_id: int = Field(..., ge=1)` |
| `backend/app/models/test_result.py` | 167 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/models/user.py` | 20 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True)` |
| `backend/app/national/domain/patient.py` | 55 | `lab_id` | **RETAIN** | `Index("ix_national_patients_lab_health_number", "lab_id", "health_number", unique=True),` |
| `backend/app/national/domain/patient.py` | 56 | `lab_id` | **RETAIN** | `Index("ix_national_patients_lab_citizen", "lab_id", "citizen_id"),` |
| `backend/app/national/events/base.py` | 19 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/national/fhir/diagnostic_report.py` | 54 | `lab_id` | **RETAIN** | `lab_id = order.get("lab_id")` |
| `backend/app/national/fhir/diagnostic_report.py` | 54 | `lab_id` | **RETAIN** | `lab_id = order.get("lab_id")` |
| `backend/app/national/fhir/diagnostic_report.py` | 55 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/national/fhir/diagnostic_report.py` | 56 | `lab_id` | **RETAIN** | `performers.append({"actor": {"reference": f"Organization/{lab_id}"}})` |
| `backend/app/national/fhir/patient.py` | 37 | `lab_id` | **RETAIN** | `"managingOrganization": [{"reference": f"Organization/{patient.lab_id}"}] if patient.lab_id else [],` |
| `backend/app/national/fhir/patient.py` | 37 | `lab_id` | **RETAIN** | `"managingOrganization": [{"reference": f"Organization/{patient.lab_id}"}] if patient.lab_id else [],` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 64 | `lab_id` | **RETAIN** | `lab_id: str = ""` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 330 | `lab_id` | **RETAIN** | `def get_reagent_forecast(self, lab_id: str, days: int = 90) -> list[ReagentForecast]:` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 355 | `lab_id` | **RETAIN** | `def record_tat(self, lab_id: str, test_code: str, tat_minutes: float) -> None:` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 356 | `lab_id` | **RETAIN** | `key = f"{lab_id}:{test_code}"` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 361 | `lab_id` | **RETAIN** | `def analyze_tat(self, lab_id: str, test_code: str, period: int = 30) -> TATData:` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 362 | `lab_id` | **RETAIN** | `key = f"{lab_id}:{test_code}"` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 368 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 368 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 383 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/national/intelligence/laboratory/analytics.py` | 383 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/national/intelligence/routes.py` | 295 | `lab_id` | **RETAIN** | `lab_id = body.get("lab_id", "")` |
| `backend/app/national/intelligence/routes.py` | 295 | `lab_id` | **RETAIN** | `lab_id = body.get("lab_id", "")` |
| `backend/app/national/intelligence/routes.py` | 298 | `lab_id` | **RETAIN** | `tat_data = tat_optimizer.analyze_tat(lab_id, test_code, period)` |
| `backend/app/national/intelligence/routes.py` | 307 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/national/intelligence/routes.py` | 307 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/national/policies/observation_policy.py` | 6 | `lab_id` | **RETAIN** | `user_lab_id = getattr(user, "lab_id", None)` |
| `backend/app/national/policies/observation_policy.py` | 7 | `lab_id` | **RETAIN** | `obs_lab_id = getattr(observation, "lab_id", None)` |
| `backend/app/national_data/models/ai_data/FeatureValue.py` | 23 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True, index=True)` |
| `backend/app/national_data/models/ai_data/VectorEmbedding.py` | 24 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True, index=True)` |
| `backend/app/national_data/models/ai_data/VectorEmbedding.py` | 31 | `lab_id` | **RETAIN** | `Index("ix_dp_vector_lab", "lab_id"),` |
| `backend/app/national_data/models/canonical_document.py` | 27 | `lab_id` | **RETAIN** | `lab_id: int \| None` |
| `backend/app/national_data/models/canonical_document.py` | 32 | `lab_id` | **RETAIN** | `def query_all(cls, db: Session, lab_id: int \| None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:` |
| `backend/app/national_data/models/canonical_document.py` | 46 | `lab_id` | **RETAIN** | `np_sub.c.lab_id,` |
| `backend/app/national_data/models/canonical_document.py` | 64 | `lab_id` | **RETAIN** | `np_sub.c.lab_id,` |
| `backend/app/national_data/models/canonical_document.py` | 75 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_document.py` | 76 | `lab_id` | **RETAIN** | `query = query.filter(union_q.c.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_document.py` | 76 | `lab_id` | **RETAIN** | `query = query.filter(union_q.c.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_encounter.py` | 32 | `lab_id` | **RETAIN** | `lab_id: int \| None` |
| `backend/app/national_data/models/canonical_encounter.py` | 36 | `lab_id` | **RETAIN** | `def query_all(cls, db: Session, lab_id: int \| None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:` |
| `backend/app/national_data/models/canonical_encounter.py` | 52 | `lab_id` | **RETAIN** | `NationalPatient.lab_id,` |
| `backend/app/national_data/models/canonical_encounter.py` | 61 | `lab_id` | **RETAIN** | `LabOrder.lab_id == NationalPatient.lab_id,` |
| `backend/app/national_data/models/canonical_encounter.py` | 61 | `lab_id` | **RETAIN** | `LabOrder.lab_id == NationalPatient.lab_id,` |
| `backend/app/national_data/models/canonical_encounter.py` | 65 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_encounter.py` | 66 | `lab_id` | **RETAIN** | `query = query.filter(NationalPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_encounter.py` | 66 | `lab_id` | **RETAIN** | `query = query.filter(NationalPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_encounter.py` | 72 | `lab_id` | **RETAIN** | `def get_by_id(cls, db: Session, encounter_id: str, lab_id: int \| None = None) -> dict[str, Any] \| None:` |
| `backend/app/national_data/models/canonical_encounter.py` | 88 | `lab_id` | **RETAIN** | `NationalPatient.lab_id,` |
| `backend/app/national_data/models/canonical_encounter.py` | 97 | `lab_id` | **RETAIN** | `LabOrder.lab_id == NationalPatient.lab_id,` |
| `backend/app/national_data/models/canonical_encounter.py` | 97 | `lab_id` | **RETAIN** | `LabOrder.lab_id == NationalPatient.lab_id,` |
| `backend/app/national_data/models/canonical_encounter.py` | 103 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_encounter.py` | 104 | `lab_id` | **RETAIN** | `query = query.filter(NationalPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_encounter.py` | 104 | `lab_id` | **RETAIN** | `query = query.filter(NationalPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_medication.py` | 38 | `lab_id` | **RETAIN** | `lab_id: int \| None` |
| `backend/app/national_data/models/canonical_medication.py` | 41 | `lab_id` | **RETAIN** | `def query_all(cls, db: Session, lab_id: int \| None = None, patient_lims_id: int \| None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:` |
| `backend/app/national_data/models/canonical_medication.py` | 61 | `lab_id` | **RETAIN** | `np_sub.c.lab_id,` |
| `backend/app/national_data/models/canonical_medication.py` | 83 | `lab_id` | **RETAIN** | `np_sub.c.lab_id,` |
| `backend/app/national_data/models/canonical_medication.py` | 105 | `lab_id` | **RETAIN** | `np_sub.c.lab_id,` |
| `backend/app/national_data/models/canonical_medication.py` | 127 | `lab_id` | **RETAIN** | `np_sub.c.lab_id,` |
| `backend/app/national_data/models/canonical_medication.py` | 136 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_medication.py` | 137 | `lab_id` | **RETAIN** | `query = query.filter(union_q.c.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_medication.py` | 137 | `lab_id` | **RETAIN** | `query = query.filter(union_q.c.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_observation.py` | 21 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/national_data/models/canonical_observation.py` | 45 | `lab_id` | **RETAIN** | `def query_all(cls, db: Session, lab_id: int \| None = None, patient_id: int \| None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:` |
| `backend/app/national_data/models/canonical_observation.py` | 48 | `lab_id` | **RETAIN** | `LabResult.lab_id,` |
| `backend/app/national_data/models/canonical_observation.py` | 75 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabResult.lab_id,` |
| `backend/app/national_data/models/canonical_observation.py` | 75 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabResult.lab_id,` |
| `backend/app/national_data/models/canonical_observation.py` | 86 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_observation.py` | 87 | `lab_id` | **RETAIN** | `query = query.filter(LabResult.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_observation.py` | 87 | `lab_id` | **RETAIN** | `query = query.filter(LabResult.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_observation.py` | 96 | `lab_id` | **RETAIN** | `def get_by_id(cls, db: Session, observation_id: int, lab_id: int \| None = None) -> dict[str, Any] \| None:` |
| `backend/app/national_data/models/canonical_observation.py` | 99 | `lab_id` | **RETAIN** | `LabResult.lab_id,` |
| `backend/app/national_data/models/canonical_observation.py` | 126 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabResult.lab_id,` |
| `backend/app/national_data/models/canonical_observation.py` | 126 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabResult.lab_id,` |
| `backend/app/national_data/models/canonical_observation.py` | 139 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_observation.py` | 140 | `lab_id` | **RETAIN** | `query = query.filter(LabResult.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_observation.py` | 140 | `lab_id` | **RETAIN** | `query = query.filter(LabResult.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_patient.py` | 19 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/national_data/models/canonical_patient.py` | 45 | `lab_id` | **RETAIN** | `def query_all(cls, db: Session, lab_id: int \| None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:` |
| `backend/app/national_data/models/canonical_patient.py` | 48 | `lab_id` | **RETAIN** | `LimsPatient.lab_id,` |
| `backend/app/national_data/models/canonical_patient.py` | 75 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LimsPatient.lab_id,` |
| `backend/app/national_data/models/canonical_patient.py` | 75 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LimsPatient.lab_id,` |
| `backend/app/national_data/models/canonical_patient.py` | 82 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_patient.py` | 83 | `lab_id` | **RETAIN** | `query = query.filter(LimsPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_patient.py` | 83 | `lab_id` | **RETAIN** | `query = query.filter(LimsPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_patient.py` | 89 | `lab_id` | **RETAIN** | `def get_by_id(cls, db: Session, patient_id: int, lab_id: int \| None = None) -> dict[str, Any] \| None:` |
| `backend/app/national_data/models/canonical_patient.py` | 92 | `lab_id` | **RETAIN** | `LimsPatient.lab_id,` |
| `backend/app/national_data/models/canonical_patient.py` | 119 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LimsPatient.lab_id,` |
| `backend/app/national_data/models/canonical_patient.py` | 119 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LimsPatient.lab_id,` |
| `backend/app/national_data/models/canonical_patient.py` | 128 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_patient.py` | 129 | `lab_id` | **RETAIN** | `query = query.filter(LimsPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_patient.py` | 129 | `lab_id` | **RETAIN** | `query = query.filter(LimsPatient.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_procedure.py` | 19 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/national_data/models/canonical_procedure.py` | 34 | `lab_id` | **RETAIN** | `def query_all(cls, db: Session, lab_id: int \| None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:` |
| `backend/app/national_data/models/canonical_procedure.py` | 37 | `lab_id` | **RETAIN** | `LabOrder.lab_id,` |
| `backend/app/national_data/models/canonical_procedure.py` | 53 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabOrder.lab_id,` |
| `backend/app/national_data/models/canonical_procedure.py` | 53 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabOrder.lab_id,` |
| `backend/app/national_data/models/canonical_procedure.py` | 60 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_procedure.py` | 61 | `lab_id` | **RETAIN** | `query = query.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_procedure.py` | 61 | `lab_id` | **RETAIN** | `query = query.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_procedure.py` | 67 | `lab_id` | **RETAIN** | `def get_by_id(cls, db: Session, procedure_id: int, lab_id: int \| None = None) -> dict[str, Any] \| None:` |
| `backend/app/national_data/models/canonical_procedure.py` | 70 | `lab_id` | **RETAIN** | `LabOrder.lab_id,` |
| `backend/app/national_data/models/canonical_procedure.py` | 86 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabOrder.lab_id,` |
| `backend/app/national_data/models/canonical_procedure.py` | 86 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == LabOrder.lab_id,` |
| `backend/app/national_data/models/canonical_procedure.py` | 95 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/national_data/models/canonical_procedure.py` | 96 | `lab_id` | **RETAIN** | `query = query.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/national_data/models/canonical_procedure.py` | 96 | `lab_id` | **RETAIN** | `query = query.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/national_data/models/governance/DataLineageEntry.py` | 31 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True, index=True)` |
| `backend/app/national_data/models/governance/DataQualityCheck.py` | 31 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True, index=True)` |
| `backend/app/national_data/models/mdm/DeviceRegistry.py` | 10 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)` |
| `backend/app/national_data/models/mdm/DeviceRegistry.py` | 33 | `lab_id` | **RETAIN** | `Index("ix_dp_device_lab", "lab_id"),` |
| `backend/app/national_data/models/mdm/LocationRegistry.py` | 10 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True)` |
| `backend/app/national_data/models/warehouse/DimFacility.py` | 10 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True)` |
| `backend/app/national_data/models/warehouse/DimPatient.py` | 24 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=True, index=True)` |
| `backend/app/national_data/models/warehouse/DimPatient.py` | 30 | `lab_id` | **RETAIN** | `Index("ix_dw_dim_patient_lab", "lab_id"),` |
| `backend/app/national_data/models/warehouse/FactDiagnosis.py` | 20 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)` |
| `backend/app/national_data/models/warehouse/FactLabResult.py` | 27 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)` |
| `backend/app/national_data/models/warehouse/FactLabResult.py` | 37 | `lab_id` | **RETAIN** | `Index("ix_dw_fact_result_lab", "lab_id"),` |
| `backend/app/national_data/models/warehouse/FactPatientVisit.py` | 20 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)` |
| `backend/app/national_data/models/warehouse/FactPatientVisit.py` | 29 | `lab_id` | **RETAIN** | `Index("ix_dw_fact_visit_lab", "lab_id"),` |
| `backend/app/nhdw/kpi.py` | 13 | `lab_id` | **RETAIN** | `def bed_occupancy_rate(db: Session, lab_id: int, department_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 14 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/nhdw/kpi.py` | 14 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/nhdw/kpi.py` | 29 | `lab_id` | **RETAIN** | `def average_length_of_stay(db: Session, lab_id: int, department_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 35 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 35 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 50 | `lab_id` | **RETAIN** | `def admission_rate(db: Session, lab_id: int, days: int = 30, department_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 53 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 53 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 70 | `lab_id` | **RETAIN** | `def discharge_rate(db: Session, lab_id: int, days: int = 30, department_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 75 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 75 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 92 | `lab_id` | **RETAIN** | `def transfer_rate(db: Session, lab_id: int, days: int = 30, department_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 95 | `lab_id` | **RETAIN** | `Transfer.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 95 | `lab_id` | **RETAIN** | `Transfer.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 114 | `lab_id` | **RETAIN** | `def readmission_rate_30d(db: Session, lab_id: int, days: int = 30, department_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 123 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 123 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 133 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 133 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 150 | `lab_id` | **RETAIN** | `def emergency_wait_times(db: Session, lab_id: int, days: int = 7, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 156 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 156 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 188 | `lab_id` | **RETAIN** | `def or_utilization_rate(db: Session, lab_id: int, days: int = 30, hospital_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 190 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 190 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 197 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 197 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 212 | `lab_id` | **RETAIN** | `def bed_turnover_interval(db: Session, lab_id: int, department_id: int \| None = None, date_range: tuple[datetime, datetime] \| None = None) -> dict:` |
| `backend/app/nhdw/kpi.py` | 216 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 216 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 224 | `lab_id` | **RETAIN** | `bed_q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/nhdw/kpi.py` | 224 | `lab_id` | **RETAIN** | `bed_q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/nhdw/kpi.py` | 237 | `lab_id` | **RETAIN** | `def occupancy_by_department(db: Session, lab_id: int) -> list[dict]:` |
| `backend/app/nhdw/kpi.py` | 239 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id, ~Department.is_deleted,` |
| `backend/app/nhdw/kpi.py` | 239 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id, ~Department.is_deleted,` |
| `backend/app/nhdw/kpi.py` | 245 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 245 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 250 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 250 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 267 | `lab_id` | **RETAIN** | `def executive_summary(db: Session, lab_id: int) -> dict:` |
| `backend/app/nhdw/kpi.py` | 268 | `lab_id` | **RETAIN** | `occ = bed_occupancy_rate(db, lab_id)` |
| `backend/app/nhdw/kpi.py` | 269 | `lab_id` | **RETAIN** | `alos = average_length_of_stay(db, lab_id)` |
| `backend/app/nhdw/kpi.py` | 270 | `lab_id` | **RETAIN** | `adm = admission_rate(db, lab_id, 30)` |
| `backend/app/nhdw/kpi.py` | 271 | `lab_id` | **RETAIN** | `dis = discharge_rate(db, lab_id, 30)` |
| `backend/app/nhdw/kpi.py` | 272 | `lab_id` | **RETAIN** | `trf = transfer_rate(db, lab_id, 30)` |
| `backend/app/nhdw/kpi.py` | 273 | `lab_id` | **RETAIN** | `readm = readmission_rate_30d(db, lab_id, 30)` |
| `backend/app/nhdw/kpi.py` | 274 | `lab_id` | **RETAIN** | `ewt = emergency_wait_times(db, lab_id, 7)` |
| `backend/app/nhdw/kpi.py` | 275 | `lab_id` | **RETAIN** | `oru = or_utilization_rate(db, lab_id, 30)` |
| `backend/app/nhdw/kpi.py` | 276 | `lab_id` | **RETAIN** | `occ_by_dept = occupancy_by_department(db, lab_id)` |
| `backend/app/nhdw/kpi.py` | 278 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/kpi.py` | 278 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/offline.py` | 167 | `lab_id` | **RETAIN** | `def apply_batch(db: Session, lab_id: int, user_id: int, batch: SyncBatch) -> dict[str, Any]:` |
| `backend/app/nhdw/offline.py` | 176 | `lab_id` | **RETAIN** | `model.lab_id == lab_id,` |
| `backend/app/nhdw/offline.py` | 176 | `lab_id` | **RETAIN** | `model.lab_id == lab_id,` |
| `backend/app/nhdw/offline.py` | 183 | `lab_id` | **RETAIN** | `if k not in ("id", "lab_id", "created_at", "created_by", "version"):` |
| `backend/app/nhdw/offline.py` | 192 | `lab_id` | **RETAIN** | `if k not in ("id", "lab_id", "created_at", "created_by", "version"):` |
| `backend/app/nhdw/offline.py` | 199 | `lab_id` | **RETAIN** | `data.setdefault("lab_id", lab_id)` |
| `backend/app/nhdw/offline.py` | 199 | `lab_id` | **RETAIN** | `data.setdefault("lab_id", lab_id)` |
| `backend/app/nhdw/offline.py` | 213 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.sync.apply_batch", 0, lab_id, user_id, {` |
| `backend/app/nhdw/offline.py` | 221 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/nhdw/offline.py` | 229 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.sync.resolve_conflict", 0, lab_id, user_id, {` |
| `backend/app/nhdw/offline.py` | 240 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/nhdw/offline.py` | 260 | `lab_id` | **RETAIN** | `model.lab_id == lab_id,` |
| `backend/app/nhdw/offline.py` | 260 | `lab_id` | **RETAIN** | `model.lab_id == lab_id,` |
| `backend/app/nhdw/routes.py` | 13 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/nhdw/routes.py` | 51 | `lab_id` | **RETAIN** | `exclude = {"lab_id", "is_deleted", "deleted_at", "version"}` |
| `backend/app/nhdw/routes.py` | 323 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 325 | `lab_id` | **RETAIN** | `admissions = NHDWService.list_admissions(db, current_user.lab_id, department_id, status, skip, limit)` |
| `backend/app/nhdw/routes.py` | 327 | `lab_id` | **RETAIN** | `Admission.lab_id == current_user.lab_id, ~Admission.is_deleted,` |
| `backend/app/nhdw/routes.py` | 327 | `lab_id` | **RETAIN** | `Admission.lab_id == current_user.lab_id, ~Admission.is_deleted,` |
| `backend/app/nhdw/routes.py` | 336 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 338 | `lab_id` | **RETAIN** | `admissions = NHDWService.get_active_admissions(db, current_user.lab_id, department_id)` |
| `backend/app/nhdw/routes.py` | 346 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 348 | `lab_id` | **RETAIN** | `admissions = NHDWService.get_admission_history(db, patient_id, current_user.lab_id)` |
| `backend/app/nhdw/routes.py` | 356 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 361 | `lab_id` | **RETAIN** | `admission = NHDWService.create_admission(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 369 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 371 | `lab_id` | **RETAIN** | `return _model_to_dict(NHDWService.get_admission(db, admission_id, current_user.lab_id))` |
| `backend/app/nhdw/routes.py` | 379 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 384 | `lab_id` | **RETAIN** | `admission = NHDWService.update_admission(db, current_user.lab_id, current_user.id, admission_id, data)` |
| `backend/app/nhdw/routes.py` | 393 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 399 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, admission_id, data,` |
| `backend/app/nhdw/routes.py` | 409 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 412 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, admission_id, body.model_dump(exclude_none=True),` |
| `backend/app/nhdw/routes.py` | 421 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 429 | `lab_id` | **RETAIN** | `entry = NHDWService.add_queue_entry(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 441 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 444 | `lab_id` | **RETAIN** | `db, current_user.lab_id, department_id, queue_date, status, skip, limit,` |
| `backend/app/nhdw/routes.py` | 447 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 447 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 457 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 459 | `lab_id` | **RETAIN** | `entry = NHDWService.serve_queue_entry(db, current_user.lab_id, current_user.id, entry_id)` |
| `backend/app/nhdw/routes.py` | 467 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 469 | `lab_id` | **RETAIN** | `entry = NHDWService.complete_queue_entry(db, current_user.lab_id, current_user.id, entry_id)` |
| `backend/app/nhdw/routes.py` | 477 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 479 | `lab_id` | **RETAIN** | `entry = NHDWService.no_show_queue_entry(db, current_user.lab_id, current_user.id, entry_id)` |
| `backend/app/nhdw/routes.py` | 490 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 493 | `lab_id` | **RETAIN** | `db, current_user.lab_id, department_id, status, skip, limit,` |
| `backend/app/nhdw/routes.py` | 496 | `lab_id` | **RETAIN** | `WaitingListEntry.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 496 | `lab_id` | **RETAIN** | `WaitingListEntry.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 506 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 511 | `lab_id` | **RETAIN** | `entry = NHDWService.add_waiting_list(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 520 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 523 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, entry_id, body.model_dump(),` |
| `backend/app/nhdw/routes.py` | 536 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 539 | `lab_id` | **RETAIN** | `db, current_user.lab_id, assigned_to, status, patient_id, skip, limit,` |
| `backend/app/nhdw/routes.py` | 542 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 542 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 552 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 557 | `lab_id` | **RETAIN** | `task = NHDWService.create_clinical_task(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 566 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 569 | `lab_id` | **RETAIN** | `task = NHDWService.update_clinical_task(db, current_user.lab_id, current_user.id, task_id, data)` |
| `backend/app/nhdw/routes.py` | 578 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 580 | `lab_id` | **RETAIN** | `task = NHDWService.assign_clinical_task(db, current_user.lab_id, current_user.id, task_id, body.assigned_to)` |
| `backend/app/nhdw/routes.py` | 588 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 590 | `lab_id` | **RETAIN** | `task = NHDWService.complete_clinical_task(db, current_user.lab_id, current_user.id, task_id)` |
| `backend/app/nhdw/routes.py` | 598 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 603 | `lab_id` | **RETAIN** | `ward_round = NHDWService.create_ward_round(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 616 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 619 | `lab_id` | **RETAIN** | `db, current_user.lab_id, department_id, patient_id, from_date, to_date, skip, limit,` |
| `backend/app/nhdw/routes.py` | 622 | `lab_id` | **RETAIN** | `WardRound.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 622 | `lab_id` | **RETAIN** | `WardRound.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 632 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 634 | `lab_id` | **RETAIN** | `return _model_to_dict(NHDWService.get_ward_round(db, round_id, current_user.lab_id))` |
| `backend/app/nhdw/routes.py` | 641 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 643 | `lab_id` | **RETAIN** | `plans = NHDWService.get_care_plans(db, patient_id, current_user.lab_id)` |
| `backend/app/nhdw/routes.py` | 651 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 657 | `lab_id` | **RETAIN** | `plan = NHDWService.create_care_plan(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 666 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 669 | `lab_id` | **RETAIN** | `plan = NHDWService.update_care_plan(db, current_user.lab_id, current_user.id, plan_id, data)` |
| `backend/app/nhdw/routes.py` | 678 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 680 | `lab_id` | **RETAIN** | `plan = NHDWService.review_care_plan(db, current_user.lab_id, current_user.id, plan_id, body.review_notes)` |
| `backend/app/nhdw/routes.py` | 687 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 689 | `lab_id` | **RETAIN** | `return executive_summary(db, current_user.lab_id)` |
| `backend/app/nhdw/routes.py` | 696 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 698 | `lab_id` | **RETAIN** | `return bed_occupancy_rate(db, current_user.lab_id, department_id)` |
| `backend/app/nhdw/routes.py` | 705 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 707 | `lab_id` | **RETAIN** | `return bed_occupancy_rate(db, current_user.lab_id, department_id)` |
| `backend/app/nhdw/routes.py` | 715 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 717 | `lab_id` | **RETAIN** | `return admission_rate(db, current_user.lab_id, days, department_id)` |
| `backend/app/nhdw/routes.py` | 725 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 727 | `lab_id` | **RETAIN** | `return discharge_rate(db, current_user.lab_id, days, department_id)` |
| `backend/app/nhdw/routes.py` | 735 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 737 | `lab_id` | **RETAIN** | `return transfer_rate(db, current_user.lab_id, days, department_id)` |
| `backend/app/nhdw/routes.py` | 744 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 746 | `lab_id` | **RETAIN** | `return average_length_of_stay(db, current_user.lab_id, department_id)` |
| `backend/app/nhdw/routes.py` | 754 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 756 | `lab_id` | **RETAIN** | `return readmission_rate_30d(db, current_user.lab_id, days, department_id)` |
| `backend/app/nhdw/routes.py` | 763 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 765 | `lab_id` | **RETAIN** | `return emergency_wait_times(db, current_user.lab_id, days)` |
| `backend/app/nhdw/routes.py` | 772 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 774 | `lab_id` | **RETAIN** | `return or_utilization_rate(db, current_user.lab_id, days)` |
| `backend/app/nhdw/routes.py` | 781 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 783 | `lab_id` | **RETAIN** | `return bed_turnover_interval(db, current_user.lab_id, department_id)` |
| `backend/app/nhdw/routes.py` | 789 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 791 | `lab_id` | **RETAIN** | `return NHDWService.admin_dashboard(db, current_user.lab_id)` |
| `backend/app/nhdw/routes.py` | 797 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 799 | `lab_id` | **RETAIN** | `return NHDWService.executive_dashboard(db, current_user.lab_id)` |
| `backend/app/nhdw/routes.py` | 805 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 807 | `lab_id` | **RETAIN** | `return NHDWService.clinical_dashboard(db, current_user.lab_id)` |
| `backend/app/nhdw/routes.py` | 816 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 819 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, direction, skip, limit,` |
| `backend/app/nhdw/routes.py` | 822 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 822 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 833 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 838 | `lab_id` | **RETAIN** | `msg = NHDWService.send_message(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 846 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 848 | `lab_id` | **RETAIN** | `return _model_to_dict(NHDWService.get_message(db, message_id, current_user.lab_id))` |
| `backend/app/nhdw/routes.py` | 855 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 857 | `lab_id` | **RETAIN** | `msg = NHDWService.mark_message_read(db, current_user.lab_id, current_user.id, message_id)` |
| `backend/app/nhdw/routes.py` | 865 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 870 | `lab_id` | **RETAIN** | `alert = NHDWService.create_alert(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 881 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 883 | `lab_id` | **RETAIN** | `alerts = NHDWService.list_alerts(db, current_user.lab_id, severity, is_resolved, skip, limit)` |
| `backend/app/nhdw/routes.py` | 885 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 885 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == current_user.lab_id,` |
| `backend/app/nhdw/routes.py` | 895 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 897 | `lab_id` | **RETAIN** | `alert = NHDWService.acknowledge_alert(db, current_user.lab_id, current_user.id, alert_id)` |
| `backend/app/nhdw/routes.py` | 905 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 907 | `lab_id` | **RETAIN** | `alert = NHDWService.resolve_alert(db, current_user.lab_id, current_user.id, alert_id)` |
| `backend/app/nhdw/routes.py` | 919 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 922 | `lab_id` | **RETAIN** | `db, current_user.lab_id, resource_type, resource_id, scheduled_date, skip, limit,` |
| `backend/app/nhdw/routes.py` | 931 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 936 | `lab_id` | **RETAIN** | `schedule = NHDWService.create_resource_schedule(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 945 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 948 | `lab_id` | **RETAIN** | `schedule = NHDWService.update_resource_schedule(db, current_user.lab_id, current_user.id, schedule_id, data)` |
| `backend/app/nhdw/routes.py` | 960 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 963 | `lab_id` | **RETAIN** | `db, current_user.lab_id, patient_id, provider_id, status, skip, limit,` |
| `backend/app/nhdw/routes.py` | 972 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 977 | `lab_id` | **RETAIN** | `session = NHDWService.create_telemedicine_session(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 985 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 987 | `lab_id` | **RETAIN** | `session = NHDWService.start_telemedicine_session(db, current_user.lab_id, session_id)` |
| `backend/app/nhdw/routes.py` | 996 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 999 | `lab_id` | **RETAIN** | `db, current_user.lab_id, session_id, body.model_dump(exclude_none=True),` |
| `backend/app/nhdw/routes.py` | 1008 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 1010 | `lab_id` | **RETAIN** | `config = NHDWService.get_dashboard_config(db, current_user.lab_id, role)` |
| `backend/app/nhdw/routes.py` | 1023 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 1026 | `lab_id` | **RETAIN** | `config = NHDWService.save_dashboard_config(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/routes.py` | 1038 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 1041 | `lab_id` | **RETAIN** | `db, current_user.lab_id, department_id, shift_type, shift_date, skip, limit,` |
| `backend/app/nhdw/routes.py` | 1050 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nhdw/routes.py` | 1055 | `lab_id` | **RETAIN** | `report = NHDWService.create_shift_report(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nhdw/services.py` | 38 | `lab_id` | **RETAIN** | `def register_patient(db: Session, lab_id: int, user_id: int, data: dict) -> Patient:` |
| `backend/app/nhdw/services.py` | 39 | `lab_id` | **RETAIN** | `data.setdefault("lab_id", lab_id)` |
| `backend/app/nhdw/services.py` | 39 | `lab_id` | **RETAIN** | `data.setdefault("lab_id", lab_id)` |
| `backend/app/nhdw/services.py` | 40 | `lab_id` | **RETAIN** | `return _create_patient(db, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 43 | `lab_id` | **RETAIN** | `def get_patient(db: Session, patient_id: int, lab_id: int) -> Patient:` |
| `backend/app/nhdw/services.py` | 44 | `lab_id` | **RETAIN** | `patient = get_patient_by_id(db, patient_id, lab_id)` |
| `backend/app/nhdw/services.py` | 50 | `lab_id` | **RETAIN** | `def search_patients(db: Session, lab_id: int, search: str \| None = None, skip: int = 0, limit: int = 50) -> dict:` |
| `backend/app/nhdw/services.py` | 51 | `lab_id` | **RETAIN** | `return _list_patients(db, lab_id, search, skip, limit)` |
| `backend/app/nhdw/services.py` | 54 | `lab_id` | **RETAIN** | `def create_admission(db: Session, lab_id: int, user_id: int, data: dict) -> Admission:` |
| `backend/app/nhdw/services.py` | 59 | `lab_id` | **RETAIN** | `Bed.id == bed_id, Bed.lab_id == lab_id, ~Bed.is_deleted,` |
| `backend/app/nhdw/services.py` | 59 | `lab_id` | **RETAIN** | `Bed.id == bed_id, Bed.lab_id == lab_id, ~Bed.is_deleted,` |
| `backend/app/nhdw/services.py` | 77 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 77 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 82 | `lab_id` | **RETAIN** | `admission = Admission(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 82 | `lab_id` | **RETAIN** | `admission = Admission(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 85 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.admission.create", admission.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 89 | `lab_id` | **RETAIN** | `def get_admission(db: Session, admission_id: str, lab_id: int) -> Admission:` |
| `backend/app/nhdw/services.py` | 92 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 92 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 100 | `lab_id` | **RETAIN** | `def update_admission(db: Session, lab_id: int, user_id: int, admission_id: str, data: dict) -> Admission:` |
| `backend/app/nhdw/services.py` | 101 | `lab_id` | **RETAIN** | `admission = NHDWService.get_admission(db, admission_id, lab_id)` |
| `backend/app/nhdw/services.py` | 109 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.admission.update", admission_id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 114 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, department_id: int \| None = None,` |
| `backend/app/nhdw/services.py` | 118 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id, ~Admission.is_deleted,` |
| `backend/app/nhdw/services.py` | 118 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id, ~Admission.is_deleted,` |
| `backend/app/nhdw/services.py` | 127 | `lab_id` | **RETAIN** | `def get_active_admissions(db: Session, lab_id: int, department_id: int \| None = None) -> list[Admission]:` |
| `backend/app/nhdw/services.py` | 129 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 129 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 138 | `lab_id` | **RETAIN** | `def get_admission_history(db: Session, patient_id: int, lab_id: int) -> list[Admission]:` |
| `backend/app/nhdw/services.py` | 141 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 141 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 147 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, admission_id: str, data: dict,` |
| `backend/app/nhdw/services.py` | 149 | `lab_id` | **RETAIN** | `admission = NHDWService.get_admission(db, admission_id, lab_id)` |
| `backend/app/nhdw/services.py` | 158 | `lab_id` | **RETAIN** | `Bed.id == admission.bed_id, Bed.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 158 | `lab_id` | **RETAIN** | `Bed.id == admission.bed_id, Bed.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 165 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/nhdw/services.py` | 165 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/nhdw/services.py` | 171 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.discharge.create", discharge.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 176 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, admission_id: str, data: dict,` |
| `backend/app/nhdw/services.py` | 178 | `lab_id` | **RETAIN** | `admission = NHDWService.get_admission(db, admission_id, lab_id)` |
| `backend/app/nhdw/services.py` | 183 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 183 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 204 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/nhdw/services.py` | 204 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/nhdw/services.py` | 220 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.transfer.create", transfer.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 224 | `lab_id` | **RETAIN** | `def add_queue_entry(db: Session, lab_id: int, user_id: int, data: dict) -> QueueEntry:` |
| `backend/app/nhdw/services.py` | 225 | `lab_id` | **RETAIN** | `entry = QueueEntry(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 225 | `lab_id` | **RETAIN** | `entry = QueueEntry(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 228 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.queue.add", entry.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 233 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, department_id: int \| None = None,` |
| `backend/app/nhdw/services.py` | 238 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id, ~QueueEntry.is_deleted,` |
| `backend/app/nhdw/services.py` | 238 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id, ~QueueEntry.is_deleted,` |
| `backend/app/nhdw/services.py` | 251 | `lab_id` | **RETAIN** | `def serve_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:` |
| `backend/app/nhdw/services.py` | 252 | `lab_id` | **RETAIN** | `return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.SEEN)` |
| `backend/app/nhdw/services.py` | 255 | `lab_id` | **RETAIN** | `def complete_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:` |
| `backend/app/nhdw/services.py` | 256 | `lab_id` | **RETAIN** | `return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.COMPLETED)` |
| `backend/app/nhdw/services.py` | 259 | `lab_id` | **RETAIN** | `def no_show_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:` |
| `backend/app/nhdw/services.py` | 260 | `lab_id` | **RETAIN** | `return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.NO_SHOW)` |
| `backend/app/nhdw/services.py` | 263 | `lab_id` | **RETAIN** | `def cancel_queue_entry(db: Session, lab_id: int, user_id: int, entry_id: str) -> QueueEntry:` |
| `backend/app/nhdw/services.py` | 264 | `lab_id` | **RETAIN** | `return NHDWService._update_queue_status(db, lab_id, user_id, entry_id, QueueStatus.CANCELLED)` |
| `backend/app/nhdw/services.py` | 267 | `lab_id` | **RETAIN** | `def _update_queue_status(db: Session, lab_id: int, user_id: int, entry_id: str, status: QueueStatus) -> QueueEntry:` |
| `backend/app/nhdw/services.py` | 270 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 270 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 285 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.queue.status", entry_id, lab_id, user_id, {"status": status.value})` |
| `backend/app/nhdw/services.py` | 289 | `lab_id` | **RETAIN** | `def get_wait_times(db: Session, lab_id: int, department_id: int \| None = None) -> dict:` |
| `backend/app/nhdw/services.py` | 291 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 291 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 310 | `lab_id` | **RETAIN** | `def add_waiting_list(db: Session, lab_id: int, user_id: int, data: dict) -> WaitingListEntry:` |
| `backend/app/nhdw/services.py` | 311 | `lab_id` | **RETAIN** | `entry = WaitingListEntry(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 311 | `lab_id` | **RETAIN** | `entry = WaitingListEntry(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 314 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.waiting_list.add", entry.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 319 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, department_id: int \| None = None,` |
| `backend/app/nhdw/services.py` | 323 | `lab_id` | **RETAIN** | `WaitingListEntry.lab_id == lab_id, ~WaitingListEntry.is_deleted,` |
| `backend/app/nhdw/services.py` | 323 | `lab_id` | **RETAIN** | `WaitingListEntry.lab_id == lab_id, ~WaitingListEntry.is_deleted,` |
| `backend/app/nhdw/services.py` | 332 | `lab_id` | **RETAIN** | `def convert_waiting_to_admission(db: Session, lab_id: int, user_id: int, entry_id: str, data: dict) -> Admission:` |
| `backend/app/nhdw/services.py` | 335 | `lab_id` | **RETAIN** | `WaitingListEntry.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 335 | `lab_id` | **RETAIN** | `WaitingListEntry.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 343 | `lab_id` | **RETAIN** | `admission = NHDWService.create_admission(db, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 346 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.waiting_list.convert", entry_id, lab_id, user_id, {"admission_id": admission.id})` |
| `backend/app/nhdw/services.py` | 350 | `lab_id` | **RETAIN** | `def create_clinical_task(db: Session, lab_id: int, user_id: int, data: dict) -> ClinicalTask:` |
| `backend/app/nhdw/services.py` | 351 | `lab_id` | **RETAIN** | `task = ClinicalTask(lab_id=lab_id, created_by=user_id, assigned_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 351 | `lab_id` | **RETAIN** | `task = ClinicalTask(lab_id=lab_id, created_by=user_id, assigned_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 354 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.task.create", task.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 358 | `lab_id` | **RETAIN** | `def update_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str, data: dict) -> ClinicalTask:` |
| `backend/app/nhdw/services.py` | 361 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 361 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 371 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.task.update", task_id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 375 | `lab_id` | **RETAIN** | `def assign_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str, assign_to: int) -> ClinicalTask:` |
| `backend/app/nhdw/services.py` | 378 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 378 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 387 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.task.assign", task_id, lab_id, user_id, {"assigned_to": assign_to})` |
| `backend/app/nhdw/services.py` | 391 | `lab_id` | **RETAIN** | `def complete_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str) -> ClinicalTask:` |
| `backend/app/nhdw/services.py` | 394 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 394 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 403 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.task.complete", task_id, lab_id, user_id)` |
| `backend/app/nhdw/services.py` | 407 | `lab_id` | **RETAIN** | `def defer_clinical_task(db: Session, lab_id: int, user_id: int, task_id: str) -> ClinicalTask:` |
| `backend/app/nhdw/services.py` | 410 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 410 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 422 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, assigned_to: int \| None = None,` |
| `backend/app/nhdw/services.py` | 427 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id, ~ClinicalTask.is_deleted,` |
| `backend/app/nhdw/services.py` | 427 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id, ~ClinicalTask.is_deleted,` |
| `backend/app/nhdw/services.py` | 438 | `lab_id` | **RETAIN** | `def get_tasks_by_patient(db: Session, patient_id: int, lab_id: int) -> list[ClinicalTask]:` |
| `backend/app/nhdw/services.py` | 441 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 441 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 446 | `lab_id` | **RETAIN** | `def get_tasks_by_nurse(db: Session, assigned_to: int, lab_id: int) -> list[ClinicalTask]:` |
| `backend/app/nhdw/services.py` | 449 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 449 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 454 | `lab_id` | **RETAIN** | `def create_ward_round(db: Session, lab_id: int, user_id: int, data: dict) -> WardRound:` |
| `backend/app/nhdw/services.py` | 455 | `lab_id` | **RETAIN** | `ward_round = WardRound(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 455 | `lab_id` | **RETAIN** | `ward_round = WardRound(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 458 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.ward_round.create", ward_round.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 462 | `lab_id` | **RETAIN** | `def add_ward_round_participant(db: Session, lab_id: int, round_id: str, participant: dict) -> WardRound:` |
| `backend/app/nhdw/services.py` | 465 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 465 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 477 | `lab_id` | **RETAIN** | `def update_ward_round_findings(db: Session, lab_id: int, user_id: int, round_id: str, data: dict) -> WardRound:` |
| `backend/app/nhdw/services.py` | 480 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 480 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 494 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, department_id: int \| None = None,` |
| `backend/app/nhdw/services.py` | 500 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id, ~WardRound.is_deleted,` |
| `backend/app/nhdw/services.py` | 500 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id, ~WardRound.is_deleted,` |
| `backend/app/nhdw/services.py` | 513 | `lab_id` | **RETAIN** | `def get_ward_round(db: Session, round_id: str, lab_id: int) -> WardRound:` |
| `backend/app/nhdw/services.py` | 516 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 516 | `lab_id` | **RETAIN** | `WardRound.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 524 | `lab_id` | **RETAIN** | `def create_care_plan(db: Session, lab_id: int, user_id: int, data: dict) -> CarePlan:` |
| `backend/app/nhdw/services.py` | 525 | `lab_id` | **RETAIN** | `care_plan = CarePlan(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 525 | `lab_id` | **RETAIN** | `care_plan = CarePlan(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 528 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.care_plan.create", care_plan.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 532 | `lab_id` | **RETAIN** | `def get_care_plans(db: Session, patient_id: int, lab_id: int) -> list[CarePlan]:` |
| `backend/app/nhdw/services.py` | 535 | `lab_id` | **RETAIN** | `CarePlan.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 535 | `lab_id` | **RETAIN** | `CarePlan.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 540 | `lab_id` | **RETAIN** | `def update_care_plan(db: Session, lab_id: int, user_id: int, plan_id: str, data: dict) -> CarePlan:` |
| `backend/app/nhdw/services.py` | 543 | `lab_id` | **RETAIN** | `CarePlan.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 543 | `lab_id` | **RETAIN** | `CarePlan.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 553 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.care_plan.update", plan_id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 557 | `lab_id` | **RETAIN** | `def review_care_plan(db: Session, lab_id: int, user_id: int, plan_id: str, review_notes: str \| None = None) -> CarePlan:` |
| `backend/app/nhdw/services.py` | 560 | `lab_id` | **RETAIN** | `CarePlan.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 560 | `lab_id` | **RETAIN** | `CarePlan.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 570 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.care_plan.review", plan_id, lab_id, user_id)` |
| `backend/app/nhdw/services.py` | 574 | `lab_id` | **RETAIN** | `def occupancy_dashboard(db: Session, lab_id: int, department_id: int \| None = None) -> dict:` |
| `backend/app/nhdw/services.py` | 575 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/nhdw/services.py` | 575 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/nhdw/services.py` | 592 | `lab_id` | **RETAIN** | `def room_occupancy_by_department(db: Session, lab_id: int) -> list[dict]:` |
| `backend/app/nhdw/services.py` | 594 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id, ~Department.is_deleted,` |
| `backend/app/nhdw/services.py` | 594 | `lab_id` | **RETAIN** | `Department.lab_id == lab_id, ~Department.is_deleted,` |
| `backend/app/nhdw/services.py` | 600 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 600 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 605 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 605 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 617 | `lab_id` | **RETAIN** | `def send_message(db: Session, lab_id: int, user_id: int, data: dict) -> HospitalMessage:` |
| `backend/app/nhdw/services.py` | 618 | `lab_id` | **RETAIN** | `msg = HospitalMessage(lab_id=lab_id, created_by=user_id, sender_id=user_id, **data)` |
| `backend/app/nhdw/services.py` | 618 | `lab_id` | **RETAIN** | `msg = HospitalMessage(lab_id=lab_id, created_by=user_id, sender_id=user_id, **data)` |
| `backend/app/nhdw/services.py` | 621 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.message.send", msg.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 626 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nhdw/services.py` | 630 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id, ~HospitalMessage.is_deleted,` |
| `backend/app/nhdw/services.py` | 630 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id, ~HospitalMessage.is_deleted,` |
| `backend/app/nhdw/services.py` | 639 | `lab_id` | **RETAIN** | `def get_message(db: Session, message_id: str, lab_id: int) -> HospitalMessage:` |
| `backend/app/nhdw/services.py` | 642 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 642 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 650 | `lab_id` | **RETAIN** | `def mark_message_read(db: Session, lab_id: int, user_id: int, message_id: str) -> HospitalMessage:` |
| `backend/app/nhdw/services.py` | 653 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 653 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 664 | `lab_id` | **RETAIN** | `def get_message_thread(db: Session, message_id: str, lab_id: int) -> list[HospitalMessage]:` |
| `backend/app/nhdw/services.py` | 667 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 667 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 675 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 675 | `lab_id` | **RETAIN** | `HospitalMessage.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 682 | `lab_id` | **RETAIN** | `def create_alert(db: Session, lab_id: int, user_id: int, data: dict) -> HospitalAlert:` |
| `backend/app/nhdw/services.py` | 683 | `lab_id` | **RETAIN** | `alert = HospitalAlert(lab_id=lab_id, created_by=user_id, triggered_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 683 | `lab_id` | **RETAIN** | `alert = HospitalAlert(lab_id=lab_id, created_by=user_id, triggered_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 686 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.alert.create", alert.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 691 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, severity: AlertSeverity \| None = None,` |
| `backend/app/nhdw/services.py` | 695 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id, ~HospitalAlert.is_deleted,` |
| `backend/app/nhdw/services.py` | 695 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id, ~HospitalAlert.is_deleted,` |
| `backend/app/nhdw/services.py` | 704 | `lab_id` | **RETAIN** | `def acknowledge_alert(db: Session, lab_id: int, user_id: int, alert_id: str) -> HospitalAlert:` |
| `backend/app/nhdw/services.py` | 707 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 707 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 720 | `lab_id` | **RETAIN** | `def resolve_alert(db: Session, lab_id: int, user_id: int, alert_id: str) -> HospitalAlert:` |
| `backend/app/nhdw/services.py` | 723 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 723 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 732 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.alert.resolve", alert_id, lab_id, user_id)` |
| `backend/app/nhdw/services.py` | 736 | `lab_id` | **RETAIN** | `def escalate_alert(db: Session, lab_id: int, user_id: int, alert_id: str) -> HospitalAlert:` |
| `backend/app/nhdw/services.py` | 739 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 739 | `lab_id` | **RETAIN** | `HospitalAlert.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 755 | `lab_id` | **RETAIN** | `def create_telemedicine_session(db: Session, lab_id: int, user_id: int, data: dict) -> TelemedicineSession:` |
| `backend/app/nhdw/services.py` | 756 | `lab_id` | **RETAIN** | `session = TelemedicineSession(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 756 | `lab_id` | **RETAIN** | `session = TelemedicineSession(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 759 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.telemedicine.create", session.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 764 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int \| None = None,` |
| `backend/app/nhdw/services.py` | 769 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 769 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 781 | `lab_id` | **RETAIN** | `def start_telemedicine_session(db: Session, lab_id: int, session_id: str) -> TelemedicineSession:` |
| `backend/app/nhdw/services.py` | 784 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 784 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 795 | `lab_id` | **RETAIN** | `def end_telemedicine_session(db: Session, lab_id: int, session_id: str, data: dict \| None = None) -> TelemedicineSession:` |
| `backend/app/nhdw/services.py` | 798 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 798 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 814 | `lab_id` | **RETAIN** | `def record_telemedicine_session(db: Session, lab_id: int, user_id: int, session_id: str, data: dict) -> TelemedicineSession:` |
| `backend/app/nhdw/services.py` | 817 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 817 | `lab_id` | **RETAIN** | `TelemedicineSession.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 830 | `lab_id` | **RETAIN** | `def create_resource_schedule(db: Session, lab_id: int, user_id: int, data: dict) -> ResourceSchedule:` |
| `backend/app/nhdw/services.py` | 831 | `lab_id` | **RETAIN** | `schedule = ResourceSchedule(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 831 | `lab_id` | **RETAIN** | `schedule = ResourceSchedule(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nhdw/services.py` | 834 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.resource_schedule.create", schedule.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 838 | `lab_id` | **RETAIN** | `def update_resource_schedule(db: Session, lab_id: int, user_id: int, schedule_id: str, data: dict) -> ResourceSchedule:` |
| `backend/app/nhdw/services.py` | 841 | `lab_id` | **RETAIN** | `ResourceSchedule.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 841 | `lab_id` | **RETAIN** | `ResourceSchedule.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 855 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, resource_type: str \| None = None,` |
| `backend/app/nhdw/services.py` | 860 | `lab_id` | **RETAIN** | `ResourceSchedule.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 860 | `lab_id` | **RETAIN** | `ResourceSchedule.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 872 | `lab_id` | **RETAIN** | `def save_dashboard_config(db: Session, lab_id: int, user_id: int, data: dict) -> DashboardConfiguration:` |
| `backend/app/nhdw/services.py` | 875 | `lab_id` | **RETAIN** | `DashboardConfiguration.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 875 | `lab_id` | **RETAIN** | `DashboardConfiguration.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 885 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.dashboard_config.update", existing.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 888 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id, user_id=user_id, **data,` |
| `backend/app/nhdw/services.py` | 888 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id, user_id=user_id, **data,` |
| `backend/app/nhdw/services.py` | 892 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.dashboard_config.create", config.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 896 | `lab_id` | **RETAIN** | `def get_dashboard_config(db: Session, lab_id: int, role: str) -> DashboardConfiguration \| None:` |
| `backend/app/nhdw/services.py` | 899 | `lab_id` | **RETAIN** | `DashboardConfiguration.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 899 | `lab_id` | **RETAIN** | `DashboardConfiguration.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 906 | `lab_id` | **RETAIN** | `DashboardConfiguration.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 906 | `lab_id` | **RETAIN** | `DashboardConfiguration.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 911 | `lab_id` | **RETAIN** | `def create_shift_report(db: Session, lab_id: int, user_id: int, data: dict) -> ShiftReport:` |
| `backend/app/nhdw/services.py` | 912 | `lab_id` | **RETAIN** | `report = ShiftReport(lab_id=lab_id, created_by=user_id, report_author=user_id, **data)` |
| `backend/app/nhdw/services.py` | 912 | `lab_id` | **RETAIN** | `report = ShiftReport(lab_id=lab_id, created_by=user_id, report_author=user_id, **data)` |
| `backend/app/nhdw/services.py` | 915 | `lab_id` | **RETAIN** | `log_action(db, "nhdw.shift_report.create", report.id, lab_id, user_id, data)` |
| `backend/app/nhdw/services.py` | 920 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, department_id: int \| None = None,` |
| `backend/app/nhdw/services.py` | 925 | `lab_id` | **RETAIN** | `ShiftReport.lab_id == lab_id, ~ShiftReport.is_deleted,` |
| `backend/app/nhdw/services.py` | 925 | `lab_id` | **RETAIN** | `ShiftReport.lab_id == lab_id, ~ShiftReport.is_deleted,` |
| `backend/app/nhdw/services.py` | 936 | `lab_id` | **RETAIN** | `def hospital_kpis(db: Session, lab_id: int, days: int = 30) -> dict:` |
| `backend/app/nhdw/services.py` | 946 | `lab_id` | **RETAIN** | `"bed_occupancy": bed_occupancy_rate(db, lab_id),` |
| `backend/app/nhdw/services.py` | 947 | `lab_id` | **RETAIN** | `"average_length_of_stay": average_length_of_stay(db, lab_id),` |
| `backend/app/nhdw/services.py` | 948 | `lab_id` | **RETAIN** | `"admissions_30d": admission_rate(db, lab_id, days),` |
| `backend/app/nhdw/services.py` | 949 | `lab_id` | **RETAIN** | `"discharges_30d": discharge_rate(db, lab_id, days),` |
| `backend/app/nhdw/services.py` | 950 | `lab_id` | **RETAIN** | `"transfers_30d": transfer_rate(db, lab_id, days),` |
| `backend/app/nhdw/services.py` | 951 | `lab_id` | **RETAIN** | `"readmissions_30d": readmission_rate_30d(db, lab_id, days),` |
| `backend/app/nhdw/services.py` | 955 | `lab_id` | **RETAIN** | `def admin_dashboard(db: Session, lab_id: int) -> dict:` |
| `backend/app/nhdw/services.py` | 964 | `lab_id` | **RETAIN** | `"occupancy": bed_occupancy_rate(db, lab_id),` |
| `backend/app/nhdw/services.py` | 965 | `lab_id` | **RETAIN** | `"occupancy_by_department": occupancy_by_department(db, lab_id),` |
| `backend/app/nhdw/services.py` | 966 | `lab_id` | **RETAIN** | `"admissions_today": admission_rate(db, lab_id, 1)["total_admissions"],` |
| `backend/app/nhdw/services.py` | 967 | `lab_id` | **RETAIN** | `"discharges_today": discharge_rate(db, lab_id, 1)["total_discharges"],` |
| `backend/app/nhdw/services.py` | 968 | `lab_id` | **RETAIN** | `"transfers_today": transfer_rate(db, lab_id, 1)["total_transfers"],` |
| `backend/app/nhdw/services.py` | 970 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 970 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 977 | `lab_id` | **RETAIN** | `def executive_dashboard(db: Session, lab_id: int) -> dict:` |
| `backend/app/nhdw/services.py` | 989 | `lab_id` | **RETAIN** | `"occupancy": bed_occupancy_rate(db, lab_id),` |
| `backend/app/nhdw/services.py` | 990 | `lab_id` | **RETAIN** | `"alos": average_length_of_stay(db, lab_id),` |
| `backend/app/nhdw/services.py` | 991 | `lab_id` | **RETAIN** | `"admissions_30d": admission_rate(db, lab_id, 30)["total_admissions"],` |
| `backend/app/nhdw/services.py` | 992 | `lab_id` | **RETAIN** | `"discharges_30d": discharge_rate(db, lab_id, 30)["total_discharges"],` |
| `backend/app/nhdw/services.py` | 993 | `lab_id` | **RETAIN** | `"transfers_30d": transfer_rate(db, lab_id, 30)["total_transfers"],` |
| `backend/app/nhdw/services.py` | 994 | `lab_id` | **RETAIN** | `"readmission_rate_30d": readmission_rate_30d(db, lab_id, 30),` |
| `backend/app/nhdw/services.py` | 995 | `lab_id` | **RETAIN** | `"or_utilization": or_utilization_rate(db, lab_id),` |
| `backend/app/nhdw/services.py` | 996 | `lab_id` | **RETAIN** | `"emergency_wait_times": emergency_wait_times(db, lab_id, 7),` |
| `backend/app/nhdw/services.py` | 998 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 998 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 1005 | `lab_id` | **RETAIN** | `def clinical_dashboard(db: Session, lab_id: int) -> dict:` |
| `backend/app/nhdw/services.py` | 1007 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 1007 | `lab_id` | **RETAIN** | `ClinicalTask.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 1012 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 1012 | `lab_id` | **RETAIN** | `Admission.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 1017 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nhdw/services.py` | 1017 | `lab_id` | **RETAIN** | `QueueEntry.lab_id == lab_id,` |
| `backend/app/nursing/coordination.py` | 19 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 24 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 24 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 34 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.physician_message", "coordination", None, user_id, lab_id, msg)` |
| `backend/app/nursing/coordination.py` | 39 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 43 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 43 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 50 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.lab_request", "coordination", None, user_id, lab_id, req)` |
| `backend/app/nursing/coordination.py` | 59 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 63 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 63 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 71 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.radiology", "coordination", None, user_id, lab_id, order)` |
| `backend/app/nursing/coordination.py` | 80 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 84 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 84 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 93 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.pharmacy", "coordination", None, user_id, lab_id, req)` |
| `backend/app/nursing/coordination.py` | 102 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 107 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 107 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 116 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.referral", "coordination", None, user_id, lab_id, referral)` |
| `backend/app/nursing/coordination.py` | 125 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 130 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 130 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 138 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.discharge_plan", "coordination", None, user_id, lab_id, plan)` |
| `backend/app/nursing/coordination.py` | 147 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 151 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 151 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 158 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.family_communication", "coordination", None, user_id, lab_id, log_entry)` |
| `backend/app/nursing/coordination.py` | 167 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/nursing/coordination.py` | 172 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 172 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/nursing/coordination.py` | 180 | `lab_id` | **RETAIN** | `log_action(db, "nursing.coordination.home_care_handover", "coordination", None, user_id, lab_id, handover)` |
| `backend/app/nursing/medication.py` | 84 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, admin_data: dict,` |
| `backend/app/nursing/medication.py` | 87 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/nursing/medication.py` | 87 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/nursing/medication.py` | 94 | `lab_id` | **RETAIN** | `log_action(db, "nursing.medication.administer", "medication_administration", admin.id, user_id, lab_id, admin_data)` |
| `backend/app/nursing/medication.py` | 99 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/medication.py` | 106 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 106 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 134 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, window_minutes: int = 30,` |
| `backend/app/nursing/medication.py` | 139 | `lab_id` | **RETAIN** | `MedicationAdministration.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 139 | `lab_id` | **RETAIN** | `MedicationAdministration.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 164 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/medication.py` | 169 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 169 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 188 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, nurse_id: str, medication_admin_id: str,` |
| `backend/app/nursing/medication.py` | 192 | `lab_id` | **RETAIN** | `MedicationAdministration.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 192 | `lab_id` | **RETAIN** | `MedicationAdministration.lab_id == lab_id,` |
| `backend/app/nursing/medication.py` | 199 | `lab_id` | **RETAIN** | `medication_admin_id, nurse_id, lab_id,` |
| `backend/app/nursing/routes.py` | 13 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/nursing/routes.py` | 35 | `lab_id` | **RETAIN** | `exclude = {"lab_id", "is_deleted", "deleted_at", "version"}` |
| `backend/app/nursing/routes.py` | 441 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 444 | `lab_id` | **RETAIN** | `return NursingService.get_nurse_dashboard(db, current_user.lab_id, str(current_user.id))` |
| `backend/app/nursing/routes.py` | 449 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 455 | `lab_id` | **RETAIN** | `NursingShift.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 455 | `lab_id` | **RETAIN** | `NursingShift.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 470 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 474 | `lab_id` | **RETAIN** | `return NursingService.get_assigned_patients(db, current_user.lab_id, nurse)` |
| `backend/app/nursing/routes.py` | 480 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 484 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id,` |
| `backend/app/nursing/routes.py` | 494 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 497 | `lab_id` | **RETAIN** | `NursingService.unassign_patient(db, current_user.lab_id, current_user.id, body.nurse_id, body.patient_id)` |
| `backend/app/nursing/routes.py` | 516 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 520 | `lab_id` | **RETAIN** | `db, current_user.lab_id, assigned_to, patient_id,` |
| `backend/app/nursing/routes.py` | 530 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 547 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 547 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 557 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 560 | `lab_id` | **RETAIN** | `task = NursingService.create_task(db, current_user.lab_id, current_user.id, body.model_dump(exclude_none=True))` |
| `backend/app/nursing/routes.py` | 568 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 574 | `lab_id` | **RETAIN** | `task = NursingService.update_task(db, current_user.lab_id, current_user.id, task_id, data)` |
| `backend/app/nursing/routes.py` | 582 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 586 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, task_id, body.patient_response, body.notes,` |
| `backend/app/nursing/routes.py` | 595 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 599 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, task_id, body.new_due_time, body.reason,` |
| `backend/app/nursing/routes.py` | 606 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 614 | `lab_id` | **RETAIN** | `NursingTask.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 614 | `lab_id` | **RETAIN** | `NursingTask.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 623 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 626 | `lab_id` | **RETAIN** | `tasks = NursingService.get_tasks_by_patient(db, current_user.lab_id, patient_id)` |
| `backend/app/nursing/routes.py` | 638 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 645 | `lab_id` | **RETAIN** | `record = NursingService.record_vital_signs(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 653 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 656 | `lab_id` | **RETAIN** | `records = NursingService.get_vital_signs(db, current_user.lab_id, patient_id, limit)` |
| `backend/app/nursing/routes.py` | 664 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 667 | `lab_id` | **RETAIN** | `records = NursingService.get_vital_signs_trend(db, current_user.lab_id, patient_id, hours)` |
| `backend/app/nursing/routes.py` | 674 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 677 | `lab_id` | **RETAIN** | `overdue = NursingService.get_vitals_due(db, current_user.lab_id, window_minutes=window_minutes)` |
| `backend/app/nursing/routes.py` | 689 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 694 | `lab_id` | **RETAIN** | `rec = NursingService.record_fluid_balance(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 703 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 706 | `lab_id` | **RETAIN** | `records = NursingService.get_fluid_balance(db, current_user.lab_id, patient_id, date_from, date_to)` |
| `backend/app/nursing/routes.py` | 714 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 717 | `lab_id` | **RETAIN** | `return NursingService.get_net_balance(db, current_user.lab_id, patient_id, balance_date)` |
| `backend/app/nursing/routes.py` | 728 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 733 | `lab_id` | **RETAIN** | `assessment = NursingService.assess_pain(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 741 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 744 | `lab_id` | **RETAIN** | `assessments = NursingService.get_pain_assessments(db, current_user.lab_id, patient_id, limit)` |
| `backend/app/nursing/routes.py` | 751 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 756 | `lab_id` | **RETAIN** | `assessment = NursingService.assess_fall_risk(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 764 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 767 | `lab_id` | **RETAIN** | `assessments = NursingService.get_fall_risk_assessments(db, current_user.lab_id, patient_id, limit)` |
| `backend/app/nursing/routes.py` | 774 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 779 | `lab_id` | **RETAIN** | `assessment = NursingService.assess_pressure_injury(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 787 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 790 | `lab_id` | **RETAIN** | `assessments = NursingService.get_pressure_injury_assessments(db, current_user.lab_id, patient_id, limit)` |
| `backend/app/nursing/routes.py` | 797 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 802 | `lab_id` | **RETAIN** | `assessment = NursingService.assess_nutrition(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 810 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 813 | `lab_id` | **RETAIN** | `assessments = NursingService.get_nutrition_assessments(db, current_user.lab_id, patient_id, limit)` |
| `backend/app/nursing/routes.py` | 825 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 828 | `lab_id` | **RETAIN** | `plans = NursingService.get_care_plans(db, current_user.lab_id, patient_id)` |
| `backend/app/nursing/routes.py` | 835 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 840 | `lab_id` | **RETAIN** | `plan = NursingService.create_care_plan(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 848 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 854 | `lab_id` | **RETAIN** | `plan = NursingService.update_care_plan(db, current_user.lab_id, current_user.id, plan_id, data)` |
| `backend/app/nursing/routes.py` | 866 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 872 | `lab_id` | **RETAIN** | `note = NursingService.create_nursing_note(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 881 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 884 | `lab_id` | **RETAIN** | `notes = NursingService.get_nursing_notes(db, current_user.lab_id, patient_id, note_type, limit)` |
| `backend/app/nursing/routes.py` | 891 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 894 | `lab_id` | **RETAIN** | `note = NursingService.get_nursing_note(db, current_user.lab_id, note_id)` |
| `backend/app/nursing/routes.py` | 906 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 912 | `lab_id` | **RETAIN** | `shift = NursingService.start_shift(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 919 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 922 | `lab_id` | **RETAIN** | `shift = NursingService.end_shift(db, current_user.lab_id, current_user.id, body.shift_id)` |
| `backend/app/nursing/routes.py` | 929 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 933 | `lab_id` | **RETAIN** | `handover = NursingService.create_shift_handover(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 941 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 944 | `lab_id` | **RETAIN** | `handovers = NursingService.get_shift_handovers(db, current_user.lab_id, department, handover_date)` |
| `backend/app/nursing/routes.py` | 951 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 956 | `lab_id` | **RETAIN** | `ShiftHandover.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 956 | `lab_id` | **RETAIN** | `ShiftHandover.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 967 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 970 | `lab_id` | **RETAIN** | `handover = NursingService.complete_shift_handover(db, current_user.lab_id, current_user.id, handover_id)` |
| `backend/app/nursing/routes.py` | 982 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 987 | `lab_id` | **RETAIN** | `checklist = NursingService.create_checklist(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 994 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 997 | `lab_id` | **RETAIN** | `checklists = NursingService.get_checklists(db, current_user.lab_id, patient_id)` |
| `backend/app/nursing/routes.py` | 1006 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1010 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, checklist_id, item_idx, body.completed,` |
| `backend/app/nursing/routes.py` | 1023 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1027 | `lab_id` | **RETAIN** | `delegation = NursingService.delegate_task(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 1034 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1038 | `lab_id` | **RETAIN** | `Delegation.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 1038 | `lab_id` | **RETAIN** | `Delegation.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 1050 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1053 | `lab_id` | **RETAIN** | `delegation = NursingService.accept_delegation(db, current_user.lab_id, current_user.id, delegation_id)` |
| `backend/app/nursing/routes.py` | 1060 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1063 | `lab_id` | **RETAIN** | `delegation = NursingService.complete_delegation(db, current_user.lab_id, current_user.id, delegation_id)` |
| `backend/app/nursing/routes.py` | 1070 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1074 | `lab_id` | **RETAIN** | `escalation = NursingService.escalate(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 1081 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1085 | `lab_id` | **RETAIN** | `EscalationRecord.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 1085 | `lab_id` | **RETAIN** | `EscalationRecord.lab_id == current_user.lab_id,` |
| `backend/app/nursing/routes.py` | 1097 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1100 | `lab_id` | **RETAIN** | `escalation = NursingService.acknowledge_escalation(db, current_user.lab_id, current_user.id, escalation_id)` |
| `backend/app/nursing/routes.py` | 1108 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1112 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, escalation_id, body.resolution,` |
| `backend/app/nursing/routes.py` | 1125 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1128 | `lab_id` | **RETAIN** | `return {"items": NursingService.get_medication_schedule(db, current_user.lab_id, patient_id)}` |
| `backend/app/nursing/routes.py` | 1135 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1138 | `lab_id` | **RETAIN** | `return {"items": NursingService.get_missed_doses(db, current_user.lab_id, patient_id, dose_date)}` |
| `backend/app/nursing/routes.py` | 1145 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1148 | `lab_id` | **RETAIN** | `return {"items": MedicationAdminService.get_late_doses(db, current_user.lab_id, patient_id, window_minutes)}` |
| `backend/app/nursing/routes.py` | 1154 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1157 | `lab_id` | **RETAIN** | `return {"items": MedicationAdminService.get_medication_alerts(db, current_user.lab_id, patient_id)}` |
| `backend/app/nursing/routes.py` | 1163 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1176 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1181 | `lab_id` | **RETAIN** | `admin = MedicationAdminService.record_administration(db, current_user.lab_id, current_user.id, data)` |
| `backend/app/nursing/routes.py` | 1188 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1192 | `lab_id` | **RETAIN** | `db, current_user.lab_id, str(current_user.id), body.medication_admin_id,` |
| `backend/app/nursing/routes.py` | 1204 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1208 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id,` |
| `backend/app/nursing/routes.py` | 1216 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1220 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.patient_id, body.tests,` |
| `backend/app/nursing/routes.py` | 1227 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1231 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.patient_id, body.exam_type, body.urgency,` |
| `backend/app/nursing/routes.py` | 1238 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1242 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.patient_id,` |
| `backend/app/nursing/routes.py` | 1250 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1254 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.patient_id,` |
| `backend/app/nursing/routes.py` | 1262 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1266 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.patient_id,` |
| `backend/app/nursing/routes.py` | 1274 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1278 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.patient_id,` |
| `backend/app/nursing/routes.py` | 1286 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/nursing/routes.py` | 1290 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.patient_id,` |
| `backend/app/nursing/services.py` | 43 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, nurse_id: str, patient_id: int,` |
| `backend/app/nursing/services.py` | 51 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 51 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 56 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/nursing/services.py` | 56 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/nursing/services.py` | 64 | `lab_id` | **RETAIN** | `log_action(db, f"{_NURSING_NS}.assign_patient", "patient_assignment", assignment.id, user_id, lab_id, {` |
| `backend/app/nursing/services.py` | 71 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, nurse_id: str, patient_id: int,` |
| `backend/app/nursing/services.py` | 77 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 77 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 85 | `lab_id` | **RETAIN** | `log_action(db, f"{_NURSING_NS}.unassign_patient", "patient_assignment", assignment.id, user_id, lab_id, {` |
| `backend/app/nursing/services.py` | 91 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, nurse_id: str,` |
| `backend/app/nursing/services.py` | 96 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 96 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 113 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, nurse_id: str,` |
| `backend/app/nursing/services.py` | 120 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 120 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 126 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 126 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 135 | `lab_id` | **RETAIN** | `EscalationRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 135 | `lab_id` | **RETAIN** | `EscalationRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 147 | `lab_id` | **RETAIN** | `def create_task(db: Session, lab_id: int, user_id: int, data: dict) -> NursingTask:` |
| `backend/app/nursing/services.py` | 148 | `lab_id` | **RETAIN** | `task = NursingTask(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 148 | `lab_id` | **RETAIN** | `task = NursingTask(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 151 | `lab_id` | **RETAIN** | `log_action(db, f"{_NURSING_NS}.create_task", "nursing_task", task.id, user_id, lab_id, data)` |
| `backend/app/nursing/services.py` | 155 | `lab_id` | **RETAIN** | `def update_task(db: Session, lab_id: int, user_id: int, task_id: str, data: dict) -> NursingTask:` |
| `backend/app/nursing/services.py` | 157 | `lab_id` | **RETAIN** | `NursingTask.id == task_id, NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 157 | `lab_id` | **RETAIN** | `NursingTask.id == task_id, NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 170 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, task_id: str,` |
| `backend/app/nursing/services.py` | 174 | `lab_id` | **RETAIN** | `NursingTask.id == task_id, NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 174 | `lab_id` | **RETAIN** | `NursingTask.id == task_id, NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 192 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, task_id: str,` |
| `backend/app/nursing/services.py` | 196 | `lab_id` | **RETAIN** | `NursingTask.id == task_id, NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 196 | `lab_id` | **RETAIN** | `NursingTask.id == task_id, NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 212 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, nurse_id: str \| None = None,` |
| `backend/app/nursing/services.py` | 218 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id, ~NursingTask.is_deleted,` |
| `backend/app/nursing/services.py` | 218 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id, ~NursingTask.is_deleted,` |
| `backend/app/nursing/services.py` | 235 | `lab_id` | **RETAIN** | `def get_tasks_by_patient(db: Session, lab_id: int, patient_id: int) -> list[NursingTask]:` |
| `backend/app/nursing/services.py` | 238 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 238 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 244 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, nurse_id: str, task_date: date \| None = None,` |
| `backend/app/nursing/services.py` | 248 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 248 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 258 | `lab_id` | **RETAIN** | `def record_vital_signs(db: Session, lab_id: int, user_id: int, data: dict) -> VitalSignsRecord:` |
| `backend/app/nursing/services.py` | 259 | `lab_id` | **RETAIN** | `record = VitalSignsRecord(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 259 | `lab_id` | **RETAIN** | `record = VitalSignsRecord(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 270 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/services.py` | 275 | `lab_id` | **RETAIN** | `VitalSignsRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 275 | `lab_id` | **RETAIN** | `VitalSignsRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 281 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, hours: int = 24,` |
| `backend/app/nursing/services.py` | 286 | `lab_id` | **RETAIN** | `VitalSignsRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 286 | `lab_id` | **RETAIN** | `VitalSignsRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 294 | `lab_id` | **RETAIN** | `def record_fluid_balance(db: Session, lab_id: int, user_id: int, data: dict) -> FluidBalance:` |
| `backend/app/nursing/services.py` | 295 | `lab_id` | **RETAIN** | `rec = FluidBalance(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 295 | `lab_id` | **RETAIN** | `rec = FluidBalance(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 302 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/services.py` | 307 | `lab_id` | **RETAIN** | `FluidBalance.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 307 | `lab_id` | **RETAIN** | `FluidBalance.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 318 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, balance_date: date,` |
| `backend/app/nursing/services.py` | 322 | `lab_id` | **RETAIN** | `FluidBalance.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 322 | `lab_id` | **RETAIN** | `FluidBalance.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 340 | `lab_id` | **RETAIN** | `def assess_pain(db: Session, lab_id: int, user_id: int, data: dict) -> PainAssessment:` |
| `backend/app/nursing/services.py` | 341 | `lab_id` | **RETAIN** | `assessment = PainAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 341 | `lab_id` | **RETAIN** | `assessment = PainAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 348 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, limit: int = 20,` |
| `backend/app/nursing/services.py` | 352 | `lab_id` | **RETAIN** | `PainAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 352 | `lab_id` | **RETAIN** | `PainAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 359 | `lab_id` | **RETAIN** | `def assess_fall_risk(db: Session, lab_id: int, user_id: int, data: dict) -> FallRiskAssessment:` |
| `backend/app/nursing/services.py` | 360 | `lab_id` | **RETAIN** | `assessment = FallRiskAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 360 | `lab_id` | **RETAIN** | `assessment = FallRiskAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 367 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, limit: int = 10,` |
| `backend/app/nursing/services.py` | 371 | `lab_id` | **RETAIN** | `FallRiskAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 371 | `lab_id` | **RETAIN** | `FallRiskAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 378 | `lab_id` | **RETAIN** | `def assess_pressure_injury(db: Session, lab_id: int, user_id: int, data: dict) -> PressureInjuryAssessment:` |
| `backend/app/nursing/services.py` | 379 | `lab_id` | **RETAIN** | `assessment = PressureInjuryAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 379 | `lab_id` | **RETAIN** | `assessment = PressureInjuryAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 386 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, limit: int = 10,` |
| `backend/app/nursing/services.py` | 390 | `lab_id` | **RETAIN** | `PressureInjuryAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 390 | `lab_id` | **RETAIN** | `PressureInjuryAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 397 | `lab_id` | **RETAIN** | `def assess_nutrition(db: Session, lab_id: int, user_id: int, data: dict) -> NutritionAssessment:` |
| `backend/app/nursing/services.py` | 398 | `lab_id` | **RETAIN** | `assessment = NutritionAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 398 | `lab_id` | **RETAIN** | `assessment = NutritionAssessment(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 407 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, limit: int = 10,` |
| `backend/app/nursing/services.py` | 411 | `lab_id` | **RETAIN** | `NutritionAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 411 | `lab_id` | **RETAIN** | `NutritionAssessment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 418 | `lab_id` | **RETAIN** | `def create_care_plan(db: Session, lab_id: int, user_id: int, data: dict) -> NursingCarePlan:` |
| `backend/app/nursing/services.py` | 419 | `lab_id` | **RETAIN** | `plan = NursingCarePlan(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 419 | `lab_id` | **RETAIN** | `plan = NursingCarePlan(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 426 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, plan_id: str, data: dict,` |
| `backend/app/nursing/services.py` | 429 | `lab_id` | **RETAIN** | `NursingCarePlan.id == plan_id, NursingCarePlan.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 429 | `lab_id` | **RETAIN** | `NursingCarePlan.id == plan_id, NursingCarePlan.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 442 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/services.py` | 446 | `lab_id` | **RETAIN** | `NursingCarePlan.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 446 | `lab_id` | **RETAIN** | `NursingCarePlan.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 453 | `lab_id` | **RETAIN** | `def create_nursing_note(db: Session, lab_id: int, user_id: int, data: dict) -> NursingNote:` |
| `backend/app/nursing/services.py` | 454 | `lab_id` | **RETAIN** | `note = NursingNote(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 454 | `lab_id` | **RETAIN** | `note = NursingNote(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 461 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/services.py` | 466 | `lab_id` | **RETAIN** | `NursingNote.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 466 | `lab_id` | **RETAIN** | `NursingNote.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 474 | `lab_id` | **RETAIN** | `def get_nursing_note(db: Session, lab_id: int, note_id: str) -> NursingNote:` |
| `backend/app/nursing/services.py` | 476 | `lab_id` | **RETAIN** | `NursingNote.id == note_id, NursingNote.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 476 | `lab_id` | **RETAIN** | `NursingNote.id == note_id, NursingNote.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 486 | `lab_id` | **RETAIN** | `def start_shift(db: Session, lab_id: int, user_id: int, data: dict) -> NursingShift:` |
| `backend/app/nursing/services.py` | 490 | `lab_id` | **RETAIN** | `NursingShift.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 490 | `lab_id` | **RETAIN** | `NursingShift.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 494 | `lab_id` | **RETAIN** | `shift = NursingShift(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 494 | `lab_id` | **RETAIN** | `shift = NursingShift(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 500 | `lab_id` | **RETAIN** | `def end_shift(db: Session, lab_id: int, user_id: int, shift_id: str) -> NursingShift:` |
| `backend/app/nursing/services.py` | 502 | `lab_id` | **RETAIN** | `NursingShift.id == shift_id, NursingShift.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 502 | `lab_id` | **RETAIN** | `NursingShift.id == shift_id, NursingShift.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 517 | `lab_id` | **RETAIN** | `def create_shift_handover(db: Session, lab_id: int, user_id: int, data: dict) -> ShiftHandover:` |
| `backend/app/nursing/services.py` | 518 | `lab_id` | **RETAIN** | `handover = ShiftHandover(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 518 | `lab_id` | **RETAIN** | `handover = ShiftHandover(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 525 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, department: int \| None = None, handover_date: date \| None = None,` |
| `backend/app/nursing/services.py` | 528 | `lab_id` | **RETAIN** | `ShiftHandover.lab_id == lab_id, ~ShiftHandover.is_deleted,` |
| `backend/app/nursing/services.py` | 528 | `lab_id` | **RETAIN** | `ShiftHandover.lab_id == lab_id, ~ShiftHandover.is_deleted,` |
| `backend/app/nursing/services.py` | 536 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, handover_id: str,` |
| `backend/app/nursing/services.py` | 539 | `lab_id` | **RETAIN** | `ShiftHandover.id == handover_id, ShiftHandover.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 539 | `lab_id` | **RETAIN** | `ShiftHandover.id == handover_id, ShiftHandover.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 553 | `lab_id` | **RETAIN** | `def create_checklist(db: Session, lab_id: int, user_id: int, data: dict) -> ClinicalChecklist:` |
| `backend/app/nursing/services.py` | 554 | `lab_id` | **RETAIN** | `checklist = ClinicalChecklist(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 554 | `lab_id` | **RETAIN** | `checklist = ClinicalChecklist(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 561 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/services.py` | 565 | `lab_id` | **RETAIN** | `ClinicalChecklist.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 565 | `lab_id` | **RETAIN** | `ClinicalChecklist.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 571 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, checklist_id: str,` |
| `backend/app/nursing/services.py` | 575 | `lab_id` | **RETAIN** | `ClinicalChecklist.id == checklist_id, ClinicalChecklist.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 575 | `lab_id` | **RETAIN** | `ClinicalChecklist.id == checklist_id, ClinicalChecklist.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 602 | `lab_id` | **RETAIN** | `def delegate_task(db: Session, lab_id: int, user_id: int, data: dict) -> Delegation:` |
| `backend/app/nursing/services.py` | 603 | `lab_id` | **RETAIN** | `delegation = Delegation(lab_id=lab_id, created_by=user_id, delegated_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 603 | `lab_id` | **RETAIN** | `delegation = Delegation(lab_id=lab_id, created_by=user_id, delegated_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 609 | `lab_id` | **RETAIN** | `def accept_delegation(db: Session, lab_id: int, user_id: int, delegation_id: str) -> Delegation:` |
| `backend/app/nursing/services.py` | 611 | `lab_id` | **RETAIN** | `Delegation.id == delegation_id, Delegation.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 611 | `lab_id` | **RETAIN** | `Delegation.id == delegation_id, Delegation.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 625 | `lab_id` | **RETAIN** | `def complete_delegation(db: Session, lab_id: int, user_id: int, delegation_id: str) -> Delegation:` |
| `backend/app/nursing/services.py` | 627 | `lab_id` | **RETAIN** | `Delegation.id == delegation_id, Delegation.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 627 | `lab_id` | **RETAIN** | `Delegation.id == delegation_id, Delegation.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 641 | `lab_id` | **RETAIN** | `def escalate(db: Session, lab_id: int, user_id: int, data: dict) -> EscalationRecord:` |
| `backend/app/nursing/services.py` | 642 | `lab_id` | **RETAIN** | `rec = EscalationRecord(lab_id=lab_id, created_by=user_id, escalated_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 642 | `lab_id` | **RETAIN** | `rec = EscalationRecord(lab_id=lab_id, created_by=user_id, escalated_by=user_id, **data)` |
| `backend/app/nursing/services.py` | 648 | `lab_id` | **RETAIN** | `def acknowledge_escalation(db: Session, lab_id: int, user_id: int, escalation_id: str) -> EscalationRecord:` |
| `backend/app/nursing/services.py` | 650 | `lab_id` | **RETAIN** | `EscalationRecord.id == escalation_id, EscalationRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 650 | `lab_id` | **RETAIN** | `EscalationRecord.id == escalation_id, EscalationRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 662 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, escalation_id: str, resolution: str \| None = None,` |
| `backend/app/nursing/services.py` | 665 | `lab_id` | **RETAIN** | `EscalationRecord.id == escalation_id, EscalationRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 665 | `lab_id` | **RETAIN** | `EscalationRecord.id == escalation_id, EscalationRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 682 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int,` |
| `backend/app/nursing/services.py` | 688 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 688 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 715 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, patient_id: int, dose_date: date \| None = None,` |
| `backend/app/nursing/services.py` | 722 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 722 | `lab_id` | **RETAIN** | `MedicationRequest.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 748 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, unit_filter: str \| None = None, window_minutes: int = 60,` |
| `backend/app/nursing/services.py` | 752 | `lab_id` | **RETAIN** | `VitalSignsRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 752 | `lab_id` | **RETAIN** | `VitalSignsRecord.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 757 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 757 | `lab_id` | **RETAIN** | `PatientAssignment.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 763 | `lab_id` | **RETAIN** | `def get_shift_summary(db: Session, lab_id: int, shift_id: str) -> dict[str, Any]:` |
| `backend/app/nursing/services.py` | 765 | `lab_id` | **RETAIN** | `NursingShift.id == shift_id, NursingShift.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 765 | `lab_id` | **RETAIN** | `NursingShift.id == shift_id, NursingShift.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 770 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/nursing/services.py` | 770 | `lab_id` | **RETAIN** | `NursingTask.lab_id == lab_id,` |
| `backend/app/payments/fx_routes.py` | 43 | `lab_id` | **RETAIN** | `if current_user.lab_id is None:` |
| `backend/app/payments/fx_routes.py` | 45 | `lab_id` | **RETAIN** | `return current_user.lab_id` |
| `backend/app/payments/fx_service.py` | 44 | `lab_id` | **RETAIN** | `if getattr(actor, "lab_id", None) != institution_id:` |
| `backend/app/payments/routes.py` | 138 | `lab_id` | **RETAIN** | `if current_user.lab_id is None:` |
| `backend/app/payments/routes.py` | 141 | `lab_id` | **RETAIN** | `institution_id=current_user.lab_id,` |
| `backend/app/payments/service.py` | 72 | `lab_id` | **RETAIN** | `if getattr(actor, "lab_id", None) != institution_id:` |
| `backend/app/payments/subscription_models.py` | 54 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, nullable=False, index=True)` |
| `backend/app/payments/subscription_routes.py` | 55 | `lab_id` | **RETAIN** | `PaymentService(db).assert_institution_access(current_user, subscription.lab_id)` |
| `backend/app/payments/subscription_routes.py` | 89 | `lab_id` | **RETAIN** | `return {"id": subscription.id, "lab_id": subscription.lab_id, "status": subscription.status, "plan_code": subscription.plan_code}` |
| `backend/app/payments/subscription_routes.py` | 89 | `lab_id` | **RETAIN** | `return {"id": subscription.id, "lab_id": subscription.lab_id, "status": subscription.status, "plan_code": subscription.plan_code}` |
| `backend/app/payments/subscription_routes.py` | 112 | `lab_id` | **RETAIN** | `"lab_id": subscription.lab_id,` |
| `backend/app/payments/subscription_routes.py` | 112 | `lab_id` | **RETAIN** | `"lab_id": subscription.lab_id,` |
| `backend/app/payments/subscription_schemas.py` | 38 | `lab_id` | **RETAIN** | `lab_id: int = Field(gt=0)` |
| `backend/app/payments/subscription_service.py` | 98 | `lab_id` | **RETAIN** | `def create_subscription(self, *, lab_id: int, plan_id: str, billing_cycle: str,` |
| `backend/app/payments/subscription_service.py` | 104 | `lab_id` | **RETAIN** | `PlatformSubscription.lab_id == lab_id,` |
| `backend/app/payments/subscription_service.py` | 104 | `lab_id` | **RETAIN** | `PlatformSubscription.lab_id == lab_id,` |
| `backend/app/payments/subscription_service.py` | 112 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/payments/subscription_service.py` | 112 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/payments/subscription_service.py` | 128 | `lab_id` | **RETAIN** | `self._audit(action="SUBSCRIPTION_CREATED", actor_user_id=actor_user_id, subscription_id=subscription.id, plan_id=plan.id, metadata={"lab_id": lab_id, "billing_cycle": billing_cycle})` |
| `backend/app/payments/subscription_service.py` | 128 | `lab_id` | **RETAIN** | `self._audit(action="SUBSCRIPTION_CREATED", actor_user_id=actor_user_id, subscription_id=subscription.id, plan_id=plan.id, metadata={"lab_id": lab_id, "billing_cycle": billing_cycle})` |
| `backend/app/pharmacy/clinical.py` | 23 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/clinical.py` | 25 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 25 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 101 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/clinical.py` | 103 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 103 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 144 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/clinical.py` | 146 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 146 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 200 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/clinical.py` | 202 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 202 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 318 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/clinical.py` | 320 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 320 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 341 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/clinical.py` | 343 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 343 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/clinical.py` | 344 | `lab_id` | **RETAIN** | `self.interaction_engine = DrugInteractionEngine(db, lab_id)` |
| `backend/app/pharmacy/dispensing.py` | 54 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/dispensing.py` | 56 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/dispensing.py` | 56 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 27 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, user_id: int \| None = None, lab_id: int \| None = None):` |
| `backend/app/pharmacy/inventory.py` | 30 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 30 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 71 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 72 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 72 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 87 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 88 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 88 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 135 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 136 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 136 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 179 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 180 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 180 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 197 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 198 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 198 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 212 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/inventory.py` | 214 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 214 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 224 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 225 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 225 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 251 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 252 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 252 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 276 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 277 | `lab_id` | **RETAIN** | `expired = expired.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 277 | `lab_id` | **RETAIN** | `expired = expired.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 300 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/inventory.py` | 302 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 302 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 365 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 366 | `lab_id` | **RETAIN** | `drug_ids_q = drug_ids_q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 366 | `lab_id` | **RETAIN** | `drug_ids_q = drug_ids_q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 383 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/inventory.py` | 385 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 385 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 399 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 400 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 400 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 473 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, user_id: int \| None = None, lab_id: int \| None = None):` |
| `backend/app/pharmacy/inventory.py` | 476 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 476 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 499 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 500 | `lab_id` | **RETAIN** | `recall.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 500 | `lab_id` | **RETAIN** | `recall.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 534 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 535 | `lab_id` | **RETAIN** | `q = q.filter(Recall.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 535 | `lab_id` | **RETAIN** | `q = q.filter(Recall.lab_id == self.lab_id)` |
| `backend/app/pharmacy/inventory.py` | 561 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, lab_id: int \| None = None):` |
| `backend/app/pharmacy/inventory.py` | 563 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 563 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/inventory.py` | 597 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/inventory.py` | 598 | `lab_id` | **RETAIN** | `forecast.lab_id = self.lab_id` |
| `backend/app/pharmacy/inventory.py` | 598 | `lab_id` | **RETAIN** | `forecast.lab_id = self.lab_id` |
| `backend/app/pharmacy/routes.py` | 496 | `lab_id` | **RETAIN** | `return PharmacyService(db=db, user_id=user.id, lab_id=user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 496 | `lab_id` | **RETAIN** | `return PharmacyService(db=db, user_id=user.id, lab_id=user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 694 | `lab_id` | **RETAIN** | `if user.lab_id:` |
| `backend/app/pharmacy/routes.py` | 695 | `lab_id` | **RETAIN** | `q = q.filter(Prescription.lab_id == user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 695 | `lab_id` | **RETAIN** | `q = q.filter(Prescription.lab_id == user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 907 | `lab_id` | **RETAIN** | `engine = DrugInteractionEngine(db, user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 921 | `lab_id` | **RETAIN** | `engine = ContraindicationEngine(db, user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 934 | `lab_id` | **RETAIN** | `engine = AllergyEngine(db, user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 947 | `lab_id` | **RETAIN** | `engine = DoseEngine(db, user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 960 | `lab_id` | **RETAIN** | `engine = DoseEngine(db, user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 975 | `lab_id` | **RETAIN** | `svc = ClinicalGuidelineService(db, user.lab_id)` |
| `backend/app/pharmacy/routes.py` | 988 | `lab_id` | **RETAIN** | `checker = PolypharmacyChecker(db, user.lab_id)` |
| `backend/app/pharmacy/services.py` | 35 | `lab_id` | **RETAIN** | `def __init__(self, db: Session, user_id: int \| None = None, lab_id: int \| None = None):` |
| `backend/app/pharmacy/services.py` | 38 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/services.py` | 38 | `lab_id` | **RETAIN** | `self.lab_id = lab_id` |
| `backend/app/pharmacy/services.py` | 54 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 55 | `lab_id` | **RETAIN** | `drug.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 55 | `lab_id` | **RETAIN** | `drug.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 63 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 64 | `lab_id` | **RETAIN** | `q = q.filter(DrugCatalog.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 64 | `lab_id` | **RETAIN** | `q = q.filter(DrugCatalog.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 97 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 98 | `lab_id` | **RETAIN** | `q = q.filter(DrugCatalog.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 98 | `lab_id` | **RETAIN** | `q = q.filter(DrugCatalog.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 125 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 126 | `lab_id` | **RETAIN** | `q = q.filter(DrugCatalog.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 126 | `lab_id` | **RETAIN** | `q = q.filter(DrugCatalog.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 134 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 135 | `lab_id` | **RETAIN** | `batch.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 135 | `lab_id` | **RETAIN** | `batch.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 146 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 147 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 147 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 159 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 160 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 160 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 165 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 166 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 166 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 178 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 179 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 179 | `lab_id` | **RETAIN** | `q = q.filter(DrugBatch.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 184 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 185 | `lab_id` | **RETAIN** | `supplier.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 185 | `lab_id` | **RETAIN** | `supplier.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 193 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 194 | `lab_id` | **RETAIN** | `q = q.filter(DrugSupplier.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 194 | `lab_id` | **RETAIN** | `q = q.filter(DrugSupplier.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 201 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 202 | `lab_id` | **RETAIN** | `rx.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 202 | `lab_id` | **RETAIN** | `rx.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 210 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 211 | `lab_id` | **RETAIN** | `q = q.filter(Prescription.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 211 | `lab_id` | **RETAIN** | `q = q.filter(Prescription.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 244 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 245 | `lab_id` | **RETAIN** | `renewal.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 245 | `lab_id` | **RETAIN** | `renewal.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 270 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 271 | `lab_id` | **RETAIN** | `new_item.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 271 | `lab_id` | **RETAIN** | `new_item.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 283 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 284 | `lab_id` | **RETAIN** | `item.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 284 | `lab_id` | **RETAIN** | `item.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 313 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 314 | `lab_id` | **RETAIN** | `q = q.filter(DispenseQueue.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 314 | `lab_id` | **RETAIN** | `q = q.filter(DispenseQueue.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 386 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 387 | `lab_id` | **RETAIN** | `record.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 387 | `lab_id` | **RETAIN** | `record.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 414 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 415 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 415 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 427 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 428 | `lab_id` | **RETAIN** | `q = q.filter(DispenseRecord.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 428 | `lab_id` | **RETAIN** | `q = q.filter(DispenseRecord.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 442 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 443 | `lab_id` | **RETAIN** | `q = q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 443 | `lab_id` | **RETAIN** | `q = q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 460 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 461 | `lab_id` | **RETAIN** | `q = q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 461 | `lab_id` | **RETAIN** | `q = q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 508 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 509 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 509 | `lab_id` | **RETAIN** | `stock.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 527 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 528 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 528 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 539 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 540 | `lab_id` | **RETAIN** | `q = q.filter(StockMovement.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 540 | `lab_id` | **RETAIN** | `q = q.filter(StockMovement.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 551 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 552 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 552 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 560 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 561 | `lab_id` | **RETAIN** | `transfer.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 561 | `lab_id` | **RETAIN** | `transfer.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 569 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 570 | `lab_id` | **RETAIN** | `q = q.filter(InventoryTransfer.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 570 | `lab_id` | **RETAIN** | `q = q.filter(InventoryTransfer.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 611 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 612 | `lab_id` | **RETAIN** | `ret.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 612 | `lab_id` | **RETAIN** | `ret.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 630 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 631 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 631 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 640 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 641 | `lab_id` | **RETAIN** | `waste.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 641 | `lab_id` | **RETAIN** | `waste.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 659 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 660 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 660 | `lab_id` | **RETAIN** | `movement.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 669 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 670 | `lab_id` | **RETAIN** | `q = q.filter(Recall.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 670 | `lab_id` | **RETAIN** | `q = q.filter(Recall.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 679 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 680 | `lab_id` | **RETAIN** | `recall.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 680 | `lab_id` | **RETAIN** | `recall.lab_id = self.lab_id` |
| `backend/app/pharmacy/services.py` | 691 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 692 | `lab_id` | **RETAIN** | `q = q.filter(InventoryForecast.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 692 | `lab_id` | **RETAIN** | `q = q.filter(InventoryForecast.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 702 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 703 | `lab_id` | **RETAIN** | `q = q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 703 | `lab_id` | **RETAIN** | `q = q.filter(StockLevel.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 726 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 727 | `lab_id` | **RETAIN** | `rx_q = rx_q.filter(Prescription.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 727 | `lab_id` | **RETAIN** | `rx_q = rx_q.filter(Prescription.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 728 | `lab_id` | **RETAIN** | `queue_q = queue_q.filter(DispenseQueue.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 728 | `lab_id` | **RETAIN** | `queue_q = queue_q.filter(DispenseQueue.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 747 | `lab_id` | **RETAIN** | `if self.lab_id:` |
| `backend/app/pharmacy/services.py` | 748 | `lab_id` | **RETAIN** | `q = q.filter(DispenseQueue.lab_id == self.lab_id)` |
| `backend/app/pharmacy/services.py` | 748 | `lab_id` | **RETAIN** | `q = q.filter(DispenseQueue.lab_id == self.lab_id)` |
| `backend/app/platform/authorization.py` | 53 | `lab_id` | **RETAIN** | `subject = {"id": user.id, "role": user.role, "lab_id": getattr(user, "lab_id", None)}` |
| `backend/app/platform/authorization.py` | 53 | `lab_id` | **RETAIN** | `subject = {"id": user.id, "role": user.role, "lab_id": getattr(user, "lab_id", None)}` |
| `backend/app/platform/identity.py` | 24 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/platform/identity.py` | 55 | `lab_id` | **RETAIN** | `lab_id=payload.get("lab_id"),` |
| `backend/app/platform/identity.py` | 55 | `lab_id` | **RETAIN** | `lab_id=payload.get("lab_id"),` |
| `backend/app/radiology/clinical_read_gate.py` | 6 | `lab_id` | **RETAIN** | ```ClinicalPolicyEvaluator``.  It never treats a legacy ``lab_id`` as a` |
| `backend/app/radiology/clinical_read_gate.py` | 20 | `LegacyAccountLink` | **RETAIN** | `from app.identity.models.legacy_account_link import LegacyAccountLink` |
| `backend/app/radiology/clinical_read_gate.py` | 39 | `legacy_lab_id` | **RETAIN** | `legacy_lab_id: int` |
| `backend/app/radiology/clinical_read_gate.py` | 63 | `LegacyAccountLink` | **RETAIN** | `db.query(LegacyAccountLink)` |
| `backend/app/radiology/clinical_read_gate.py` | 65 | `LegacyAccountLink` | **RETAIN** | `LegacyAccountLink.source_kind == "lab_user",` |
| `backend/app/radiology/clinical_read_gate.py` | 66 | `LegacyAccountLink` | **RETAIN** | `LegacyAccountLink.legacy_account_id == lab_user.id,` |
| `backend/app/radiology/clinical_read_gate.py` | 67 | `LegacyAccountLink` | **RETAIN** | `LegacyAccountLink.status == "migrated",` |
| `backend/app/radiology/clinical_read_gate.py` | 85 | `legacy_lab_id` | **RETAIN** | `ClinicalLabFacilityBinding.legacy_lab_id == lab_user.lab_id,` |
| `backend/app/radiology/clinical_read_gate.py` | 85 | `lab_id` | **RETAIN** | `ClinicalLabFacilityBinding.legacy_lab_id == lab_user.lab_id,` |
| `backend/app/radiology/clinical_read_gate.py` | 137 | `legacy_lab_id` | **RETAIN** | `legacy_lab_id=lab_user.lab_id,` |
| `backend/app/radiology/clinical_read_gate.py` | 137 | `lab_id` | **RETAIN** | `legacy_lab_id=lab_user.lab_id,` |
| `backend/app/radiology/clinical_read_gate.py` | 161 | `lab_id` | **RETAIN** | `"lab_id": getattr(lab_user, "lab_id", None),` |
| `backend/app/radiology/clinical_read_gate.py` | 161 | `lab_id` | **RETAIN** | `"lab_id": getattr(lab_user, "lab_id", None),` |
| `backend/app/radiology/routes.py` | 14 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/radiology/routes.py` | 249 | `LabUser` | **RETAIN** | `def _patient_for_user(db: Session, current_user: LabUser, patient_id: str) -> Patient:` |
| `backend/app/radiology/routes.py` | 256 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/radiology/routes.py` | 256 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/radiology/routes.py` | 264 | `LabUser` | **RETAIN** | `def _tenant_patient_keys(db: Session, current_user: LabUser) -> set[str]:` |
| `backend/app/radiology/routes.py` | 265 | `lab_id` | **RETAIN** | `rows = db.query(Patient.id, Patient.health_id).filter(Patient.lab_id == current_user.lab_id).all()` |
| `backend/app/radiology/routes.py` | 265 | `lab_id` | **RETAIN** | `rows = db.query(Patient.id, Patient.health_id).filter(Patient.lab_id == current_user.lab_id).all()` |
| `backend/app/radiology/routes.py` | 274 | `LabUser` | **RETAIN** | `def _critical_finding_for_user(db: Session, current_user: LabUser, finding_id: str):` |
| `backend/app/radiology/routes.py` | 286 | `LabUser` | **RETAIN** | `def _study_for_user(db: Session, current_user: LabUser, study_uid: str):` |
| `backend/app/radiology/routes.py` | 303 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 335 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 368 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 406 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 431 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 446 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 470 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 495 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 521 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 538 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 555 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 581 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 607 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 633 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 648 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 666 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 684 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 698 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 710 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 730 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 741 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 766 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 790 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 822 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 848 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 876 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 891 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 916 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 934 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 958 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 977 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 988 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1019 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1045 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1056 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1079 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1091 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1108 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1127 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1146 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1164 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1187 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1198 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1225 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1238 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1252 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1273 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1300 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1329 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1359 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1379 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1403 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1424 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1443 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1457 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1478 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1501 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/radiology/routes.py` | 1521 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/reference/domain/interfaces.py` | 25 | `lab_id` | **RETAIN** | `lab_id: str \| None = None,` |
| `backend/app/reference/domain/interfaces.py` | 37 | `lab_id` | **RETAIN** | `lab_id: str,` |
| `backend/app/reference/domain/interfaces.py` | 82 | `lab_id` | **RETAIN** | `lab_id: str,` |
| `backend/app/reference/domain/models.py` | 36 | `lab_id` | **RETAIN** | `lab_id: str = ""` |
| `backend/app/reference/domain/models.py` | 61 | `lab_id` | **RETAIN** | `lab_id: str = ""` |
| `backend/app/reference/domain/models.py` | 101 | `lab_id` | **RETAIN** | `lab_id: str = ""` |
| `backend/app/reference/domain/services.py` | 80 | `lab_id` | **RETAIN** | `lab_id=patient.lab_id,` |
| `backend/app/reference/domain/services.py` | 80 | `lab_id` | **RETAIN** | `lab_id=patient.lab_id,` |
| `backend/app/reference/domain/services.py` | 108 | `lab_id` | **RETAIN** | `REQUIRED_FIELDS = {"patient_id", "test_type", "lab_id"}` |
| `backend/app/reference/domain/services.py` | 121 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/reference/domain/services.py` | 121 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 30 | `lab_id` | **RETAIN** | `column("lab_id"),` |
| `backend/app/reference/infrastructure/repositories.py` | 48 | `lab_id` | **RETAIN** | `"lab_id": "lab_id",` |
| `backend/app/reference/infrastructure/repositories.py` | 48 | `lab_id` | **RETAIN** | `"lab_id": "lab_id",` |
| `backend/app/reference/infrastructure/repositories.py` | 58 | `lab_id` | **RETAIN** | `lab_id, national_id, address,` |
| `backend/app/reference/infrastructure/repositories.py` | 61 | `lab_id` | **RETAIN** | `:lab_id, :national_id, :address, :created_at, :updated_at)` |
| `backend/app/reference/infrastructure/repositories.py` | 68 | `lab_id` | **RETAIN** | `lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 83 | `lab_id` | **RETAIN** | `"lab_id": patient.lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 83 | `lab_id` | **RETAIN** | `"lab_id": patient.lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 97 | `lab_id` | **RETAIN** | `lab_id, national_id, address, created_at, updated_at` |
| `backend/app/reference/infrastructure/repositories.py` | 111 | `lab_id` | **RETAIN** | `lab_id: str \| None = None,` |
| `backend/app/reference/infrastructure/repositories.py` | 124 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/reference/infrastructure/repositories.py` | 125 | `lab_id` | **RETAIN** | `conditions.append(_PATIENTS.c.lab_id == bindparam("lab_id"))` |
| `backend/app/reference/infrastructure/repositories.py` | 125 | `lab_id` | **RETAIN** | `conditions.append(_PATIENTS.c.lab_id == bindparam("lab_id"))` |
| `backend/app/reference/infrastructure/repositories.py` | 126 | `lab_id` | **RETAIN** | `params["lab_id"] = lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 126 | `lab_id` | **RETAIN** | `params["lab_id"] = lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 144 | `lab_id` | **RETAIN** | `_PATIENTS.c.lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 167 | `lab_id` | **RETAIN** | `lab_id: str,` |
| `backend/app/reference/infrastructure/repositories.py` | 171 | `lab_id` | **RETAIN** | `lab_id, national_id, address, created_at, updated_at` |
| `backend/app/reference/infrastructure/repositories.py` | 173 | `lab_id` | **RETAIN** | `WHERE name = :name AND phone = :phone AND lab_id = :lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 173 | `lab_id` | **RETAIN** | `WHERE name = :name AND phone = :phone AND lab_id = :lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 182 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 182 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 196 | `lab_id` | **RETAIN** | `lab_id=row["lab_id"],` |
| `backend/app/reference/infrastructure/repositories.py` | 196 | `lab_id` | **RETAIN** | `lab_id=row["lab_id"],` |
| `backend/app/reference/infrastructure/repositories.py` | 213 | `lab_id` | **RETAIN** | `(patient_id, lab_id, test_type, status, priority,` |
| `backend/app/reference/infrastructure/repositories.py` | 216 | `lab_id` | **RETAIN** | `(:patient_id, :lab_id, :test_type, :status, :priority,` |
| `backend/app/reference/infrastructure/repositories.py` | 219 | `lab_id` | **RETAIN** | `id AS order_id, patient_id, lab_id, test_type, status,` |
| `backend/app/reference/infrastructure/repositories.py` | 228 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 228 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 243 | `lab_id` | **RETAIN** | `SELECT id AS order_id, patient_id, lab_id, test_type, status,` |
| `backend/app/reference/infrastructure/repositories.py` | 272 | `lab_id` | **RETAIN** | `SELECT id AS order_id, patient_id, lab_id, test_type, status,` |
| `backend/app/reference/infrastructure/repositories.py` | 296 | `lab_id` | **RETAIN** | `lab_id=row["lab_id"],` |
| `backend/app/reference/infrastructure/repositories.py` | 296 | `lab_id` | **RETAIN** | `lab_id=row["lab_id"],` |
| `backend/app/reference/infrastructure/repositories.py` | 384 | `lab_id` | **RETAIN** | `lab_id: str,` |
| `backend/app/reference/infrastructure/repositories.py` | 393 | `lab_id` | **RETAIN** | `AND lo.lab_id = :lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 393 | `lab_id` | **RETAIN** | `AND lo.lab_id = :lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 397 | `lab_id` | **RETAIN** | `count_stmt, {"lab_id": lab_id},` |
| `backend/app/reference/infrastructure/repositories.py` | 397 | `lab_id` | **RETAIN** | `count_stmt, {"lab_id": lab_id},` |
| `backend/app/reference/infrastructure/repositories.py` | 412 | `lab_id` | **RETAIN** | `AND lo.lab_id = :lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 412 | `lab_id` | **RETAIN** | `AND lo.lab_id = :lab_id` |
| `backend/app/reference/infrastructure/repositories.py` | 420 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/reference/infrastructure/repositories.py` | 420 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/reference/routes/orders.py` | 22 | `lab_id` | **RETAIN** | `lab_id: str = Query(..., description="معرف المختبر"),` |
| `backend/app/reference/routes/orders.py` | 30 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/routes/orders.py` | 30 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/routes/orders.py` | 60 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/reference/routes/orders.py` | 60 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/reference/routes/patients.py` | 39 | `lab_id` | **RETAIN** | `lab_id: str = Query(..., description="معرف المختبر"),` |
| `backend/app/reference/routes/patients.py` | 49 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/routes/patients.py` | 49 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/routes/patients.py` | 68 | `lab_id` | **RETAIN** | `lab_id: str \| None = Query(None, description="معرف المختبر"),` |
| `backend/app/reference/routes/patients.py` | 77 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/routes/patients.py` | 77 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/routes/patients.py` | 101 | `lab_id` | **RETAIN** | `"lab_id": patient.lab_id,` |
| `backend/app/reference/routes/patients.py` | 101 | `lab_id` | **RETAIN** | `"lab_id": patient.lab_id,` |
| `backend/app/reference/routes/results.py` | 70 | `lab_id` | **RETAIN** | `lab_id: str = Query(..., description="معرف المختبر"),` |
| `backend/app/reference/routes/results.py` | 76 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/routes/results.py` | 76 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/services/patient_service.py` | 39 | `lab_id` | **RETAIN** | `lab_id: str \| None = None,` |
| `backend/app/reference/services/patient_service.py` | 47 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/services/patient_service.py` | 47 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/services/result_service.py` | 53 | `lab_id` | **RETAIN** | `lab_id: str,` |
| `backend/app/reference/services/result_service.py` | 58 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/services/result_service.py` | 58 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/reference/tests/test_domain.py` | 55 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 62 | `lab_id` | **RETAIN** | `patient = PatientDomain(name="", gender=Gender.MALE, lab_id="lab-1")` |
| `backend/app/reference/tests/test_domain.py` | 72 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 83 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 94 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 100 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 110 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 142 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 152 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 158 | `lab_id` | **RETAIN** | `patient = PatientDomain(name="علي أحمد", lab_id="lab-1")` |
| `backend/app/reference/tests/test_domain.py` | 176 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 184 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 201 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 228 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_domain.py` | 248 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 79 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 89 | `lab_id` | **RETAIN** | `lab_id="lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 209 | `lab_id` | **RETAIN** | `"lab_id": "lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 236 | `lab_id` | **RETAIN** | `"lab_id": "lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 257 | `lab_id` | **RETAIN** | `"lab_id": "lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 274 | `lab_id` | **RETAIN** | `params={"name": "علي", "lab_id": "lab-1"},` |
| `backend/app/reference/tests/test_routes.py` | 303 | `lab_id` | **RETAIN** | `"lab_id": "lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 329 | `lab_id` | **RETAIN** | `"lab_id": "lab-1",` |
| `backend/app/reference/tests/test_routes.py` | 459 | `lab_id` | **RETAIN** | `params={"lab_id": "lab-1"},` |
| `backend/app/research_platform/bi_dashboards.py` | 179 | `lab_id` | **RETAIN** | `def render(self, lab_id: str) -> dict[str, Any]:` |
| `backend/app/research_platform/bi_dashboards.py` | 182 | `lab_id` | **RETAIN** | `filters={"lab_id": int(lab_id) if lab_id.isdigit() else 0},` |
| `backend/app/research_platform/bi_dashboards.py` | 182 | `lab_id` | **RETAIN** | `filters={"lab_id": int(lab_id) if lab_id.isdigit() else 0},` |
| `backend/app/research_platform/bi_dashboards.py` | 182 | `lab_id` | **RETAIN** | `filters={"lab_id": int(lab_id) if lab_id.isdigit() else 0},` |
| `backend/app/research_platform/bi_dashboards.py` | 188 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/research_platform/bi_dashboards.py` | 188 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/research_platform/bi_dashboards.py` | 192 | `lab_id` | **RETAIN** | `"tat": self._tat_analysis(lab_id),` |
| `backend/app/research_platform/bi_dashboards.py` | 193 | `lab_id` | **RETAIN** | `"quality_control": self._qc_summary(lab_id),` |
| `backend/app/research_platform/bi_dashboards.py` | 197 | `lab_id` | **RETAIN** | `def _tat_analysis(self, lab_id: str) -> dict:` |
| `backend/app/research_platform/bi_dashboards.py` | 200 | `lab_id` | **RETAIN** | `def _qc_summary(self, lab_id: str) -> dict:` |
| `backend/app/research_platform/routes.py` | 330 | `lab_id` | **RETAIN** | `@router.get("/dashboards/laboratory/{lab_id}")` |
| `backend/app/research_platform/routes.py` | 331 | `lab_id` | **RETAIN** | `def laboratory_dashboard(lab_id: str, sdk: ResearchSDK = Depends(get_sdk)):` |
| `backend/app/research_platform/routes.py` | 332 | `lab_id` | **RETAIN** | `return sdk.lab_dashboard.render(lab_id)` |
| `backend/app/routes/admin.py` | 23 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/admin.py` | 46 | `LabUser` | **RETAIN** | `def require_admin(current_user: LabUser = Depends(require_permission("system:admin"))):` |
| `backend/app/routes/admin.py` | 52 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("platform:manage_users")),` |
| `backend/app/routes/admin.py` | 61 | `LabUser` | **RETAIN** | `def _user_dict(u: LabUser, lab_name: str \| None = None) -> dict:` |
| `backend/app/routes/admin.py` | 68 | `lab_id` | **RETAIN** | `"lab_id": u.lab_id,` |
| `backend/app/routes/admin.py` | 68 | `lab_id` | **RETAIN** | `"lab_id": u.lab_id,` |
| `backend/app/routes/admin.py` | 83 | `LabUser` | **RETAIN** | `def platform_stats(admin: LabUser = Depends(require_admin), db: Session = Depends(get_db)):` |
| `backend/app/routes/admin.py` | 88 | `LabUser` | **RETAIN** | `"total_users": db.query(func.count(LabUser.id)).scalar() or 0,` |
| `backend/app/routes/admin.py` | 93 | `LabUser` | **RETAIN** | `role: db.query(func.count(LabUser.id)).filter(LabUser.role == role).scalar() or 0` |
| `backend/app/routes/admin.py` | 93 | `LabUser` | **RETAIN** | `role: db.query(func.count(LabUser.id)).filter(LabUser.role == role).scalar() or 0` |
| `backend/app/routes/admin.py` | 106 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 117 | `LabUser` | **RETAIN** | `for row in db.query(LabUser.lab_id)` |
| `backend/app/routes/admin.py` | 117 | `lab_id` | **RETAIN** | `for row in db.query(LabUser.lab_id)` |
| `backend/app/routes/admin.py` | 118 | `LabUser` | **RETAIN** | `.filter(LabUser.province_id == actor.province_id)` |
| `backend/app/routes/admin.py` | 125 | `lab_id` | **RETAIN** | `query = query.filter(Lab.id == actor.lab_id)` |
| `backend/app/routes/admin.py` | 133 | `LabUser` | **RETAIN** | `db.query(LabUser.lab_id, func.count(LabUser.id))` |
| `backend/app/routes/admin.py` | 133 | `lab_id` | **RETAIN** | `db.query(LabUser.lab_id, func.count(LabUser.id))` |
| `backend/app/routes/admin.py` | 133 | `LabUser` | **RETAIN** | `db.query(LabUser.lab_id, func.count(LabUser.id))` |
| `backend/app/routes/admin.py` | 134 | `LabUser` | **RETAIN** | `.filter(LabUser.lab_id.in_(lab_ids))` |
| `backend/app/routes/admin.py` | 134 | `lab_id` | **RETAIN** | `.filter(LabUser.lab_id.in_(lab_ids))` |
| `backend/app/routes/admin.py` | 135 | `LabUser` | **RETAIN** | `.group_by(LabUser.lab_id)` |
| `backend/app/routes/admin.py` | 135 | `lab_id` | **RETAIN** | `.group_by(LabUser.lab_id)` |
| `backend/app/routes/admin.py` | 144 | `lab_id` | **RETAIN** | `db.query(Patient.lab_id, func.count(Patient.id))` |
| `backend/app/routes/admin.py` | 145 | `lab_id` | **RETAIN** | `.filter(Patient.lab_id.in_(lab_ids))` |
| `backend/app/routes/admin.py` | 146 | `lab_id` | **RETAIN** | `.group_by(Patient.lab_id)` |
| `backend/app/routes/admin.py` | 172 | `lab_id` | **RETAIN** | `@router.put("/labs/{lab_id}/toggle")` |
| `backend/app/routes/admin.py` | 174 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/routes/admin.py` | 175 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 179 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == lab_id).first()` |
| `backend/app/routes/admin.py` | 186 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/routes/admin.py` | 188 | `LabUser` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/routes/admin.py` | 188 | `lab_id` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/routes/admin.py` | 188 | `lab_id` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/routes/admin.py` | 189 | `LabUser` | **RETAIN** | `LabUser.province_id == actor.province_id,` |
| `backend/app/routes/admin.py` | 213 | `lab_id` | **RETAIN** | `@router.put("/labs/{lab_id}/activate")` |
| `backend/app/routes/admin.py` | 215 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/routes/admin.py` | 216 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 222 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == lab_id).first()` |
| `backend/app/routes/admin.py` | 226 | `lab_id` | **RETAIN** | `return {"message": "Lab is already active", "lab_id": lab_id, "is_active": True}` |
| `backend/app/routes/admin.py` | 226 | `lab_id` | **RETAIN** | `return {"message": "Lab is already active", "lab_id": lab_id, "is_active": True}` |
| `backend/app/routes/admin.py` | 231 | `LabUser` | **RETAIN** | `db.query(LabUser).filter(` |
| `backend/app/routes/admin.py` | 232 | `LabUser` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/routes/admin.py` | 232 | `lab_id` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/routes/admin.py` | 232 | `lab_id` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/routes/admin.py` | 233 | `LabUser` | **RETAIN** | `LabUser.role == "admin",` |
| `backend/app/routes/admin.py` | 246 | `lab_id` | **RETAIN** | `return {"message": "Lab activated successfully", "lab_id": lab_id, "is_active": True}` |
| `backend/app/routes/admin.py` | 246 | `lab_id` | **RETAIN** | `return {"message": "Lab activated successfully", "lab_id": lab_id, "is_active": True}` |
| `backend/app/routes/admin.py` | 251 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 262 | `LabUser` | **RETAIN** | `for row in db.query(LabUser.lab_id)` |
| `backend/app/routes/admin.py` | 262 | `lab_id` | **RETAIN** | `for row in db.query(LabUser.lab_id)` |
| `backend/app/routes/admin.py` | 263 | `LabUser` | **RETAIN** | `.filter(LabUser.province_id == actor.province_id)` |
| `backend/app/routes/admin.py` | 275 | `LabUser` | **RETAIN** | `db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 275 | `LabUser` | **RETAIN** | `db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 275 | `lab_id` | **RETAIN** | `db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 275 | `LabUser` | **RETAIN** | `db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 293 | `lab_id` | **RETAIN** | `@router.get("/labs/{lab_id}")` |
| `backend/app/routes/admin.py` | 295 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/routes/admin.py` | 296 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 300 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == lab_id).first()` |
| `backend/app/routes/admin.py` | 304 | `LabUser` | **RETAIN** | `admin_user = db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 304 | `LabUser` | **RETAIN** | `admin_user = db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 304 | `lab_id` | **RETAIN** | `admin_user = db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 304 | `LabUser` | **RETAIN** | `admin_user = db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()` |
| `backend/app/routes/admin.py` | 305 | `LabUser` | **RETAIN** | `staff_count = db.query(func.count(LabUser.id)).filter(LabUser.lab_id == lab.id).scalar() or 0` |
| `backend/app/routes/admin.py` | 305 | `LabUser` | **RETAIN** | `staff_count = db.query(func.count(LabUser.id)).filter(LabUser.lab_id == lab.id).scalar() or 0` |
| `backend/app/routes/admin.py` | 305 | `lab_id` | **RETAIN** | `staff_count = db.query(func.count(LabUser.id)).filter(LabUser.lab_id == lab.id).scalar() or 0` |
| `backend/app/routes/admin.py` | 306 | `lab_id` | **RETAIN** | `patient_count = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab.id).scalar() or 0` |
| `backend/app/routes/admin.py` | 334 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 376 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 423 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 460 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 500 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 532 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 596 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 603 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.admin_email).first():` |
| `backend/app/routes/admin.py` | 603 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.admin_email).first():` |
| `backend/app/routes/admin.py` | 615 | `LabUser` | **RETAIN** | `lab_admin = LabUser(` |
| `backend/app/routes/admin.py` | 616 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/routes/admin.py` | 635 | `lab_id` | **RETAIN** | `return {"message": "Lab created", "lab_id": lab.id, "admin_email": data.admin_email}` |
| `backend/app/routes/admin.py` | 645 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 648 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/routes/admin.py` | 654 | `LabUser` | **RETAIN** | `query = db.query(LabUser)` |
| `backend/app/routes/admin.py` | 660 | `LabUser` | **RETAIN** | `query = query.filter(LabUser.role.in_(visible_roles))` |
| `backend/app/routes/admin.py` | 664 | `LabUser` | **RETAIN** | `query = query.filter(LabUser.province_id == actor.province_id)` |
| `backend/app/routes/admin.py` | 668 | `LabUser` | **RETAIN** | `query = query.filter(LabUser.lab_id == actor.lab_id)` |
| `backend/app/routes/admin.py` | 668 | `lab_id` | **RETAIN** | `query = query.filter(LabUser.lab_id == actor.lab_id)` |
| `backend/app/routes/admin.py` | 668 | `lab_id` | **RETAIN** | `query = query.filter(LabUser.lab_id == actor.lab_id)` |
| `backend/app/routes/admin.py` | 677 | `LabUser` | **RETAIN** | `query = query.filter(LabUser.role == role)` |
| `backend/app/routes/admin.py` | 679 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/routes/admin.py` | 680 | `LabUser` | **RETAIN** | `query = query.filter(LabUser.lab_id == lab_id)` |
| `backend/app/routes/admin.py` | 680 | `lab_id` | **RETAIN** | `query = query.filter(LabUser.lab_id == lab_id)` |
| `backend/app/routes/admin.py` | 680 | `lab_id` | **RETAIN** | `query = query.filter(LabUser.lab_id == lab_id)` |
| `backend/app/routes/admin.py` | 683 | `LabUser` | **RETAIN** | `users = query.order_by(LabUser.created_at.desc()).offset(skip).limit(limit).all()` |
| `backend/app/routes/admin.py` | 686 | `lab_id` | **RETAIN** | `lab_ids = {u.lab_id for u in users}` |
| `backend/app/routes/admin.py` | 693 | `lab_id` | **RETAIN** | `"users": [_user_dict(u, labs_map.get(u.lab_id)) for u in users],` |
| `backend/app/routes/admin.py` | 702 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/routes/admin.py` | 729 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 750 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.email).first():` |
| `backend/app/routes/admin.py` | 750 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.email).first():` |
| `backend/app/routes/admin.py` | 753 | `lab_id` | **RETAIN** | `# Determine lab_id` |
| `backend/app/routes/admin.py` | 754 | `lab_id` | **RETAIN** | `target_lab_id = data.lab_id or actor.lab_id` |
| `backend/app/routes/admin.py` | 754 | `lab_id` | **RETAIN** | `target_lab_id = data.lab_id or actor.lab_id` |
| `backend/app/routes/admin.py` | 756 | `lab_id` | **RETAIN** | `target_lab_id = actor.lab_id  # lab admin can only create in own lab` |
| `backend/app/routes/admin.py` | 771 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.national_id_hash == nid_hash).first():` |
| `backend/app/routes/admin.py` | 771 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.national_id_hash == nid_hash).first():` |
| `backend/app/routes/admin.py` | 774 | `LabUser` | **RETAIN** | `new_user = LabUser(` |
| `backend/app/routes/admin.py` | 775 | `lab_id` | **RETAIN** | `lab_id=target_lab_id,` |
| `backend/app/routes/admin.py` | 813 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 821 | `LabUser` | **RETAIN** | `target = db.query(LabUser).filter(LabUser.id == user_id).first()` |
| `backend/app/routes/admin.py` | 821 | `LabUser` | **RETAIN** | `target = db.query(LabUser).filter(LabUser.id == user_id).first()` |
| `backend/app/routes/admin.py` | 873 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_manage_users),` |
| `backend/app/routes/admin.py` | 877 | `LabUser` | **RETAIN** | `target = db.query(LabUser).filter(LabUser.id == user_id).first()` |
| `backend/app/routes/admin.py` | 877 | `LabUser` | **RETAIN** | `target = db.query(LabUser).filter(LabUser.id == user_id).first()` |
| `backend/app/routes/admin.py` | 907 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(require_permission("audit:read")),` |
| `backend/app/routes/admin.py` | 920 | `LabUser` | **RETAIN** | `row[0] for row in db.query(LabUser.id).filter(LabUser.lab_id == actor.lab_id).all()` |
| `backend/app/routes/admin.py` | 920 | `LabUser` | **RETAIN** | `row[0] for row in db.query(LabUser.id).filter(LabUser.lab_id == actor.lab_id).all()` |
| `backend/app/routes/admin.py` | 920 | `lab_id` | **RETAIN** | `row[0] for row in db.query(LabUser.id).filter(LabUser.lab_id == actor.lab_id).all()` |
| `backend/app/routes/admin.py` | 920 | `lab_id` | **RETAIN** | `row[0] for row in db.query(LabUser.id).filter(LabUser.lab_id == actor.lab_id).all()` |
| `backend/app/routes/admin.py` | 969 | `LabUser` | **RETAIN** | `def kill_switch_status(admin: LabUser = Depends(require_admin)):` |
| `backend/app/routes/admin.py` | 979 | `LabUser` | **RETAIN** | `admin: LabUser = Depends(require_admin),` |
| `backend/app/routes/admin.py` | 1005 | `LabUser` | **RETAIN** | `admin: LabUser = Depends(require_admin),` |
| `backend/app/routes/admin.py` | 1029 | `LabUser` | **RETAIN** | `def control_layer_stats(admin: LabUser = Depends(require_admin)):` |
| `backend/app/routes/admin_log_level.py` | 8 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/admin_log_level.py` | 24 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/admin_log_level.py` | 38 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ai.py` | 273 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/ai.py` | 273 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/ai.py` | 809 | `lab_id` | **RETAIN** | `lab_order_ids = db.query(LabOrder.id).filter(LabOrder.lab_id == current_user.lab_id).subquery()` |
| `backend/app/routes/ai.py` | 809 | `lab_id` | **RETAIN** | `lab_order_ids = db.query(LabOrder.id).filter(LabOrder.lab_id == current_user.lab_id).subquery()` |
| `backend/app/routes/ai_platform.py` | 127 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 127 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 150 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 150 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 174 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 174 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 251 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 251 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 288 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 288 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 295 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 295 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 340 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 340 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 359 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_platform.py` | 359 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 12 | `LabUser` | **RETAIN** | `All write endpoints require an authenticated ``LabUser`` and enforce tenant` |
| `backend/app/routes/ai_telemetry.py` | 13 | `lab_id` | **RETAIN** | `isolation by stamping ``lab_id`` from the JWT (never trusting the request body).` |
| `backend/app/routes/ai_telemetry.py` | 57 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/ai_telemetry.py` | 156 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/routes/ai_telemetry.py` | 204 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ai_telemetry.py` | 215 | `lab_id` | **RETAIN** | `"ai.dataset.intent.unknown intent=%s lab_id=%s", payload.intent, current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 215 | `lab_id` | **RETAIN** | `"ai.dataset.intent.unknown intent=%s lab_id=%s", payload.intent, current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 271 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 271 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 319 | `lab_id` | **RETAIN** | `lab_id=interaction.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 319 | `lab_id` | **RETAIN** | `lab_id=interaction.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 336 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ai_telemetry.py` | 349 | `lab_id` | **RETAIN** | `.filter(AIInteraction.id == iid, AIInteraction.lab_id == current_user.lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 349 | `lab_id` | **RETAIN** | `.filter(AIInteraction.id == iid, AIInteraction.lab_id == current_user.lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 387 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ai_telemetry.py` | 400 | `lab_id` | **RETAIN** | `.filter(AIInteraction.id == iid, AIInteraction.lab_id == current_user.lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 400 | `lab_id` | **RETAIN** | `.filter(AIInteraction.id == iid, AIInteraction.lab_id == current_user.lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 411 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 411 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 433 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ai_telemetry.py` | 442 | `lab_id` | **RETAIN** | `.filter(AIInteraction.id == iid_uuid, AIInteraction.lab_id == current_user.lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 442 | `lab_id` | **RETAIN** | `.filter(AIInteraction.id == iid_uuid, AIInteraction.lab_id == current_user.lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 453 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 453 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 475 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ai_telemetry.py` | 478 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/ai_telemetry.py` | 478 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/ai_telemetry.py` | 481 | `lab_id` | **RETAIN** | `db.query(func.count(AIInteraction.id)).filter(AIInteraction.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/ai_telemetry.py` | 481 | `lab_id` | **RETAIN** | `db.query(func.count(AIInteraction.id)).filter(AIInteraction.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/ai_telemetry.py` | 484 | `lab_id` | **RETAIN** | `db.query(func.count(AIFeedback.id)).filter(AIFeedback.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/ai_telemetry.py` | 484 | `lab_id` | **RETAIN** | `db.query(func.count(AIFeedback.id)).filter(AIFeedback.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/ai_telemetry.py` | 488 | `lab_id` | **RETAIN** | `.filter(AIUnresolvedQuestion.lab_id == lab_id, AIUnresolvedQuestion.status == "open")` |
| `backend/app/routes/ai_telemetry.py` | 488 | `lab_id` | **RETAIN** | `.filter(AIUnresolvedQuestion.lab_id == lab_id, AIUnresolvedQuestion.status == "open")` |
| `backend/app/routes/ai_telemetry.py` | 494 | `lab_id` | **RETAIN** | `.filter(AIFeedback.lab_id == lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 494 | `lab_id` | **RETAIN** | `.filter(AIFeedback.lab_id == lab_id)` |
| `backend/app/routes/ai_telemetry.py` | 500 | `lab_id` | **RETAIN** | `# All filters tenant-scoped on lab_id.` |
| `backend/app/routes/ai_telemetry.py` | 503 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.risk_level.isnot(None))` |
| `backend/app/routes/ai_telemetry.py` | 503 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.risk_level.isnot(None))` |
| `backend/app/routes/ai_telemetry.py` | 509 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.escalation_recommended.is_(True))` |
| `backend/app/routes/ai_telemetry.py` | 509 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.escalation_recommended.is_(True))` |
| `backend/app/routes/ai_telemetry.py` | 515 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.fallback_generation.is_(True))` |
| `backend/app/routes/ai_telemetry.py` | 515 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.fallback_generation.is_(True))` |
| `backend/app/routes/ai_telemetry.py` | 521 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.confidence_score.isnot(None))` |
| `backend/app/routes/ai_telemetry.py` | 521 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.confidence_score.isnot(None))` |
| `backend/app/routes/ai_telemetry.py` | 526 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.source_quality.isnot(None))` |
| `backend/app/routes/ai_telemetry.py` | 526 | `lab_id` | **RETAIN** | `.filter(AIInteraction.lab_id == lab_id, AIInteraction.source_quality.isnot(None))` |
| `backend/app/routes/ai_telemetry.py` | 530 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/routes/ai_telemetry.py` | 530 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/routes/authorization.py` | 296 | `lab_id` | **RETAIN** | `context["user"]["lab_id"] = current_user.lab_id` |
| `backend/app/routes/authorization.py` | 296 | `lab_id` | **RETAIN** | `context["user"]["lab_id"] = current_user.lab_id` |
| `backend/app/routes/batch.py` | 8 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/batch.py` | 40 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/batch.py` | 53 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/batch.py` | 53 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/batch.py` | 70 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/batch.py` | 70 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/canonical_patient.py` | 10 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/canonical_patient.py` | 27 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/routes/canonical_patient.py` | 46 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/routes/canonical_patient.py` | 117 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/canonical_patient.py` | 133 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/canonical_patient.py` | 148 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/canonical_patient.py` | 166 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/canonical_patient.py` | 181 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/canonical_patient.py` | 199 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/canonical_patient.py` | 236 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/canonical_patient.py` | 264 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 16 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/care_continuum.py` | 99 | `LabUser` | **RETAIN** | `def _lab_id(user: LabUser) -> int \| None:` |
| `backend/app/routes/care_continuum.py` | 100 | `lab_id` | **RETAIN** | `return user.lab_id` |
| `backend/app/routes/care_continuum.py` | 103 | `LabUser` | **RETAIN** | `def _practitioner_id(user: LabUser) -> str \| None:` |
| `backend/app/routes/care_continuum.py` | 115 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 127 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 143 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 158 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 180 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 193 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 202 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 215 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 224 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 235 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 244 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 257 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 271 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 280 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 293 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 307 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 325 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 340 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 351 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 362 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 376 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 390 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 399 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 413 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 422 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 433 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 442 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 453 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 462 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 471 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 480 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 491 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 500 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 513 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 529 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 543 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 559 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 572 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 585 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 596 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 609 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 620 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 634 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 646 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 660 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 671 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 680 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 691 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 700 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 711 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 723 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 737 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 750 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 761 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 774 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 784 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 793 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 803 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 814 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 828 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 838 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 849 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 860 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 872 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 881 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 892 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 904 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 916 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 930 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 943 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 956 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 968 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 985 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/care_continuum.py` | 1002 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/cds_hooks.py` | 13 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/cds_hooks.py` | 44 | `LabUser` | **RETAIN** | `def cds_services(current_user: LabUser = Depends(get_current_user)) -> dict:` |
| `backend/app/routes/cds_hooks.py` | 68 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/citizen_portal.py` | 21 | `LabUser` | **RETAIN** | `- Requires role='citizen' in JWT (LabUser.role == 'citizen' rejected)` |
| `backend/app/routes/citizen_portal.py` | 208 | `lab_id` | **RETAIN** | `"lab_id": None,` |
| `backend/app/routes/citizen_portal.py` | 273 | `lab_id` | **RETAIN** | `lab_ids = {p.lab_id for p in patients if p.lab_id}` |
| `backend/app/routes/citizen_portal.py` | 273 | `lab_id` | **RETAIN** | `lab_ids = {p.lab_id for p in patients if p.lab_id}` |
| `backend/app/routes/citizen_portal.py` | 303 | `lab_id` | **RETAIN** | `lab_map = {}  # lab_id → lab_name` |
| `backend/app/routes/citizen_portal.py` | 315 | `lab_id` | **RETAIN** | `lab_ids = {o.lab_id for o in orders}` |
| `backend/app/routes/citizen_portal.py` | 323 | `lab_id` | **RETAIN** | `lab_name = lab_map.get(order.lab_id, "مختبر")` |
| `backend/app/routes/citizen_portal.py` | 377 | `lab_id` | **RETAIN** | `lab_ids = {o.lab_id for o in orders}` |
| `backend/app/routes/citizen_portal.py` | 392 | `lab_id` | **RETAIN** | `"lab_name": lab_map.get(o.lab_id, "مختبر"),` |
| `backend/app/routes/citizen_portal.py` | 446 | `lab_id` | **RETAIN** | `lab_name = f"مختبر #{order.lab_id}"` |
| `backend/app/routes/citizen_portal.py` | 486 | `lab_id` | **RETAIN** | `"labs_visited": len({o.lab_id for o in orders}),` |
| `backend/app/routes/citizen_relationship_admin.py` | 20 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/citizen_relationship_admin.py` | 53 | `LabUser` | **RETAIN** | `def _relationship_admin(actor: LabUser = Depends(require_permission("platform:manage_users"))) -> LabUser:` |
| `backend/app/routes/citizen_relationship_admin.py` | 53 | `LabUser` | **RETAIN** | `def _relationship_admin(actor: LabUser = Depends(require_permission("platform:manage_users"))) -> LabUser:` |
| `backend/app/routes/citizen_relationship_admin.py` | 74 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(_relationship_admin),` |
| `backend/app/routes/citizen_relationship_admin.py` | 106 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(_relationship_admin),` |
| `backend/app/routes/citizen_relationship_admin.py` | 127 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(_relationship_admin),` |
| `backend/app/routes/citizen_relationship_admin.py` | 145 | `LabUser` | **RETAIN** | `actor: LabUser = Depends(_relationship_admin),` |
| `backend/app/routes/claims.py` | 10 | `lab_id` | **RETAIN** | `current_user.lab_id (security invariant).` |
| `backend/app/routes/claims.py` | 21 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/claims.py` | 62 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/routes/claims.py` | 82 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/routes/claims.py` | 82 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/routes/claims.py` | 114 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/claims.py` | 126 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/claims.py` | 126 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/claims.py` | 141 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/claims.py` | 149 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/claims.py` | 149 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/claims.py` | 163 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/claims.py` | 171 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/claims.py` | 171 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/claims.py` | 185 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/claims.py` | 193 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/claims.py` | 193 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/clinical.py` | 15 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/clinical.py` | 117 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 129 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 139 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 152 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 164 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 178 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 188 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 198 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 210 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 220 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 230 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 241 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 251 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 264 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 279 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 293 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 305 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 345 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 494 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 506 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 516 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 529 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 546 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 558 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 568 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 581 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 598 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 610 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 620 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 633 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 648 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 663 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 675 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 688 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 749 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 761 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 773 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 788 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 800 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 814 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 831 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 845 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 857 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 987 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1004 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1014 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1028 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1045 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1055 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1070 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1085 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1097 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1109 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1121 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1133 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1170 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1181 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1196 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1206 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1220 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1263 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1276 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1290 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1303 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical.py` | 1317 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 13 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/clinical_documentation.py` | 161 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 175 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 189 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 203 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 217 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 231 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 249 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 267 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 285 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 299 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 311 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_documentation.py` | 311 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_documentation.py` | 327 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_documentation.py` | 363 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 13 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/clinical_orders.py` | 97 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 116 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_orders.py` | 116 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_orders.py` | 133 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 156 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 168 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 188 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 230 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 244 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 251 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_orders.py` | 251 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_orders.py` | 269 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 282 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_orders.py` | 282 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/clinical_orders.py` | 296 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_orders.py` | 318 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_quality.py` | 10 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/clinical_quality.py` | 27 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_quality.py` | 53 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_quality.py` | 68 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/clinical_quality.py` | 85 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 35 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/compliance.py` | 49 | `LabUser` | **RETAIN** | `def system_info(current_user: LabUser = Depends(get_current_user)):` |
| `backend/app/routes/compliance.py` | 142 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 152 | `LabUser` | **RETAIN** | `u.id for u in db.query(LabUser.id).filter(LabUser.lab_id == current_user.lab_id).all()` |
| `backend/app/routes/compliance.py` | 152 | `LabUser` | **RETAIN** | `u.id for u in db.query(LabUser.id).filter(LabUser.lab_id == current_user.lab_id).all()` |
| `backend/app/routes/compliance.py` | 152 | `lab_id` | **RETAIN** | `u.id for u in db.query(LabUser.id).filter(LabUser.lab_id == current_user.lab_id).all()` |
| `backend/app/routes/compliance.py` | 152 | `lab_id` | **RETAIN** | `u.id for u in db.query(LabUser.id).filter(LabUser.lab_id == current_user.lab_id).all()` |
| `backend/app/routes/compliance.py` | 170 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 170 | `lab_id` | **RETAIN** | `"lab_id": current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 182 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 195 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 195 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 231 | `lab_id` | **RETAIN** | `"reference": f"Organization/{patient.lab_id}",` |
| `backend/app/routes/compliance.py` | 258 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 268 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 268 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 281 | `lab_id` | **RETAIN** | `.filter(LabResult.order_id == order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/compliance.py` | 281 | `lab_id` | **RETAIN** | `.filter(LabResult.order_id == order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/compliance.py` | 312 | `lab_id` | **RETAIN** | `"performer": [{"reference": f"Organization/{order.lab_id}"}],` |
| `backend/app/routes/compliance.py` | 357 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 373 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 373 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 384 | `lab_id` | **RETAIN** | `.filter(LabResult.order_id == order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/compliance.py` | 384 | `lab_id` | **RETAIN** | `.filter(LabResult.order_id == order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/compliance.py` | 388 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == order.lab_id).first()` |
| `backend/app/routes/compliance.py` | 446 | `lab_id` | **RETAIN** | `"reference": f"Organization/{order.lab_id}",` |
| `backend/app/routes/compliance.py` | 468 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 483 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 483 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 495 | `lab_id` | **RETAIN** | `.filter(LabResult.order_id == order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/compliance.py` | 495 | `lab_id` | **RETAIN** | `.filter(LabResult.order_id == order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/compliance.py` | 539 | `lab_id` | **RETAIN** | `"performer": [{"reference": f"Organization/{order.lab_id}"}],` |
| `backend/app/routes/compliance.py` | 553 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 578 | `lab_id` | **RETAIN** | `WHERE lab_orders.lab_id = :lab_id` |
| `backend/app/routes/compliance.py` | 578 | `lab_id` | **RETAIN** | `WHERE lab_orders.lab_id = :lab_id` |
| `backend/app/routes/compliance.py` | 583 | `lab_id` | **RETAIN** | `{"lab_id": current_user.lab_id},` |
| `backend/app/routes/compliance.py` | 583 | `lab_id` | **RETAIN** | `{"lab_id": current_user.lab_id},` |
| `backend/app/routes/compliance.py` | 594 | `lab_id` | **RETAIN** | `WHERE lab_id = :lab_id` |
| `backend/app/routes/compliance.py` | 594 | `lab_id` | **RETAIN** | `WHERE lab_id = :lab_id` |
| `backend/app/routes/compliance.py` | 599 | `lab_id` | **RETAIN** | `{"lab_id": current_user.lab_id},` |
| `backend/app/routes/compliance.py` | 599 | `lab_id` | **RETAIN** | `{"lab_id": current_user.lab_id},` |
| `backend/app/routes/compliance.py` | 603 | `lab_id` | **RETAIN** | `db.query(func.count(Patient.id)).filter(Patient.lab_id == current_user.lab_id).scalar() or 0` |
| `backend/app/routes/compliance.py` | 603 | `lab_id` | **RETAIN** | `db.query(func.count(Patient.id)).filter(Patient.lab_id == current_user.lab_id).scalar() or 0` |
| `backend/app/routes/compliance.py` | 607 | `lab_id` | **RETAIN** | `db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == current_user.lab_id).scalar()` |
| `backend/app/routes/compliance.py` | 607 | `lab_id` | **RETAIN** | `db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == current_user.lab_id).scalar()` |
| `backend/app/routes/compliance.py` | 633 | `lab_id` | **RETAIN** | `"orgUnit": f"LAB_{current_user.lab_id}",` |
| `backend/app/routes/compliance.py` | 671 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 690 | `lab_id` | **RETAIN** | `result["lab_id"] = current_user.lab_id` |
| `backend/app/routes/compliance.py` | 690 | `lab_id` | **RETAIN** | `result["lab_id"] = current_user.lab_id` |
| `backend/app/routes/compliance.py` | 702 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 733 | `LabUser` | **RETAIN** | `db.query(func.count(LabUser.id))` |
| `backend/app/routes/compliance.py` | 735 | `LabUser` | **RETAIN** | `LabUser.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 735 | `lab_id` | **RETAIN** | `LabUser.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 735 | `lab_id` | **RETAIN** | `LabUser.lab_id == current_user.lab_id,` |
| `backend/app/routes/compliance.py` | 736 | `LabUser` | **RETAIN** | `LabUser.is_active,` |
| `backend/app/routes/compliance.py` | 763 | `lab_id` | **RETAIN** | `"object_level_auth": "PASS - patient/order/result access checked per lab_id",` |
| `backend/app/routes/compliance.py` | 923 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/compliance.py` | 956 | `lab_id` | **RETAIN** | `db.query(func.count(Patient.id)).filter(Patient.lab_id == current_user.lab_id).scalar() or 0` |
| `backend/app/routes/compliance.py` | 956 | `lab_id` | **RETAIN** | `db.query(func.count(Patient.id)).filter(Patient.lab_id == current_user.lab_id).scalar() or 0` |
| `backend/app/routes/compliance.py` | 960 | `lab_id` | **RETAIN** | `db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == current_user.lab_id).scalar()` |
| `backend/app/routes/compliance.py` | 960 | `lab_id` | **RETAIN** | `db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == current_user.lab_id).scalar()` |
| `backend/app/routes/consent.py` | 25 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/consent.py` | 79 | `LabUser` | **RETAIN** | `def _user_owns_gpid(user: LabUser, gpid: str) -> bool:` |
| `backend/app/routes/consent.py` | 91 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/consent.py` | 143 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/consent.py` | 178 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/critical_alerts.py` | 7 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/critical_alerts.py` | 23 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/critical_alerts.py` | 27 | `lab_id` | **RETAIN** | `return _get_critical_alerts(db, current_user.lab_id, hours)` |
| `backend/app/routes/critical_alerts.py` | 32 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/critical_alerts.py` | 36 | `lab_id` | **RETAIN** | `return _alert_statistics(db, current_user.lab_id)` |
| `backend/app/routes/dashboard.py` | 12 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/dashboard.py` | 40 | `LabUser` | **RETAIN** | `def greeting(current_user: LabUser = Depends(get_current_user)):` |
| `backend/app/routes/dashboard.py` | 53 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("dashboard:read")),` |
| `backend/app/routes/dashboard.py` | 56 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/dashboard.py` | 56 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/dashboard.py` | 70 | `lab_id` | **RETAIN** | `.filter(Patient.lab_id == lab_id)` |
| `backend/app/routes/dashboard.py` | 70 | `lab_id` | **RETAIN** | `.filter(Patient.lab_id == lab_id)` |
| `backend/app/routes/dashboard.py` | 82 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/dashboard.py` | 82 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/dashboard.py` | 109 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/dashboard.py` | 109 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/dashboard.py` | 119 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/dashboard.py` | 119 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/dashboard.py` | 148 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/dashboard.py` | 148 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/demo.py` | 18 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/demo.py` | 81 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.email == selected["email"]).first()` |
| `backend/app/routes/demo.py` | 81 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.email == selected["email"]).first()` |
| `backend/app/routes/demo.py` | 83 | `LabUser` | **RETAIN** | `user = LabUser(` |
| `backend/app/routes/demo.py` | 84 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/routes/demo.py` | 97 | `lab_id` | **RETAIN** | `or user.lab_id != lab.id` |
| `backend/app/routes/demo.py` | 137 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/routes/demo.py` | 137 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/routes/device_results.py` | 10 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/device_results.py` | 39 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/device_results.py` | 60 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/device_results.py` | 60 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/edge.py` | 71 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/edge.py` | 226 | `lab_id` | **RETAIN** | `lab_id: int \| None = None` |
| `backend/app/routes/edge.py` | 242 | `LabUser` | **RETAIN** | `def _require_admin(user: LabUser) -> None:` |
| `backend/app/routes/edge.py` | 247 | `LabUser` | **RETAIN** | `def _require_master(user: LabUser) -> None:` |
| `backend/app/routes/edge.py` | 281 | `lab_id` | **RETAIN** | `# over (device_id, cert_fingerprint, lab_id) with the global signing key.` |
| `backend/app/routes/edge.py` | 290 | `lab_id` | **RETAIN** | `msg = f"{device.device_id}\|{device.cert_fingerprint}\|{device.lab_id}".encode()` |
| `backend/app/routes/edge.py` | 334 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 342 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 342 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 371 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 376 | `lab_id` | **RETAIN** | `q = db.query(EdgeDevice).filter(EdgeDevice.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 376 | `lab_id` | **RETAIN** | `q = db.query(EdgeDevice).filter(EdgeDevice.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 387 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 392 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 392 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 395 | `lab_id` | **RETAIN** | `latest = tele.latest(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 395 | `lab_id` | **RETAIN** | `latest = tele.latest(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 422 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 428 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 428 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 441 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 447 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 447 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 459 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 465 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 465 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 481 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 487 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 487 | `lab_id` | **RETAIN** | `d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 504 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 512 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 512 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 545 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 550 | `lab_id` | **RETAIN** | `q = db.query(EdgeTask).filter(EdgeTask.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 550 | `lab_id` | **RETAIN** | `q = db.query(EdgeTask).filter(EdgeTask.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 563 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 570 | `lab_id` | **RETAIN** | `.filter(EdgeTask.task_uid == task_uid, EdgeTask.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 570 | `lab_id` | **RETAIN** | `.filter(EdgeTask.task_uid == task_uid, EdgeTask.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 590 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 597 | `lab_id` | **RETAIN** | `.filter(EdgeTask.task_uid == task_uid, EdgeTask.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 597 | `lab_id` | **RETAIN** | `.filter(EdgeTask.task_uid == task_uid, EdgeTask.lab_id == user.lab_id)` |
| `backend/app/routes/edge.py` | 615 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 620 | `lab_id` | **RETAIN** | `p = policy_mod.get_policy(db, user.lab_id)` |
| `backend/app/routes/edge.py` | 628 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 637 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 637 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 643 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 643 | `lab_id` | **RETAIN** | `lab_id=user.lab_id,` |
| `backend/app/routes/edge.py` | 651 | `lab_id` | **RETAIN** | `p = policy_mod.get_policy(db, user.lab_id)` |
| `backend/app/routes/edge.py` | 658 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 663 | `lab_id` | **RETAIN** | `summary = tele.fleet_summary(db, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 663 | `lab_id` | **RETAIN** | `summary = tele.fleet_summary(db, lab_id=user.lab_id)` |
| `backend/app/routes/edge.py` | 664 | `lab_id` | **RETAIN** | `devices_total = db.query(EdgeDevice).filter(EdgeDevice.lab_id == user.lab_id).count()` |
| `backend/app/routes/edge.py` | 664 | `lab_id` | **RETAIN** | `devices_total = db.query(EdgeDevice).filter(EdgeDevice.lab_id == user.lab_id).count()` |
| `backend/app/routes/edge.py` | 668 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == user.lab_id,` |
| `backend/app/routes/edge.py` | 668 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == user.lab_id,` |
| `backend/app/routes/edge.py` | 677 | `lab_id` | **RETAIN** | `"kill_switched": policy_mod.get_policy(db, user.lab_id).kill_switch,` |
| `backend/app/routes/edge.py` | 690 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 722 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 748 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 773 | `LabUser` | **RETAIN** | `user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/edge.py` | 778 | `lab_id` | **RETAIN** | `if body.lab_id is not None and body.lab_id != user.lab_id:` |
| `backend/app/routes/edge.py` | 778 | `lab_id` | **RETAIN** | `if body.lab_id is not None and body.lab_id != user.lab_id:` |
| `backend/app/routes/edge.py` | 778 | `lab_id` | **RETAIN** | `if body.lab_id is not None and body.lab_id != user.lab_id:` |
| `backend/app/routes/edge.py` | 790 | `lab_id` | **RETAIN** | `lab_id=body.lab_id if body.lab_id is not None else user.lab_id,` |
| `backend/app/routes/edge.py` | 790 | `lab_id` | **RETAIN** | `lab_id=body.lab_id if body.lab_id is not None else user.lab_id,` |
| `backend/app/routes/edge.py` | 790 | `lab_id` | **RETAIN** | `lab_id=body.lab_id if body.lab_id is not None else user.lab_id,` |
| `backend/app/routes/edge.py` | 790 | `lab_id` | **RETAIN** | `lab_id=body.lab_id if body.lab_id is not None else user.lab_id,` |
| `backend/app/routes/edge.py` | 797 | `lab_id` | **RETAIN** | `return {"id": a.id, "model_uid": a.model_uid, "lab_id": a.lab_id, "device_id": a.device_id}` |
| `backend/app/routes/edge.py` | 797 | `lab_id` | **RETAIN** | `return {"id": a.id, "model_uid": a.model_uid, "lab_id": a.lab_id, "device_id": a.device_id}` |
| `backend/app/routes/edge.py` | 828 | `lab_id` | **RETAIN** | `tele.record(db, lab_id=device.lab_id, device_id=device.device_id, sample=body.telemetry)` |
| `backend/app/routes/edge.py` | 828 | `lab_id` | **RETAIN** | `tele.record(db, lab_id=device.lab_id, device_id=device.device_id, sample=body.telemetry)` |
| `backend/app/routes/edge.py` | 832 | `lab_id` | **RETAIN** | `pol = policy_mod.get_policy(db, device.lab_id)` |
| `backend/app/routes/edge.py` | 880 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == device.lab_id,` |
| `backend/app/routes/edge.py` | 880 | `lab_id` | **RETAIN** | `EdgeTask.lab_id == device.lab_id,` |
| `backend/app/routes/edge.py` | 912 | `lab_id` | **RETAIN** | `tele.record(db, lab_id=device.lab_id, device_id=device.device_id, sample=sample)` |
| `backend/app/routes/edge.py` | 912 | `lab_id` | **RETAIN** | `tele.record(db, lab_id=device.lab_id, device_id=device.device_id, sample=sample)` |
| `backend/app/routes/ehr.py` | 27 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/ehr.py` | 36 | `lab_id` | **RETAIN** | `def _get_patient(db: Session, patient_id: str, lab_id: int):` |
| `backend/app/routes/ehr.py` | 37 | `lab_id` | **RETAIN** | `return ehr_service.get_national_patient_or_404(db, patient_id, lab_id)` |
| `backend/app/routes/ehr.py` | 94 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 97 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 106 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 112 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 123 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 144 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 150 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 161 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 167 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 181 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 184 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 197 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 244 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 247 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 256 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 262 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 270 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 276 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 285 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 291 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 305 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 308 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 348 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 351 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 363 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 369 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 380 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 386 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 400 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 406 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 420 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 423 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 470 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 473 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 485 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 491 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 502 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 508 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 522 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 528 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 542 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 545 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 585 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 588 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 600 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 606 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 617 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 623 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 637 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 643 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 657 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 660 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 699 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 702 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 716 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 722 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 733 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 739 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 753 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 759 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 773 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 776 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 820 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 823 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 832 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 838 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 854 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 860 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 877 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 883 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 897 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 900 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 935 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 941 | `lab_id` | **RETAIN** | `_get_patient(db, cp.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 956 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 964 | `lab_id` | **RETAIN** | `_get_patient(db, cp.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 978 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 986 | `lab_id` | **RETAIN** | `_get_patient(db, cp.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1021 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1027 | `lab_id` | **RETAIN** | `_get_patient(db, cp.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1042 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1050 | `lab_id` | **RETAIN** | `_get_patient(db, cp.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1064 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1072 | `lab_id` | **RETAIN** | `_get_patient(db, cp.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1116 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1119 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1131 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1137 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1148 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1154 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1168 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1174 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1188 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1191 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1237 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1240 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1252 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1258 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1269 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1275 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1287 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1293 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1307 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1310 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1356 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1359 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1371 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1377 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1388 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1394 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1406 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1412 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1426 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1429 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1470 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1473 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1485 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1491 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1502 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1508 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1522 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1528 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1542 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1545 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1596 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1599 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1611 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1617 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1628 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1634 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1648 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1654 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1668 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1671 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1715 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1718 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1730 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1736 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1747 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1753 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1767 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1773 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1787 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1790 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1844 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1847 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1859 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1865 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1876 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1882 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1896 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1902 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1916 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1919 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1969 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1972 | `lab_id` | **RETAIN** | `_get_patient(db, body.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 1984 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 1990 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 2001 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 2007 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 2021 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 2027 | `lab_id` | **RETAIN** | `_get_patient(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 2041 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 2044 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 2064 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 2067 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 2083 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 2086 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr.py` | 2097 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr.py` | 2100 | `lab_id` | **RETAIN** | `_get_patient(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 33 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/ehr_fhir.py` | 114 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 131 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 134 | `lab_id` | **RETAIN** | `patient = ehr_service.get_national_patient_or_404(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 181 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 192 | `lab_id` | **RETAIN** | `db, encounter.patient_id, current_user.lab_id,` |
| `backend/app/routes/ehr_fhir.py` | 246 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 263 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 324 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 328 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 360 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 373 | `lab_id` | **RETAIN** | `.filter(LabOrder.id == result.order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 373 | `lab_id` | **RETAIN** | `.filter(LabOrder.id == result.order_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 425 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 437 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 437 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 505 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 518 | `lab_id` | **RETAIN** | `.filter(AuditLog.lab_id == current_user.lab_id, AuditLog.resource_type == "FHIR")` |
| `backend/app/routes/ehr_fhir.py` | 518 | `lab_id` | **RETAIN** | `.filter(AuditLog.lab_id == current_user.lab_id, AuditLog.resource_type == "FHIR")` |
| `backend/app/routes/ehr_fhir.py` | 545 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 552 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 552 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 593 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 599 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 660 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 664 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 689 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 695 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 748 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 754 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 807 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 813 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 834 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 838 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 878 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 884 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 932 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 936 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 961 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 967 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1028 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1032 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1057 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1063 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1106 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1110 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1138 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1144 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1201 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1205 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1236 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1246 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1249 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, bundle_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1317 | `lab_id` | **RETAIN** | `.filter(LabOrder.patient_id == bundle_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1317 | `lab_id` | **RETAIN** | `.filter(LabOrder.patient_id == bundle_id, LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1372 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1382 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, patient_id, current_user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1397 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1419 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1440 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/ehr_fhir.py` | 1469 | `lab_id` | **RETAIN** | `if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1469 | `lab_id` | **RETAIN** | `if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1469 | `lab_id` | **RETAIN** | `if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1483 | `lab_id` | **RETAIN** | `if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1483 | `lab_id` | **RETAIN** | `if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1483 | `lab_id` | **RETAIN** | `if rec and hasattr(rec, "lab_id") and getattr(rec, "lab_id", None) != current_user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1569 | `LabUser` | **RETAIN** | `def _get_fhir_resource_or_404(db: Session, resource_type: str, resource_id: str, user: LabUser):` |
| `backend/app/routes/ehr_fhir.py` | 1578 | `lab_id` | **RETAIN** | `if hasattr(record, "lab_id") and getattr(record, "lab_id", None) and record.lab_id != user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1578 | `lab_id` | **RETAIN** | `if hasattr(record, "lab_id") and getattr(record, "lab_id", None) and record.lab_id != user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1578 | `lab_id` | **RETAIN** | `if hasattr(record, "lab_id") and getattr(record, "lab_id", None) and record.lab_id != user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1578 | `lab_id` | **RETAIN** | `if hasattr(record, "lab_id") and getattr(record, "lab_id", None) and record.lab_id != user.lab_id:` |
| `backend/app/routes/ehr_fhir.py` | 1581 | `lab_id` | **RETAIN** | `ehr_service.get_national_patient_or_404(db, record.patient_id, user.lab_id)` |
| `backend/app/routes/ehr_fhir.py` | 1588 | `LabUser` | **RETAIN** | `user: LabUser, now: datetime,` |
| `backend/app/routes/ehr_fhir.py` | 1594 | `lab_id` | **RETAIN** | `if hasattr(record, "lab_id"):` |
| `backend/app/routes/ehr_fhir.py` | 1595 | `lab_id` | **RETAIN** | `record.lab_id = user.lab_id` |
| `backend/app/routes/ehr_fhir.py` | 1595 | `lab_id` | **RETAIN** | `record.lab_id = user.lab_id` |
| `backend/app/routes/ehr_fhir.py` | 1619 | `LabUser` | **RETAIN** | `user: LabUser, now: datetime,` |
| `backend/app/routes/hospital.py` | 18 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/hospital.py` | 233 | `lab_id` | **RETAIN** | `exclude = {"lab_id", "is_deleted", "deleted_at", "version"}` |
| `backend/app/routes/hospital.py` | 262 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 264 | `lab_id` | **RETAIN** | `hospitals = HospitalService.list_hospitals(db, current_user.lab_id, skip, limit)` |
| `backend/app/routes/hospital.py` | 266 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == current_user.lab_id,` |
| `backend/app/routes/hospital.py` | 266 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == current_user.lab_id,` |
| `backend/app/routes/hospital.py` | 278 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 280 | `lab_id` | **RETAIN** | `return _model_to_dict(HospitalService.get_hospital(db, hospital_id, current_user.lab_id))` |
| `backend/app/routes/hospital.py` | 287 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 290 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 300 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 306 | `lab_id` | **RETAIN** | `db, hospital_id, current_user.lab_id, current_user.id, data,` |
| `backend/app/routes/hospital.py` | 315 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 317 | `lab_id` | **RETAIN** | `HospitalService.deactivate_hospital(db, hospital_id, current_user.lab_id, current_user.id)` |
| `backend/app/routes/hospital.py` | 328 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 330 | `lab_id` | **RETAIN** | `campuses = HospitalService.list_campuses(db, current_user.lab_id, hospital_id)` |
| `backend/app/routes/hospital.py` | 339 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 342 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 352 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 354 | `lab_id` | **RETAIN** | `campus = HospitalService._get_entity(db, Campus, campus_id, current_user.lab_id)` |
| `backend/app/routes/hospital.py` | 369 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 371 | `lab_id` | **RETAIN** | `buildings = HospitalService.list_buildings(db, current_user.lab_id, campus_id)` |
| `backend/app/routes/hospital.py` | 380 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 383 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, campus_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 395 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 397 | `lab_id` | **RETAIN** | `floors = HospitalService.list_floors(db, current_user.lab_id, building_id)` |
| `backend/app/routes/hospital.py` | 406 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 409 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, building_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 422 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 425 | `lab_id` | **RETAIN** | `db, current_user.lab_id, hospital_id, parent_id,` |
| `backend/app/routes/hospital.py` | 435 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 438 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 448 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 450 | `lab_id` | **RETAIN** | `dept = HospitalService._get_entity(db, HospitalDepartment, dept_id, current_user.lab_id)` |
| `backend/app/routes/hospital.py` | 465 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 467 | `lab_id` | **RETAIN** | `clinics = HospitalService.list_clinics(db, current_user.lab_id, dept_id)` |
| `backend/app/routes/hospital.py` | 476 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 479 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, dept_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 492 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 494 | `lab_id` | **RETAIN** | `rooms = HospitalService.list_rooms(db, current_user.lab_id, dept_id, room_type)` |
| `backend/app/routes/hospital.py` | 503 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 506 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, dept_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 520 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 522 | `lab_id` | **RETAIN** | `beds = HospitalService.list_beds(db, current_user.lab_id, room_id, status, bed_type)` |
| `backend/app/routes/hospital.py` | 531 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 534 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, room_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 547 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 550 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, bed_id,` |
| `backend/app/routes/hospital.py` | 561 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 564 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, bed_id, body.discharge_reason,` |
| `backend/app/routes/hospital.py` | 574 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 577 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id,` |
| `backend/app/routes/hospital.py` | 589 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 591 | `lab_id` | **RETAIN** | `return HospitalService.bed_occupancy_stats(db, current_user.lab_id, hospital_id)` |
| `backend/app/routes/hospital.py` | 601 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 603 | `lab_id` | **RETAIN** | `units = HospitalService.list_units(db, current_user.lab_id, hospital_id)` |
| `backend/app/routes/hospital.py` | 612 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 615 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 627 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 629 | `lab_id` | **RETAIN** | `ots = HospitalService.list_operation_theaters(db, current_user.lab_id, hospital_id)` |
| `backend/app/routes/hospital.py` | 638 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 641 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 651 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 653 | `lab_id` | **RETAIN** | `ot = HospitalService._get_entity(db, OperationTheater, ot_id, current_user.lab_id)` |
| `backend/app/routes/hospital.py` | 671 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 674 | `lab_id` | **RETAIN** | `db, current_user.lab_id, hospital_id, category, equipment_status,` |
| `backend/app/routes/hospital.py` | 684 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 687 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 697 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 699 | `lab_id` | **RETAIN** | `equip = HospitalService._get_entity(db, MedicalEquipment, equip_id, current_user.lab_id)` |
| `backend/app/routes/hospital.py` | 714 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 716 | `lab_id` | **RETAIN** | `ccs = HospitalService.list_cost_centers(db, current_user.lab_id, hospital_id)` |
| `backend/app/routes/hospital.py` | 725 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 728 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, hospital_id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 743 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 746 | `lab_id` | **RETAIN** | `db, current_user.lab_id, hospital_id, patient_id, skip, limit,` |
| `backend/app/routes/hospital.py` | 758 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 761 | `lab_id` | **RETAIN** | `db, current_user.lab_id, current_user.id, body.model_dump(),` |
| `backend/app/routes/hospital.py` | 773 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 775 | `lab_id` | **RETAIN** | `return HospitalService.dashboard(db, current_user.lab_id, hospital_id)` |
| `backend/app/routes/hospital.py` | 785 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/hospital.py` | 787 | `lab_id` | **RETAIN** | `HospitalService._get_entity(db, Bed, bed_id, current_user.lab_id)` |
| `backend/app/routes/hospital.py` | 790 | `lab_id` | **RETAIN** | `BedAssignment.lab_id == current_user.lab_id,` |
| `backend/app/routes/hospital.py` | 790 | `lab_id` | **RETAIN** | `BedAssignment.lab_id == current_user.lab_id,` |
| `backend/app/routes/id_scan.py` | 20 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/id_scan.py` | 140 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/identity.py` | 8 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/identity.py` | 25 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/identity.py` | 33 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/identity.py` | 33 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/identity.py` | 70 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/identity.py` | 79 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/identity.py` | 79 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/insurance.py` | 4 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/insurance.py` | 13 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/integrations.py` | 51 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/integrations.py` | 167 | `LabUser` | **RETAIN** | `_user: LabUser = Depends(require_role("master_admin", "ministry_admin")),` |
| `backend/app/routes/integrations.py` | 205 | `LabUser` | **RETAIN** | `reviewer: LabUser = Depends(require_role("master_admin", "ministry_admin")),` |
| `backend/app/routes/integrations.py` | 218 | `lab_id` | **RETAIN** | `lab_id=getattr(reviewer, "lab_id", None),` |
| `backend/app/routes/integrations.py` | 218 | `lab_id` | **RETAIN** | `lab_id=getattr(reviewer, "lab_id", None),` |
| `backend/app/routes/integrations.py` | 294 | `LabUser` | **RETAIN** | `_user: LabUser = Depends(require_role("master_admin", "ministry_admin")),` |
| `backend/app/routes/integrations.py` | 308 | `LabUser` | **RETAIN** | `_user: LabUser = Depends(require_role("master_admin", "ministry_admin")),` |
| `backend/app/routes/labs.py` | 7 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/labs.py` | 35 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/labs.py` | 38 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()` |
| `backend/app/routes/labs.py` | 90 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/labs.py` | 97 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/routes/labs.py` | 98 | `LabUser` | **RETAIN** | `.filter(LabUser.lab_id == current_user.lab_id)` |
| `backend/app/routes/labs.py` | 98 | `lab_id` | **RETAIN** | `.filter(LabUser.lab_id == current_user.lab_id)` |
| `backend/app/routes/labs.py` | 98 | `lab_id` | **RETAIN** | `.filter(LabUser.lab_id == current_user.lab_id)` |
| `backend/app/routes/labs.py` | 99 | `LabUser` | **RETAIN** | `.order_by(LabUser.created_at.desc())` |
| `backend/app/routes/labs.py` | 120 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/labs.py` | 128 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.email).first():` |
| `backend/app/routes/labs.py` | 128 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.email).first():` |
| `backend/app/routes/labs.py` | 131 | `LabUser` | **RETAIN** | `employee = LabUser(` |
| `backend/app/routes/labs.py` | 132 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/labs.py` | 132 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/labs.py` | 149 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/labs.py` | 156 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/routes/labs.py` | 157 | `LabUser` | **RETAIN** | `.filter(LabUser.id == employee_id, LabUser.lab_id == current_user.lab_id)` |
| `backend/app/routes/labs.py` | 157 | `LabUser` | **RETAIN** | `.filter(LabUser.id == employee_id, LabUser.lab_id == current_user.lab_id)` |
| `backend/app/routes/labs.py` | 157 | `lab_id` | **RETAIN** | `.filter(LabUser.id == employee_id, LabUser.lab_id == current_user.lab_id)` |
| `backend/app/routes/labs.py` | 157 | `lab_id` | **RETAIN** | `.filter(LabUser.id == employee_id, LabUser.lab_id == current_user.lab_id)` |
| `backend/app/routes/labs.py` | 187 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/labs.py` | 193 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()` |
| `backend/app/routes/login.py` | 12 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/login.py` | 53 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/routes/login.py` | 55 | `LabUser` | **RETAIN** | `LabUser.email == identifier,` |
| `backend/app/routes/login.py` | 56 | `LabUser` | **RETAIN** | `LabUser.is_active,` |
| `backend/app/routes/login.py` | 99 | `LabUser` | **RETAIN** | `if not isinstance(user, LabUser) and not user.is_verified:` |
| `backend/app/routes/login.py` | 141 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == lab_user.lab_id, Lab.is_active).first()` |
| `backend/app/routes/login.py` | 164 | `lab_id` | **RETAIN** | `"lab_id": None,` |
| `backend/app/routes/login.py` | 218 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/routes/login.py` | 218 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/routes/login.py` | 262 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.id == user_id).first()` |
| `backend/app/routes/login.py` | 262 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.id == user_id).first()` |
| `backend/app/routes/login.py` | 287 | `LabUser` | **RETAIN** | `if isinstance(user, LabUser) and user.lab_id:` |
| `backend/app/routes/login.py` | 287 | `lab_id` | **RETAIN** | `if isinstance(user, LabUser) and user.lab_id:` |
| `backend/app/routes/login.py` | 290 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == user.lab_id).first()` |
| `backend/app/routes/login.py` | 298 | `lab_id` | **RETAIN** | `"lab_id": getattr(user, "lab_id", None),` |
| `backend/app/routes/login.py` | 298 | `lab_id` | **RETAIN** | `"lab_id": getattr(user, "lab_id", None),` |
| `backend/app/routes/metrics.py` | 23 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/metrics.py` | 78 | `lab_id` | **RETAIN** | `def _order_stats(db: Session, lab_id: int \| None) -> dict:` |
| `backend/app/routes/metrics.py` | 96 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/routes/metrics.py` | 97 | `lab_id` | **RETAIN** | `q = q.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/metrics.py` | 97 | `lab_id` | **RETAIN** | `q = q.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/routes/metrics.py` | 111 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/metrics.py` | 117 | `lab_id` | **RETAIN** | `- Everyone else: scoped to their lab_id` |
| `backend/app/routes/metrics.py` | 123 | `lab_id` | **RETAIN** | `stats = _order_stats(db, lab_id=None if is_wide else current_user.lab_id)` |
| `backend/app/routes/metrics.py` | 123 | `lab_id` | **RETAIN** | `stats = _order_stats(db, lab_id=None if is_wide else current_user.lab_id)` |
| `backend/app/routes/metrics.py` | 167 | `lab_id` | **RETAIN** | `stats = _order_stats(db, lab_id=None)` |
| `backend/app/routes/mobile.py` | 24 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/mobile.py` | 84 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/routes/mobile.py` | 85 | `LabUser` | **RETAIN** | `.filter(LabUser.id == user_id, LabUser.is_active)` |
| `backend/app/routes/mobile.py` | 85 | `LabUser` | **RETAIN** | `.filter(LabUser.id == user_id, LabUser.is_active)` |
| `backend/app/routes/mobile.py` | 100 | `LabUser` | **RETAIN** | `if isinstance(user, LabUser) and user.role != "master_admin":` |
| `backend/app/routes/mobile.py` | 101 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == user.lab_id, Lab.is_active).first()` |
| `backend/app/routes/mobile.py` | 121 | `LabUser` | **RETAIN** | `if isinstance(user, LabUser)` |
| `backend/app/routes/mobile.py` | 124 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/routes/mobile.py` | 124 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/routes/mobile.py` | 194 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/mobile.py` | 256 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/mobile.py` | 263 | `lab_id` | **RETAIN** | `if current_user.lab_id:` |
| `backend/app/routes/mobile.py` | 264 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()` |
| `backend/app/routes/mobile.py` | 312 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/mobile.py` | 348 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/mobile.py` | 364 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/mobile.py` | 364 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/mobile.py` | 366 | `lab_id` | **RETAIN** | `total_patients = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/mobile.py` | 366 | `lab_id` | **RETAIN** | `total_patients = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/mobile.py` | 368 | `lab_id` | **RETAIN** | `total_orders = db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/mobile.py` | 368 | `lab_id` | **RETAIN** | `total_orders = db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/mobile.py` | 373 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/mobile.py` | 373 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/mobile.py` | 383 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/mobile.py` | 383 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/national_data.py` | 9 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/national_data.py` | 175 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 178 | `lab_id` | **RETAIN** | `return CanonicalPatient.query_all(db=db, lab_id=current_user.lab_id, skip=skip, limit=limit)` |
| `backend/app/routes/national_data.py` | 178 | `lab_id` | **RETAIN** | `return CanonicalPatient.query_all(db=db, lab_id=current_user.lab_id, skip=skip, limit=limit)` |
| `backend/app/routes/national_data.py` | 184 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 187 | `lab_id` | **RETAIN** | `result = CanonicalPatient.get_by_id(db=db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/national_data.py` | 187 | `lab_id` | **RETAIN** | `result = CanonicalPatient.get_by_id(db=db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/national_data.py` | 199 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 202 | `lab_id` | **RETAIN** | `return CanonicalEncounter.query_all(db=db, lab_id=current_user.lab_id, skip=skip, limit=limit)` |
| `backend/app/routes/national_data.py` | 202 | `lab_id` | **RETAIN** | `return CanonicalEncounter.query_all(db=db, lab_id=current_user.lab_id, skip=skip, limit=limit)` |
| `backend/app/routes/national_data.py` | 208 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 211 | `lab_id` | **RETAIN** | `result = CanonicalEncounter.get_by_id(db=db, encounter_id=encounter_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/national_data.py` | 211 | `lab_id` | **RETAIN** | `result = CanonicalEncounter.get_by_id(db=db, encounter_id=encounter_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/national_data.py` | 220 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 242 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 246 | `lab_id` | **RETAIN** | `db=db, lab_id=current_user.lab_id, patient_id=patient_id, skip=skip, limit=limit,` |
| `backend/app/routes/national_data.py` | 246 | `lab_id` | **RETAIN** | `db=db, lab_id=current_user.lab_id, patient_id=patient_id, skip=skip, limit=limit,` |
| `backend/app/routes/national_data.py` | 253 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 256 | `lab_id` | **RETAIN** | `result = CanonicalObservation.get_by_id(db=db, observation_id=observation_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/national_data.py` | 256 | `lab_id` | **RETAIN** | `result = CanonicalObservation.get_by_id(db=db, observation_id=observation_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/national_data.py` | 265 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("results:write")),` |
| `backend/app/routes/national_data.py` | 286 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 298 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 318 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 338 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 365 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 393 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 418 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 447 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 461 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 488 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 521 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 532 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 545 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/national_data.py` | 545 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/national_data.py` | 556 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 569 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 594 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 609 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 632 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 655 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 681 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 705 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 732 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 743 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/national_data.py` | 743 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/national_data.py` | 754 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 782 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 806 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 836 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_data.py` | 865 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_data.py` | 876 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/national_data.py` | 876 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/national_identity.py` | 7 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/national_identity.py` | 20 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/national_streaming.py` | 13 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/national_streaming.py` | 74 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_streaming.py` | 117 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_streaming.py` | 166 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/national_streaming.py` | 205 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:read")),` |
| `backend/app/routes/national_streaming.py` | 240 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("patients:write")),` |
| `backend/app/routes/notifications.py` | 14 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/notifications.py` | 38 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/notifications.py` | 47 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/notifications.py` | 47 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/notifications.py` | 58 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == order.lab_id).first()` |
| `backend/app/routes/notifications.py` | 101 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/notifications.py` | 111 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/notifications.py` | 111 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/password_reset.py` | 12 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/password_reset.py` | 41 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.email == req.email).first()` |
| `backend/app/routes/password_reset.py` | 41 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.email == req.email).first()` |
| `backend/app/routes/password_reset.py` | 64 | `LabUser` | **RETAIN** | `users = db.query(LabUser).filter(` |
| `backend/app/routes/password_reset.py` | 65 | `LabUser` | **RETAIN** | `LabUser.reset_token.isnot(None),` |
| `backend/app/routes/password_reset.py` | 66 | `LabUser` | **RETAIN** | `LabUser.reset_token_expires > datetime.now(UTC),` |
| `backend/app/routes/patient_card.py` | 12 | `lab_id` | **RETAIN** | `- All reads filter by ``current_user.lab_id`` (tenant isolation).` |
| `backend/app/routes/patient_card.py` | 27 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/patient_card.py` | 58 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patient_card.py` | 64 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 64 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 68 | `lab_id` | **RETAIN** | `token = issue_card_token(patient.id, patient.lab_id)` |
| `backend/app/routes/patient_card.py` | 92 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patient_card.py` | 100 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 100 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 104 | `lab_id` | **RETAIN** | `token = issue_card_token(patient.id, patient.lab_id)` |
| `backend/app/routes/patient_card.py` | 116 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patient_card.py` | 144 | `lab_id` | **RETAIN** | `if token_lab_id != current_user.lab_id:` |
| `backend/app/routes/patient_card.py` | 158 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 158 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 184 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patient_card.py` | 190 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 190 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 272 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patient_card.py` | 280 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 280 | `lab_id` | **RETAIN** | `patient = lookup_patient_for_lab(db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patient_card.py` | 284 | `lab_id` | **RETAIN** | `token = issue_card_token(patient.id, patient.lab_id)` |
| `backend/app/routes/patients.py` | 6 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/patients.py` | 165 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patients.py` | 171 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/patients.py` | 171 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/patients.py` | 182 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patients.py` | 189 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/patients.py` | 189 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/patients.py` | 213 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patients.py` | 221 | `lab_id` | **RETAIN** | `result = _get_family_members(db=db, family_id=family_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patients.py` | 221 | `lab_id` | **RETAIN** | `result = _get_family_members(db=db, family_id=family_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patients.py` | 232 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patients.py` | 240 | `lab_id` | **RETAIN** | `result = _get_patient_children(db=db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patients.py` | 240 | `lab_id` | **RETAIN** | `result = _get_patient_children(db=db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patients.py` | 251 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patients.py` | 254 | `lab_id` | **RETAIN** | `result = _get_patient_by_id(db=db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patients.py` | 254 | `lab_id` | **RETAIN** | `result = _get_patient_by_id(db=db, patient_id=patient_id, lab_id=current_user.lab_id)` |
| `backend/app/routes/patients.py` | 265 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/patients.py` | 271 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/patients.py` | 271 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/qr.py` | 45 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == order.lab_id).first() if order else None` |
| `backend/app/routes/quality_control.py` | 13 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/quality_control.py` | 61 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/routes/quality_control.py` | 85 | `lab_id` | **RETAIN** | `QualityControl.lab_id == lab_id,` |
| `backend/app/routes/quality_control.py` | 85 | `lab_id` | **RETAIN** | `QualityControl.lab_id == lab_id,` |
| `backend/app/routes/quality_control.py` | 150 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/quality_control.py` | 159 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 159 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 170 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 170 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 199 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/quality_control.py` | 208 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 208 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 218 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 218 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 253 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/quality_control.py` | 259 | `lab_id` | **RETAIN** | `QualityControl.lab_id == current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 259 | `lab_id` | **RETAIN** | `QualityControl.lab_id == current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 279 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/quality_control.py` | 291 | `lab_id` | **RETAIN** | `QualityControl.lab_id == current_user.lab_id,` |
| `backend/app/routes/quality_control.py` | 291 | `lab_id` | **RETAIN** | `QualityControl.lab_id == current_user.lab_id,` |
| `backend/app/routes/register.py` | 11 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/register.py` | 203 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.email == data.email).first()` |
| `backend/app/routes/register.py` | 203 | `LabUser` | **RETAIN** | `existing = db.query(LabUser).filter(LabUser.email == data.email).first()` |
| `backend/app/routes/register.py` | 227 | `LabUser` | **RETAIN** | `user = LabUser(` |
| `backend/app/routes/register.py` | 228 | `lab_id` | **RETAIN** | `lab_id=lab.id,` |
| `backend/app/routes/register.py` | 244 | `lab_id` | **RETAIN** | `details=f"New lab registration pending approval: {data.lab_name} (lab_id={lab.id})",` |
| `backend/app/routes/register.py` | 256 | `lab_id` | **RETAIN** | `"lab_id": lab.id,` |
| `backend/app/routes/register.py` | 443 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/register.py` | 463 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.email).first():` |
| `backend/app/routes/register.py` | 463 | `LabUser` | **RETAIN** | `if db.query(LabUser).filter(LabUser.email == data.email).first():` |
| `backend/app/routes/register.py` | 472 | `LabUser` | **RETAIN** | `staff = LabUser(` |
| `backend/app/routes/register.py` | 473 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/register.py` | 473 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/register.py` | 491 | `lab_id` | **RETAIN** | `details=f"Staff registered: {data.name} <{data.email}> role={data.role} lab_id={current_user.lab_id}",` |
| `backend/app/routes/register.py` | 491 | `lab_id` | **RETAIN** | `details=f"Staff registered: {data.name} <{data.email}> role={data.role} lab_id={current_user.lab_id}",` |
| `backend/app/routes/register.py` | 503 | `lab_id` | **RETAIN** | `"lab_id": staff.lab_id,` |
| `backend/app/routes/register.py` | 503 | `lab_id` | **RETAIN** | `"lab_id": staff.lab_id,` |
| `backend/app/routes/results.py` | 8 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/results.py` | 98 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 117 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 117 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 139 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 144 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 144 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 156 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 162 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 162 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 176 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 197 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 197 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 214 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 223 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 223 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 268 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 275 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 275 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/results.py` | 312 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 347 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/results.py` | 360 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/results.py` | 360 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/samples.py` | 10 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/samples.py` | 52 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/samples.py` | 60 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/samples.py` | 60 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/samples.py` | 105 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/samples.py` | 112 | `lab_id` | **RETAIN** | `query = db.query(Sample).join(LabOrder).filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/samples.py` | 112 | `lab_id` | **RETAIN** | `query = db.query(Sample).join(LabOrder).filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/samples.py` | 126 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/samples.py` | 135 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/samples.py` | 135 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/samples.py` | 149 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/samples.py` | 158 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/samples.py` | 158 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/security.py` | 13 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/security.py` | 21 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/setup.py` | 12 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/setup.py` | 30 | `LabUser` | **RETAIN** | `has_users = db.query(LabUser.id).first() is not None` |
| `backend/app/routes/stats.py` | 4 | `lab_id` | **RETAIN** | `All queries are scoped to the requesting lab's tenant (lab_id isolation).` |
| `backend/app/routes/stats.py` | 7 | `lab_id` | **RETAIN** | `Cache key format: stats:{lab_id}:{endpoint}:{params_hash}` |
| `backend/app/routes/stats.py` | 25 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/stats.py` | 75 | `lab_id` | **RETAIN** | `def _cache_key(lab_id: int, endpoint: str, **params) -> str:` |
| `backend/app/routes/stats.py` | 79 | `lab_id` | **RETAIN** | `return f"stats:{lab_id}:{endpoint}:{h}"` |
| `backend/app/routes/stats.py` | 88 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/stats.py` | 96 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 96 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 97 | `lab_id` | **RETAIN** | `cache_key = _cache_key(lab_id, "daily_trends", days=days)` |
| `backend/app/routes/stats.py` | 118 | `lab_id` | **RETAIN** | `WHERE lo.lab_id = :lab_id` |
| `backend/app/routes/stats.py` | 118 | `lab_id` | **RETAIN** | `WHERE lo.lab_id = :lab_id` |
| `backend/app/routes/stats.py` | 123 | `lab_id` | **RETAIN** | `{"lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/routes/stats.py` | 123 | `lab_id` | **RETAIN** | `{"lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/routes/stats.py` | 150 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/stats.py` | 157 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 157 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 158 | `lab_id` | **RETAIN** | `cache_key = _cache_key(lab_id, "test_frequency", days=days, limit=limit)` |
| `backend/app/routes/stats.py` | 177 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/stats.py` | 177 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/stats.py` | 206 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/stats.py` | 213 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 213 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 214 | `lab_id` | **RETAIN** | `cache_key = _cache_key(lab_id, "flag_distribution", days=days)` |
| `backend/app/routes/stats.py` | 228 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/stats.py` | 228 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/stats.py` | 256 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/stats.py` | 263 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 263 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 264 | `lab_id` | **RETAIN** | `cache_key = _cache_key(lab_id, "patient_growth", days=days)` |
| `backend/app/routes/stats.py` | 279 | `lab_id` | **RETAIN** | `WHERE lab_id = :lab_id` |
| `backend/app/routes/stats.py` | 279 | `lab_id` | **RETAIN** | `WHERE lab_id = :lab_id` |
| `backend/app/routes/stats.py` | 284 | `lab_id` | **RETAIN** | `{"lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/routes/stats.py` | 284 | `lab_id` | **RETAIN** | `{"lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/routes/stats.py` | 306 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/stats.py` | 313 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 313 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 314 | `lab_id` | **RETAIN** | `cache_key = _cache_key(lab_id, "summary")` |
| `backend/app/routes/stats.py` | 324 | `lab_id` | **RETAIN** | `total_patients = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/stats.py` | 324 | `lab_id` | **RETAIN** | `total_patients = db.query(func.count(Patient.id)).filter(Patient.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/stats.py` | 325 | `lab_id` | **RETAIN** | `total_orders = db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/stats.py` | 325 | `lab_id` | **RETAIN** | `total_orders = db.query(func.count(LabOrder.id)).filter(LabOrder.lab_id == lab_id).scalar() or 0` |
| `backend/app/routes/stats.py` | 327 | `lab_id` | **RETAIN** | `db.query(func.count(LabResult.id)).join(LabOrder).filter(LabOrder.lab_id == lab_id).scalar()` |
| `backend/app/routes/stats.py` | 327 | `lab_id` | **RETAIN** | `db.query(func.count(LabResult.id)).join(LabOrder).filter(LabOrder.lab_id == lab_id).scalar()` |
| `backend/app/routes/stats.py` | 333 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabResult.flag == "critical")` |
| `backend/app/routes/stats.py` | 333 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabResult.flag == "critical")` |
| `backend/app/routes/stats.py` | 340 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= today_start)` |
| `backend/app/routes/stats.py` | 340 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= today_start)` |
| `backend/app/routes/stats.py` | 347 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= week_start)` |
| `backend/app/routes/stats.py` | 347 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= week_start)` |
| `backend/app/routes/stats.py` | 354 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= month_start)` |
| `backend/app/routes/stats.py` | 354 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id, LabOrder.created_at >= month_start)` |
| `backend/app/routes/stats.py` | 363 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/stats.py` | 363 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/routes/stats.py` | 394 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/stats.py` | 401 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 401 | `lab_id` | **RETAIN** | `lab_id = current_user.lab_id` |
| `backend/app/routes/stats.py` | 402 | `lab_id` | **RETAIN** | `cache_key = _cache_key(lab_id, "turnaround", days=days)` |
| `backend/app/routes/stats.py` | 422 | `lab_id` | **RETAIN** | `WHERE lab_id = :lab_id` |
| `backend/app/routes/stats.py` | 422 | `lab_id` | **RETAIN** | `WHERE lab_id = :lab_id` |
| `backend/app/routes/stats.py` | 427 | `lab_id` | **RETAIN** | `{"lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/routes/stats.py` | 427 | `lab_id` | **RETAIN** | `{"lab_id": lab_id, "cutoff": cutoff},` |
| `backend/app/routes/telegram_webhook.py` | 12 | `LabUser` | **RETAIN** | `from app.models.lab_user import LabUser` |
| `backend/app/routes/telegram_webhook.py` | 85 | `LabUser` | **RETAIN** | `_current_user: LabUser = Depends(require_role("master_admin", "ministry_admin")),` |
| `backend/app/routes/test_results.py` | 32 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/test_results.py` | 236 | `LabUser` | **RETAIN** | `def _get_patient_scoped(db: Session, current_user: LabUser, health_id: str) -> Patient:` |
| `backend/app/routes/test_results.py` | 241 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 241 | `lab_id` | **RETAIN** | `Patient.lab_id == current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 281 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/test_results.py` | 310 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 310 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 326 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 326 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 403 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/routes/test_results.py` | 403 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/routes/test_results.py` | 443 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/test_results.py` | 476 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/test_results.py` | 495 | `lab_id` | **RETAIN** | `q = q.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/test_results.py` | 495 | `lab_id` | **RETAIN** | `q = q.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/test_results.py` | 507 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/test_results.py` | 527 | `lab_id` | **RETAIN** | `base = base.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/test_results.py` | 527 | `lab_id` | **RETAIN** | `base = base.filter(LabOrder.lab_id == current_user.lab_id)` |
| `backend/app/routes/test_results.py` | 591 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/test_results.py` | 611 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 611 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 660 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/test_results.py` | 689 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/test_results.py` | 689 | `lab_id` | **RETAIN** | `LabOrder.lab_id == current_user.lab_id,` |
| `backend/app/routes/tiers.py` | 10 | `lab_id` | **RETAIN** | `PUT  /admin/tiers/{lab_id}        — platform admin: manually set tier` |
| `backend/app/routes/tiers.py` | 11 | `lab_id` | **RETAIN** | `POST /admin/tiers/flags/{lab_id}  — platform admin: set/remove feature flag` |
| `backend/app/routes/tiers.py` | 35 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/routes/tiers.py` | 83 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/tiers.py` | 87 | `lab_id` | **RETAIN** | `if not current_user.lab_id:` |
| `backend/app/routes/tiers.py` | 89 | `lab_id` | **RETAIN** | `return get_lab_subscription_info(current_user.lab_id, db)` |
| `backend/app/routes/tiers.py` | 131 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/tiers.py` | 140 | `lab_id` | **RETAIN** | `if not current_user.lab_id:` |
| `backend/app/routes/tiers.py` | 144 | `lab_id` | **RETAIN** | `sub = db.query(LabSubscription).filter(LabSubscription.lab_id == current_user.lab_id).first()` |
| `backend/app/routes/tiers.py` | 144 | `lab_id` | **RETAIN** | `sub = db.query(LabSubscription).filter(LabSubscription.lab_id == current_user.lab_id).first()` |
| `backend/app/routes/tiers.py` | 156 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/tiers.py` | 156 | `lab_id` | **RETAIN** | `lab_id=current_user.lab_id,` |
| `backend/app/routes/tiers.py` | 167 | `lab_id` | **RETAIN** | `_update_demand_score(current_user.lab_id, db)` |
| `backend/app/routes/tiers.py` | 173 | `lab_id` | **RETAIN** | `resource_id=current_user.lab_id,` |
| `backend/app/routes/tiers.py` | 194 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/routes/tiers.py` | 220 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == body.lab_id, Lab.is_active).first()` |
| `backend/app/routes/tiers.py` | 228 | `lab_id` | **RETAIN** | `UpgradeRequest.lab_id == body.lab_id,` |
| `backend/app/routes/tiers.py` | 228 | `lab_id` | **RETAIN** | `UpgradeRequest.lab_id == body.lab_id,` |
| `backend/app/routes/tiers.py` | 251 | `lab_id` | **RETAIN** | `lab_id=body.lab_id,` |
| `backend/app/routes/tiers.py` | 251 | `lab_id` | **RETAIN** | `lab_id=body.lab_id,` |
| `backend/app/routes/tiers.py` | 259 | `lab_id` | **RETAIN** | `_update_demand_score(body.lab_id, db)` |
| `backend/app/routes/tiers.py` | 265 | `lab_id` | **RETAIN** | `resource_id=body.lab_id,` |
| `backend/app/routes/tiers.py` | 286 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/tiers.py` | 301 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == s.lab_id).first()` |
| `backend/app/routes/tiers.py` | 302 | `lab_id` | **RETAIN** | `sub = db.query(LabSubscription).filter(LabSubscription.lab_id == s.lab_id).first()` |
| `backend/app/routes/tiers.py` | 302 | `lab_id` | **RETAIN** | `sub = db.query(LabSubscription).filter(LabSubscription.lab_id == s.lab_id).first()` |
| `backend/app/routes/tiers.py` | 305 | `lab_id` | **RETAIN** | `"lab_id": s.lab_id,` |
| `backend/app/routes/tiers.py` | 305 | `lab_id` | **RETAIN** | `"lab_id": s.lab_id,` |
| `backend/app/routes/tiers.py` | 348 | `lab_id` | **RETAIN** | `@router.put("/admin/tiers/{lab_id}", summary="Platform admin: set lab tier")` |
| `backend/app/routes/tiers.py` | 350 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/routes/tiers.py` | 353 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/tiers.py` | 360 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == lab_id).first()` |
| `backend/app/routes/tiers.py` | 364 | `lab_id` | **RETAIN** | `sub = db.query(LabSubscription).filter(LabSubscription.lab_id == lab_id).first()` |
| `backend/app/routes/tiers.py` | 364 | `lab_id` | **RETAIN** | `sub = db.query(LabSubscription).filter(LabSubscription.lab_id == lab_id).first()` |
| `backend/app/routes/tiers.py` | 381 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/routes/tiers.py` | 381 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/routes/tiers.py` | 393 | `lab_id` | **RETAIN** | `UpgradeRequest.lab_id == lab_id,` |
| `backend/app/routes/tiers.py` | 393 | `lab_id` | **RETAIN** | `UpgradeRequest.lab_id == lab_id,` |
| `backend/app/routes/tiers.py` | 408 | `lab_id` | **RETAIN** | `resource_id=lab_id,` |
| `backend/app/routes/tiers.py` | 417 | `lab_id` | **RETAIN** | `"message": f"Lab {lab_id} tier updated to {body.tier}",` |
| `backend/app/routes/tiers.py` | 435 | `lab_id` | **RETAIN** | `@router.post("/admin/tiers/flags/{lab_id}", status_code=201, summary="Set feature flag for a lab")` |
| `backend/app/routes/tiers.py` | 437 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/routes/tiers.py` | 440 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/tiers.py` | 449 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == lab_id).first()` |
| `backend/app/routes/tiers.py` | 464 | `lab_id` | **RETAIN** | `FeatureFlag.lab_id == lab_id,` |
| `backend/app/routes/tiers.py` | 464 | `lab_id` | **RETAIN** | `FeatureFlag.lab_id == lab_id,` |
| `backend/app/routes/tiers.py` | 477 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/routes/tiers.py` | 477 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/routes/tiers.py` | 490 | `lab_id` | **RETAIN** | `resource_id=lab_id,` |
| `backend/app/routes/tiers.py` | 499 | `lab_id` | **RETAIN** | `"message": f"Feature flag '{body.feature_key}' set to {body.is_enabled} for lab {lab_id}",` |
| `backend/app/routes/tiers.py` | 506 | `lab_id` | **RETAIN** | `@router.get("/admin/tiers/flags/{lab_id}", summary="List feature flags for a lab")` |
| `backend/app/routes/tiers.py` | 508 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/routes/tiers.py` | 509 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/routes/tiers.py` | 514 | `lab_id` | **RETAIN** | `if current_user.role == "admin" and current_user.lab_id != lab_id:` |
| `backend/app/routes/tiers.py` | 514 | `lab_id` | **RETAIN** | `if current_user.role == "admin" and current_user.lab_id != lab_id:` |
| `backend/app/routes/tiers.py` | 517 | `lab_id` | **RETAIN** | `flags = db.query(FeatureFlag).filter(FeatureFlag.lab_id == lab_id).all()` |
| `backend/app/routes/tiers.py` | 517 | `lab_id` | **RETAIN** | `flags = db.query(FeatureFlag).filter(FeatureFlag.lab_id == lab_id).all()` |
| `backend/app/routes/tiers.py` | 519 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/routes/tiers.py` | 519 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/routes/tiers.py` | 536 | `lab_id` | **RETAIN** | `def _update_demand_score(lab_id: int, db: Session) -> None:` |
| `backend/app/routes/tiers.py` | 550 | `lab_id` | **RETAIN** | `UpgradeRequest.lab_id == lab_id,` |
| `backend/app/routes/tiers.py` | 550 | `lab_id` | **RETAIN** | `UpgradeRequest.lab_id == lab_id,` |
| `backend/app/routes/tiers.py` | 560 | `lab_id` | **RETAIN** | `score = db.query(UpgradeDemandScore).filter(UpgradeDemandScore.lab_id == lab_id).first()` |
| `backend/app/routes/tiers.py` | 560 | `lab_id` | **RETAIN** | `score = db.query(UpgradeDemandScore).filter(UpgradeDemandScore.lab_id == lab_id).first()` |
| `backend/app/routes/tiers.py` | 569 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/routes/tiers.py` | 569 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/security/auth.py` | 6 | `LabUser` | **RETAIN** | `- build_token_payload for LabUser` |
| `backend/app/security/auth.py` | 70 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/security/auth.py` | 70 | `lab_id` | **RETAIN** | `"lab_id": user.lab_id,` |
| `backend/app/security/consent_dep.py` | 39 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/security/consent_dep.py` | 44 | `LabUser` | **RETAIN** | `def _actor_id_for(user: LabUser) -> str:` |
| `backend/app/security/consent_dep.py` | 53 | `LabUser` | **RETAIN** | `def _is_owner(user: LabUser, gpid: str) -> bool:` |
| `backend/app/security/consent_dep.py` | 56 | `LabUser` | **RETAIN** | `LabUser exposes `national_id_hash` but not `citizen_ulid` directly;` |
| `backend/app/security/consent_dep.py` | 94 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/security/consent_dep.py` | 96 | `LabUser` | **RETAIN** | `) -> LabUser:` |
| `backend/app/security/dependencies.py` | 12 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/security/dependencies.py` | 40 | `LabUser` | **RETAIN** | `) -> LabUser:` |
| `backend/app/security/dependencies.py` | 65 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.id == user_id, LabUser.is_active).first()` |
| `backend/app/security/dependencies.py` | 65 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.id == user_id, LabUser.is_active).first()` |
| `backend/app/security/dependencies.py` | 65 | `LabUser` | **RETAIN** | `user = db.query(LabUser).filter(LabUser.id == user_id, LabUser.is_active).first()` |
| `backend/app/security/dependencies.py` | 98 | `LabUser` | **RETAIN** | `if isinstance(user, LabUser) and user.role != "master_admin":` |
| `backend/app/security/dependencies.py` | 99 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == user.lab_id, Lab.is_active).first()` |
| `backend/app/security/dependencies.py` | 110 | `lab_id` | **RETAIN** | `_lab_id_var.set(user.lab_id)` |
| `backend/app/security/dependencies.py` | 127 | `LabUser` | **RETAIN** | `def checker(current_user: LabUser = Depends(get_current_user)) -> LabUser:` |
| `backend/app/security/dependencies.py` | 127 | `LabUser` | **RETAIN** | `def checker(current_user: LabUser = Depends(get_current_user)) -> LabUser:` |
| `backend/app/security/dependencies.py` | 139 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/security/dependencies.py` | 142 | `lab_id` | **RETAIN** | `lab = db.query(Lab).filter(Lab.id == current_user.lab_id, Lab.is_active).first()` |
| `backend/app/security/dependencies.py` | 155 | `LabUser` | **RETAIN** | `) -> LabUser \| ServiceAccount:` |
| `backend/app/security/rbac.py` | 92 | `lab_id` | **RETAIN** | `if getattr(current_user, "lab_id", None) != resource_lab_id:` |
| `backend/app/security/rbac.py` | 103 | `lab_id` | **RETAIN** | `def require_feature_for_lab(feature: str, lab_id: int, db) -> None:` |
| `backend/app/security/rbac.py` | 106 | `lab_id` | **RETAIN** | `require_feature(feature, lab_id, db)` |
| `backend/app/security/rbac.py` | 109 | `lab_id` | **RETAIN** | `def assert_lab_within_limit(limit_field: str, current_count: int, lab_id: int, db) -> None:` |
| `backend/app/security/rbac.py` | 117 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/security/rbac.py` | 117 | `lab_id` | **RETAIN** | `LabSubscription.lab_id == lab_id,` |
| `backend/app/security/session.py` | 12 | `lab_id` | **RETAIN** | `- lab_id change` |
| `backend/app/security/session.py` | 19 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/security/session.py` | 41 | `LabUser` | **RETAIN** | `user: LabUser,` |
| `backend/app/security/session.py` | 82 | `LabUser` | **RETAIN** | `def warm_perm_version(user: LabUser) -> None:` |
| `backend/app/services/audit_service.py` | 191 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/audit_service.py` | 206 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/audit_service.py` | 206 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/authorization_service.py` | 407 | `lab_id` | **RETAIN** | `"lab_id": getattr(user, "lab_id", None),` |
| `backend/app/services/authorization_service.py` | 407 | `lab_id` | **RETAIN** | `"lab_id": getattr(user, "lab_id", None),` |
| `backend/app/services/care_continuum_service.py` | 105 | `lab_id` | **RETAIN** | `def _apply_lab_filter(query, model, lab_id: int \| None):` |
| `backend/app/services/care_continuum_service.py` | 106 | `lab_id` | **RETAIN** | `if lab_id is not None and hasattr(model, "lab_id"):` |
| `backend/app/services/care_continuum_service.py` | 106 | `lab_id` | **RETAIN** | `if lab_id is not None and hasattr(model, "lab_id"):` |
| `backend/app/services/care_continuum_service.py` | 107 | `lab_id` | **RETAIN** | `return query.filter(model.lab_id == lab_id)` |
| `backend/app/services/care_continuum_service.py` | 107 | `lab_id` | **RETAIN** | `return query.filter(model.lab_id == lab_id)` |
| `backend/app/services/care_continuum_service.py` | 117 | `lab_id` | **RETAIN** | `db: Session, data: dict, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 135 | `lab_id` | **RETAIN** | `practitioner_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 145 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, PrimaryCareEncounter, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 158 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 164 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, FamilyMedicineRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 177 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 183 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, CommunityClinicRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 196 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 202 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, HealthAssessment, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 215 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 221 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, PreventiveCareRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 240 | `lab_id` | **RETAIN** | `def accept_referral(db: Session, referral_id: str, lab_id: int \| None = None) -> dict \| None:` |
| `backend/app/services/care_continuum_service.py` | 284 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 300 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, ReferralRequest, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 437 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 443 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, CareJourney, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 456 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 462 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, FollowUpPlan, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 475 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 481 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, CareCoordination, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 510 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 516 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, HomeCarePlan, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 529 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 535 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, CommunityCareRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 556 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 565 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, ChronicDiseaseRegistry, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 572 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 580 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, ChronicDiseaseRegistry, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 593 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 599 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, DiseaseManagementPlan, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 612 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 618 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, RiskStratification, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 651 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 657 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, PregnancyRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 758 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 764 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, VaccinationRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 777 | `lab_id` | **RETAIN** | `db: Session, patient_id: str \| None = None, lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 783 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, ImmunizationSchedule, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 787 | `lab_id` | **RETAIN** | `def get_missed_vaccinations(db: Session, lab_id: int \| None = None) -> dict:` |
| `backend/app/services/care_continuum_service.py` | 793 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, ImmunizationSchedule, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 809 | `lab_id` | **RETAIN** | `def get_immunization_coverage(db: Session, lab_id: int \| None = None) -> dict:` |
| `backend/app/services/care_continuum_service.py` | 811 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, VaccinationRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 823 | `lab_id` | **RETAIN** | `q_pat = _apply_lab_filter(unique_patients, VaccinationRecord, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 855 | `lab_id` | **RETAIN** | `db: Session, lab_id: int \| None = None, skip: int = 0, limit: int = 50,` |
| `backend/app/services/care_continuum_service.py` | 858 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, HealthProgram, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 879 | `lab_id` | **RETAIN** | `db: Session, lab_id: int \| None = None, skip: int = 0, limit: int = 50,` |
| `backend/app/services/care_continuum_service.py` | 882 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, ScreeningCampaign, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 936 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/care_continuum_service.py` | 947 | `lab_id` | **RETAIN** | `q = _apply_lab_filter(q, PatientTask, lab_id)` |
| `backend/app/services/care_continuum_service.py` | 972 | `lab_id` | **RETAIN** | `def detect_care_gaps(db: Session, patient_id: str, lab_id: int \| None = None) -> dict:` |
| `backend/app/services/claims_service.py` | 3 | `lab_id` | **RETAIN** | `All queries filter by lab_id to enforce the multi-tenant security invariant:` |
| `backend/app/services/claims_service.py` | 4 | `lab_id` | **RETAIN** | `"All patient data queries MUST filter by lab_id = current_user.lab_id"` |
| `backend/app/services/claims_service.py` | 4 | `lab_id` | **RETAIN** | `"All patient data queries MUST filter by lab_id = current_user.lab_id"` |
| `backend/app/services/claims_service.py` | 34 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/claims_service.py` | 53 | `lab_id` | **RETAIN** | `Claim.lab_id == lab_id,` |
| `backend/app/services/claims_service.py` | 53 | `lab_id` | **RETAIN** | `Claim.lab_id == lab_id,` |
| `backend/app/services/claims_service.py` | 68 | `lab_id` | **RETAIN** | `Patient.lab_id == lab_id,` |
| `backend/app/services/claims_service.py` | 68 | `lab_id` | **RETAIN** | `Patient.lab_id == lab_id,` |
| `backend/app/services/claims_service.py` | 73 | `lab_id` | **RETAIN** | `raise ValueError(f"Patient {patient_id} not found for lab {lab_id}")` |
| `backend/app/services/claims_service.py` | 80 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/claims_service.py` | 80 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/claims_service.py` | 106 | `lab_id` | **RETAIN** | `"[CLAIMS] Created claim_id=%d lab_id=%d patient_id=%d total=%s",` |
| `backend/app/services/claims_service.py` | 108 | `lab_id` | **RETAIN** | `lab_id,` |
| `backend/app/services/claims_service.py` | 118 | `lab_id` | **RETAIN** | `def validate_claim(db: Session, claim_id: int, lab_id: int) -> Claim:` |
| `backend/app/services/claims_service.py` | 127 | `lab_id` | **RETAIN** | `claim = _get_claim_or_raise(db, claim_id, lab_id)` |
| `backend/app/services/claims_service.py` | 149 | `lab_id` | **RETAIN** | `logger.info("[CLAIMS] Validated claim_id=%d lab_id=%d", claim_id, lab_id)` |
| `backend/app/services/claims_service.py` | 149 | `lab_id` | **RETAIN** | `logger.info("[CLAIMS] Validated claim_id=%d lab_id=%d", claim_id, lab_id)` |
| `backend/app/services/claims_service.py` | 156 | `lab_id` | **RETAIN** | `def submit_claim(db: Session, claim_id: int, lab_id: int) -> Claim:` |
| `backend/app/services/claims_service.py` | 162 | `lab_id` | **RETAIN** | `claim = _get_claim_or_raise(db, claim_id, lab_id)` |
| `backend/app/services/claims_service.py` | 190 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/services/claims_service.py` | 190 | `lab_id` | **RETAIN** | `"lab_id": lab_id,` |
| `backend/app/services/claims_service.py` | 204 | `lab_id` | **RETAIN** | `"[CLAIMS] Submitted claim_id=%d lab_id=%d total=%s", claim_id, lab_id, claim.total_amount,` |
| `backend/app/services/claims_service.py` | 204 | `lab_id` | **RETAIN** | `"[CLAIMS] Submitted claim_id=%d lab_id=%d total=%s", claim_id, lab_id, claim.total_amount,` |
| `backend/app/services/claims_service.py` | 212 | `lab_id` | **RETAIN** | `def get_claim(db: Session, claim_id: int, lab_id: int) -> Claim:` |
| `backend/app/services/claims_service.py` | 213 | `lab_id` | **RETAIN** | `"""Retrieve a claim by ID, enforcing lab_id ownership.` |
| `backend/app/services/claims_service.py` | 216 | `lab_id` | **RETAIN** | `return _get_claim_or_raise(db, claim_id, lab_id)` |
| `backend/app/services/claims_service.py` | 222 | `lab_id` | **RETAIN** | `def _get_claim_or_raise(db: Session, claim_id: int, lab_id: int) -> Claim:` |
| `backend/app/services/claims_service.py` | 223 | `lab_id` | **RETAIN** | `"""Load claim filtered by lab_id — enforces multi-tenant isolation."""` |
| `backend/app/services/claims_service.py` | 228 | `lab_id` | **RETAIN** | `Claim.lab_id == lab_id,` |
| `backend/app/services/claims_service.py` | 228 | `lab_id` | **RETAIN** | `Claim.lab_id == lab_id,` |
| `backend/app/services/claims_service.py` | 233 | `lab_id` | **RETAIN** | `raise ValueError(f"Claim {claim_id} not found for lab {lab_id}")` |
| `backend/app/services/clinical_scope_bridge_service.py` | 38 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id: int,` |
| `backend/app/services/clinical_scope_bridge_service.py` | 42 | `legacy_lab_id` | **ADAPTER** | `if legacy_lab_id <= 0 or facility_resource_id <= 0:` |
| `backend/app/services/clinical_scope_bridge_service.py` | 45 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/services/clinical_scope_bridge_service.py` | 45 | `legacy_lab_id` | **ADAPTER** | `legacy_lab_id=legacy_lab_id,` |
| `backend/app/services/clinical_scope_bridge_service.py` | 86 | `legacy_lab_id` | **ADAPTER** | `async def resolve_active_binding(self, legacy_lab_id: int) -> ClinicalLabFacilityBinding:` |
| `backend/app/services/clinical_scope_bridge_service.py` | 93 | `legacy_lab_id` | **ADAPTER** | `if legacy_lab_id <= 0:` |
| `backend/app/services/clinical_scope_bridge_service.py` | 100 | `legacy_lab_id` | **ADAPTER** | `ClinicalLabFacilityBinding.legacy_lab_id == legacy_lab_id,` |
| `backend/app/services/clinical_scope_bridge_service.py` | 100 | `legacy_lab_id` | **ADAPTER** | `ClinicalLabFacilityBinding.legacy_lab_id == legacy_lab_id,` |
| `backend/app/services/critical_alerts.py` | 96 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/critical_alerts.py` | 107 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/services/critical_alerts.py` | 107 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/services/critical_alerts.py` | 145 | `lab_id` | **RETAIN** | `def alert_statistics(db: Session, lab_id: int) -> dict:` |
| `backend/app/services/critical_alerts.py` | 156 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/services/critical_alerts.py` | 156 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/services/critical_alerts.py` | 165 | `lab_id` | **RETAIN** | `"top_critical_tests": _top_critical_tests(db, lab_id, week_ago),` |
| `backend/app/services/critical_alerts.py` | 169 | `lab_id` | **RETAIN** | `def _top_critical_tests(db: Session, lab_id: int, since: datetime) -> list:` |
| `backend/app/services/critical_alerts.py` | 178 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/services/critical_alerts.py` | 178 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/services/data_platform_service.py` | 251 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/data_platform_service.py` | 263 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/data_platform_service.py` | 263 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/data_platform_service.py` | 366 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/data_platform_service.py` | 380 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/data_platform_service.py` | 380 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/data_platform_service.py` | 451 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/data_platform_service.py` | 463 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/data_platform_service.py` | 463 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/data_platform_service.py` | 571 | `lab_id` | **RETAIN** | `lab_id: int \| None = None,` |
| `backend/app/services/data_platform_service.py` | 580 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/data_platform_service.py` | 580 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/ehr_service.py` | 32 | `lab_id` | **RETAIN** | `db: Session, patient_id: str, lab_id: int,` |
| `backend/app/services/ehr_service.py` | 38 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == lab_id,` |
| `backend/app/services/ehr_service.py` | 38 | `lab_id` | **RETAIN** | `NationalPatient.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 40 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/hospital_service.py` | 45 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 45 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 51 | `lab_id` | **RETAIN** | `hospital = HospitalMaster(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/services/hospital_service.py` | 51 | `lab_id` | **RETAIN** | `hospital = HospitalMaster(lab_id=lab_id, created_by=user_id, **data)` |
| `backend/app/services/hospital_service.py` | 54 | `lab_id` | **RETAIN** | `log_action(db, "hospital.create", hospital.id, lab_id, user_id, data)` |
| `backend/app/services/hospital_service.py` | 61 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/hospital_service.py` | 67 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 67 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 76 | `lab_id` | **RETAIN** | `log_action(db, "hospital.update", hospital_id, lab_id, user_id, data)` |
| `backend/app/services/hospital_service.py` | 81 | `lab_id` | **RETAIN** | `db: Session, hospital_id: int, lab_id: int, user_id: int,` |
| `backend/app/services/hospital_service.py` | 85 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 85 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 93 | `lab_id` | **RETAIN** | `log_action(db, "hospital.deactivate", hospital_id, lab_id, user_id)` |
| `backend/app/services/hospital_service.py` | 96 | `lab_id` | **RETAIN** | `def get_hospital(db: Session, hospital_id: int, lab_id: int) -> HospitalMaster:` |
| `backend/app/services/hospital_service.py` | 99 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 99 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 108 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, skip: int = 0, limit: int = 50,` |
| `backend/app/services/hospital_service.py` | 111 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 111 | `lab_id` | **RETAIN** | `HospitalMaster.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 118 | `lab_id` | **RETAIN** | `def _get_entity(db: Session, model, entity_id: int, lab_id: int, parent_filter=None):` |
| `backend/app/services/hospital_service.py` | 119 | `lab_id` | **RETAIN** | `q = db.query(model).filter(model.id == entity_id, model.lab_id == lab_id, not model.is_deleted)` |
| `backend/app/services/hospital_service.py` | 119 | `lab_id` | **RETAIN** | `q = db.query(model).filter(model.id == entity_id, model.lab_id == lab_id, not model.is_deleted)` |
| `backend/app/services/hospital_service.py` | 130 | `lab_id` | **RETAIN** | `def create_campus(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> Campus:` |
| `backend/app/services/hospital_service.py` | 131 | `lab_id` | **RETAIN** | `HospitalService.get_hospital(db, hospital_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 132 | `lab_id` | **RETAIN** | `campus = Campus(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 132 | `lab_id` | **RETAIN** | `campus = Campus(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 135 | `lab_id` | **RETAIN** | `log_action(db, "campus.create", campus.id, lab_id, user_id, data)` |
| `backend/app/services/hospital_service.py` | 139 | `lab_id` | **RETAIN** | `def list_campuses(db: Session, lab_id: int, hospital_id: int) -> list[Campus]:` |
| `backend/app/services/hospital_service.py` | 141 | `lab_id` | **RETAIN** | `Campus.hospital_id == hospital_id, Campus.lab_id == lab_id, ~Campus.is_deleted,` |
| `backend/app/services/hospital_service.py` | 141 | `lab_id` | **RETAIN** | `Campus.hospital_id == hospital_id, Campus.lab_id == lab_id, ~Campus.is_deleted,` |
| `backend/app/services/hospital_service.py` | 147 | `lab_id` | **RETAIN** | `def create_building(db: Session, lab_id: int, user_id: int, campus_id: int, data: dict) -> Building:` |
| `backend/app/services/hospital_service.py` | 148 | `lab_id` | **RETAIN** | `HospitalService._get_entity(db, Campus, campus_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 149 | `lab_id` | **RETAIN** | `building = Building(lab_id=lab_id, created_by=user_id, campus_id=campus_id, **data)` |
| `backend/app/services/hospital_service.py` | 149 | `lab_id` | **RETAIN** | `building = Building(lab_id=lab_id, created_by=user_id, campus_id=campus_id, **data)` |
| `backend/app/services/hospital_service.py` | 155 | `lab_id` | **RETAIN** | `def list_buildings(db: Session, lab_id: int, campus_id: int) -> list[Building]:` |
| `backend/app/services/hospital_service.py` | 157 | `lab_id` | **RETAIN** | `Building.campus_id == campus_id, Building.lab_id == lab_id, ~Building.is_deleted,` |
| `backend/app/services/hospital_service.py` | 157 | `lab_id` | **RETAIN** | `Building.campus_id == campus_id, Building.lab_id == lab_id, ~Building.is_deleted,` |
| `backend/app/services/hospital_service.py` | 163 | `lab_id` | **RETAIN** | `def create_floor(db: Session, lab_id: int, user_id: int, building_id: int, data: dict) -> Floor:` |
| `backend/app/services/hospital_service.py` | 164 | `lab_id` | **RETAIN** | `HospitalService._get_entity(db, Building, building_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 165 | `lab_id` | **RETAIN** | `floor = Floor(lab_id=lab_id, created_by=user_id, building_id=building_id, **data)` |
| `backend/app/services/hospital_service.py` | 165 | `lab_id` | **RETAIN** | `floor = Floor(lab_id=lab_id, created_by=user_id, building_id=building_id, **data)` |
| `backend/app/services/hospital_service.py` | 171 | `lab_id` | **RETAIN** | `def list_floors(db: Session, lab_id: int, building_id: int) -> list[Floor]:` |
| `backend/app/services/hospital_service.py` | 173 | `lab_id` | **RETAIN** | `Floor.building_id == building_id, Floor.lab_id == lab_id, ~Floor.is_deleted,` |
| `backend/app/services/hospital_service.py` | 173 | `lab_id` | **RETAIN** | `Floor.building_id == building_id, Floor.lab_id == lab_id, ~Floor.is_deleted,` |
| `backend/app/services/hospital_service.py` | 179 | `lab_id` | **RETAIN** | `def create_department(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> HospitalDepartment:` |
| `backend/app/services/hospital_service.py` | 180 | `lab_id` | **RETAIN** | `HospitalService.get_hospital(db, hospital_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 182 | `lab_id` | **RETAIN** | `HospitalService._get_entity(db, HospitalDepartment, data["parent_id"], lab_id, HospitalDepartment.hospital_id == hospital_id)` |
| `backend/app/services/hospital_service.py` | 183 | `lab_id` | **RETAIN** | `dept = HospitalDepartment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 183 | `lab_id` | **RETAIN** | `dept = HospitalDepartment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 189 | `lab_id` | **RETAIN** | `def list_departments(db: Session, lab_id: int, hospital_id: int, parent_id: int \| None = None) -> list[HospitalDepartment]:` |
| `backend/app/services/hospital_service.py` | 191 | `lab_id` | **RETAIN** | `HospitalDepartment.hospital_id == hospital_id, HospitalDepartment.lab_id == lab_id, ~HospitalDepartment.is_deleted,` |
| `backend/app/services/hospital_service.py` | 191 | `lab_id` | **RETAIN** | `HospitalDepartment.hospital_id == hospital_id, HospitalDepartment.lab_id == lab_id, ~HospitalDepartment.is_deleted,` |
| `backend/app/services/hospital_service.py` | 200 | `lab_id` | **RETAIN** | `def create_clinic(db: Session, lab_id: int, user_id: int, department_id: int, data: dict) -> Clinic:` |
| `backend/app/services/hospital_service.py` | 201 | `lab_id` | **RETAIN** | `dept = HospitalService._get_entity(db, HospitalDepartment, department_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 203 | `lab_id` | **RETAIN** | `clinic = Clinic(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)` |
| `backend/app/services/hospital_service.py` | 203 | `lab_id` | **RETAIN** | `clinic = Clinic(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)` |
| `backend/app/services/hospital_service.py` | 209 | `lab_id` | **RETAIN** | `def list_clinics(db: Session, lab_id: int, department_id: int \| None = None) -> list[Clinic]:` |
| `backend/app/services/hospital_service.py` | 210 | `lab_id` | **RETAIN** | `q = db.query(Clinic).filter(Clinic.lab_id == lab_id, ~Clinic.is_deleted)` |
| `backend/app/services/hospital_service.py` | 210 | `lab_id` | **RETAIN** | `q = db.query(Clinic).filter(Clinic.lab_id == lab_id, ~Clinic.is_deleted)` |
| `backend/app/services/hospital_service.py` | 218 | `lab_id` | **RETAIN** | `def create_room(db: Session, lab_id: int, user_id: int, department_id: int, data: dict) -> Room:` |
| `backend/app/services/hospital_service.py` | 219 | `lab_id` | **RETAIN** | `HospitalService._get_entity(db, HospitalDepartment, department_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 220 | `lab_id` | **RETAIN** | `room = Room(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)` |
| `backend/app/services/hospital_service.py` | 220 | `lab_id` | **RETAIN** | `room = Room(lab_id=lab_id, created_by=user_id, department_id=department_id, **data)` |
| `backend/app/services/hospital_service.py` | 227 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, department_id: int \| None = None,` |
| `backend/app/services/hospital_service.py` | 230 | `lab_id` | **RETAIN** | `q = db.query(Room).filter(Room.lab_id == lab_id, ~Room.is_deleted)` |
| `backend/app/services/hospital_service.py` | 230 | `lab_id` | **RETAIN** | `q = db.query(Room).filter(Room.lab_id == lab_id, ~Room.is_deleted)` |
| `backend/app/services/hospital_service.py` | 240 | `lab_id` | **RETAIN** | `def create_bed(db: Session, lab_id: int, user_id: int, room_id: int, data: dict) -> Bed:` |
| `backend/app/services/hospital_service.py` | 241 | `lab_id` | **RETAIN** | `HospitalService._get_entity(db, Room, room_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 242 | `lab_id` | **RETAIN** | `bed = Bed(lab_id=lab_id, created_by=user_id, room_id=room_id, **data)` |
| `backend/app/services/hospital_service.py` | 242 | `lab_id` | **RETAIN** | `bed = Bed(lab_id=lab_id, created_by=user_id, room_id=room_id, **data)` |
| `backend/app/services/hospital_service.py` | 249 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, room_id: int \| None = None,` |
| `backend/app/services/hospital_service.py` | 252 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/services/hospital_service.py` | 252 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/services/hospital_service.py` | 263 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, bed_id: int, patient_id: int,` |
| `backend/app/services/hospital_service.py` | 266 | `lab_id` | **RETAIN** | `bed = HospitalService._get_entity(db, Bed, bed_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 268 | `lab_id` | **RETAIN** | `Patient.id == patient_id, Patient.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 268 | `lab_id` | **RETAIN** | `Patient.id == patient_id, Patient.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 277 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/services/hospital_service.py` | 277 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/services/hospital_service.py` | 284 | `lab_id` | **RETAIN** | `log_action(db, "bed.assign", bed_id, lab_id, user_id, {` |
| `backend/app/services/hospital_service.py` | 291 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, bed_id: int,` |
| `backend/app/services/hospital_service.py` | 294 | `lab_id` | **RETAIN** | `bed = HospitalService._get_entity(db, Bed, bed_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 308 | `lab_id` | **RETAIN** | `log_action(db, "bed.discharge", bed_id, lab_id, user_id, {` |
| `backend/app/services/hospital_service.py` | 315 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int,` |
| `backend/app/services/hospital_service.py` | 319 | `lab_id` | **RETAIN** | `source = HospitalService.discharge_bed(db, lab_id, user_id, from_bed_id, reason)` |
| `backend/app/services/hospital_service.py` | 320 | `lab_id` | **RETAIN** | `target = HospitalService._get_entity(db, Bed, to_bed_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 327 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/services/hospital_service.py` | 327 | `lab_id` | **RETAIN** | `lab_id=lab_id, created_by=user_id,` |
| `backend/app/services/hospital_service.py` | 337 | `lab_id` | **RETAIN** | `def bed_occupancy_stats(db: Session, lab_id: int, hospital_id: int \| None = None) -> dict[str, Any]:` |
| `backend/app/services/hospital_service.py` | 338 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/services/hospital_service.py` | 338 | `lab_id` | **RETAIN** | `q = db.query(Bed).filter(Bed.lab_id == lab_id, ~Bed.is_deleted)` |
| `backend/app/services/hospital_service.py` | 361 | `lab_id` | **RETAIN** | `def create_unit(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> Unit:` |
| `backend/app/services/hospital_service.py` | 362 | `lab_id` | **RETAIN** | `HospitalService.get_hospital(db, hospital_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 363 | `lab_id` | **RETAIN** | `unit = Unit(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 363 | `lab_id` | **RETAIN** | `unit = Unit(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 369 | `lab_id` | **RETAIN** | `def list_units(db: Session, lab_id: int, hospital_id: int) -> list[Unit]:` |
| `backend/app/services/hospital_service.py` | 371 | `lab_id` | **RETAIN** | `Unit.hospital_id == hospital_id, Unit.lab_id == lab_id, ~Unit.is_deleted,` |
| `backend/app/services/hospital_service.py` | 371 | `lab_id` | **RETAIN** | `Unit.hospital_id == hospital_id, Unit.lab_id == lab_id, ~Unit.is_deleted,` |
| `backend/app/services/hospital_service.py` | 377 | `lab_id` | **RETAIN** | `def create_ot(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> OperationTheater:` |
| `backend/app/services/hospital_service.py` | 378 | `lab_id` | **RETAIN** | `HospitalService.get_hospital(db, hospital_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 379 | `lab_id` | **RETAIN** | `ot = OperationTheater(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 379 | `lab_id` | **RETAIN** | `ot = OperationTheater(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 385 | `lab_id` | **RETAIN** | `def list_operation_theaters(db: Session, lab_id: int, hospital_id: int) -> list[OperationTheater]:` |
| `backend/app/services/hospital_service.py` | 388 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 388 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 395 | `lab_id` | **RETAIN** | `def create_equipment(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> MedicalEquipment:` |
| `backend/app/services/hospital_service.py` | 396 | `lab_id` | **RETAIN** | `HospitalService.get_hospital(db, hospital_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 397 | `lab_id` | **RETAIN** | `equip = MedicalEquipment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 397 | `lab_id` | **RETAIN** | `equip = MedicalEquipment(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 404 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, hospital_id: int,` |
| `backend/app/services/hospital_service.py` | 409 | `lab_id` | **RETAIN** | `MedicalEquipment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 409 | `lab_id` | **RETAIN** | `MedicalEquipment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 421 | `lab_id` | **RETAIN** | `def create_cost_center(db: Session, lab_id: int, user_id: int, hospital_id: int, data: dict) -> CostCenter:` |
| `backend/app/services/hospital_service.py` | 422 | `lab_id` | **RETAIN** | `HospitalService.get_hospital(db, hospital_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 423 | `lab_id` | **RETAIN** | `cc = CostCenter(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 423 | `lab_id` | **RETAIN** | `cc = CostCenter(lab_id=lab_id, created_by=user_id, hospital_id=hospital_id, **data)` |
| `backend/app/services/hospital_service.py` | 429 | `lab_id` | **RETAIN** | `def list_cost_centers(db: Session, lab_id: int, hospital_id: int) -> list[CostCenter]:` |
| `backend/app/services/hospital_service.py` | 432 | `lab_id` | **RETAIN** | `CostCenter.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 432 | `lab_id` | **RETAIN** | `CostCenter.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 439 | `lab_id` | **RETAIN** | `def dashboard(db: Session, lab_id: int, hospital_id: int) -> dict[str, Any]:` |
| `backend/app/services/hospital_service.py` | 440 | `lab_id` | **RETAIN** | `HospitalService.get_hospital(db, hospital_id, lab_id)` |
| `backend/app/services/hospital_service.py` | 443 | `lab_id` | **RETAIN** | `HospitalDepartment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 443 | `lab_id` | **RETAIN** | `HospitalDepartment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 454 | `lab_id` | **RETAIN** | `HospitalDepartment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 454 | `lab_id` | **RETAIN** | `HospitalDepartment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 461 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 461 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 465 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 465 | `lab_id` | **RETAIN** | `Bed.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 471 | `lab_id` | **RETAIN** | `MedicalEquipment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 471 | `lab_id` | **RETAIN** | `MedicalEquipment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 476 | `lab_id` | **RETAIN** | `MedicalEquipment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 476 | `lab_id` | **RETAIN** | `MedicalEquipment.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 482 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 482 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 487 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 487 | `lab_id` | **RETAIN** | `OperationTheater.lab_id == lab_id,` |
| `backend/app/services/hospital_service.py` | 505 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, hospital_id: int \| None = None,` |
| `backend/app/services/hospital_service.py` | 508 | `lab_id` | **RETAIN** | `q = db.query(Appointment).filter(Appointment.lab_id == lab_id)` |
| `backend/app/services/hospital_service.py` | 508 | `lab_id` | **RETAIN** | `q = db.query(Appointment).filter(Appointment.lab_id == lab_id)` |
| `backend/app/services/hospital_service.py` | 515 | `lab_id` | **RETAIN** | `db: Session, lab_id: int, user_id: int, data: dict[str, Any],` |
| `backend/app/services/hospital_service.py` | 517 | `lab_id` | **RETAIN** | `apt = Appointment(lab_id=lab_id, **data)` |
| `backend/app/services/hospital_service.py` | 517 | `lab_id` | **RETAIN** | `apt = Appointment(lab_id=lab_id, **data)` |
| `backend/app/services/hospital_service.py` | 520 | `lab_id` | **RETAIN** | `log_action(db, "appointment.create", apt.id, lab_id, user_id, data)` |
| `backend/app/services/identity_matching.py` | 265 | `lab_id` | **RETAIN** | `The caller is responsible for scoping by ``lab_id`` if multi-tenant` |
| `backend/app/services/identity_matching.py` | 275 | `lab_id` | **RETAIN** | `lab_id = _get(citizen_data, "lab_id")` |
| `backend/app/services/identity_matching.py` | 275 | `lab_id` | **RETAIN** | `lab_id = _get(citizen_data, "lab_id")` |
| `backend/app/services/identity_matching.py` | 278 | `lab_id` | **RETAIN** | `if lab_id is not None:` |
| `backend/app/services/identity_matching.py` | 279 | `lab_id` | **RETAIN** | `base_query = base_query.filter(Patient.lab_id == lab_id)` |
| `backend/app/services/identity_matching.py` | 279 | `lab_id` | **RETAIN** | `base_query = base_query.filter(Patient.lab_id == lab_id)` |
| `backend/app/services/mpi/api.py` | 16 | `LabUser` | **RETAIN** | `from ...models.lab_user import LabUser` |
| `backend/app/services/mpi/api.py` | 45 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(get_current_user),` |
| `backend/app/services/mpi/api.py` | 50 | `lab_id` | **RETAIN** | `Idempotent: re-calling for the same (lab_id, patient_id) returns the` |
| `backend/app/services/mpi/api.py` | 55 | `lab_id` | **RETAIN** | `require_own_lab(current_user, data.lab_id)` |
| `backend/app/services/mpi/api.py` | 60 | `lab_id` | **RETAIN** | `.filter(Patient.id == data.patient_id, Patient.lab_id == data.lab_id)` |
| `backend/app/services/mpi/api.py` | 60 | `lab_id` | **RETAIN** | `.filter(Patient.id == data.patient_id, Patient.lab_id == data.lab_id)` |
| `backend/app/services/mpi/api.py` | 75 | `lab_id` | **RETAIN** | `lab_id=data.lab_id,` |
| `backend/app/services/mpi/api.py` | 75 | `lab_id` | **RETAIN** | `lab_id=data.lab_id,` |
| `backend/app/services/mpi/api.py` | 104 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(` |
| `backend/app/services/mpi/api.py` | 145 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(` |
| `backend/app/services/mpi/api.py` | 186 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(` |
| `backend/app/services/mpi/api.py` | 213 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/services/mpi/api.py` | 213 | `lab_id` | **RETAIN** | `lab_id=claim.lab_id,` |
| `backend/app/services/mpi/api.py` | 230 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(` |
| `backend/app/services/mpi/api.py` | 263 | `lab_id` | **RETAIN** | `.filter(Patient.id == claim.local_patient_id, Patient.lab_id == claim.lab_id)` |
| `backend/app/services/mpi/api.py` | 263 | `lab_id` | **RETAIN** | `.filter(Patient.id == claim.local_patient_id, Patient.lab_id == claim.lab_id)` |
| `backend/app/services/mpi/api.py` | 273 | `lab_id` | **RETAIN** | `# Delete the old claim first (uniqueness constraint on lab_id+local_patient_id)` |
| `backend/app/services/mpi/api.py` | 280 | `lab_id` | **RETAIN** | `lab_id=patient.lab_id,` |
| `backend/app/services/mpi/api.py` | 280 | `lab_id` | **RETAIN** | `lab_id=patient.lab_id,` |
| `backend/app/services/mpi/api.py` | 316 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_consent("read:citizen")),` |
| `backend/app/services/mpi/canonical_service.py` | 34 | `lab_id` | **RETAIN** | `lab_id=patient_or_citizen.lab_id,` |
| `backend/app/services/mpi/canonical_service.py` | 34 | `lab_id` | **RETAIN** | `lab_id=patient_or_citizen.lab_id,` |
| `backend/app/services/mpi/canonical_service.py` | 123 | `lab_id` | **RETAIN** | `source.lab_id = None` |
| `backend/app/services/mpi/models.py` | 7 | `lab_id` | **RETAIN** | `- IdentityClaim — bridge row from (lab_id, patient_id) → citizen_id` |
| `backend/app/services/mpi/models.py` | 12 | `lab_id` | **RETAIN** | `- Never scoped by lab_id.` |
| `backend/app/services/mpi/models.py` | 116 | `lab_id` | **RETAIN** | `"""Bridge row: LIMS patient (lab_id, patient_id) → canonical citizen.` |
| `backend/app/services/mpi/models.py` | 118 | `lab_id` | **RETAIN** | `Exactly one claim per (lab_id, local_patient_id). Created by` |
| `backend/app/services/mpi/models.py` | 124 | `lab_id` | **RETAIN** | `UniqueConstraint("lab_id", "local_patient_id", name="uq_identity_claims_lab_patient"),` |
| `backend/app/services/mpi/models.py` | 126 | `lab_id` | **RETAIN** | `Index("ix_identity_claims_lab_patient", "lab_id", "local_patient_id"),` |
| `backend/app/services/mpi/models.py` | 132 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)` |
| `backend/app/services/mpi/resolver.py` | 18 | `lab_id` | **RETAIN** | `The IdentityClaim UNIQUE(lab_id, local_patient_id) constraint makes` |
| `backend/app/services/mpi/resolver.py` | 166 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/mpi/resolver.py` | 180 | `lab_id` | **RETAIN** | `Idempotent: re-calling with the same (lab_id, local_patient_id)` |
| `backend/app/services/mpi/resolver.py` | 185 | `lab_id` | **RETAIN** | `db.query(IdentityClaim).filter_by(lab_id=lab_id, local_patient_id=local_patient_id).first()` |
| `backend/app/services/mpi/resolver.py` | 185 | `lab_id` | **RETAIN** | `db.query(IdentityClaim).filter_by(lab_id=lab_id, local_patient_id=local_patient_id).first()` |
| `backend/app/services/mpi/resolver.py` | 331 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/mpi/resolver.py` | 331 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/mpi/schemas.py` | 15 | `lab_id` | **RETAIN** | `lab_id: int = Field(..., ge=1)` |
| `backend/app/services/mpi/schemas.py` | 75 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/services/order_service.py` | 297 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/services/order_service.py` | 297 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/services/order_service.py` | 313 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/services/order_service.py` | 313 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/services/order_service.py` | 320 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/order_service.py` | 333 | `lab_id` | **RETAIN** | `cache_key = f"idempotency:order:{lab_id}:{idempotency_key}"` |
| `backend/app/services/order_service.py` | 339 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/order_service.py` | 339 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/order_service.py` | 345 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/services/order_service.py` | 348 | `LabUser` | **RETAIN** | `db.query(LabUser)` |
| `backend/app/services/order_service.py` | 350 | `LabUser` | **RETAIN** | `LabUser.id == doctor_user_id,` |
| `backend/app/services/order_service.py` | 351 | `LabUser` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/services/order_service.py` | 351 | `lab_id` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/services/order_service.py` | 351 | `lab_id` | **RETAIN** | `LabUser.lab_id == lab_id,` |
| `backend/app/services/order_service.py` | 352 | `LabUser` | **RETAIN** | `LabUser.role == "doctor",` |
| `backend/app/services/order_service.py` | 362 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/order_service.py` | 362 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/order_service.py` | 435 | `lab_id` | **RETAIN** | `cache_key = f"idempotency:order:{lab_id}:{idempotency_key}"` |
| `backend/app/services/order_service.py` | 447 | `lab_id` | **RETAIN** | `db: Session, order_id: int, lab_id: int, user_role: str, user_id: int,` |
| `backend/app/services/order_service.py` | 451 | `lab_id` | **RETAIN** | `_base_order_query(db, user_role, user_id, lab_id).filter(LabOrder.id == order_id).first()` |
| `backend/app/services/order_service.py` | 460 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/order_service.py` | 468 | `lab_id` | **RETAIN** | `query = _base_order_query(db, user_role, user_id, lab_id)` |
| `backend/app/services/order_service.py` | 491 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/order_service.py` | 504 | `lab_id` | **RETAIN** | `_base_order_query(db, user_role, user_id, lab_id).filter(LabOrder.id == order_id).first()` |
| `backend/app/services/order_service.py` | 555 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/services/order_service.py` | 555 | `lab_id` | **RETAIN** | `"lab_id": order.lab_id,` |
| `backend/app/services/order_service.py` | 566 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/order_service.py` | 573 | `lab_id` | **RETAIN** | `_base_order_query(db, user_role, user_id, lab_id).filter(LabOrder.id == order_id).first()` |
| `backend/app/services/order_service.py` | 764 | `lab_id` | **RETAIN** | `def get_patient_history_by_id(db: Session, patient_id: int, lab_id: int) -> dict \| None:` |
| `backend/app/services/order_service.py` | 766 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/order_service.py` | 766 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/order_service.py` | 772 | `lab_id` | **RETAIN** | `.filter(LabOrder.patient_id == patient.id, LabOrder.lab_id == lab_id)` |
| `backend/app/services/order_service.py` | 772 | `lab_id` | **RETAIN** | `.filter(LabOrder.patient_id == patient.id, LabOrder.lab_id == lab_id)` |
| `backend/app/services/order_service.py` | 875 | `lab_id` | **RETAIN** | `def _base_order_query(db: Session, user_role: str, user_id: int, lab_id: int):` |
| `backend/app/services/order_service.py` | 884 | `lab_id` | **RETAIN** | `return base.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/services/order_service.py` | 884 | `lab_id` | **RETAIN** | `return base.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/services/outbox_service.py` | 22 | `lab_id` | **RETAIN** | `payload={"order_id": order.id, "lab_id": lab_id})` |
| `backend/app/services/outbox_service.py` | 22 | `lab_id` | **RETAIN** | `payload={"order_id": order.id, "lab_id": lab_id})` |
| `backend/app/services/patient_card.py` | 4 | `lab_id` | **RETAIN** | `short-lived, HMAC-signed token that encodes (patient_id, lab_id, exp). Lab` |
| `backend/app/services/patient_card.py` | 34 | `lab_id` | **RETAIN** | `# Body = base64url("<patient_id>.<lab_id>.<exp_unix>")` |
| `backend/app/services/patient_card.py` | 59 | `lab_id` | **RETAIN** | `def issue_card_token(patient_id: int, lab_id: int, ttl_seconds: int = _DEFAULT_TTL_SECONDS) -> str:` |
| `backend/app/services/patient_card.py` | 62 | `lab_id` | **RETAIN** | `body = f"{patient_id}.{lab_id}.{exp}".encode("ascii")` |
| `backend/app/services/patient_card.py` | 73 | `lab_id` | **RETAIN** | `"""Verify a card token and return ``(patient_id, lab_id)``.` |
| `backend/app/services/patient_card.py` | 76 | `lab_id` | **RETAIN** | `returned ``lab_id`` matches the scanning user's lab — this function` |
| `backend/app/services/patient_card.py` | 95 | `lab_id` | **RETAIN** | `lab_id = int(lab_s)` |
| `backend/app/services/patient_card.py` | 103 | `lab_id` | **RETAIN** | `if patient_id <= 0 or lab_id <= 0:` |
| `backend/app/services/patient_card.py` | 106 | `lab_id` | **RETAIN** | `return patient_id, lab_id` |
| `backend/app/services/patient_card.py` | 136 | `lab_id` | **RETAIN** | `"lab_id": patient.lab_id,` |
| `backend/app/services/patient_card.py` | 136 | `lab_id` | **RETAIN** | `"lab_id": patient.lab_id,` |
| `backend/app/services/patient_card.py` | 152 | `lab_id` | **RETAIN** | `filtered by the current user's lab_id. We re-assert it on every nested` |
| `backend/app/services/patient_card.py` | 159 | `lab_id` | **RETAIN** | `LabOrder.lab_id == patient.lab_id,` |
| `backend/app/services/patient_card.py` | 159 | `lab_id` | **RETAIN** | `LabOrder.lab_id == patient.lab_id,` |
| `backend/app/services/patient_card.py` | 234 | `lab_id` | **RETAIN** | `def lookup_patient_for_lab(db: Session, *, patient_id: int, lab_id: int) -> Patient \| None:` |
| `backend/app/services/patient_card.py` | 236 | `lab_id` | **RETAIN** | `return db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_card.py` | 236 | `lab_id` | **RETAIN** | `return db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 70 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/patient_service.py` | 78 | `lab_id` | **RETAIN** | `query = db.query(Patient).filter(Patient.lab_id == lab_id)` |
| `backend/app/services/patient_service.py` | 78 | `lab_id` | **RETAIN** | `query = db.query(Patient).filter(Patient.lab_id == lab_id)` |
| `backend/app/services/patient_service.py` | 95 | `lab_id` | **RETAIN** | `def get_patient_by_id(db: Session, patient_id: int, lab_id: int) -> dict \| None:` |
| `backend/app/services/patient_service.py` | 97 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 97 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 105 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/patient_service.py` | 127 | `lab_id` | **RETAIN** | `db, lab_id, full_name, phone, birth_date or "", nid_hash,` |
| `backend/app/services/patient_service.py` | 135 | `lab_id` | **RETAIN** | `db.query(Patient).filter(Patient.id == guardian_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 135 | `lab_id` | **RETAIN** | `db.query(Patient).filter(Patient.id == guardian_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 143 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/patient_service.py` | 143 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/patient_service.py` | 159 | `lab_id` | **RETAIN** | `db, patient, national_id, family_id, user_id, lab_id,` |
| `backend/app/services/patient_service.py` | 185 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/patient_service.py` | 197 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 197 | `lab_id` | **RETAIN** | `patient = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 237 | `lab_id` | **RETAIN** | `def get_family_members(db: Session, family_id: str, lab_id: int) -> dict:` |
| `backend/app/services/patient_service.py` | 249 | `lab_id` | **RETAIN** | `.filter(Patient.family_id_hash == fid_hash, Patient.lab_id == lab_id)` |
| `backend/app/services/patient_service.py` | 249 | `lab_id` | **RETAIN** | `.filter(Patient.family_id_hash == fid_hash, Patient.lab_id == lab_id)` |
| `backend/app/services/patient_service.py` | 279 | `lab_id` | **RETAIN** | `def get_patient_children(db: Session, patient_id: int, lab_id: int) -> dict:` |
| `backend/app/services/patient_service.py` | 281 | `lab_id` | **RETAIN** | `guardian = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 281 | `lab_id` | **RETAIN** | `guardian = db.query(Patient).filter(Patient.id == patient_id, Patient.lab_id == lab_id).first()` |
| `backend/app/services/patient_service.py` | 287 | `lab_id` | **RETAIN** | `.filter(Patient.guardian_id == patient_id, Patient.lab_id == lab_id)` |
| `backend/app/services/patient_service.py` | 287 | `lab_id` | **RETAIN** | `.filter(Patient.guardian_id == patient_id, Patient.lab_id == lab_id)` |
| `backend/app/services/patient_service.py` | 301 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/patient_service.py` | 324 | `lab_id` | **RETAIN** | `db.query(Patient).filter(Patient.lab_id == lab_id, Patient.phone == phone).limit(10).all()` |
| `backend/app/services/patient_service.py` | 324 | `lab_id` | **RETAIN** | `db.query(Patient).filter(Patient.lab_id == lab_id, Patient.phone == phone).limit(10).all()` |
| `backend/app/services/patient_service.py` | 348 | `lab_id` | **RETAIN** | `.filter(Patient.lab_id == lab_id, Patient.full_name.ilike(f"{name_prefix}%"))` |
| `backend/app/services/patient_service.py` | 348 | `lab_id` | **RETAIN** | `.filter(Patient.lab_id == lab_id, Patient.full_name.ilike(f"{name_prefix}%"))` |
| `backend/app/services/patient_service.py` | 388 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/services/patient_service.py` | 403 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/patient_service.py` | 403 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/services/telegram_bot_commands.py` | 36 | `lab_id` | **RETAIN** | `# Using default lab_id=1 for system admin overview` |
| `backend/app/services/telegram_bot_commands.py` | 38 | `lab_id` | **RETAIN** | `alerts_data = get_critical_alerts(db, lab_id=1, hours=24)` |
| `backend/app/services/telegram_bot_commands.py` | 52 | `lab_id` | **RETAIN** | `stats = alert_statistics(db, lab_id=1)` |
| `backend/app/simulation/engine.py` | 393 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == entity_id)` |
| `backend/app/simulation/engine.py` | 399 | `lab_id` | **RETAIN** | `.filter(Patient.lab_id == entity_id)` |
| `backend/app/simulation/engine.py` | 537 | `lab_id` | **RETAIN** | `lab_id = entity_id if entity_type == "lab" else None` |
| `backend/app/simulation/engine.py` | 544 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/simulation/engine.py` | 548 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 548 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 606 | `lab_id` | **RETAIN** | `lab_id = entity_id if entity_type == "lab" else None` |
| `backend/app/simulation/engine.py` | 612 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/simulation/engine.py` | 616 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 616 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 656 | `lab_id` | **RETAIN** | `lab_id = entity_id if entity_type == "lab" else None` |
| `backend/app/simulation/engine.py` | 662 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/simulation/engine.py` | 666 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 666 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 675 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 675 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 684 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 684 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 747 | `lab_id` | **RETAIN** | `lab_id = entity_id if entity_type == "lab" else None` |
| `backend/app/simulation/engine.py` | 752 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/simulation/engine.py` | 757 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 757 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 816 | `lab_id` | **RETAIN** | `lab_id = entity_id if entity_type == "lab" else None` |
| `backend/app/simulation/engine.py` | 821 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/simulation/engine.py` | 826 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 826 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 874 | `lab_id` | **RETAIN** | `lab_id = entity_id if entity_type == "lab" else None` |
| `backend/app/simulation/engine.py` | 880 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/simulation/engine.py` | 885 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 885 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 895 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 895 | `lab_id` | **RETAIN** | `LabOrder.lab_id == lab_id,` |
| `backend/app/simulation/engine.py` | 904 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/simulation/engine.py` | 904 | `lab_id` | **RETAIN** | `.filter(LabOrder.lab_id == lab_id)` |
| `backend/app/simulation/routes.py` | 8 | `LabUser` | **RETAIN** | `from ..models.lab_user import LabUser` |
| `backend/app/simulation/routes.py` | 134 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:write")),` |
| `backend/app/simulation/routes.py` | 166 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:read")),` |
| `backend/app/simulation/routes.py` | 192 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:write")),` |
| `backend/app/simulation/routes.py` | 229 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:read")),` |
| `backend/app/simulation/routes.py` | 263 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:write")),` |
| `backend/app/simulation/routes.py` | 297 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:read")),` |
| `backend/app/simulation/routes.py` | 322 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:read")),` |
| `backend/app/simulation/routes.py` | 333 | `LabUser` | **RETAIN** | `current_user: LabUser = Depends(require_permission("simulation:read")),` |
| `backend/app/trust/models.py` | 25 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)` |
| `backend/app/trust/models.py` | 73 | `lab_id` | **RETAIN** | `lab_id = Column(Integer, ForeignKey("labs.id"), nullable=True)` |
| `backend/app/trust/routes.py` | 36 | `lab_id` | **RETAIN** | `lab_id: int` |
| `backend/app/trust/routes.py` | 79 | `lab_id` | **RETAIN** | `lab_id=current_user.get("lab_id", 0),` |
| `backend/app/trust/routes.py` | 79 | `lab_id` | **RETAIN** | `lab_id=current_user.get("lab_id", 0),` |
| `backend/app/trust/routes.py` | 88 | `lab_id` | **RETAIN** | `lab_id=record.lab_id,` |
| `backend/app/trust/routes.py` | 88 | `lab_id` | **RETAIN** | `lab_id=record.lab_id,` |
| `backend/app/trust/routes.py` | 112 | `lab_id` | **RETAIN** | `lab_id = current_user.get("lab_id", 0)` |
| `backend/app/trust/routes.py` | 112 | `lab_id` | **RETAIN** | `lab_id = current_user.get("lab_id", 0)` |
| `backend/app/trust/routes.py` | 113 | `lab_id` | **RETAIN** | `granted = service.verify_consent(patient_id, lab_id, purpose_enum, category_enum)` |
| `backend/app/trust/routes.py` | 216 | `lab_id` | **RETAIN** | `lab_id=current_user.get("lab_id", 0),` |
| `backend/app/trust/routes.py` | 216 | `lab_id` | **RETAIN** | `lab_id=current_user.get("lab_id", 0),` |
| `backend/app/trust/routes.py` | 238 | `lab_id` | **RETAIN** | `lab_id=current_user.get("lab_id", 0),` |
| `backend/app/trust/routes.py` | 238 | `lab_id` | **RETAIN** | `lab_id=current_user.get("lab_id", 0),` |
| `backend/app/trust/routes.py` | 287 | `lab_id` | **RETAIN** | `lab_id: int \| None = Query(None),` |
| `backend/app/trust/routes.py` | 292 | `lab_id` | **RETAIN** | `return service.get_compliance_dashboard(lab_id)` |
| `backend/app/trust/services.py` | 41 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/trust/services.py` | 51 | `lab_id` | **RETAIN** | `consent_data = f"{patient_id}:{lab_id}:{purpose_str}:{categories_str}:{int(time.time())}"` |
| `backend/app/trust/services.py` | 60 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/trust/services.py` | 60 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/trust/services.py` | 79 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/trust/services.py` | 85 | `lab_id` | **RETAIN** | `ConsentRecord.lab_id == lab_id,` |
| `backend/app/trust/services.py` | 85 | `lab_id` | **RETAIN** | `ConsentRecord.lab_id == lab_id,` |
| `backend/app/trust/services.py` | 171 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/trust/services.py` | 174 | `lab_id` | **RETAIN** | `signature_data = f"{document_hash}:{user_id}:{lab_id}:{int(time.time())}"` |
| `backend/app/trust/services.py` | 185 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/trust/services.py` | 185 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/trust/services.py` | 200 | `lab_id` | **RETAIN** | `lab_id: int,` |
| `backend/app/trust/services.py` | 210 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/trust/services.py` | 210 | `lab_id` | **RETAIN** | `lab_id=lab_id,` |
| `backend/app/trust/services.py` | 301 | `lab_id` | **RETAIN** | `def get_compliance_dashboard(self, lab_id: int \| None = None) -> dict[str, Any]:` |
| `backend/app/trust/services.py` | 303 | `lab_id` | **RETAIN** | `if lab_id:` |
| `backend/app/trust/services.py` | 304 | `lab_id` | **RETAIN** | `query = query.filter(ComplianceCheck.target_id == str(lab_id))` |
| `frontend-v2/src/api/endpoints/admin.ts` | 36 | `lab_id` | **DEPRECATE** | `lab_id?: string;` |
| `frontend-v2/src/api/endpoints/admin.ts` | 48 | `lab_id` | **DEPRECATE** | `lab_id: string;` |
| `frontend-v2/src/api/types.ts` | 23 | `lab_id` | **DEPRECATE** | `lab_id: string \| null;` |
| `frontend-v2/src/contexts/AuthContext.tsx` | 85 | `lab_id` | **DEPRECATE** | `labId: user.lab_id \|\| undefined,` |
| `frontend-v2/src/services/WorkflowEngine.ts` | 62 | `lab_id` | **DEPRECATE** | `const result = await apiGet<{ data: Task[] }>('/tasks', { lab_id: labId });` |
| `frontend-v2/src/views/DashboardView.tsx` | 73 | `lab_id` | **DEPRECATE** | `labId: authUser.lab_id \|\| undefined,` |
| `frontend-v3/src/api/client.ts` | 181 | `lab_id` | **MIGRATE** | `lab_id: "demo-tenant",` |
| `frontend-v3/src/api/demoIsolation.test.ts` | 18 | `lab_id` | **MIGRATE** | `lab_id: "demo-tenant",` |
| `frontend-v3/src/api/endpoints.ts` | 215 | `lab_id` | **MIGRATE** | `users: (params?: { role?: string; lab_id?: number; skip?: number; limit?: number }) =>` |
| `frontend-v3/src/api/endpoints.ts` | 340 | `lab_id` | **MIGRATE** | `demand: (data: { lab_id: number; target_tier: string; reason?: string }) =>` |
| `frontend-v3/src/api/generated/types.ts` | 9159 | `LabUser` | **RETAIN** | `// backend model: LabUser  (table: lab_users)` |
| `frontend-v3/src/api/generated/types.ts` | 9160 | `LabUser` | **RETAIN** | `export interface LabUser {` |
| `frontend-v3/src/api/workspaceScopedReads.test.ts` | 12 | `lab_id` | **MIGRATE** | `expect(parseVerifiedWorkspaceScope({ user: { lab_id: 24 } })).toEqual({ labId: 24 });` |
| `frontend-v3/src/api/workspaceScopedReads.test.ts` | 16 | `lab_id` | **MIGRATE** | `expect(() => parseVerifiedWorkspaceScope({ user: { lab_id: null } })).toThrow(WorkspaceReadBlockedError);` |
| `frontend-v3/src/api/workspaceScopedReads.ts` | 18 | `lab_id` | **MIGRATE** | `* موجهات `/patients` و`/lims/orders` تعزل بـ `lab_id`، لكنها لا تستدعي` |
| `frontend-v3/src/api/workspaceScopedReads.ts` | 67 | `lab_id` | **MIGRATE** | `const labId = asPositiveInteger(user?.lab_id);` |
| `frontend-v3/src/api/workspaceScopedReads.ts` | 90 | `lab_id` | **MIGRATE** | `resource_attrs: { lab_id: scope.labId },` |
| `frontend-v3/src/hooks/useApi.ts` | 137 | `lab_id` | **MIGRATE** | `return useQuery({ queryKey: queryKeys.admin.users(params), queryFn: () => adminApi.users(params as { role?: string; lab_id?: number; skip?: number; limit?: number }), ...opts });` |
| `frontend-v3/src/pages/patients/PatientsPage.tsx` | 27 | `lab_id` | **MIGRATE** | `{ accessorKey: "lab_id", header: "رقم المختبر" },` |
| `frontend-v3/src/types/api.ts` | 38 | `lab_id` | **MIGRATE** | `lab_id: number \| null;` |
| `frontend-v3/src/types/api.ts` | 45 | `lab_id` | **MIGRATE** | `lab_id: number \| null;` |
| `frontend-v3/src/types/backend.ts` | 32 | `LabUser` | **MIGRATE** | `export interface LabUser {` |
| `frontend-v3/src/types/backend.ts` | 34 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/backend.ts` | 83 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/backend.ts` | 97 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/backend.ts` | 106 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/backend.ts` | 117 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/backend.ts` | 129 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/backend.ts` | 140 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/backend.ts` | 211 | `lab_id` | **MIGRATE** | `lab_id?: number;` |
| `frontend-v3/src/types/backend.ts` | 315 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/models.ts` | 7 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/models.ts` | 45 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/models.ts` | 54 | `lab_id` | **MIGRATE** | `lab_id: number;` |
| `frontend-v3/src/types/models.ts` | 217 | `lab_id` | **MIGRATE** | `lab_id: number;` |
