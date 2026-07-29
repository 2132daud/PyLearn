import json

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user

from app.code_runner import check_task_solution
from app.decorators import require_role_for_blueprint
from app.extensions import db
from app.forms import CodeSubmitForm
from app.models import Course, Enrollment, Lesson, QuizChoice, Submission, Task, TaskType, UserRole

student_bp = Blueprint("student", __name__)
student_bp.before_request(require_role_for_blueprint(UserRole.STUDENT))


def _require_enrollment(course):
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course.id).first()
    if not enrollment:
        abort(403)
    return enrollment


def _solved_task_ids():
    return {s.task_id for s in current_user.submissions if s.is_correct}


@student_bp.route("/")
def dashboard():
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    return render_template("student/dashboard.html", enrollments=enrollments)


@student_bp.route("/courses")
def browse_courses():
    courses = Course.query.filter_by(is_published=True).order_by(Course.created_at.desc()).all()
    enrolled_ids = {e.course_id for e in current_user.enrollments}
    return render_template("student/browse_courses.html", courses=courses, enrolled_ids=enrolled_ids)


@student_bp.route("/courses/<int:course_id>/enroll", methods=["POST"])
def enroll(course_id):
    course = Course.query.get_or_404(course_id)
    if not course.is_published:
        abort(404)
    existing = Enrollment.query.filter_by(student_id=current_user.id, course_id=course.id).first()
    if not existing:
        db.session.add(Enrollment(student_id=current_user.id, course_id=course.id))
        db.session.commit()
        flash(f"Вы записаны на курс «{course.title}».", "success")
    return redirect(url_for("student.course_detail", course_id=course.id))


@student_bp.route("/courses/<int:course_id>")
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    _require_enrollment(course)

    solved_task_ids = _solved_task_ids()
    total_tasks = course.task_count()
    solved_in_course = sum(1 for lesson in course.lessons for task in lesson.tasks if task.id in solved_task_ids)
    progress = int((solved_in_course / total_tasks) * 100) if total_tasks else 0

    return render_template(
        "student/course_detail.html", course=course, solved_task_ids=solved_task_ids, progress=progress
    )


@student_bp.route("/lessons/<int:lesson_id>")
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    _require_enrollment(lesson.course)
    return render_template("student/lesson_detail.html", lesson=lesson, solved_task_ids=_solved_task_ids())


def _latest_submission(task_id):
    return (
        Submission.query.filter_by(task_id=task_id, student_id=current_user.id)
        .order_by(Submission.submitted_at.desc())
        .first()
    )


@student_bp.route("/tasks/<int:task_id>")
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    _require_enrollment(task.lesson.course)

    last_submission = _latest_submission(task.id)

    if task.type == TaskType.QUIZ:
        return render_template("student/task_quiz.html", task=task, last_submission=last_submission)

    form = CodeSubmitForm()
    if last_submission and not form.is_submitted():
        form.code_text.data = last_submission.code_text
    sample_cases = [tc for tc in task.test_cases if tc.is_sample]
    return render_template(
        "student/task_code.html", task=task, form=form, last_submission=last_submission, sample_cases=sample_cases
    )


@student_bp.route("/tasks/<int:task_id>/submit-quiz", methods=["POST"])
def submit_quiz(task_id):
    task = Task.query.get_or_404(task_id)
    _require_enrollment(task.lesson.course)
    if task.type != TaskType.QUIZ:
        abort(400)

    answers = {}
    correct_count = 0
    for question in task.questions:
        selected = request.form.get(f"question_{question.id}")
        answers[str(question.id)] = selected
        if selected and selected.isdigit():
            choice = QuizChoice.query.get(int(selected))
            if choice and choice.question_id == question.id and choice.is_correct:
                correct_count += 1

    total_questions = len(task.questions)
    is_correct = total_questions > 0 and correct_count == total_questions
    score = int((correct_count / total_questions) * task.max_score) if total_questions else 0

    submission = Submission(
        task_id=task.id,
        student_id=current_user.id,
        is_correct=is_correct,
        score=score,
        answers_json=json.dumps(answers),
        feedback=f"Правильных ответов: {correct_count} из {total_questions}",
    )
    db.session.add(submission)
    db.session.commit()

    if is_correct:
        flash(f"Тест пройден! Правильных ответов: {correct_count}/{total_questions}.", "success")
    else:
        flash(f"Правильных ответов: {correct_count}/{total_questions}. Попробуйте ещё раз.", "warning")

    return redirect(url_for("student.task_detail", task_id=task.id))


@student_bp.route("/tasks/<int:task_id>/submit-code", methods=["POST"])
def submit_code(task_id):
    task = Task.query.get_or_404(task_id)
    _require_enrollment(task.lesson.course)
    if task.type != TaskType.CODE:
        abort(400)

    form = CodeSubmitForm()
    if not form.validate_on_submit():
        flash("Введите код перед отправкой.", "danger")
        return redirect(url_for("student.task_detail", task_id=task.id))

    code_text = form.code_text.data
    max_len = current_app.config.get("MAX_CODE_LENGTH", 20000)
    if len(code_text) > max_len:
        flash(f"Код слишком длинный (максимум {max_len} символов).", "danger")
        return redirect(url_for("student.task_detail", task_id=task.id))

    timeout = current_app.config.get("CODE_EXECUTION_TIMEOUT", 5)
    passed, total, details = check_task_solution(code_text, task.test_cases, timeout=timeout)

    is_correct = total > 0 and passed == total
    score = int((passed / total) * task.max_score) if total else 0

    submission = Submission(
        task_id=task.id,
        student_id=current_user.id,
        is_correct=is_correct,
        score=score,
        code_text=code_text,
        feedback=json.dumps(details),
    )
    db.session.add(submission)
    db.session.commit()

    if is_correct:
        flash(f"Решение принято! Пройдено тестов: {passed}/{total}.", "success")
    else:
        flash(f"Пройдено тестов: {passed}/{total}. Проверьте результаты ниже.", "warning")

    return redirect(url_for("student.task_detail", task_id=task.id))


@student_bp.route("/progress")
def progress():
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    solved_task_ids = _solved_task_ids()

    rows = []
    for enrollment in enrollments:
        course = enrollment.course
        total_tasks = course.task_count()
        solved = sum(1 for lesson in course.lessons for task in lesson.tasks if task.id in solved_task_ids)
        pct = int((solved / total_tasks) * 100) if total_tasks else 0
        rows.append({"course": course, "solved": solved, "total": total_tasks, "progress": pct})

    return render_template("student/progress.html", rows=rows)
