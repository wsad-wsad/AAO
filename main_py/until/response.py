from datetime import datetime
from typing import Any


class ResponseApi:
    def __init__(self):
        pass

    def __call__(
        self, status_code: int = 200, data: Any = None, message: str = "success"
    ):
        status = "success" if 200 <= status_code < 300 else "error"

        response_body = {
            "status": status,
            "statusCode": status_code,
            "message": message,
            "data": data,
            "meta": {"timestamp": datetime.now().isoformat(), "version": "1.0"},
        }

        return response_body, status_code


response = ResponseApi()
