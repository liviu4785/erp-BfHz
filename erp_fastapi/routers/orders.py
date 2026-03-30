from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.order import Order, OrderLine
from erp_fastapi.models.user import User
from erp_fastapi.schemas.order import OrderCreate, OrderUpdate, OrderOut
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Order).order_by(Order.id.desc()).all()


@router.post("/", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = Order(
        order_type=payload.order_type,
        partner_id=payload.partner_id,
        partner_type=payload.partner_type,
        date=payload.date,
        status=payload.status,
        notes=payload.notes,
    )
    for line in payload.items:
        order.items.append(OrderLine(**line.model_dump()))
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}", response_model=OrderOut)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    update_data = payload.model_dump(exclude_unset=True)
    items_data = update_data.pop("items", None)
    for field, value in update_data.items():
        setattr(order, field, value)
    if items_data is not None:
        order.items.clear()
        for line in items_data:
            order.items.append(OrderLine(**line))
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
