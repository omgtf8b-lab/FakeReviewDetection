from sqlalchemy import select, func
import models
from extended_models import Moderation


def current_label():
    manual=select(Moderation.label).where(Moderation.review_id==models.Review.id).order_by(Moderation.id.desc()).limit(1).correlate(models.Review).scalar_subquery()
    predicted=select(models.Prediction.predicted_label).where(models.Prediction.review_id==models.Review.id).order_by(models.Prediction.id.desc()).limit(1).correlate(models.Review).scalar_subquery()
    return func.coalesce(manual,predicted)
