from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from erp_fastapi.config import CORS_ORIGINS
from erp_fastapi.database import engine, Base
from erp_fastapi.routers import auth, users, roles, companies, people, products, inventory, orders, comments, documents, addresses

# Create all tables
import os
if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="ERP WLB", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
from erp_fastapi.routers import integrations
app.include_router(integrations.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(companies.router)
app.include_router(people.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(comments.router)
app.include_router(documents.router)
app.include_router(addresses.router)

# Static files for frontend
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def root():
    index = static_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"ok": True, "app": "ERP WLB", "version": "2.0.0", "docs": "/docs"}


@app.get("/health")
def health():
    from sqlalchemy import text
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "healthy"}


from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"detail": "Conflicting data or invalid reference"})

@app.exception_handler(StaleDataError)
async def concurrent_error(request: Request, exc: StaleDataError):
    return JSONResponse(status_code=409, content={"detail": "Record changed concurrently; reload and retry"})
