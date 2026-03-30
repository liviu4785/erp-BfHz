from pydantic import BaseModel, Field
from typing import Optional, List


class OrderLineCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)
    discount_percent: float = 0.0
    vat_percent: float = 19.0


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
    partner_type: str = "company"
    date: str
    status: Optional[str] = "draft"
    notes: Optional[str] = None
    items: List[OrderLineCreate] = []


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
