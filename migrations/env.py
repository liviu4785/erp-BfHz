from alembic import context
from erp_fastapi.database import engine, Base
import erp_fastapi.models

def run():
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
run()
