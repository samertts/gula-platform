"""Unit tests for GULA-KERNEL-EXT-001 Phase 7 — AI Marketplace."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.marketplace import (
    APPROVED_LICENSES,
    ITEM_KINDS,
    CatalogItem,
    Marketplace,
    MarketplaceError,
)


def _item(item_id: str = "CAT-100001", **overrides) -> CatalogItem:
    base = {
        "id": item_id,
        "kind": "plugin",
        "name": "demo plugin",
        "version": "1.0.0",
        "description": "a demo plugin",
        "license": "MIT",
    }
    base.update(overrides)
    return CatalogItem(**base)


class TestItem:
    def test_valid_item(self):
        item = _item()
        assert item.kind == "plugin"

    def test_bad_id(self):
        with pytest.raises(MarketplaceError):
            _item(id="BAD-1")

    def test_bad_kind(self):
        with pytest.raises(MarketplaceError):
            _item(kind="nope")

    def test_bad_version(self):
        with pytest.raises(MarketplaceError):
            _item(version="1.0")

    def test_unapproved_license(self):
        with pytest.raises(MarketplaceError):
            _item(license="Proprietary")

    def test_all_kinds_valid(self):
        for kind in ITEM_KINDS:
            assert _item(kind=kind).kind == kind

    def test_all_licenses_valid(self):
        for license_name in APPROVED_LICENSES:
            assert _item(license=license_name).license == license_name


class TestMarketplace:
    def test_add_and_get(self):
        marketplace = Marketplace()
        item = marketplace.add(_item())
        assert marketplace.get("CAT-100001") is item

    def test_duplicate_add_raises(self):
        marketplace = Marketplace()
        marketplace.add(_item())
        with pytest.raises(MarketplaceError):
            marketplace.add(_item())

    def test_search_all(self):
        marketplace = Marketplace()
        marketplace.add(_item("CAT-100001", kind="plugin"))
        marketplace.add(_item("CAT-100002", kind="policy"))
        assert len(marketplace.search()) == 2

    def test_search_by_kind(self):
        marketplace = Marketplace()
        marketplace.add(_item("CAT-100001", kind="plugin"))
        marketplace.add(_item("CAT-100002", kind="policy"))
        assert [i.id for i in marketplace.search(kind="policy")] == ["CAT-100002"]

    def test_search_by_query(self):
        marketplace = Marketplace()
        marketplace.add(_item("CAT-100001", name="alpha tool"))
        marketplace.add(_item("CAT-100002", name="beta skill"))
        assert [i.id for i in marketplace.search(query="beta")] == ["CAT-100002"]

    def test_search_sorted(self):
        marketplace = Marketplace()
        marketplace.add(_item("CAT-100002", name="zeta"))
        marketplace.add(_item("CAT-100001", name="alpha"))
        assert [i.name for i in marketplace.search()] == ["alpha", "zeta"]

    def test_install_and_uninstall(self):
        marketplace = Marketplace()
        marketplace.add(_item())
        assert marketplace.install("CAT-100001") == "1.0.0"
        assert marketplace.is_installed("CAT-100001")
        marketplace.uninstall("CAT-100001")
        assert not marketplace.is_installed("CAT-100001")

    def test_double_install_raises(self):
        marketplace = Marketplace()
        marketplace.add(_item())
        marketplace.install("CAT-100001")
        with pytest.raises(MarketplaceError):
            marketplace.install("CAT-100001")

    def test_uninstall_not_installed_raises(self):
        marketplace = Marketplace()
        marketplace.add(_item())
        with pytest.raises(MarketplaceError):
            marketplace.uninstall("CAT-100001")

    def test_unknown_item_raises(self):
        marketplace = Marketplace()
        with pytest.raises(MarketplaceError):
            marketplace.get("CAT-000000")

    def test_installed_list(self):
        marketplace = Marketplace()
        marketplace.add(_item("CAT-100001"))
        marketplace.add(_item("CAT-100002"))
        marketplace.install("CAT-100002")
        assert [i.id for i in marketplace.installed()] == ["CAT-100002"]

    def test_snapshot_and_save(self, tmp_path):
        marketplace = Marketplace()
        marketplace.add(_item())
        marketplace.install("CAT-100001")
        path = marketplace.save(tmp_path / "catalog.json")
        data = path.read_text(encoding="utf-8")
        assert "CAT-100001" in data
        assert "installed" in data

    def test_history_recorded(self):
        marketplace = Marketplace()
        marketplace.add(_item())
        marketplace.install("CAT-100001")
        events = [h["event"] for h in marketplace.snapshot()["history"]]
        assert "indexed" in events and "installed" in events
