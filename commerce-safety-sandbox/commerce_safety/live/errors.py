from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiveHTTPError(Exception):
    status_code: int
    code: str
    message: str

    def __str__(self) -> str:
        return self.message


def error_response(status_code: int, code: str, message: str) -> tuple[int, dict]:
    return status_code, {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
        },
    }
