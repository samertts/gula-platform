"""National Data Platform base classes.

Uses Integer PK (intentional — data warehouse fact tables use auto-increment).
Mixins are imported from shared.models.
"""


from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

from shared.models import BaseEntityMixin, SoftDeleteMixin, TimestampMixin

DataPlatformBase = declarative_base()


class BaseEntity(TimestampMixin, SoftDeleteMixin, BaseEntityMixin, DataPlatformBase):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
