from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database.db import SessionLocal
from schemas.user_schema import UserCreate, UserResponse
from services.user_service import create_user, get_users

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return get_users(db)

@router.post("/users", response_model=UserResponse)
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)
