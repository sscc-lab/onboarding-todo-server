# onboarding-todo-server

SSCCOps Maintainer Onboarding **3회차 · Architecture & CI/CD** 실습용 Backend Repository입니다.
화면은 짝 Repository [`onboarding-todo-web`](https://github.com/sscc-lab/onboarding-todo-web)이 맡습니다.

이 템플릿에는 **이 README 하나만** 있습니다. 코드는 여러분의 2회차 `onboarding-todo`에서 직접 옮겨 오고,
그 `main.py` 한 파일을 **Router · Service · Repository**로 나눕니다.
**기초**에서는 PR마다 테스트가 저절로 도는 **CI**를 켜고, **심화**에서는 Merge 한 번이 Container Image · 배포까지 이어지는 **CD**를 더합니다.

```text
Application Flow                         Deployment Flow
Browser (onboarding-todo-web)            Commit
  │ HTTP / JSON                            → GitHub Actions (Test → Docker Build)
  ▼                                        → GitHub Container Registry (Image)
Router      app/routers/todo.py            → Render Deploy Hook
  ↓                                        → Render (Container 실행)
Service     app/services/todo_service.py
  ↓
Repository  app/repositories/todo_repository.py
  ↓
Database    SQLite(로컬) · PostgreSQL(Supabase)
```

> 2회차 `onboarding-todo`는 **고치지 않고 그대로 둡니다.** 거기서 복사해 올 뿐이고, 처음 모습과 지금을 비교하는 기준이 됩니다.

## 이번 주의 순서 — 한 단계 = Issue 하나 = PR 하나

| 단계 | Issue 제목 | Branch | 끝나면 |
|---|---|---|---|
| ① | 2회차 서버 코드를 옮겨 오고 테스트로 기준 잡기 | `chore/#1-import` | `pytest` 11 passed |
| ② | CI 켜기 — PR마다 테스트, 통과해야 Merge | `chore/#2-ci` | PR의 Checks에 `test` ✓ |
| ③ | 설정 · DB · 모델 · 스키마를 나누고 목록 조회를 Layer로 | `refactor/#3-structure` | 11 passed · CI ✓ |
| ④ | 등록을 Layer로 옮기기 | `refactor/#4-create` | 11 passed · CI ✓ |
| ⑤ | 수정 · 완료 변경을 Layer로 옮기기 | `refactor/#5-update` | 11 passed · CI ✓ |
| ⑥ | 삭제를 Layer로 옮기고 Service 테스트 더하기 | `refactor/#6-delete` | **16 passed** · CI ✓ |
| ⑦ | Dockerfile 만들기 *(심화)* | `chore/#7-docker` | — |
| ⑧ | CI에 CD 더하기 *(심화)* | `chore/#8-cd` | Merge하면 Render에 배포 |
| ⑨ | 장애 주입 — 세 가지 이상 *(심화)* | Issue «[장애] …» | — |

> **리팩터링 = 동작은 그대로, 구조만 바꾸기.** ①에서 테스트를 먼저 붙이고 ②에서 CI를 켜 두면, ③–⑥의 PR마다 GitHub가 «여전히 11개가 통과하는가»를
> 확인해 줍니다. 깨뜨렸다면 Merge 버튼이 잠깁니다. 초록불에서 시작해 초록불로 끝나는 것이 리팩터링입니다.
> 번호(`#1` …)는 화면에서 받은 내 Issue 번호로 바꿔 쓰세요.

## 만들 구조와 꼭 지킬 이름

```text
onboarding-todo-server/
├── app/
│   ├── __init__.py                   (빈 파일)
│   ├── main.py                       앱 조립 — CORS · Router 등록 · GET /
│   ├── config.py                     환경변수 읽기
│   ├── database.py                   engine · Session · Base
│   ├── models/todo.py                DB 테이블 todo (class Todo)
│   ├── schemas/todo.py               요청 · 응답 JSON 모양
│   ├── routers/todo.py               HTTP 요청 · 응답
│   ├── services/todo_service.py      규칙 (Business Logic)
│   └── repositories/todo_repository.py DB 접근
├── tests/                            ①에서 만든다
├── requirements.txt · requirements-dev.txt
├── .github/workflows/ci.yml          ②에서 만들고(CI), ⑧에서 CD를 더한다
└── Dockerfile · .dockerignore        ⑦에서 만든다
```

`models` · `schemas` · `routers` · `services` · `repositories` 폴더에도 빈 `__init__.py`를 하나씩 둡니다.

테스트와 채점이 아래 이름으로 코드를 찾으므로, **파일 위치와 이 이름들은 그대로** 씁니다.

| 파일 | 이 이름으로 |
|---|---|
| `app/main.py` | `app` (FastAPI 앱) |
| `app/database.py` | `engine` · `Base` · `get_session()` · `init_db()` |
| `app/models/todo.py` | `class Todo` |
| `app/repositories/todo_repository.py` | `class TodoRepository(session)` — `find_all()` · `find_by_id(todo_id)` · `save(todo)` · `delete(todo)` |
| `app/services/todo_service.py` | `class TodoService(repository)` — `list_todos()` · `create_todo(title)` · `update_todo(todo_id, title=None, completed=None)` · `delete_todo(todo_id)`<br>예외 `InvalidTitleError` · `TodoNotFoundError` |
| `app/routers/todo.py` | `router` (`APIRouter(prefix="/todos")`) · `get_service()` |

## Layer 규칙 — 누가 누구를 부르나

| Layer | 하는 일 | 알아도 되는 것 | 몰라야 하는 것 |
|---|---|---|---|
| Router | 요청에서 값을 꺼내고, Service를 부르고, 결과 · 예외를 HTTP 응답으로 바꾼다 | HTTP 상태 코드 · JSON 모양 | SQL · 규칙의 내용 |
| Service | 규칙 — 제목 공백 지우기, 빈 제목 금지, 없는 TODO 처리 | 규칙 · 자기 예외(`InvalidTitleError` · `TodoNotFoundError`) | HTTP(400 · 404) · SQL |
| Repository | DB에 저장 · 조회 · 삭제 | SQLAlchemy · 테이블 | HTTP · 규칙 |

- **위에서 아래로만 부릅니다.** Router → Service → Repository. Repository가 Service를 부르지 않습니다.
- **Service는 HTTP를 모릅니다.** 400 · 404 대신 자기 예외를 던지고, Router가 그것을 상태 코드로 바꿉니다.

## 0. 준비

이번 주에는 Repository를 **두 개** 만듭니다 — 이 `onboarding-todo-server`와 `onboarding-todo-web`. 둘 다 같은 방법입니다.

1. 이 페이지 오른쪽 위의 **Use this template → Create a new repository** → Owner는 **내 계정**, 이름은 `onboarding-todo-server`, Public.
2. **Settings → Collaborators**에서 Pair를 초대합니다.
3. 2회차 Repository **옆에** 내려받습니다. 아래 명령은 두 폴더가 나란히 있다고 보고 `../onboarding-todo`에서 복사합니다.

```bash
cd <2회차 onboarding-todo가 있는 폴더>
git clone https://github.com/<내 GitHub 아이디>/onboarding-todo-server.git
cd onboarding-todo-server
```

> 2회차 기능 네 개를 다 끝내지 못했다면, 먼저 2회차를 마무리하고 옵니다.
> 막혔다면 `sscc-lab/onboarding-todo`의 `solution` Branch를 참고해도 됩니다.

## 1. 기초 실습 — 옮기고, 테스트로 기준을 잡고, CI를 켜고, Layer로 나누기

### ① 2회차 서버 코드를 옮겨 오고 테스트로 기준 잡기 — `chore/#1-import`

2회차 `main.py`를 **고치지 않고** `app/main.py`로 옮깁니다. 화면(`index.html`)은 `onboarding-todo-web`으로 갈 것이라 가져오지 않습니다.

```bash
git switch -c chore/#1-import
mkdir -p app tests
cp ../onboarding-todo/main.py app/main.py
cp ../onboarding-todo/requirements.txt ../onboarding-todo/.gitignore .
touch app/__init__.py tests/__init__.py
printf -- "-r requirements.txt\npytest\nhttpx\n" > requirements-dev.txt   # 테스트에만 쓰는 패키지

python -m venv .venv
source .venv/bin/activate          # Windows(Git Bash): source .venv/Scripts/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload      # → http://localhost:8000/docs — 2회차와 똑같이 동작하는가
```

그다음 아래 두 파일을 `tests/`에 만듭니다. 이 테스트가 2회차 README의 **API 계약**을 코드로 적은 것입니다.

<details>
<summary><code>tests/conftest.py</code> — 테스트마다 빈 임시 DB에서 시작</summary>

```python
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
```
</details>

<details>
<summary><code>tests/test_todo_api.py</code> — API 계약 테스트 11개</summary>

```python
"""API 계약 테스트 — 2회차 README의 API 계약을 그대로 시험한다.

구조를 바꿔도(리팩터링) 밖에서 보는 동작은 그대로여야 한다. 이 테스트가 그 약속을 지킨다.
화면(onboarding-todo-web)은 이 계약만 믿고 API를 부른다.
"""


def create(client, title):
    return client.post("/todos", json={"title": title})


def test_health(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_is_empty_at_first(client):
    assert client.get("/todos").json() == []


def test_create_strips_title(client):
    r = create(client, "  공부하기 ")
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "공부하기"
    assert body["completed"] is False
    assert isinstance(body["id"], int)


def test_create_blank_title_is_400(client):
    assert create(client, "   ").status_code == 400


def test_list_is_newest_first(client):
    create(client, "첫째")
    create(client, "둘째")
    assert [t["title"] for t in client.get("/todos").json()] == ["둘째", "첫째"]


def test_update_title(client):
    todo_id = create(client, "공부하기").json()["id"]
    r = client.patch(f"/todos/{todo_id}", json={"title": "복습하기"})
    assert r.status_code == 200
    assert r.json()["title"] == "복습하기"


def test_update_completed_keeps_title(client):
    todo_id = create(client, "공부하기").json()["id"]
    r = client.patch(f"/todos/{todo_id}", json={"completed": True})
    assert r.status_code == 200
    assert r.json()["completed"] is True
    assert r.json()["title"] == "공부하기"
    saved = [t for t in client.get("/todos").json() if t["id"] == todo_id]
    assert saved[0]["completed"] is True  # 다시 조회해도 저장되어 있다 (commit)


def test_update_missing_is_404(client):
    assert client.patch("/todos/99999", json={"completed": True}).status_code == 404


def test_delete(client):
    todo_id = create(client, "공부하기").json()["id"]
    assert client.delete(f"/todos/{todo_id}").status_code == 204
    assert todo_id not in [t["id"] for t in client.get("/todos").json()]


def test_delete_missing_is_404(client):
    assert client.delete("/todos/99999").status_code == 404


def test_cors_allows_local_web(client):
    r = client.get("/todos", headers={"Origin": "http://localhost:5500"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5500"
```
</details>

```bash
pytest            # 11 passed — 이것이 기준선. 지금부터 PR마다 이 11개가 계속 통과해야 한다
git add .
git commit -m "#1 chore: 2회차 서버 코드를 옮겨 오고 API 계약 테스트를 더한다"
git push -u origin chore/#1-import
# → PR [#1] 2회차 서버 코드를 옮겨 오고 테스트로 기준 잡기 (Closes #1) → Pair Review → Squash and merge
```

> 11개 중 실패가 있다면 2회차 코드가 API 계약과 다른 곳입니다. 실패 메시지를 읽고 2회차 코드부터 고칩니다.

### ② CI 켜기 — `chore/#2-ci`

①에서 만든 테스트를 **GitHub가 PR마다 돌리게** 합니다. GitHub는 `.github/workflows/` 안의 YAML 파일만 읽습니다.
이제부터 ③–⑥의 리팩터링 PR마다 CI가 «여전히 11 passed인가»를 확인해 줍니다.

<details>
<summary><code>.github/workflows/ci.yml</code> — 기초용 (test Job 하나)</summary>

```yaml
# CI — Pull Request마다 테스트를 돌리고, main에 들어간 Commit도 한 번 더 확인한다.
#
#   Pull Request       : test   (합쳐도 되는지 확인)
#   main에 Push(Merge) : test   (합친 결과도 확인)
#
# 심화 실습 ⑧에서 이 파일에 build · push · deploy Job을 더해 CD까지 만든다.

name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test: # main 보호 규칙의 «Require status checks»에 이 이름(test)을 넣는다
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: 패키지 설치
        run: pip install -r requirements-dev.txt
      - name: 테스트
        run: pytest -v
```
</details>

```bash
git switch main && git pull
git switch -c chore/#2-ci
mkdir -p .github/workflows
# 위 내용으로 .github/workflows/ci.yml을 만든다
git add .github/workflows/ci.yml
git commit -m "#2 chore: PR마다 테스트를 돌리는 CI를 켠다"
git push -u origin chore/#2-ci
```

PR 화면 아래 **Checks**에 `CI / test`가 돌고 초록불이 되면 Merge합니다. **Actions** 탭에서 Step마다 로그를 열어 봅니다.

**main 보호 규칙** — Merge한 뒤 Repository의 **Settings → Rules → Rulesets → New ruleset → New branch ruleset**:

| 칸 | 값 |
|---|---|
| Ruleset Name | `main 보호` |
| Enforcement status | **Active** |
| Target branches | **Add target → Include default branch** |
| Require a pull request before merging | ✓ — Required approvals `1` (Pair의 Approve) |
| Require status checks to pass | ✓ — **Add checks**에서 `test` |
| Block force pushes | ✓ (기본으로 켜져 있다) |

이제 `test`가 빨간 PR은 **Merge 버튼이 잠기고**, `main`에 직접 Push도 막힙니다.
`test`는 CI가 한 번 돈 뒤에야 Add checks 목록에 나타나므로, 이 PR을 먼저 Merge하고 규칙을 겁니다.

### ③ 설정 · DB · 모델 · 스키마를 나누고 목록 조회를 Layer로 — `refactor/#3-structure`

`app/main.py`에서 «HTTP가 아닌 것»을 먼저 떼어 냅니다. 설정과 DB 연결은 아래 내용을 그대로 써도 됩니다
(2회차 코드에 `REQUIRE_DATABASE_URL`과 `version` 두 가지가 더해졌습니다 — ⑦ · ⑧에서 씁니다).

<details>
<summary><code>app/config.py</code> — 환경변수를 읽는 곳은 이 파일 하나</summary>

```python
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
```
</details>

<details>
<summary><code>app/database.py</code> — engine · Session · Base</summary>

```python
"""DB 연결 — engine과 Session을 만드는 곳입니다."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# echo=True — SQLAlchemy가 실제로 실행하는 SQL을 터미널에 보여 줍니다(2회차와 같다).
engine = create_engine(settings.database_url, echo=True)
SessionLocal = sessionmaker(engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """테이블이 없으면 만든다. 모델을 먼저 import해야 Base가 테이블을 안다."""
    from app.models import todo  # noqa: F401

    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """요청 하나에 Session 하나 — 요청이 끝나면 닫는다 (FastAPI의 Depends로 쓴다)."""
    with SessionLocal() as session:
        yield session
```
</details>

나머지는 2회차 `main.py`에서 옮깁니다.

| 2회차 `main.py`에 있던 것 | 옮길 곳 |
|---|---|
| `class Todo(Base)` | `app/models/todo.py` — `from app.database import Base` |
| `class TodoCreate` · `class TodoUpdate` | `app/schemas/todo.py` |
| `to_dict()` | 없앤다 — 대신 `schemas/todo.py`에 응답 모양 `TodoResponse`를 둔다 (아래) |
| `list_todos`의 `select(Todo).order_by(...)` | `TodoRepository.find_all()` |
| (규칙 없음) | `TodoService.list_todos()` — `self.repository.find_all()`을 돌려준다 |
| `@app.get("/todos")` | `app/routers/todo.py`의 `@router.get("")` |

```python
# app/schemas/todo.py에 더한다 — Todo 객체를 이 모양의 JSON으로 바꿔 준다 (to_dict 대신)
from pydantic import BaseModel, ConfigDict

class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    completed: bool
    created_at: str
```

```python
# app/routers/todo.py — 요청마다 Repository와 Service를 만들어 잇는다
router = APIRouter(prefix="/todos", tags=["todos"])

def get_service(session: Session = Depends(get_session)) -> TodoService:
    return TodoService(TodoRepository(session))

@router.get("", response_model=list[TodoResponse])
def list_todos(service: TodoService = Depends(get_service)):
    return service.list_todos()
```

`app/main.py`는 이렇게 바뀝니다 — 앱을 만들고, CORS를 걸고, `init_db()`, `app.include_router(todo.router)`,
그리고 `GET /`이 `{"status": "ok", "version": settings.version}`을 돌려주게 합니다.
**등록 · 수정 · 삭제 함수는 아직 `main.py`에 남겨 둡니다** — import만 새 위치(`app.database` · `app.models.todo` · `app.schemas.todo`)로 바꾸고, `to_dict`가 필요하면 그 함수도 잠시 남겨 둡니다.

```bash
pytest            # 여전히 11 passed — 구조만 바뀌고 동작은 그대로
git commit -m "#3 refactor: 설정 · DB · 모델 · 스키마를 나누고 목록 조회를 Layer로 옮긴다"
```

### ④ · ⑤ · ⑥ 기능 하나씩 Layer로 옮기기

기능 하나를 옮길 때마다 `main.py`에서 그 함수를 지우고, **아래층부터** 채웁니다 — Repository → Service → Router.
아래층부터 채우면 위층에서 부를 것이 먼저 생깁니다.

| 단계 | Repository | Service | Router | `main.py`에서 지울 것 |
|---|---|---|---|---|
| ④ 등록 | `save(todo)` | `create_todo(title)` + `InvalidTitleError` | `@router.post("", status_code=201)` | `create_todo` |
| ⑤ 수정 · 완료 변경 | `find_by_id(todo_id)` | `update_todo(...)` + `TodoNotFoundError` | `@router.patch("/{todo_id}")` | `update_todo` |
| ⑥ 삭제 | `delete(todo)` | `delete_todo(todo_id)` | `@router.delete("/{todo_id}", status_code=204)` | `delete_todo` |

**2회차 코드가 어디로 가나** — 등록을 예로 들면:

```python
# 2회차 main.py                                    → 3회차
title = body.title.strip()                          # Service — 공백 지우기
if not title:
    raise HTTPException(status_code=400, ...)       # Service: raise InvalidTitleError()
                                                    # Router:  except InvalidTitleError → HTTPException(400)
todo = Todo(title=title, completed=False, created_at=now())   # Service
session.add(todo); session.commit(); session.refresh(todo)    # Repository.save
return to_dict(todo)                                # Router: response_model=TodoResponse가 대신 한다
```

```python
# Service는 HTTP 대신 자기 예외를 던진다 — app/services/todo_service.py
class InvalidTitleError(Exception):
    """제목이 비어 있다."""

class TodoNotFoundError(Exception):
    """그 id의 TODO가 없다."""

# Router가 그것을 상태 코드로 바꾼다 — app/routers/todo.py
try:
    return service.create_todo(body.title)
except InvalidTitleError:
    raise HTTPException(status_code=400, detail="제목을 입력하세요")
```

**⑥에서 Service 테스트를 더합니다.** 진짜 DB 대신 가짜 Repository를 넣어 규칙만 시험합니다 — Layer를 나눴기 때문에 할 수 있는 일입니다.

<details>
<summary><code>tests/test_todo_service.py</code> — Service 테스트 5개</summary>

```python
"""Service 테스트 — DB도 HTTP도 없이 규칙만 시험한다.

Layer를 나눈 덕분에 할 수 있는 일입니다. 진짜 Repository 대신 리스트에 담아 두는 가짜(FakeRepository)를
넣으면, Service는 그것이 가짜인지 모른 채 똑같이 동작합니다.
2회차처럼 한 함수에 HTTP · 규칙 · DB가 섞여 있으면 이렇게 떼어 시험할 수 없습니다.
"""

import pytest

from app.models.todo import Todo
from app.services.todo_service import InvalidTitleError, TodoNotFoundError, TodoService


class FakeRepository:
    def __init__(self):
        self.items: dict[int, Todo] = {}

    def find_all(self):
        return sorted(self.items.values(), key=lambda t: t.id, reverse=True)

    def find_by_id(self, todo_id):
        return self.items.get(todo_id)

    def save(self, todo):
        if todo.id is None:
            todo.id = len(self.items) + 1
        self.items[todo.id] = todo
        return todo

    def delete(self, todo):
        del self.items[todo.id]


@pytest.fixture()
def service():
    return TodoService(FakeRepository())


def test_create_strips_title(service):
    assert service.create_todo("  공부하기 ").title == "공부하기"


def test_create_blank_title_raises(service):
    with pytest.raises(InvalidTitleError):
        service.create_todo("   ")


def test_update_missing_raises(service):
    with pytest.raises(TodoNotFoundError):
        service.update_todo(99, completed=True)


def test_update_only_completed_keeps_title(service):
    todo = service.create_todo("공부하기")
    updated = service.update_todo(todo.id, completed=True)
    assert updated.completed is True
    assert updated.title == "공부하기"


def test_delete_missing_raises(service):
    with pytest.raises(TodoNotFoundError):
        service.delete_todo(99)
```
</details>

```bash
pytest            # 16 passed — API 계약 11 + Service 규칙 5
```

⑥이 끝나면 `app/main.py`에는 «조립»만 남습니다. 그다음 `onboarding-todo-web`의 README대로 화면을 옮기고,
화면(5500)과 이 서버(8000)를 함께 띄워 2회차와 똑같이 동작하는지 확인합니다.

**확인할 것**

- 2회차와 3회차의 `create_todo`를 나란히 놓으면 각 줄이 어느 Layer로 갔는가
- `tests/test_todo_service.py`는 왜 DB 없이도 돌아가는가
- 서버를 다 나눴는데 화면은 왜 한 줄도 바꾸지 않아도 되는가 — **API 계약**이 같기 때문이다

## 2. 심화 실습 — Container와 CD

```text
Commit → GitHub Actions ─ test ─ build ─ push ─▶ ghcr.io/<아이디>/onboarding-todo-server:<commit>
                                                    │
                                      deploy ─▶ Render Deploy Hook ─▶ Render가 그 Image를 받아 Container 실행
                                                    │
                                      verify ─▶ GET / 의 version이 이 Commit인지 확인
```

### ⑦ Dockerfile 만들기 — `chore/#7-docker`

Repository 맨 위에 두 파일을 만듭니다. 한 줄씩 무엇을 하는지 주석을 읽으며 옮겨 적습니다.

<details>
<summary><code>Dockerfile</code></summary>

```dockerfile
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
```
</details>

<details>
<summary><code>.dockerignore</code> — Image에 넣지 않을 것</summary>

```text
# Image에 넣지 않을 것 — 작고 깨끗한 Image를 위해
.git
.github
.venv
venv
__pycache__
*.pyc
.pytest_cache
tests
todo.db
.env
*.md
```
</details>

Docker Desktop이 있으면 내 컴퓨터에서 먼저 띄워 봅니다. 없으면 건너뛰어도 ⑧의 Workflow가 같은 일을 합니다.

```bash
docker build -t todo-server .
docker run --rm -p 8000:8000 -e DATABASE_URL=sqlite:////tmp/todo.db todo-server
# → http://localhost:8000/docs   (Ctrl+C로 끈다)
docker run --rm -p 8000:8000 todo-server
# → DATABASE_URL이 없어 바로 멈춘다 — 로그의 RuntimeError를 읽어 본다
```

### ⑧ CI에 CD 더하기 — `chore/#8-cd`

②에서 만든 `.github/workflows/ci.yml`에 **build · deploy Job을 더합니다.** `test` Job은 그대로 두고, 그 뒤에 이어 붙입니다.
CD가 CI 뒤에 서기 때문에, **테스트를 통과한 Commit만 Image가 되고 배포됩니다.**

<details>
<summary><code>.github/workflows/ci.yml</code> — 심화 완성 (test → build → deploy)</summary>

```yaml
# CI/CD — ②에서 만든 CI에 ⑧에서 CD(build · push · deploy)를 더한 모습
#
#   Pull Request       : test → build                              (합쳐도 되는지 확인만)
#   main에 Push(Merge) : test → build → push → deploy → verify     (실제로 배포)
#
# 필요한 설정 (README «2. 심화 실습»)
#   Secrets   RENDER_DEPLOY_HOOK  Render 서비스의 Deploy Hook 주소
#   Variables API_URL             Render 서비스 주소 (https://….onrender.com)

name: CI/CD

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch: # Actions 탭에서 손으로 돌리기 (test · build만)

permissions:
  contents: read
  packages: write # GitHub Container Registry(ghcr.io)에 Image를 올리기 위해

jobs:
  test: # main 보호 규칙의 «Require status checks»에 이 이름(test)을 넣는다
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: 패키지 설치
        run: pip install -r requirements-dev.txt
      - name: 테스트
        run: pytest -v

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Image 이름 정하기
        # ghcr.io 주소는 소문자만 된다 — GitHub 아이디에 대문자가 있어도 되도록 바꾼다
        run: echo "IMAGE=ghcr.io/${GITHUB_REPOSITORY,,}" >> "$GITHUB_ENV"
      - name: Docker Image 빌드
        run: docker build --build-arg GIT_SHA=${{ github.sha }} -t $IMAGE:${{ github.sha }} -t $IMAGE:latest .
      - name: Registry 로그인
        if: github.event_name == 'push'
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      - name: Registry에 올리기
        if: github.event_name == 'push'
        run: |
          docker push $IMAGE:${{ github.sha }}
          docker push $IMAGE:latest

  deploy:
    needs: build
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - name: Render에 배포 요청 (Deploy Hook)
        env:
          HOOK: ${{ secrets.RENDER_DEPLOY_HOOK }}
        run: |
          if [ -z "$HOOK" ]; then
            echo "::error::RENDER_DEPLOY_HOOK Secret이 없습니다 — Settings → Secrets and variables → Actions에 넣으세요"
            exit 1
          fi
          IMAGE="ghcr.io/${GITHUB_REPOSITORY,,}:${{ github.sha }}"
          ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$IMAGE")
          # 이 Commit의 Image로 배포하라고 Render에 알린다
          curl -fsS -X POST "$HOOK&imgURL=$ENCODED"
          echo
          echo "배포 요청: $IMAGE"

      - name: 배포 확인 — 새 버전이 뜰 때까지 기다리기
        env:
          API_URL: ${{ vars.API_URL }}
        run: |
          if [ -z "$API_URL" ]; then
            echo "::warning::API_URL Variable이 없어 배포 확인을 건너뜁니다"
            exit 0
          fi
          # Render가 Image를 받아 Container를 띄우는 데 몇 분 걸린다 — 최대 10분, 20초마다 확인
          for i in $(seq 1 30); do
            VERSION=$(curl -fsS "$API_URL/" | python3 -c "import json,sys; print(json.load(sys.stdin).get('version',''))" || true)
            echo "[$i/30] 지금 버전: ${VERSION:-응답 없음}"
            if [ "$VERSION" = "${{ github.sha }}" ]; then
              echo "배포 완료 — $API_URL 에서 ${{ github.sha }} 이 돌고 있습니다"
              exit 0
            fi
            sleep 20
          done
          echo "::error::10분이 지나도 새 버전이 뜨지 않았습니다 — Render의 Events · Logs에서 Container가 왜 멈췄는지 보세요"
          exit 1
```
</details>

| 이벤트 | 도는 Job | 뜻 |
|---|---|---|
| Pull Request | test → build | 합쳐도 되는지 확인만 한다. Image는 올리지 않는다 |
| `main`에 Merge(Push) | test → build → push → deploy → verify | 실제로 배포한다 |

PR을 만들면 **Checks**에 `test` · `build`가 돕니다 — Dockerfile이 망가졌다면 여기서 멈춥니다.

**첫 Merge — 첫 배포는 실패하는 것이 정상입니다.** `main`에서 `test → build → push`까지 성공하고 **`deploy`가 빨갛게** 멈춥니다.
로그에 `RENDER_DEPLOY_HOOK Secret이 없습니다`가 보입니다 — 아직 Render를 연결하지 않았기 때문입니다. 이것이 첫 장애 추적입니다.

그래도 Image는 올라갔습니다. Repository 첫 화면 오른쪽 **Packages**에 `onboarding-todo-server`가 보입니다.
Package를 열고 **Package settings → Change visibility**가 Private이면 **Public**으로 바꿉니다 — Render가 로그인 없이 Image를 받게 하기 위해서입니다.

### Render — Image로 배포하는 새 서비스

2회차 Render 서비스는 코드를 직접 빌드했습니다. 이번에는 **이미 만들어진 Image를 실행**하는 서비스를 새로 만듭니다.

1. Render에서 **New → Web Service → Existing Image**.
2. Image URL: `ghcr.io/<내 GitHub 아이디 — 소문자>/onboarding-todo-server:latest`
3. Instance Type **Free**.
4. **Environment**:
   - `DATABASE_URL` — 2회차에 쓰던 Supabase 주소 그대로 (같은 DB를 계속 씁니다)
   - `ALLOWED_ORIGINS` — `onboarding-todo-web`의 Cloudflare Pages 주소 (웹 README 참고)
5. 배포가 끝나면 `https://<서비스 이름>.onrender.com/` → `{"status":"ok","version":"…"}`.
6. **Settings → Deploy Hook**의 주소를 복사합니다. 이 주소를 아는 사람은 누구나 배포를 일으킬 수 있으니 **비밀 값**입니다.
7. 2회차 Render 서비스는 **Settings → Suspend**로 멈춥니다. 무료 사용 시간을 두 서비스가 나눠 쓰지 않게 하기 위해서입니다.

### GitHub에 Secret · Variable 넣고 다시 돌리기

내 Repository의 **Settings → Secrets and variables → Actions**:

| 탭 | 이름 | 값 | 왜 이 칸인가 |
|---|---|---|---|
| Secrets | `RENDER_DEPLOY_HOOK` | Render의 Deploy Hook 주소 | 비밀 값 — 로그에 `***`로 가려진다 |
| Variables | `API_URL` | `https://<서비스 이름>.onrender.com` | 비밀이 아니다 — 배포 확인에 쓴다 |

그다음 **Actions → 빨갛게 멈춘 실행 → Re-run failed jobs**. `deploy`가 Render에 이 Commit의 Image로 배포하라고 알리고,
`배포 확인` Step이 `GET /`의 `version`이 이 Commit이 될 때까지 기다립니다(최대 10분). 이제부터는 PR을 Merge할 때마다 이 흐름이 저절로 돕니다.

## 3. 장애 주입 — 일부러 고장 내고 로그로 찾기 (⑨)

배포가 한 번 성공한 뒤에 합니다. 아래에서 **세 가지 이상**을 골라, 고장마다 Issue를 하나씩 남깁니다.
Issue 제목은 **`[장애] `로 시작**하고, 본문은 아래 «장애 기록 양식»을 붙여 넣어 채웁니다.

| # | 고장 내는 법 | 어디서 멈추나 | 로그에서 찾을 것 |
|---|---|---|---|
| 1 | `services/todo_service.py`에서 `.strip()`을 지우고 PR | PR의 `test` Job | `assert '  공부하기 ' == '공부하기'` |
| 2 | `Dockerfile`의 `COPY app/ app/`를 `COPY ap/ app/`로 바꾸고 PR | PR의 `build` Job | `"/ap": not found` |
| 3 | Render Environment에서 `DATABASE_URL`을 지우고 **Manual Deploy** | Render Events · Logs | `RuntimeError: DATABASE_URL 환경변수가 없습니다` |
| 4 | Render `DATABASE_URL`의 비밀번호를 한 글자 틀리게 | Render Logs | `password authentication failed` |
| 5 | `Dockerfile` CMD의 `--host 0.0.0.0`을 `--host 127.0.0.1`로 바꿔 Merge | `deploy`의 배포 확인 Step이 10분 뒤 실패, Render는 Port를 못 찾는다 | Render Events의 Port 관련 메시지 · 2회차 localhost 단원 |
| 6 | `Dockerfile` CMD의 `app.main:app`을 `app.mian:app`으로 바꿔 Merge | Render Logs (Container 시작) | `Could not import module "app.mian"` |
| 7 | Render Environment의 `ALLOWED_ORIGINS`에서 Pages 주소를 빼고 Manual Deploy | 브라우저 Console | `blocked by CORS policy` |

- 1 · 2는 PR에서 멈추므로 **합치지 않고** 닫으면 끝입니다. CI가 `main`을 지켜 준 것입니다.
- 5 · 6처럼 `main`에 들어간 고장은 1회차에서 배운 대로 **`git revert`로 되돌리는 PR**을 올립니다. `main`의 이력을 지우지 않습니다.
- 3 · 4 · 7은 코드가 아니라 **설정**의 고장입니다. Render에서 원래 값으로 돌려놓습니다.
- 로그에 비밀번호가 보이면 Issue에 붙이기 전에 지웁니다.

<details>
<summary>장애 기록 양식 — Issue 본문에 붙여 넣고, «어느 단계» 목록은 하나만 남기고 지운다</summary>

````markdown
## 무엇이 안 됐나

<!-- 눈에 보인 증상. 예: Actions가 빨갛다, 화면에 Failed to fetch, Render가 Deploy failed -->

## 어느 단계에서 멈췄나

<!-- 하나를 고르고 나머지는 지웁니다 -->
- Commit → **CI(Test)** → Build → Registry → Deploy Hook → Container → Application → Database
- Commit → CI(Test) → **Build** → Registry → Deploy Hook → Container → Application → Database
- Commit → CI(Test) → Build → **Registry** → Deploy Hook → Container → Application → Database
- Commit → CI(Test) → Build → Registry → **Deploy Hook** → Container → Application → Database
- Commit → CI(Test) → Build → Registry → Deploy Hook → **Container** → Application → Database
- Commit → CI(Test) → Build → Registry → Deploy Hook → Container → **Application** → Database
- Commit → CI(Test) → Build → Registry → Deploy Hook → Container → Application → **Database**

## 로그에서 찾은 한 줄

```text
여기에 원인을 말해 주는 로그 한 줄을 붙입니다 (비밀번호 · 토큰은 지웁니다)
```

로그를 본 곳: <!-- Actions의 어느 Job · Step / Render Events · Logs / 브라우저 Console · Network -->

## 원인

## 어떻게 풀었나

<!-- 고친 PR 번호(#번호)나 바꾼 설정 -->
````
</details>

> 같은 양식을 `.github/ISSUE_TEMPLATE/incident.md`로 만들어 두면 Issue를 만들 때 고를 수 있습니다(선택).

## 막힐 때

| 보이는 것 | 의심할 곳 |
|---|---|
| `ModuleNotFoundError: No module named 'app'` | Repository 맨 위 폴더에서 `uvicorn app.main:app`·`pytest`를 실행했는가, `app/__init__.py`가 있는가 |
| `ImportError: cannot import name …` | «꼭 지킬 이름» 표와 이름이 같은가 |
| ③–⑥ 뒤에 테스트가 실패 | 구조를 옮기다 동작이 바뀌었다 — 실패한 테스트 이름이 무엇이 달라졌는지 알려 준다 |
| Actions 탭에 아무것도 없다 | Workflow 파일이 `.github/workflows/` 안에 있는가, 확장자가 `.yml`인가 |
| `Invalid workflow file` | YAML 들여쓰기 — 공백 두 칸, Tab 금지 |
| Merge 버튼이 잠겨 있다 | main 보호 규칙 — `test`가 초록인가, Pair의 Approve를 받았는가 |
| 보호 규칙의 Add checks에 `test`가 없다 | CI가 아직 한 번도 돌지 않았다 — ② PR을 먼저 올려 돌린다 |
| `push`에서 `denied` · `403` | Workflow 맨 위 `permissions: packages: write`가 있는가 |
| Render가 Image를 못 받는다 | Package가 Public인가, Image 주소가 **소문자**인가 |
| `deploy`에서 `curl: (22) … 4xx` | `RENDER_DEPLOY_HOOK` 값이 정확한가, Render 서비스가 Image 방식인가 |
| 배포 확인이 10분 뒤 실패 | Render의 Events · Logs — Container가 왜 멈췄는지 (3절 표) |
| 화면에서 `Failed to fetch` · CORS | 웹의 `API_BASE`가 새 Render 주소인가, `ALLOWED_ORIGINS`에 새 Pages 주소가 있는가 |

## 완료 체크리스트

- [ ] 2회차 서버 코드를 옮겨 오고, API 계약 테스트 11개로 기준을 잡았다
- [ ] CI를 켜고 main 보호 규칙(PR 필수 · `test` 통과 필수)을 걸었다
- [ ] 구조 · 등록 · 수정 · 삭제를 PR로 하나씩 Router · Service · Repository에 옮기며, PR마다 CI가 초록이었다
- [ ] `pytest`가 16 passed
- [ ] `onboarding-todo-web`과 함께 로컬에서 2회차와 똑같이 동작한다
- [ ] Dockerfile을 만들고 CI에 CD를 더해, PR에서 test · build가 도는 것을 확인했다
- [ ] Merge 한 번으로 Image가 ghcr.io에 올라가고 Render에 배포되는 것을 확인했다
- [ ] 장애를 세 가지 이상 일으키고, «[장애]» Issue에 단계 · 로그 · 원인 · 해결을 남겼다
- [ ] Application Flow(Frontend → Router → Service → Repository → DB)와
      Deployment Flow(Commit → CI → Image → Registry → CD → Server)를 자기 말로 설명할 수 있다

## 규칙

1회차와 같습니다 — Branch `type/#번호-설명`, Commit `#번호 type: 내용`, PR `[#번호] 내용`, Squash and merge, `main`에 직접 Push하지 않기.
Secret(Deploy Hook · DB 주소)은 코드에 쓰지 않고 GitHub Secrets와 Render Environment에만 둡니다.

## 강사 · 채점용

- 완성본과 정본 테스트는 `sscc-lab/onboarding-todo-server`의 두 Branch에 있습니다 — [`solution-basic`](https://github.com/sscc-lab/onboarding-todo-server/tree/solution-basic)(기초 ①–⑥ — Layer + CI까지) · [`solution-advanced`](https://github.com/sscc-lab/onboarding-todo-server/tree/solution-advanced)(심화 ⑦ · ⑧ — CD까지). 먼저 직접 해 본 뒤에 봅니다.
- 평가표는 [`solution-advanced` Branch의 `grading/rubric.md`](https://github.com/sscc-lab/onboarding-todo-server/blob/solution-advanced/grading/rubric.md)입니다 — 실습을 마친 뒤 스스로 점검하는 데 써도 됩니다.
