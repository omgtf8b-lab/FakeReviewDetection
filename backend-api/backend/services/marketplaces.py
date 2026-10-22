"""Bounded public-page collection; no login, CAPTCHA bypass or fabricated reviews."""
import ipaddress
import json
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urlsplit, urlunsplit, urljoin, parse_qs
import httpx

PLATFORMS = {
    'shopee': ('shopee.vn', 's.shopee.vn', 'shope.ee', 'vn.shp.ee'),
    'tiktok_shop': ('tiktok.com', 'tiktokshop.com'),
    'lazada': ('lazada.vn',),
}
MEDIA_HOSTS = ('shopee.vn', 'susercontent.com', 'shopeemobile.com', 'lazada.vn', 'slatic.net',
               'alicdn.com', 'lazcdn.com', 'tiktokcdn.com', 'tiktokcdn-us.com', 'tiktokcdn-eu.com', 'ibytedtos.com', 'byteoversea.com')


class CollectionError(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)


def under(host, domain):
    return host == domain or host.endswith('.' + domain)


def identify_url(value):
    try:
        u = urlsplit(value.strip())
        host = (u.hostname or '').lower()
        if u.scheme not in ('https', 'http') or u.username or u.password or u.port not in (None, 80, 443):
            raise ValueError()
        platform = next((p for p, domains in PLATFORMS.items() if any(under(host, d) for d in domains)), None)
        if not platform or len(value) > 2000 or not u.path.strip('/'):
            raise ValueError()
        # Never carry credentials, fragments or user-specified ports into requests.
        path,query=u.path,u.query
        # Drop tracking parameters from recognized product URLs, keeping short-link
        # parameters and site API parameters needed to resolve/fetch the source.
        if platform=='shopee' and (match:=re.search(r'(?:-i\.|/product/)(\d+)[./](\d+)',path)):
            host='shopee.vn';path=f'/product/{match.group(1)}/{match.group(2)}';query=''
        elif platform=='lazada' and re.search(r'-i\d+(?:-|\.)',path):query=''
        elif platform=='tiktok_shop' and '/pdp/' in path:query=''
        return platform, urlunsplit(('https', host, path, query, ''))
    except (ValueError, TypeError):
        raise CollectionError('invalid_url', 'Nhập link sản phẩm HTTPS của Shopee Việt Nam, TikTok Shop hoặc Lazada Việt Nam.')


def public_host(host):
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise CollectionError('unsafe_address', 'Địa chỉ mạng không được phép truy cập.')
    except socket.gaierror as exc:
        raise CollectionError('network_error', 'Không phân giải được địa chỉ của sàn.') from exc


def bounded_get(url, *, media=False, max_bytes=2_000_000, expected_platform=None):
    """Validate every redirect before following it; never fetch arbitrary user hosts."""
    with httpx.Client(timeout=httpx.Timeout(8, connect=4), follow_redirects=False, trust_env=False) as client:
        for _ in range(5):
            u = urlsplit(url)
            if media:
                if u.scheme != 'https' or u.username or u.password or u.port not in (None,443) or not any(under(u.hostname or '', d) for d in MEDIA_HOSTS):
                    raise CollectionError('media_host_not_supported', 'Nguồn media chưa nằm trong danh sách được tải.')
            else:
                platform, url = identify_url(url)
                if expected_platform and platform != expected_platform:
                    raise CollectionError('unexpected_redirect', 'Link chuyển sang một sàn khác; không tiếp tục thu thập.')
            public_host(urlsplit(url).hostname)
            with client.stream('GET', url, headers={'User-Agent':'FakeReviewDetection-Research/1.0', 'Accept':'*/*' if media else 'text/html,application/json'}) as response:
                if response.status_code in (301,302,303,307,308):
                    location = response.headers.get('location')
                    if not location: raise CollectionError('invalid_redirect', 'Sàn trả chuyển hướng không hợp lệ.')
                    url = urljoin(url,location)
                    continue
                if response.status_code in (401,403,429):
                    raise CollectionError('access_restricted', 'Sàn yêu cầu quyền truy cập, đăng nhập hoặc giới hạn truy cập. Chưa lấy được review.')
                if response.status_code >= 400:
                    raise CollectionError('source_error', f'Sàn trả HTTP {response.status_code}; chưa có dữ liệu để kết luận.')
                payload = bytearray()
                for chunk in response.iter_bytes():
                    payload.extend(chunk)
                    if len(payload) > max_bytes:
                        raise CollectionError('source_too_large', 'Dữ liệu vượt giới hạn tải của một lần phân tích.')
                return str(response.url), bytes(payload), response.headers.get('content-type','')
    raise CollectionError('too_many_redirects', 'Link có quá nhiều lần chuyển hướng.')


