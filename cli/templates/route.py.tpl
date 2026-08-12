from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..security.dependencies import get_current_user

router = APIRouter(prefix="/{{ prefix }}", tags=["{{ tag }}"])


class {{ class_name }}Create(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2 or len(v) > 200:
            raise ValueError("Name must be between 2 and 200 characters")
        return v


class {{ class_name }}Update(BaseModel):
    name: str | None = None


@router.get("/")
def list_{{ plural }}(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    from ..models.{{ model_import }} import {{ class_name }}

    items = (
        db.query({{ class_name }})
        .filter({{ class_name }}.lab_id == current_user.lab_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items


@router.get("/{id}")
def get_{{ name }}(
    id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    from ..models.{{ model_import }} import {{ class_name }}

    item = db.query({{ class_name }}).filter(
        {{ class_name }}.id == id,
        {{ class_name }}.lab_id == current_user.lab_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="{{ class_name }} not found")
    return item


@router.post("/", status_code=201)
def create_{{ name }}(
    payload: {{ class_name }}Create,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    from ..models.{{ model_import }} import {{ class_name }}

    item = {{ class_name }}(
        lab_id=current_user.lab_id,
        **payload.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{id}")
def update_{{ name }}(
    id: int,
    payload: {{ class_name }}Update,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    from ..models.{{ model_import }} import {{ class_name }}

    item = db.query({{ class_name }}).filter(
        {{ class_name }}.id == id,
        {{ class_name }}.lab_id == current_user.lab_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="{{ class_name }} not found")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, val)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{id}")
def delete_{{ name }}(
    id: int,
    db: Session = Depends(get_db),
    current_user: LabUser = Depends(get_current_user),
):
    from ..models.{{ model_import }} import {{ class_name }}

    item = db.query({{ class_name }}).filter(
        {{ class_name }}.id == id,
        {{ class_name }}.lab_id == current_user.lab_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="{{ class_name }} not found")
    db.delete(item)
    db.commit()
    return {"detail": "{{ class_name }} deleted"}
