"""Explainable behavioral rules; account risk is not NLP class confidence."""
import json
import re
from collections import Counter, defaultdict
from datetime import timedelta, datetime, timezone
import networkx as nx
import models
import extended_models as ex


def normalized(text):
    return ' '.join(re.findall(r'\w+', text.casefold(), flags=re.UNICODE))


def levels(db):
    row = db.get(ex.Setting, 'risk_thresholds')
    return json.loads(row.value) if row else {'normal_max': 50., 'suspicious_min': 70.}


def level(score, thresholds):
    return 'high' if score >= thresholds['suspicious_min'] else 'moderate' if score > thresholds['normal_max'] else 'low'


def account_risk(db, user_id, persist=False, commit=True):
    reviews = db.query(models.Review).filter_by(user_id=user_id).order_by(models.Review.created_at).all()
    duplicate_products = defaultdict(set)
    for r in reviews:
        duplicate_products[normalized(r.content)].add(r.product_id)
    results = []
    blacklist = db.get(ex.Setting, 'blacklist')
    keywords = json.loads(blacklist.value) if blacklist else []
    for r in reviews:
        reasons = []
        words = normalized(r.content).split()
        if len(words) <= 1:
            reasons.append('Nội dung chỉ có một từ hoặc một ký tự')
        if len(duplicate_products[normalized(r.content)]) >= 2:
            reasons.append('Nội dung trùng trên nhiều sản phẩm')
        matched = [k for k in keywords if k.casefold() in r.content.casefold()]
        if matched:
            reasons.append('Từ khóa cần kiểm tra theo cấu hình: ' + ', '.join(matched))
        window = [x for x in reviews if r.created_at-timedelta(hours=1) <= x.created_at <= r.created_at]
        if len(window) >= 5 and len({x.product_id for x in window}) >= 3:
            reasons.append('Ít nhất 5 review trên ít nhất 3 sản phẩm trong một giờ')
        results.append({'review_id': r.id, 'product_id': r.product_id, 'reasons': reasons, 'abnormal': bool(reasons)})
    abnormal = sum(x['abnormal'] for x in results)
    score = 100 * abnormal / len(reviews) if reviews else 0.
    result = {'user_id': user_id, 'total_reviews': len(reviews), 'abnormal_reviews': abnormal,
              'score': round(score, 2), 'level': level(score, levels(db)) if reviews else 'insufficient_data',
              'formula': '100 × review có ít nhất một dấu hiệu / tổng review',
              'evidence': results, 'note': 'Tín hiệu để kiểm tra; không tự động kết luận hoặc khóa tài khoản.'}
    if persist:
        db.add(ex.RiskSnapshot(user_id=user_id, score=score, level=result['level'], evidence=json.dumps(results, ensure_ascii=False)))
        if commit: db.commit()
    return result


def latest_prediction(db, review_id):
    return db.query(models.Prediction).filter_by(review_id=review_id).order_by(models.Prediction.id.desc()).first()


def effective_label(db, review_id):
    manual = db.query(ex.Moderation).filter_by(review_id=review_id).order_by(ex.Moderation.id.desc()).first()
    prediction = latest_prediction(db, review_id)
    return manual.label if manual else prediction.predicted_label if prediction else None