class PageData(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta, self.scripts = {}, []
        self.capture = False
        self.in_title = False
        self.title = ''
        self.buffer = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title': self.in_title = True
        if tag == 'meta': self.meta[a.get('property',a.get('name',''))] = a.get('content','')
        if tag == 'script':
            self.capture = a.get('type') == 'application/ld+json' or a.get('id') in ('__NEXT_DATA__','__UNIVERSAL_DATA_FOR_REHYDRATION__','SIGI_STATE')
            self.buffer = []

    def handle_data(self, data):
        if self.capture: self.buffer.append(data)
        if self.in_title: self.title += data

    def handle_endtag(self, tag):
        if tag == 'title': self.in_title = False
        if tag == 'script' and self.capture:
            try: self.scripts.append(json.loads(''.join(self.buffer)))
            except (ValueError,RecursionError): pass
            self.capture = False


def objects(data, depth=0, budget=None):
    budget = budget if budget is not None else [30000]
    if depth > 25 or budget[0] <= 0: return
    budget[0] -= 1
    if isinstance(data,dict):
        yield data
        for value in data.values(): yield from objects(value,depth+1,budget)
    elif isinstance(data,list):
        for value in data: yield from objects(value,depth+1,budget)


def text(value):
    return str(value).strip()[:5000] if isinstance(value,(str,int,float)) else ''


def media_urls(value):
    if not isinstance(value,list): value = [value]
    result=[]
    for item in value[:10]:
        url = item.get('contentUrl') or item.get('url') if isinstance(item,dict) else item
        if isinstance(url,str) and url.startswith('https://') and len(url)<=2000: result.append(url)
    return result


def parse_page(html, limit=50):
    page=PageData(); page.feed(html)
    if any(word in page.title.lower() for word in ('security check','captcha','access denied','đăng nhập','login','security verification')):
        raise CollectionError('access_restricted','Sàn trả trang xác minh/đăng nhập; chưa có review để phân tích.')
    product={'name':page.meta.get('og:title',''), 'description':page.meta.get('og:description',''), 'images':media_urls(page.meta.get('og:image',[]))}
    reviews=[]; reported_total=None; ids=set()
    for script in page.scripts:
        for item in objects(script):
            types=item.get('@type',[]);types=[types] if isinstance(types,str) else types if isinstance(types,list) else []
            if 'Product' in types:
                product['name']=text(item.get('name')) or product['name']
                product['description']=text(item.get('description')) or product['description']
                product['images']=media_urls(item.get('image',[])) or product['images']
                offer=item.get('offers',{});offer=offer[0] if isinstance(offer,list) and offer else offer
                if isinstance(offer,dict):
                    product['price']=text(offer.get('price') or offer.get('lowPrice'))
                    product['currency']=text(offer.get('priceCurrency'))
                aggregate=item.get('aggregateRating',{})
                if isinstance(aggregate,dict):
                    try: reported_total=int(aggregate.get('reviewCount',aggregate.get('ratingCount')))
                    except (TypeError,ValueError): pass
            # Parse only explicitly typed reviews, never arbitrary page comments or marketing text.
            if 'Review' in types and len(reviews)<limit:
                body=text(item.get('reviewBody'))
                if not body: continue
                author=item.get('author',{})
                author_id=text(author.get('@id') or author.get('identifier')) if isinstance(author,dict) else ''
                author=text(author.get('name')) if isinstance(author,dict) else text(author)
                rating=item.get('reviewRating',{})
                try: stars=float(rating.get('ratingValue')) if isinstance(rating,dict) else None
                except (ValueError,TypeError): stars=None
                key=text(item.get('@id')) or (author+'|'+body+'|'+text(item.get('datePublished')))
                if key in ids: continue
                ids.add(key)
                reviews.append({'id':str(len(reviews)+1),'text':body,'author_id':author_id or None,
                    'rating':stars if stars is not None and 1<=stars<=5 else None,'created_at':text(item.get('datePublished')) or None,
                    'images':media_urls(item.get('image',[])),'videos':media_urls(item.get('video',[])), 'language':'unknown'})
    return product,reviews,reported_total


def product_identity(url):
    platform,canonical=identify_url(url)
    path=urlsplit(canonical).path
    pattern={'shopee':r'(?:-i\.|/product/)(\d+)[./](\d+)', 'tiktok_shop':r'/(?:pdp/[^/]+/|product/|view/product/)(\d+)', 'lazada':r'-i(\d+)(?:-|\.)'}[platform]
    match=re.search(pattern,path)
    if not match:return {'platform':platform,'product_id':None,'shop_id':None}
    return {'platform':platform,'product_id':match.group(2) if platform=='shopee' else match.group(1),'shop_id':match.group(1) if platform=='shopee' else None}


def shopee_reviews(url, limit):
    identity=product_identity(url)
    if not identity['product_id']:return [],None
    from urllib.parse import urlencode
    result=[];total=None
    for offset in range(0,limit,50):
        endpoint='https://shopee.vn/api/v2/item/get_ratings?'+urlencode({'itemid':identity['product_id'],'shopid':identity['shop_id'],'limit':min(50,limit-offset),'offset':offset,'filter':0,'type':0})
        _,body,kind=bounded_get(endpoint,expected_platform='shopee')
        try:payload=json.loads(body)
        except ValueError:raise CollectionError('access_restricted','Shopee không trả dữ liệu review công khai đọc được.')
        if payload.get('error') not in (None,0):raise CollectionError('access_restricted','Shopee chưa cho phép lấy review từ lần truy cập này.')
        data=payload.get('data') or {};rows=data.get('ratings') or []
        if not isinstance(rows,list):break
        total=(data.get('item_rating_summary') or {}).get('rating_total',total)
        for row in rows:
            if not isinstance(row,dict):continue
            images=[('https://down-vn.img.susercontent.com/file/'+x if '://' not in x else x) for x in row.get('images',[])[:10] if isinstance(x,str)]
            videos=[]
            for video in row.get('videos',[])[:3]:
                if isinstance(video,dict):videos.extend(media_urls(video.get('url',[])))
            result.append({'id':str(row.get('cmtid',len(result)+1)),'text':text(row.get('comment')),'rating':row.get('rating_star'),
                'author_id':str(row['userid']) if row.get('userid') else None,'created_at':row.get('ctime'), 'images':images,'videos':videos,'language':'unknown'})
        if len(rows)<min(50,limit-offset):break
    return result,total


def parse_lazada_review_page(payload, limit=50):
    """Normalize public review data without names, email or order identifiers."""
    if not isinstance(payload,dict) or payload.get('success') is not True:
        raise CollectionError('access_restricted','Lazada chưa cho phép đọc review trong lần truy cập này.')
    model=payload.get('model') or {}
    if not isinstance(model,dict) or not isinstance(model.get('items'),list):
        raise CollectionError('unsupported_response','Cấu trúc danh sách review Lazada đã thay đổi.')
    paging=model.get('paging') or {};item=model.get('item') or {};reviews=[];seen=set()
    if not isinstance(paging,dict):paging={}
    if not isinstance(item,dict):item={}
    product={'name':text(item.get('itemTitle')),'images':media_urls(item.get('itemPic',[]))}
    for row in model['items']:
        if not isinstance(row,dict) or not row.get('reviewRateId'):continue
        key=str(row['reviewRateId'])
        if key in seen:continue
        seen.add(key)
        images=media_urls(row.get('images') or []);videos=[]
        media_list=row.get('mediaList') or []
        for media in media_list[:15] if isinstance(media_list,list) else []:
            if not isinstance(media,dict):continue
            if media.get('videoUrl'):videos.extend(media_urls(media['videoUrl']))
            elif media.get('coverUrl'):images.extend(media_urls(media['coverUrl']))
        try:rating=float(row.get('rating'))
        except (TypeError,ValueError):rating=None
        content=text(row.get('reviewContent'))
        if not content and not images and not videos:continue
        reviews.append({'id':key,'text':content,'rating':rating if rating is not None and 1<=rating<=5 else None,
            'author_id':str(row['buyerId']) if row.get('buyerId') and not row.get('isAnonymous') else None,
            'created_at':text(row.get('reviewTime')) or None,'images':list(dict.fromkeys(images))[:10],
            'videos':list(dict.fromkeys(videos))[:3],'language':'unknown'})
        if len(reviews)>=limit:break
    try:total=max(0,int(paging.get('totalItems')))
    except (TypeError,ValueError):total=None
    try:total_pages=max(1,int(paging.get('totalPages')))
    except (TypeError,ValueError):total_pages=None
    return product,reviews,total,total_pages,len(model['items'])


def lazada_reviews(url, limit):
    """Read at most three public PDP review pages. Stop on any restriction."""
    from urllib.parse import urlencode
    import time
    identity=product_identity(url)
    if not identity['product_id']:return [],None,{},0,None
    result=[];seen=set();total=None;product={};pages=0;warning=None
    for page in range(1,4):
        if page>1:time.sleep(1)
        endpoint='https://my.lazada.vn/pdp/review/getReviewList?'+urlencode({
            'itemId':identity['product_id'],'pageSize':10,'filter':0,'sort':0,'pageNo':page})
        try:
            _,body,_=bounded_get(endpoint,expected_platform='lazada')
            try:payload=json.loads(body)
            except ValueError:raise CollectionError('access_restricted','Lazada trả trang xác minh thay vì danh sách review.')
            product,rows,total,total_pages,count=parse_lazada_review_page(payload,limit-len(result))
        except (CollectionError,httpx.HTTPError) as exc:
            if not result:raise
            warning=getattr(exc,'message','Nguồn không trả trang review tiếp theo trong thời gian cho phép.')
            break
        pages+=1;before=len(seen)
        for row in rows:
            if row['id'] not in seen:
                seen.add(row['id']);result.append(row)
            if len(result)>=limit:break
        if len(result)>=limit or not count or (total_pages is not None and page>=total_pages):break
        # A page containing rating-only records may be followed by text reviews.
        if rows and len(seen)==before:break
    return result,total,product,pages,warning


def collect(url, limit=50):
    platform,canonical=identify_url(url)
    try:
        if platform=='lazada' and product_identity(canonical)['product_id']:
            reviews,total,product,pages,warning=lazada_reviews(canonical,limit)
            return {'platform':platform,'url':canonical,'product':product,'reviews':reviews,'reported_total':total,
                'source':'lazada_public_reviews_endpoint','collection_status':'reviews_collected' if reviews else 'no_accessible_reviews',
                'collection_message':('Đã lấy mẫu review công khai từ Lazada; tối đa 3 trang, bỏ bản ghi chỉ có số sao. Không đảm bảo toàn bộ review.' if reviews else 'Nguồn trả dữ liệu nhưng chưa có nội dung review đọc được.')+(' Trang tiếp theo chưa đọc được: '+warning if warning else ''),
                'limit':limit,'pages_checked':pages,'collection_warning':warning}
        final,content,kind=bounded_get(canonical,expected_platform=platform)
        if 'html' not in kind and 'json' not in kind:
            raise CollectionError('unsupported_response','Sàn không trả trang sản phẩm có thể đọc.')
        product,reviews,total=parse_page(content.decode('utf-8',errors='replace'),limit)
        source='public_page_structured_data'
        if platform=='shopee' and not reviews:
            reviews,total=shopee_reviews(final,limit)
            source='shopee_public_reviews_endpoint'
        pages=None
        # Never interpret a login page title as product information.
        if any(word in product.get('name','').lower() for word in ('captcha','access denied','đăng nhập','log in','login','security verification')):
            raise CollectionError('access_restricted','Trang yêu cầu xác minh/đăng nhập; chưa thu thập được sản phẩm.')
        return {'platform':platform,'url':final,'product':product,'reviews':reviews,'reported_total':total,
            'source':source,'collection_status':'reviews_collected' if reviews else 'no_accessible_reviews',
            'collection_message':'Chỉ phân tích review công khai đọc được; không đảm bảo toàn bộ review.' if reviews else 'Chưa đọc được review công khai. Không có dữ liệu để phân tích; có thể thử lại hoặc dùng bản thu thập từ trình duyệt.',
            'limit':limit,'pages_checked':pages}
    except (CollectionError,httpx.HTTPError) as exc:
        return {'platform':platform,'url':canonical,'product':{},'reviews':[],'reported_total':None,
            'source':'lazada_public_reviews_endpoint' if platform=='lazada' else 'public_page_structured_data','collection_status':getattr(exc,'code','network_error'),
            'collection_message':getattr(exc,'message','Không kết nối được sàn trong thời gian cho phép.'),'limit':limit}
