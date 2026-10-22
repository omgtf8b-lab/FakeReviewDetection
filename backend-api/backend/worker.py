"""Run --once for maintenance; add --deliver only after configuring providers."""
import argparse
import json
import time
from datetime import datetime,timezone
from database import SessionLocal
import extended_models as ex
import models
from services.providers import deliver, queue_alert
from services.search import health,reindex
from services.intelligence import shop_trust


def tick(deliver_messages=False):
    with SessionLocal() as db:
        pending=db.query(ex.SearchEvent).filter_by(status='queued').all()
        if pending and health()['available']:
            reindex(db)
            for event in pending:event.status='done'
            db.commit()
        week=datetime.now(timezone.utc).strftime('%G-W%V')
        marker=db.get(ex.Setting,'weekly_report')
        if not marker or marker.value!=week:
            for shop, in db.query(models.Product.shop_id).distinct():
                summary=shop_trust(db,shop,True)
                ratio = summary['fake_percentage']
                message = f"Tổng hợp lũy kế tại {week}: {summary['total_reviews']} review; tỷ lệ đáng ngờ {str(ratio)+'%' if ratio is not None else 'chưa có dữ liệu'}."
                db.add(ex.Notification(user_id=shop,message=message))
                queue_alert(db,shop,message)
            marker=marker or ex.Setting(key='weekly_report');marker.value=week;db.add(marker);db.commit()
        delivered=0
        if deliver_messages:
            for row in db.query(ex.Outbox).filter_by(status='queued').limit(50):
                try:deliver(row);row.status='sent';delivered+=1
                except Exception as exc:
                    row.status='failed'
                    # Log only exception type: tokens/credentials must not leak into logs.
                    print(f'Outbox {row.id}: {type(exc).__name__}',flush=True)
                db.commit()
        return {'search_events':len(pending),'delivered':delivered,'week':week}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--once',action='store_true');p.add_argument('--deliver',action='store_true');args=p.parse_args()
    while True:
        try:print(json.dumps(tick(args.deliver)),flush=True)
        except Exception as exc:print(type(exc).__name__,str(exc)[:200],flush=True)
        if args.once:break
        time.sleep(30)
