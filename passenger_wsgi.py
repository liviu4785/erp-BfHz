import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(APP_ROOT / ".env")
except Exception:
    pass

from a2wsgi import ASGIMiddleware
from erp_fastapi.main import app as asgi_app

application = ASGIMiddleware(asgi_app)
