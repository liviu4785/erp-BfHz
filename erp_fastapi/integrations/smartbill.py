"""Explicit SmartBill invoice requests; no fabricated invoice IDs."""
from fastapi import HTTPException
from .common import request, setting, enabled
BASE = "https://ws.smartbill.ro/SBORO/api"

def create_invoice(payload):
    enabled()
    if payload.get("companyVatCode") != setting("SMARTBILL_COMPANY_VAT_CODE"):
        raise HTTPException(400, "Invoice company does not match configured issuer")
    result = request("POST", BASE + "/invoice/v2", auth=(setting("SMARTBILL_EMAIL"), setting("SMARTBILL_TOKEN")), json=payload).json()
    if result.get("errorText") or not result.get("series") or not result.get("number"):
        raise HTTPException(502, "SmartBill did not confirm an invoice number")
    return {"series": result["series"], "number": str(result["number"])}

def fetch_invoice_pdf(series, number):
    enabled()
    response = request("GET", BASE + "/invoice/pdf", auth=(setting("SMARTBILL_EMAIL"), setting("SMARTBILL_TOKEN")),
        params={"cif": setting("SMARTBILL_COMPANY_VAT_CODE"), "seriesname": series, "number": number})
    if not response.content.startswith(b"%PDF"):
        raise HTTPException(502, "SmartBill returned an invalid PDF")
    return response.content
