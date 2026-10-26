from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

INVALID_REQUEST = "입력값을 다시 확인해 주세요."


class AppError(Exception):
    """화면에 보여줄 안내 문구와 칸별 오류를 담아 돌려주는 오류입니다.

    응답 모양: {"message": "...", "errors": {"칸 이름": "안내 문구"}}
    """

    def __init__(self, status_code: int, message: str, errors: dict[str, str] | None = None):
        self.status_code = status_code
        self.message = message
        self.errors = errors or {}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message, "errors": exc.errors},
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # 칸이 빠졌거나 글자가 아닌 값처럼 형식 자체가 잘못된 요청입니다.
        errors = {}
        for error in exc.errors():
            location = error.get("loc", ())
            if len(location) > 1:
                errors[str(location[-1])] = INVALID_REQUEST
        return JSONResponse(status_code=400, content={"message": INVALID_REQUEST, "errors": errors})
