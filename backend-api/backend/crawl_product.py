"""Local administrator CLI, using the same collection/storage pipeline as the API."""
import argparse
import json
from database import Base,engine,SessionLocal
import models
import extended_models as ex
from routers.product_links import LinkInput,validated_url,reserve,run_job


def main():
    parser=argparse.ArgumentParser(description='Collect product review evidence into the local application database.')
    parser.add_argument('--url',required=True)
    parser.add_argument('--owner-email',required=True,help='Existing local account that will own this job')
    parser.add_argument('--limit',type=int,default=10)
    parser.add_argument('--mode',choices=['auto','browser','http'],default='auto')
    args=parser.parse_args()
    body=LinkInput(url=args.url,limit=args.limit,collection_mode=args.mode)
    platform,body.url=validated_url(body.url)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user=db.query(models.User).filter_by(email=args.owner_email).first()
        if user is None:parser.error('Owner account does not exist in this database')
        job=reserve(db,user,body.url,platform);jid=job.id
    run_job(jid,body)
    with SessionLocal() as db:
        job=db.get(ex.ProductLinkAnalysis,jid);result=json.loads(job.result or '{}')
        print(json.dumps({'job_id':jid,'job_status':job.status,
            'collection_status':result.get('collection_status'),'source':result.get('source'),
            'observed_reviews':result.get('summary',{}).get('observed_reviews'),
            'reported_total':result.get('reported_total'),'snapshot_id':result.get('provenance',{}).get('snapshot_id',result.get('snapshot_id')),
            'message':result.get('collection_message') or result.get('message')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
