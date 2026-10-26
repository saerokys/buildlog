from fastapi import FastAPI

from app.core.config import get_settings


def create_app() -> FastAPI:
    # 필수 설정이 없으면 서버가 시작되지 않도록 먼저 읽습니다.
    get_settings()

    app = FastAPI(title="BuildLog API")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
