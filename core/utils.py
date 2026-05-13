#base62
from math import remainder

BASE62_charset="0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE=len(BASE62_charset)

def int_to_base62(num:int)->str:
    if num==0:
        return BASE62_charset[0]
    result=""
    while num>0:
        num,remainder=divmod(num,BASE)
        result=BASE62_charset[remainder]+result
    return result

def base62_to_int(s:str)->int:
    num=0
    for char in s:
        num=num*BASE+BASE62_charset.index(char)
    return num

import uuid
from  .models import ShortURL

def create_short_link(original_url):
    while True:
        temp_id=uuid.uuid4().int%(62**4)
        short_code=int_to_base62(temp_id)
        if not ShortURL.objects.filter(short_code=short_code).exists():
            break
    link=ShortURL(
        original_url=original_url,
        short_code=short_code
    )
    link.save()
    return link
