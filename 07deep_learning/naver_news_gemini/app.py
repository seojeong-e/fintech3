import os
import re
import html
import requests
import pandas as pd
import gradio as gr
from dotenv import load_dotenv
from google import genai

# -----------------------------
# 1) 환경변수 로드 (.env_gemini)
# -----------------------------
load_dotenv("./.env_gemini")

USER_ID = os.getenv("user_id")
USER_SECRET = os.getenv("user_secret")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# -----------------------------
# 2) 텍스트 정제 함수
# -----------------------------
def text_clean(text: str) -> str:
    if text is None:
        return ""
    # HTML 태그 제거
    text = re.sub(r"<.*?>", "", text)
    # HTML 엔티티(&quot; 등) 복원
    text = html.unescape(text)
    return text.strip()

# -----------------------------
# 3) 네이버 뉴스 수집 함수
# -----------------------------
def fetch_naver_news(keyword: str,
                     display: int = 50,
                     max_pages: int = 2) -> pd.DataFrame:
    """
    keyword로 네이버 뉴스 검색 후 DataFrame 반환
    - display: 페이지당 결과 수 (최대 100)
    - max_pages: 가져올 최대 페이지 수
    """
    if not USER_ID or not USER_SECRET:
        raise RuntimeError("user_id / user_secret 환경변수가 설정되어 있지 않습니다.")

    url = "https://openapi.naver.com/v1/search/news"
    headers = {
        "X-Naver-Client-Id": USER_ID,
        "X-Naver-Client-Secret": USER_SECRET,
    }

    all_items = []

    # 1페이지 먼저 요청해서 total 확인
    payload = dict(query=keyword, display=display, start=1, sort="date")
    r = requests.get(url, params=payload, headers=headers)
    if r.status_code != 200:
        raise RuntimeError(f"네이버 API 오류: {r.status_code}, {r.text}")

    response = r.json()
    total = response.get("total", 0)
    if total == 0:
        return pd.DataFrame()

    total_pages = total // display + 1
    total_pages = min(total_pages, max_pages)

    all_items.extend(response.get("items", []))

    for page in range(2, total_pages + 1):
        start = (page - 1) * display + 1
        if start > 1000:  # 네이버 뉴스 API start 최대 1000
            break

        payload = dict(query=keyword, display=display, start=start, sort="date")
        r = requests.get(url, params=payload, headers=headers)
        if r.status_code != 200:
            print(f"[경고] {page}페이지 요청 실패: {r.status_code}")
            break

        resp = r.json()
        items = resp.get("items", [])
        if not items:
            break
        all_items.extend(items)

    result = {}
    for item in all_items:
        for key, value in item.items():
            if key in ["title", "description"]:
                result.setdefault(key, []).append(text_clean(value))
            else:
                result.setdefault(key, []).append(value)

    df = pd.DataFrame(result)
    return df

# -----------------------------
# 4) Gemini 요약 함수
# -----------------------------
def summarize_with_gemini(df: pd.DataFrame, keyword: str) -> str:
    if GEMINI_API_KEY is None:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    if df.empty:
        return f"'{keyword}' 키워드로 수집된 뉴스가 없습니다."

    # 너무 길어지지 않도록 상위 20개만 사용
    df_use = df.head(20)

    news_lines = []
    for i, row in df_use.iterrows():
        title = row.get("title", "")
        desc = row.get("description", "")
        link = row.get("link", "")
        line = f"{i+1}. 제목: {title}\n   요약: {desc}\n   링크: {link}"
        news_lines.append(line)

    news_text = "\n\n".join(news_lines)

    prompt = f"""
다음은 '{keyword}' 키워드로 수집한 네이버 뉴스 목록입니다.

{news_text}

위 기사들을 바탕으로 다음 내용을 한국어로 정리해줘.

1) 전체 뉴스를 5~7줄 정도로 핵심만 요약
2) 주요 이슈/논점이 무엇인지 정리
3) 전반적인 분위기(긍정/부정/중립)를 한 줄로 평가
4) 추가로 눈에 띄는 서브 이슈가 있다면 2~3개 정도 bullet로 정리
5) 수집된 기사와 키워드의 주가를 분석해서 향후 주가에 미칠 영향 알려줘
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

# -----------------------------
# 5) Gradio용 파이프라인 함수
# -----------------------------
def run_pipeline(keyword: str,
                 max_pages: int = 2,
                 display: int = 50):
    keyword = keyword.strip()
    if not keyword:
        return "키워드를 입력하세요.", pd.DataFrame()

    try:
        df = fetch_naver_news(keyword, display=display, max_pages=max_pages)
    except Exception as e:
        return f"네이버 뉴스 수집 중 오류 발생:\n{e}", pd.DataFrame()

    if df.empty:
        return f"'{keyword}' 키워드로 뉴스가 없습니다.", pd.DataFrame()

    try:
        summary = summarize_with_gemini(df, keyword)
    except Exception as e:
        return f"Gemini 요약 중 오류 발생:\n{e}", df[["title", "link"]]

    # 프리뷰용으로 제목+링크만 보여줌
    preview_df = df[["title", "link"]].head(50)

    return summary, preview_df

# -----------------------------
# 6) Gradio 인터페이스 정의
# -----------------------------
with gr.Blocks(title="네이버 뉴스 + Gemini 요약") as demo:
    gr.Markdown("## 🔍 키워드 기반 네이버 뉴스 요약 서비스\n\n"
                "키워드를 입력하면 네이버 뉴스에서 기사를 가져와서 Gemini로 요약해줍니다.")

    with gr.Row():
        keyword_input = gr.Textbox(
            label="검색 키워드",
            placeholder="예) 핀테크, 인공지능, 비트코인 ..."
        )
    with gr.Row():
        max_pages_input = gr.Slider(
            minimum=1,
            maximum=5,
            value=2,
            step=1,
            label="가져올 페이지 수 (페이지당 display개)"
        )
        display_input = gr.Slider(
            minimum=10,
            maximum=100,
            value=50,
            step=10,
            label="페이지당 기사 수 (display)"
        )

    run_button = gr.Button("뉴스 수집 & 요약 실행")

    summary_output = gr.Markdown(label="Gemini 요약 결과")
    table_output = gr.Dataframe(label="수집된 뉴스 (제목 + 링크)")

    run_button.click(
        fn=run_pipeline,
        inputs=[keyword_input, max_pages_input, display_input],
        outputs=[summary_output, table_output]
    )

# -----------------------------
# 7) 실행
# -----------------------------
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
