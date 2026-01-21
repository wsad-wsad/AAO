from datetime import datetime

from flask import jsonify


def response(status_code, data, message):
    status = "success" if 200 <= status_code < 300 else "error"

    response_body = {
        "status": status,
        "statusCode": status_code,
        "message": message,
        # Data dibungkus list sesuai format Express kamu
        "data": [data] if data is not None else [],
        "meta": {"timestamp": datetime.now().isoformat(), "version": "1.0"},
    }

    return jsonify(response_body), status_code
