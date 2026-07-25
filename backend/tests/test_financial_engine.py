from __future__ import annotations

from app.financial import ads_enabled, is_enabled
from app.financial.models import FinProvider, FinSubscription, FinTransaction


class TestFinancialFlags:
    def test_is_enabled_default_false(self) -> None:
        assert is_enabled() is False

    def test_ads_enabled_default_false(self) -> None:
        assert ads_enabled() is False


class TestFinancialModels:
    def test_fin_provider_fields(self) -> None:
        assert hasattr(FinProvider, "lab_id")
        assert hasattr(FinProvider, "name")
        assert hasattr(FinProvider, "provider_type")
        assert hasattr(FinProvider, "status")
        assert hasattr(FinProvider, "quality_score")
        assert hasattr(FinProvider, "accredited")

    def test_fin_subscription_fields(self) -> None:
        assert hasattr(FinSubscription, "plan")
        assert hasattr(FinSubscription, "billing_cycle")
        assert hasattr(FinSubscription, "amount")
        assert hasattr(FinSubscription, "currency")
        assert hasattr(FinSubscription, "auto_renew")

    def test_fin_transaction_fields(self) -> None:
        assert hasattr(FinTransaction, "transaction_type")
        assert hasattr(FinTransaction, "amount")
        assert hasattr(FinTransaction, "status")
        assert hasattr(FinTransaction, "reference_id")
        assert hasattr(FinTransaction, "settled_at")

    def test_fin_provider_tablename(self) -> None:
        assert FinProvider.__tablename__ == "fin_providers"

    def test_fin_subscription_tablename(self) -> None:
        assert FinSubscription.__tablename__ == "fin_subscriptions"

    def test_fin_transaction_tablename(self) -> None:
        assert FinTransaction.__tablename__ == "fin_transactions"

    def test_fin_provider_defaults(self) -> None:
        p = FinProvider()
        assert p.status == "active" or p.status is None

    def test_fin_subscription_defaults(self) -> None:
        s = FinSubscription()
        assert s.auto_renew is True or s.auto_renew is None

    def test_fin_transaction_defaults(self) -> None:
        t = FinTransaction()
        assert t.status == "pending" or t.status is None


class TestFinancialRoutes:
    def test_router_prefix(self) -> None:
        from app.financial.routes import router

        assert router.prefix == "/financial"
        assert len(router.routes) >= 2

    def test_register_routes_imports(self) -> None:
        from app.financial import register_routes

        assert callable(register_routes)
