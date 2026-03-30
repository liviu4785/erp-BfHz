from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from erp_fastapi.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_type = Column(String(50), nullable=False)  # sale, purchase, return_sale, return_purchase
    partner_id = Column(Integer, nullable=False)
    partner_type = Column(String(50), default="company")  # company or person
    date = Column(String(20), nullable=False)
    status = Column(String(50), default="draft")
    notes = Column(String(500), nullable=True)

    items = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")


class OrderLine(Base):
    __tablename__ = "order_lines"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)
    vat_percent = Column(Float, default=19.0)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_lines")
