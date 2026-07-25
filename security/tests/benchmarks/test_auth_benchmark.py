from __future__ import annotations

import os

import pytest


class TestJWTBenchmark:
    def bench_jwt_create(self, benchmark, auth_fixtures):
        jwt = auth_fixtures["jwt"]
        result = benchmark(jwt.create_access_token, "user-001", {"role": "admin"})
        assert result is not None

    def bench_jwt_verify(self, benchmark, auth_fixtures):
        jwt = auth_fixtures["jwt"]
        token = jwt.create_access_token("user-001", {"role": "admin"})
        result = benchmark(jwt.verify_access_token, token)
        assert result is not None

    def bench_jwt_with_claims(self, benchmark, auth_fixtures):
        jwt = auth_fixtures["jwt"]
        claims = {f"claim_{i}": f"value_{i}" for i in range(20)}
        result = benchmark(jwt.create_access_token, "user-001", claims)
        assert result is not None


class TestRBACBenchmark:
    def bench_rbac_check(self, benchmark, auth_fixtures):
        rbac = auth_fixtures["rbac"]
        rbac.assign_role("user-001", "admin")
        rbac.grant_permission("admin", "read")
        result = benchmark(rbac.check_permission, "user-001", "read")
        assert result is True

    def bench_rbac_large_roleset(self, benchmark, auth_fixtures):
        rbac = auth_fixtures["rbac"]
        for i in range(100):
            rbac.assign_role(f"user-{i}", f"role-{i % 10}")
            rbac.grant_permission(f"role-{i % 10}", f"perm-{i % 50}")
        result = benchmark(rbac.check_permission, "user-050", "perm-25")
        assert result is True or result is False


class TestAuditBenchmark:
    def bench_audit_create(self, benchmark, audit_fixtures):
        audit = audit_fixtures["audit"]
        from security.modules.audit.models import AuditEvent

        def create():
            audit.create_event(AuditEvent(
                actor_id="user-001", action="data.access",
                resource_type="patient", resource_id="pat-001",
            ))

        benchmark(create)

    def bench_audit_query(self, benchmark, audit_fixtures):
        audit = audit_fixtures["audit"]
        from security.modules.audit.models import AuditEvent
        from security.modules.audit.service import AuditQuery

        for i in range(100):
            audit.create_event(AuditEvent(
                actor_id=f"user-{i % 10}", action="data.read",
                resource_type="patient", resource_id=f"pat-{i}",
            ))

        query = AuditQuery(actor_id="user-001", limit=10)
        result = benchmark(audit.query_events, query)
        assert len(result) > 0

    def bench_immutable_append(self, benchmark, audit_fixtures):
        immutable_log = audit_fixtures["immutable"]
        from security.modules.audit.models import AuditEvent

        def append():
            immutable_log.append(AuditEvent(
                event_id=f"evt-{os.urandom(4).hex()}",
                actor_id="user-001", action="data.access",
                resource_type="patient", resource_id="pat-001",
            ))

        benchmark(append)

    def bench_audit_export(self, benchmark, audit_fixtures):
        audit = audit_fixtures["audit"]
        from security.modules.audit.models import AuditEvent

        for i in range(100):
            audit.create_event(AuditEvent(
                actor_id=f"user-{i}", action="data.read",
                resource_type="patient", resource_id=f"pat-{i}",
            ))
        result = benchmark(audit.export_events, "json")
        assert result is not None
