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
