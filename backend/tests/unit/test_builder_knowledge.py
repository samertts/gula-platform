"""Unit tests for GULA-BUILDER-001 Phase 6 — Knowledge Integration."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.knowledge import (
    KNOWLEDGE_SOURCES,
    KnowledgeError,
    collect,
    reuse_summary,
    search,
    search_memory,
)


class TestSearch:
    def test_returns_references(self):
        references = search("pytest import failure")
        assert references

    def test_sorted_by_relevance(self):
        references = search("pytest import failure")
        relevances = [ref.relevance for ref in references]
        assert relevances == sorted(relevances, reverse=True)

    def test_limit(self):
        assert len(search("pytest import failure", limit=3)) <= 3

    def test_empty_query_raises(self):
        with pytest.raises(KnowledgeError):
            search("   ")

    def test_source_filter(self):
        references = search("docker build", source="playbooks")
        assert references
        assert all(ref.source == "playbooks" for ref in references)

    def test_source_filter_no_match(self):
        assert search("zzzq", source="runbooks") == []

    def test_paths_are_relative(self):
        references = search("pytest import failure", limit=5)
        for ref in references:
            assert not pathlib.PurePath(ref.path).is_absolute()

    def test_matched_terms(self):
        references = search("pytest import failure", limit=5)
        assert all(ref.matched for ref in references)


class TestMemory:
    def test_search_memory(self):
        references = search_memory("checkpoint")
        assert isinstance(references, list)

    def test_collect_includes_memory(self):
        combined = collect("checkpoint")
        assert len(combined) >= len(search_memory("checkpoint"))

    def test_collect_excludes_memory_store(self):
        file_only = collect("pytest import failure", include_memory=False)
        assert all(ref.path != ".ai/core/memory/memory_store.json" for ref in file_only)


class TestSources:
    def test_known_sources(self):
        labels = {label for label, _path, _globs in KNOWLEDGE_SOURCES}
        assert {"skills", "playbooks", "runbooks", "adr", "registry", "memory", "constitution"} <= labels


class TestSummary:
    def test_summary_empty(self):
        assert "no reusable" in reuse_summary([])

    def test_summary_nonempty(self):
        references = search("pytest import failure", limit=2)
        text = reuse_summary(references)
        if references:
            assert references[0].source in text
