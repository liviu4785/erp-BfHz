import os
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['SECRET_KEY'] = 'testing-only-secret-key-with-more-than-32-chars'
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from erp_fastapi.main import app
from erp_fastapi.database import Base, get_db
from erp_fastapi.models import User, Role, Company, Product, InventoryItem
from erp_fastapi.auth import hash_password, create_access_token

@pytest.fixture
def env():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    @event.listens_for(engine, 'connect')
    def fk(conn, rec): conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    def database():
        with sessions() as db:
            yield db
    app.dependency_overrides[get_db] = database
    with sessions.begin() as db:
        for name in ('admin','operator','viewer'):
            role=Role(name=name);db.add(role);db.flush()
            db.add(User(name=name,email=name+'@test.ro',hashed_password=hash_password('test-password'),role_id=role.id))
        db.add(Company(name='Customer'))
        db.add(Product(name='Book', code='BOOK', vat_percent=11))
        db.flush()
        db.add(InventoryItem(product_id=1,quantity=10,reserved=0))
    client=TestClient(app)
    def auth(uid=1): return {'Authorization':'Bearer '+create_access_token(uid)}
    yield client, sessions, auth
    app.dependency_overrides.clear()
    engine.dispose()
