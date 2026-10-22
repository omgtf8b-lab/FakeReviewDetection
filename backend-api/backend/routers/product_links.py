import json
import hashlib
from datetime import datetime,timedelta,timezone
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks,UploadFile,File,Request,Query
from pydantic import BaseModel,Field,ConfigDict,field_validator
from sqlalchemy.orm import Session
from database import get_db,SessionLocal
from auth import get_current_user,require_roles
import extended_models as ex
from services.marketplaces import identify_url,CollectionError
from services.collection_strategy import collect_bounded as collect
from services.link_analysis import analyze
from services.upload_analysis import analyze_files,InvalidMedia
from services.review_repository import save_collection,load_collection
from services.crawl_pipeline import crawl_to_database,analyze_from_database
from services.browser_diagnostics import public_collection

router=APIRouter(prefix='/api/product-links',tags=['Kiểm tra sản phẩm từ link và media'])


class LinkInput(BaseModel):
    url:str=Field(min_length=10,max_length=2000)
    limit:int=Field(default=50,ge=1,le=200)
    inspect_images:bool=False
    collection_mode:Literal['auto','browser','http']='auto'


class SourceReview(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str=Field(max_length=150,min_length=1)
    text:str=Field(default='',max_length=5000)
    author_id:str|None=Field(default=None,max_length=150)
    rating:float|None=Field(default=None,ge=1,le=5)
    created_at:str|None=Field(default=None,max_length=100)
    images:list[str]=Field(default_factory=list,max_length=10)
    videos:list[str]=Field(default_factory=list,max_length=3)
    language:Literal['en','vi','unknown']='unknown'

    @field_validator('images','videos')
    @classmethod
    def valid_media(cls,values):
        from urllib.parse import urlsplit
        if any(len(v)>2000 or urlsplit(v).scheme!='https' or not urlsplit(v).hostname for v in values):
            raise ValueError('Media cần URL HTTPS hợp lệ')
        return values


class ReviewImport(LinkInput):
    reviews:list[SourceReview]=Field(min_length=1,max_length=200)
    product_name:str=Field(default='',max_length=300)
    input_method:Literal['file','form','browser']='file'
    captured_at:datetime | None=None


def validated_url(value):
    try:return identify_url(value)
    except CollectionError as exc:raise HTTPException(422,exc.message) from exc


def output(row):
    created=row.created_at
    if created and created.tzinfo is None:created=created.replace(tzinfo=timezone.utc)
    return {'id':row.id,'url':row.url,'platform':row.platform,'status':row.status,
        'created_at':created,'result':public_collection(json.loads(row.result)) if row.result else None}


def expire_stalled(db,user_id):
    cutoff=datetime.now(timezone.utc)-timedelta(minutes=5)
    db.query(ex.ProductLinkAnalysis).filter(ex.ProductLinkAnalysis.user_id==user_id,
        ex.ProductLinkAnalysis.status.in_(['queued','running']),
        ex.ProductLinkAnalysis.created_at<cutoff).update({
            'status':'failed','result':json.dumps({'message':'Yêu cầu đã quá thời gian xử lý hoặc server đã khởi động lại. Hãy thử lại hoặc nhập bản thu thập từ Chrome; chưa có kết luận về sản phẩm.'},ensure_ascii=False)},synchronize_session=False)
    db.commit()


def reserve(db,user,url,platform):
    expire_stalled(db,user.id)
    pending=db.query(ex.ProductLinkAnalysis).filter(ex.ProductLinkAnalysis.user_id==user.id,
        ex.ProductLinkAnalysis.status.in_(['queued','running']),
        ex.ProductLinkAnalysis.created_at>=datetime.now(timezone.utc)-timedelta(minutes=10)).count()
    if pending>=3:raise HTTPException(429,'Bạn đã có ba yêu cầu đang chạy. Vui lòng đợi kết quả.')
    row=ex.ProductLinkAnalysis(user_id=user.id,url=url,platform=platform,status='queued')
    db.add(row);db.commit();db.refresh(row);return row


def run_job(jid,payload,imported=None,snapshot_id=None):
    with SessionLocal() as db:
        row=db.get(ex.ProductLinkAnalysis,jid)
        if not row:return
        row.status='running';db.commit()
        snapshot=None
        saved_snapshot_id=None
        try:
            mode='live'
            if snapshot_id is not None:
                snapshot,data=load_collection(db,snapshot_id,row.user_id);mode='snapshot'
                saved_snapshot_id=snapshot.id
            else:
                if imported is not None:
                    mode='user_input';snapshot=save_collection(db,row.user_id,imported);db.commit()
                else:
                    snapshot=crawl_to_database(db,row.user_id,payload.url,payload.limit,payload.collection_mode,collector=collect)
                saved_snapshot_id=snapshot.id
            snapshot,result=analyze_from_database(db,snapshot.id,row.user_id,payload.inspect_images,analyzer=analyze)
            db.refresh(row)
            if row.status!='running':return
            captured=snapshot.created_at
            if captured and captured.tzinfo is None:captured=captured.replace(tzinfo=timezone.utc)
            result['provenance']={'mode':mode,'snapshot_id':snapshot.id,'sha256':snapshot.sha256,
                'captured_at':captured.isoformat() if captured else None,'original_source':snapshot.source,
                'collector_version':'collection-1.1'}
            row.result=json.dumps(result,ensure_ascii=False);row.status='completed'
        except Exception:
            db.rollback()
            row=db.get(ex.ProductLinkAnalysis,jid)
            if row is None:return
            message={'message':'Phân tích chưa hoàn tất. Vui lòng thử lại; chưa có kết luận về sản phẩm.'}
            if saved_snapshot_id is not None:
                stored=db.query(ex.CollectionSnapshot).filter_by(id=saved_snapshot_id,user_id=row.user_id).first()
                if stored:
                    message.update({'message':'Dữ liệu nguồn đã lưu vào database, nhưng bước phân tích chưa hoàn tất. Có thể phân tích lại bản lưu mà không cào lần nữa.',
                        'snapshot_id':stored.id})
                    try:
                        _,evidence=load_collection(db,stored.id,row.user_id)
                        safe=public_collection(evidence)
                        for key in ('diagnostics','attempts'):
                            if key in safe:message[key]=safe[key]
                    except (LookupError,ValueError,TypeError,KeyError):pass
            row.status='failed';row.result=json.dumps(message,ensure_ascii=False)
        db.commit()


@router.post('',status_code=202)
def submit(body:LinkInput,tasks:BackgroundTasks,db:Session=Depends(get_db),user=Depends(get_current_user)):
    platform,url=validated_url(body.url);body.url=url
    row=reserve(db,user,url,platform);tasks.add_task(run_job,row.id,body)
    return output(row)


@router.post('/import',status_code=202)
def import_reviews(body:ReviewImport,tasks:BackgroundTasks,db:Session=Depends(get_db),user=Depends(get_current_user)):
    platform,url=validated_url(body.url);body.url=url
    row=reserve(db,user,url,platform)
    imported={'platform':platform,'url':url,'product':{'name':body.product_name},
        'reviews':[r.model_dump() for r in body.reviews],'reported_total':None,
        'source':'browser_page_import' if body.input_method=='browser' else 'user_written_review' if body.input_method=='form' else 'user_supplied_review_import',
        'collection_status':'imported','collection_message':'Review do người dùng nhập để phân tích/kiểm thử; không phải dữ liệu vừa thu thập từ sàn.','limit':len(body.reviews)}
    if body.input_method=='browser':
        imported['collection_message']='Bản thu thập từ trang trình duyệt do người dùng cung cấp; chỉ gồm review đã tải. Server chưa xác minh độc lập nguồn hoặc tính thật/giả.'
        imported['client_captured_at']=body.captured_at.isoformat() if body.captured_at else None
    if body.input_method=='form':
        for review in imported['reviews']:review['author_id']=str(user.id)
    tasks.add_task(run_job,row.id,body,imported)
    return output(row)


@router.post('/media')
async def upload_media(request:Request,files:list[UploadFile]=File(...),db:Session=Depends(get_db),user=Depends(get_current_user)):
    if len(files)>6:raise HTTPException(413,'Mỗi lần tối đa 6 tệp.')
    received=[];total=0
    try:
        for file in files:
            body=bytearray()
            while chunk:=await file.read(65536):
                body.extend(chunk);total+=len(chunk)
                if len(body)>40_000_000 or total>60_000_000:
                    raise HTTPException(413,'Mỗi tệp tối đa 40 MB, tổng tối đa 60 MB.')
            if not body:raise HTTPException(422,'Có tệp rỗng trong lần gửi.')
            received.append((file.filename or 'media',bytes(body)))
        # CPU decoding runs outside the async event loop.
        from starlette.concurrency import run_in_threadpool
        result=await run_in_threadpool(analyze_files,received)
    except InvalidMedia as exc:
        raise HTTPException(422,str(exc)) from exc
    finally:
        for file in files:await file.close()
    row=ex.ProductLinkAnalysis(user_id=user.id,url='',platform='upload',status='completed',result=json.dumps(result,ensure_ascii=False))
    db.add(row);db.commit();db.refresh(row);return output(row)


@router.get('')
def history(db:Session=Depends(get_db),user=Depends(get_current_user)):
    expire_stalled(db,user.id)
    return [output(x) for x in db.query(ex.ProductLinkAnalysis).filter_by(user_id=user.id).order_by(ex.ProductLinkAnalysis.id.desc()).limit(30)]


@router.get('/snapshots/{sid}')
def snapshot_data(sid:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    row,data=owned_collection(db,sid,user.id)
    safe=public_collection(data)
    # sha256 remains the verified immutable source digest, including for old rows.
    # The export view may redact historical diagnostics without mutating storage.
    public_digest=hashlib.sha256(json.dumps(safe,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'snapshot_id':row.id,'source':row.source,'sha256':row.sha256,'dataset_sha256':public_digest,
        'captured_at':row.created_at.replace(tzinfo=timezone.utc).isoformat() if row.created_at else None,'dataset':safe}


def owned_collection(db,sid,user_id):
    try:return load_collection(db,sid,user_id)
    except LookupError:raise HTTPException(404,'Không tìm thấy bản dữ liệu thuộc tài khoản của bạn.')
    except (ValueError,TypeError,KeyError):raise HTTPException(409,'Bản dữ liệu không vượt kiểm tra toàn vẹn.')


@router.get('/snapshots/{sid}/reviews')
def stored_reviews(sid:int,offset:int=Query(default=0,ge=0),limit:int=Query(default=50,ge=1,le=200),
                   db:Session=Depends(get_db),user=Depends(get_current_user)):
    snapshot,data=owned_collection(db,sid,user.id)
    return {'snapshot_id':snapshot.id,'source':snapshot.source,'total':len(data['reviews']),
        'offset':offset,'limit':limit,'reviews':data['reviews'][offset:offset+limit]}


@router.post('/snapshots/{sid}/analyze',status_code=202)
def replay(sid:int,tasks:BackgroundTasks,db:Session=Depends(get_db),user=Depends(get_current_user)):
    row,dataset=owned_collection(db,sid,user.id)
    if not dataset.get('reviews'):raise HTTPException(409,'Bản lưu này chưa có review; không thể tạo kết luận khi phân tích lại.')
    body=LinkInput(url=row.canonical_url)
    job=reserve(db,user,row.canonical_url,row.platform);tasks.add_task(run_job,job.id,body,None,row.id)
    return output(job)


@router.get('/admin/summary')
def admin_summary(db:Session=Depends(get_db),user=Depends(require_roles('admin','engineer'))):
    from collections import Counter
    platform=Counter();status=Counter();sources=Counter();modes=Counter();users=set();reviews=files=0
    for row in db.query(ex.ProductLinkAnalysis).yield_per(100):
        platform[row.platform]+=1;status[row.status]+=1;users.add(row.user_id)
        data=json.loads(row.result) if row.result else {}
        sources[data.get('source','pending')]+=1
        modes[data.get('provenance',{}).get('mode','upload' if row.platform=='upload' else 'previous_version')]+=1
        reviews+=data.get('summary',{}).get('observed_reviews',0)
        files+=data.get('summary',{}).get('observed_files',0)
    return {'total_checks':sum(platform.values()),'users_with_checks':len(users),'review_observations':reviews,'files_inspected':files,
        'platforms':dict(platform),'statuses':dict(status),'sources':dict(sources),'modes':dict(modes),
        'note':'Đây là số lượt xử lý, có thể gồm lần kiểm tra lại. Không phải số sản phẩm duy nhất hoặc accuracy thực địa.'}


@router.get('/{jid}')
def detail(jid:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    expire_stalled(db,user.id)
    row=db.query(ex.ProductLinkAnalysis).filter_by(id=jid,user_id=user.id).first()
    if not row:raise HTTPException(404,'Không tìm thấy lần kiểm tra thuộc tài khoản của bạn.')
    return output(row)
