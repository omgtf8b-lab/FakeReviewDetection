import json
import socket
from types import SimpleNamespace
import pytest
from auth import get_current_user
import main,extended_models as ex
from routers import product_links
from services import collection_strategy
from services.browser_proxy import public_addresses,PublicProxy
from test_product_links import client,sample


def test_proxy_rejects_private_and_pins_public_dns(monkeypatch):
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))])
    with pytest.raises(ValueError):public_addresses('example.com',443)
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:[(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))])
    assert public_addresses('example.com',443)==['8.8.8.8']
    with pytest.raises(ValueError):public_addresses('example.com',8080)


def test_proxy_denies_local_connect_without_requesting_upstream():
    import http.client
    from urllib.parse import urlsplit
    with PublicProxy() as address:
        parsed=urlsplit(address);connection=http.client.HTTPConnection(parsed.hostname,parsed.port,timeout=3)
        connection.request('CONNECT','127.0.0.1:443')
        assert connection.getresponse().status==403
        connection.close()


def test_browser_is_primary_and_http_is_explicit_secondary(monkeypatch):
    browser=sample([{'id':'one','text':'Đẹp','language':'vi'}]);browser['source']='selenium_rendered_page'
    monkeypatch.setattr(collection_strategy,'collect_browser',lambda *a:browser.copy())
    monkeypatch.setattr(collection_strategy,'collect_http',lambda *a:pytest.fail('HTTP should not run after successful browser collection'))
    result=collection_strategy.collect(browser['url'])
    assert result['source']=='selenium_rendered_page' and len(result['attempts'])==1
    blocked={**sample([]),'collection_status':'access_restricted','source':'selenium_rendered_page'}
    monkeypatch.setattr(collection_strategy,'collect_browser',lambda *a:blocked.copy())
    monkeypatch.setattr(collection_strategy,'collect_http',lambda *a:sample([{'id':'two','text':'Tốt'}]))
    result=collection_strategy.collect(browser['url'])
    assert result['source']=='test_fixture' and len(result['attempts'])==2
    assert collection_strategy.collect(browser['url'],mode='browser')['collection_status']=='access_restricted'


def test_snapshot_replay_is_owned_immutable_and_does_not_fetch_again(client,monkeypatch):
    c,factory=client;calls=[]
    def collect(url,limit):calls.append(url);return sample([{'id':'one','text':'Chất lượng tốt','language':'vi'}])
    monkeypatch.setattr(product_links,'collect',collect)
    queued=c.post('/api/product-links',json={'url':'https://shopee.vn/product/123/456'}).json()
    original=c.get(f"/api/product-links/{queued['id']}").json()['result'];p=original['provenance'];sid=p['snapshot_id']
    assert p['mode']=='live' and len(p['sha256'])==64
    assert c.get(f'/api/product-links/snapshots/{sid}').json()['source']=='test_fixture'
    repeated=c.post(f'/api/product-links/snapshots/{sid}/analyze');assert repeated.status_code==202
    replay=c.get(f"/api/product-links/{repeated.json()['id']}").json()['result']['provenance']
    assert replay['mode']=='snapshot' and replay['sha256']==p['sha256'] and replay['captured_at']==p['captured_at']
    assert len(calls)==1
    with factory() as db:assert db.query(ex.CollectionSnapshot).count()==1
    main.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=2,role='buyer')
    assert c.get(f'/api/product-links/snapshots/{sid}').status_code==404
    assert c.post(f'/api/product-links/snapshots/{sid}/analyze').status_code==404
    main.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=1,role='buyer')
    with factory() as db:
        row=db.get(ex.CollectionSnapshot,sid);row.payload='{}';db.commit()
    assert c.get(f'/api/product-links/snapshots/{sid}').status_code==409
    assert c.post(f'/api/product-links/snapshots/{sid}/analyze').status_code==409


def test_manual_review_is_labelled_fallback_and_author_is_not_spoofable(client):
    c,_=client
    response=c.post('/api/product-links/import',json={'url':'https://shopee.vn/product/123/456','input_method':'form','reviews':[{'id':'own','text':'Đẹp','author_id':'someone-else','language':'vi'}]})
    assert response.status_code==202
    result=c.get(f"/api/product-links/{response.json()['id']}").json()['result']
    assert result['source']=='user_written_review' and result['provenance']['mode']=='user_input'
    assert result['reviews'][0]['author_id']=='1'


