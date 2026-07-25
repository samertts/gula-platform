from sqlalchemy import JSON, Column, String, Text

from app.national_data.base import BaseEntity


class MetadataEntry(BaseEntity):
    __tablename__ = "dp_metadata_registry"

    entity_name = Column(String(200), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=True)

    metadata_key = Column(String(100), nullable=False)
    metadata_value = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    metadata_type = Column(String(50), default="string", nullable=False)

    source = Column(String(100), nullable=True)
    version = Column(String(20), nullable=True)

    __table_args__ = ({"extend_existing": True},)
