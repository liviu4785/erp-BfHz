from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.address import Address
from erp_fastapi.models.user import User
from erp_fastapi.schemas.address import AddressCreate, AddressUpdate, AddressOut
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("/", response_model=List[AddressOut])
def list_addresses(
    record_type: str = Query(None),
    record_id: int = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Address)
    if record_type:
        query = query.filter(Address.record_type == record_type)
    if record_id:
        query = query.filter(Address.record_id == record_id)
    return query.all()


@router.post("/", response_model=AddressOut, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    addr = Address(**payload.model_dump())
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


@router.get("/{addr_id}", response_model=AddressOut)
def get_address(addr_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    addr = db.query(Address).filter(Address.id == addr_id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    return addr


@router.put("/{addr_id}", response_model=AddressOut)
def update_address(addr_id: int, payload: AddressUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    addr = db.query(Address).filter(Address.id == addr_id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(addr, field, value)
    db.commit()
    db.refresh(addr)
    return addr


@router.delete("/{addr_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(addr_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    addr = db.query(Address).filter(Address.id == addr_id).first()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(addr)
    db.commit()
