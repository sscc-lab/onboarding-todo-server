"""설정 — 환경변수를 읽는 곳은 이 파일 하나뿐입니다.

코드 여기저기서 os.environ을 읽으면, 어떤 값이 필요한지 한눈에 보이지 않습니다.
그래서 설정은 여기서 한 번 읽고, 다른 파일은 settings만 씁니다.
"""

import os
from dataclasses import dataclass


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Container(Dockerfile)는 REQUIRE_DATABASE_URL=1로 실행된다.
        # 배포에서 DATABASE_URL을 빠뜨렸는데 조용히 SQLite로 돌면, 서버를 다시 시작할 때마다 데이터가 사라진다.
        # 그래서 Container에서는 시작하자마자 멈추고 로그에 이유를 남긴다.
        if os.environ.get("REQUIRE_DATABASE_URL") == "1":
            raise RuntimeError("DATABASE_URL 환경변수가 없습니다 — Render의 Environment에 넣으세요")
        return "sqlite:///./todo.db"  # 로컬 개발용 기본값
    # Supabase가 주는 postgresql:// 주소를 psycopg(3) 드라이버로 연결하도록 맞춥니다.
    if url.startswith(("postgresql://", "postgres://")):
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str
    allowed_origins: list[str]
    version: str


settings = Settings(
    database_url=_database_url(),
    # 이 API를 불러도 되는 화면 주소. 배포하면 Cloudflare Pages 주소를 넣는다(쉼표로 여러 개).
    allowed_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500").split(","),
    # 지금 돌고 있는 코드가 어느 Commit인지 — CI가 Image를 만들 때 넣는다. 로컬에서는 dev.
    version=os.environ.get("GIT_SHA", "dev"),
)
