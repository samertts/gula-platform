"""Configuration tests for the isolated staging deployment boundary."""

import importlib
import sys

import pytest

STAGING_ENVIRONMENT = {
    "ENV": "staging",
    "RUNTIME_MODE": "api",
    "FEATURE_BACKGROUND_TASKS": "false",
    "BASE_URL": "https://api.staging.gula-platform.example",
    "CORS_ORIGINS": "https://staging.gula-platform.example",
    "TRUSTED_HOSTS": "api.staging.gula-platform.example",
    "GULA_DATABASE_URL": "postgresql://staging:isolated@db.example/staging",
    "REDIS_URL": "redis://cache.example:6379/0",
    # Deterministic low-entropy placeholders: config validates length/policy, and
    # no reusable credential material is committed to the repository.
    "SECRET_KEY": "x" * 64,
    "REFRESH_TOKEN_SECRET": "y" * 64,
    "ENCRYPTION_KEY": "z" * 64,
    "NID_HMAC_KEY": "w" * 64,
    "AUDIT_ANCHOR_KEY": "v" * 64,
}


def _load_config(monkeypatch: pytest.MonkeyPatch, **overrides: str):
    """Import config under a temporary, fully isolated environment."""
    environment = {**STAGING_ENVIRONMENT, **overrides}
    with monkeypatch.context() as scoped_env:
        for name, value in environment.items():
            scoped_env.setenv(name, value)
        if "DEMO_MODE" not in overrides:
            scoped_env.delenv("DEMO_MODE", raising=False)
        saved = sys.modules.pop("app.config", None)
        try:
            return importlib.import_module("app.config")
        finally:
            # NR-126. Dropping the freshly imported copy is right; leaving
            # app.config ABSENT from sys.modules is not. The next
            # `from ..config import X` anywhere in the process then re-imports
            # the module from scratch, reading whatever the ambient environment
            # says at that moment rather than what the suite set up.
            #
            # That is how 45 tenant-isolation tests failed: migrations/env.py
            # sets os.environ["RUNTIME_MODE"] = "migration" at import and never
            # restores it, so after this helper evicted the module the re-import
            # bound RUNTIME_MODE="migration". run_startup_guard() reads that name
            # at call time, stopped taking its RUNTIME_MODE == "test" bypass, ran
            # full production validation against the in-memory SQLite, failed on
            # the missing alembic_version table, and left system_ready False --
            # after which ReadinessMiddleware answered 503 to every request for
            # the rest of the session.
            sys.modules.pop("app.config", None)
            if saved is not None:
                sys.modules["app.config"] = saved
                # importlib.import_module also rebinds the attribute on the
                # PARENT package, and `import app.config as cfg` reads that
                # attribute before it consults sys.modules. Restoring only
                # sys.modules left `app.config` pointing at the staging copy,
                # which is RUNTIME_MODE="api" -- still not "test", so the
                # startup-guard bypass still did not fire. Both bindings have
                # to be put back or the module has two identities.
                parent = sys.modules.get("app")
                if parent is not None:
                    parent.config = saved


def test_staging_uses_hardened_production_guards(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _load_config(monkeypatch)

    assert config.IS_STAGING is True
    assert config.IS_PRODUCTION is True
    assert config.USE_SECURE_COOKIES is True
    assert config.background_tasks_enabled() is False


def test_staging_requires_explicit_network_allowlists(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit, match="CORS_ORIGINS"):
        _load_config(monkeypatch, CORS_ORIGINS="")

    with pytest.raises(SystemExit, match="TRUSTED_HOSTS"):
        _load_config(monkeypatch, TRUSTED_HOSTS="")


def test_staging_rejects_demo_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit, match="DEMO_MODE"):
        _load_config(monkeypatch, DEMO_MODE="true")


# ── NR-126: the helper must not change what the rest of the session sees ─────


def test_loading_config_in_isolation_leaves_the_canonical_module_untouched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The regression that cost 45 tenant-isolation tests.

    `_load_config` evicts ``app.config`` from ``sys.modules`` so it can import a
    second copy under a staging environment. It used to leave it evicted. The
    next ``from ..config import X`` anywhere in the process then re-imported the
    module against the AMBIENT environment -- and ``migrations/env.py`` sets
    ``os.environ["RUNTIME_MODE"] = "migration"`` at import time and never puts it
    back, so any test session that had imported it bound RUNTIME_MODE to
    "migration" from here on.

    ``run_startup_guard()`` reads that name at call time, so it stopped taking
    its ``RUNTIME_MODE == "test"`` bypass, ran full production validation against
    the in-memory SQLite, failed on the missing ``alembic_version`` table, and
    left ``system_ready`` False. ``ReadinessMiddleware`` then answered 503 to
    every request for the remainder of the session.

    The environment below reproduces the ambient poisoning in miniature.
    """
    import app
    import app.config as canonical

    before_in_sys_modules = sys.modules.get("app.config")
    before_on_parent = getattr(app, "config", None)
    before_mode = canonical.RUNTIME_MODE

    monkeypatch.setenv("RUNTIME_MODE", "migration")

    staged = _load_config(monkeypatch)
    # Positive control: the helper really did load a separate staging config.
    # Without this, a helper that silently did nothing would also "pass".
    assert staged.RUNTIME_MODE == "api", (
        "the helper no longer loads the staging environment, so the assertions "
        "below prove nothing"
    )
    assert staged is not before_in_sys_modules

    assert sys.modules.get("app.config") is before_in_sys_modules, (
        "app.config was left evicted from sys.modules; the next import in this "
        "process will rebuild it from the ambient environment"
    )
    assert getattr(app, "config", None) is before_on_parent, (
        "the `config` attribute on the `app` package still points at the staging "
        "copy; `import app.config as cfg` reads that attribute before sys.modules"
    )

    # The exact read path app/core/startup_guard.py uses at call time.
    from app.config import RUNTIME_MODE as reimported

    assert reimported == before_mode == "test", (
        f"a function-level import now sees RUNTIME_MODE={reimported!r}; the "
        f"startup-guard test-mode bypass will not fire and every later request "
        f"will get 503"
    )
