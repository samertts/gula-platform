from __future__ import annotations

import pytest

from app.ai_fabric.evaluation import (
    AIEvaluationHarness,
    ClinicalEvalSuite,
    EvalExample,
    EvalRunStatus,
    RAGEvaluationSuite,
)


def _mock_inference(prompt: str, model: str = "", system_prompt: str = "") -> dict:
    return {
        "text": f"Response to: {prompt[:50]}",
        "token_count": 50,
        "model": model,
    }


class TestAIEvaluationHarness:
    def test_register_and_run(self) -> None:
        harness = AIEvaluationHarness()
        examples = [
            EvalExample(input="test input", expected_output="test"),
        ]
        harness.register_suite("test_suite", examples)
        run = harness.run_suite("test_suite", "test-model", _mock_inference)
        assert run.status == EvalRunStatus.COMPLETED
        assert len(run.examples) == 1
        assert run.metrics["total_examples"] == 1

    def test_empty_suite(self) -> None:
        harness = AIEvaluationHarness()
        examples: list[EvalExample] = []
        harness.register_suite("empty", examples)
        run = harness.run_suite("empty", "test", _mock_inference)
        assert run.status == EvalRunStatus.COMPLETED
        assert run.metrics == {}

    def test_unknown_suite(self) -> None:
        harness = AIEvaluationHarness()
        with pytest.raises(ValueError, match="Unknown eval suite"):
            harness.run_suite("nonexistent", "test", _mock_inference)

    def test_scoring(self) -> None:
        harness = AIEvaluationHarness()
        examples = [
            EvalExample(input="what is hemoglobin", expected_output="completely unrelated answer here"),
            EvalExample(input="test2", expected_output=""),
        ]
        harness.register_suite("scoring", examples)
        run = harness.run_suite("scoring", "test", _mock_inference)
        assert run.examples[0].score < 1.0
        assert run.examples[1].score == 1.0  # no expected = always 1

    def test_rag_suite_registration(self) -> None:
        harness = AIEvaluationHarness()
        rag = RAGEvaluationSuite(harness)
        rag.register_all()
        summary = harness.summary()
        assert summary["status"] == "no_runs"

    def test_clinical_suite_registration(self) -> None:
        harness = AIEvaluationHarness()
        clinical = ClinicalEvalSuite(harness)
        clinical.register_all()
        summary = harness.summary()
        assert summary["status"] == "no_runs"

    def test_summary_after_runs(self) -> None:
        harness = AIEvaluationHarness()
        examples = [EvalExample(input="x", expected_output="x")]
        harness.register_suite("s1", examples)
        harness.run_suite("s1", "m1", _mock_inference)
        summary = harness.summary()
        assert summary["total_runs"] == 1
        assert summary["latest_run"]["suite"] == "s1"
        assert summary["latest_run"]["status"] == "completed"

    def test_multiple_runs(self) -> None:
        harness = AIEvaluationHarness()
        for i in range(3):
            examples = [EvalExample(input=f"test{i}", expected_output=f"out{i}")]
            harness.register_suite(f"suite_{i}", examples)
            harness.run_suite(f"suite_{i}", "m1", _mock_inference)
        assert len(harness.get_runs()) == 3
        assert len(harness.get_runs("suite_0")) == 1
