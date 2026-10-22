from sqlalchemy import select, func
from services.labels import current_label
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
import models
import schemas
from auth import get_current_user
from database import get_db
from services.prediction_service import predict_for_review
from ml.predictor import predictor
import extended_models as ex

router = APIRouter(prefix="/api/reviews", tags=["Đánh giá"])


def _review_query(db: Session):
    return db.query(models.Review).options(joinedload(models.Review.predictions))


def _list_reviews(db: Session, product_id: int | None, label: str | None, rating: float | None, page: int, page_size: int):
    query = _review_query(db)
    if product_id is not None:
        query = query.filter(models.Review.product_id == product_id)
    if rating is not None:
        query = query.filter(models.Review.rating == rating)
    if label == 'pending':
        query=query.filter(current_label().is_(None))
    elif label:
        query=query.filter(current_label()==label)
    total = query.count()
    items = query.order_by(models.Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=schemas.ReviewResponse, status_code=status.HTTP_201_CREATED, summary="Tạo đánh giá và phân tích")
def submit_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == review.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    purchase = db.query(ex.Purchase).filter_by(user_id=current_user.id, product_id=review.product_id, status='completed').first()
    if not purchase:
        raise HTTPException(403, 'Chỉ được đánh giá sau khi đơn hàng đã được người bán xác nhận hoàn tất.')
    predictor.predict(review.content)
    new_review = models.Review(product_id=review.product_id, user_id=current_user.id, rating=review.rating, content=review.content.strip())
    db.add(new_review)
    try:
        db.flush()
        predict_for_review(db, new_review, commit=False)
        db.commit()
        db.refresh(new_review)
    except Exception:
        db.rollback()
        raise
    return new_review


@router.get("/me", response_model=schemas.PaginatedReviews, summary="Xem các đánh giá của tôi")
def get_my_reviews(
    label: str | None = Query(None, pattern="^(real|fake|pending)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = _review_query(db).filter(models.Review.user_id == current_user.id)
    if label == 'pending':
        query=query.filter(current_label().is_(None))
    elif label:
        query=query.filter(current_label()==label)
    total = query.count()
    items = query.order_by(models.Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/product/{product_id}", response_model=schemas.PaginatedReviews, summary="Xem đánh giá của sản phẩm")
def get_product_reviews(
    product_id: int,
    label: str | None = Query(None, pattern="^(real|fake)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _list_reviews(db, product_id, label, None, page, page_size)


@router.get("/{review_id}", response_model=schemas.ReviewResponse, summary="Xem chi tiết đánh giá")
def get_review(review_id: int, db: Session = Depends(get_db)):
    review = _review_query(db).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Đánh giá không tồn tại")
    return review


@router.put("/{review_id}", response_model=schemas.ReviewResponse, summary="Sửa đánh giá và phân tích lại")
def update_review(review_id: int, payload: schemas.ReviewUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Đánh giá không tồn tại")
    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa đánh giá này")
    predictor.predict(payload.content if payload.content is not None else review.content)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(review, key, value.strip() if isinstance(value, str) else value)
    try:
        db.flush()
        predict_for_review(db, review, commit=False)
        db.commit()
        db.refresh(review)
    except Exception:
        db.rollback()
        raise
    return review


@router.delete("/{review_id}", response_model=schemas.MessageResponse, summary="Xóa đánh giá")
def delete_review(review_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Đánh giá không tồn tại")
    if review.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa review này")
    db.add(ex.SearchEvent(kind="review",entity_id=review.id,operation="delete"))
    db.delete(review)
    db.commit()
    return {"message": "Xóa đánh giá thành công"}


@router.get("", response_model=schemas.PaginatedReviews, summary="Tra cứu tất cả đánh giá")
def list_reviews(
    product_id: int | None = None,
    label: str | None = Query(None, pattern="^(real|fake|pending)$"),
    rating: float | None = Query(None, ge=1, le=5),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _list_reviews(db, product_id, label, rating, page, page_size)

@router.post("/{review_id}/report", response_model=schemas.ReviewReportResponse, status_code=status.HTTP_201_CREATED, summary="Báo cáo đánh giá vi phạm")
def report_review(
    review_id: int,
    payload: schemas.ReviewReportCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    existing_report = (
        db.query(models.ReviewReport)
        .filter(
            models.ReviewReport.review_id == review_id,
            models.ReviewReport.reporter_user_id == current_user.id,
        )
        .first()
    )
    if existing_report:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review already reported by this user")

    report = models.ReviewReport(
        review_id=review_id,
        reporter_user_id=current_user.id,
        reason=payload.reason,
        description=payload.description.strip() if payload.description else None,
        status="pending",
    )
    try:
        db.add(report)
        db.commit()
        db.refresh(report)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Review already reported by this user")

    return report

