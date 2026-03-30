from pydantic import BaseModel, Field
from typing import Optional


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=300)
    fiscal_code: Optional[str] = None
    trade_registry_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    fiscal_code: Optional[str] = None
    trade_registry_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None


class CompanyOut(BaseModel):
    id: int
    name: str
    fiscal_code: Optional[str] = None
    trade_registry_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None

    model_config = {"from_attributes": True}
