from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from erp_fastapi.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    code = Column(String(50), nullable=True, index=True)
    producer = Column(String(200), nullable=True)
    category = Column(String(100), nullable=True)
    unit_of_measure = Column(String(20), default="buc")
    package_unit = Column(String(20), nullable=True)
    quantity_per_package = Column(Integer, nullable=True)
    list_price = Column(Float, default=0.0)
    vat_percent = Column(Float, default=19.0)
    status = Column(String(50), default="active")
    description = Column(Text, nullable=True)

    inventory = relationship("InventoryItem", back_populates="product", uselist=False)
    order_lines = relationship("OrderLine", back_populates="product")
