"""Explicit local admin bootstrap; never exposes a public first-user endpoint."""
import argparse
from getpass import getpass
from erp_fastapi.database import SessionLocal
from erp_fastapi.models import User, Role
from erp_fastapi.auth import hash_password

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Administrator")
    args = parser.parse_args()
    password = getpass("Admin password (at least 12 characters): ")
    if len(password) < 12:
        parser.error("Password must have at least 12 characters")
    with SessionLocal.begin() as db:
        roles = {}
        for name in ("admin", "operator", "viewer"):
            role = db.query(Role).filter_by(name=name).first()
            if not role:
                role = Role(name=name)
                db.add(role)
                db.flush()
            roles[name] = role
        user = db.query(User).filter_by(email=args.email).first()
        if user:
            parser.error("Account already exists; use promote-admin instead")
        db.add(User(name=args.name, email=args.email, hashed_password=hash_password(password), role_id=roles["admin"].id))
    print("Administrator created")

if __name__ == "__main__":
    main()
