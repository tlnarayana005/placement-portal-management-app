from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt


def role_required(*roles: str):
    """
    Lightweight RBAC helper.
    Assumes JWT includes `role` in additional_claims.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt() or {}
            role = claims.get("role")
            if role not in roles:
                return jsonify({"error": "forbidden"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator

