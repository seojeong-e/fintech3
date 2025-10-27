import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dbio2 import to_db, db_connect

# --- 2. 헬퍼 함수: 날짜 변환 ---
def to_date(date_str):
    try:
        parsed_str = date_str.replace(" ","").replace("년","-").replace("월","-").replace("일","")
        return datetime.strptime(parsed_str, "%Y-%m-%d").date()
    except ValueError:
        return None

# --- 3. 핵심 기능: 앱 리뷰 스크래핑 함수 ---
def app_review_extractor(app_tuple):
    
    app_name, app_id = app_tuple
    
    options = Options()
    options.add_experimental_option("detach", True)
    options.add_argument("start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
    options.add_argument("lang=ko_KR")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
        )
    
    driver.get(f"https://play.google.com/store/apps/details?id={app_id}&hl=ko")
    wait = WebDriverWait(driver, 10)

    try:
        driver.execute_script("window.scrollTo(0,1400)")
        time.sleep(2)
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label *= "평점 및 리뷰 자세히 알아보기"]')))
        button.click()
        wait.until(EC.element_to_be_clickable((By.ID, "sortBy_1"))).click()
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'span[aria-label *= "최신"]'))).click()
        time.sleep(2)
    except TimeoutException:
        driver.close()
        return pd.DataFrame() 

    today = datetime.today().date()
    end_date = today - timedelta(days=7) 
    
    try:
        scrollable_element = driver.find_element(By.CSS_SELECTOR, ".fysCi.Vk3ZVd")
    except NoSuchElementException:
        driver.close()
        return pd.DataFrame()

    previous_review_count = 0

    while True:
        review_list = driver.find_elements(By.CSS_SELECTOR, "div.RHo1pe")
        current_review_count = len(review_list)

        if current_review_count == previous_review_count:
            break
            
        previous_review_count = current_review_count
        
        try:
            last_review = review_list[-1]
            last_date_str = last_review.find_element(By.CSS_SELECTOR, ".bp9Aid").get_attribute('innerHTML')
            last_review_date = to_date(last_date_str) 

            if last_review_date and last_review_date < end_date:
                break
        except Exception:
            break

        driver.execute_script("arguments[0].scrollBy(0, 5000);", scrollable_element)
        time.sleep(2)

    review_list = driver.find_elements(By.CSS_SELECTOR, "div.RHo1pe")

    result = {}
    cols = ('리뷰일','앱 이름','별점','사용자 리뷰','회사 응답')
    
    for review in review_list:
        try:
            review_date_str = review.find_element(By.CSS_SELECTOR, ".bp9Aid").get_attribute('innerHTML')
            review_date = to_date(review_date_str)
            
            if not review_date or review_date < end_date:
                continue 

            rating = float(review.find_element(By.CSS_SELECTOR, 'div[aria-label*="별표 5개 만점에"]').get_attribute('aria-label').split()[3].replace("개를",""))
            user_review = review.find_element(By.CSS_SELECTOR,".h3YV2d").get_attribute('innerHTML')

            try:
                company_reply = review.find_element(By.CSS_SELECTOR,".ras4vb > div").text.replace("\n", " ")
            except NoSuchElementException:
                company_reply = "회사 응답 없음"

            values = (review_date, app_name, rating, user_review, company_reply) 
            for key, value in zip(cols, values):
                result.setdefault(key, []).append(value)
        
        except Exception:
            continue

    driver.close()
    df = pd.DataFrame(result)
    return df

# --- 4. 메인(Main) 함수: DB 연결 및 작업 실행 ---
def main():
    
    DB_NAME = "Bank_reviews" 
    
    apps = {
        "토스": "viva.republica.toss",
        "KB스타뱅킹": "com.kbstar.kbbank",
        "하나원큐": "com.kebhana.hanapush",
        "뱅크샐러드" : "com.rainist.banksalad2", 
        "핀다": "kr.co.finda.finda"
    }

    for app_tuple in apps.items():
        app_name = app_tuple[0]
        app_id = app_tuple[1]
        
        TABLE_NAME = app_id.replace(".", "_") 
        
        df = app_review_extractor(app_tuple) 
        
        if df.empty:
            continue

        try:
            to_db(DB_NAME, TABLE_NAME, df)
        except Exception:
            continue # DB 저장 실패 시 조용히 다음 앱으로 넘어감

# --- 5. 스크립트 실행 시작점 ---
if __name__ == "__main__":
    main()