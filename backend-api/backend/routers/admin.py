from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
import schemas
from auth import require_roles
from database import get_db

router = APIRouter(prefix="/api/admin", tags=["Quản trị"])


@router.get("/reviews", response_model=list[schemas.ReviewResponse], dependencies=[Depends(require_roles("admin", "engineer"))], summary="Xem danh sách đánh giá")
def admin_reviews(db: Session = Depends(get_db)):
    reviews = db.query(models.Review).order_by(models.Review.created_at.desc()).limit(200).all()
    return reviews


@router.delete("/reviews/{review_id}", response_model=schemas.MessageResponse, summary="Xóa đánh giá")
def admin_delete_review(review_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("admin"))):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Đánh giá không tồn tại")
    db.delete(review)
    db.commit()
    return {"message": "Quản trị viên đã xóa đánh giá"}


@router.patch("/users/{user_id}/role", response_model=schemas.UserResponse, summary="Đổi vai trò người dùng")
def change_role(user_id: int, payload: schemas.RoleUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_roles("admin"))):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/products/{product_id}/verification", response_model=schemas.ProductResponse, summary="Xác nhận hoặc thu hồi mã sản phẩm")
def change_product_verification(
    product_id: int,
    payload: schemas.ProductVerificationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("admin")),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    product.verification_status = payload.verification_status
    product.is_verified = payload.verification_status == "verified"
    if payload.verification_note is not None:
        product.verification_note = payload.verification_note.strip()
    db.commit()
    db.refresh(product)
    return product

@router.get("/review-reports", response_model=list[schemas.ReviewReportResponse], dependencies=[Depends(require_roles("admin", "engineer"))], summary="Xem danh sách báo cáo đánh giá")
def admin_review_reports(db: Session = Depends(get_db)):
    reports = db.query(models.ReviewReport).order_by(models.ReviewReport.created_at.desc()).limit(200).all()
    return reports

