import ast
import hashlib
import logging
import os
import re
from collections import deque
from pathlib import Path

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app._compat import UTC

from ..database import SessionLocal
from .models import EdgeType, KnowledgeEdge, KnowledgeGraphSnapshot, KnowledgeNode, NodeType

logger = logging.getLogger("gula.knowledge_graph")

_ROUTER_INCLUDE_PATTERN = re.compile(r"app\.include_router\((\w+)\.router\)")
_ROUTE_DECORATOR_PATTERN = re.compile(r"@router\.(get|post|put|patch|delete)\(")
_MODEL_PATTERN = re.compile(r"class\s+(\w+)\(.*Base.*\):")
_EVENT_PATTERN = re.compile(r"class\s+(\w+Event)\b")
_TABLENAME_PATTERN = re.compile(r'__tablename__\s*=\s*["\']([^"\']+)["\']')

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)
BACKEND_APP = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app")


def _compute_graph_hash(nodes: list[KnowledgeNode], edges: list[KnowledgeEdge]) -> str:
    hasher = hashlib.sha256()
    for n in sorted(nodes, key=lambda x: x.qualified_name):
        hasher.update(f"{n.node_type}:{n.qualified_name}:{n.version}".encode())
    for e in sorted(edges, key=lambda x: f"{x.source_node_id}:{x.target_node_id}"):
        hasher.update(f"{e.source_node_id}:{e.target_node_id}:{e.edge_type}".encode())
    return hasher.hexdigest()[:16]


def _get_or_create_node(
    db: Session,
    node_type: NodeType,
    name: str,
    qualified_name: str,
    description: str = "",
    metadata: dict | None = None,
    source_path: str = "",
    tags: list[str] | None = None,
    version: str = "1.0.0",
) -> KnowledgeNode:
    existing = db.query(KnowledgeNode).filter(
        KnowledgeNode.qualified_name == qualified_name
    ).first()
    if existing:
        existing.name = name
        existing.description = description or existing.description
        existing.tags = tags or existing.tags
        existing.extra_metadata = metadata or existing.extra_metadata
        existing.source_path = source_path or existing.source_path
        existing.updated_at = func.now()
        return existing
    node = KnowledgeNode(
        node_type=node_type.value,
        name=name,
        qualified_name=qualified_name,
        description=description,
        extra_metadata=metadata or {},
        source_path=source_path,
        tags=tags or [],
        version=version,
    )
    db.add(node)
    db.flush()
    return node


def _get_node_by_qualified_name(db: Session, qualified_name: str) -> KnowledgeNode | None:
    return db.query(KnowledgeNode).filter(
        KnowledgeNode.qualified_name == qualified_name
    ).first()


def _create_edge(
    db: Session,
    source_qualified_name: str,
    target_qualified_name: str,
    edge_type: EdgeType,
    metadata: dict | None = None,
    weight: float = 1.0,
) -> KnowledgeEdge | None:
    source = _get_node_by_qualified_name(db, source_qualified_name)
    target = _get_node_by_qualified_name(db, target_qualified_name)
    if not source or not target:
        logger.warning(
            "Cannot create edge %s: source=%s (%s) target=%s (%s)",
            edge_type.value,
            source_qualified_name,
            "found" if source else "NOT FOUND",
            target_qualified_name,
            "found" if target else "NOT FOUND",
        )
        return None
    existing = db.query(KnowledgeEdge).filter(
        KnowledgeEdge.source_node_id == source.id,
        KnowledgeEdge.target_node_id == target.id,
        KnowledgeEdge.edge_type == edge_type.value,
    ).first()
    if existing:
        return existing
    edge = KnowledgeEdge(
        source_node_id=source.id,
        target_node_id=target.id,
        edge_type=edge_type.value,
        metadata=metadata or {},
        weight=weight,
    )
    db.add(edge)
    db.flush()
    return edge


