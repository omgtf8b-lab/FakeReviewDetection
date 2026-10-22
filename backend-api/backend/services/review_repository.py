"""Persist collection evidence before analysis. No network or model side effects."""
import hashlib
import json
from sqlalchemy.orm import Session
from extended_models import CollectionSnapshot,CollectedReview
from services.browser_diagnostics import public_collection


def encode(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def save_collection(db:Session,user_id:int,data:dict):
    """Flush an immutable dataset plus queryable review rows; caller commits."""
    data=public_collection(data)
    raw=encode({**data,'storage_schema':'review-rows-v1'})
    snapshot=CollectionSnapshot(user_id=user_id,canonical_url=data['url'],platform=data['platform'],
        source=data['source'],payload=raw,sha256=digest(raw))
    db.add(snapshot);db.flush()
    seen=set()
    for review in data['reviews']:
        key=str(review['id'])
        if key in seen:continue
        if not key or len(key)>150:raise ValueError('Invalid source review ID')
        seen.add(key);payload=encode({**review,'id':key})
        db.add(CollectedReview(snapshot_id=snapshot.id,source_review_id=key,content=review.get('text') or '',
            rating=review.get('rating'),author_id=review.get('author_id'),payload=payload,sha256=digest(payload)))
    db.flush()
    return snapshot


def load_collection(db:Session,snapshot_id:int,user_id:int):
    """Only load the owner's data, verifying evidence and normalized records."""
    snapshot=db.query(CollectionSnapshot).filter_by(id=snapshot_id,user_id=user_id).first()
    if snapshot is None:raise LookupError('Collection not found')
    if digest(snapshot.payload)!=snapshot.sha256:raise ValueError('Collection checksum mismatch')
    data=json.loads(snapshot.payload)
    rows=db.query(CollectedReview).filter_by(snapshot_id=snapshot.id).order_by(CollectedReview.id).all()
    # Old snapshots remain usable without a destructive database migration.
    if rows or data.get('storage_schema')=='review-rows-v1':
        expected={}
        for r in data['reviews']:expected.setdefault(str(r['id']),{**r,'id':str(r['id'])})
        normalized=[]
        for row in rows:
            if digest(row.payload)!=row.sha256:raise ValueError('Review checksum mismatch')
            value=json.loads(row.payload)
            if value!=expected.pop(row.source_review_id,None):raise ValueError('Review does not match evidence')
            if row.content!=(value.get('text') or '') or row.rating!=value.get('rating') or row.author_id!=value.get('author_id'):
                raise ValueError('Review index does not match evidence')
            normalized.append(value)
        if expected:raise ValueError('Missing collected review')
        data['reviews']=normalized
    return snapshot,data
