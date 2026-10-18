import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def upgrade(path):
    env=dict(os.environ,DATABASE_URL='sqlite:///'+str(path))
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],env=env,check=True,capture_output=True)


def test_migration_adopts_original_schema_without_changing_stock(tmp_path):
    path=tmp_path/'legacy.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE orders (id INTEGER PRIMARY KEY, order_type VARCHAR(50) NOT NULL, partner_id INTEGER NOT NULL, partner_type VARCHAR(50), date VARCHAR(20) NOT NULL, status VARCHAR(50), notes VARCHAR(500))')
        db.execute("INSERT INTO orders VALUES (7, 'sale', 1, 'company', '2026-01-01', 'completed', 'preserve me')")
    upgrade(path);upgrade(path)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT id, notes, version, workflow_managed FROM orders').fetchone()==(7,'preserve me',1,0)
        assert db.execute('SELECT count(*) FROM stock_movements').fetchone()[0]==0
        assert db.execute('SELECT version_num FROM alembic_version').fetchone()[0]=='003'


def test_fresh_install_migrates(tmp_path):
    path=tmp_path/'fresh.db';upgrade(path)
    with sqlite3.connect(path) as db:
        names={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {'users','orders','inventory','stock_movements','external_orders','integration_operations'} <= names
