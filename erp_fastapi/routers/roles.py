from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.role import Role
from erp_fastapi.models.user import User
from erp_fastapi.schemas.role import RoleCreate, RoleUpdate, RoleOut
from erp_fastapi.auth import get_current_user

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[RoleOut])
def list_roles(db: Session = Depends(get_db)):
    return db.query(Role).all()


@router.post("/", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    role = Role(**payload.model_dump())
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.put("/{role_id}", response_model=RoleOut)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(role, field, value)
    db.commit()
    db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(role)
    db.commit()
