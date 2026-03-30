from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CommentCreate(BaseModel):
    content: str
    record_type: str
    record_id: int


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class CommentOut(BaseModel):
    id: int
    content: str
    author_id: int
    author_name: Optional[str] = None
    record_type: str
    record_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
