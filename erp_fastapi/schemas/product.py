from pydantic import BaseModel, Field
from typing import Optional


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    code: Optional[str] = None
    producer: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = "buc"
    package_unit: Optional[str] = None
    quantity_per_package: Optional[int] = None
    list_price: Optional[float] = 0.0
    vat_percent: Optional[float] = 19.0
    status: Optional[str] = "active"
    description: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    producer: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    package_unit: Optional[str] = None
    quantity_per_package: Optional[int] = None
    list_price: Optional[float] = None
    vat_percent: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    producer: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    package_unit: Optional[str] = None
    quantity_per_package: Optional[int] = None
    list_price: Optional[float] = None
    vat_percent: Optional[float] = None
    status: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}
