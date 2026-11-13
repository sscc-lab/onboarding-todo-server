"""앱 조립 — 설정 · CORS · Router를 한데 모아 FastAPI 앱 하나를 만듭니다.

2회차에는 main.py 한 파일이 전부였습니다. 이제 main.py는 «조립»만 하고,
실제 일은 routers → services → repositories가 나눠 맡습니다.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import todo

app = FastAPI(title="onboarding-todo-server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
app.include_router(todo.router)


@app.get("/")
def health():
    # 서버가 살아 있는지, 지금 어느 Commit이 돌고 있는지 확인하는 용도 — CD가 배포 완료를 이것으로 확인한다.
    return {"status": "ok", "version": settings.version}
