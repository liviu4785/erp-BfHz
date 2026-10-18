"""eMAG API 4.5.2: filters at top level; writes wrapped in data."""
import os
from fastapi import HTTPException
from .common import request, setting, enabled

def call(resource, payload):
    enabled()
    response = request("POST", "https://marketplace-api.emag.ro/api-3/" + resource,
        auth=(setting("EMAG_USERNAME"), setting("EMAG_PASSWORD")), json=payload).json()
    if response.get("isError") is not False:
        raise HTTPException(502, "eMAG rejected the request")
    return response.get("results", [])

def fetch_emag_orders(filters=None):
    return call("order/read", filters or {"currentPage": 1, "itemsPerPage": 100})

def sync_products_to_emag(products):
    return call("product_offer/save", {"data": products})

def update_stock_in_emag(product_id, quantity):
    return sync_products_to_emag([{"id": int(product_id), "stock": [{"warehouse_id": 1, "value": quantity}]}])
