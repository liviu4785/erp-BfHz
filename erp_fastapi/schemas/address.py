from pydantic import BaseModel
from typing import Optional


class AddressCreate(BaseModel):
    record_type: Optional[str] = None
    record_id: Optional[int] = None
    country: str = "Romania"
    postal_code: Optional[str] = None
    county: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    additional_info: Optional[str] = None
    is_default: bool = False
    is_billing: bool = False
    is_shipping: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class AddressUpdate(BaseModel):
    country: Optional[str] = None
    postal_code: Optional[str] = None
    county: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    additional_info: Optional[str] = None
    is_default: Optional[bool] = None
    is_billing: Optional[bool] = None
    is_shipping: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None


class AddressOut(BaseModel):
    id: int
    record_type: Optional[str] = None
    record_id: Optional[int] = None
    country: str
    postal_code: Optional[str] = None
    county: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    additional_info: Optional[str] = None
    is_default: bool
    is_billing: bool
    is_shipping: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}
