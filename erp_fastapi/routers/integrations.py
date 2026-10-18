"""Admin-only integration operations. No external writes run implicitly."""
import json
from typing import Literal
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from erp_fastapi.auth import require_admin
from erp_fastapi.database import get_db
from erp_fastapi.models import User, Product, InventoryItem, Order, OrderLine
from erp_fastapi.models.integration import ExternalOrder, ProductMapping, IntegrationOperation
from erp_fastapi.schemas.order import OrderCreate
from erp_fastapi.services.stock import validate_order, apply_effects
from erp_fastapi.integrations import emag, smartbill, shopify

router = APIRouter(prefix="/integrations", tags=["integrations"], dependencies=[Depends(require_admin)])

class MappingInput(BaseModel):
    channel: Literal["emag", "shopify"]
    external_id: str = Field(min_length=1, max_length=100)
    product_id: int
    location_id: str | None = None

@router.post("/mappings")
def set_mapping(payload: MappingInput, db: Session = Depends(get_db)):
    if not db.get(Product, payload.product_id):
        raise HTTPException(400, "Product not found")
    row = db.query(ProductMapping).filter_by(channel=payload.channel, external_id=payload.external_id).first()
    if row:
        row.product_id, row.location_id = payload.product_id, payload.location_id
    else:
        row = ProductMapping(**payload.model_dump())
        db.add(row)
    db.commit()
    return {"id": row.id}

@router.get("/mappings")
def mappings(db: Session = Depends(get_db)):
    return [{"id": m.id, "channel": m.channel, "external_id": m.external_id,
             "product_id": m.product_id, "location_id": m.location_id} for m in db.query(ProductMapping).all()]

class ImportedOrder(BaseModel):
    channel: Literal["emag", "shopify"]
    external_id: str = Field(min_length=1, max_length=100)
    order: OrderCreate

