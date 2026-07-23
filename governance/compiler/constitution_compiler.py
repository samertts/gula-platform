from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from governance.compiler.models import (
    CompiledConstitution,
    ConstitutionalDocument,
    ConstitutionalRule,
    RuleCategory,
    RuleSeverity,
)


class ConstitutionCompiler:
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent

    CONSTITUTION_PATHS = [
        "docs/constitution/COST_GOVERNANCE.md",
        "docs/constitution/SYSTEM_CONSTITUTION.md",
        "docs/constitution/PLATFORM-CONSTITUTION.md",
        "docs/constitution/ENGINEERING_CONSTITUTION.md",
        "docs/architecture/FREE_FIRST_POLICY.md",
        "docs/architecture/OPEN_SOURCE_POLICY.md",
        "docs/architecture/VENDOR_LOCK_IN_POLICY.md",
        "docs/architecture/DEPENDENCY_APPROVAL_POLICY.md",
        "docs/architecture/ARCHITECTURE_RULES_PROGRAM_CONSTITUTION_001.md",
        "AGENTS.md",
        "CLAUDE.md",
        "ARCHITECTURE.md",
    ]

    RULE_PATTERNS: dict[str, tuple[RuleCategory, RuleSeverity]] = {
        "free first": (RuleCategory.FREE_FIRST, RuleSeverity.BLOCKER),
        "free solution": (RuleCategory.FREE_FIRST, RuleSeverity.BLOCKER),
        "open source first": (RuleCategory.OPEN_SOURCE_FIRST, RuleSeverity.HIGH),
        "open source": (RuleCategory.OPEN_SOURCE_FIRST, RuleSeverity.HIGH),
        "self-hosted first": (RuleCategory.SELF_HOSTED_FIRST, RuleSeverity.HIGH),
        "self hosted": (RuleCategory.SELF_HOSTED_FIRST, RuleSeverity.HIGH),
        "vendor lock-in": (RuleCategory.NO_VENDOR_LOCK_IN, RuleSeverity.BLOCKER),
        "vendor lock": (RuleCategory.NO_VENDOR_LOCK_IN, RuleSeverity.BLOCKER),
        "no vendor": (RuleCategory.NO_VENDOR_LOCK_IN, RuleSeverity.BLOCKER),
        "zero paid": (RuleCategory.ZERO_PAID_DEPENDENCY, RuleSeverity.BLOCKER),
        "paid dependency": (RuleCategory.ZERO_PAID_DEPENDENCY, RuleSeverity.HIGH),
        "paid software": (RuleCategory.ZERO_PAID_DEPENDENCY, RuleSeverity.HIGH),
        "reuse before build": (RuleCategory.REUSE_BEFORE_BUILD, RuleSeverity.BLOCKER),
        "never duplicate": (RuleCategory.REUSE_BEFORE_BUILD, RuleSeverity.HIGH),
        "local ai": (RuleCategory.LOCAL_AI_FIRST, RuleSeverity.HIGH),
        "ai inference": (RuleCategory.LOCAL_AI_FIRST, RuleSeverity.MEDIUM),
        "free security": (RuleCategory.FREE_SECURITY_FIRST, RuleSeverity.MEDIUM),
        "cost governance": (RuleCategory.COST_GOVERNANCE, RuleSeverity.HIGH),
        "lowest cost": (RuleCategory.COST_GOVERNANCE, RuleSeverity.MEDIUM),
        "platform sovereignty": (RuleCategory.PLATFORM_SOVEREIGNTY, RuleSeverity.BLOCKER),
        "self-hosted first": (RuleCategory.SELF_HOSTED_FIRST, RuleSeverity.HIGH),
        "security by design": (RuleCategory.SECURITY_BY_DESIGN, RuleSeverity.BLOCKER),
        "privacy by design": (RuleCategory.PRIVACY_BY_DESIGN, RuleSeverity.BLOCKER),
        "architecture before": (RuleCategory.ARCHITECTURE_BEFORE_IMPLEMENTATION, RuleSeverity.HIGH),
        "evidence based": (RuleCategory.EVIDENCE_BASED_DECISIONS, RuleSeverity.MEDIUM),
    }

    def __init__(self) -> None:
        self.documents: list[ConstitutionalDocument] = []
        self.rules: list[ConstitutionalRule] = []
        self.conflicts: list[dict[str, Any]] = []

    def compile_all(self) -> CompiledConstitution:
        for path in self.CONSTITUTION_PATHS:
            full_path = self.REPO_ROOT / path
            if full_path.exists():
                doc = self._compile_document(full_path, path)
                self.documents.append(doc)
                self.rules.extend(doc.rules)

        self._detect_conflicts()
        dep_graph = self._build_dependency_graph()
        inherit_tree = self._build_inheritance_tree()
        checksum = self._compute_checksum()

        return CompiledConstitution(
            documents=self.documents,
            rules=self.rules,
            checksum=checksum,
            version="1.0.0",
            compiled_at=datetime.now(timezone.utc).isoformat(),
            rule_count=len(self.rules),
            document_count=len(self.documents),
            conflict_count=len(self.conflicts),
            dependency_graph=dep_graph,
            inheritance_tree=inherit_tree,
        )

    def output_all(self) -> dict[str, str]:
        compiled = self.compile_all()
        return {
            "json": compiled.to_json(),
            "yaml": compiled.to_yaml(),
        }

    def _compile_document(self, full_path: Path, rel_path: str) -> ConstitutionalDocument:
        text = full_path.read_text(encoding="utf-8", errors="replace")
        checksum = hashlib.sha256(text.encode()).hexdigest()
        rules = self._extract_rules(text, rel_path)
        articles = self._extract_articles(text)

        version = self._extract_version(text) or "1.0.0"

        return ConstitutionalDocument(
            name=full_path.stem,
            path=rel_path,
            version=version,
            checksum=checksum,
            rules=rules,
            articles=articles,
            compiled_at=datetime.now(timezone.utc).isoformat(),
        )

    def _extract_rules(self, text: str, source: str) -> list[ConstitutionalRule]:
        rules: list[ConstitutionalRule] = []
        lines = text.splitlines()
        seen: set[str] = set()

        for i, line in enumerate(lines):
            lower = line.lower()
            for keyword, (category, severity) in self.RULE_PATTERNS.items():
                if keyword in lower:
                    rule_id = f"{category.value}_{len(rules) + 1:03d}"
                    if rule_id in seen:
                        continue
                    seen.add(rule_id)
                    article = self._find_current_article(lines, i)
                    context_lines = lines[max(0, i - 1): min(len(lines), i + 4)]
                    context = " ".join(c.strip() for c in context_lines if c.strip())

                    checks = self._extract_checks(context, category)
                    exceptions = self._extract_exceptions(context)

                    rules.append(ConstitutionalRule(
                        id=rule_id,
                        article=f"Article {article}" if article else "",
                        title=line.strip().strip("#").strip()[:100],
                        description=context[:200],
                        category=category,
                        severity=severity,
                        source_document=source,
                        checks=checks,
                        exceptions=exceptions,
                        enforcement=self._find_enforcement(lines, i),
                    ))
                    break

        return rules

    def _extract_articles(self, text: str) -> list[str]:
        articles: list[str] = []
        for line in text.splitlines():
            if re.match(r"^#{1,3}\s+(Article|Section|Rule)\s", line, re.IGNORECASE):
                articles.append(line.strip().lstrip("#").strip())
        return articles

    def _extract_version(self, text: str) -> str:
        match = re.search(r"(?:Version|version|v)[:\s]*(\d+\.\d+\.\d+)", text)
        return match.group(1) if match else ""

    def _find_current_article(self, lines: list[str], current: int) -> str:
        for i in range(current, -1, -1):
            match = re.match(r"^#{1,3}\s+(Article|Section)\s+(\d+)", lines[i], re.IGNORECASE)
            if match:
                return match.group(2)
        return ""

    def _extract_checks(self, context: str, category: RuleCategory) -> list[str]:
        checks: list[str] = []
        if "must" in context.lower():
            checks.append("Verify mandatory requirement is met")
        if "prohibit" in context.lower() or "never" in context.lower() or "shall not" in context.lower():
            checks.append("Verify prohibition is not violated")
        if category == RuleCategory.FREE_FIRST:
            checks.append("Scan for paid service references")
            checks.append("Verify free alternative evaluation exists")
        elif category == RuleCategory.OPEN_SOURCE_FIRST:
            checks.append("Verify license is OSI-approved")
            checks.append("Check for proprietary license references")
        elif category == RuleCategory.NO_VENDOR_LOCK_IN:
            checks.append("Scan for direct vendor SDK imports")
            checks.append("Verify abstraction layer exists")
        elif category == RuleCategory.ZERO_PAID_DEPENDENCY:
            checks.append("Check for paid dependency without ADR")
        elif category == RuleCategory.REUSE_BEFORE_BUILD:
            checks.append("Search existing codebase for duplicates")
        elif category == RuleCategory.SELF_HOSTED_FIRST:
            checks.append("Check for SaaS references")
        return checks

    def _extract_exceptions(self, context: str) -> list[str]:
        exceptions: list[str] = []
        exc_match = re.search(r"(?:unless|except|exception|exemption|waiver)[^.]*\.", context, re.IGNORECASE)
        if exc_match:
            exceptions.append(exc_match.group(0).strip())
        return exceptions

    def _find_enforcement(self, lines: list[str], current: int) -> str:
        for i in range(current, min(len(lines), current + 10)):
            if "enforce" in lines[i].lower() or "ci " in lines[i].lower() or "block" in lines[i].lower():
                return lines[i].strip()
        return "Architecture Review Board"

    def _detect_conflicts(self) -> None:
        self.conflicts = []
        for i, r1 in enumerate(self.rules):
            for r2 in self.rules[i + 1:]:
                if r1.category == r2.category and r1.severity != r2.severity:
                    self.conflicts.append({
                        "type": "severity_mismatch",
                        "rule1": r1.id,
                        "rule2": r2.id,
                        "description": f"Rule {r1.id} ({r1.severity.value}) conflicts with {r2.id} ({r2.severity.value})",
                    })

    def _build_dependency_graph(self) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        for doc in self.documents:
            deps: list[str] = []
            text = ""
            full_path = self.REPO_ROOT / doc.path
            if full_path.exists():
                text = full_path.read_text(encoding="utf-8", errors="replace")
            for other in self.documents:
                if other.name != doc.name and other.name.lower() in text.lower():
                    deps.append(other.name)
            graph[doc.name] = deps
        return graph

    def _build_inheritance_tree(self) -> dict[str, list[str]]:
        return {
            "PLATFORM-CONSTITUTION": [
                "SYSTEM_CONSTITUTION",
                "COST_GOVERNANCE",
                "ENGINEERING_CONSTITUTION",
            ],
            "COST_GOVERNANCE": [
                "FREE_FIRST_POLICY",
                "OPEN_SOURCE_POLICY",
                "VENDOR_LOCK_IN_POLICY",
                "DEPENDENCY_APPROVAL_POLICY",
            ],
            "SYSTEM_CONSTITUTION": [
                "ARCHITECTURE_RULES_PROGRAM_CONSTITUTION_001",
            ],
        }

    def _compute_checksum(self) -> str:
        combined = ""
        for doc in self.documents:
            combined += doc.checksum
        return hashlib.sha256(combined.encode()).hexdigest()

    def export_json(self, output_path: str | None = None) -> str:
        compiled = self.compile_all()
        data = compiled.to_dict()
        result = json.dumps(data, indent=2, ensure_ascii=False)
        if output_path:
            Path(output_path).write_text(result, encoding="utf-8")
        return result

    def export_yaml(self, output_path: str | None = None) -> str:
        compiled = self.compile_all()
        data = compiled.to_dict()
        result = yaml.dump(data, default_flow_style=False, allow_unicode=True)
        if output_path:
            Path(output_path).write_text(result, encoding="utf-8")
        return result

    def export_db(self, output_path: str | None = None) -> str:
        import sqlite3
        compiled = self.compile_all()
        db_path = output_path or str(self.REPO_ROOT / "governance" / "constitution.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS constitutional_rules (
                id TEXT PRIMARY KEY,
                article TEXT,
                title TEXT,
                description TEXT,
                category TEXT,
                severity TEXT,
                source_document TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS constitutional_documents (
                name TEXT PRIMARY KEY,
                path TEXT,
                version TEXT,
                checksum TEXT,
                compiled_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS rule_dependencies (
                rule_id TEXT,
                depends_on TEXT,
                FOREIGN KEY (rule_id) REFERENCES constitutional_rules(id)
            )
        """)
        for r in compiled.rules:
            cur.execute(
                "INSERT OR REPLACE INTO constitutional_rules VALUES (?,?,?,?,?,?,?)",
                (r.id, r.article, r.title, r.description, r.category.value, r.severity.value, r.source_document),
            )
        for d in compiled.documents:
            cur.execute(
                "INSERT OR REPLACE INTO constitutional_documents VALUES (?,?,?,?,?)",
                (d.name, d.path, d.version, d.checksum, d.compiled_at),
            )
        for r in compiled.rules:
            for dep in r.dependencies:
                cur.execute("INSERT OR REPLACE INTO rule_dependencies VALUES (?,?)", (r.id, dep))
        conn.commit()
        conn.close()
        return db_path

    def export_graph(self, output_path: str | None = None) -> str:
        compiled = self.compile_all()
        nodes: list[str] = []
        edges: list[str] = []
        for doc in compiled.documents:
            nodes.append(f'  "{doc.name}" [label="{doc.name}\\n{doc.version}\\n{doc.rule_count} rules"]')
        for parent, children in compiled.inheritance_tree.items():
            for child in children:
                edges.append(f'  "{parent}" -> "{child}"')
        dot = f"digraph Constitution {{\n  rankdir=LR;\n  node [shape=box, style=rounded];\n" + "\n".join(nodes) + "\n" + "\n".join(edges) + "\n}"
        if output_path:
            Path(output_path).write_text(dot, encoding="utf-8")
        return dot
