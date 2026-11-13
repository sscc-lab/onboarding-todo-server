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
