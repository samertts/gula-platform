from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text

from app.database import get_db

logger = logging.getLogger("gula.ai.knowledge_graph")


@dataclass
class KnowledgeNode:
    id: int
    node_type: str
    label: str
    description: str | None = None
    aliases: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    external_id: str | None = None


@dataclass
class KnowledgeEdge:
    source_id: int
    target_id: int
    relationship: str
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


_GRAPH_CACHE: dict[str, list[KnowledgeNode]] = {}
_EDGE_CACHE: dict[str, list[KnowledgeEdge]] = {}
_NEIGHBOR_CACHE: dict[int, list[tuple[KnowledgeNode, str, float]]] = {}


class KnowledgeGraph:

    def __init__(self):
        self._initialized = False
        self.nodes: dict[int, KnowledgeNode] = {}
        self.edges: list[KnowledgeEdge] = []
        self._adj: dict[int, list[tuple[int, str, float]]] = {}

    def initialize(self, force: bool = False) -> None:
        if self._initialized and not force:
            return
        self._load_builtin()
        self._initialized = True
        logger.info("[KnowledgeGraph] initialized with %d nodes, %d edges", len(self.nodes), len(self.edges))

    def _load_builtin(self) -> None:
        builtin = _BUILTIN_NODES
        for node_spec in builtin:
            n = KnowledgeNode(**node_spec)
            self.nodes[n.id] = n
        for edge_spec in _BUILTIN_EDGES:
            e = KnowledgeEdge(**edge_spec)
            self.edges.append(e)
            self._adj.setdefault(e.source_id, []).append((e.target_id, e.relationship, e.weight))
            self._adj.setdefault(e.target_id, []).append((e.source_id, e.relationship, e.weight))

    def search_nodes(self, query: str, node_type: str | None = None, limit: int = 20) -> list[KnowledgeNode]:
        q = query.lower().strip()
        results: list[KnowledgeNode] = []
        for node in self.nodes.values():
            if node_type and node.node_type != node_type:
                continue
            if q in node.label.lower():
                results.append(node)
                continue
            for alias in node.aliases:
                if q in alias.lower():
                    results.append(node)
                    break
            else:
                if node.description and q in node.description.lower():
                    results.append(node)
        return results[:limit]

    def get_node(self, node_id: int) -> KnowledgeNode | None:
        return self.nodes.get(node_id)

    def get_node_by_external(self, node_type: str, external_id: str) -> KnowledgeNode | None:
        for node in self.nodes.values():
            if node.node_type == node_type and node.external_id == external_id:
                return node
        try:
            db = next(get_db())
        except Exception:
            return None
        try:
            row = db.execute(
                text("SELECT id, node_type, external_id, label, description, aliases, properties FROM ai_knowledge_nodes WHERE node_type = :nt AND external_id = :eid"),
                {"nt": node_type, "eid": external_id},
            ).fetchone()
            if row:
                return KnowledgeNode(
                    id=row.id, node_type=row.node_type, label=row.label,
                    description=row.description, external_id=row.external_id,
                    aliases=row.aliases if isinstance(row.aliases, list) else [],
                    properties=row.properties if isinstance(row.properties, dict) else {},
                )
        except Exception:
            return None
        finally:
            db.close()
        return None

    def get_neighbors(
        self, node_id: int, relationship: str | None = None, max_depth: int = 1, limit: int = 50
    ) -> list[tuple[KnowledgeNode, str, float]]:
        if max_depth == 1:
            neighbors: list[tuple[KnowledgeNode, str, float]] = []
            for target_id, rel, weight in self._adj.get(node_id, []):
                if relationship and rel != relationship:
                    continue
                target = self.nodes.get(target_id)
                if target:
                    neighbors.append((target, rel, weight))
            return neighbors[:limit]
        visited = {node_id}
        queue: list[tuple[int, int]] = [(node_id, 0)]
        results: list[tuple[KnowledgeNode, str, float]] = []
        while queue and len(results) < limit:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for target_id, rel, weight in self._adj.get(current, []):
                if target_id in visited:
                    continue
                visited.add(target_id)
                target = self.nodes.get(target_id)
                if target:
                    results.append((target, rel, weight))
                queue.append((target_id, depth + 1))
        return results[:limit]

    def shortest_path(self, source_id: int, target_id: int) -> list[KnowledgeNode] | None:
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        if source_id == target_id:
            return [self.nodes[source_id]]
        visited = {source_id}
        queue: list[list[int]] = [[source_id]]
        while queue:
            path = queue.pop(0)
            current = path[-1]
            for neighbor_id, _, _ in self._adj.get(current, []):
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                new_path = [*path, neighbor_id]
                if neighbor_id == target_id:
                    return [self.nodes[nid] for nid in new_path]
                queue.append(new_path)
        return None

    def create_node(
        self, node_type: str, label: str, description: str | None = None,
        aliases: list[str] | None = None, properties: dict[str, Any] | None = None,
        external_id: str | None = None,
    ) -> KnowledgeNode:
        node_id = max(self.nodes.keys()) + 1 if self.nodes else 1
        node = KnowledgeNode(
            id=node_id, node_type=node_type, label=label,
            description=description, aliases=aliases or [],
            properties=properties or {}, external_id=external_id,
        )
        self.nodes[node.id] = node
        db = next(get_db())
        try:
            aliases_json = f"'{_jsonify(aliases or [])}'::jsonb"
            props_json = f"'{_jsonify(properties or {})}'::jsonb"
            db.execute(
                text(f"INSERT INTO ai_knowledge_nodes (node_type, external_id, label, description, aliases, properties) VALUES (:nt, :eid, :label, :desc, {aliases_json}, {props_json})"),
                {"nt": node_type, "eid": external_id, "label": label, "desc": description},
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("[KnowledgeGraph] DB insert failed (in-memory only): %s", exc)
        finally:
            db.close()
        return node

    def create_edge(
        self, source_id: int, target_id: int, relationship: str,
        weight: float = 1.0, properties: dict[str, Any] | None = None,
    ) -> KnowledgeEdge:
        edge = KnowledgeEdge(
            source_id=source_id, target_id=target_id,
            relationship=relationship, weight=weight,
            properties=properties or {},
        )
        self.edges.append(edge)
        self._adj.setdefault(source_id, []).append((target_id, relationship, weight))
        self._adj.setdefault(target_id, []).append((source_id, relationship, weight))
        return edge


def _jsonify(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)


_BUILTIN_NODES = [
    {"id": 1, "node_type": "lab_test", "label": "Complete Blood Count (CBC)", "aliases": ["cbc", "blood count", "hemogram", "صورة دم كاملة"], "description": "Complete blood count measuring cellular components of blood", "external_id": "LOINC:58410-2"},
    {"id": 2, "node_type": "lab_test", "label": "Hemoglobin", "aliases": ["hgb", "hb", "هيموغلوبين"], "description": "Hemoglobin concentration in blood", "external_id": "LOINC:718-7"},
    {"id": 3, "node_type": "lab_test", "label": "White Blood Cell Count", "aliases": ["wbc", "leukocyte count", "كريات بيضاء"], "description": "Total white blood cell count", "external_id": "LOINC:6690-2"},
    {"id": 4, "node_type": "lab_test", "label": "Platelet Count", "aliases": ["plt", "thrombocyte count", "صفائح دموية"], "description": "Platelet count", "external_id": "LOINC:777-3"},
    {"id": 5, "node_type": "lab_test", "label": "Serum Glucose", "aliases": ["glucose", "blood sugar", "fbs", "rbs", "سكر"], "description": "Glucose level in blood", "external_id": "LOINC:2345-7"},
    {"id": 6, "node_type": "lab_test", "label": "HbA1c", "aliases": ["glycated hemoglobin", "a1c", "سكر تراكمي"], "description": "Glycated hemoglobin for diabetes monitoring", "external_id": "LOINC:4548-4"},
    {"id": 7, "node_type": "lab_test", "label": "Serum Creatinine", "aliases": ["creatinine", "كرياتينين"], "description": "Creatinine level for kidney function", "external_id": "LOINC:2160-0"},
    {"id": 8, "node_type": "lab_test", "label": "Blood Urea Nitrogen", "aliases": ["bun", "urea", "يوريا"], "description": "Urea nitrogen level", "external_id": "LOINC:3094-0"},
    {"id": 9, "node_type": "lab_test", "label": "Serum Sodium", "aliases": ["sodium", "na+", "صوديوم"], "description": "Sodium level", "external_id": "LOINC:2951-2"},
    {"id": 10, "node_type": "lab_test", "label": "Serum Potassium", "aliases": ["potassium", "k+", "بوتاسيوم"], "description": "Potassium level", "external_id": "LOINC:2823-3"},
    {"id": 11, "node_type": "lab_test", "label": "Serum Calcium", "aliases": ["calcium", "ca2+", "كالسيوم"], "description": "Calcium level", "external_id": "LOINC:17861-6"},
    {"id": 12, "node_type": "lab_test", "label": "Troponin I", "aliases": ["troponin", "cTnI", "تروبونين"], "description": "Cardiac troponin I for heart attack diagnosis", "external_id": "LOINC:10839-9"},
    {"id": 13, "node_type": "lab_test", "label": "Prothrombin Time / INR", "aliases": ["pt", "inr", "prothrombin time", "زمن البروثرومبين"], "description": "Prothrombin time and INR for coagulation", "external_id": "LOINC:5964-2"},
    {"id": 14, "node_type": "lab_test", "label": "ALT", "aliases": ["alt", "sgpt", "alanine transaminase"], "description": "Alanine transaminase for liver function", "external_id": "LOINC:1742-6"},
    {"id": 15, "node_type": "lab_test", "label": "AST", "aliases": ["ast", "sgot", "aspartate transaminase"], "description": "Aspartate transaminase for liver function", "external_id": "LOINC:1920-8"},
    {"id": 16, "node_type": "lab_test", "label": "TSH", "aliases": ["tsh", "thyroid stimulating hormone"], "description": "Thyroid stimulating hormone", "external_id": "LOINC:3016-3"},
    {"id": 17, "node_type": "lab_test", "label": "HDL Cholesterol", "aliases": ["hdl", "good cholesterol"], "description": "HDL cholesterol level", "external_id": "LOINC:2085-9"},
    {"id": 18, "node_type": "lab_test", "label": "LDL Cholesterol", "aliases": ["ldl", "bad cholesterol"], "description": "LDL cholesterol level", "external_id": "LOINC:18262-6"},
    {"id": 19, "node_type": "lab_test", "label": "Total Cholesterol", "aliases": ["cholesterol", "total cholesterol", "كولسترول"], "description": "Total cholesterol level", "external_id": "LOINC:2093-3"},
    {"id": 20, "node_type": "lab_test", "label": "Triglycerides", "aliases": ["trig", "tg", "دهون ثلاثية"], "description": "Triglyceride level", "external_id": "LOINC:2571-8"},
    {"id": 21, "node_type": "lab_test", "label": "Bilirubin Total", "aliases": ["bilirubin total", "tbil", "صفار"], "description": "Total bilirubin level", "external_id": "LOINC:1975-2"},
    {"id": 22, "node_type": "lab_test", "label": "Albumin", "aliases": ["albumin", "زلال"], "description": "Serum albumin level", "external_id": "LOINC:1751-7"},
    {"id": 23, "node_type": "condition", "label": "Anemia", "aliases": ["فقر دم", "anemia"], "description": "Decreased hemoglobin or red blood cell count", "external_id": "SNOMED:271737000"},
    {"id": 24, "node_type": "condition", "label": "Diabetes Mellitus", "aliases": ["diabetes", "سكري", "dm"], "description": "Elevated blood glucose", "external_id": "SNOMED:73211009"},
    {"id": 25, "node_type": "condition", "label": "Chronic Kidney Disease", "aliases": ["ckd", "renal failure", "فشل كلوي"], "description": "Decreased kidney function", "external_id": "SNOMED:709044004"},
    {"id": 26, "node_type": "condition", "label": "Hyperkalemia", "aliases": ["high potassium", "فرط بوتاسيوم"], "description": "Elevated serum potassium", "external_id": "SNOMED:14140009"},
    {"id": 27, "node_type": "condition", "label": "Hypernatremia", "aliases": ["high sodium", "فرط صوديوم"], "description": "Elevated serum sodium", "external_id": "SNOMED:89627008"},
    {"id": 28, "node_type": "condition", "label": "Myocardial Infarction", "aliases": ["heart attack", "MI", "احتشاء قلبي"], "description": "Heart muscle damage from ischemia", "external_id": "SNOMED:22298006"},
    {"id": 29, "node_type": "condition", "label": "Liver Disease", "aliases": ["hepatic", "مرض كبدي"], "description": "Impaired liver function", "external_id": "SNOMED:235856003"},
    {"id": 30, "node_type": "condition", "label": "Hypothyroidism", "aliases": ["قصور درقي", "underactive thyroid"], "description": "Decreased thyroid function", "external_id": "SNOMED:40930008"},
    {"id": 31, "node_type": "condition", "label": "Hyperthyroidism", "aliases": ["فرط درقي", "overactive thyroid"], "description": "Increased thyroid function", "external_id": "SNOMED:34486009"},
    {"id": 32, "node_type": "condition", "label": "Hyperlipidemia", "aliases": ["high cholesterol", "فرط شحميات"], "description": "Elevated blood lipids", "external_id": "SNOMED:55822004"},
    {"id": 33, "node_type": "medication", "label": "Metformin", "aliases": ["glucophage", "ميتفورمين"], "description": "First-line diabetes medication", "external_id": "RxNorm:6809"},
    {"id": 34, "node_type": "medication", "label": "Insulin", "aliases": ["انسولين"], "description": "Hormone for glucose regulation", "external_id": "RxNorm:5794"},
    {"id": 35, "node_type": "medication", "label": "Warfarin", "aliases": ["coumarin", "وارفارين"], "description": "Anticoagulant medication", "external_id": "RxNorm:11289"},
    {"id": 36, "node_type": "medication", "label": "Levothyroxine", "aliases": ["synthroid", "ليفوثيروكسين"], "description": "Thyroid hormone replacement", "external_id": "RxNorm:10582"},
    {"id": 37, "node_type": "medication", "label": "Atorvastatin", "aliases": ["lipitor", "أتورفاستاتين"], "description": "Statin for cholesterol reduction", "external_id": "RxNorm:83367"},
    {"id": 38, "node_type": "specimen", "label": "Blood (Venous)", "aliases": ["venous blood", "serum", "plasma", "دم وريدي"], "description": "Venous blood sample", "external_id": "SNOMED:122554006"},
    {"id": 39, "node_type": "specimen", "label": "Blood (Capillary)", "aliases": ["capillary blood", "دم شعري"], "description": "Capillary blood sample", "external_id": "SNOMED:122555007"},
    {"id": 40, "node_type": "specimen", "label": "Urine", "aliases": ["بول", "urine sample"], "description": "Urine specimen", "external_id": "SNOMED:122575008"},
    {"id": 41, "node_type": "specimen", "label": "CSF", "aliases": ["cerebrospinal fluid", "سائل دماغي شوكي"], "description": "Cerebrospinal fluid specimen", "external_id": "SNOMED:112638006"},
    {"id": 42, "node_type": "panel", "label": "Basic Metabolic Panel", "aliases": ["bmp", "أيض أساسي"], "description": "Glucose, BUN, Creatinine, Sodium, Potassium, Chloride, CO2, Calcium", "external_id": "LOINC:24321-2"},
    {"id": 43, "node_type": "panel", "label": "Comprehensive Metabolic Panel", "aliases": ["cmp", "أيض شامل"], "description": "BMP + ALT, AST, Bilirubin, Alk Phos, Total Protein, Albumin", "external_id": "LOINC:24323-8"},
    {"id": 44, "node_type": "panel", "label": "Lipid Panel", "aliases": ["دهون", "lipid profile"], "description": "Total Cholesterol, HDL, LDL, Triglycerides", "external_id": "LOINC:24331-1"},
    {"id": 45, "node_type": "panel", "label": "Liver Function Panel", "aliases": ["lfp", "وظائف كبد"], "description": "ALT, AST, Bilirubin, Alk Phos, Total Protein, Albumin", "external_id": "LOINC:24320-4"},
    {"id": 46, "node_type": "panel", "label": "Thyroid Panel", "aliases": ["غدة درقية", "thyroid function"], "description": "TSH, T3, T4", "external_id": "LOINC:24332-9"},
    {"id": 47, "node_type": "department", "label": "Hematology", "aliases": ["hematology lab", "مختبر دم"], "description": "Blood cell analysis", "external_id": "dept_hematology"},
    {"id": 48, "node_type": "department", "label": "Clinical Chemistry", "aliases": ["biochemistry lab", "كيمياء سريرية"], "description": "Chemical analysis of body fluids", "external_id": "dept_chemistry"},
    {"id": 49, "node_type": "department", "label": "Microbiology", "aliases": ["micro lab", "ميكروبيولوجي"], "description": "Microorganism detection and identification", "external_id": "dept_microbiology"},
    {"id": 50, "node_type": "department", "label": "Immunology/Serology", "aliases": ["serology lab", "مناعة"], "description": "Antibody and antigen testing", "external_id": "dept_immunology"},
]

_BUILTIN_EDGES = [
    {"source_id": 1, "target_id": 2, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 1, "target_id": 3, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 1, "target_id": 4, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 42, "target_id": 5, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 42, "target_id": 7, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 42, "target_id": 8, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 42, "target_id": 9, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 42, "target_id": 10, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 43, "target_id": 42, "relationship": "extends", "weight": 1.0},
    {"source_id": 44, "target_id": 17, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 44, "target_id": 18, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 44, "target_id": 19, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 44, "target_id": 20, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 45, "target_id": 14, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 45, "target_id": 15, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 45, "target_id": 21, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 45, "target_id": 22, "relationship": "includes_test", "weight": 1.0},
    {"source_id": 2, "target_id": 23, "relationship": "indicates", "weight": 0.8},
    {"source_id": 5, "target_id": 24, "relationship": "indicates", "weight": 0.9},
    {"source_id": 6, "target_id": 24, "relationship": "monitors", "weight": 0.9},
    {"source_id": 7, "target_id": 25, "relationship": "indicates", "weight": 0.8},
    {"source_id": 8, "target_id": 25, "relationship": "indicates", "weight": 0.7},
    {"source_id": 10, "target_id": 26, "relationship": "indicates", "weight": 0.9},
    {"source_id": 9, "target_id": 27, "relationship": "indicates", "weight": 0.9},
    {"source_id": 12, "target_id": 28, "relationship": "indicates", "weight": 0.95},
    {"source_id": 14, "target_id": 29, "relationship": "indicates", "weight": 0.7},
    {"source_id": 15, "target_id": 29, "relationship": "indicates", "weight": 0.7},
    {"source_id": 16, "target_id": 30, "relationship": "indicates", "weight": 0.6},
    {"source_id": 16, "target_id": 31, "relationship": "indicates", "weight": 0.6},
    {"source_id": 19, "target_id": 32, "relationship": "indicates", "weight": 0.7},
    {"source_id": 20, "target_id": 32, "relationship": "indicates", "weight": 0.6},
    {"source_id": 24, "target_id": 33, "relationship": "treated_by", "weight": 0.9},
    {"source_id": 24, "target_id": 34, "relationship": "treated_by", "weight": 0.8},
    {"source_id": 13, "target_id": 35, "relationship": "monitored_by", "weight": 0.9},
    {"source_id": 30, "target_id": 36, "relationship": "treated_by", "weight": 0.9},
    {"source_id": 32, "target_id": 37, "relationship": "treated_by", "weight": 0.8},
    {"source_id": 2, "target_id": 38, "relationship": "uses_specimen", "weight": 1.0},
    {"source_id": 3, "target_id": 38, "relationship": "uses_specimen", "weight": 1.0},
    {"source_id": 4, "target_id": 38, "relationship": "uses_specimen", "weight": 1.0},
    {"source_id": 5, "target_id": 38, "relationship": "uses_specimen", "weight": 1.0},
    {"source_id": 5, "target_id": 39, "relationship": "uses_specimen", "weight": 0.5},
    {"source_id": 7, "target_id": 38, "relationship": "uses_specimen", "weight": 1.0},
    {"source_id": 40, "target_id": 7, "relationship": "alternative_for", "weight": 0.5},
    {"source_id": 2, "target_id": 47, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 3, "target_id": 47, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 4, "target_id": 47, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 5, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 7, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 10, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 9, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 42, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 43, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 44, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 45, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 46, "target_id": 48, "relationship": "performed_by", "weight": 1.0},
    {"source_id": 42, "target_id": 46, "relationship": "differs_from", "weight": 0.3},
    {"source_id": 32, "target_id": 28, "relationship": "risk_factor_for", "weight": 0.5},
    {"source_id": 24, "target_id": 25, "relationship": "risk_factor_for", "weight": 0.4},
    {"source_id": 24, "target_id": 28, "relationship": "risk_factor_for", "weight": 0.3},
    {"source_id": 32, "target_id": 28, "relationship": "risk_factor_for", "weight": 0.4},
    {"source_id": 25, "target_id": 26, "relationship": "complication_of", "weight": 0.5},
    {"source_id": 29, "target_id": 21, "relationship": "associated_with", "weight": 0.6},
]

knowledge_graph = KnowledgeGraph()
