"""Фабрика Flask-приложения PyLearn."""

import json
import os

from flask import Flask, render_template

from config import Config
from app.extensions import csrf, db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
    login_manager.login_message_category = "warning"

    from app import models  # noqa: F401  (регистрация моделей в metadata)

    from app.admin.routes import admin_bp
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.student.routes import student_bp
    from app.teacher.routes import teacher_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")

    _register_cli(app)
    _register_error_handlers(app)
    _register_template_filters(app)

    return app


def _register_cli(app):
    from app.cli import create_admin_command, init_db_command, seed_demo_command

    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(seed_demo_command)


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404


def _register_template_filters(app):
    import markdown as md

    from app.utils import plural_ru

    @app.template_filter("markdown")
    def markdown_filter(text):
        if not text:
            return ""
        return md.markdown(text, extensions=["fenced_code", "tables"])

    @app.template_filter("fromjson")
    def fromjson_filter(text):
        if not text:
            return []
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            return []

    @app.template_filter("plural_ru")
    def plural_ru_filter(number, forms):
        """Склоняет русское существительное по числу.

        Использование в шаблоне:
            {{ count }} {{ count|plural_ru("задание,задания,заданий") }}

        `forms` — строка из трёх вариантов через запятую: для 1, для 2-4, для 5+.
        """
        one, few, many = [f.strip() for f in forms.split(",")]
        return plural_ru(number, one, few, many)
