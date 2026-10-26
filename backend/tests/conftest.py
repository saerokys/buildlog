import os
import tempfile
from pathlib import Path

# 테스트는 .env 파일 없이도 실행되어야 하고 개발용 DB를 건드리면 안 되므로,
# 앱을 불러오기 전에 테스트용 값을 먼저 넣습니다.
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-real-use")
_unused_db_dir = Path(tempfile.mkdtemp(prefix="buildlog-test-"))
os.environ["DATABASE_URL"] = "sqlite:///" + (_unused_db_dir / "unused.sqlite3").as_posix()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database import get_db, make_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture
def engine(tmp_path):
    """테스트마다 새 임시 SQLite 파일을 만듭니다."""
    test_engine = make_engine("sqlite:///" + (tmp_path / "test.sqlite3").as_posix())
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
