from pydantic import BaseModel, Field
from typing import Optional


class InventoryCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=0)
    reserved: int = Field(0, ge=0)


class InventoryUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=0)
    reserved: Optional[int] = Field(None, ge=0)


class InventoryOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    reserved: int
    product_name: Optional[str] = None

    model_config = {"from_attributes": True}
