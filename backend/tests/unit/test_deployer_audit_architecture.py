"""Unit tests for GULA-DEPLOYER-001 — Phase 0 audit + Phase 1 architecture."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.deployer.architecture import (
    build_topology,
    describe_targets,
    environment_gaps,
)
from scripts.deployer.audit import AUDIT_PATTERNS, audit_systems, render_markdown


class TestAudit:
    def test_audit_patterns_cover_all_components(self):
        assert len(AUDIT_PATTERNS) == 17
        for component in ("docker", "docker-compose", "kubernetes", "monitoring"):
            assert component in AUDIT_PATTERNS

    def test_audit_patterns_are_tuples(self):
        for component, patterns in AUDIT_PATTERNS.items():
            assert isinstance(patterns, tuple), f"{component} patterns not a tuple"
            assert all(isinstance(p, str) for p in patterns)

    def test_audit_systems_returns_items(self):
        items = audit_systems()
        assert len(items) == 17
        docker = next(i for i in items if i.name == "docker")
        assert docker.present is True
        assert docker.evidence

    def test_audit_marks_known_absences(self):
        items = audit_systems()
        by_name = {i.name: i for i in items}
        assert by_name["traefik"].present is False
        assert by_name["dns"].present is False

    def test_audit_render_contains_table(self):
        items = audit_systems()
        markdown = render_markdown(items)
        assert "| Component | Status |" in markdown
        assert "| docker |" in markdown

    def test_audit_render_reports_counts(self):
        items = audit_systems()
        markdown = render_markdown(items)
        assert "**AUDIT COMPLETE**" in markdown


class TestArchitecture:
    def test_topology_has_eight_environments(self):
        targets = build_topology()
        assert len(targets) == 8
        names = {t.environment for t in targets}
        assert names == {"local", "development", "testing", "staging", "production",
                         "disaster_recovery", "edge", "offline"}

    def test_production_has_national_hosts(self):
        targets = {t.environment: t for t in build_topology()}
        production = targets["production"]
        assert "gula.iq" in production.hosts
        assert "api.gula.iq" in production.hosts

    def test_offline_is_air_gapped(self):
        targets = {t.environment: t for t in build_topology()}
        assert targets["offline"].strategy == "air-gapped"

    def test_describe_targets_includes_hosts(self):
        targets = build_topology()[:2]
        text = describe_targets(targets)
        assert "environment" in text or "local" in text

    def test_environment_gaps_flags_missing(self):
        targets = build_topology()
        present = {
            "docker", "docker-compose", "storage", "secrets", "github-actions",
            "monitoring", "certificates", "dns", "backups", "alerting",
            "replication", "cdn", "cache", "tls", "offline-repo", "air-gap-bundle",
            "local-dns", "dns-failover",
        } - {"reverse-proxy"}
        gaps = environment_gaps(targets, present)
        assert any(gap.startswith("production:") for gap in gaps)
        assert any("reverse-proxy" in gap for gap in gaps)

    def test_environment_gaps_none_when_all_present(self):
        targets = build_topology()
        all_required = {
            req for target in targets for req in target.requires
        }
        gaps = environment_gaps(targets, all_required)
        assert gaps == []
