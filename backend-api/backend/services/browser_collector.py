"""Read rendered public product pages with ordinary Selenium, in an isolated worker."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import urlsplit
from services.marketplaces import identify_url, parse_page, CollectionError

DOM_SCRIPT = r"""
const platform=arguments[0], limit=arguments[1];
const selectors={
  shopee:['.shopee-product-rating','[data-testid="review-item"]'],
  lazada:['.mod-reviews .item','[data-testid="review-item"]'],
  tiktok_shop:['[data-e2e="review-item"]','[data-testid="review-item"]','[data-testid="product-review-item"]']
};
const contentSelectors={
 shopee:['.shopee-product-rating__content','[data-testid="review-content"]'],
 lazada:['.content','[data-testid="review-content"]'],
 tiktok_shop:['[data-e2e="review-content"]','[data-testid="review-content"]']
};
const output=[];
let nodes=[];
for(const selector of selectors[platform]){nodes=[...document.querySelectorAll(selector)];if(nodes.length)break;}
for(const node of nodes.slice(0,limit)){
 if(!node.getClientRects().length)continue;
 let content=null;for(const selector of contentSelectors[platform]){content=node.querySelector(selector);if(content)break;}
 if(!content)continue;
 const text=(content.innerText||'').trim().slice(0,5000);
 const author=node.querySelector('[data-user-id]');
 const date=node.querySelector('time,.shopee-product-rating__time,.top .date');
 const label=node.getAttribute('data-rating')||node.querySelector('[aria-label*="out of 5"],[aria-label*="/5"]')?.getAttribute('aria-label')||'';
 const match=label.match(/([1-5](?:\.\d)?)\s*(?:out of|\/)?\s*5?/);
 const images=[...node.querySelectorAll('img')].filter(x=>!(/avatar/i.test((x.className||'')+' '+(x.alt||'')))).map(x=>x.getAttribute('data-src')||x.currentSrc||x.src).filter(x=>x?.startsWith('https://')).slice(0,10);
 const videos=[...node.querySelectorAll('video,video source')].map(x=>x.src).filter(x=>x?.startsWith('https://')).slice(0,3);
 if(!text&&!images.length&&!videos.length)continue;
 output.push({id:node.getAttribute('data-review-id')||node.getAttribute('data-id')||null,text,author_id:author?.getAttribute('data-user-id')||null,
  created_at:(date?.getAttribute('datetime')||date?.innerText||'').trim().slice(0,100)||null,
  rating:match?Number(match[1]):null,images,videos,language:'unknown'});
}
return {reviews:output,name:(document.querySelector('h1')?.innerText||'').trim().slice(0,300)};
"""

_slots = threading.BoundedSemaphore(1)
ROOT = Path(__file__).resolve().parents[1]


def unavailable(url, code, message):
    platform,url=identify_url(url)
    return {'platform':platform,'url':url,'product':{},'reviews':[],'reported_total':None,
        'source':'selenium_rendered_page','collection_status':code,'collection_message':message}


def collect_browser(url, limit=50):
    _,url=identify_url(url)
    if os.getenv('BROWSER_SCRAPING_ENABLED','true').lower() != 'true':
        return unavailable(url,'browser_disabled','Thu thập bằng trình duyệt đang tắt trong cấu hình server.')
    if not _slots.acquire(timeout=2):
        return unavailable(url,'browser_busy','Bộ thu thập đang xử lý một yêu cầu khác; có thể thử lại sau.')
    try:
        command=[sys.executable,'-m','services.browser_collector','--worker']
        env={**os.environ,'PYTHONIOENCODING':'utf-8','NO_PROXY':'localhost,127.0.0.1','no_proxy':'localhost,127.0.0.1'}
        env.setdefault('SE_CACHE_PATH',str(ROOT/'data/browser-cache'))
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        process=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding='utf-8',creationflags=flags)
        try:
            stdout,_=process.communicate(json.dumps({'url':url,'limit':limit}),timeout=65)
        except subprocess.TimeoutExpired:
            if os.name=='nt':
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
            else:process.kill()
            process.communicate(timeout=5)
            return unavailable(url,'browser_timeout','Trình duyệt vượt thời gian thu thập; chưa xác nhận đủ dữ liệu.')
        try:
            data=json.loads(stdout)
            if not isinstance(data,dict) or not isinstance(data.get('reviews'),list):raise ValueError()
            return data
        except ValueError:
            return unavailable(url,'browser_unavailable','Chưa khởi động được bộ đọc trình duyệt. Kiểm tra Selenium, Chrome và driver trên server.')
    finally:
        _slots.release()


def read_rendered(driver, url, limit):
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    platform,url=identify_url(url)
    driver.set_page_load_timeout(18);driver.set_script_timeout(5)
    try:driver.get(url)
    except TimeoutException:pass
    data=unavailable(url,'no_accessible_reviews','Không đọc được review công khai sau khi tải trang bằng trình duyệt.')
    records={};deadline=time.monotonic()+25
    for page in range(3):
        final_platform,final=identify_url(driver.current_url)
        if final_platform!=platform:raise CollectionError('unexpected_redirect','Link chuyển sang sàn khác, dừng thu thập.')
        data['url']=final
        try:product,structured,total=parse_page(driver.page_source,limit)
        except CollectionError as exc:
            data['collection_status']=exc.code;data['collection_message']=exc.message;break
        data['product']=product;data['reported_total']=total
        # Scroll only the reviews section, never click login, CAPTCHA or purchase controls.
        sections=driver.find_elements(By.CSS_SELECTOR,'.product-ratings,#module_product_review,[data-testid="reviews-section"],[data-e2e="product-review"]')
        if sections:driver.execute_script('arguments[0].scrollIntoView({block:"center"});',sections[0])
        else:driver.execute_script('window.scrollTo(0,Math.min(document.body.scrollHeight,2400));')
        rendered={}
        def has_reviews(d):
            nonlocal rendered
            rendered=d.execute_script(DOM_SCRIPT,platform,limit)
            return bool(rendered.get('reviews'))
        try:WebDriverWait(driver,4,poll_frequency=.5).until(has_reviews)
        except TimeoutException:pass
        if not product.get('name') and rendered.get('name') and rendered.get('reviews'):product['name']=rendered['name']
        rows=rendered.get('reviews') or structured
        for review in rows:
            if not rendered.get('reviews') or not review.get('id'):
                key=json.dumps([review.get('author_id'),review.get('text'),review.get('created_at')],ensure_ascii=False)
                review['id']='page-'+hashlib.sha256(key.encode()).hexdigest()[:24]
            records.setdefault(str(review['id']),review)
            if len(records)>=limit:break
        if len(records)>=limit or time.monotonic()>deadline:break
        next_selectors={
            'shopee':'.product-ratings .shopee-page-controller .shopee-icon-button--right',
            'lazada':'#module_product_review button.next-next,.mod-reviews button.next-next',
            'tiktok_shop':'[data-testid="reviews-next"]',
        }
        buttons=driver.find_elements(By.CSS_SELECTOR,next_selectors[platform])
        available=next((b for b in buttons if b.is_displayed() and b.is_enabled() and b.get_attribute('aria-disabled')!='true'),None)
        if available is None:break
        # Explicitly wait for the first review to change after pagination.
        before=[r.get('text') for r in rendered.get('reviews',[])]
        available.click()
        try:WebDriverWait(driver,4,poll_frequency=.5).until(lambda d:[r.get('text') for r in d.execute_script(DOM_SCRIPT,platform,limit)['reviews']]!=before)
        except TimeoutException:break
    data['reviews']=list(records.values())[:limit]
    if records:
        data['collection_status']='reviews_collected'
        data['collection_message']='Đã đọc mẫu review từ trang trình duyệt. Tối đa 3 trang đánh giá; không đảm bảo toàn bộ review của sản phẩm.'
    data['pages_checked']=page+1
    return data


def worker(payload):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from services.browser_proxy import PublicProxy
    url=payload['url'];identify_url(url)
    base=Path(os.getenv('BROWSER_TEMP_DIR',str(ROOT/'data/browser-temp')));base.mkdir(parents=True,exist_ok=True)
    with PublicProxy() as proxy,tempfile.TemporaryDirectory(prefix='collector-',dir=base,ignore_cleanup_errors=True) as profile:
        options=webdriver.ChromeOptions();options.page_load_strategy='eager'
        for arg in ['--headless=new','--disable-gpu','--disable-background-networking','--disable-sync','--disable-default-apps',
                    '--no-first-run','--disable-quic','--autoplay-policy=user-gesture-required',f'--user-data-dir={profile}',
                    f'--proxy-server={proxy}','--proxy-bypass-list=<-loopback>']:
            options.add_argument(arg)
        options.add_experimental_option('prefs',{'profile.managed_default_content_settings.images':2,'credentials_enable_service':False})
        if os.getenv('BROWSER_BINARY'):options.binary_location=os.environ['BROWSER_BINARY']
        service=Service(executable_path=os.getenv('BROWSER_DRIVER_PATH') or None,log_output=subprocess.DEVNULL)
        if os.name=='nt':service.creation_flags=subprocess.CREATE_NO_WINDOW
        driver=None
        try:
            try:
                driver=webdriver.Chrome(service=service,options=options)
            except Exception:
                return unavailable(url,'browser_start_failed','Chrome trên server chưa khởi động được; đây chưa phải lỗi quyền truy cập của sàn. Có thể dùng mục Thu thập từ Chrome để nhập review đang hiển thị trên trình duyệt của bạn.')
            return read_rendered(driver,url,min(int(payload.get('limit',50)),200))
        finally:
            if driver is not None:driver.quit()


if __name__=='__main__':
    payload=json.load(sys.stdin)
    try:result=worker(payload)
    except CollectionError as exc:result=unavailable(payload['url'],exc.code,exc.message)
    except Exception:result=unavailable(payload['url'],'browser_unavailable','Không khởi động/đọc được trình duyệt. Kiểm tra Chrome và driver; chưa có kết luận về sản phẩm.')
    print(json.dumps(result,ensure_ascii=False))
