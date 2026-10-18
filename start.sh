#!/bin/sh
set -eu
alembic upgrade head
exec uvicorn erp_fastapi.main:app --host 0.0.0.0 --port "${PORT:-8000}"
