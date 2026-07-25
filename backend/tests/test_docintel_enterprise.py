from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path

import pytest
from app.document_intelligence.backup_dr import BackupEntry, BackupScheduler, BackupService
from app.document_intelligence.distributed.batch_processor import BatchProcessor
from app.document_intelligence.distributed.partition_manager import PartitionManager
from app.document_intelligence.distributed.task_queue import (
    Task,
    TaskPriority,
    TaskQueue,
    TaskStatus,
)
from app.document_intelligence.distributed.worker_pool import WorkerPool
from app.document_intelligence.multitenancy import (
    QuotaManager,
    Tenant,
    TenantContext,
    TenantManager,
)
from app.document_intelligence.observability import (
    AlertManager,
    HealthChecker,
    MetricsCollector,
    StructuredLogger,
    Tracer,
    get_metrics,
)
from app.document_intelligence.performance import (
    AsyncMemoizer,
    BatchAggregator,
    ConnectionPool,
    LRUCache,
    ProcessingTimeTracker,
)
from app.document_intelligence.security import (
    AuditLogger,
    EncryptionService,
    InputValidator,
    IntegrityChecker,
    RateLimiter,
)

# ═══════════════════════════════════════════════════════════════════
# DISTRIBUTED TASK QUEUE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestTaskQueue:
    @pytest.mark.asyncio
    async def test_enqueue_and_execute(self):
        queue = TaskQueue(max_concurrent=5)
        results = []

        async def test_handler(task: Task) -> str:
            results.append(task.payload.get("value"))
            return f"done-{task.payload.get('value')}"

        queue.register_handler("test_task", test_handler)
        await queue.start()

        task = Task(name="test_task", payload={"value": 42})
        await queue.enqueue(task)
        await asyncio.sleep(0.1)

        assert len(results) == 1
        assert results[0] == 42

        completed = queue._completed.get(task.id)
        assert completed is not None
        assert completed.status == TaskStatus.completed

        await queue.stop()

    @pytest.mark.asyncio
    async def test_task_priority(self):
        queue = TaskQueue(max_concurrent=10)
        results = []

        async def handler(task: Task):
            results.append(task.payload.get("priority"))
            return

        queue.register_handler("prio", handler)
        await queue.start()

        for i in range(5):
            prio = TaskPriority.urgent if i == 0 else TaskPriority.low
            await queue.enqueue(Task(name="prio", payload={"priority": i}, priority=prio))

        await asyncio.sleep(0.2)
        assert len(results) == 5
        await queue.stop()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        queue = TaskQueue()
        stats = queue.get_stats()
        assert "pending" in stats
        assert "running" in stats
        assert "completed" in stats
        assert "failed" in stats

    def test_task_defaults(self):
        task = Task(name="test")
        assert task.status == TaskStatus.pending
        assert task.priority == TaskPriority.normal
        assert task.retry_count == 0
        assert task.max_retries == 3

    @pytest.mark.asyncio
    async def test_cancel_pending(self):
        queue = TaskQueue()
        task = Task(name="test")
        await queue.enqueue(task)
        cancelled = await queue.cancel(task.id)
        assert cancelled is True
        assert task.status == TaskStatus.cancelled


