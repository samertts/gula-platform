"""IA-007 — the generated invoice number must reach the claim's mapped metadata column.

`InsuranceClaim` maps table `ins_claims`, whose physical column `metadata` is mapped
under the Python attribute `extra_metadata`: a declarative class already owns
`.metadata`, where SQLAlchemy keeps the MetaData registry. `InvoiceGenerator` read and
wrote `claim.metadata`, so:

* `claim.metadata or {}` yielded the registry, which is truthy;
* `metadata["invoice_number"] = …` raised
  `TypeError: 'MetaData' object does not support item assignment`;
* and had it not raised, `claim.metadata = …` would have set an instance attribute
  shadowing the class one, never reaching the column, so the following `commit()`
  would have persisted nothing.

The invoice dict is built entirely from claim fields **before** those lines, so no
financial figure depends on them. These tests pin the stamping, not the arithmetic.

No schema is needed: the defect is attribute resolution. A stub session stands in for
the database so the test stays independent of the absent `ins_*` tables (IA-006).
"""

from __future__ import annotations

from decimal import Decimal

from app.insurance.domain.models import InsuranceClaim
from app.insurance.financial.engine import InvoiceGenerator
from sqlalchemy import MetaData


class _StubQuery:
    def __init__(self, row):
        self._row = row

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._row


class _StubSession:
    """Returns one claim and records whether commit was reached."""

    def __init__(self, row):
        self._row = row
        self.committed = False

    def query(self, *_args, **_kwargs):
        return _StubQuery(self._row)

    def commit(self):
        self.committed = True


def _claim(**over):
    claim = InsuranceClaim()
    claim.id = over.pop("id", 1)
    claim.claim_number = over.pop("claim_number", "CLM-IA007-1")
    claim.total_billed = Decimal("100.00")
    claim.total_allowed = Decimal("80.00")
    claim.currency = "IQD"
    claim.items = []
    for key, value in over.items():
        setattr(claim, key, value)
    return claim


def test_the_column_is_mapped_under_another_name():
    """Guards everything below: if this changes, the fix must be revisited."""
    mapped = [k for k, c in InsuranceClaim.__mapper__.columns.items() if c.name == "metadata"]
    assert mapped == ["extra_metadata"], (
        f"ins_claims.metadata is mapped as {mapped}, not 'extra_metadata'"
    )


def test_generate_invoice_stamps_the_invoice_number_on_the_claim():
    claim = _claim()
    db = _StubSession(claim)
    invoice = InvoiceGenerator(db).generate_invoice(claim.id)

    assert invoice["invoice_number"].startswith("INV-CLM-IA007-1-")
    assert db.committed, "generate_invoice never reached commit()"
    assert claim.extra_metadata is not None, "the claim recorded no invoice number"
    assert claim.extra_metadata["invoice_number"] == invoice["invoice_number"]


def test_generate_invoice_does_not_leak_the_metadata_registry():
    claim = _claim(claim_number="CLM-IA007-2")
    InvoiceGenerator(_StubSession(claim)).generate_invoice(claim.id)
    assert not isinstance(claim.extra_metadata, MetaData)
    assert isinstance(claim.extra_metadata, dict)


def test_existing_metadata_is_preserved_not_replaced():
    claim = _claim(claim_number="CLM-IA007-3", extra_metadata={"source": "portal"})
    invoice = InvoiceGenerator(_StubSession(claim)).generate_invoice(claim.id)
    assert claim.extra_metadata["source"] == "portal", "pre-existing metadata was discarded"
    assert claim.extra_metadata["invoice_number"] == invoice["invoice_number"]


def test_the_invoice_figures_do_not_depend_on_metadata():
    """The arithmetic comes from claim fields only, so this fix cannot move a number."""
    claim = _claim(claim_number="CLM-IA007-4", extra_metadata={"invoice_number": "STALE"})
    invoice = InvoiceGenerator(_StubSession(claim)).generate_invoice(claim.id)
    assert invoice["subtotal"] == "100.00"
    assert invoice["allowed_amount"] == "80.00"
    assert invoice["tax"] == "0"
    assert invoice["total_with_tax"] == "80.00"    # calculate_tax returns 0 at rate 0
    assert invoice["currency"] == "IQD"
    assert invoice["invoice_number"] != "STALE"
