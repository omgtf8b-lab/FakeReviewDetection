import io
import json
from types import SimpleNamespace
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import main,models,extended_models as ex
from auth import get_current_user
from database import Base,get_db
from routers import product_links
from services import marketplaces
from services.marketplaces import identify_url,product_identity,parse_page,CollectionError
from services.link_analysis import analyze
from services.link_analysis import observations
from services.upload_analysis import analyze_files,InvalidMedia


def sample(reviews):
    return {'url':'https://shopee.vn/product/123/456','platform':'shopee','product':{'name':'Fixture only'},'reviews':reviews,
            'reported_total':100,'source':'test_fixture','collection_status':'reviews_collected','collection_message':'Fixture'}


@pytest.fixture
def client(monkeypatch):
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine);factory=sessionmaker(bind=engine)
    with factory() as db:
        db.add_all([models.User(id=1,email='fixture1@example.com',password_hash='test',role='buyer'),models.User(id=2,email='fixture2@example.com',password_hash='test',role='buyer')]);db.commit()
    def override():
        with factory() as db:yield db
    main.app.dependency_overrides[get_db]=override
    main.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=1,role='buyer')
    monkeypatch.setattr(product_links,'SessionLocal',factory)
    with TestClient(main.app) as c:yield c,factory
    main.app.dependency_overrides.clear();engine.dispose()


@pytest.mark.parametrize('url',[
    'http://127.0.0.1/admin','https://shopee.vn.evil.example/product/1/2','https://shopee.vn@127.0.0.1/a',
    'file:///etc/passwd','https://shopee.vn:9000/product/1/2','https://evil.example/shopee.vn/a',
])
def test_reject_untrusted_urls(url):
    with pytest.raises(CollectionError):identify_url(url)


@pytest.mark.parametrize('url,platform,pid',[
    ('https://shopee.vn/product/1556630007/51200696506','shopee','51200696506'),
    ('https://shopee.vn/Giay-i.1556630007.51200696506?x=1','shopee','51200696506'),
    ('https://shop.tiktok.com/vn/pdp/shirt/1730096415976294875','tiktok_shop','1730096415976294875'),
    ('https://www.lazada.vn/products/pdp-i13326005147-s116386241186.html','lazada','13326005147'),
])
def test_actual_link_patterns(url,platform,pid):
    value=product_identity(url);assert value['platform']==platform and value['product_id']==pid


def test_redirect_cannot_escape_platform(monkeypatch):
    import httpx
    requests=[];original=httpx.Client
    def handle(request):
        requests.append(str(request.url));return httpx.Response(302,headers={'location':'http://127.0.0.1/private'})
    monkeypatch.setattr(marketplaces,'public_host',lambda host:None)
    monkeypatch.setattr(httpx,'Client',lambda **kwargs:original(transport=httpx.MockTransport(handle)))
    with pytest.raises(CollectionError):marketplaces.bounded_get('https://shopee.vn/product/1/2',expected_platform='shopee')
    assert len(requests)==1


def test_captcha_is_not_product_and_jsonld_does_not_scrape_arbitrary_comments():
    with pytest.raises(CollectionError):parse_page('<title>Security Check</title><script>captcha()</script>')
    product,reviews,total=parse_page('''<script type="application/ld+json">{"@type":"Product","name":"Cable","aggregateRating":{"reviewCount":50},"review":[{"@type":"Review","reviewBody":"Đã dùng một tháng","author":{"name":"A"},"reviewRating":{"ratingValue":4}}]}</script><script type="application/ld+json">{"comment":"promotional text"}</script>''')
    assert product['name']=='Cable' and total==50 and len(reviews)==1


def test_no_reviews_never_means_real_product():
    result=analyze(sample([]));assert result['summary']['verdict']=='insufficient_data'
    assert result['summary']['signal_percentage'] is None
    assert result['summary']['product_authenticity']=='not_verified'


def test_count_distinct_records_and_skip_vietnamese_nlp():
    rows=[{'id':str(i),'text':'Sản phẩm tốt giống mô tả','language':'vi','images':[],'videos':[]} for i in range(5)]
    rows.append(rows[0].copy())
    result=analyze(sample(rows));s=result['summary']
    assert s['observed_reviews']==5 and s['signal_percentage']==100 and s['nlp_reviews']==0
    assert s['coverage']=='partial' and all(r['identity']=='not_verified' for r in result['reviews'])


def test_product_observations_deduplicate_and_handle_negative_phrase():
    result=observations([{'id':'1','text':'Chất lượng không tốt'},{'id':'2','text':'Chất lượng không tốt'}])
    assert result['distinct_texts']==1
    assert result['aspects'][0]['negative_mentions']==1 and result['aspects'][0]['positive_mentions']==0


def png():
    stream=io.BytesIO();Image.new('RGB',(256,256),'red').save(stream,format='PNG');return stream.getvalue()


def test_image_and_video_decoding_and_no_fake_probability(tmp_path,monkeypatch):
    result=analyze_files([('one.png',png()),('two.png',png())])
    assert result['duplicates'] and result['summary']['signal_percentage']==100
    assert 'fake_probability' not in result['files'][0]
    with pytest.raises(InvalidMedia):analyze_files([('fake.png',b'not a real image')])
    import cv2,numpy as np
    monkeypatch.setenv('MEDIA_TEMP_DIR',str(tmp_path))
    path=tmp_path/'fixture.mp4';writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),10,(64,64))
    assert writer.isOpened()
    for i in range(20):writer.write(np.full((64,64,3),i*10,dtype=np.uint8))
    writer.release();video=analyze_files([('fixture.mp4',path.read_bytes())])['files'][0]
    assert video['kind']=='video' and video['frames_sampled']==6


def test_owned_jobs_import_and_upload(client,monkeypatch):
    c,factory=client
    monkeypatch.setattr(product_links,'collect',lambda url,limit:sample([]))
    queued=c.post('/api/product-links',json={'url':'https://shopee.vn/product/123/456'})
    assert queued.status_code==202
    jid=queued.json()['id'];response=c.get(f'/api/product-links/{jid}')
    assert response.json()['status']=='completed' and response.json()['result']['summary']['signal_percentage'] is None
    imported=c.post('/api/product-links/import',json={'url':'https://shopee.vn/product/123/456','reviews':[{'id':'one','text':'Đẹp','language':'vi'}]})
    assert imported.status_code==202
    result=c.get(f"/api/product-links/{imported.json()['id']}").json()['result']
    assert result['source']=='user_supplied_review_import'
    assert c.post('/api/product-links/media',files=[('files',('x.png',png(),'image/png'))]).status_code==200
    assert c.post('/api/product-links/media',files=[('files',('x.png',b'fake','image/png'))]).status_code==422
    main.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=2,role='buyer')
    assert c.get(f'/api/product-links/{jid}').status_code==404
    assert c.get('/api/product-links').json()==[]


def test_only_staff_can_view_cross_user_metrics(client):
    c,_=client
    assert c.get('/api/product-links/admin/summary').status_code==403
    main.app.dependency_overrides[get_current_user]=lambda:SimpleNamespace(id=1,role='admin')
    response=c.get('/api/product-links/admin/summary')
    assert response.status_code==200 and response.json()['total_checks']==0
