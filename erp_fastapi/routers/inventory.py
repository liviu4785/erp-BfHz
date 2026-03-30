from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.inventory import InventoryItem
from erp_fastapi.models.product import Product
from erp_fastapi.models.user import User
from erp_fastapi.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryOut
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _inv_out(item: InventoryItem) -> InventoryOut:
    return InventoryOut(
        id=item.id, product_id=item.product_id,
        quantity=item.quantity, reserved=item.reserved,
        product_name=item.product.name if item.product else None,
    )


@router.get("/", response_model=List[InventoryOut])
def list_inventory(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [_inv_out(i) for i in db.query(InventoryItem).all()]


@router.post("/", response_model=InventoryOut, status_code=status.HTTP_201_CREATED)
def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.query(Product).filter(Product.id == payload.product_id).first():
        raise HTTPException(status_code=400, detail="Product does not exist")
    if db.query(InventoryItem).filter(InventoryItem.product_id == payload.product_id).first():
        raise HTTPException(status_code=400, detail="Inventory for this product already exists")
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _inv_out(item)


@router.get("/{item_id}", response_model=InventoryOut)
def get_inventory(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return _inv_out(item)


@router.put("/{item_id}", response_model=InventoryOut)
def update_inventory(item_id: int, payload: InventoryUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _inv_out(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    db.delete(item)
    db.commit()
