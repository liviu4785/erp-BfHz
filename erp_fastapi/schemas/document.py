from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentCreate(BaseModel):
    name: str
    type: str
    url: Optional[str] = None
    record_type: str
    record_id: int


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None


class DocumentOut(BaseModel):
    id: int
    name: str
    type: str
    url: Optional[str] = None
    record_type: str
    record_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
