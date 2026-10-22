"""Browser scraping is primary; HTTP is a recorded secondary attempt, never fake data."""
from services.browser_collector import collect_browser
from services.marketplaces import collect as collect_http
from services.marketplaces import identify_url
from services.browser_diagnostics import CODES
import json
import os
from pathlib import Path
import subprocess
import sys


def collect_bounded(url,limit=50,mode='auto'):
    """Bound browser + HTTP + DNS as one operation, including child processes."""
    platform,url=identify_url(url)
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    process=subprocess.Popen([sys.executable,'-m','services.collection_strategy'],
        cwd=Path(__file__).resolve().parents[1],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,encoding='utf-8',creationflags=flags,
        env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    try:
        output,_=process.communicate(json.dumps({'url':url,'limit':limit,'mode':mode}),timeout=105)
        data=json.loads(output)
        if not isinstance(data,dict) or not isinstance(data.get('reviews'),list):raise ValueError()
        return data
    except subprocess.TimeoutExpired:
        if os.name=='nt':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,timeout=5)
        else:process.kill()
        process.kill()
        return {'platform':platform,'url':url,'product':{},'reviews':[],
            'source':'collection_timeout','collection_status':'collection_timeout',
            'collection_message':'Đã dừng sau 105 giây vì nguồn chưa trả dữ liệu. Hãy dùng mục Thu thập từ Chrome hoặc nhập nội dung bình luận; chưa có kết luận về sản phẩm.'}
    except (ValueError,OSError):
        return {'platform':platform,'url':url,'product':{},'reviews':[],
            'source':'collection_error','collection_status':'collector_error',
            'collection_message':'Bộ thu thập chưa trả dữ liệu hợp lệ. Có thể nhập bản thu thập từ Chrome; chưa có kết luận về sản phẩm.'}
    finally:
        for stream in (process.stdin,process.stdout):
            if stream:stream.close()
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:process.kill()


def collect(url,limit=50,mode='auto'):
    if mode=='http':
        data=collect_http(url,limit)
        data['attempts']=[{'collector':'http','status':data['collection_status']}]
        return data
    platform,_=identify_url(url)
    # Lazada exposes a public PDP review resource. Avoid launching a browser
    # when that source already yields genuine review records.
    direct=None
    if mode=='auto' and platform=='lazada':
        direct=collect_http(url,limit)
        direct['attempts']=[{'collector':'http','status':direct['collection_status']}]
        if direct.get('reviews'):return direct
    browser=collect_browser(url,limit)
    browser['attempts']=(direct['attempts'] if direct else [])+[{'collector':'selenium','status':browser['collection_status']}]
    code=browser.get('diagnostics',{}).get('code')
    if code in CODES:
        browser['attempts'][-1]['diagnostic_code']=code
    if browser.get('reviews') or mode=='browser':return browser
    if direct is None:
        direct=collect_http(url,limit)
        attempts=browser['attempts']+[{'collector':'http','status':direct['collection_status']}]
    else:attempts=browser['attempts']
    # Prefer the attempt with reviews, then useful product metadata.
    selected=direct if direct.get('reviews') or (not browser.get('product',{}).get('name') and direct.get('product',{}).get('name')) else browser
    selected['attempts']=attempts
    return selected


if __name__=='__main__':
    payload=json.load(sys.stdin)
    print(json.dumps(collect(payload['url'],payload.get('limit',50),payload.get('mode','auto')),ensure_ascii=False))