@router.post("/orders/import")
def import_order(payload: ImportedOrder, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    existing = db.query(ExternalOrder).filter_by(channel=payload.channel, external_id=payload.external_id).first()
    if existing:
        return {"order_id": existing.order_id, "created": False}
    if payload.order.order_type != "sale" or payload.order.status not in ("draft", "confirmed"):
        raise HTTPException(400, "Imports must be draft or confirmed sales")
    order = Order(**payload.order.model_dump(exclude={"items"}))
    order.items = [OrderLine(**i.model_dump()) for i in payload.order.items]
    validate_order(db, order)
    db.add(order)
    db.flush()
    db.add(ExternalOrder(channel=payload.channel, external_id=payload.external_id, order_id=order.id))
    try:
        db.flush()  # unique constraint wins before any stock change
        apply_effects(db, order, {}, user.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(ExternalOrder).filter_by(channel=payload.channel, external_id=payload.external_id).first()
        if not existing:
            raise
        return {"order_id": existing.order_id, "created": False}
    return {"order_id": order.id, "created": True}

class EmagFilters(BaseModel):
    currentPage: int = Field(1, ge=1)
    itemsPerPage: int = Field(100, ge=1, le=100)
    status: int | None = None
    createdAfter: str | None = None
    createdBefore: str | None = None

@router.post("/emag/orders/read")
def read_emag(payload: EmagFilters):
    return emag.fetch_emag_orders(payload.model_dump(exclude_none=True))

class StockInput(BaseModel):
    mapping_id: int
    compare_quantity: int = Field(ge=0)
    idempotency_key: str = Field(min_length=16, max_length=100)

@router.post("/stock/publish")
def publish_stock(payload: StockInput, db: Session = Depends(get_db)):
    mapping = db.get(ProductMapping, payload.mapping_id)
    if not mapping:
        raise HTTPException(404, "Mapping not found")
    stock = db.query(InventoryItem).filter_by(product_id=mapping.product_id).first()
    if not stock:
        raise HTTPException(400, "Inventory not found")
    quantity = stock.quantity - stock.reserved
    key = f"stock:{mapping.id}:{payload.idempotency_key}"
    return execute_operation(db, key, mapping.channel, lambda: (
        shopify.update_stock(mapping.external_id, mapping.location_id, quantity, payload.compare_quantity, payload.idempotency_key)
        if mapping.channel == "shopify" and mapping.location_id else
        emag.update_stock_in_emag(mapping.external_id, quantity) if mapping.channel == "emag" else
        missing_location()))

def missing_location():
    raise HTTPException(400, "Shopify mapping requires location_id")

def execute_operation(db, key, channel, action):
    previous = db.query(IntegrationOperation).filter_by(key=key).first()
    if previous:
        if previous.status == "succeeded":
            return json.loads(previous.result)
        raise HTTPException(409, "Operation pending or uncertain; reconcile with provider before retrying")
    operation = IntegrationOperation(key=key, channel=channel, status="pending")
    db.add(operation)
    try:
        db.commit()  # durable intent before external write; concurrent attempts cannot both send
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Operation already started")
    try:
        result = action()
    except Exception as exc:
        if isinstance(exc, HTTPException) and exc.status_code in (400, 503):
            db.delete(operation)  # request was rejected locally, before an external write
        else:
            operation.status = "uncertain"
        db.commit()
        raise
    operation.status = "succeeded"
    operation.result = json.dumps(result)
    db.commit()
    return result

class InvoiceInput(BaseModel):
    payload: dict

@router.post("/smartbill/orders/{order_id}/invoice")
def invoice(order_id: int, body: InvoiceInput, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order or order.order_type != "sale" or order.status not in ("confirmed", "completed"):
        raise HTTPException(400, "Invoice requires a confirmed sale")
    from decimal import Decimal
    from erp_fastapi.integrations.common import setting
    payload = dict(body.payload)
    if not payload.get("seriesName") or not isinstance(payload.get("client"), dict) or not payload["client"].get("name"):
        raise HTTPException(422, "Reviewed invoice series and client are required")
    payload["companyVatCode"] = setting("SMARTBILL_COMPANY_VAT_CODE")
    payload["issueDate"] = payload.get("issueDate", order.date)
    payload["currency"] = "RON"
    payload["useStock"] = False  # ERP owns the physical movements
    payload["products"] = [{"name": line.product.name, "code": line.product.code or str(line.product_id),
        "quantity": line.quantity, "measuringUnitName": line.product.unit_of_measure,
        "taxPercentage": line.vat_percent, "isTaxIncluded": False,
        "price": float(Decimal(str(line.unit_price)) * (1 - Decimal(str(line.discount_percent)) / 100))}
        for line in order.items]
    order.version += 1  # serialize invoice intent against concurrent order changes
    return execute_operation(db, f"invoice:{order_id}", "smartbill", lambda: smartbill.create_invoice(payload))

@router.get("/smartbill/orders/{order_id}/invoice.pdf")
def invoice_pdf(order_id: int, db: Session = Depends(get_db)):
    op = db.query(IntegrationOperation).filter_by(key=f"invoice:{order_id}", status="succeeded").first()
    if not op:
        raise HTTPException(404, "Confirmed invoice not found")
    result = json.loads(op.result)
    return Response(smartbill.fetch_invoice_pdf(result["series"], result["number"]), media_type="application/pdf")

@router.get("/operations")
def operations(db: Session = Depends(get_db)):
    return [{"id": o.id, "key": o.key, "channel": o.channel, "status": o.status, "result": o.result}
            for o in db.query(IntegrationOperation).order_by(IntegrationOperation.id.desc()).limit(200)]


class EmagImportInput(BaseModel):
    external_id: int = Field(gt=0)
    partner_id: int
    partner_type: Literal["company", "person"] = "company"

@router.post("/emag/orders/import")
def import_emag(body: EmagImportInput, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    existing = db.query(ExternalOrder).filter_by(channel="emag", external_id=str(body.external_id)).first()
    if existing:
        return {"order_id": existing.order_id, "created": False}
    records = emag.fetch_emag_orders({"id": body.external_id})
    raw = next((r for r in records if str(r.get("id")) == str(body.external_id)), None)
    if raw is None:
        raise HTTPException(404, "eMAG order not found")
    if raw.get("status") not in (1, 2, 3):
        raise HTTPException(409, "Only open eMAG orders can be imported")
    # Do not silently drop shipping, vouchers, SGR or foreign-currency adjustments.
    if float(raw.get("shipping_tax", 0) or 0) or raw.get("vouchers"):
        raise HTTPException(422, "Shipping/voucher adjustments require a reviewed normalized order via /integrations/orders/import")
    lines = []
    for item in raw.get("products", []):
        if item.get("status") == 0:
            continue
        if item.get("product_voucher_split") or item.get("recycle_warranties") or item.get("currency", "RON") != "RON":
            raise HTTPException(422, "Fiscal adjustments require a reviewed normalized order")
        mapping = db.query(ProductMapping).filter_by(channel="emag", external_id=str(item.get("product_id"))).first()
        if not mapping:
            raise HTTPException(422, "An eMAG product has no ERP mapping")
        product = db.get(Product, mapping.product_id)
        lines.append({"product_id": product.id, "quantity": item["quantity"],
                      "unit_price": float(item["sale_price"]), "vat_percent": product.vat_percent})
    normalized = ImportedOrder(channel="emag", external_id=str(body.external_id), order=OrderCreate(
        order_type="sale", partner_id=body.partner_id, partner_type=body.partner_type,
        date=str(raw["date"])[:10], status="draft", items=lines,
        notes="Imported from eMAG; review customer, VAT and totals before confirmation"))
    return import_order(normalized, db, user)

class ReconcileInput(BaseModel):
    outcome: Literal["not_sent", "succeeded"]
    note: str = Field(min_length=10, max_length=1000)
    series: str | None = None
    number: str | None = None

@router.post("/operations/{operation_id}/reconcile")
def reconcile(operation_id: int, body: ReconcileInput, db: Session = Depends(get_db)):
    operation = db.get(IntegrationOperation, operation_id)
    if not operation or operation.status != "uncertain":
        raise HTTPException(409, "Only uncertain operations can be reconciled")
    if body.outcome == "not_sent":
        # Preserve an audit record while releasing the original operation key for an explicit retry.
        operation.key = f"reconciled:{operation.id}:{operation.key}"[:200]
        operation.status = "confirmed_absent"
        operation.result = json.dumps({"note": body.note})
    else:
        if operation.channel == "smartbill":
            if not body.series or not body.number:
                raise HTTPException(422, "Confirmed invoice series and number are required")
            result = {"series": body.series, "number": body.number, "reconciliation_note": body.note}
        else:
            result = {"updated": True, "reconciliation_note": body.note}
        operation.status = "succeeded"
        operation.result = json.dumps(result)
    db.commit()
    return {"status": operation.status}


@router.get("/status")
def integration_status():
    import os
    required = {"emag": ["EMAG_USERNAME", "EMAG_PASSWORD"],
                "smartbill": ["SMARTBILL_EMAIL", "SMARTBILL_TOKEN", "SMARTBILL_COMPANY_VAT_CODE"],
                "shopify": ["SHOPIFY_SHOP", "SHOPIFY_ACCESS_TOKEN"]}
    return {"enabled": os.getenv("INTEGRATIONS_ENABLED", "false").lower() == "true",
            "providers": {name: {"configured": all(os.getenv(k) for k in keys),
                                "missing": [k for k in keys if not os.getenv(k)]} for name, keys in required.items()}}