def shop_trust(db, shop_id, snapshot=False, commit=True):
    reviews = db.query(models.Review).join(models.Product).filter(models.Product.shop_id == shop_id).all()
    labels = {r.id: effective_label(db, r.id) for r in reviews}
    total = len(reviews)
    fake = sum(x == 'fake' for x in labels.values())
    analyzed = sum(x is not None for x in labels.values())
    ratio = fake / analyzed * 100 if analyzed else None
    trust = 100 - ratio if ratio is not None else None
    clean_ratings = [r.rating for r in reviews if labels[r.id] == 'real']
    daily = defaultdict(lambda: {'total': 0, 'fake': 0, 'analyzed': 0})
    for r in reviews:
        day = str(r.created_at.date())
        daily[day]['total'] += 1
        daily[day]['fake'] += labels[r.id] == 'fake'
        daily[day]['analyzed'] += labels[r.id] is not None
    if snapshot:
        day = str(datetime.now(timezone.utc).date())
        row = db.query(ex.TrustSnapshot).filter_by(shop_id=shop_id, day=day).first()
        if not row:
            row = ex.TrustSnapshot(shop_id=shop_id, day=day)
            db.add(row)
        row.total, row.fake, row.pending, row.trust_score = total, fake, total-analyzed, trust
        if commit: db.commit()
    profile = db.get(ex.Profile, shop_id)
    return {'shop_id': shop_id, 'shop_name': profile.shop_name if profile and profile.shop_name else f'Shop #{shop_id}',
        'total_reviews': total, 'analyzed_reviews': analyzed, 'pending_reviews': total-analyzed,
        'fake_reviews': fake, 'fake_percentage': round(ratio, 2) if ratio is not None else None,
        'trust_score': round(trust, 2) if trust is not None else None,
        'filtered_average_rating': round(sum(clean_ratings)/len(clean_ratings), 2) if clean_ratings else None,
        'timeline': [{'day': day, **v, 'fake_percentage': round(100*v['fake']/v['analyzed'],2) if v['analyzed'] else None} for day,v in sorted(daily.items())],
        'snapshots': [{'day': r.day, 'trust_score': r.trust_score, 'total': r.total, 'fake': r.fake} for r in db.query(ex.TrustSnapshot).filter_by(shop_id=shop_id).order_by(ex.TrustSnapshot.day).all()],
        'note': 'Tỷ lệ dựa trên review đã phân loại/kiểm duyệt; số mẫu nhỏ chưa đủ đánh giá shop.'}


def network_scan(db, persist=False):
    reviews = db.query(models.Review).all()
    by_product = defaultdict(list)
    bipartite = nx.Graph()
    for r in reviews:
        by_product[r.product_id].append(r)
        bipartite.add_edge(f'u{r.user_id}', f'p{r.product_id}', type='review')
    coordinated = defaultdict(lambda: {'products': set(), 'matches': []})
    for pid, rows in by_product.items():
        for i, a in enumerate(rows):
            for b in rows[i+1:]:
                if a.user_id == b.user_id:
                    continue
                repeated = normalized(a.content) == normalized(b.content)
                close = abs((a.created_at-b.created_at).total_seconds()) <= 600 and a.rating == b.rating
                if repeated or close:
                    pair = tuple(sorted((a.user_id, b.user_id)))
                    coordinated[pair]['products'].add(pid)
                    coordinated[pair]['matches'].append({'product_id': pid, 'review_ids': [a.id,b.id], 'same_text': repeated, 'same_rating_within_10_minutes': close})
    graph = nx.Graph()
    for (a,b), evidence in coordinated.items():
        # Require at least two shared products, not mere participation in a popular product.
        if len(evidence['products']) >= 2:
            graph.add_edge(a,b,weight=len(evidence['products']))
    communities = nx.community.louvain_communities(graph, seed=42, weight='weight') if graph.number_of_edges() else []
    clusters = []
    for group in communities:
        edges = [{'users': [a,b], 'products': sorted(coordinated[tuple(sorted((a,b)))]['products']),
                  'matches': coordinated[tuple(sorted((a,b)))]['matches']} for a,b in graph.subgraph(group).edges]
        item = {'members': sorted(group), 'evidence': edges, 'status': 'needs_review'}
        if persist:
            row = ex.FraudCluster(members=json.dumps(item['members']), evidence=json.dumps(edges))
            db.add(row)
        clusters.append(item)
    if persist:
        db.commit()
    return {'algorithm': 'Louvain, seed=42', 'clusters': clusters,
            'nodes': [{'id': n, 'kind': 'user' if str(n).startswith('u') else 'product'} for n in bipartite.nodes],
            'links': [{'source': a, 'target': b} for a,b in bipartite.edges],
            'note': 'Cụm hành vi phối hợp để kiểm tra, chưa phải nhãn gian lận đã xác minh.'}
