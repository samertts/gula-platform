"""The one origin allowlist.

There were two. ``factory.py`` built one for the CORS middleware and
``csrf.py`` built another for the origin check on cookie-authenticated writes,
each reading ``CORS_ORIGINS`` and each carrying its own hardcoded development
fallback. Two copies of one policy drift, and these had: both listed
``http://localhost:*`` and neither listed ``http://127.0.0.1:*``, although
``playwright.config.ts`` drives the browser from ``http://127.0.0.1:4173`` and
``vite.config.ts`` allows both spellings. A browser treats them as different
origins, so every browser-originated write from a Playwright run against a real
backend was answered

    403 {"detail": "Cross-origin request rejected"}

which reads as a defect in the page.

Fixing that in one of the two copies fixes nothing, because the CORS middleware
and the CSRF middleware answer different questions and a request has to pass
both. So the list lives here now and both call it.

This module decides WHAT is allowed. It does not decide what to do about it:
``factory.py`` still applies its own production validation (no wildcard with
credentials, HTTPS only) on top of what it gets back.
"""
from __future__ import annotations

import os

#: Where the platform is actually served from.
_PRODUCTION_ORIGINS = (
    "https://gula-platform.org",
    "https://www.gula-platform.org",
)

#: Where this repository's own tooling serves the app from in development:
#: 3000 the legacy client, 5173 the Vite dev server, 4173 the Vite preview
#: server that playwright.config.ts starts, 8000 the backend itself. Both
#: spellings of the loopback host, because a browser treats them as different
#: origins and the repository uses both.
_DEVELOPMENT_ORIGINS = tuple(
    f"http://{host}:{port}"
    for host in ("localhost", "127.0.0.1")
    for port in (3000, 4173, 5173, 8000)
)


def configured_origins() -> list[str]:
    """Exactly what CORS_ORIGINS names, cleaned. Empty when it is unset."""
    return [
        origin.strip().rstrip("/")
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]


def is_development() -> bool:
    """True only when ENV explicitly says so. Absent means production."""
    return os.getenv("ENV", "production").lower() in {"development", "test"}


def allowed_origins() -> list[str]:
    """The origins this deployment accepts browser traffic from.

    An explicit CORS_ORIGINS REPLACES the defaults rather than extending them,
    so a deployment that names its origins gets exactly those.
    """
    configured = configured_origins()
    if configured:
        return configured

    origins = list(_PRODUCTION_ORIGINS)
    if is_development():
        origins += list(_DEVELOPMENT_ORIGINS)
    return origins
