from fastapi import FastAPI

from app.accounts.router import router as accounts_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers


def create_app() -> FastAPI:
    # 필수 설정이 없으면 서버가 시작되지 않도록 먼저 읽습니다.
    get_settings()

    app = FastAPI(title="BuildLog API")
    register_error_handlers(app)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(accounts_router)

    return app


app = create_app()
