from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..models.lab import Lab
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/labs", tags=["labs"])


class LabUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None


@router.get("/me")
def get_my_lab(
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    return {
        "id": lab.id,
        "name": lab.name,
        "license_number": lab.license_number,
        "city": lab.city,
        "address": lab.address,
        "phone": lab.phone,
        "is_active": lab.is_active,
        "created_at": lab.created_at.isoformat() if lab.created_at else None,
    }


@router.put("/me")
def update_my_lab(
    data: LabUpdate,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can update lab info")

    lab = db.query(Lab).filter(Lab.id == current_user.lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lab, field, value)

    db.commit()
    db.refresh(lab)

    return {"message": "Lab updated", "lab": {
        "id": lab.id,
        "name": lab.name,
        "city": lab.city,
        "address": lab.address,
        "phone": lab.phone,
    }}
