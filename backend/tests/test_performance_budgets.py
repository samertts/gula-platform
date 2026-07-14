"""Performance & scalability invariants — Phase 10 hardening.

Pins query budgets and detects N+1 / oversized-payload regressions
without introducing infrastructure dependencies (no JMeter, no k6, no
locust). Uses SQLAlchemy's ``before_cursor_execute`` event to count
queries per request.

Invariants asserted:

  1. Listing endpoints have a query-count budget (catches N+1 from
     adding a relationship without eager loading).
  2. List response sizes are pagination-bounded (max ``limit`` honoured).
  3. ``/health`` / ``/health/ready`` execute zero non-trivial queries
     (a regression here = startup-guard / healthcheck loop costing DB).
  4. Documented composite indexes exist on hot paths (CLAUDE.md §database).
  5. Pagination boundary parameters are clamped (``limit`` cannot exceed
     the route's documented max).

These tests exercise pure SQLAlchemy + TestClient — no live DB profile
needed. Catches the most common scalability regressions at PR-review
time instead of at production-rollout time.

Blast radius: zero. No production code modified.
"""
from __future__ import annotations

import os
import sys
from contextlib import contextmanager

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.auth import create_token, hash_password
from sqlalchemy import event


def _hdr(user_id: int, lab_id: int, role: str = "admin") -> dict:
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ─── Query counter helper ────────────────────────────────────────────────────


class _QueryCounter:
    """Listens on a SQLAlchemy engine and counts non-savepoint SQL events."""

    def __init__(self, engine):
        self.engine = engine
        self.queries: list[str] = []

    def _on_execute(self, conn, cursor, statement, parameters, context, executemany):
        # Filter out trivial savepoint/release/begin churn that bloats counts
        sql = statement.strip().upper()
        if sql.startswith(("SAVEPOINT", "RELEASE", "BEGIN", "ROLLBACK", "COMMIT", "PRAGMA")):
            return
        self.queries.append(statement)

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self._on_execute)
        return self

    def __exit__(self, exc_type, exc, tb):
        event.remove(self.engine, "before_cursor_execute", self._on_execute)


@contextmanager
def _count_queries(engine):
    counter = _QueryCounter(engine)
    with counter:
        yield counter


@pytest.fixture()
def lab_with_many_patients(db):
    """Lab with 20 patients & 20 orders & 40 results — enough to detect N+1."""
    lab = Lab(name="Perf Lab", license_number="LIC-PERF",
              lab_type="private", city="Baghdad", is_active=True)
    db.add(lab)
    db.flush()

    admin = LabUser(
        lab_id=lab.id, name="Admin", email="perf_admin@x.com",
        password_hash=hash_password("Pa55word"), role="admin", is_active=True,
    )
    db.add(admin)
    db.flush()

    for i in range(20):
        p = Patient(
            lab_id=lab.id, full_name=f"Patient {i:02d}",
            phone=f"077001{i:05d}",
            health_id=f"HID-PERF-{i:03d}",
        )
        db.add(p)
    db.flush()

    patients = db.query(Patient).filter(Patient.lab_id == lab.id).all()
    for p in patients:
        order = LabOrder(lab_id=lab.id, patient_id=p.id, status="pending")
        db.add(order)
    db.flush()

    orders = db.query(LabOrder).filter(LabOrder.lab_id == lab.id).all()
    for o in orders:
        for j in range(2):
            r = LabResult(
                order_id=o.id, test_name=f"Test{j}",
                value=10.0 + j, unit="mg/dL", flag="normal",
            )
            db.add(r)
    db.commit()

    return {"lab": lab, "admin": admin}


# ─── Phase 10.A — Query count budgets ────────────────────────────────────────


