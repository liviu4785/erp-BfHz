import os
import httpx
from fastapi import HTTPException

def setting(name):
    value = os.getenv(name)
    if not value:
        raise HTTPException(503, f"Missing integration setting: {name}")
    return value

def enabled():
    if os.getenv("INTEGRATIONS_ENABLED", "false").lower() != "true":
        raise HTTPException(503, "External integrations are disabled")

def request(method, url, **kwargs):
    try:
        response = httpx.request(method, url, timeout=30, follow_redirects=False, **kwargs)
        response.raise_for_status()
        return response
    except httpx.HTTPError:
        # Do not expose auth headers, customer data or supplier response bodies.
        raise HTTPException(502, "External API request failed; check provider before retrying writes")
