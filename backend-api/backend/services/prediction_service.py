from sqlalchemy.orm import Session
import models
from ml.predictor import predictor


def predict_for_review(db: Session, review: models.Review, commit=True) -> models.Prediction:
    # Keep versioned predictions for auditing and model comparisons.
    import hashlib, json, time
    from extended_models import ModelExperiment, ModelObservation
    from ml.predictor import version_predictor
    experiment = db.query(ModelExperiment).filter_by(active=True).order_by(ModelExperiment.id.desc()).first()
    variant = None
    selected = predictor
    if experiment:
        bucket = int(hashlib.sha256(f'{experiment.id}:{review.user_id}'.encode()).hexdigest()[:8], 16) % 100
        variant = 'B' if bucket < experiment.traffic_b else 'A'
        selected = version_predictor(experiment.model_b if variant == 'B' else experiment.model_a)
    start = time.perf_counter()
    result = selected.predict(review.content)
    if experiment:
        db.add(ModelObservation(experiment_id=experiment.id, review_id=review.id, variant=variant, result=json.dumps(result), latency_ms=(time.perf_counter()-start)*1000))
    prediction = models.Prediction(review_id=review.id, **result)
    db.add(prediction)
    from extended_models import SearchEvent
    db.add(SearchEvent(kind='review', entity_id=review.id, operation='upsert'))
    db.flush()
    db.expire(review, ['predictions'])
    from extended_models import Watch, Notification
    from services.intelligence import account_risk, shop_trust
    account_risk(db, review.user_id, persist=True, commit=False)
    shop_trust(db, review.product.shop_id, snapshot=True, commit=False)
    if result['predicted_label'] == 'fake':
        for watch in db.query(Watch).filter_by(product_id=review.product_id).all():
            message = f'Sản phẩm #{review.product_id} có review #{review.id} được mô hình gắn nhãn đáng ngờ.'
            db.add(Notification(user_id=watch.user_id, message=message))
            from services.providers import queue_alert
            queue_alert(db,watch.user_id,message)
    if commit:
        db.commit()
        db.refresh(prediction)
    return prediction
