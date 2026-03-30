from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from erp_fastapi.config import CORS_ORIGINS
from erp_fastapi.database import engine, Base
from erp_fastapi.routers import auth, users, roles, companies, people, products, inventory, orders, comments, documents, addresses

# Create all tables
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
    return {"status": "healthy"}
