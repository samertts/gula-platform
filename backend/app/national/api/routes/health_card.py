from __future__ import annotations

from datetime import datetime
from app._compat import UTC

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.domain.health_card import HealthCard
from app.national.enums import HealthCardStatus
from app.security.dependencies import get_current_user

router = APIRouter(prefix="/health-cards", tags=["Health Cards"])


class HealthCardIssue(BaseModel):
    citizen_id: str
    health_number: str
    card_type: str = "standard"


class HealthCardResponse(BaseModel):
    id: str
    citizen_id: str
    health_number: str
    card_number: str
    card_type: str
    status: str
    issued_at: str
    expires_at: str | None = None
    is_active: bool = True
    is_lost: bool = False

    @classmethod
    def from_orm(cls, card: HealthCard) -> HealthCardResponse:
        return cls(
            id=card.id,
            citizen_id=card.citizen_id,
            health_number=card.health_number,
            card_number=card.card_number,
            card_type=card.card_type,
            status=card.status.value if card.status else "active",
            issued_at=card.issued_at.isoformat() if card.issued_at else "",
            expires_at=card.expires_at.isoformat() if card.expires_at else None,
            is_active=card.is_active,
            is_lost=card.is_lost,
        )


def _generate_card_number(db: Session) -> str:
    import uuid
    return f"HC-{uuid.uuid4().hex[:12].upper()}"


@router.post("/", response_model=HealthCardResponse, status_code=201)
async def issue_health_card(
    data: HealthCardIssue,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    card = HealthCard(
        citizen_id=data.citizen_id,
        health_number=data.health_number,
        card_number=_generate_card_number(db),
        card_type=data.card_type,
        status=HealthCardStatus.ACTIVE,
        issued_at=datetime.now(UTC),
        is_active=True,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return HealthCardResponse.from_orm(card)


@router.get("/{card_id}", response_model=HealthCardResponse)
async def get_health_card(
    card_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    card = db.query(HealthCard).filter(HealthCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Health card not found")
    return HealthCardResponse.from_orm(card)


@router.get("/citizen/{citizen_id}", response_model=list[HealthCardResponse])
async def get_citizen_health_card(
    citizen_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cards = db.query(HealthCard).filter(HealthCard.citizen_id == citizen_id).all()
    return [HealthCardResponse.from_orm(c) for c in cards]
