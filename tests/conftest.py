"""테스트 준비 — 테스트마다 빈 임시 SQLite에서 시작한다.

app을 import하기 전에 DATABASE_URL을 정해야 한다(engine은 import할 때 만들어진다).
그래서 이 파일 맨 위에서 환경변수부터 바꾼다. 내 todo.db나 Supabase에는 닿지 않는다.

2회차 main.py를 app/main.py로 그대로 옮긴 처음에도, Layer로 나눈 뒤에도 똑같이 돈다.
"""

import os
import tempfile

_db = os.path.join(tempfile.mkdtemp(prefix="todo-test-"), "test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _db.replace("\\", "/")
os.environ.pop("REQUIRE_DATABASE_URL", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

try:
    from app.database import Base, engine  # Layer로 나눈 뒤 — engine은 database.py에
except ImportError:
    from app.main import Base, engine  # 처음 — 2회차 main.py를 그대로 옮겼을 때


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c
