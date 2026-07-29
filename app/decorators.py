"""Вспомогательные декораторы/guard-функции для ограничения доступа по ролям."""

from functools import wraps

from flask import abort
from flask_login import current_user

from app.extensions import login_manager


def role_required(*roles):
    """Декоратор для отдельного view: разрешает доступ только указанным ролям."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def require_role_for_blueprint(role):
    """Фабрика guard-функции для before_request всего блюпринта (одна роль)."""

    def guard():
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if current_user.role != role:
            abort(403)

    return guard
