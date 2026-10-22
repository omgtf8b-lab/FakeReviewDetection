from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
import models
import schemas
from auth import require_roles, get_current_user
from database import get_db

router = APIRouter(prefix="/api/statistics", tags=["Thống kê"])


@router.get("/overview", response_model=schemas.StatisticsOverview, dependencies=[Depends(require_roles("admin", "engineer"))], summary="Thống kê tổng quan")
def overview(db: Session = Depends(get_db)):
    total_reviews = db.query(models.Review).count()
    fake_reviews = db.query(models.Prediction).filter(models.Prediction.predicted_label == "fake").count()
    real_reviews = db.query(models.Prediction).filter(models.Prediction.predicted_label == "real").count()
    pending_reviews = max(total_reviews - fake_reviews - real_reviews, 0)
    fake_percentage = round((fake_reviews / total_reviews * 100) if total_reviews else 0, 2)
    return {
        "total_users": db.query(models.User).count(),
        "total_products": db.query(models.Product).count(),
        "total_reviews": total_reviews,
        "total_predictions": db.query(models.Prediction).count(),
        "fake_reviews": fake_reviews,
        "real_reviews": real_reviews,
        "pending_reviews": pending_reviews,
        "fake_percentage": fake_percentage,
    }


@router.get("/me", response_model=schemas.MyStatisticsOverview, summary="Thống kê của tài khoản đang đăng nhập")
def my_overview(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    my_reviews = db.query(models.Review).filter(models.Review.user_id == current_user.id).count()
    my_predictions = (
        db.query(models.Prediction)
        .join(models.Review, models.Review.id == models.Prediction.review_id)
        .filter(models.Review.user_id == current_user.id)
        .count()
    )
    my_fake_reviews = (
        db.query(models.Prediction)
        .join(models.Review, models.Review.id == models.Prediction.review_id)
        .filter(models.Review.user_id == current_user.id, models.Prediction.predicted_label == "fake")
        .count()
    )
    my_real_reviews = (
        db.query(models.Prediction)
        .join(models.Review, models.Review.id == models.Prediction.review_id)
        .filter(models.Review.user_id == current_user.id, models.Prediction.predicted_label == "real")
        .count()
    )
    my_pending_reviews = max(my_reviews - my_fake_reviews - my_real_reviews, 0)
    return {
        "total_products": db.query(models.Product).count(),
        "my_reviews": my_reviews,
        "my_predictions": my_predictions,
        "my_fake_reviews": my_fake_reviews,
        "my_real_reviews": my_real_reviews,
        "my_pending_reviews": my_pending_reviews,
        "my_fake_percentage": round((my_fake_reviews / my_reviews * 100) if my_reviews else 0, 2),
    }


@router.get("/products/{product_id}", response_model=schemas.ProductStatistics, summary="Thống kê theo sản phẩm")
def product_statistics(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")
    total_reviews = db.query(models.Review).filter(models.Review.product_id == product_id).count()
    fake_reviews = (
        db.query(models.Prediction).join(models.Review).filter(models.Review.product_id == product_id, models.Prediction.predicted_label == "fake").count()
    )
    real_reviews = (
        db.query(models.Prediction).join(models.Review).filter(models.Review.product_id == product_id, models.Prediction.predicted_label == "real").count()
    )
    avg_rating = db.query(func.avg(models.Review.rating)).filter(models.Review.product_id == product_id).scalar() or 0
    return {
        "product_id": product_id,
        "total_reviews": total_reviews,
        "fake_reviews": fake_reviews,
        "real_reviews": real_reviews,
        "average_rating": round(float(avg_rating), 2),
        "fake_percentage": round((fake_reviews / total_reviews * 100) if total_reviews else 0, 2),
    }
