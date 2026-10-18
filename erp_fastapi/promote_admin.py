import argparse
from erp_fastapi.database import SessionLocal
from erp_fastapi.models import User, Role

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    with SessionLocal.begin() as db:
        user = db.query(User).filter_by(email=args.email).first()
        if not user:
            parser.error("User not found")
        role = db.query(Role).filter_by(name="admin").first()
        if not role:
            role = Role(name="admin")
            db.add(role)
            db.flush()
        user.role_id = role.id
        user.is_active = True
    print("Administrator role assigned")

if __name__ == "__main__":
    main()
