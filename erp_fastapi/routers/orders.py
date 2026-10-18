from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.order import Order, OrderLine
from erp_fastapi.models.user import User
from erp_fastapi.schemas.order import OrderCreate, OrderUpdate, OrderOut
from erp_fastapi.auth import get_current_user
from erp_fastapi.services.stock import effects, validate_order, apply_effects

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/", response_model=List[OrderOut])
def list_orders(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Order).order_by(Order.id.desc()).all()

@router.post("/", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = Order(**payload.model_dump(exclude={"items"}))
    order.items = [OrderLine(**line.model_dump()) for line in payload.items]
    validate_order(db, order)
    db.add(order)
    db.flush()
    apply_effects(db, order, {}, user.id)
    db.commit()
    db.refresh(order)
    return order

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order

@router.put("/{order_id}", response_model=OrderOut)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = get_order(order_id, db, user)
    if not order.workflow_managed:
        raise HTTPException(409, "Legacy order requires stock review by an administrator")
    data = payload.model_dump(exclude_unset=True)
    from erp_fastapi.models.integration import IntegrationOperation
    invoice = db.query(IntegrationOperation).filter_by(key=f"invoice:{order.id}").first()
    if invoice and any(key != "notes" and not (key == "status" and value in ("confirmed", "completed")) for key, value in data.items()):
        raise HTTPException(409, "Invoicing has started; reconcile the fiscal document before changing this sale")
    # Finalized and cancelled records are immutable; returns are separate documents.
    if order.status in ("completed", "cancelled"):
        if all(getattr(order, k, None) == v for k, v in data.items() if k != "items") and "items" not in data:
            return order
        raise HTTPException(409, "Finalized orders are immutable; create a return instead")
    if order.status == "confirmed" and any(k not in ("status", "notes") for k in data):
        raise HTTPException(409, "Only status and notes can change after confirmation")
    merged = {k: getattr(order, k) for k in OrderCreate.model_fields if k != "items"}
    merged["items"] = [{k: getattr(i, k) for k in ("product_id", "quantity", "unit_price", "discount_percent", "vat_percent")} for i in order.items]
    merged.update(data)
    from pydantic import ValidationError
    try:
        validated = OrderCreate.model_validate(merged)
    except ValidationError:
        raise HTTPException(422, "Invalid order update")
    before = effects(order)
    for key, value in validated.model_dump(exclude={"items"}).items():
        setattr(order, key, value)
    if "items" in data:
        order.items = [OrderLine(**i.model_dump()) for i in validated.items]
    validate_order(db, order)
    db.flush()  # version check precedes any stock effect
    apply_effects(db, order, before, user.id)
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = get_order(order_id, db, user)
    if order.status != "draft":
        raise HTTPException(409, "Only draft orders can be deleted")
    db.delete(order)
    db.commit()


from erp_fastapi.auth import require_admin

@router.post("/{order_id}/adopt-stock", response_model=OrderOut)
def adopt_stock(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    order = get_order(order_id, db, user)
    if order.workflow_managed:
        return order
    if order.status not in ("draft", "confirmed"):
        raise HTTPException(409, "Historical completed/cancelled orders remain read-only")
    validate_order(db, order)
    order.workflow_managed = True
    db.flush()
    apply_effects(db, order, {}, user.id)
    db.commit()
    return order
