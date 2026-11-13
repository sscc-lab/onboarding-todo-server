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
