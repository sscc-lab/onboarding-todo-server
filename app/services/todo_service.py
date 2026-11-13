"""Service — 이 서비스의 규칙(Business Logic)을 두는 곳입니다.

«제목은 앞뒤 공백을 지운다», «빈 제목은 안 된다», «없는 TODO는 고칠 수 없다» 같은 규칙이 여기 있습니다.
Service는 HTTP를 모릅니다 — 상태 코드(400 · 404) 대신 이 파일의 예외를 던지고,
그것을 상태 코드로 바꾸는 일은 Router가 합니다. 그래서 Service는 HTTP 없이도 시험할 수 있습니다.
"""

from datetime import datetime

from app.models.todo import Todo
from app.repositories.todo_repository import TodoRepository


class TodoNotFoundError(Exception):
    """그 id의 TODO가 없다."""


class InvalidTitleError(Exception):
    """제목이 비어 있다."""


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class TodoService:
    def __init__(self, repository: TodoRepository):
        self.repository = repository

    def list_todos(self) -> list[Todo]:
        """예시 · 목록 — 규칙이 없으니 Repository에 그대로 맡긴다."""
        return self.repository.find_all()

    def create_todo(self, title: str) -> Todo:
        todo = Todo(title=self._clean_title(title), completed=False, created_at=now())
        return self.repository.save(todo)

    def update_todo(self, todo_id: int, title: str | None = None, completed: bool | None = None) -> Todo:
        todo = self._get(todo_id)
        if title is not None:
            todo.title = self._clean_title(title)
        if completed is not None:
            todo.completed = completed
        return self.repository.save(todo)

    def delete_todo(self, todo_id: int) -> None:
        self.repository.delete(self._get(todo_id))

    def _get(self, todo_id: int) -> Todo:
        todo = self.repository.find_by_id(todo_id)
        if todo is None:
            raise TodoNotFoundError(todo_id)
        return todo

    @staticmethod
    def _clean_title(title: str) -> str:
        cleaned = title.strip()
        if not cleaned:
            raise InvalidTitleError()
        return cleaned
