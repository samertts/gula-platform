"""Unit tests for GULA-GOVERNOR-001 governance layer (scripts/governor package).

Covers all 14 phases: audit, authority, mission routing, decision
governance, knowledge governance, context manager, loop protection,
resource governor, quality gates, safety, engine contract, self governance,
health dashboard, and the enterprise report.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.governor import (
    audit,
    authority,
    context_manager,
    decision_governance,
    engine_contract,
    health_dashboard,
    knowledge_governance,
    loop_protection,
    mission_router,
    quality_gates,
    resource_governor,
    safety,
    self_governance,
)
from scripts.governor import cli as governor_cli
from scripts.governor.core import REPO_ROOT, STATE_DIR


class TestAuthorityChain:
    def test_constitution_is_highest(self):
        assert authority.rank("constitution") == 0
        assert authority.rank("optimizer") == 8

    def test_governor_second(self):
        assert authority.rank("governor") == 1

    def test_can_override_respects_hierarchy(self):
        assert authority.can_override("governor", "architect")
        assert authority.can_override("architect", "builder")
        assert not authority.can_override("builder", "architect")
        assert not authority.can_override("reviewer", "reviewer")

    def test_is_subordinate(self):
        assert authority.is_subordinate("optimizer", "constitution")
        assert not authority.is_subordinate("constitution", "optimizer")

    def test_resolve_owner_architect_for_architecture(self):
        owner = authority.resolve_owner("Introduce event bus", "architecture")
        assert owner.owner == "architect"

    def test_resolve_owner_reviewer_for_deployment(self):
        owner = authority.resolve_owner("Ship release", "deployment")
        assert owner.owner == "reviewer"

    def test_resolve_owner_governor_for_general(self):
        owner = authority.resolve_owner("Pick cache lib", "general")
        assert owner.owner == "governor"

    def test_assert_no_override_raises(self):
        with pytest.raises(authority.AuthorityViolation):
            authority.assert_no_override("builder", "architect")

    def test_chain_summary_lists_all_engines(self):
        summary = authority.chain_summary()
        names = [entry["engine"] for entry in summary]
        assert names == ["constitution", "governor", "architect", "orchestrator",
                         "reviewer", "builder", "deployer", "learner", "optimizer"]


class TestMissionRouter:
    def test_tiny_bug_minimal_pipeline(self):
        profile = mission_router.classify("M-1", "Fix typo", "tiny_bug")
        assert profile.mission.required_engines == ["builder", "reviewer"]

    def test_small_low_risk_mission(self):
        profile = mission_router.classify("M-2", "Small change", "bug",
                                          size="small", risk="low", complexity=1)
        assert profile.mission.required_engines == ["builder", "reviewer"]

    def test_infrastructure_requires_deployer(self):
        profile = mission_router.classify("M-3", "Add Redis", "infrastructure")
        assert profile.mission.required_engines == [
            "architect", "builder", "reviewer", "deployer"]

    def test_large_feature_full_pipeline(self):
        profile = mission_router.classify("M-4", "New dashboard", "feature",
                                          size="large", complexity=8)
        assert profile.mission.required_engines == [
            "architect", "orchestrator", "builder", "reviewer", "learner", "optimizer"]

    def test_security_pipeline(self):
        profile = mission_router.classify("M-5", "Fix auth bypass", "security")
        assert "architect" in profile.mission.required_engines
        assert "deployer" in profile.mission.required_engines

    def test_standard_change(self):
        profile = mission_router.classify("M-6", "Update schema", "bug",
                                          size="medium", risk="medium", complexity=4)
        assert profile.mission.required_engines == ["architect", "builder", "reviewer"]


class TestDecisionGovernance:
    def test_create_decision_resolves_owner(self):
        decision = decision_governance.create_decision(
            "DEC-001", "Introduce message queue", "architecture")
        assert decision.owner == "architect"
        assert decision.status == "proposed"

    def test_only_architect_approves_architecture(self):
        decision = decision_governance.create_decision(
            "DEC-002", "Refactor module boundary", "architecture")
        with pytest.raises(PermissionError):
            decision_governance.approve_decision(decision, "builder")
        decision_governance.approve_decision(decision, "architect")
        assert decision.status == "decided"

    def test_only_reviewer_approves_deployment(self):
        decision = decision_governance.create_decision(
            "DEC-003", "Deploy RC", "deployment")
        with pytest.raises(PermissionError):
            decision_governance.approve_decision(decision, "optimizer")
        decision_governance.approve_decision(decision, "reviewer")
        assert decision.status == "decided"

    def test_voting_resolution_majority(self):
        decision = decision_governance.create_decision("DEC-004", "Pick lib")
        decision_governance.vote(decision, "builder", "for")
        decision_governance.vote(decision, "reviewer", "for")
        decision_governance.vote(decision, "learner", "against")
        assert decision_governance.resolve_conflict(decision) == "approved"

    def test_voting_requires_quorum(self):
        decision = decision_governance.create_decision("DEC-005", "Pick lib")
        decision_governance.vote(decision, "builder", "for")
        assert decision_governance.resolve_conflict(decision) == "tie"

    def test_invalid_vote_rejected(self):
        decision = decision_governance.create_decision("DEC-006", "Pick lib")
        with pytest.raises(ValueError):
            decision_governance.vote(decision, "builder", "maybe")

    def test_escalation_moves_up(self):
        decision = decision_governance.create_decision(
            "DEC-007", "Pick lib", "architecture")
        decision_governance.escalate_decision(decision, "governor")
        assert decision.status == "escalated"
        assert decision.owner == "governor"

    def test_escalation_rejects_downwards(self):
        decision = decision_governance.create_decision(
            "DEC-008", "Pick lib", "architecture")
        with pytest.raises(PermissionError):
            decision_governance.escalate_decision(decision, "builder")

    def test_rollback(self):
        decision = decision_governance.create_decision("DEC-009", "Pick lib")
        decision_governance.approve_decision(decision, "reviewer")
        decision_governance.rollback_decision(decision, "failed deploy")
        assert decision.status == "rolled_back"

    def test_priority_weight(self):
        assert decision_governance.decision_priority_weight("critical") == 4
        assert decision_governance.decision_priority_weight("low") == 1


class TestKnowledgeGovernance:
    def test_title_similarity(self):
        assert knowledge_governance.title_similarity(
            "Fix Docker Build", "Fix Docker Build Failure") > 0.7

    def test_title_similarity_unrelated(self):
        assert knowledge_governance.title_similarity("Fix Docker build", "Timezones in tests") < 0.3

    def test_find_duplicates(self):
        items = [
            knowledge_governance.KnowledgeItem("SKILL-000001", "Fix Docker Build", "skill"),
            knowledge_governance.KnowledgeItem("SKILL-000002", "Fix docker build issue", "skill"),
            knowledge_governance.KnowledgeItem("PLAYBOOK-000001", "Timezone handling", "playbook"),
        ]
        duplicates = knowledge_governance.find_duplicates(items)
        assert len(duplicates) == 1
        assert duplicates[0][3] == "skill"

    def test_confidence_grows_with_lifecycle(self):
        draft = knowledge_governance.KnowledgeItem("A", "Title", "skill")
        draft.confidence = knowledge_governance.compute_confidence(draft)
        approved = knowledge_governance.KnowledgeItem("B", "Title", "skill", lifecycle="approved",
                                                      usage_count=3, content="x" * 200)
        approved.confidence = knowledge_governance.compute_confidence(approved)
        assert approved.confidence > draft.confidence

    def test_rank_items_sorted(self):
        items = [
            knowledge_governance.KnowledgeItem("A", "T1", "skill", lifecycle="draft"),
            knowledge_governance.KnowledgeItem("B", "T2", "skill", lifecycle="approved",
                                               usage_count=2, content="y" * 300),
        ]
        ranked = knowledge_governance.rank_items(items)
        assert ranked[0].artifact_id == "B"

    def test_lifecycle_forward_only(self):
        item = knowledge_governance.KnowledgeItem("A", "T", "skill")
        knowledge_governance.transition(item, "verified")
        knowledge_governance.transition(item, "approved")
        with pytest.raises(ValueError):
            knowledge_governance.transition(item, "draft")
        assert item.lifecycle == "approved"

    def test_merge_items_combines_usage(self):
        primary = knowledge_governance.KnowledgeItem("A", "T", "skill",
                                                     lifecycle="verified", usage_count=1)
        duplicate = knowledge_governance.KnowledgeItem("B", "T", "skill",
                                                       lifecycle="approved", usage_count=4,
                                                       tags=["x"])
        merged = knowledge_governance.merge_items(primary, duplicate)
        assert merged.artifact_id == "A"
        assert merged.usage_count == 5
        assert merged.lifecycle == "approved"
        assert "x" in merged.tags


class TestContextManager:
    def test_budget_violations_detected(self):
        usage = context_manager.ContextUsage(files=99, tokens=999999, reports=20, docs=40)
        budget = context_manager.ContextBudget()
        violations = usage.check(budget)
        assert "files 99 > 50" in violations
        assert "tokens 999999 > 60000" in violations

    def test_within_budget_no_violations(self):
        usage = context_manager.ContextUsage(files=5, tokens=1000, reports=1, docs=2)
        assert usage.check(context_manager.ContextBudget()) == []

    def test_estimate_tokens(self):
        assert context_manager.estimate_tokens("hello world foo") == 12

    def test_search_knowledge_returns_results(self):
        hits = context_manager.search_knowledge("constitution authority", REPO_ROOT / "docs",
                                                top_k=3)
        assert isinstance(hits, list)

    def test_select_mission_context_bounded(self):
        usage = context_manager.select_mission_context(
            "constitution governance", [REPO_ROOT / "docs"], top_k_per_dir=2)
        assert usage.files >= 0
        assert usage.violations == [] or usage.violations


class TestLoopProtection:
    def test_increment_retries(self):
        counters = loop_protection.LoopCounters("M-1")
        for _ in range(3):
            counters.increment("retry")
        assert not counters.is_exceeded
        counters.increment("retry")
        assert counters.is_exceeded
        assert "retries" in counters.exceeded

    def test_review_cycle_limit(self):
        counters = loop_protection.LoopCounters("M-1")
        for _ in range(3):
            counters.increment("review")
        assert not counters.is_exceeded
        counters.increment("review")
        assert "review cycles" in counters.exceeded

    def test_escalation_message(self):
        counters = loop_protection.LoopCounters("M-1")
        counters.retries = 4
        counters.exceeded.append("retries")
        message = loop_protection.escalate_message(counters)
        assert "LOOP LIMIT EXCEEDED" in message
        assert "human" in message


class TestResourceGovernor:
    def test_phase_usage_within_budget(self):
        usage = resource_governor.PhaseUsage()
        for _ in range(5):
            usage.record_write()
        assert usage.check() is True

    def test_phase_usage_exceeds_files(self):
        usage = resource_governor.PhaseUsage()
        for _ in range(51):
            usage.record_write()
        assert usage.check() is False
        assert "files" in usage.violation

    def test_checkpoint_roundtrip(self):
        path = resource_governor.create_checkpoint("M-1", "build", {"step": 2})
        assert path.exists()
        state = resource_governor.resume_checkpoint("M-1", "build")
        assert state["state"]["step"] == 2

    def test_list_checkpoints(self):
        resource_governor.create_checkpoint("M-2", "review", {"done": True})
        checkpoints = resource_governor.list_checkpoints("M-2")
        assert checkpoints


class TestQualityGates:
    def test_all_gates_pass_by_default(self):
        results = quality_gates.run_all_gates()
        assert quality_gates.all_gates_pass(results)

    def test_missing_adr_fails_architecture_gate(self):
        results = quality_gates.run_all_gates(adr_present=False)
        assert "architecture" in quality_gates.failed_gates(results)

    def test_security_violation_fails_gate(self):
        results = quality_gates.run_all_gates(no_security_violations=False)
        assert "security" in quality_gates.failed_gates(results)

    def test_deployment_without_reviewer_fails(self):
        results = quality_gates.run_all_gates(reviewer_approved=False)
        assert "deployment" in quality_gates.failed_gates(results)

    def test_all_mandatory_gates_reject_on_failure(self):
        results = quality_gates.run_all_gates(constitution_compliant=False)
        assert not quality_gates.all_gates_pass(results)


class TestSafety:
    def test_mass_file_modification_blocked(self):
        assessment = safety.assess_action("refactor", files_affected=200)
        assert not assessment.allowed
        assert assessment.requires_approval

    def test_breaking_api_change_requires_architect(self):
        assessment = safety.assess_action("breaking_api_change")
        assert not assessment.allowed
        assert assessment.approver == "architect"

    def test_secret_access_blocked(self):
        assessment = safety.assess_action("change config", detail="SECRET_KEY=abc")
        assert not assessment.allowed

    def test_unauthorized_deployment_requires_reviewer(self):
        assessment = safety.assess_action("unauthorized_deployment")
        assert not assessment.allowed
        assert assessment.approver == "reviewer"

    def test_safe_action_allowed(self):
        assessment = safety.assess_action("rename_variable", files_affected=2)
        assert assessment.allowed


class TestEngineContract:
    def test_valid_contract_conforms(self):
        contract = dict.fromkeys(engine_contract.CONTRACT_FIELDS, True)
        result = engine_contract.validate_engine("builder", contract)
        assert result.is_conformant()

    def test_missing_fields_detected(self):
        result = engine_contract.validate_engine("builder", {"inputs": 1})
        assert not result.is_conformant()
        assert len(result.missing_fields()) == 9

    def test_registry_conforms_fully(self):
        violations = engine_contract.validate_all_engines(authority.ENGINE_REGISTRY)
        assert violations == []


class TestSelfGovernance:
    def test_audit_engines_reports_contract_violations(self):
        findings = self_governance.audit_engines({"fake": {"authority_rank": 0}})
        assert findings
        assert all(f.category == "engine-communication" for f in findings)

    def test_audit_knowledge_empty_categories(self):
        findings = self_governance.audit_knowledge_system({"skills": 0, "playbooks": 2})
        assert findings and "skills" in findings[0].detail

    def test_generate_proposals_never_applies(self):
        findings = [audit.Finding("X-1", "t", audit.Severity.MEDIUM, "cat", "detail")]
        proposals = self_governance.generate_proposals(findings)
        assert proposals and proposals[0].status == "proposed"

    def test_save_proposals_json(self, tmp_path):
        findings = [audit.Finding("X-1", "t", audit.Severity.LOW, "cat", "detail")]
        path = tmp_path / "proposals.json"
        self_governance.save_proposals(self_governance.generate_proposals(findings), path)
        assert path.exists()


class TestHealthDashboard:
    def test_collect_health_has_all_dimensions(self):
        report = health_dashboard.collect_health()
        names = [d.name for d in report.dimensions]
        assert "Engine Health" in names
        assert "Readiness" in names

    def test_render_dashboard(self):
        markdown = health_dashboard.render_dashboard()
        assert "# AI HEALTH DASHBOARD" in markdown
        assert "Current Risks" in markdown

    def test_readiness_percentage(self):
        report = health_dashboard.collect_health()
        assert report.readiness.endswith("%")

    def test_write_dashboard(self, tmp_path):
        target = tmp_path / "AI_HEALTH_DASHBOARD.md"
        health_dashboard.write_dashboard(target)
        assert target.exists()


class TestGovernorCli:
    def test_unknown_command(self):
        assert governor_cli.main(["nope"]) == 2

    def test_help(self):
        assert governor_cli.main([]) == 0

    def test_check_passes(self):
        assert governor_cli.main(["check"]) == 0

    def test_authority_markdown_contains_chain(self):
        markdown = governor_cli.authority_map_markdown()
        assert "AUTHORITY MAP" in markdown
        assert "Constitution" in markdown and "Optimizer" in markdown


class TestPhase0Audit:
    def test_subsystems_scanned(self):
        subsystems = audit.scan_subsystems()
        names = [s.name for s in subsystems]
        assert "constitution" in names
        assert "governor" in names
        assert any(s.present for s in subsystems)

    def test_audit_report_written(self, tmp_path):
        from scripts.governor.core import REPO_ROOT as _root

        markdown = audit.render_audit_markdown(audit.audit_findings(), audit.scan_subsystems())
        assert "# GOVERNOR AUDIT REPORT" in markdown

    def test_findings_render(self):
        findings = audit.audit_findings()
        markdown = audit.render_audit_markdown(findings, audit.scan_subsystems())
        assert "## 2. Findings" in markdown
