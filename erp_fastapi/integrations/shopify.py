import re
from fastapi import HTTPException
from .common import request, setting, enabled

def graphql(query, variables):
    enabled()
    shop = setting("SHOPIFY_SHOP")
    if not re.fullmatch(r"[a-zA-Z0-9-]+\.myshopify\.com", shop):
        raise HTTPException(503, "SHOPIFY_SHOP must be a myshopify.com hostname")
    result = request("POST", f"https://{shop}/admin/api/2026-07/graphql.json",
        headers={"X-Shopify-Access-Token": setting("SHOPIFY_ACCESS_TOKEN")},
        json={"query": query, "variables": variables}).json()
    if result.get("errors"):
        raise HTTPException(502, "Shopify GraphQL request failed")
    return result["data"]

def update_stock(inventory_id, location_id, quantity, compare_quantity, key):
    result = graphql("""mutation SetStock($input: InventorySetQuantitiesInput!, $key: String!) {
      inventorySetQuantities(input: $input) @idempotent(key: $key) {
        inventoryAdjustmentGroup { createdAt }
        userErrors { field message }
      }
    }""", {"input": {"name": "available", "reason": "correction", "quantities": [{
        "inventoryItemId": inventory_id, "locationId": location_id,
        "quantity": quantity, "compareQuantity": compare_quantity}]}, "key": key})["inventorySetQuantities"]
    if result.get("userErrors"):
        raise HTTPException(409, "Shopify stock changed or mapping is invalid; reload before retrying")
    return {"updated": True}
