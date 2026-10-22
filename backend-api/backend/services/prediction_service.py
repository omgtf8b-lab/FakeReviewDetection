from sqlalchemy.orm import Session
import models
from ml.predictor import predictor


def predict_for_review(db: Session, review: models.Review) -> models.Prediction:
    # Mỗi review giữ một kết quả dự đoán hiện tại để lịch sử không bị nhân bản khi sửa review.
    db.query(models.Prediction).filter(models.Prediction.review_id == review.id).delete(synchronize_session=False)
    result = predictor.predict(review.content)
    prediction = models.Prediction(review_id=review.id, **result)
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
