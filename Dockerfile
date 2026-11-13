# onboarding-todo-server Container Image
# 한 줄씩 위에서 아래로 실행되고, 줄마다 Image의 층(layer)이 하나씩 쌓입니다.

# 1. 바탕 — Python 3.12가 설치된 작은 Linux
FROM python:3.12-slim

# 2. Container 안에서 일할 폴더
WORKDIR /srv

# .pyc 파일을 만들지 않고, 로그를 바로바로 내보낸다 (Render 로그에서 늦게 보이지 않게)
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# 3. 패키지 먼저 설치 — requirements.txt가 그대로면 이 층을 다시 쓰므로(cache) 빌드가 빨라진다
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 코드 복사 — 코드만 바뀌면 여기부터 다시 빌드한다
COPY app/ app/

# 5. 이 Image가 어느 Commit에서 왔는지 (CI가 --build-arg GIT_SHA=…로 넣는다)
ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA

# 6. Container에서는 DATABASE_URL이 꼭 있어야 한다 — 없으면 시작하지 않는다 (app/config.py)
ENV REQUIRE_DATABASE_URL=1

# 7. 실행 — Render가 정해 주는 PORT 환경변수로 연다(없으면 8000)
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
