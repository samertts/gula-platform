"""Unit tests for GULA-KERNEL-001 Enterprise AI Execution Kernel.

Covers all 19 phases: audit, execution state, autonomy, engine contract,
mission scheduler, resource manager, lock manager, context engine, decision
engine, knowledge engine, safety engine, simulation engine, quality engine,
observability, failure recovery, technical debt, engine registry, self
diagnostics, and the enterprise report.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel import (
    audit,
    autonomy,
    context,
    contract,
    debt,
    decisions,
    diagnostics,
    knowledge,
    locks,
    observability,
    quality,
    recovery,
    registry,
    report,
    resource,
    safety,
    scheduler,
    simulation,
    state,
)
from scripts.kernel import cli as kernel_cli
from scripts.kernel.core import (
    AUTONOMY_LEVELS,
    ENGINE_REGISTRY,
    KERNEL_CONTRACT_FIELDS,
    REPO_ROOT,
    Lock,
    MissionStatus,
    Task,
    TaskStatus,
)


class TestPhase0Audit:
    def test_audit_findings_include_missing_or_dup(self):
        findings = audit.audit_findings()
        assert findings
        assert any(f.id.startswith("KRN-") for f in findings)

    def test_scan_subsystems_finds_kernel(self):
        subsystems = audit.scan_subsystems()
        kernel = next(s for s in subsystems if s.name == "kernel")
        assert kernel.present

    def test_duplicate_responsibilities_detected(self):
        findings = audit.find_duplicate_responsibilities()
        assert any(f.category == "architecture" for f in findings)

    def test_audit_markdown_renders(self):
        findings = audit.audit_findings()
        markdown = audit.render_audit_markdown(findings, audit.scan_subsystems())
        assert "KERNEL AUDIT REPORT" in markdown
        assert "Subsystem Inventory" in markdown


class TestPhase1ExecutionState:
    def test_start_mission_sets_context(self):
        current = state.load_state()
        current = state.start_mission(current, "M-1", "governor", "constitution")
        assert current.current_mission == "M-1"
        assert "M-1" in current.mission_history
        assert current.current_owner == "governor"
        assert current.current_authority == "constitution"

    def test_record_task_moves_buckets(self):
        current = state.load_state()
        task = Task("T-1", "M-1", "builder", status=TaskStatus.RUNNING.value)
        state.record_task(current, task)
        assert "T-1" in current.running_tasks
        task.status = TaskStatus.COMPLETED.value
        state.record_task(current, task)
        assert "T-1" in current.completed_tasks
        assert "T-1" not in current.running_tasks

    def test_checkpoint_pointer_updates(self):
        current = state.load_state()
        state.set_checkpoint_pointer(current, "build", "/tmp/cp.json")
        assert current.checkpoint_pointer == "build:/tmp/cp.json"

    def test_snapshot_summary(self):
        current = state.load_state()
        summary = state.snapshot_summary(current)
        assert summary["mission_status"] in {MissionStatus.QUEUED.value, MissionStatus.RUNNING.value}


class TestPhase2Autonomy:
    def test_level_order(self):
        assert autonomy.level_index("L0") == 0
        assert autonomy.level_index("L8") == 8

    def test_read_allowed_at_L0(self):
        assert autonomy.assess("read", "L0").allowed

    def test_write_blocked_below_L3(self):
        assert not autonomy.assess("write_file", "L2").allowed
        assert autonomy.assess("write_file", "L3").allowed

    def test_commit_requires_L4(self):
        assert autonomy.assess("commit", "L3").requires_approval
        assert autonomy.assess("commit", "L4").allowed

    def test_dangerous_always_requires_approval(self):
        assert autonomy.assess("dangerous_operation", "L8").requires_approval
        assert not autonomy.assess("dangerous_operation", "L8").allowed

    def test_approve_and_revoke(self):
        assert autonomy.approve("L3") == "L4"
        assert autonomy.revoke("L3") == "L2"

    def test_all_levels_present(self):
        assert len(AUTONOMY_LEVELS) == 9


class TestPhase3Contract:
    def test_all_engines_conform(self):
        assert contract.contract_violations(ENGINE_REGISTRY) == []

    def test_contract_has_16_fields(self):
        assert len(KERNEL_CONTRACT_FIELDS) == 16

    def test_engine_missing_field_detected(self):
        violations = contract.contract_violations({"builder": {"inputs": []}})
        assert any("builder" in v for v in violations)

    def test_missing_fields_reported(self):
        result = contract.validate_engine("x", {"inputs": []})
        assert "ownership" in result.missing_fields()


class TestPhase4Scheduler:
    def _tasks(self):
        return [
            Task("build", "M", "builder", dependencies=[], priority=2),
            Task("review", "M", "reviewer", dependencies=["build"], priority=1),
            Task("sim", "M", "simulation", dependencies=["build"], priority=1),
            Task("deploy", "M", "deployer", dependencies=["review"], priority=1),
        ]

    def test_priority_queue_order(self):
        queue = scheduler.PriorityQueue()
        queue.push(Task("low", "M", "b", priority=1))
        queue.push(Task("high", "M", "b", priority=5))
        assert queue.pop().task_id == "high"

    def test_execution_layers_parallelizable(self):
        layers = scheduler.execution_layers(self._tasks())
        assert layers == [["build"], ["review", "sim"], ["deploy"]]

    def test_cycle_detected(self):
        tasks = [
            Task("a", "M", "b", dependencies=["b"]),
            Task("b", "M", "b", dependencies=["a"]),
        ]
        assert scheduler.find_cycle(tasks)

    def test_critical_path(self):
        path = scheduler.critical_path(self._tasks())
        assert path[0] == "build"
        assert path[-1] == "deploy"

    def test_fair_schedule_interleaves_engines(self):
        tasks = [
            Task("a", "M", "builder", priority=1),
            Task("b", "M", "reviewer", priority=1),
            Task("c", "M", "builder", priority=1),
        ]
        order = scheduler.fair_schedule(tasks)
        assert [t.engine for t in order] == ["builder", "reviewer", "builder"]

    def test_mission_schedule_complete(self):
        plan = scheduler.mission_schedule("M", self._tasks())
        assert plan["status"] == "ready"
        assert plan["critical_path"]
        assert plan["execution_graph"]


class TestPhase5ResourceManager:
    def test_system_snapshot_fields(self):
        load = resource.monitor_system()
        assert 0.0 <= load.cpu_percent <= 100.0
        assert "disk_percent" in load.to_dict()

    def test_context_ratio(self):
        assert resource.context_usage_ratio(100, 200) == 0.5

    def test_split_work_respects_budget(self):
        phases = resource.split_work(list(range(7)), budget=__import__(
            "scripts.governor.resource_governor", fromlist=["PhaseBudget"]
        ).PhaseBudget(max_minutes=5, max_files=3))
        assert [len(phase) for phase in phases] == [3, 3, 1]

    def test_phase_usage_tracks_io(self):
        usage = resource.with_usage(["a", "b"])
        assert usage.file_reads == 2 and usage.file_writes == 2

    def test_checkpoint_roundtrip(self, tmp_path, monkeypatch):
        monkeypatch.setattr(resource, "create_checkpoint", lambda m, p, s: tmp_path / f"{m}__{p}.json")
        path = resource.phase_checkpoint("M", "build", {"x": 1})
        assert path.endswith(".json")


class TestPhase6LockManager:
    def test_acquire_and_release(self):
        manager = locks.LockManager()
        lock = manager.acquire("module_a", "module", "builder")
        assert manager.is_locked("module_a")
        assert manager.owner_of("module_a") == "builder"
        manager.release("module_a", "builder")
        assert not manager.is_locked("module_a")

    def test_conflict_raises(self):
        manager = locks.LockManager()
        manager.acquire("file_x", "file", "builder")
        with pytest.raises(locks.LockConflictError):
            manager.acquire("file_x", "file", "reviewer")

    def test_release_ownership_enforced(self):
        manager = locks.LockManager()
        manager.acquire("file_x", "file", "builder")
        with pytest.raises(PermissionError):
            manager.release("file_x", "reviewer")

    def test_auto_unlock_expired_ttl(self):
        manager = locks.LockManager()
        lock = manager.acquire("file_x", "file", "builder", ttl_seconds=1)
        lock.acquired_at = "2000-01-01T00:00:00+00:00"
        expired = manager.auto_unlock()
        assert expired == ["file_x"]

    def test_deadlock_detection(self):
        manager = locks.LockManager()
        manager.acquire("r1", "database", "A")
        manager.acquire("r2", "database", "B")
        pending = {"A": ("r2", "database"), "B": ("r1", "database")}
        cycle = manager.detect_deadlock(pending)
        assert cycle

    def test_resolve_conflict_preempts_high_priority(self):
        manager = locks.LockManager()
        manager.acquire("r1", "file", "builder")
        manager.resolve_conflict("r1", "architect", {"architect": 10, "builder": 5})
        assert not manager.is_locked("r1")


class TestPhase7ContextEngine:
    def test_lazy_load_and_cache(self, tmp_path):
        source = tmp_path / "doc.md"
        source.write_text("hello world kernel context", encoding="utf-8")
        engine = context.ContextEngine()
        engine.load(source)
        assert str(source) in engine.cached_files
        assert engine.token_usage > 0

    def test_auto_unload_evicts_lru(self):
        engine = context.ContextEngine()
        first = pathlib.Path("/tmp/kernel-a.md")
        second = pathlib.Path("/tmp/kernel-b.md")
        engine._cache = {
            str(first): context.CacheEntry(str(first), 10, 1),
            str(second): context.CacheEntry(str(second), 10, 2),
        }
        evicted = engine.auto_unload(keep=1)
        assert evicted == [str(first)]

    def test_compress_truncates(self):
        engine = context.ContextEngine()
        compressed = engine.compress("word " * 100, max_tokens=10)
        assert "compressed" in compressed

    def test_search_ranks_by_relevance(self, tmp_path):
        (tmp_path / "deployment.md").write_text("deployment pipeline deploy", encoding="utf-8")
        (tmp_path / "testing.md").write_text("testing unit tests quality", encoding="utf-8")
        engine = context.ContextEngine()
        hits = engine.search("deployment", tmp_path, top_k=2)
        assert hits and hits[0][0].name == "deployment.md"


class TestPhase8DecisionEngine:
    def test_decision_confidence_and_risk(self):
        record = decisions.decide("D-1", "Add auth", "security", "high", evidence_points=5)
        assert record.confidence > 0.5
        assert record.risk > 0.5
        assert record.risk_level in {"high", "medium"}

    def test_simulation_failure_for_risky_decision(self):
        record = decisions.decide("D-2", "Deploy", "deployment", "critical", evidence_points=1)
        record.risk = 0.9
        record.risk_level = "high"
        decisions.simulate(record, scenario="adverse")
        assert record.simulated_outcome == "failed"

    def test_simulation_success(self):
        record = decisions.decide("D-3", "Refactor util", "general", "low", evidence_points=5)
        decisions.simulate(record)
        assert record.simulated_outcome == "succeeded"

    def test_commit_and_rollback_trace(self):
        record = decisions.decide("D-4", "Ship feature", "general", "medium")
        decisions.commit(record, "governor")
        assert record.decision.status == "decided"
        decisions.rollback(record, "test failed")
        assert record.decision.status == "rolled_back"
        assert any("rolled_back" in t for t in record.trace)


class TestPhase9KnowledgeEngine:
    def _artifacts(self):
        from scripts.governor.knowledge_governance import KnowledgeItem

        return [
            knowledge.KnowledgeArtifact(
                KnowledgeItem("K-1", "Deployment runbook", "runbook", "approved", 0.9, "deploy content"),
                dependencies=["K-2"],
            ),
            knowledge.KnowledgeArtifact(
                KnowledgeItem("K-2", "Rollback runbook", "runbook", "verified", 0.7, "rollback content"),
            ),
        ]

    def test_search_ranks_matching_artifact(self):
        results = knowledge.search(self._artifacts(), "deployment", top_k=2)
        assert results[0].artifact_id == "K-1"

    def test_dependency_graph(self):
        graph = knowledge.dependency_graph(self._artifacts())
        assert graph["K-1"] == ["K-2"]

    def test_health_check_counts_lifecycle(self):
        health = knowledge.health_check(self._artifacts())
        assert health["total"] == 2
        assert health["lifecycle_counts"]["approved"] == 1

    def test_validate_reports_violations(self):
        from scripts.governor.knowledge_governance import KnowledgeItem

        bad = knowledge.KnowledgeArtifact(KnowledgeItem("", "", lifecycle="invalid"))
        assert knowledge.validate(bad)

    def test_archive_moves_to_archived(self):
        from scripts.governor.knowledge_governance import KnowledgeItem

        artifact = knowledge.KnowledgeArtifact(KnowledgeItem("K-9", "Old", lifecycle="deprecated"))
        knowledge.archive(artifact)
        assert artifact.item.lifecycle == "archived"


class TestPhase10SafetyEngine:
    def test_dangerous_command_denied(self):
        assert not safety.assess_command("git push --force").allowed
        assert not safety.assess_command("rm -rf /").allowed

    def test_mass_modification_requires_approval(self):
        assert safety.check_mass_modification(51).requires_approval
        assert safety.check_mass_modification(10).allowed

    def test_unauthorized_deployment_blocked(self):
        assert safety.check_unauthorized_deployment(reviewer_approved=False).requires_approval
        assert safety.check_unauthorized_deployment(reviewer_approved=True).allowed

    def test_secret_exposure_blocked(self):
        assessment = safety.assess_action("write_config", detail="PASSWORD=supersecret")
        assert assessment.requires_approval

    def test_loop_counters_trigger_safety(self):
        from scripts.governor.loop_protection import LoopCounters

        counters = LoopCounters("M")
        for _ in range(4):
            counters.increment("retry")
        assessment = safety.assess_action("retry_task", counters=counters)
        assert assessment.requires_approval

    def test_architecture_violation_blocked(self):
        assert safety.check_architecture_violation(architect_approved=False).requires_approval


class TestPhase11SimulationEngine:
    def test_simulation_passes(self):
        result = simulation.simulate_mission("SIM-1", [
            {"kind": "file", "path": "a.py", "content": "x"},
            {"kind": "db", "table": "users", "row": {"id": 1}},
            {"kind": "assert", "pass": True},
        ])
        assert result.passed
        assert len(result.steps) == 3

    def test_simulation_stops_on_failure(self):
        result = simulation.simulate_mission("SIM-2", [
            {"kind": "file", "path": "a.py"},
            {"kind": "assert", "pass": False},
            {"kind": "file", "path": "b.py"},
        ])
        assert not result.passed
        assert len(result.steps) == 2

    def test_infrastructure_budget(self):
        infra = simulation.VirtualInfrastructure(cpu_available=1.0)
        assert not infra.consume(cpu=5.0, memory=1.0, disk=1.0)

    def test_virtual_db_rollback(self):
        database = simulation.VirtualDatabase()
        database.insert("users", {"id": 1})
        snapshot = database.snapshot()
        database.insert("users", {"id": 2})
        database.rollback(snapshot)
        assert len(database.query("users")) == 1

    def test_require_pass_raises_on_failure(self):
        result = simulation.SimulationResult("SIM-3", passed=False, failures=["x"])
        with pytest.raises(RuntimeError):
            simulation.require_simulation_pass(result)


class TestPhase12QualityEngine:
    def test_nine_gates(self):
        results = quality.run_quality_gates()
        assert len(results) == 9
        names = {gate.name for gate in results}
        assert "governance" in names
        assert "constitution" in names

    def test_all_pass_by_default(self):
        assert quality.all_pass(quality.run_quality_gates())

    def test_failed_gate_detected(self):
        results = quality.run_quality_gates(tests_pass=False)
        assert "testing" in quality.failed(results)
        assert not quality.all_pass(results)

    def test_require_pass_raises(self):
        results = quality.run_quality_gates(constitution_compliant=False)
        with pytest.raises(RuntimeError):
            quality.require_pass(results)


class TestPhase13Observability:
    def test_metrics_summary(self):
        metrics = observability.MetricsRegistry()
        metrics.record("missions", 1)
        metrics.record("missions", 3)
        assert metrics.summary("missions")["mean"] == 2.0

    def test_tracer_spans(self):
        tracer = observability.Tracer()
        tracer.start("s1", "build", "builder")
        tracer.end("s1", duration_ms=12.5)
        spans = tracer.export()
        assert spans[0]["duration_ms"] == 12.5

    def test_audit_trail_searchable(self):
        audit_log = observability.AuditLog()
        audit_log.record("kernel", "check")
        audit_log.record("builder", "write")
        assert len(audit_log.find(actor="builder")) == 1

    def test_timeline_ordered(self):
        timeline = observability.Timeline()
        timeline.event("start")
        timeline.event("end")
        assert len(timeline.export()) == 2

    def test_graphs(self):
        assert observability.knowledge_graph(["a"], {"a": ["b"]})["edges"] == [["a", "b"]]
        assert observability.decision_graph(["d"], {"d": "approved"})["edges"] == [["d", "approved"]]

    def test_suite_export(self):
        suite = observability.ObservabilitySuite()
        export = suite.export()
        assert set(export) == {"metrics", "spans", "audit", "timeline"}


class TestPhase14Recovery:
    def test_failure_classification(self):
        assert recovery.classify_failure("connection timeout") == "transient"
        assert recovery.classify_failure("permission denied") == "security"
        assert recovery.classify_failure("strange unknown error") == "permanent"

    def test_human_approval_for_security(self):
        assert recovery.requires_human_approval("security")
        assert not recovery.requires_human_approval("transient")

    def test_retry_strategy_for_transient(self):
        from scripts.governor.loop_protection import LoopCounters

        plan = recovery.plan_recovery("M", "transient", LoopCounters("M"))
        assert plan["strategy"] == "retry"

    def test_rollback_strategy_for_permanent(self):
        from scripts.governor.loop_protection import LoopCounters

        plan = recovery.plan_recovery("M", "permanent", LoopCounters("M"))
        assert plan["strategy"] == "rollback"

    def test_retry_bounded(self):
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            recovery.retry(flaky, recovery.RetryPolicy(max_retries=2, backoff_seconds=0))
        assert calls["n"] == 3

    def test_incident_record_and_resolve(self, tmp_path, monkeypatch):
        monkeypatch.setattr(recovery, "INCIDENTS_FILE", tmp_path / "incidents.json")
        incident = recovery.Incident("INC-1", "M", "security", "denied")
        recovery.record_incident(incident)
        loaded = recovery.load_incidents()
        assert loaded[0].incident_id == "INC-1"
        resolved = recovery.resolve_incident("INC-1", "human approved")
        assert resolved.resolved


class TestPhase15Debt:
    def _module(self, lines=10, docstring=True, todo=0):
        return debt.ModuleStats("mod.py", lines, docstring, todo, 0, 0)

    def test_large_modules(self):
        findings = debt.large_modules([self._module(lines=600)])
        assert len(findings) == 1
        assert findings[0].category == "large-modules"

    def test_todo_density(self):
        findings = debt.todo_density([self._module(todo=5)])
        assert findings[0].category == "maintainability-debt"

    def test_missing_docstring(self):
        findings = debt.missing_docstrings([self._module(docstring=False)])
        assert len(findings) == 1

    def test_dead_code_detection(self):
        graph = {"main": ["a"], "a": ["b"], "orphan": []}
        findings = debt.dead_code(graph, ["main"])
        assert [f.title for f in findings] == ["Dead module: orphan"]

    def test_knowledge_drift(self):
        findings = debt.knowledge_drift(["K-1"], ["K-2"])
        assert findings[0].category == "knowledge-drift"

    def test_dependency_drift(self):
        findings = debt.dependency_drift(["requests"], ["flask"])
        assert findings[0].category == "dependency-drift"

    def test_configuration_drift(self):
        findings = debt.configuration_drift(["DATABASE_URL"], [])
        assert findings[0].category == "configuration-drift"

    def test_architecture_drift(self):
        findings = debt.architecture_drift([["a", "b", "a"]])
        assert findings[0].category == "architecture-drift"

    def test_duplicate_blocks(self):
        blocks = debt.extract_duplicate_blocks({
            "a.py": "def f():\n    return 1\n    x = 2\n    y = 3\n    z = 4\n",
            "b.py": "def f():\n    return 1\n    x = 2\n    y = 3\n    z = 4\n",
        })
        findings = debt.duplicate_code(blocks)
        assert findings[0].category == "duplicate-code"

    def test_security_debt(self):
        module = debt.ModuleStats("s.py", 5, True, 0, secret_pattern_count=1, nested_loop_count=0)
        findings = debt.security_debt([module])
        assert findings[0].category == "security-debt"


class TestPhase16Registry:
    def test_capabilities_matrix(self):
        caps = registry.capabilities()
        assert "builder" in caps
        assert caps["builder"]

    def test_version_matrix(self):
        versions = registry.version_matrix()
        assert all(versions.values())

    def test_health_matrix(self):
        assert registry.health_matrix()["builder"] == "healthy"

    def test_ownership_matrix(self):
        ownership = registry.ownership_matrix()
        assert "deployment-approval" in ownership["reviewer"]

    def test_all_matrices_complete(self):
        matrices = registry.all_matrices()
        assert set(matrices) == {
            "capabilities", "compatibility", "versions", "health",
            "ownership", "communication", "dependencies",
        }

    def test_render_matrices(self):
        markdown = registry.render_matrices()
        assert "ENGINE REGISTRY" in markdown
        assert "Version Matrix" in markdown


class TestPhase17Diagnostics:
    def test_audit_components_all_present(self):
        audits = diagnostics.audit_components()
        assert all(audit.present for audit in audits)
        assert all(audit.health == "healthy" for audit in audits)

    def test_audit_components_present_regardless_of_cwd(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        audits = diagnostics.audit_components()
        assert all(audit.present for audit in audits)
        assert all(audit.health == "healthy" for audit in audits)

    def test_engine_contract_findings_empty(self):
        assert diagnostics.audit_engine_contract() == []

    def test_registry_health_findings(self):
        findings = diagnostics.audit_registry_health({"x": {}})
        assert any(f.category == "registry" for f in findings)

    def test_run_diagnostics_and_proposals(self):
        proposals = diagnostics.diagnose_and_propose()
        assert isinstance(proposals, list)


class TestPhase18Report:
    def test_phase_coverage_full(self):
        implemented, coverage = report.phase_coverage()
        assert implemented == 19
        assert coverage == 100.0

    def test_readiness_score(self):
        readiness = report.compute_readiness()
        assert readiness["score"] == 100.0
        assert readiness["grade"] == "A"

    def test_implementation_markdown(self):
        markdown = report.implementation_markdown()
        assert "KERNEL IMPLEMENTATION REPORT" in markdown
        assert "Phase 18" in markdown

    def test_operating_status_markdown(self):
        markdown = report.operating_status_markdown()
        assert "AI OPERATING STATUS" in markdown
        assert "Engine Status Matrix" in markdown

    def test_write_enterprise_report(self, monkeypatch, tmp_path):
        monkeypatch.setattr(report, "REPO_ROOT", tmp_path)
        paths = report.write_enterprise_report()
        assert len(paths) == 3
        assert all(pathlib.Path(p).exists() for p in paths)


class TestKernelCli:
    def test_unknown_command(self):
        assert kernel_cli.main(["nope"]) == 2

    def test_help(self):
        assert kernel_cli.main(["--help"]) == 0

    def test_check_passes(self):
        assert kernel_cli.main(["check"]) == 0

    def test_report_generates_files(self, monkeypatch, tmp_path):
        monkeypatch.setattr(report, "REPO_ROOT", tmp_path)
        assert kernel_cli.main(["report"]) == 0

    def test_audit_writes_report(self, monkeypatch, tmp_path):
        monkeypatch.setattr(kernel_cli, "_AUDIT_PATH", tmp_path / "KERNEL_AUDIT_REPORT.md")
        assert kernel_cli.main(["audit"]) == 0
        assert (tmp_path / "KERNEL_AUDIT_REPORT.md").exists()
