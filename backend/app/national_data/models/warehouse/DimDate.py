from app.national_data.base import BaseEntity
from sqlalchemy import Column, Index, Integer, SmallInteger, String


class DimDate(BaseEntity):
    __tablename__ = "dw_dim_date"

    date_value = Column(String(10), nullable=False, unique=True, index=True)
    year = Column(SmallInteger, nullable=False)
    quarter = Column(SmallInteger, nullable=False)
    month = Column(SmallInteger, nullable=False)
    month_name = Column(String(20), nullable=False)
    month_name_ar = Column(String(20), nullable=True)
    week = Column(SmallInteger, nullable=False)
    day = Column(SmallInteger, nullable=False)
    day_of_week = Column(SmallInteger, nullable=False)
    day_name = Column(String(20), nullable=False)
    day_name_ar = Column(String(20), nullable=True)
    is_weekend = Column(Integer, default=0, nullable=False)
    is_holiday = Column(Integer, default=0, nullable=False)
    fiscal_year = Column(SmallInteger, nullable=True)
    fiscal_quarter = Column(SmallInteger, nullable=True)

    __table_args__ = (
        Index("ix_dw_dim_date_year_month", "year", "month"),
        Index("ix_dw_dim_date_year_quarter", "year", "quarter"),
        {"extend_existing": True},
    )
