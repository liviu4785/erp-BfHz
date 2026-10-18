"""Do not infer historical stock movements from pre-workflow orders."""
from alembic import op
from sqlalchemy import Column, Boolean, inspect
revision = "003"
down_revision = "002"
def upgrade():
    bind = op.get_bind()
    if "workflow_managed" not in {c["name"] for c in inspect(bind).get_columns("orders")}:
        op.add_column("orders", Column("workflow_managed", Boolean, nullable=False, server_default="0"))
def downgrade():
    raise RuntimeError("Historical workflow adoption must be preserved")