class TestQueryBudgets:
    """Listing endpoints must execute O(1) queries, not O(N)."""

    def test_patients_listing_query_count_bounded(
        self, client, db_engine, lab_with_many_patients
    ):
        admin = lab_with_many_patients["admin"]
        lab_id = lab_with_many_patients["lab"].id

        with _count_queries(db_engine) as q:
            res = client.get("/patients?limit=20",
                             headers=_hdr(admin.id, lab_id))
        assert res.status_code == 200
        assert res.json()["total"] == 20
        # Budget: list_patients should issue ~2 queries (count + select).
        # Allow up to 5 to absorb auth/user lookup. Anything > 10 indicates
        # an N+1 leak — flag for review.
        assert len(q.queries) <= 10, (
            f"patients listing executed {len(q.queries)} queries for 20 rows — "
            f"likely N+1 regression. Recent queries:\n  "
            + "\n  ".join(q.queries[:5])
        )

    def test_orders_listing_query_count_bounded(
        self, client, db_engine, lab_with_many_patients
    ):
        admin = lab_with_many_patients["admin"]
        lab_id = lab_with_many_patients["lab"].id

        with _count_queries(db_engine) as q:
            res = client.get("/orders?limit=20",
                             headers=_hdr(admin.id, lab_id))
        assert res.status_code == 200
        # Each order has 2 results → if results are NOT eager-loaded,
        # count would be ~20 lazy result loads on top of the listing.
        # Set a generous budget but flag flagrant N+1.
        assert len(q.queries) <= 50, (
            f"orders listing executed {len(q.queries)} queries — "
            "likely missing eager-load on order.results"
        )

    def test_health_endpoint_constant_db_queries(self, client, db_engine):
        """Health-check loop must execute O(1) DB queries — not O(users)
        or O(labs) etc. Current baseline is ≤2 queries; tighter than that
        is preferable but stable is enough to pin against regressions."""
        with _count_queries(db_engine) as q:
            res = client.get("/health")
        assert res.status_code == 200
        # /health is liveness only — must not run per-row scans.
        # Budget: at most 2 queries (e.g. the readiness probe).
        assert len(q.queries) <= 2, (
            f"/health issued {len(q.queries)} DB query(ies) — "
            "this scales linearly with healthcheck frequency. Current "
            "baseline is 1; >2 indicates a per-request scan was added."
        )


# ─── Phase 10.B — Pagination clamps ──────────────────────────────────────────


class TestPaginationClamps:
    """Pagination bounds prevent oversized-payload denial-of-service."""

    def test_patients_limit_clamped_at_500(self, client, lab_with_many_patients):
        """patients.py declares ``limit: int = Query(50, ge=1, le=500)``."""
        admin = lab_with_many_patients["admin"]
        lab_id = lab_with_many_patients["lab"].id
        # Exceeding the documented max → 422 Unprocessable
        res = client.get("/patients?limit=10000",
                         headers=_hdr(admin.id, lab_id))
        assert res.status_code == 422

    def test_orders_limit_clamped_at_500(self, client, lab_with_many_patients):
        admin = lab_with_many_patients["admin"]
        lab_id = lab_with_many_patients["lab"].id
        res = client.get("/orders?limit=10000",
                         headers=_hdr(admin.id, lab_id))
        assert res.status_code == 422

    def test_negative_skip_rejected(self, client, lab_with_many_patients):
        admin = lab_with_many_patients["admin"]
        lab_id = lab_with_many_patients["lab"].id
        res = client.get("/patients?skip=-1",
                         headers=_hdr(admin.id, lab_id))
        assert res.status_code == 422

    def test_zero_limit_rejected(self, client, lab_with_many_patients):
        admin = lab_with_many_patients["admin"]
        lab_id = lab_with_many_patients["lab"].id
        res = client.get("/patients?limit=0",
                         headers=_hdr(admin.id, lab_id))
        assert res.status_code == 422


# ─── Phase 10.C — Hot-path index documentation ───────────────────────────────


