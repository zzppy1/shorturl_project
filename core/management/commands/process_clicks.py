# core/management/commands/process_clicks.py
import json
import time

import redis
from django.conf import settings
from django.core.management import BaseCommand
from django.db import connection

redis_conn=redis.Redis.from_url(settings.CACHES['default']['LOCATION'])

class Command(BaseCommand):
    help='消费点击队列，批量更新数据库'
    def handle(self,*args,**options):
        queue_key="click_queue"
        batch_size=100
        while True:
            # 从队列右侧弹出（先进先出）
            items=[]
            for _ in range(batch_size):
                item=redis_conn.rpop(queue_key)
                if not item:
                    break
                items.append(json.loads(item))

            if not items:
                time.sleep(1)
                continue

            # 聚合统计每个 short_code 的点击次数
            counter={}
            for item in items:
                code=item['short_code']
                counter[code]=counter.get(code,0)+1

            # 批量更新数据库（使用原生 SQL 或 ORM 的 bulk_update）
            with connection.cursor() as cursor:
                for code,clicks in counter.items():
                    cursor.execute(
                        "UPDATE core_shorturl SET total_dicks = total_dicks + %s WHERE short_code = %s",
                        [clicks,code]
                    )
            self.stdout.write(f"Processed{len(items)}clicks,updated{len(counter)}short URLs")