class TestBatchProcessor:
    @pytest.mark.asyncio
    async def test_process_batch(self):
        processor = BatchProcessor(batch_size=10)
        processed = []

        async def processor_fn(item: int) -> int:
            processed.append(item)
            return item * 2

        job = await processor.process_batch(list(range(25)), processor_fn)
        assert job.total == 25
        assert job.completed == 25
        assert job.failed == 0
        assert len(processed) == 25

    @pytest.mark.asyncio
    async def test_get_job(self):
        processor = BatchProcessor()
        job = await processor.process_batch([1, 2, 3], lambda x: x)
        retrieved = processor.get_job(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id

    def test_all_jobs(self):
        processor = BatchProcessor()
        assert isinstance(processor.all_jobs(), list)


class TestWorkerPool:
    @pytest.mark.asyncio
    async def test_submit_and_process(self):
        pool = WorkerPool(min_workers=2, max_workers=5)
        await pool.start()
        results = []

        async def worker(item: int) -> None:
            results.append(item)

        await pool.submit(worker, 1)
        await pool.submit(worker, 2)
        await pool.submit(worker, 3)
        await asyncio.sleep(0.2)

        assert len(results) == 3
        await pool.stop()

    @pytest.mark.asyncio
    async def test_worker_pool_stats(self):
        pool = WorkerPool(min_workers=2, max_workers=5)
        await pool.start()
        assert pool.total_workers == 2
        assert pool.queue_size == 0
        await pool.stop()


class TestPartitionManager:
    def test_get_partition(self):
        pm = PartitionManager(num_partitions=16)
        doc_id = str(uuid.uuid4())
        partition = pm.get_partition(doc_id)
        assert 0 <= partition < 16

    def test_consistent_partition(self):
        pm = PartitionManager()
        doc_id = str(uuid.uuid4())
        p1 = pm.get_partition(doc_id)
        p2 = pm.get_partition(doc_id)
        assert p1 == p2

    def test_assign_and_get_worker(self):
        pm = PartitionManager()
        doc_id = str(uuid.uuid4())
        partition = pm.get_partition(doc_id)
        pm.assign_worker(partition, "worker-1")
        assert pm.get_worker(doc_id) == "worker-1"

    def test_rebalance(self):
        pm = PartitionManager(num_partitions=16)
        pm.rebalance(["worker-a", "worker-b"])
        stats = pm.get_stats()
        assert stats["active_workers"] == 2
        assert stats["total_partitions"] == 16


# ═══════════════════════════════════════════════════════════════════
# MULTI-TENANCY TESTS
# ═══════════════════════════════════════════════════════════════════


class TestTenantManager:
    def test_register_and_get(self):
        mgr = TenantManager()
        tenant = Tenant(id="lab-1", name="Lab One")
        mgr.register_tenant(tenant)
        assert mgr.get_tenant("lab-1") is tenant
        assert mgr.tenant_exists("lab-1") is True

    def test_list_tenants(self):
        mgr = TenantManager()
        mgr.register_tenant(Tenant(id="a", name="A"))
        mgr.register_tenant(Tenant(id="b", name="B"))
        assert len(mgr.list_tenants()) == 2

    def test_unregister(self):
        mgr = TenantManager()
        mgr.register_tenant(Tenant(id="x", name="X"))
        mgr.unregister_tenant("x")
        assert mgr.tenant_exists("x") is False


class TestTenantContext:
    def test_set_and_get(self):
        assert TenantContext.get() is None
        TenantContext.set("lab-1")
        assert TenantContext.get() == "lab-1"
        TenantContext.clear()
        assert TenantContext.get() is None

    def test_context_isolation(self):
        TenantContext.set("tenant-a")
        val_a = TenantContext.get()

        async def nested():
            TenantContext.set("tenant-b")
            return TenantContext.get()

        val_b = asyncio.run(nested())
        assert val_a == "tenant-a"
        assert val_b == "tenant-b"


class TestQuotaManager:
    @pytest.mark.asyncio
    async def test_check_quota(self):
        mgr = TenantManager()
        mgr.register_tenant(Tenant(id="t1", name="T1", quotas={"documents": 5}))
        qm = QuotaManager(mgr)

        for _ in range(5):
            assert await qm.check_quota("t1", "documents") is True
            await qm.increment_usage("t1", "documents")

        assert await qm.check_quota("t1", "documents") is False

    @pytest.mark.asyncio
    async def test_unlimited_quota(self):
        mgr = TenantManager()
        mgr.register_tenant(Tenant(id="t2", name="T2"))
        qm = QuotaManager(mgr)
        assert await qm.check_quota("t2", "anything") is True


# ═══════════════════════════════════════════════════════════════════
# BACKUP/DR TESTS
# ═══════════════════════════════════════════════════════════════════


class TestBackupService:
    @pytest.mark.asyncio
    async def test_create_and_restore(self):
        service = BackupService(backup_dir="/tmp/docintel_test_backups")
        entries = [
            BackupEntry(key="doc-1", data=b"hello world"),
            BackupEntry(key="doc-2", data=b"test data"),
        ]
        manifest = await service.create_backup(entries)
        assert manifest.status == "completed"
        assert manifest.entries == 2
        assert manifest.size_bytes > 0

        restored = await service.restore_backup(manifest.id)
        assert len(restored) == 2
        assert restored[0].key == "doc-1"
        assert restored[0].data == b"hello world"

    @pytest.mark.asyncio
    async def test_verify_backup(self):
        service = BackupService(backup_dir="/tmp/docintel_test_backups")
        entries = [BackupEntry(key="k1", data=b"data")]
        manifest = await service.create_backup(entries)
        assert await service.verify_backup(manifest.id) is True

    @pytest.mark.asyncio
    async def test_list_backups(self):
        service = BackupService(backup_dir="/tmp/docintel_test_backups")
        entries = [BackupEntry(key="k1", data=b"data")]
        await service.create_backup(entries)
        await service.create_backup(entries)
        assert len(service.list_backups()) == 2

    @pytest.mark.asyncio
    async def test_restore_nonexistent(self):
        service = BackupService(backup_dir="/tmp/docintel_test_backups")
        with pytest.raises(ValueError):
            await service.restore_backup("nonexistent-id")


class TestBackupScheduler:
    @pytest.mark.asyncio
    async def test_add_and_remove_schedule(self):
        scheduler = BackupScheduler()
        calls = []

        async def backup_fn():
            calls.append("ran")
            from app.document_intelligence.backup_dr import BackupManifest

            return BackupManifest()

        scheduler.add_schedule("hourly", 3600, backup_fn)
        assert len(scheduler.get_schedules()) == 1
        scheduler.remove_schedule("hourly")
        assert len(scheduler.get_schedules()) == 0


# ═══════════════════════════════════════════════════════════════════
# OBSERVABILITY TESTS
# ═══════════════════════════════════════════════════════════════════


class TestMetricsCollector:
    def test_counter(self):
        m = MetricsCollector()
        m.increment("docs.processed")
        m.increment("docs.processed", 5)
        snap = m.snapshot()
        assert snap["counters"]["docs.processed"] == 6

    def test_gauge(self):
        m = MetricsCollector()
        m.gauge("queue.size", 42)
        snap = m.snapshot()
        assert snap["gauges"]["queue.size"] == 42

    def test_histogram(self):
        m = MetricsCollector()
        for v in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            m.histogram("latency", v)
        snap = m.snapshot()
        assert snap["histograms"]["latency"]["min"] == 1
        assert snap["histograms"]["latency"]["max"] == 10
        assert snap["histograms"]["latency"]["count"] == 10

    def test_reset(self):
        m = MetricsCollector()
        m.increment("count")
        m.reset()
        snap = m.snapshot()
        assert snap["counters"] == {}


class TestTracer:
    @pytest.mark.asyncio
    async def test_start_end_span(self):
        tracer = Tracer()
        span = tracer.start_span("ocr.process")
        await asyncio.sleep(0.01)
        tracer.end_span(span.id)
        assert span.duration_ms > 0
        assert span.status == "ok"

    def test_span_with_parent(self):
        tracer = Tracer()
        parent = tracer.start_span("parent")
        child = tracer.start_span("child")
        assert child.parent_id == parent.id
        tracer.end_span(child.id)
        tracer.end_span(parent.id)

    def test_get_trace(self):
        tracer = Tracer()
        parent = tracer.start_span("root")
        child = tracer.start_span("leaf")
        tracer.end_span(child.id)
        tracer.end_span(parent.id)
        trace = tracer.get_trace(child.id)
        assert len(trace) >= 2

    def test_add_event(self):
        tracer = Tracer()
        span = tracer.start_span("test")
        tracer.add_event(span.id, "error", {"msg": "timeout"})
        assert len(span.events) == 1
        tracer.end_span(span.id)

    @pytest.mark.asyncio
    async def test_trace_decorator(self):
        tracer = Tracer()

        @tracer.trace("my_operation")
        async def my_func():
            return 42

        result = await my_func()
        assert result == 42


class TestHealthChecker:
    @pytest.mark.asyncio
    async def test_healthy(self):
        hc = HealthChecker()

        async def db_check():
            return {"ok": True, "latency_ms": 5}

        async def redis_check():
            return {"ok": True, "latency_ms": 2}

        hc.register("database", db_check)
        hc.register("redis", redis_check)

        result = await hc.run_all()
        assert result["status"] == "healthy"
        assert result["checks"]["database"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_unhealthy(self):
        hc = HealthChecker()

        async def failing():
            raise RuntimeError("Connection refused")

        hc.register("db", failing)
        result = await hc.run_all()
        assert result["status"] == "degraded"

    def test_is_healthy_empty(self):
        hc = HealthChecker()
        assert hc.is_healthy() is True


class TestStructuredLogger:
    def test_log_methods(self):
        logger = StructuredLogger(service_name="test_svc")
        logger.info("test message", extra="data")
        logger.error("error message")
        logger.warning("warning")
        logger.debug("debug")
        logger.critical("critical")


class TestAlertManager:
    @pytest.mark.asyncio
    async def test_evaluate_triggers(self):
        am = AlertManager()

        async def high_errors(metrics):
            return metrics.get("counters", {}).get("errors", 0) > 10

        am.add_rule("high_errors", high_errors, severity="critical", message="Too many errors")
        alerts = await am.evaluate({"counters": {"errors": 15}})
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "critical"

        alerts2 = await am.evaluate({"counters": {"errors": 5}})
        assert len(alerts2) == 0

    def test_get_alerts(self):
        am = AlertManager()
        assert isinstance(am.get_alerts(), list)

    def test_clear_alerts(self):
        am = AlertManager()
        am._alerts.append({"test": True})
        am.clear_alerts()
        assert len(am._alerts) == 0


# ═══════════════════════════════════════════════════════════════════
# SECURITY TESTS
# ═══════════════════════════════════════════════════════════════════


class TestInputValidator:
    def test_sanitize_string(self):
        assert InputValidator.sanitize_string("  hello  ") == "hello"
        assert InputValidator.sanitize_string("a" * 20000) == "a" * 10000
        assert InputValidator.sanitize_string(123) == ""

    def test_sanitize_filename(self):
        assert InputValidator.sanitize_filename("report.pdf") == "report.pdf"
        assert InputValidator.sanitize_filename("../etc/passwd") == "unnamed_file"
        assert InputValidator.sanitize_filename(".hidden") == "unnamed_file"
        assert InputValidator.sanitize_filename(".....") == "unnamed_file"

    def test_is_valid_uuid(self):
        assert InputValidator.is_valid_uuid(str(uuid.uuid4())) is True
        assert InputValidator.is_valid_uuid("not-a-uuid") is False

    def test_validate_email(self):
        assert InputValidator.validate_email("user@example.com") is True
        assert InputValidator.validate_email("not-an-email") is False

    def test_validate_national_id(self):
        assert InputValidator.validate_national_id("123456789012") is True
        assert InputValidator.validate_national_id("12345") is False

    def test_strip_html(self):
        assert InputValidator.strip_html("<script>alert('xss')</script>") == "alert('xss')"

    def test_sanitize_dict(self):
        data = {"key": "value", "nested": {"inner": "deep"}}
        result = InputValidator.sanitize_dict(data)
        assert result["key"] == "value"


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_rate_limit(self):
        rl = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert await rl.check("user-1") is True
        assert await rl.check("user-1") is False

    @pytest.mark.asyncio
    async def test_remaining(self):
        rl = RateLimiter(max_requests=10, window_seconds=60)
        remaining = await rl.remaining("user-1")
        assert remaining == 10

    def test_reset(self):
        rl = RateLimiter()
        rl._buckets["key"] = [time.time()]
        rl.reset("key")
        assert "key" not in rl._buckets
        rl._buckets["k1"] = []
        rl._buckets["k2"] = []
        rl.reset()
        assert rl._buckets == {}


class TestAuditLogger:
    @pytest.mark.asyncio
    async def test_log_entry(self):
        al = AuditLogger()
        entry = await al.log(
            action="view",
            entity_type="document",
            entity_id="doc-123",
            actor="user-1",
            changes={"status": "viewed"},
        )
        assert entry["action"] == "view"
        assert entry["entity_type"] == "document"
        assert entry["actor"] == "user-1"

    def test_get_entries(self):
        al = AuditLogger()
        asyncio.run(al.log("create", "doc", "1", "user"))
        entries = al.get_entries("1")
        assert len(entries) == 1

    def test_search(self):
        al = AuditLogger()
        asyncio.run(al.log("delete", "doc", "2", "admin", metadata={"reason": "cleanup"}))
        results = al.search("cleanup")
        assert len(results) == 1


class TestIntegrityChecker:
    @pytest.mark.asyncio
    async def test_add_and_verify(self):
        ic = IntegrityChecker()
        await ic.add_entry({"type": "ocr_result", "doc_id": "123"})
        await ic.add_entry({"type": "classification", "doc_id": "123"})
        assert ic.verify_chain() is True
        assert ic.get_latest_hash() != "0" * 64

    @pytest.mark.asyncio
    async def test_tamper_detection(self):
        ic = IntegrityChecker()
        await ic.add_entry({"type": "ocr"})
        await ic.add_entry({"type": "classify"})
        ic._chain[1]["hash"] = "tampered"
        assert ic.verify_chain() is False


class TestEncryptionService:
    def test_encrypt_decrypt(self):
        svc = EncryptionService(key=b"0123456789abcdef0123456789abcdef")
        data = b"sensitive patient data"
        encrypted = svc.encrypt(data)
        assert encrypted != data
        decrypted = svc.decrypt(encrypted)
        assert decrypted == data


# ═══════════════════════════════════════════════════════════════════
# PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════════


class TestLRUCache:
    def test_set_and_get(self):
        cache = LRUCache(maxsize=10, ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_expiry(self):
        cache = LRUCache(maxsize=100, ttl_seconds=0)
        cache.set("key1", "value1")
        assert cache.get("key1") is None

    def test_maxsize_eviction(self):
        cache = LRUCache(maxsize=3, ttl_seconds=60)
        for i in range(5):
            cache.set(f"key{i}", f"value{i}")
        assert cache.size() <= 3

    def test_contains(self):
        cache = LRUCache()
        cache.set("k", "v")
        assert cache.contains("k") is True
        assert cache.contains("missing") is False

    def test_delete(self):
        cache = LRUCache()
        cache.set("k", "v")
        cache.delete("k")
        assert cache.get("k") is None

    def test_clear(self):
        cache = LRUCache()
        cache.set("a", "1")
        cache.set("b", "2")
        cache.clear()
        assert cache.size() == 0

    def test_keys(self):
        cache = LRUCache()
        cache.set("a", "1")
        cache.set("b", "2")
        keys = cache.keys()
        assert "a" in keys
        assert "b" in keys


class TestAsyncMemoizer:
    @pytest.mark.asyncio
    async def test_memoize(self):
        memoizer = AsyncMemoizer(maxsize=100, ttl=60)
        call_count = 0

        @memoizer.memoize
        async def expensive_func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        assert await expensive_func(5) == 10
        assert call_count == 1
        assert await expensive_func(5) == 10
        assert call_count == 1
        assert await expensive_func(10) == 20
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_invalidate_all(self):
        memoizer = AsyncMemoizer()
        call_count = 0

        @memoizer.memoize
        async def fn(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x

        await fn(1)
        await fn(2)
        assert call_count == 2
        memoizer.invalidate()
        await fn(1)
        assert call_count == 3


class TestConnectionPool:
    @pytest.mark.asyncio
    async def test_acquire_release(self):
        pool = ConnectionPool(min_size=1, max_size=5)
        conn = await pool.acquire()
        assert conn is not None
        assert pool.in_use_count == 1
        await pool.release(conn)
        assert pool.in_use_count == 0
        assert pool.available_count == 1

    @pytest.mark.asyncio
    async def test_pool_size(self):
        pool = ConnectionPool(min_size=2, max_size=10)
        conns = []
        for _ in range(5):
            conns.append(await pool.acquire())
        assert pool.size == 5
        for conn in conns:
            await pool.release(conn)
        assert pool.size == 5

    @pytest.mark.asyncio
    async def test_pool_exhaustion(self):
        pool = ConnectionPool(min_size=1, max_size=2)
        c1 = await pool.acquire()
        c2 = await pool.acquire()
        with pytest.raises(RuntimeError, match="Connection pool exhausted"):
            await pool.acquire()
        await pool.release(c1)
        await pool.release(c2)


class TestBatchAggregator:
    @pytest.mark.asyncio
    async def test_aggregate_and_flush(self):
        aggregator = BatchAggregator(max_batch_size=100, flush_interval=0.1)
        flushed = []

        async def handler(items: list[int]) -> None:
            flushed.extend(items)

        aggregator.register_handler("test_type", handler)
        await aggregator.start()

        await aggregator.add("test_type", 1)
        await aggregator.add("test_type", 2)
        await aggregator.add("test_type", 3)
        await asyncio.sleep(0.3)

        assert len(flushed) == 3
        await aggregator.stop()


class TestProcessingTimeTracker:
    @pytest.mark.asyncio
    async def test_track_time(self):
        tracker = ProcessingTimeTracker()

        async def slow_op():
            await asyncio.sleep(0.01)
            return 42

        result = await tracker.track("slow_op", slow_op)
        assert result == 42
        stats = tracker.get_stats("slow_op")
        assert stats["slow_op"]["count"] == 1
        assert stats["slow_op"]["min_ms"] > 0

    def test_get_stats_empty(self):
        tracker = ProcessingTimeTracker()
        assert tracker.get_stats("nonexistent") == {}

    def test_reset(self):
        tracker = ProcessingTimeTracker()
        tracker._timings["op1"] = [10.0, 20.0]
        tracker.reset("op1")
        assert "op1" not in tracker._timings
