from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import date as Date


class OrderLineCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    discount_percent: float = Field(0, ge=0, le=100)
    vat_percent: float = Field(19, ge=0, le=100)


class OrderLineOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    discount_percent: float
    vat_percent: float

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    order_type: str = Field(..., pattern="^(sale|purchase|return_sale|return_purchase)$")
    partner_id: int
    partner_type: Literal["company", "person"] = "company"
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    status: Literal["draft", "confirmed", "completed", "cancelled"] = "draft"
    notes: Optional[str] = None
    items: List[OrderLineCreate] = Field(min_length=1)


    @field_validator("date")
    @classmethod
    def valid_date(cls, value):
        Date.fromisoformat(value)
        return value


class OrderUpdate(BaseModel):
    order_type: Optional[str] = None
    partner_id: Optional[int] = None
    partner_type: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[OrderLineCreate]] = None


class OrderOut(BaseModel):
    id: int
    order_type: str
    partner_id: int
    partner_type: str
    date: str
    status: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderLineOut] = []

    model_config = {"from_attributes": True}
