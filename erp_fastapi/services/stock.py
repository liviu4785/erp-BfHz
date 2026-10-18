"""Order stock effects, persisted atomically with order changes."""
from collections import Counter
from fastapi import HTTPException
from sqlalchemy import update
from erp_fastapi.models.inventory import InventoryItem
from erp_fastapi.models.product import Product
from erp_fastapi.models.company import Company
from erp_fastapi.models.person import Person
from erp_fastapi.models.stock_movement import StockMovement


def effects(order):
    result = {}
    if not order:
        return result
    for line in order.items:
        qty = line.quantity
        physical = reserved = 0
        if order.status == "confirmed" and order.order_type in ("sale", "return_purchase"):
            reserved = qty
        elif order.status == "completed":
            physical = qty if order.order_type in ("purchase", "return_sale") else -qty
        old = result.get(line.product_id, (0, 0))
        result[line.product_id] = (old[0] + physical, old[1] + reserved)
    return result


def validate_order(db, order):
    partner = {"company": Company, "person": Person}.get(order.partner_type)
    if not partner or not db.get(partner, order.partner_id):
        raise HTTPException(400, "Partner does not exist")
    if not order.items:
        raise HTTPException(400, "An order must have at least one line")
    for line in order.items:
        if not db.get(Product, line.product_id):
            raise HTTPException(400, f"Product {line.product_id} does not exist")


def apply_effects(db, order, before, actor_id):
    after = effects(order)
    for pid in sorted(set(before) | set(after)):
        old_q, old_r = before.get(pid, (0, 0))
        new_q, new_r = after.get(pid, (0, 0))
        dq, dr = new_q - old_q, new_r - old_r
        if not dq and not dr:
            continue
        # Conditional SQL update is atomic, including on SQLite; no read-modify-write race.
        stmt = update(InventoryItem).where(
            InventoryItem.product_id == pid,
            InventoryItem.quantity + dq >= 0,
            InventoryItem.reserved + dr >= 0,
            InventoryItem.quantity + dq >= InventoryItem.reserved + dr,
        ).values(quantity=InventoryItem.quantity + dq, reserved=InventoryItem.reserved + dr)
        if db.execute(stmt).rowcount != 1:
            raise HTTPException(409, f"Insufficient available stock or missing inventory for product {pid}")
        db.add(StockMovement(order_id=order.id, product_id=pid, quantity_delta=dq, reserved_delta=dr, actor_id=actor_id))
