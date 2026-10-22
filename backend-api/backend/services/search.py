import os
import httpx
from fastapi import HTTPException
import models
from services.intelligence import effective_label

URL = os.getenv('ELASTICSEARCH_URL', 'http://127.0.0.1:9200').rstrip('/')
INDEX = 'fake-review-search-v1'


def client():
    return httpx.Client(base_url=URL, timeout=httpx.Timeout(30,connect=3), auth=(os.getenv('ELASTICSEARCH_USER','elastic'), os.getenv('ELASTICSEARCH_PASSWORD','')) if os.getenv('ELASTICSEARCH_PASSWORD') else None)


def health():
    try:
        with client() as c:
            response=c.get('/'); response.raise_for_status()
        return {'available':True,'version':response.json().get('version',{}).get('number')}
    except httpx.HTTPError:
        return {'available':False,'message':'Elasticsearch chưa chạy. Khởi động docker compose --profile search up -d.'}


def reindex(db):
    lines=[]
    import json
    for p in db.query(models.Product).all():
        lines.extend([json.dumps({'index':{'_id':f'p{p.id}'}}),json.dumps({'kind':'product','entity_id':p.id,'text':f'{p.name} {p.description or ""}', 'category':p.category,'shop_id':p.shop_id})])
    for r in db.query(models.Review).all():
        lines.extend([json.dumps({'index':{'_id':f'r{r.id}'}}),json.dumps({'kind':'review','entity_id':r.id,'text':r.content,'product_id':r.product_id,'user_id':r.user_id,'label':effective_label(db,r.id),'rating':r.rating,'created_at':r.created_at.isoformat()})])
    try:
        with client() as c:
            c.delete('/'+INDEX)
            response=c.put('/'+INDEX,json={'settings':{'number_of_shards':1,'number_of_replicas':0},'mappings':{'properties':{'text':{'type':'text'},'kind':{'type':'keyword'},'label':{'type':'keyword'},'category':{'type':'keyword'},'created_at':{'type':'date'}}}})
            response.raise_for_status()
            if lines:
                response=c.post(f'/{INDEX}/_bulk?refresh=true',content='\n'.join(lines)+'\n',headers={'Content-Type':'application/x-ndjson'})
                response.raise_for_status()
                if response.json().get('errors'):raise HTTPException(502,'Có bản ghi index bị lỗi')
        return {'indexed':len(lines)//2}
    except httpx.HTTPError as exc:
        raise HTTPException(503,'Không kết nối được Elasticsearch; dữ liệu SQL vẫn được giữ nguyên.') from exc


def search(q,kind,label,page,page_size):
    filters=[{'term':{'kind':kind}}] if kind else []
    if label:filters.append({'term':{'label':label}})
    query={'bool':{'must':[{'match':{'text':q}}] if q else [{'match_all':{}}],'filter':filters}}
    try:
        with client() as c:
            response=c.post(f'/{INDEX}/_search',json={'query':query,'from':(page-1)*page_size,'size':page_size,'track_total_hits':True,'highlight':{'fields':{'text':{}}}})
            response.raise_for_status()
        hits=response.json()['hits']
        return {'engine':'elasticsearch','total':hits['total']['value'],'items':[{'score':x['_score'],**x['_source'],'highlight':x.get('highlight',{})} for x in hits['hits']]}
    except httpx.HTTPError as exc:
        raise HTTPException(503,'Elasticsearch chưa sẵn sàng hoặc chưa tạo index. Dùng tìm kiếm SQL cơ bản trên trang Sản phẩm.') from exc
