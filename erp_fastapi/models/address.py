from sqlalchemy import Column, Integer, String, Boolean, Float, Text
from erp_fastapi.database import Base


class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(50), nullable=True)
    record_id = Column(Integer, nullable=True)
    country = Column(String(100), default="Romania")
    postal_code = Column(String(20), nullable=True)
    county = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    street = Column(String(300), nullable=True)
    additional_info = Column(String(300), nullable=True)
    is_default = Column(Boolean, default=False)
    is_billing = Column(Boolean, default=False)
    is_shipping = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
