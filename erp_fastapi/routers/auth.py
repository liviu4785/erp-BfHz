from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from erp_fastapi.database import get_db
from erp_fastapi.models.user import User
from erp_fastapi.schemas.user import UserCreate, UserOut, Token, LoginRequest
from erp_fastapi.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role_id=payload.role_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return Token(
        access_token=token,
        user=UserOut(
            id=user.id, name=user.name, email=user.email,
            is_active=user.is_active, role_id=user.role_id,
            role_name=user.role.name if user.role else None,
        ),
    )


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id)
    return Token(
        access_token=token,
        user=UserOut(
            id=user.id, name=user.name, email=user.email,
            is_active=user.is_active, role_id=user.role_id,
            role_name=user.role.name if user.role else None,
        ),
    )


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id, name=current_user.name, email=current_user.email,
        is_active=current_user.is_active, role_id=current_user.role_id,
        role_name=current_user.role.name if current_user.role else None,
    )
