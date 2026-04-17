"""FastAPI app for the nhop-platform citizen registry service."""
from fastapi import FastAPI

from .api.v1 import api_router
from .core.database import Base, engine


def create_app() -> FastAPI:
    app = FastAPI(
        title="NHOP — Citizen Registry",
        version="0.1.0",
        description="National Health Oversight Platform: citizen registry API.",
    )
    # Models imported for side-effect so Base.metadata is populated.
    from . import models  # noqa: F401
    Base.metadata.create_all(engine)

    app.include_router(api_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
