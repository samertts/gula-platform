"""National Data Platform base classes.

Uses Integer PK (intentional — data warehouse fact tables use auto-increment).
Mixins are imported from shared.models.
"""


from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

from app.orm_topology import SHARED_METADATA
from shared.models import BaseEntityMixin, SoftDeleteMixin, TimestampMixin

#: NR-086 -- constructed against the one shared namespace so this base's
#: cross-base foreign keys resolve. See app/orm_topology.py.
DataPlatformBase = declarative_base(metadata=SHARED_METADATA)


class BaseEntity(TimestampMixin, SoftDeleteMixin, BaseEntityMixin, DataPlatformBase):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
