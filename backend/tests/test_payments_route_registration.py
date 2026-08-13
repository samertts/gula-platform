import inspect

from app.factory import _register_routes
from app.payments.fx_routes import router as fx_router
from app.payments.orchestration_routes import router as orchestration_router
from app.payments.routes import router as payments_router
from app.payments.subscription_routes import router as subscription_router


def _effective_paths(router):
    # FastAPI materializes the APIRouter prefix into each route path at declaration time.
    return {route.path for route in router.routes}


def test_payment_and_fx_routes_are_declared_and_registered_by_factory():
    payment_paths = _effective_paths(payments_router)
    fx_paths = _effective_paths(fx_router)
    orchestration_paths = _effective_paths(orchestration_router)
    subscription_paths = _effective_paths(subscription_router)
    registration_source = inspect.getsource(_register_routes)

    assert "/payments/invoices" in payment_paths
    assert "/payments/intents" in payment_paths
    assert "/payments/fx/quotes" in fx_paths
    assert "/payments/fx/rate-snapshots" in fx_paths
    assert "/payments/orchestration/intents/{payment_intent_id}/advise" in orchestration_paths
    assert "/payments/subscriptions/{subscription_id}/usage" in subscription_paths
    assert "app.include_router(payments_router)" in registration_source
    assert "app.include_router(payments_fx_router)" in registration_source
    assert "app.include_router(payments_orchestration_router)" in registration_source
    assert "app.include_router(payments_subscription_router)" in registration_source
