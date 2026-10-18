from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.user import User
from erp_fastapi.schemas.user import UserOut, UserUpdate, UserCreate
from erp_fastapi.auth import hash_password
from erp_fastapi.auth import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    users = db.query(User).all()
    return [
        UserOut(
            id=u.id, name=u.name, email=u.email, is_active=u.is_active,
            role_id=u.role_id, role_name=u.role.name if u.role else None,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=u.id, name=u.name, email=u.email, is_active=u.is_active,
        role_id=u.role_id, role_name=u.role.name if u.role else None,
    )


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == _.id and (payload.is_active is False or ("role_id" in payload.model_fields_set and payload.role_id != _.role_id)):
        raise HTTPException(409, "Administrators cannot deactivate or demote themselves")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(u, field, value)
    db.commit()
    db.refresh(u)
    return UserOut(
        id=u.id, name=u.name, email=u.email, is_active=u.is_active,
        role_id=u.role_id, role_name=u.role.name if u.role else None,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == _.id:
        raise HTTPException(409, "Administrators cannot delete themselves")
    db.delete(u)
    db.commit()


@router.post("/", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=payload.name, email=payload.email, hashed_password=hash_password(payload.password), role_id=payload.role_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(id=user.id, name=user.name, email=user.email, is_active=user.is_active, role_id=user.role_id,
                   role_name=user.role.name if user.role else None)
