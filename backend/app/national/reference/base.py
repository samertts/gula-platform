from app.national.base import BaseEntity
from sqlalchemy import Boolean, Column, String, Text


class ReferenceEntity(BaseEntity):
    __abstract__ = True

    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    external_ref = Column(String(100), nullable=True)
    version = Column(String(20), nullable=True)
