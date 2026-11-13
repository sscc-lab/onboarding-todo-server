"""요청 · 응답 본문의 모양 — API 계약을 코드로 적은 것입니다.

DB 모델(models/todo.py)과 따로 두는 이유: DB 테이블이 바뀌어도 화면과 약속한 JSON 모양은
그대로 지킬 수 있어야 하기 때문입니다.
"""

from pydantic import BaseModel, ConfigDict


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None


class TodoResponse(BaseModel):
    # from_attributes — Todo 객체의 속성을 읽어 이 모양으로 바꿔 준다 (2회차의 to_dict 대신)
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    completed: bool
    created_at: str
