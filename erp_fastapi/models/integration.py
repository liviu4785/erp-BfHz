from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Text, func
from erp_fastapi.database import Base

class ExternalOrder(Base):
    __tablename__ = "external_orders"
    __table_args__ = (UniqueConstraint("channel", "external_id", name="uq_external_order"),)
    id = Column(Integer, primary_key=True)
    channel = Column(String(30), nullable=False)
    external_id = Column(String(100), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())

class ProductMapping(Base):
    __tablename__ = "product_mappings"
    __table_args__ = (UniqueConstraint("channel", "external_id", name="uq_product_mapping"),)
    id = Column(Integer, primary_key=True)
    channel = Column(String(30), nullable=False)
    external_id = Column(String(100), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    location_id = Column(String(100), nullable=True)

class IntegrationOperation(Base):
    __tablename__ = "integration_operations"
    id = Column(Integer, primary_key=True)
    key = Column(String(200), unique=True, nullable=False)
    channel = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="pending")
    result = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
