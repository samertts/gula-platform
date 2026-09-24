"""One origin allowlist, and it covers the origins this repo actually serves from.

There used to be two allowlists: factory.py built one for the CORS middleware
and csrf.py built another for the origin check on cookie-authenticated writes.
Both read CORS_ORIGINS, both carried their own development fallback, and both
fallbacks listed only the `localhost` spelling -- while playwright.config.ts
drives the browser from http://127.0.0.1:4173 and vite.config.ts allows both.
A browser treats those as different origins, so every browser-originated write
from a Playwright run against a real backend was answered

    403 {"detail": "Cross-origin request rejected"}

which looks like a defect in the page. Fixing one copy fixed nothing, because a
write has to pass both layers -- which is how the second copy was found.

These tests read the list the app was actually built with, rather than
re-deriving it, so they fail if it moves rather than silently passing.
"""
from __future__ import annotations

import pytest
from starlette.middleware.cors import CORSMiddleware

#: The origins the repository's own tooling serves the app from.
_TOOLING_ORIGINS = [
    "http://localhost:5173",    # vite.config.ts server port
    "http://127.0.0.1:5173",
    "http://localhost:4173",    # playwright.config.ts webServer / vite preview
    "http://127.0.0.1:4173",
]


def _cors_origins(monkeypatch, env: str) -> list[str]:
    """Build the app under this ENV and read back the CORS middleware's list."""
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    monkeypatch.setenv("ENV", env)

    from app.factory import create_app

    app = create_app()
    for middleware in app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return list(middleware.kwargs["allow_origins"])
    pytest.fail("the app has no CORSMiddleware, so this test proves nothing")


@pytest.mark.parametrize("env", ["development", "test"])
@pytest.mark.parametrize("origin", _TOOLING_ORIGINS)
def test_the_dev_fallback_allows_the_origins_this_repo_serves_from(monkeypatch, env, origin):
    assert origin in _cors_origins(monkeypatch, env), (
        f"{origin} is not allowed under ENV={env}. The repository serves the "
        "app from this origin, so a browser driven against a real backend is "
        "refused on every write."
    )


def test_the_fallback_is_development_only(monkeypatch):
    """Positive control: the test above must be proving something ENV-specific.

    If loopback origins were allowed in production too, the parametrised test
    would pass for a reason that has nothing to do with the fallback.
    """
    allowed = _cors_origins(monkeypatch, "production")
    leaked = [origin for origin in _TOOLING_ORIGINS if origin in allowed]
    assert leaked == [], f"loopback origins must not be allowed in production: {leaked}"


def test_an_explicit_setting_still_wins(monkeypatch):
    """A configured allowlist replaces the fallback rather than adding to it."""
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("CORS_ORIGINS", "https://example.test")

    from app.factory import create_app

    app = create_app()
    allowed = next(
        list(m.kwargs["allow_origins"])
        for m in app.user_middleware
        if m.cls is CORSMiddleware
    )
    assert allowed == ["https://example.test"]


@pytest.mark.parametrize(
    ("env", "configured"),
    [
        ("development", None),
        ("test", None),
        ("production", None),
        ("development", "https://example.test,https://other.test"),
        ("production", "https://example.test"),
    ],
)
def test_the_cors_middleware_and_the_csrf_check_never_disagree(monkeypatch, env, configured):
    """The regression that would have caught the two-copies defect.

    A browser write must pass the CORS middleware AND the CSRF origin check. If
    those two consult different lists, one layer rejects what the other allows
    and the failure surfaces as an unexplained 403 at whichever layer is
    stricter. They must be the same set.
    """
    monkeypatch.setenv("ENV", env)
    if configured is None:
        monkeypatch.delenv("CORS_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ORIGINS", configured)

    from app.factory import create_app
    from app.security.csrf import _allowed_origins as csrf_origins

    app = create_app()
    cors = next(
        set(m.kwargs["allow_origins"])
        for m in app.user_middleware
        if m.cls is CORSMiddleware
    )

    assert cors == csrf_origins(), (
        "the CORS middleware and the CSRF origin check must consult the same "
        f"list; they differ by {cors ^ csrf_origins()}"
    )
