"""DB 모델 — 테이블 todo 하나 = 클래스 Todo 하나 (2회차 main.py에서 그대로 옮겼다)."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(primary_key=True)  # 자동 증가 번호
    title: Mapped[str] = mapped_column(String(200))
    completed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(String(32))
