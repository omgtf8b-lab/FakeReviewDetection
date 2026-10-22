from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from auth import get_current_user, require_roles
from database import get_db

router = APIRouter(prefix="/api/users", tags=["Người dùng"])


@router.get("/me", response_model=schemas.UserResponse, summary="Xem hồ sơ cá nhân")
def get_current_profile(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[schemas.UserResponse], dependencies=[Depends(require_roles("admin"))], summary="Danh sách người dùng")
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.id.desc()).all()


@router.patch("/{user_id}/status", response_model=schemas.UserResponse, summary="Khóa hoặc mở khóa người dùng")
def change_user_status(user_id: int, is_active: bool, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("admin"))):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if user.id == current_user.id and not is_active:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản quản trị đang đăng nhập")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