class _ASTScanner:
    """Internal AST-based code scanner for discovery and indexing."""

    def __init__(self, engine: "KnowledgeGraphEngine"):
        self.engine = engine
        self.db = SessionLocal()

    def close(self):
        self.db.close()

    def commit(self):
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def scan_file(self, filepath: str, rel_path: str) -> int:
        """Scan a single Python file, creating nodes for classes, functions, routes."""
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                source = f.read()
        except Exception as exc:
            logger.warning("Cannot read %s: %s", filepath, exc)
            return 0

        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as exc:
            logger.warning("Syntax error in %s: %s", filepath, exc)
            return 0

        nodes_created = 0
        module_qn = rel_path.replace(".py", "").replace("/", ".")

        _get_or_create_node(
            self.db,
            NodeType.MODULE,
            os.path.basename(filepath),
            module_qn,
            description=f"Python module: {rel_path}",
            source_path=rel_path,
            tags=["python", "module"],
        )
        nodes_created += 1

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_qn = f"{module_qn}.{node.name}"
                is_model = bool(
                    any(
                        base
                        for base in node.bases
                        if isinstance(base, ast.Name) and base.id == "Base"
                    )
                )
                class_type = NodeType.MODEL if is_model else NodeType.CLASS

                decorator_names = {d.id for d in node.decorator_list if isinstance(d, ast.Name)}
                if "app" in decorator_names or "router" in decorator_names:
                    class_type = NodeType.ROUTE

                tablename = None
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "__tablename__":
                                if isinstance(item.value, ast.Constant):
                                    tablename = item.value.value

                meta = {}
                if tablename:
                    meta["table_name"] = tablename
                    class_type = NodeType.DATABASE_TABLE

                _get_or_create_node(
                    self.db,
                    class_type,
                    node.name,
                    class_qn,
                    description=ast.get_docstring(node) or "",
                    source_path=rel_path,
                    tags=["model" if is_model else "class", class_type.value.lower()],
                    metadata=meta,
                )

                _create_edge(
                    self.db,
                    module_qn,
                    class_qn,
                    EdgeType.CONTAINS,
                    weight=1.0,
                )

                if tablename:
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            col_name = item.target.id
                            col_qn = f"{class_qn}.{col_name}"
                            _get_or_create_node(
                                self.db,
                                NodeType.DATABASE_COLUMN,
                                col_name,
                                col_qn,
                                source_path=rel_path,
                                tags=["column"],
                                metadata={"parent_table": tablename},
                            )
                            _create_edge(
                                self.db,
                                class_qn,
                                col_qn,
                                EdgeType.CONTAINS,
                                weight=0.5,
                            )
                            nodes_created += 1

                nodes_created += 1

            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith("_"):
                    continue
                func_qn = f"{module_qn}.{node.name}"

                decorator_names = []
                for d in node.decorator_list:
                    if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute):
                        decorator_names.append(f"{d.func.attr}")
                    elif isinstance(d, ast.Call) and isinstance(d.func, ast.Name):
                        decorator_names.append(d.func.id)

                is_route_handler = any(
                    d in ("get", "post", "put", "patch", "delete") for d in decorator_names
                )
                fn_type = NodeType.ENDPOINT if is_route_handler else NodeType.FUNCTION
                fn_tags = ["route_handler" if is_route_handler else "function"]

                _get_or_create_node(
                    self.db,
                    fn_type,
                    node.name,
                    func_qn,
                    description=ast.get_docstring(node) or "",
                    source_path=rel_path,
                    tags=fn_tags,
                )

                container = module_qn
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        for item in parent.body:
                            if isinstance(item, ast.FunctionDef) and item.name == node.name:
                                container = f"{module_qn}.{parent.name}"
                                _create_edge(
                                    self.db,
                                    container,
                                    func_qn,
                                    EdgeType.CONTAINS,
                                    weight=1.0,
                                )
                                break

                if container == module_qn:
                    _create_edge(
                        self.db,
                        module_qn,
                        func_qn,
                        EdgeType.CONTAINS,
                        weight=1.0,
                    )

                if is_route_handler:
                    http_methods = [d for d in decorator_names if d in ("get", "post", "put", "patch", "delete")]
                    path_str = ""
                    for d in node.decorator_list:
                        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ("get", "post", "put", "patch", "delete"):
                            if d.args:
                                path_str = d.args[0].value if isinstance(d.args[0], ast.Constant) else ""
                            break
                    param_names = [arg.arg for arg in node.args.args if arg.arg not in ("self", "cls")]
                    route_node = _get_or_create_node(
                        self.db,
                        NodeType.ROUTE,
                        f"{','.join(http_methods).upper()} {path_str}",
                        f"route:{','.join(http_methods)}:{path_str}",
                        source_path=rel_path,
                        tags=["route", *http_methods],
                        metadata={"methods": http_methods, "path": path_str, "params": param_names},
                    )
                    _create_edge(
                        self.db,
                        route_node.qualified_name,
                        func_qn,
                        EdgeType.IMPLEMENTS,
                        weight=1.0,
                    )
                    nodes_created += 1

                nodes_created += 1

        return nodes_created

    def scan_directory(self, directory: str, prefix: str = "") -> int:
        """Recursively scan a directory for Python files."""
        total = 0
        dir_path = Path(directory)
        if not dir_path.is_dir():
            return 0

        if prefix:
            _get_or_create_node(
                self.db,
                NodeType.PACKAGE,
                dir_path.name,
                prefix,
                description=f"Package: {dir_path}",
                source_path=str(dir_path),
                tags=["package"],
            )

        for entry in sorted(dir_path.iterdir()):
            if entry.name.startswith("__") or entry.name.startswith("."):
                continue

            rel = f"{prefix}.{entry.stem}" if prefix else entry.stem

            if entry.is_dir():
                init_file = entry / "__init__.py"
                if init_file.exists():
                    total += self.scan_file(str(init_file), f"{rel}/__init__.py")
                total += self.scan_directory(str(entry), rel)
            elif entry.suffix == ".py":
                total += self.scan_file(str(entry), f"{rel}.py")

        return total

    def scan_route_patterns(self) -> int:
        """Scan main.py for app.include_router statements and index discovered routes."""
        main_py = os.path.join(BACKEND_APP, "main.py")
        if not os.path.exists(main_py):
            return 0

        count = 0
        router_registrations = []
        with open(main_py, encoding="utf-8") as f:
            source = f.read()

        for match in _ROUTER_INCLUDE_PATTERN.finditer(source):
            router_var = match.group(1)
            router_registrations.append(router_var)
            qn = f"gula.routes.{router_var}"
            _get_or_create_node(
                self.db,
                NodeType.ROUTE,
                f"router:{router_var}",
                qn,
                description=f"Router registration: {router_var}",
                source_path="backend/app/main.py",
                tags=["router", "registration"],
            )
            count += 1

        project_node = _get_node_by_qualified_name(self.db, "gula")
        if project_node:
            for reg in router_registrations:
                qn = f"gula.routes.{reg}"
                _create_edge(
                    self.db,
                    "gula",
                    qn,
                    EdgeType.CONTAINS,
                    weight=1.0,
                )

        self.commit()
        return count

    def scan_event_patterns(self) -> int:
        """Scan Python files for event class definitions."""
        count = 0
        for root, _dirs, files in os.walk(BACKEND_APP):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, encoding="utf-8", errors="replace") as f:
                        source = f.read()
                except Exception:
                    continue
                for match in _EVENT_PATTERN.finditer(source):
                    event_name = match.group(1)
                    rel = os.path.relpath(fpath, PROJECT_ROOT)
                    qn = f"gula.events.{event_name}"
                    _get_or_create_node(
                        self.db,
                        NodeType.EVENT,
                        event_name,
                        qn,
                        source_path=rel,
                        tags=["event"],
                    )
                    count += 1

        self.commit()
        return count

    def scan_model_patterns(self) -> int:
        """Scan Python files for SQLAlchemy model definitions."""
        count = 0
        for root, _dirs, files in os.walk(BACKEND_APP):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, encoding="utf-8", errors="replace") as f:
                        source = f.read()
                except Exception:
                    continue
                for match in _MODEL_PATTERN.finditer(source):
                    model_name = match.group(1)
                    rel = os.path.relpath(fpath, PROJECT_ROOT)
                    qn = f"gula.models.{model_name}"
                    node = _get_or_create_node(
                        self.db,
                        NodeType.MODEL,
                        model_name,
                        qn,
                        source_path=rel,
                        tags=["sqlalchemy", "model"],
                    )
                    tablename_match = _TABLENAME_PATTERN.search(source)
                    if tablename_match:
                        node.extra_metadata = {**(node.extra_metadata or {}), "table_name": tablename_match.group(1)}
                    count += 1
        self.commit()
        return count


