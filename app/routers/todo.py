"""Router — HTTP 요청을 받고 응답을 돌려주는 곳입니다.

Router가 하는 일은 셋뿐입니다.
1. 요청에서 값을 꺼낸다 (경로의 id, 본문 JSON → schemas)
2. Service를 부른다
3. 결과를 응답으로, Service의 예외를 상태 코드(400 · 404)로 바꾼다
규칙(빈 제목 검사 등)이나 DB 코드는 여기 두지 않습니다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import TodoCreate, TodoResponse, TodoUpdate
from app.services.todo_service import InvalidTitleError, TodoNotFoundError, TodoService

router = APIRouter(prefix="/todos", tags=["todos"])


def get_service(session: Session = Depends(get_session)) -> TodoService:
    """요청마다 Repository와 Service를 만들어 이어 준다 — Router → Service → Repository → DB."""
    return TodoService(TodoRepository(session))


@router.get("", response_model=list[TodoResponse])
def list_todos(service: TodoService = Depends(get_service)):
    """예시 · 목록 조회 — GET /todos."""
    return service.list_todos()


@router.post("", status_code=201, response_model=TodoResponse)
def create_todo(body: TodoCreate, service: TodoService = Depends(get_service)):
    try:
        return service.create_todo(body.title)
    except InvalidTitleError:
        raise HTTPException(status_code=400, detail="제목을 입력하세요")


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, body: TodoUpdate, service: TodoService = Depends(get_service)):
    try:
        return service.update_todo(todo_id, title=body.title, completed=body.completed)
    except TodoNotFoundError:
        raise HTTPException(status_code=404, detail="없는 TODO입니다")
    except InvalidTitleError:
        raise HTTPException(status_code=400, detail="제목을 입력하세요")


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, service: TodoService = Depends(get_service)):
    try:
        service.delete_todo(todo_id)
    except TodoNotFoundError:
        raise HTTPException(status_code=404, detail="없는 TODO입니다")
