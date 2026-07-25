from __future__ import annotations

import pytest
from app.kernel.plugin.marketplace import MarketplacePlugin, PluginMarketplaceInterface


class TestPluginMarketplace:
    def test_register_and_search(self):
        mp = PluginMarketplaceInterface()
        p1 = MarketplacePlugin(
            id="p1", name="Plugin One", version="1.0", description="First plugin", author="dev"
        )
        p2 = MarketplacePlugin(
            id="p2", name="Plugin Two", version="2.0", description="Second plugin", author="dev"
        )
        mp.register_available(p1)
        mp.register_available(p2)
        assert len(mp.list_available()) == 2
        results = mp.search("first")
        assert len(results) == 1
        assert mp.get_available("p1") is not None
        assert mp.get_available("nonexistent") is None

    def test_marketplace_plugin_defaults(self):
        mp = MarketplacePlugin(id="p1", name="P1", version="1.0", description="D", author="A")
        assert mp.downloads == 0
        assert mp.rating == 0.0
        assert mp.tags == []
        assert not mp.verified
