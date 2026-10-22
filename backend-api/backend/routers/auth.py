from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models
import schemas
from auth import create_access_token, get_current_user, hash_password, verify_password
from database import get_db
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Xác thực"])
legacy_router = APIRouter(prefix="/api", tags=["Xác thực"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, summary="Đăng ký tài khoản")
def register_user(user: schemas.UserAuth, db: Session = Depends(get_db)):
    email = user.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")
    new_user = models.User(email=email, password_hash=hash_password(user.password), role="buyer")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.TokenResponse, summary="Đăng nhập")
def login_user(user: schemas.UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email.lower()).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không đúng")
    token = create_access_token(db_user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": db_user,
    }


@router.get("/me", response_model=schemas.UserResponse, summary="Xem tài khoản đang đăng nhập")
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@legacy_router.post("/register", summary="Đăng ký tài khoản (tương thích phiên bản cũ)")
def legacy_register(user: schemas.UserAuth, db: Session = Depends(get_db)):
    email = user.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký.")
    new_user = models.User(email=email, password_hash=hash_password(user.password), role="buyer")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Đăng ký thành công!", "user_id": new_user.id, "role": new_user.role}


@legacy_router.post("/login", summary="Đăng nhập (tương thích phiên bản cũ)")
def legacy_login(user: schemas.UserAuth, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email.lower()).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không đúng")
    token = create_access_token(db_user)
    return {
        "message": "Đăng nhập thành công",
        "user_id": db_user.id,
        "role": db_user.role,
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }
