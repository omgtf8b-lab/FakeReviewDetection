"""Evidence-based review screening, separate from identity/product authentication."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import re
import unicodedata
from services.marketplaces import bounded_get, CollectionError, product_identity
from services.browser_diagnostics import public_collection


def normalize(value):
    return ' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',value).casefold()))


def english_supported(review):
    if review.get('language')=='en':return True,'declared_en'
    if review.get('language')=='vi':return False,'declared_vi'
    content=review.get('text','').lower()
    if re.search(r'[à-ỹđ]',content):return False,'non_english_or_unknown'
    common={'the','this','product','with','for','after','was','have','but','my','and','it','is','not','bought','used'}
    return len(set(content.split()) & common)>=4,'conservative_english_heuristic'


def observations(reviews):
    aspects={
        'Chất lượng và độ bền':['chất lượng','bền','lỗi','hỏng','rách','quality','broke','broken','durable'],
        'Kích thước và độ vừa':['size','kích thước','vừa','chật','rộng','small','large','fit'],
        'Ngoại hình và mô tả':['màu','đẹp','mô tả','color','appearance','description'],
        'Giá cả':['giá','đắt','rẻ','price','cheap','expensive'],
        'Giao hàng và đóng gói':['giao hàng','đóng gói','vận chuyển','ship','delivery','packaging'],
    }
    positive=['tốt','đẹp','đúng mô tả','bền','nhanh','good','excellent','durable','works well','fits well']
    negative=['không tốt','không đúng','không vừa','quá nhỏ','quá to','lỗi','hỏng','kém','chậm','rách','đắt','not good','broken','broke','poor','too small','too large','damaged','late']
    groups={};seen=set()
    for review in reviews:
        content=review['text'].casefold();key=normalize(content)
        if not key or key in seen:continue
        seen.add(key)
        neg=any(x in content for x in negative)
        scrubbed=content
        for x in negative:scrubbed=scrubbed.replace(x,' ')
        pos=any(x in scrubbed for x in positive)
        for aspect,words in aspects.items():
            if not any(x in content for x in words):continue
            group=groups.setdefault(aspect,{'aspect':aspect,'mentions':0,'positive_mentions':0,'negative_mentions':0,'evidence':[]})
            group['mentions']+=1;group['positive_mentions']+=int(pos);group['negative_mentions']+=int(neg)
            if len(group['evidence'])<3:group['evidence'].append({'review_id':review['id'],'quote':review['text'][:250]})
    return {'method':'Tổng hợp theo từ khóa Việt/Anh trên văn bản không trùng; không xác minh trải nghiệm thật, không phải mô hình sentiment đã được đánh giá.',
        'distinct_texts':len(seen),'aspects':list(groups.values())}


def media_evidence(reviews, inspect=False):
    references=[]
    for r in reviews:
        for kind in ('images','videos'):
            for url in r.get(kind,[])[:10]:references.append({'review_id':r['id'],'kind':kind,'url':url})
    groups=defaultdict(list)
    for ref in references:groups[(ref['kind'],ref['url'])].append(ref['review_id'])
    duplicates=[{'kind':kind,'method':'same_url','review_ids':sorted(set(ids)),'count':len(set(ids))} for (kind,url),ids in groups.items() if len(set(ids))>1]
    inspected=[];errors=[];hashes=defaultdict(list);pixels=defaultdict(list)
    if inspect:
        # Bounded: at most eight distinct images; videos are references only.
        for url in list(dict.fromkeys(x['url'] for x in references if x['kind']=='images'))[:8]:
            ids=sorted(set(x['review_id'] for x in references if x['url']==url))
            try:
                _,body,content_type=bounded_get(url,media=True,max_bytes=4_000_000)
                if not content_type.startswith('image/'):raise ValueError('Not an image')
                from PIL import Image
                with Image.open(BytesIO(body)) as image:
                    if image.width*image.height>20_000_000:raise ValueError('Image too large')
                    width,height=image.size
                    gray=image.convert('L').resize((9,8))
                    values=list(gray.get_flattened_data() if hasattr(gray,'get_flattened_data') else gray.getdata())
                    dhash=sum((values[y*9+x]>values[y*9+x+1]) << (y*8+x) for y in range(8) for x in range(8))
                digest=sha256(body).hexdigest()
                hashes[digest].extend(ids);pixels[f'{dhash:016x}'].extend(ids)
                inspected.append({'review_ids':ids,'sha256':digest,'dhash':f'{dhash:016x}','width':width,'height':height})
            except Exception as exc:
                errors.append({'review_ids':ids,'reason':exc.message if isinstance(exc,CollectionError) else 'Không tải/giải mã được ảnh trong giới hạn an toàn.'})
        for method,groups_ in [('same_file_sha256',hashes),('same_perceptual_hash',pixels)]:
            for key,ids in groups_.items():
                if len(set(ids))>1:duplicates.append({'kind':'images','method':method,'review_ids':sorted(set(ids)),'count':len(set(ids))})
    return {'image_references':sum(x['kind']=='images' for x in references),'video_references':sum(x['kind']=='videos' for x in references),
        'images_inspected':len(inspected),'inspected':inspected,'errors':errors,'duplicate_groups':duplicates,
        'video_analysis':'reference_duplicates_only','semantic_authenticity':'not_assessed',
        'note':'Ảnh trùng hoặc video dùng cùng URL chỉ là dấu hiệu tái sử dụng. Chưa xác minh ảnh/video do AI tạo, nội dung liên quan sản phẩm hay người thật; chưa đọc khung hình/âm thanh video.'}


def analyze(collected, inspect_media=False):
    collected=public_collection(collected)
    # Stable IDs remove pagination duplicates; never double-count identical source records.
    seen=set();reviews=[]
    for row in collected['reviews']:
        key=str(row['id'])
        if key in seen:continue
        seen.add(key); reviews.append({**row,'id':key,'text':row.get('text','') or ''})
    counts=Counter(normalize(r['text']) for r in reviews if len(normalize(r['text']).split())>=3)
    media=media_evidence(reviews,inspect_media)
    reused={rid for group in media['duplicate_groups'] for rid in group['review_ids']}
    author_counts=Counter(r.get('author_id') for r in reviews if r.get('author_id'))
    analyzed=[];nlp_count=0
    for row in reviews:
        reasons=[];normal=normalize(row['text']);words=normal.split()
        if row['text'].strip() and len(words)<=1:reasons.append({'code':'very_short','message':'Review chỉ có một từ hoặc ký tự; cần kiểm tra thêm.'})
        if len(words)>=3 and counts[normal]>1:reasons.append({'code':'duplicate_text','message':f'Nội dung chuẩn hóa trùng trong {counts[normal]} review của mẫu.'})
        if re.search(r'(https?://|\b(zalo|telegram|whatsapp)\b)',row['text'],re.I):reasons.append({'code':'external_contact','message':'Có link hoặc kênh liên hệ ngoài; cần xem ngữ cảnh.'})
        if row['id'] in reused:reasons.append({'code':'reused_media','message':'Ảnh/video có dấu hiệu tái sử dụng trong mẫu review.'})
        if row.get('author_id') and author_counts[row['author_id']]>=3:reasons.append({'code':'repeated_author','message':'Cùng mã tác giả xuất hiện ít nhất ba lần trong mẫu; có thể là review cập nhật, cần đối chiếu.'})
        supported,language_method=english_supported(row);prediction=None
        if supported and len(words)>=3:
            from ml.predictor import predictor
            if predictor.ready:
                prediction=predictor.predict(row['text']);nlp_count+=1
                if prediction['fake_probability']>=.8:reasons.append({'code':'english_or_cg_model','message':'Model tiếng Anh nhận thấy dấu hiệu nội dung sinh tự động; không xác minh gian lận.'})
        analyzed.append({**row,'signals':reasons,'assessment':'needs_review' if reasons else 'no_obvious_signals' if row['text'].strip() else 'insufficient_data',
            'nlp':prediction,'language_method':language_method,'identity':'not_verified'})
    suspicious=sum(bool(r['signals']) for r in analyzed)
    total=len(analyzed);reported=collected.get('reported_total')
    verdict='insufficient_data' if total<5 else 'signals_detected' if suspicious else 'no_obvious_signals'
    return {k:v for k,v in {**collected,'identity':product_identity(collected['url']),'reviews':analyzed,'media':media,'observations':observations(reviews),
        'summary':{'observed_reviews':total,'reviews_with_signals':suspicious,'signal_percentage':round(100*suspicious/total,2) if total else None,
            'text_reviews':sum(bool(r['text'].strip()) for r in analyzed),
            'reviews_with_media':sum(bool(r.get('images') or r.get('videos')) for r in analyzed),
            'rating_distribution':dict(Counter(str(r['rating']) for r in analyzed if r.get('rating') is not None)),
            'nlp_reviews':nlp_count,'reported_total':reported,'coverage':'partial' if reported and total<reported else 'unknown',
            'verdict':verdict,'product_authenticity':'not_verified','human_authorship':'not_verified'},
        'analyzed_at':datetime.now(timezone.utc).isoformat(),
        'limitations':['Kết quả chỉ áp dụng cho mẫu lấy được, không đại diện toàn bộ sản phẩm hoặc shop.',
            'Không xác minh hàng thật/hàng giả hoặc người thật/bot từ link và review.',
            'Tỷ lệ có dấu hiệu không phải xác suất review giả. Ít hơn 5 review được đánh dấu chưa đủ dữ liệu.',
            'Model hiện tại chỉ hỗ trợ tiếng Anh OR/CG; review tiếng Việt được kiểm tra bằng quy tắc, chưa có điểm NLP tiếng Việt.',
            'Chưa đánh giá nội dung ngữ nghĩa/AI của ảnh và video.']}.items()}
