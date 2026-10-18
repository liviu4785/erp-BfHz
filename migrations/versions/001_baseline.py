"""Adopt existing ERP tables without replacing customer data."""
from alembic import op
from sqlalchemy import Column, Integer, inspect
from erp_fastapi.database import Base
import erp_fastapi.models
revision = "001"
down_revision = None

def upgrade():
    bind = op.get_bind()
    # Existing installations contain the original tables but no Alembic revision.
    from sqlalchemy import MetaData
    frozen = MetaData()
    for table in Base.metadata.sorted_tables:
        if table.name not in ("external_orders", "product_mappings", "integration_operations"):
            copy = table.to_metadata(frozen)
            if table.name == "orders":
                copy._columns.remove(copy.c.workflow_managed)
    frozen.create_all(bind)
    if "version" not in {c["name"] for c in inspect(bind).get_columns("orders")}:
        op.add_column("orders", Column("version", Integer, nullable=False, server_default="1"))

def downgrade():
    raise RuntimeError("Baseline downgrade is intentionally disabled to preserve ERP data")
