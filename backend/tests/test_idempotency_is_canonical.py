"""One idempotency claim, used by every clinical write that needs one.

`app/services/idempotency.py` is the canonical implementation. It was not
written from scratch: it is the one correct implementation the platform already
had, inlined in `order_service.create_order`, extracted so the other call sites
stop being a matter of whoever remembered to re-type it.

Three properties have to hold together, and the reason they live in one module
is that omitting any single one still looks like it works:

* **the tenant is in the key**, `idempotency:{scope}:{tenant}:{key}`, so two
  labs cannot name the same entry -- the cache-side statement of NR-094;
* **the payload is fingerprinted**, so reusing a key for different content is
  refused with 409 rather than silently returning the first response and
  discarding a clinical write;
* **the claim is atomic** (`set_if_absent`), which is the only thing standing
  between two concurrent retries. Executed with eight threads on one key:
  exactly one claimed, seven conflicted.

**Coverage was the actual defect.** The mechanism existed and worked; two
mutating clinical endpoints simply did not call it. `POST /samples` had none at
all, and `POST /batch/orders` passed `idempotency_key=None` explicitly, so a
retried batch duplicated up to fifty orders and their results.

`POST /samples` needs it and cannot get protection any other way. A sample is a
physical specimen record. `samples.barcode` is NOT NULL and UNIQUE, but
`generate_barcode()` mints `SMP-` + `secrets.token_hex(6)` per INSERT, so the
constraint cannot deduplicate a retry -- it guarantees barcode uniqueness, not
request identity. And `(order_id, sample_type)` must not be unique, because an
order legitimately carries several tubes of the same type. The key is the only
mechanism left.

**The limitation this file does not paper over.** The claim store is
`redis_client.cache`, which falls back to a per-process `_MemoryStore` when
`REDIS_URL` is unset or Redis is unreachable. Executed: two `_MemoryStore`
instances, standing for two gunicorn workers, do not see each other's claims,
so a retry landing elsewhere is treated as new. `is_shared()` reports it and
`/compliance/system-status` publishes it as MEASURED_PASS / MEASURED_FAIL. The
durable fix is a database-backed store; NR-095 records it.
"""

from __future__ import annotations

import ast
import pathlib
import threading

import pytest
from app.services import idempotency

BACKEND = pathlib.Path(__file__).resolve().parents[1]

#: Route handlers that create or mutate clinical data and must accept an
#: Idempotency-Key. This may grow. It may not shrink: removing an entry means a
#: clinical write became replayable again.
DECLARED_IDEMPOTENT_HANDLERS = {
    "app/routes/samples.py": ("create_sample",),
    "app/routes/batch.py": ("create_batch_orders",),
    "app/routes/results.py": ("create_order_route",),
}


