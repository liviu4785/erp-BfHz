from sqlalchemy import Column, Integer, String, DateTime, func
from erp_fastapi.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(300), nullable=False)
    type = Column(String(50), nullable=False)
    url = Column(String(500), nullable=True)
    record_type = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
