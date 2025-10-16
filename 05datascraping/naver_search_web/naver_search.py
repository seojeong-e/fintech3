import requests
import pandas as pd
from dotenv import load_dotenv
import os
import re
from datetime import datetime
import time
load_dotenv(dotenv_path="./data/.env")

def text_clean(text):
    # HTML 태그를 없애는 정규표현식
    result = re.sub(r"</?[^>]+>", "", text)
    # 한글, 영문, 숫자 외의 모든 문자 제거 후 공백으로 변환
    result = re.sub(r"[^가-힣a-zA-Z0-9]", " ", result)
    result = result.replace("  ", " ").replace("  ", " ").replace("  ", " ")
    return result

def naver_api(keyword):
    page_num = 1
    total_page = 1
    start_num = 1
    
    result = []
    while page_num <= total_page:
        print(page_num, total_page, end="\r")
        time.sleep(0.8)
        user_id = os.getenv("Id")
        user_secret = os.getenv("Secret")
        url = f"https://openapi.naver.com/v1/search/news"
        payload = dict(query=keyword, display=100, start=start_num, sort="date")
        headers = {"X-Naver-Client-Id" : user_id, "X-Naver-Client-Secret" : user_secret}
        r = requests.get(url, params=payload, headers=headers)
        response = r.json()

        for item in response['items']:
            result.append(dict(title=item['title'], desc=text_clean(item['description']), link=item['link']))
            
        
        total_page = response['total'] // 100 + 1
        if total_page > 11:
            total_page = 11
        else:
            total_page = response['total'] // 100 + 1


        page_num += 1

        if start_num < 901:
            start_num += 100
        elif start_num > 900:
            start_num += 99
    

    return result 