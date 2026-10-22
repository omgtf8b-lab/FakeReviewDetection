"""Optional Redis cache; falls back to a bounded, expiring local cache."""
import json
import os
import time
from threading import Lock

_cache={}
_lock=Lock()


def get(key):
    if os.getenv('REDIS_URL'):
        try:
            import redis
            value=redis.Redis.from_url(os.environ['REDIS_URL'],socket_connect_timeout=.5,socket_timeout=.5).get(key)
            if value:return json.loads(value)
        except Exception:pass
    with _lock:
        item=_cache.get(key)
        if item and item[0]>time.monotonic():return dict(item[1])
        _cache.pop(key,None)
    return None


def put(key,value,ttl=300):
    if os.getenv('REDIS_URL'):
        try:
            import redis
            redis.Redis.from_url(os.environ['REDIS_URL'],socket_connect_timeout=.5,socket_timeout=.5).setex(key,ttl,json.dumps(value))
        except Exception:pass
    with _lock:
        if len(_cache)>=1000:_cache.pop(next(iter(_cache)))
        _cache[key]=(time.monotonic()+ttl,dict(value))
