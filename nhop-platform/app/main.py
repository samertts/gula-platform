"""NHOP Platform API — main application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import router as api_v1_router
from app.database import get_session, init_db
from app.models import Analysis, Citizen, Lab


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="NHOP Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/v1/stats")
async def stats(session: AsyncSession = Depends(get_session)):
    citizens = await session.scalar(select(func.count()).select_from(Citizen))
    labs = await session.scalar(select(func.count()).select_from(Lab))
    analyses = await session.scalar(select(func.count()).select_from(Analysis))
    return {
        "citizens": citizens or 0,
        "labs": labs or 0,
        "analyses": analyses or 0,
    }