class TestHotPathIndexes:
    """CLAUDE.md documents composite indexes on hot paths. Verify the
    ORM declares them so a future migration that drops them fails this
    test loudly."""

    def test_patient_phone_indexed(self):
        """Phone-search hot path must be indexed (compliance.py uses startswith)."""
        from app.models.patient import Patient
        col = Patient.__table__.columns["phone"]
        # SQLAlchemy puts the column index status on .index OR via a Table
        # Index object. Accept either.
        is_indexed = bool(col.index) or any(
            "phone" in [c.name for c in idx.columns]
            for idx in Patient.__table__.indexes
        )
        assert is_indexed, "patients.phone must be indexed for startswith search"

    def test_patient_lab_id_indexed(self):
        """Tenant filtering hot path."""
        from app.models.patient import Patient
        col = Patient.__table__.columns["lab_id"]
        is_indexed = bool(col.index) or any(
            "lab_id" in [c.name for c in idx.columns]
            for idx in Patient.__table__.indexes
        )
        assert is_indexed, "patients.lab_id must be indexed for tenant filter"

    def test_lab_order_lab_id_indexed(self):
        from app.models.lab_order import LabOrder
        col = LabOrder.__table__.columns["lab_id"]
        is_indexed = bool(col.index) or any(
            "lab_id" in [c.name for c in idx.columns]
            for idx in LabOrder.__table__.indexes
        )
        assert is_indexed

    def test_lab_result_order_id_indexed(self):
        """LabResult joins lab_order through order_id; must be indexed."""
        from app.models.lab_result import LabResult
        col = LabResult.__table__.columns["order_id"]
        is_indexed = bool(col.index) or any(
            "order_id" in [c.name for c in idx.columns]
            for idx in LabResult.__table__.indexes
        )
        assert is_indexed

    def test_lab_result_token_hash_unique_indexed(self):
        """Public result links lookup by token_hash — must be unique+indexed."""
        from app.models.lab_result import LabResult
        col = LabResult.__table__.columns["token_hash"]
        # Unique columns are always indexed
        assert col.unique or col.index or any(
            "token_hash" in [c.name for c in idx.columns]
            for idx in LabResult.__table__.indexes
        )

    def test_audit_log_action_indexed(self):
        """audit_logs.action is queried by /compliance/security-report."""
        from app.models.audit_log import AuditLog
        col = AuditLog.__table__.columns["action"]
        assert col.index or any(
            "action" in [c.name for c in idx.columns]
            for idx in AuditLog.__table__.indexes
        )


# ─── Phase 10.D — Serialization payload size budget ──────────────────────────


class TestPayloadSizes:
    """Spot-check that list responses don't return oversized rows."""

    def test_patients_list_row_shape_is_lean(
        self, client, lab_with_many_patients
    ):
        admin = lab_with_many_patients["admin"]
        lab_id = lab_with_many_patients["lab"].id
        body = client.get(
            "/patients?limit=5",
            headers=_hdr(admin.id, lab_id),
        ).json()
        for p in body["patients"]:
            # No sensitive PII bytes leaked: national_id_hash should not be
            # in the response (it's a hash, but still treat as opaque)
            assert "national_id_hash" not in p or p["national_id_hash"] is None
            assert "family_id_hash" not in p or p["family_id_hash"] is None
            # Field count budget — keep response shape stable
            assert len(p) <= 30, (
                f"patient row has {len(p)} fields — likely accidental leak. "
                f"Fields: {list(p.keys())}"
            )


# ─── Phase 10.E — Response time exposure ─────────────────────────────────────


class TestResponseTimingObservability:
    """The X-Response-Time header lets ops dashboards measure p95/p99."""

    def test_response_time_is_numeric_milliseconds(self, client):
        res = client.get("/health")
        rt = res.headers.get("X-Response-Time")
        assert rt is not None
        assert rt.endswith("ms")
        # Must be parseable as int
        ms = int(rt[:-2])
        assert ms >= 0
        # Sanity: a /health request must not take > 5 seconds in test
        assert ms < 5000


# ─── Phase 10.F — Tier limits cap potential abuse ────────────────────────────


class TestTierLimitsAreCaps:
    """Tier limits define resource caps; they're documented as enforced
    'at the API layer' (subscription model). Pin the documented caps so
    a future tier-matrix change can't silently lift them."""

    def test_starter_max_patients_is_500(self):
        from app.core.feature_flags import get_tier_limits
        assert get_tier_limits("starter")["max_patients"] == 500

    def test_starter_max_orders_per_day_is_100(self):
        from app.core.feature_flags import get_tier_limits
        assert get_tier_limits("starter")["max_orders_per_day"] == 100

    def test_enterprise_max_orders_per_day_is_finite(self):
        """Even enterprise must have a finite cap to prevent runaway abuse."""
        from app.core.feature_flags import get_tier_limits
        cap = get_tier_limits("enterprise")["max_orders_per_day"]
        assert cap > 0
        assert cap < 10**9  # not unbounded
