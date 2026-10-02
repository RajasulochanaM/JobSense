"""Consistent JSON envelope for every API response."""
from flask import jsonify


def success(data=None, message="OK", status=200):
    return jsonify({"success": True, "data": data, "message": message}), status


def error(message, code="ERROR", status=400, details=None):
    return jsonify({
        "success": False,
        "data": None,
        "message": message,
        "error": {"code": code, "details": details},
    }), status


class APIError(Exception):
    """Raise anywhere inside a request to return a structured error response."""

    def __init__(self, message, code="BAD_REQUEST", status=400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.details = details


class NotFound(APIError):
    def __init__(self, message="Resource not found"):
        super().__init__(message, "NOT_FOUND", 404)


class ValidationError(APIError):
    def __init__(self, message, details=None):
        super().__init__(message, "VALIDATION_ERROR", 422, details)
