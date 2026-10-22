"""Report datasets, always scoped before export."""
import json
from pathlib import Path
from fastapi import HTTPException
import models
import extended_models as ex
from services.intelligence import effective_label, shop_trust


def report_rows(db, user, kind):
    products = db.query(models.Product)
    if user.role == 'seller':
        products = products.filter(models.Product.shop_id == user.id)
    if kind == 'reviews':
        reviews = db.query(models.Review).filter(models.Review.product_id.in_(products.with_entities(models.Product.id)))
        return [['Review ID','Product ID','User ID','Rating','Effective label','Content']] + [
            [r.id,r.product_id,r.user_id,r.rating,effective_label(db,r.id) or 'pending',r.content]
            for r in reviews.order_by(models.Review.id)]
    if kind == 'shops':
        rows = [['Shop ID','Shop','Total reviews','Analyzed','Suspicious (%)','Trust score']]
        for shop_id, in products.with_entities(models.Product.shop_id).distinct():
            s = shop_trust(db, shop_id)
            rows.append([shop_id,s['shop_name'],s['total_reviews'],s['analyzed_reviews'],s['fake_percentage'],s['trust_score']])
        return rows
    if kind == 'categories':
        rows = [['Category','Products','Reviews','Analyzed','Suspicious','Suspicious (%)']]
        groups = {}
        for p in products:
            group = groups.setdefault(p.category or 'Uncategorized', [0,0,0,0])
            group[0] += 1
            for r in db.query(models.Review).filter_by(product_id=p.id):
                label = effective_label(db,r.id)
                group[1] += 1; group[2] += int(label in ('real','fake')); group[3] += int(label == 'fake')
        return rows + [[name,*values,round(100*values[3]/values[2],2) if values[2] else None] for name,values in sorted(groups.items())]
    if user.role not in ('admin','engineer'):
        raise HTTPException(403,'Chỉ quản trị viên và kỹ sư được xuất dữ liệu này')
    if kind == 'clusters':
        return [['Cluster ID','Detected at','Members','Evidence']] + [[r.id,r.detected_at,r.members,r.evidence] for r in db.query(ex.FraudCluster).order_by(ex.FraudCluster.id)]
    rows = [['Model','Version','Accuracy','Macro F1','ROC AUC','Test size']]
    for path in sorted((Path(__file__).resolve().parents[1]/'ml/models').glob('*.json')):
        try: data = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError,OSError): continue
        if isinstance(data,dict) and data.get('model_name'):
            rows.append([data['model_name'],data.get('version'),data.get('accuracy'),data.get('classification_report',{}).get('macro avg',{}).get('f1-score'),data.get('roc_auc'),data.get('test_size')])
    return rows
