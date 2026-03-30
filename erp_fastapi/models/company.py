from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from erp_fastapi.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    fiscal_code = Column(String(50), nullable=True)
    trade_registry_number = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    status = Column(String(50), default="active")

    people = relationship("Person", secondary="person_company", back_populates="companies")
