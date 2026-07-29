from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm, RegisterForm
from app.models import User, UserRole

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Неверное имя пользователя или пароль.", "danger")
            return render_template("auth/login.html", form=form)
        if not user.is_active_account:
            flash("Учётная запись деактивирована. Обратитесь к администратору.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user)
        flash(f"Добро пожаловать, {user.username}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        if User.query.filter_by(username=username).first():
            flash("Такое имя пользователя уже занято.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("Такой email уже зарегистрирован.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(username=username, email=email, role=UserRole.STUDENT)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Регистрация прошла успешно. Теперь вы можете войти.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("main.index"))
