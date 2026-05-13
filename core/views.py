import json
import time
import random

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from socketio.base_client import original_signal_handler

from .models import ShortURL
from .utils import create_short_link
import redis
# Create your views here.
#
def check_rate_limit(ip,limit=10,window=60):
    """
       滑动窗口限流
       ip: 用户标识
       limit: 窗口内最大请求数
       window: 窗口大小（秒）
       返回 True 表示允许请求，False 表示超限
    """
    key=f"rate_limit:sliding:{ip}"
    now=time.time()
    # 移除窗口外的旧记录
    # redis_conn.zremrangebyscore(key,0,now-window)
    removed = redis_conn.zremrangebyscore(key, 0, now - window)

    # 获取当前窗口内请求数
    current=redis_conn.zcard(key)
    print(f"[RATE] {ip} current={current}, removed={removed}")
    if current>=limit:
        return False
    member=str(time.time_ns())
    redis_conn.zadd(key,{member:now})
    redis_conn.expire(key,window+10)
    return True

def index(request):
    return render(request,'index.html')

redis_conn=redis.Redis.from_url(settings.CACHES['default']['LOCATION'])

@csrf_exempt
@require_http_methods(["POST"])
def shorten_api(request):
    try :
        data=json.loads(request.body)
        original_url=data.get('url')
        if not original_url:
            return JsonResponse({'error':'Missing url'},status=400)
        # 可选：限流（同一IP每分钟最多10次）
        # ip = request.META.get('REMOTE_ADDR')
        # rate_key = f'rate_limit:{ip}'
        # current = redis_conn.incr(rate_key)
        # if current == 1:
        #     redis_conn.expire(rate_key, 60)
        # if current > 10:
        #     return JsonResponse({'error': 'Too many requests'}, status=429

        ip=request.META.get('REMOTE_ADDR')
        if not check_rate_limit(ip,limit=10,window=60):
            return JsonResponse({'error':'Too many request.Please try latter.'},status=429)
        link=create_short_link(original_url)
        short_url=request.build_absolute_uri(f'/{link.short_code}')

        #缓存雪崩防护（随机过期时间）
        expire_time=3600+random.randint(0,300)#60分钟+0~5分钟随机
        cache.set(f'shortlink:{link.short_code}',original_url,expire_time)

        return JsonResponse({
            'short_code':link.short_code,
            'short_url':short_url,
            'original_url':original_url,
        })
    except Exception as e:
        return JsonResponse({'error':str(e)},status=500)


def redirect_view(request, short_code):
    original_url = cache.get(f'url:{short_code}')
    # original_url=None
    if original_url is None:
        # 缓存中没有（包括没有空值情况），尝试获取锁
        lock_key=f"lock:url:{short_code}"
        lock_acquired=redis_conn.setnx(lock_key,"1")
        if lock_acquired:
            #获得锁，设置锁自动过期时间，防止死锁
            redis_conn.expire(lock_key,5)
            try:
                #查数据库
                link = ShortURL.objects.filter(short_code=short_code).first()
                if link:
                    original_url = link.original_url
                    #命中数据库写入缓存
                    expire_time = 3600 + random.randint(0, 300)  # 60分钟+0~5分钟随机
                    cache.set(f'shortlink:{link.short_code}', original_url, expire_time)
            except ShortURL.DoesNotExist:
                # 缓存一个空值，过期时间60~90秒，防止缓存穿透
                expire_time = 60 + random.randint(0, 30)  # 60~90秒
                cache.set(f'url:{short_code}', None, expire_time)
                return HttpResponseNotFound("短链接不存在")
            finally:
                #释放锁
                redis_conn.delete(lock_key)
        else:
            #未获得锁，说明有其他请求正在重建缓存，等待并重试
            #简单重试 10 次，每次等待 0.05 秒
            for _ in range(10):
                time.sleep(0.05)
                original_url=cache.get(f'url:{short_code}')
                if original_url is not None:
                    break
            else:
                # 最终仍未从缓存获取到，返回错误（或降级处理）
                return HttpResponseNotFound("短链接暂时不可用，请稍后重试")

    else:
        # 如果缓存中取到的值是 None，说明之前查过不存在，直接返回404
        if original_url is None:
            return HttpResponseNotFound("短链接不存在")

    #点击计数
    # click_key = f'click_count:{short_code}'
    # count = redis_conn.incr(click_key)
    # print(f"[DEBUG] short_code={short_code}, count={count}, count%10={count%10}")
    #
    # if count % 100 == 0:
    #     print("[DEBUG] 进入更新分支")
    #     try:
    #         link = ShortURL.objects.get(short_code=short_code)
    #         print(f"[DEBUG] 更新前 total_dicks={link.total_dicks}")
    #         link.total_dicks = count
    #         link.save(update_fields=['total_dicks'])
    #         print(f"[DEBUG] 更新后 total_dicks={link.total_dicks}")
    #     except Exception as e:
    #         import traceback
    #         traceback.print_exc()
    # else:
    #     print("[DEBUG] 未进入更新分支")

    #将点击计数改为异步计数
    #将点击事件推入redis列表
    queue_key="click_queue"
    event=json.dumps({"short_code":short_code,
                      "timestamp":time.time()
                      })
    redis_conn.lpush(queue_key,event)

    return HttpResponseRedirect(original_url)