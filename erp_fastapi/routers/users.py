from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.user import User
from erp_fastapi.schemas.user import UserOut, UserUpdate
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    users = db.query(User).all()
    return [
        UserOut(
            id=u.id, name=u.name, email=u.email, is_active=u.is_active,
            role_id=u.role_id, role_name=u.role.name if u.role else None,
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut(
        id=u.id, name=u.name, email=u.email, is_active=u.is_active,
        role_id=u.role_id, role_name=u.role.name if u.role else None,
    )


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(u, field, value)
    db.commit()
    db.refresh(u)
    return UserOut(
        id=u.id, name=u.name, email=u.email, is_active=u.is_active,
        role_id=u.role_id, role_name=u.role.name if u.role else None,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(u)
    db.commit()
