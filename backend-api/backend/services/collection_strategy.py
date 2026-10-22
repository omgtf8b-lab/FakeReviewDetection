"""Browser scraping is primary; HTTP is a recorded secondary attempt, never fake data."""
from services.browser_collector import collect_browser
from services.marketplaces import collect as collect_http
from services.marketplaces import identify_url
from services.browser_diagnostics import public_collection, public_diagnostics
import json
import os
from pathlib import Path
import subprocess
import sys


def collect_bounded(url,limit=50,mode='auto'):
    """Bound browser + HTTP + DNS as one operation, including child processes."""
    platform,url=identify_url(url)
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    def failed(code, exc=None, returncode=None):
        data={'platform':platform,'url':url,'product':{},'reviews':[], 'source':'collection_error',
              'collection_status':'collection_timeout' if code=='collection_timeout' else 'collector_error',
              'collection_message':'Bộ thu thập chưa hoàn tất; chưa có dữ liệu để kết luận.',
              'diagnostics':{'stage':'collection','code':code}}
        if exc is not None: data['diagnostics']['exception_type']=type(exc).__name__
        if returncode is not None: data['diagnostics']['returncode']=returncode
        data['attempts']=[{'collector':'collection','status':data['collection_status'],'diagnostics':data['diagnostics']}]
        return public_collection(data)
    try:
        process=subprocess.Popen([sys.executable,'-m','services.collection_strategy'],
            cwd=Path(__file__).resolve().parents[1],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,encoding='utf-8',creationflags=flags,
            env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    except OSError as exc:return failed('collection_spawn_failed',exc)
    try:
        output,_=process.communicate(json.dumps({'url':url,'limit':limit,'mode':mode}),timeout=105)
        if process.returncode != 0:return failed('collection_exit_failed',returncode=process.returncode)
        data=json.loads(output)
        if not isinstance(data,dict) or not isinstance(data.get('reviews'),list):raise ValueError()
        return public_collection(data)
    except subprocess.TimeoutExpired:
        if os.name=='nt':
            try:
                subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags,timeout=5)
            except (OSError,subprocess.TimeoutExpired):pass
        try:process.kill()
        except OSError:pass
        return failed('collection_timeout',subprocess.TimeoutExpired('collection',105))
    except ValueError:return failed('collection_invalid_output')
    except OSError as exc:return failed('collection_io_failed',exc)
    finally:
        for stream in (process.stdin,process.stdout):
            if stream:stream.close()
        try:process.wait(timeout=2)
        except OSError:pass
        except subprocess.TimeoutExpired:
            try:process.kill()
            except OSError:pass


def collect(url,limit=50,mode='auto'):
    if mode=='http':
        data=collect_http(url,limit)
        data['attempts']=[{'collector':'http','status':data['collection_status']}]
        return public_collection(data)
    platform,_=identify_url(url)
    # Lazada exposes a public PDP review resource. Avoid launching a browser
    # when that source already yields genuine review records.
    direct=None
    if mode=='auto' and platform=='lazada':
        direct=collect_http(url,limit)
        direct['attempts']=[{'collector':'http','status':direct['collection_status']}]
        if direct.get('reviews'):return public_collection(direct)
    browser=public_collection(collect_browser(url,limit))
    browser['attempts']=(direct['attempts'] if direct else [])+[{'collector':'selenium','status':browser['collection_status']}]
    safe=public_diagnostics(browser.get('diagnostics'))
    if safe:
        browser['attempts'][-1].update(diagnostic_code=safe['code'],diagnostics=safe)
    if browser.get('reviews') or mode=='browser':return public_collection(browser)
    if direct is None:
        direct=collect_http(url,limit)
        attempts=browser['attempts']+[{'collector':'http','status':direct['collection_status']}]
    else:attempts=browser['attempts']
    # Prefer the attempt with reviews, then useful product metadata.
    selected=direct if direct.get('reviews') or (not browser.get('product',{}).get('name') and direct.get('product',{}).get('name')) else browser
    selected['attempts']=attempts
    return public_collection(selected)


if __name__=='__main__':
    payload=json.load(sys.stdin)
    print(json.dumps(collect(payload['url'],payload.get('limit',50),payload.get('mode','auto')),ensure_ascii=False))