def test_browser_capture_import_preserves_unverified_source_and_time(client):
    c,factory=client
    response=c.post('/api/product-links/import',json={
        'url':'https://shopee.vn/product/123/456','input_method':'browser',
        'captured_at':'2026-10-20T08:00:00Z','reviews':[
            {'id':f'real-shape-fixture-{i}','text':'Vải mỏng nhưng đường may đều, dữ liệu kiểm thử tổng hợp.','language':'vi'} for i in range(5)]})
    assert response.status_code==202
    data=c.get('/api/product-links/'+str(response.json()['id'])).json()['result']
    assert data['source']=='browser_page_import'
    assert data['client_captured_at'].startswith('2026-10-20T08:00:00')
    assert data['summary']['observed_reviews']==5
    assert data['summary']['reviews_with_signals']==5
    assert 'chưa xác minh' in data['collection_message']
    assert data['provenance']['mode']=='user_input'
    assert data['summary']['product_authenticity']=='not_verified'


def test_stale_job_stops_polling_without_exposing_other_users(client):
    from datetime import datetime,timedelta,timezone
    c,factory=client
    with factory() as db:
        old=ex.ProductLinkAnalysis(user_id=1,url='https://shopee.vn/product/1/2',platform='shopee',status='running',created_at=datetime.now(timezone.utc)-timedelta(minutes=6))
        other=ex.ProductLinkAnalysis(user_id=2,url='https://shopee.vn/product/1/2',platform='shopee',status='running',created_at=datetime.now(timezone.utc)-timedelta(minutes=6))
        db.add_all([old,other]);db.commit();jid=old.id;other_id=other.id
    result=c.get(f'/api/product-links/{jid}').json()
    assert result['status']=='failed' and 'quá thời gian' in result['result']['message']
    assert c.get(f'/api/product-links/{other_id}').status_code==404
    with factory() as db:assert db.get(ex.ProductLinkAnalysis,other_id).status=='running'


def test_whole_collection_timeout_kills_only_own_worker(monkeypatch):
    import io,subprocess
    calls=[]
    class Worker:
        pid=99999999
        stdin=io.StringIO();stdout=io.StringIO()
        def communicate(self,*args,**kwargs):
            assert kwargs['timeout']==105
            raise subprocess.TimeoutExpired('fixture',105)
        def kill(self):calls.append('kill')
        def wait(self,timeout):return 0
    monkeypatch.setattr(collection_strategy.subprocess,'Popen',lambda *a,**k:Worker())
    monkeypatch.setattr(collection_strategy.subprocess,'run',lambda args,**k:calls.append(args))
    data=collection_strategy.collect_bounded('https://shopee.vn/product/1/2')
    assert data['collection_status']=='collection_timeout' and data['reviews']==[]
    assert 'kill' in calls
    if collection_strategy.os.name=='nt':assert ['taskkill','/PID','99999999','/T','/F'] in calls


def lazada_payload(page=1):
    return {'success':True,'model':{'item':{'itemTitle':'Fixture shirt'},
        'paging':{'totalItems':30,'totalPages':3,'currentPage':page},'items':[
        {'reviewRateId':page,'reviewContent':'Vải mỏng nhưng đường may đều','rating':4,'buyerId':55,
         'buyerEmail':'private-fixture@example.com','tradeOrderId':'private-order','buyerName':'Private name',
         'mediaList':[{'videoUrl':'https://lazvideo.lazcdn.com/sample.mp4'}]},
        {'reviewRateId':page,'reviewContent':'duplicate same ID'},
        {'reviewRateId':page+100,'reviewContent':'','rating':5}]}}


def test_lazada_public_parser_minimizes_data_and_skips_rating_only():
    from services.marketplaces import parse_lazada_review_page
    product,rows,total,pages,count=parse_lazada_review_page(lazada_payload())
    assert len(rows)==1 and rows[0]['rating']==4 and total==30 and pages==3
    assert rows[0]['videos']==['https://lazvideo.lazcdn.com/sample.mp4']
    assert 'private' not in json.dumps(rows)
    assert product['name']=='Fixture shirt'


