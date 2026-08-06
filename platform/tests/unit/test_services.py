import pytest


class TestWorkflowEngine:
    def test_define_and_execute(self, workflow_engine):
        from platform.core.workflow import StepResult, StepStatus, WorkflowStep

        class SimpleStep(WorkflowStep):
            async def execute(self, context):
                return StepResult(status=StepStatus.COMPLETED, data={"processed": True})

        workflow_engine.define("test_flow", [SimpleStep("step1")])
        import asyncio
        context = asyncio.run(workflow_engine.execute("test_flow"))
        assert context.get("processed") is True

    def test_unknown_workflow_raises(self, workflow_engine):
        import asyncio

        import pytest
        with pytest.raises(ValueError, match="Unknown workflow"):
            asyncio.run(workflow_engine.execute("does_not_exist"))

    def test_workflow_history(self, workflow_engine):
        from platform.core.workflow import StepResult, StepStatus, WorkflowStep

        class OkStep(WorkflowStep):
            async def execute(self, context):
                return StepResult(status=StepStatus.COMPLETED)

        workflow_engine.define("hist", [OkStep("s1")])
        import asyncio
        asyncio.run(workflow_engine.execute("hist"))
        history = workflow_engine.get_history("hist")
        assert len(history) == 1
        assert history[0]["steps"][0]["status"] == "completed"

    def test_step_failure_stops_workflow(self, workflow_engine):
        from platform.core.workflow import StepResult, StepStatus, WorkflowStep

        class FailStep(WorkflowStep):
            async def execute(self, context):
                return StepResult(status=StepStatus.FAILED, error="oops")

        class NeverRunStep(WorkflowStep):
            async def execute(self, context):
                pytest.fail("Should not run")

        workflow_engine.define("fail_flow", [FailStep("f1"), NeverRunStep("f2")])
        import asyncio
        asyncio.run(workflow_engine.execute("fail_flow"))
        history = workflow_engine.get_history("fail_flow")
        assert history[0]["steps"][0]["status"] == "failed"
        assert len(history[0]["steps"]) == 1

    def test_defined_workflows(self, workflow_engine):
        from platform.core.workflow import StepResult, StepStatus, WorkflowStep

        class DummyStep(WorkflowStep):
            async def execute(self, context):
                return StepResult(status=StepStatus.COMPLETED)

        workflow_engine.define("w1", [DummyStep("s1")])
        workflow_engine.define("w2", [DummyStep("s1")])
        assert sorted(workflow_engine.defined_workflows()) == sorted(["w1", "w2"])


class TestMetricsCollector:
    def test_counter_increment(self):
        from platform.core.observability import MetricsCollector
        m = MetricsCollector()
        m.increment("requests")
        m.increment("requests")
        assert m.get_counter("requests") == 2.0

    def test_counter_with_labels(self):
        from platform.core.observability import MetricsCollector
        m = MetricsCollector()
        m.increment("api_calls", labels={"method": "GET"})
        m.increment("api_calls", labels={"method": "POST"})
        assert m.get_counter("api_calls", labels={"method": "GET"}) == 1.0

    def test_gauge(self):
        from platform.core.observability import MetricsCollector
        m = MetricsCollector()
        m.gauge("memory_usage", 512.0)
        assert m.get_gauge("memory_usage") == 512.0

    def test_snapshot_structure(self):
        from platform.core.observability import MetricsCollector
        m = MetricsCollector()
        m.increment("req")
        m.gauge("mem", 100)
        snap = m.snapshot()
        assert "counters" in snap
        assert "gauges" in snap
        assert "histograms" in snap

    def test_reset(self):
        from platform.core.observability import MetricsCollector
        m = MetricsCollector()
        m.increment("req", 5)
        m.reset()
        assert m.get_counter("req") == 0.0


class TestTracer:
    def test_start_span(self):
        from platform.core.observability import Tracer
        t = Tracer("test")
        span = t.start_span("operation")
        assert span.name == "operation"
        assert span.trace_id is not None
        assert span.span_id is not None
        t.end_span(span)
        assert span.duration_ms is not None

    def test_trace_groups_spans(self):
        from platform.core.observability import Tracer
        t = Tracer("test")
        s1 = t.start_span("a")
        t.end_span(s1)
        s2 = t.start_span("b", trace_id=s1.trace_id)
        t.end_span(s2)
        trace = t.get_trace(s1.trace_id)
        assert len(trace) == 2

    def test_span_tags(self):
        from platform.core.observability import Tracer
        t = Tracer("test")
        span = t.start_span("tagged")
        span.set_tag("key", "value")
        assert span.tags["key"] == "value"
        t.end_span(span)