class KnowledgeGraphEngine:
    """Platform Knowledge Graph — complete map of the GULA ecosystem."""

    def __init__(self):
        self._scanner: _ASTScanner | None = None

    @property
    def scanner(self) -> _ASTScanner:
        if self._scanner is None:
            self._scanner = _ASTScanner(self)
        return self._scanner

    async def add_node(
        self,
        node_type: NodeType,
        name: str,
        qualified_name: str,
        description: str = "",
        metadata: dict | None = None,
        source_path: str = "",
        tags: list[str] | None = None,
        version: str = "1.0.0",
    ) -> KnowledgeNode:
        db = SessionLocal()
        try:
            node = _get_or_create_node(
                db, node_type, name, qualified_name, description,
                metadata, source_path, tags, version,
            )
            db.commit()
            return node
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def add_edge(
        self,
        source_qualified_name: str,
        target_qualified_name: str,
        edge_type: EdgeType,
        metadata: dict | None = None,
        weight: float = 1.0,
    ) -> KnowledgeEdge | None:
        db = SessionLocal()
        try:
            edge = _create_edge(db, source_qualified_name, target_qualified_name, edge_type, metadata, weight)
            db.commit()
            return edge
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def get_node(self, qualified_name: str) -> KnowledgeNode | None:
        db = SessionLocal()
        try:
            return _get_node_by_qualified_name(db, qualified_name)
        finally:
            db.close()

    async def get_neighbors(
        self,
        qualified_name: str,
        edge_types: list[EdgeType] | None = None,
        max_depth: int = 1,
    ) -> list[dict]:
        db = SessionLocal()
        try:
            node = _get_node_by_qualified_name(db, qualified_name)
            if not node:
                return []

            visited = {node.id}
            results: list[dict] = []
            queue = deque([(node, 0)])

            while queue:
                current, depth = queue.popleft()
                if depth >= max_depth:
                    continue

                type_filter = [et.value for et in edge_types] if edge_types else None

                for edge in db.query(KnowledgeEdge).filter(
                    KnowledgeEdge.source_node_id == current.id
                ).all():
                    if type_filter and edge.edge_type not in type_filter:
                        continue
                    target = db.query(KnowledgeNode).filter(KnowledgeNode.id == edge.target_node_id).first()
                    if target and target.id not in visited:
                        visited.add(target.id)
                        entry = {
                            "node": {
                                "id": target.id,
                                "node_type": target.node_type,
                                "name": target.name,
                                "qualified_name": target.qualified_name,
                                "description": target.description,
                            },
                            "edge": {
                                "id": edge.id,
                                "edge_type": edge.edge_type,
                                "weight": edge.weight,
                            },
                            "depth": depth + 1,
                            "direction": "outgoing",
                        }
                        results.append(entry)
                        queue.append((target, depth + 1))

                for edge in db.query(KnowledgeEdge).filter(
                    KnowledgeEdge.target_node_id == current.id
                ).all():
                    if type_filter and edge.edge_type not in type_filter:
                        continue
                    source = db.query(KnowledgeNode).filter(KnowledgeNode.id == edge.source_node_id).first()
                    if source and source.id not in visited:
                        visited.add(source.id)
                        entry = {
                            "node": {
                                "id": source.id,
                                "node_type": source.node_type,
                                "name": source.name,
                                "qualified_name": source.qualified_name,
                                "description": source.description,
                            },
                            "edge": {
                                "id": edge.id,
                                "edge_type": edge.edge_type,
                                "weight": edge.weight,
                            },
                            "depth": depth + 1,
                            "direction": "incoming",
                        }
                        results.append(entry)
                        queue.append((source, depth + 1))

            return results
        finally:
            db.close()

    async def find_path(self, source_name: str, target_name: str) -> list[dict]:
        """BFS shortest path between two qualified names."""
        db = SessionLocal()
        try:
            source = _get_node_by_qualified_name(db, source_name)
            target = _get_node_by_qualified_name(db, target_name)
            if not source or not target:
                return []

            if source.id == target.id:
                return [{"node": {"id": source.id, "qualified_name": source.qualified_name, "name": source.name}, "edge": None}]

            parent: dict[int, tuple[int, KnowledgeEdge | None]] = {source.id: (-1, None)}
            queue = deque([source])
            found = False

            while queue and not found:
                current = queue.popleft()
                for edge in db.query(KnowledgeEdge).filter(
                    KnowledgeEdge.source_node_id == current.id
                ).all():
                    nid = edge.target_node_id
                    if nid not in parent:
                        parent[nid] = (current.id, edge)
                        if nid == target.id:
                            found = True
                            break
                        neighbor = db.query(KnowledgeNode).filter(KnowledgeNode.id == nid).first()
                        if neighbor:
                            queue.append(neighbor)
                if not found:
                    for edge in db.query(KnowledgeEdge).filter(
                        KnowledgeEdge.target_node_id == current.id
                    ).all():
                        nid = edge.source_node_id
                        if nid not in parent:
                            parent[nid] = (current.id, edge)
                            if nid == target.id:
                                found = True
                                break
                            neighbor = db.query(KnowledgeNode).filter(KnowledgeNode.id == nid).first()
                            if neighbor:
                                queue.append(neighbor)

            if not found:
                return []

            path: list[dict] = []
            cur = target.id
            while cur != -1:
                prev_id, edge = parent[cur]
                node = db.query(KnowledgeNode).filter(KnowledgeNode.id == cur).first()
                path.append({
                    "node": {
                        "id": node.id,
                        "qualified_name": node.qualified_name,
                        "name": node.name,
                        "node_type": node.node_type,
                    },
                    "edge": {
                        "id": edge.id,
                        "edge_type": edge.edge_type,
                        "weight": edge.weight,
                    } if edge else None,
                })
                cur = prev_id
            path.reverse()
            return path
        finally:
            db.close()

    async def search_nodes(
        self,
        query: str,
        node_types: list[NodeType] | None = None,
    ) -> list[dict]:
        db = SessionLocal()
        try:
            q = db.query(KnowledgeNode)
            like = f"%{query}%"
            q = q.filter(
                KnowledgeNode.name.ilike(like)
                | KnowledgeNode.qualified_name.ilike(like)
                | KnowledgeNode.description.ilike(like)
            )
            if node_types:
                type_values = [nt.value for nt in node_types]
                q = q.filter(KnowledgeNode.node_type.in_(type_values))
            q = q.order_by(KnowledgeNode.node_type, KnowledgeNode.name).limit(100)
            nodes = q.all()
            return [
                {
                    "id": n.id,
                    "node_type": n.node_type,
                    "name": n.name,
                    "qualified_name": n.qualified_name,
                    "description": n.description,
                    "source_path": n.source_path,
                    "tags": n.tags,
                    "version": n.version,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in nodes
            ]
        finally:
            db.close()

    async def get_dependency_graph(self, qualified_name: str) -> dict:
        db = SessionLocal()
        try:
            node = _get_node_by_qualified_name(db, qualified_name)
            if not node:
                return {"error": f"Node '{qualified_name}' not found"}

            dependencies: list[dict] = []
            dependents: list[dict] = []

            for edge in db.query(KnowledgeEdge).filter(
                KnowledgeEdge.source_node_id == node.id,
                KnowledgeEdge.edge_type.in_(["DEPENDS_ON", "CALLS", "REFERENCES", "EXTENDS", "IMPLEMENTS"]),
            ).all():
                target = db.query(KnowledgeNode).filter(KnowledgeNode.id == edge.target_node_id).first()
                if target:
                    dependencies.append({
                        "qualified_name": target.qualified_name,
                        "name": target.name,
                        "node_type": target.node_type,
                        "edge_type": edge.edge_type,
                        "weight": edge.weight,
                    })

            for edge in db.query(KnowledgeEdge).filter(
                KnowledgeEdge.target_node_id == node.id,
                KnowledgeEdge.edge_type.in_(["DEPENDS_ON", "CALLS", "REFERENCES", "EXTENDS", "IMPLEMENTS"]),
            ).all():
                source = db.query(KnowledgeNode).filter(KnowledgeNode.id == edge.source_node_id).first()
                if source:
                    dependents.append({
                        "qualified_name": source.qualified_name,
                        "name": source.name,
                        "node_type": source.node_type,
                        "edge_type": edge.edge_type,
                        "weight": edge.weight,
                    })

            return {
                "node": {
                    "id": node.id,
                    "qualified_name": node.qualified_name,
                    "name": node.name,
                    "node_type": node.node_type,
                },
                "dependencies": dependencies,
                "dependents": dependents,
            }
        finally:
            db.close()

    async def snapshot(self) -> KnowledgeGraphSnapshot:
        db = SessionLocal()
        try:
            node_count = db.query(func.count(KnowledgeNode.id)).scalar() or 0
            edge_count = db.query(func.count(KnowledgeEdge.id)).scalar() or 0
            nodes = db.query(KnowledgeNode).all()
            edges = db.query(KnowledgeEdge).all()
            graph_hash = _compute_graph_hash(nodes, edges)

            snap = KnowledgeGraphSnapshot(
                version="1.0.0",
                node_count=node_count,
                edge_count=edge_count,
                graph_hash=graph_hash,
                metadata={"generated_at": str(UTC.utcnow())},
            )
            db.add(snap)
            db.commit()
            db.refresh(snap)
            return snap
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    async def get_statistics(self) -> dict:
        db = SessionLocal()
        try:
            node_count = db.query(func.count(KnowledgeNode.id)).scalar() or 0
            edge_count = db.query(func.count(KnowledgeEdge.id)).scalar() or 0

            type_distribution = db.execute(
                text("""
                    SELECT node_type, COUNT(*) as cnt
                    FROM knowledge_nodes
                    GROUP BY node_type
                    ORDER BY cnt DESC
                """)
            ).fetchall()

            edge_type_distribution = db.execute(
                text("""
                    SELECT edge_type, COUNT(*) as cnt
                    FROM knowledge_edges
                    GROUP BY edge_type
                    ORDER BY cnt DESC
                """)
            ).fetchall()

            latest_snap = db.query(KnowledgeGraphSnapshot).order_by(
                KnowledgeGraphSnapshot.created_at.desc()
            ).first()

            return {
                "node_count": node_count,
                "edge_count": edge_count,
                "node_type_distribution": {row[0]: row[1] for row in type_distribution},
                "edge_type_distribution": {row[0]: row[1] for row in edge_type_distribution},
                "average_degree": round(2 * edge_count / node_count, 2) if node_count else 0.0,
                "last_snapshot": {
                    "version": latest_snap.version,
                    "node_count": latest_snap.node_count,
                    "edge_count": latest_snap.edge_count,
                    "graph_hash": latest_snap.graph_hash,
                    "created_at": latest_snap.created_at.isoformat() if latest_snap.created_at else None,
                } if latest_snap else None,
            }
        finally:
            db.close()

    async def scan_project(self, project_root: str | None = None) -> int:
        """Auto-discover and scan project structure."""
        root = project_root or BACKEND_APP
        scanner = self.scanner
        try:
            _get_or_create_node(
                scanner.db,
                NodeType.PROJECT,
                "GULA Platform",
                "gula",
                description="GULA Medical Laboratory Platform — complete ecosystem map",
                source_path="backend/",
                tags=["gula", "platform", "lims"],
                version="2.1.0",
            )
            scanner.db.flush()
            count = scanner.scan_directory(root, "gula")
            scanner.commit()
            return count + 1
        except Exception:
            scanner.db.rollback()
            raise

    async def scan_backend_routes(self) -> int:
        """Discover and index all FastAPI routes."""
        scanner = self.scanner
        try:
            count = scanner.scan_route_patterns()
            scanner.commit()
            return count
        except Exception:
            scanner.db.rollback()
            raise

    async def scan_models(self) -> int:
        """Discover and index all SQLAlchemy models."""
        scanner = self.scanner
        try:
            count = scanner.scan_model_patterns()
            scanner.commit()
            return count
        except Exception:
            scanner.db.rollback()
            raise

    async def scan_events(self) -> int:
        """Discover and index all event definitions."""
        scanner = self.scanner
        try:
            count = scanner.scan_event_patterns()
            scanner.commit()
            return count
        except Exception:
            scanner.db.rollback()
            raise


engine = KnowledgeGraphEngine()
