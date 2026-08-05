"""Phase 9 — Knowledge Search.

Search every knowledge store (skills, playbooks, runbooks, memory) and
recommend the most relevant knowledge for any query. The recommendation
engine ranks matches by term overlap, and supports building an index and
retrieving top-N results. This is what lets a future mission start from
what the platform already knows instead of re-solving it.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.learner.core import read_json

SEARCH_ROOT = REPO_ROOT / ".ai" / "core"
SKILL_DIR = SEARCH_ROOT / "skills"
PLAYBOOK_DIR = SEARCH_ROOT / "playbooks"
RUNBOOK_DIR = SEARCH_ROOT / "runbooks"
MEMORY_DIR = SEARCH_ROOT / "memory"
INDEX_PATH = REPO_ROOT / ".ai" / "core" / "learner" / "search_index.json"
_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def build_index() -> Path:
    """Build a tokenized search index over all knowledge stores."""
    documents: list[dict] = []
    for kind, directory in _source_directories():
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            if path.is_relative_to(REPO_ROOT):
                relative = path.relative_to(REPO_ROOT).as_posix()
            else:
                relative = path.as_posix()
            documents.append({
                "kind": kind,
                "id": path.stem,
                "path": relative,
                "tokens": _tokens(text),
            })
    payload = {
        "documents": documents,
        "updated_at": None,
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return INDEX_PATH


def search(query: str, top_n: int = 5) -> list[dict]:
    """Return the top-N knowledge documents most relevant to the query."""
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    results: list[tuple[float, dict]] = []
    for doc in _load_documents():
        score = _rank(query_tokens, doc["tokens"])
        if score:
            results.append((score, doc))
    results.sort(key=lambda pair: pair[0], reverse=True)
    return [doc for _score, doc in results[:top_n]]


def recommendations(topic: str, top_n: int = 3) -> list[dict]:
    """Recommendations for a topic, filtered to reusable knowledge kinds."""
    results = search(topic, top_n=top_n * 2)
    ordered = sorted(results, key=lambda doc: 0 if doc["kind"] == "skill" else 1)
    return ordered[:top_n]


def _source_directories() -> Iterable[tuple[str, Path]]:
    return (
        ("skill", SKILL_DIR),
        ("playbook", PLAYBOOK_DIR),
        ("runbook", RUNBOOK_DIR),
        ("memory", MEMORY_DIR),
    )


def _load_documents() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    payload = read_json(INDEX_PATH)
    return payload.get("documents", [])


def _tokens(text: str) -> list[str]:
    lowered = text.lower()
    body = lowered.split("---", 2)[-1] if lowered.count("---") >= 2 else lowered
    return _TOKEN_RE.findall(body)


def _rank(query_tokens: set[str], document_tokens: list[str]) -> float:
    doc_counts: dict[str, int] = {}
    for token in document_tokens:
        doc_counts[token] = doc_counts.get(token, 0) + 1
    score = 0.0
    for token in query_tokens:
        if token in doc_counts:
            score += 1.0 + 0.1 * doc_counts[token]
    if not document_tokens:
        return 0.0
    return score / len(document_tokens)


def count_documents() -> int:
    return len(_load_documents())
