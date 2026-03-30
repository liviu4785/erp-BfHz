from pydantic import BaseModel, Field
from typing import Optional, List


class PersonCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    unique_identifier: Optional[str] = None
    notes: Optional[str] = None
    company_ids: List[int] = []


class PersonUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    unique_identifier: Optional[str] = None
    notes: Optional[str] = None
    company_ids: Optional[List[int]] = None


class PersonOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    unique_identifier: Optional[str] = None
    notes: Optional[str] = None
    company_ids: List[int] = []

    model_config = {"from_attributes": True}
