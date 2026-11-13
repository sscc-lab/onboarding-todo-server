"""Repository — DB에 닿는 코드는 여기에만 둡니다.

SQLAlchemy(Session · select)를 아는 층은 이 파일 하나입니다.
Service는 «저장해 줘 · 찾아 줘»라고만 말하고, 어떻게 저장하는지는 모릅니다.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.todo import Todo


class TodoRepository:
    def __init__(self, session: Session):
        self.session = session

    def find_all(self) -> list[Todo]:
        """예시 · 전부 찾기 — 최신순."""
        return list(self.session.scalars(select(Todo).order_by(Todo.id.desc())))

    def find_by_id(self, todo_id: int) -> Todo | None:
        """id로 하나 찾기 — 없으면 None."""
        return self.session.get(Todo, todo_id)

    def save(self, todo: Todo) -> Todo:
        """새 Todo는 INSERT, 이미 있던 Todo는 바뀐 값을 UPDATE — 저장한 뒤 DB가 정한 값(id)을 받아 온다."""
        self.session.add(todo)
        self.session.commit()
        self.session.refresh(todo)
        return todo

    def delete(self, todo: Todo) -> None:
        """지우기 — DELETE."""
        self.session.delete(todo)
        self.session.commit()
