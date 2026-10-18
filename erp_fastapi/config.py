import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./erp.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

if os.getenv("APP_ENV") == "production" and (SECRET_KEY == "dev-secret-key-change-in-production" or len(SECRET_KEY) < 32):
    raise RuntimeError("Production requires a random SECRET_KEY of at least 32 characters")
