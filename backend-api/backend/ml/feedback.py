"""Export only latest human-verified labels, not unresolved user allegations."""
import csv
from pathlib import Path
from sqlalchemy import select,func
import models
import extended_models as ex


def export_feedback(db,path):
    latest=select(func.max(ex.Moderation.id)).group_by(ex.Moderation.review_id)
    rows=db.query(ex.Moderation,models.Review).join(models.Review,models.Review.id==ex.Moderation.review_id).filter(ex.Moderation.id.in_(latest)).all()
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['text','label','label_source'])
        writer.writeheader()
        for moderation,review in rows:writer.writerow({'text':review.content,'label':moderation.label,'label_source':'human_moderation'})
    return len(rows)
