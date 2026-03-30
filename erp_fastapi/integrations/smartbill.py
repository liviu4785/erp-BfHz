"""SmartBill invoicing integration stubs."""
from typing import Dict, Any


def create_invoice(order: Dict[str, Any]) -> str:
    # TODO: send HTTP request to SmartBill API
    return "INVOICE_ID"


def fetch_invoice_pdf(invoice_id: str) -> bytes:
    # TODO: send HTTP GET to SmartBill API
    return b""


def sync_stock_to_smartbill(product_id: int, quantity: int) -> None:
    # TODO: implement API call to SmartBill
    return None
