from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user

from app.decorators import require_role_for_blueprint
from app.extensions import db
from app.forms import CreateTeacherForm, UserEditForm
from app.models import Course, User, UserRole

admin_bp = Blueprint("admin", __name__)
admin_bp.before_request(require_role_for_blueprint(UserRole.ADMIN))


@admin_bp.route("/")
def dashboard():
    stats = {
        "total_users": User.query.count(),
        "total_students": User.query.filter_by(role=UserRole.STUDENT).count(),
        "total_teachers": User.query.filter_by(role=UserRole.TEACHER).count(),
        "total_admins": User.query.filter_by(role=UserRole.ADMIN).count(),
        "total_courses": Course.query.count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.route("/users")
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.route("/users/create-teacher", methods=["GET", "POST"])
def create_teacher():
    form = CreateTeacherForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()

        if User.query.filter_by(username=username).first():
            flash("Такое имя пользователя уже занято.", "danger")
            return render_template("admin/create_teacher.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("Такой email уже зарегистрирован.", "danger")
            return render_template("admin/create_teacher.html", form=form)

        teacher = User(username=username, email=email, role=UserRole.TEACHER)
        teacher.set_password(form.password.data)
        db.session.add(teacher)
        db.session.commit()
        flash(f"Учитель «{teacher.username}» создан.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/create_teacher.html", form=form)


@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        if user.id == current_user.id and form.role.data != UserRole.ADMIN:
            flash("Нельзя понизить роль собственной учётной записи.", "danger")
            return render_template("admin/user_edit.html", form=form, user=user)

        user.role = form.role.data
        user.is_active_account = form.is_active_account.data
        db.session.commit()
        flash("Пользователь обновлён.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/user_edit.html", form=form, user=user)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Нельзя удалить собственную учётную запись.", "danger")
        return redirect(url_for("admin.users"))
    db.session.delete(user)
    db.session.commit()
    flash("Пользователь удалён.", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/courses")
def courses():
    all_courses = Course.query.order_by(Course.created_at.desc()).all()
    return render_template("admin/courses.html", courses=all_courses)


@admin_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Курс удалён.", "info")
    return redirect(url_for("admin.courses"))
