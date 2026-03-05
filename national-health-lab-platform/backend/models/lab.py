from sqlalchemy import Column, Integer, String
from database.db import Base

class Laboratory(Base):
    __tablename__ = "laboratories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    city = Column(String)
    type = Column(String)
