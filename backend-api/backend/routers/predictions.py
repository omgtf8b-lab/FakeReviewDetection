from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import models
import schemas
from auth import get_current_user, require_roles
from database import get_db
from ml.predictor import predictor
from services.prediction_service import predict_for_review
from config import settings

router = APIRouter(prefix="/api/predictions", tags=["Phát hiện đánh giá giả"])


@router.post("/analyze", response_model=schemas.PredictionDirectResponse, summary="Phân tích nội dung review")
def analyze_text(payload: schemas.PredictionDirectRequest):
    return predictor.predict(payload.content)


@router.get("/model-info", summary="Xem thông tin mô hình")
def get_model_info():
    return {
        "ready": predictor.ready,
        "model_name": settings.model_name,
        "model_version": settings.model_version,
        "model_path": settings.model_path,
        "metrics_path": settings.model_metrics_path,
        "message": "Model đã train và được load." if predictor.ready else "Chưa có model artifact; API đang dùng fallback dev-only.",
    }


@router.post("/model/reload", summary="Nạp lại mô hình")
def reload_model(current_user: models.User = Depends(require_roles("admin", "engineer"))):
    return {
        "ready": predictor.reload(),
        "message": "Đã reload model." if predictor.ready else "Không tìm thấy model artifact.",
    }


@router.post("", response_model=schemas.PredictionResponse, summary="Phân tích một review đã lưu")
def predict_review(payload: schemas.PredictionRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    review = db.query(models.Review).filter(models.Review.id == payload.review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Đánh giá không tồn tại")
    if review.user_id != current_user.id and current_user.role not in {"admin", "engineer"}:
        raise HTTPException(status_code=403, detail="Bạn không có quyền phân tích đánh giá này")
    return predict_for_review(db, review)


@router.get("/history/me", response_model=list[schemas.PredictionResponse], summary="Xem lịch sử dự đoán của tôi")
def get_my_prediction_history(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return (
        db.query(models.Prediction)
        .join(models.Review, models.Review.id == models.Prediction.review_id)
        .filter(models.Review.user_id == current_user.id)
        .order_by(models.Prediction.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{prediction_id}", response_model=schemas.PredictionResponse, summary="Xem kết quả dự đoán")
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    prediction = db.query(models.Prediction).filter(models.Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Kết quả dự đoán không tồn tại")
    return prediction
