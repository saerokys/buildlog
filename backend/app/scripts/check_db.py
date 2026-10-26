"""backend/.env의 DB 연결 정보를 확인합니다.

실행: backend 폴더에서 `.venv\\Scripts\\python -m app.scripts.check_db`

비밀번호와 전체 연결 주소는 출력하지 않습니다.
"""

import sys
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import ENV_FILE, SettingsError, get_settings

BACKEND_DIR = Path(__file__).resolve().parents[2]

CONNECTION_HINTS = """연결하지 못했습니다. 다음을 확인해 주세요.
- Supabase 대시보드의 Connect에서 'Session pooler' 주소를 복사했는지 (포트 5432)
- [YOUR-PASSWORD] 자리에 데이터베이스 비밀번호를 넣었는지
- 비밀번호에 @ : / # 같은 특수문자가 있다면 URL 인코딩했는지
- 사용자 이름이 postgres.프로젝트ID 형태인지
- Supabase 프로젝트가 일시 정지(Paused) 상태가 아닌지
- 인터넷 연결이 되는지"""


def _head_revision() -> str:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return ScriptDirectory.from_config(config).get_current_head()


def main() -> int:
    if not ENV_FILE.exists():
        print("backend/.env 파일이 없습니다. backend/.env.example을 복사해 만들어 주세요.")
        return 1

    try:
        settings = get_settings()
    except SettingsError as error:
        print(error)
        return 1

    # 설정을 확인한 뒤에 불러옵니다. 이 모듈은 불러올 때 설정을 읽기 때문입니다.
    from app.core.database import make_engine

    url = make_url(settings.database_url.get_secret_value())
    print(f"DB 종류: {url.get_backend_name()}")
    print(f"접속할 서버: {url.host or '(로컬 파일)'}")

    engine = make_engine(url.render_as_string(hide_password=False))
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            current = MigrationContext.configure(connection).get_current_revision()
    except SQLAlchemyError as error:
        reason = str(getattr(error, "orig", error)).strip().splitlines()[0]
        print(f"오류 내용: {reason}")
        print(CONNECTION_HINTS)
        return 1
    finally:
        engine.dispose()

    print("연결 성공")
    head = _head_revision()
    if current == head:
        print("테이블 준비 완료 (최신 상태)")
    else:
        print("테이블 준비가 필요합니다. backend 폴더에서 다음 명령을 실행해 주세요.")
        print("  .venv\\Scripts\\python -m alembic upgrade head")
    return 0


if __name__ == "__main__":
    sys.exit(main())
