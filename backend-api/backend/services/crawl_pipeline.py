"""Public library interface: URL -> local database -> analysis of saved evidence."""
from services.collection_strategy import collect_bounded
from services.marketplaces import identify_url
from services.review_repository import save_collection,load_collection
from services.link_analysis import analyze


def crawl_to_database(db,user_id,url,limit=50,mode='auto',collector=None):
    """Commit evidence even when no reviews were accessible; never invent rows."""
    _,url=identify_url(url)
    if not 1<=limit<=200:raise ValueError('Review limit must be between 1 and 200')
    if mode not in ('auto','browser','http'):raise ValueError('Unknown collection mode')
    collector=collector or collect_bounded
    data=collector(url,limit) if mode=='auto' else collector(url,limit,mode=mode)
    snapshot=save_collection(db,user_id,data)
    db.commit();db.refresh(snapshot)
    return snapshot


def analyze_from_database(db,snapshot_id,user_id,inspect_images=False,analyzer=None):
    """Re-read and verify persisted records, without collecting a second time."""
    snapshot,data=load_collection(db,snapshot_id,user_id)
    result=(analyzer or analyze)(data,inspect_images)
    result['storage']={'snapshot_id':snapshot.id,'review_table':'collected_reviews' if data.get('storage_schema') else 'collection_snapshots_legacy_json',
        'deduplication':'source_review_id_within_snapshot','persisted_before_analysis':True}
    return snapshot,result
