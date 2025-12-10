FROM python:3.10-slim

# 시스템 기본 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 생성
WORKDIR /app

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .

# Gradio는 0.0.0.0으로 실행해야 외부 접속 가능
EXPOSE 7860

CMD ["python", "app.py"]