def _handlers(path: pathlib.Path) -> dict[str, ast.AST]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        n.name: n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _mentions_idempotency_key(node: ast.AST) -> bool:
    """Either a Header(alias="Idempotency-Key") param or a header read."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and sub.value == "Idempotency-Key":
            return True
    return False


# ── the mechanism ────────────────────────────────────────────────────────────


def test_the_tenant_is_in_the_key_not_in_a_filter() -> None:
    """Two labs using the same key must not collide at all."""
    key, payload = "INV-2026-001", {"order_id": 5}
    first = idempotency.begin("sample", 901, key, payload)
    assert first.claimed
    first.complete({"id": 1})

    other_lab = idempotency.begin("sample", 902, key, payload)
    assert other_lab.claimed, (
        "lab 902 was blocked by lab 901's key. The tenant must be part of the "
        "cache key so the two never name the same entry."
    )


def test_a_retry_replays_instead_of_repeating_the_work() -> None:
    key, payload = "replay-key", {"order_id": 7}
    first = idempotency.begin("sample", 905, key, payload)
    assert first.claimed
    first.complete({"sample": {"id": 77}})

    retry = idempotency.begin("sample", 905, key, payload)
    assert retry.replay == {"sample": {"id": 77}}
    assert not retry.claimed, "a replay must not also be treated as a fresh claim"


def test_reusing_a_key_for_different_content_is_refused() -> None:
    """Returning the first response for a second payload would discard a write."""
    key = "reused-key"
    first = idempotency.begin("sample", 906, key, {"order_id": 1})
    first.complete({"id": 1})

    different = idempotency.begin("sample", 906, key, {"order_id": 2})
    assert different.conflict is not None
    assert different.conflict["status_code"] == 409
    assert "different payload" in different.conflict["error"]


def test_scope_separates_operations_sharing_a_key() -> None:
    key, payload = "shared-across-scopes", {"x": 1}
    idempotency.begin("order", 907, key, payload).complete({"order": 1})
    sample = idempotency.begin("sample", 907, key, payload)
    assert sample.claimed, "a key claimed for an order must not block a sample"


def test_exactly_one_of_many_concurrent_requests_claims_the_key(monkeypatch) -> None:
    """The atomic claim is the whole defence against a double clinical write.

    The interleaving has to be forced. Started naively, the first thread wins
    the initial lookup and every other thread simply *reads* its claim, so the
    test passes against a get-then-set implementation that has no atomicity at
    all -- which is exactly what it did, until the negative proof below failed
    to fail. Holding every thread past the lookup before any of them writes is
    what puts the pressure on `set_if_absent` rather than on scheduling luck.
    """
    workers = 8
    barrier = threading.Barrier(workers, timeout=10)
    waited = threading.local()
    real_get = idempotency._cache.get

    def get_holding_everyone_past_the_lookup(key: str):
        value = real_get(key)
        if value is None and not getattr(waited, "done", False):
            waited.done = True
            barrier.wait()
        return value

    monkeypatch.setattr(idempotency._cache, "get", get_holding_everyone_past_the_lookup)

    outcomes: list[str] = []
    lock = threading.Lock()

    def attempt() -> None:
        result = idempotency.begin("sample", 908, "concurrent-key", {"order_id": 3})
        with lock:
            outcomes.append("claimed" if result.claimed else "refused")

    threads = [threading.Thread(target=attempt) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(outcomes) == workers, (
        f"only {len(outcomes)} of {workers} threads finished; the barrier did "
        "not release, so this test proved nothing."
    )
    assert outcomes.count("claimed") == 1, (
        f"{outcomes.count('claimed')} of {workers} concurrent requests claimed "
        "the same key after all of them passed the lookup. Only one may "
        "proceed; the rest must be refused. A get-then-set claim gives this "
        "result only by scheduling luck."
    )


def test_a_released_claim_can_be_retried() -> None:
    """A request that failed validation must not lock its key for five minutes."""
    key, payload = "released-key", {"order_id": 4}
    first = idempotency.begin("sample", 909, key, payload)
    assert first.claimed
    first.release()

    again = idempotency.begin("sample", 909, key, payload)
    assert again.claimed, "releasing a claim must let a corrected retry through"


# ── coverage: the defect was which endpoints called it ───────────────────────


@pytest.mark.parametrize(
    ("relative", "handlers"),
    sorted((k, v) for k, v in DECLARED_IDEMPOTENT_HANDLERS.items()),
)
def test_each_declared_clinical_write_accepts_an_idempotency_key(
    relative: str, handlers: tuple[str, ...],
) -> None:
    """The ratchet. These are mutating clinical writes; a retry must not duplicate."""
    path = BACKEND / relative
    found = _handlers(path)
    missing = []
    for name in handlers:
        node = found.get(name)
        if node is None or not _mentions_idempotency_key(node):
            missing.append(name)

    assert missing == [], (
        f"{relative}: {missing} no longer accept an Idempotency-Key. These "
        "create clinical records with no natural uniqueness -- a sample's "
        "barcode is minted per INSERT, and an order legitimately has several "
        "tubes of the same type -- so a retried request creates a duplicate "
        "specimen or a duplicate order."
    )


def test_the_store_topology_is_reported_rather_than_asserted() -> None:
    """`is_shared()` must stay a measurement.

    A per-worker store is a deployment problem, not a caller's, so it must not
    refuse writes -- but it must not be reported as protection either.
    /compliance/system-status publishes MEASURED_PASS or MEASURED_FAIL from it.
    """
    assert isinstance(idempotency.is_shared(), bool)

    report = (BACKEND / "app" / "routes" / "compliance.py").read_text(encoding="utf-8")
    assert "idempotency.is_shared()" in report, (
        "the security report no longer measures whether the claim store is "
        "shared across workers. Without it the report implies replay "
        "protection that a per-worker store does not provide."
    )
    assert "MEASURED_FAIL" in report, (
        "the un-shared case must be reported as a measured failure, not "
        "omitted and not softened into a PASS."
    )
