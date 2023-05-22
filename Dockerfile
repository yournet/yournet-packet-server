# Docker 이미지의 베이스 이미지 선택
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 어플리케이션 소스 코드 복사
COPY . .

# 어플리케이션 실행
CMD ["python", "app.py"]
