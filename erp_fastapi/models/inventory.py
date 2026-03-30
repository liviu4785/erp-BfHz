from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from erp_fastapi.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False)
    quantity = Column(Integer, default=0)
    reserved = Column(Integer, default=0)

    product = relationship("Product", back_populates="inventory")
