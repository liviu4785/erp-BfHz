from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from erp_fastapi.database import Base


class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    unique_identifier = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    companies = relationship("Company", secondary="person_company", back_populates="people")
