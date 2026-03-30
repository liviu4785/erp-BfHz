from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from erp_fastapi.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    author = relationship("User", back_populates="comments")
