from alembic import op
from erp_fastapi.models.integration import ExternalOrder, ProductMapping, IntegrationOperation
revision = "002"
down_revision = "001"
def upgrade():
    for model in (ExternalOrder, ProductMapping, IntegrationOperation):
        model.__table__.create(op.get_bind(), checkfirst=True)
def downgrade():
    raise RuntimeError("Integration history cannot be dropped automatically")