def test_lazada_keeps_first_page_when_next_page_is_restricted(monkeypatch):
    from services import marketplaces
    calls=[]
    def get(url,**kwargs):
        calls.append(url)
        if len(calls)==1:return url,json.dumps(lazada_payload()).encode(),'application/json'
        return url,b'<title>Security Check</title>','text/html'
    monkeypatch.setattr(marketplaces,'bounded_get',get)
    monkeypatch.setattr('time.sleep',lambda *_:None)
    result=marketplaces.collect('https://www.lazada.vn/products/pdp-i123-s456.html',50)
    assert len(calls)==2 and 'pageSize=10' in calls[0]
    assert len(result['reviews'])==1 and result['pages_checked']==1
    assert result['collection_warning'] and result['collection_status']=='reviews_collected'
    assert result['source']=='lazada_public_reviews_endpoint'


def test_lazada_live_source_precedes_browser_without_double_requests(monkeypatch):
    direct=sample([{'id':'one','text':'Vải đẹp'}]);direct['platform']='lazada'
    direct['url']='https://www.lazada.vn/products/pdp-i123-s456.html'
    monkeypatch.setattr(collection_strategy,'collect_http',lambda *a:direct.copy())
    monkeypatch.setattr(collection_strategy,'collect_browser',lambda *a:pytest.fail('Browser unnecessary'))
    result=collection_strategy.collect(direct['url'])
    assert result['attempts']==[{'collector':'http','status':direct['collection_status']}]


def test_reviews_are_committed_before_analysis_and_replay_recovers(client,monkeypatch):
    from services import link_analysis
    c,factory=client;calls=[]
    def collector(url,limit):
        calls.append(url)
        return sample([{'id':'same','text':'Vải đẹp','language':'vi'},{'id':'same','text':'Vải đẹp','language':'vi'}])
    monkeypatch.setattr(product_links,'collect',collector)
    def fail_analysis(*args):
        with factory() as db:
            assert db.query(ex.CollectionSnapshot).count()==1
            assert db.query(ex.CollectedReview).count()==1
        raise RuntimeError('fixture model failure')
    monkeypatch.setattr(product_links,'analyze',fail_analysis)
    job=c.post('/api/product-links',json={'url':'https://shopee.vn/product/123/456'}).json()
    failed=c.get(f"/api/product-links/{job['id']}").json()
    assert failed['status']=='failed'
    sid=failed['result']['snapshot_id']
    rows=c.get(f'/api/product-links/snapshots/{sid}/reviews?limit=1').json()
    assert rows['total']==1 and rows['reviews'][0]['text']=='Vải đẹp'
    monkeypatch.setattr(product_links,'analyze',link_analysis.analyze)
    replay=c.post(f'/api/product-links/snapshots/{sid}/analyze').json()
    result=c.get(f"/api/product-links/{replay['id']}").json()
    assert result['status']=='completed'
    assert result['result']['storage']['persisted_before_analysis'] is True
    assert len(calls)==1
    with factory() as db:assert db.query(ex.CollectedReview).count()==1


def test_normalized_review_tampering_and_missing_rows_are_rejected(client,monkeypatch):
    c,factory=client
    monkeypatch.setattr(product_links,'collect',lambda *a:sample([{'id':'one','text':'Chất lượng tốt','language':'vi'}]))
    jid=c.post('/api/product-links',json={'url':'https://shopee.vn/product/123/456'}).json()['id']
    sid=c.get(f'/api/product-links/{jid}').json()['result']['provenance']['snapshot_id']
    main.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=2,role='buyer')
    assert c.get(f'/api/product-links/snapshots/{sid}/reviews').status_code==404
    main.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=1,role='buyer')
    with factory() as db:
        row=db.query(ex.CollectedReview).filter_by(snapshot_id=sid).one();row.content='tampered';db.commit()
    assert c.get(f'/api/product-links/snapshots/{sid}/reviews').status_code==409
    with factory() as db:db.query(ex.CollectedReview).filter_by(snapshot_id=sid).delete();db.commit()
    assert c.get(f'/api/product-links/snapshots/{sid}/reviews').status_code==409


def test_restricted_collection_stores_attempt_without_fake_reviews(client,monkeypatch):
    c,factory=client
    monkeypatch.setattr(product_links,'collect',lambda *a:{**sample([]),'collection_status':'access_restricted'})
    jid=c.post('/api/product-links',json={'url':'https://shopee.vn/product/123/456'}).json()['id']
    result=c.get(f'/api/product-links/{jid}').json()['result']
    assert result['summary']['observed_reviews']==0 and result['summary']['signal_percentage'] is None
    with factory() as db:
        assert db.query(ex.CollectionSnapshot).count()==1
        assert db.query(ex.CollectedReview).count()==0
