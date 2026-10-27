from datetime import datetime

from app.core.types import utc_now
from app.records.models import ErrorRecord, Todo
from app.records.validators import SOLUTION_REQUIRED


def set_todo_done(todo: Todo, done: bool, now: datetime | None = None) -> None:
    """할 일을 완료하거나 완료를 취소합니다.

    완료하면 완료 날짜·시간을 저장하고, 취소하면 지웁니다.
    이미 완료한 할 일을 다시 완료해도 처음 완료한 시간을 유지합니다.
    """
    if done:
        if not todo.is_done:
            todo.is_done = True
            todo.completed_at = now or utc_now()
    else:
        todo.is_done = False
        todo.completed_at = None


def resolve_error(record: ErrorRecord, solution: str | None = None, now: datetime | None = None) -> None:
    """오류를 해결 상태로 바꿉니다. 해결 방법이 없으면 바꾸지 않습니다.

    solution을 넘기면 해결 방법을 함께 저장합니다.
    이미 해결한 오류를 다시 해결해도 처음 해결한 시간을 유지합니다.
    """
    if solution is not None:
        record.solution = solution
    if not record.solution:
        raise ValueError(SOLUTION_REQUIRED)
    if not record.is_resolved:
        record.is_resolved = True
        record.resolved_at = now or utc_now()


def unresolve_error(record: ErrorRecord) -> None:
    """오류를 미해결로 되돌립니다. 해결 방법은 남기고 해결 날짜·시간만 지웁니다."""
    record.is_resolved = False
    record.resolved_at = None
