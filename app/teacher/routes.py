from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user

from app.decorators import require_role_for_blueprint
from app.extensions import db
from app.forms import CodeTestCaseForm, CourseForm, LessonForm, QuizQuestionForm, TaskForm
from app.models import (
    CodeTestCase,
    Course,
    Lesson,
    QuizChoice,
    QuizQuestion,
    Submission,
    Task,
    TaskType,
    UserRole,
)

teacher_bp = Blueprint("teacher", __name__)
teacher_bp.before_request(require_role_for_blueprint(UserRole.TEACHER))


def _get_owned_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.teacher_id != current_user.id:
        abort(403)
    return course


def _get_owned_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.course.teacher_id != current_user.id:
        abort(403)
    return lesson


def _get_owned_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.lesson.course.teacher_id != current_user.id:
        abort(403)
    return task


@teacher_bp.route("/")
def dashboard():
    courses = Course.query.filter_by(teacher_id=current_user.id).order_by(Course.created_at.desc()).all()
    return render_template("teacher/dashboard.html", courses=courses)


# --- Курсы -------------------------------------------------------------

@teacher_bp.route("/courses/new", methods=["GET", "POST"])
def new_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            title=form.title.data.strip(),
            description=form.description.data or "",
            is_published=form.is_published.data,
            teacher_id=current_user.id,
        )
        db.session.add(course)
        db.session.commit()
        flash("Курс создан.", "success")
        return redirect(url_for("teacher.course_detail", course_id=course.id))
    return render_template("teacher/course_form.html", form=form, title="Новый курс")


@teacher_bp.route("/courses/<int:course_id>")
def course_detail(course_id):
    course = _get_owned_course(course_id)
    return render_template("teacher/course_detail.html", course=course)


@teacher_bp.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
def edit_course(course_id):
    course = _get_owned_course(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.title = form.title.data.strip()
        course.description = form.description.data or ""
        course.is_published = form.is_published.data
        db.session.commit()
        flash("Курс обновлён.", "success")
        return redirect(url_for("teacher.course_detail", course_id=course.id))
    return render_template("teacher/course_form.html", form=form, title="Редактировать курс")


@teacher_bp.route("/courses/<int:course_id>/delete", methods=["POST"])
def delete_course(course_id):
    course = _get_owned_course(course_id)
    db.session.delete(course)
    db.session.commit()
    flash("Курс удалён.", "info")
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/courses/<int:course_id>/students")
def course_students(course_id):
    course = _get_owned_course(course_id)
    total_tasks = course.task_count()

    rows = []
    for enrollment in course.enrollments:
        student = enrollment.student
        solved = sum(
            1
            for submission in student.submissions
            if submission.is_correct and submission.task.lesson.course_id == course.id
        )
        progress = int((solved / total_tasks) * 100) if total_tasks else 0
        rows.append({"student": student, "progress": progress, "solved": solved, "total": total_tasks})

    return render_template("teacher/course_students.html", course=course, rows=rows)


# --- Уроки ---------------------------------------------------------------

@teacher_bp.route("/courses/<int:course_id>/lessons/new", methods=["GET", "POST"])
def new_lesson(course_id):
    course = _get_owned_course(course_id)
    form = LessonForm()
    if form.validate_on_submit():
        lesson = Lesson(
            course_id=course.id,
            title=form.title.data.strip(),
            content=form.content.data or "",
            order_index=form.order_index.data or 0,
        )
        db.session.add(lesson)
        db.session.commit()
        flash("Урок добавлен.", "success")
        return redirect(url_for("teacher.course_detail", course_id=course.id))
    return render_template("teacher/lesson_form.html", form=form, course=course, title="Новый урок")


@teacher_bp.route("/lessons/<int:lesson_id>")
def lesson_detail(lesson_id):
    lesson = _get_owned_lesson(lesson_id)
    return render_template("teacher/lesson_detail.html", lesson=lesson)


@teacher_bp.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
def edit_lesson(lesson_id):
    lesson = _get_owned_lesson(lesson_id)
    form = LessonForm(obj=lesson)
    if form.validate_on_submit():
        lesson.title = form.title.data.strip()
        lesson.content = form.content.data or ""
        lesson.order_index = form.order_index.data or 0
        db.session.commit()
        flash("Урок обновлён.", "success")
        return redirect(url_for("teacher.lesson_detail", lesson_id=lesson.id))
    return render_template("teacher/lesson_form.html", form=form, course=lesson.course, title="Редактировать урок")


@teacher_bp.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
def delete_lesson(lesson_id):
    lesson = _get_owned_lesson(lesson_id)
    course_id = lesson.course_id
    db.session.delete(lesson)
    db.session.commit()
    flash("Урок удалён.", "info")
    return redirect(url_for("teacher.course_detail", course_id=course_id))


# --- Задания ---------------------------------------------------------------

@teacher_bp.route("/lessons/<int:lesson_id>/tasks/new", methods=["GET", "POST"])
def new_task(lesson_id):
    lesson = _get_owned_lesson(lesson_id)
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            lesson_id=lesson.id,
            title=form.title.data.strip(),
            description=form.description.data or "",
            type=form.type.data,
            order_index=form.order_index.data or 0,
            max_score=form.max_score.data or 10,
        )
        db.session.add(task)
        db.session.commit()
        flash("Задание создано. Теперь добавьте вопросы или тест-кейсы.", "success")
        return redirect(url_for("teacher.task_detail", task_id=task.id))
    return render_template("teacher/task_form.html", form=form, lesson=lesson, title="Новое задание")


@teacher_bp.route("/tasks/<int:task_id>")
def task_detail(task_id):
    task = _get_owned_task(task_id)
    if task.type == TaskType.QUIZ:
        form = QuizQuestionForm()
        return render_template("teacher/task_quiz_detail.html", task=task, form=form)
    form = CodeTestCaseForm()
    return render_template("teacher/task_code_detail.html", task=task, form=form)


@teacher_bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    task = _get_owned_task(task_id)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = form.title.data.strip()
        task.description = form.description.data or ""
        task.type = form.type.data
        task.order_index = form.order_index.data or 0
        task.max_score = form.max_score.data or 10
        db.session.commit()
        flash("Задание обновлено.", "success")
        return redirect(url_for("teacher.task_detail", task_id=task.id))
    return render_template("teacher/task_form.html", form=form, lesson=task.lesson, title="Редактировать задание")


@teacher_bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    task = _get_owned_task(task_id)
    lesson_id = task.lesson_id
    db.session.delete(task)
    db.session.commit()
    flash("Задание удалено.", "info")
    return redirect(url_for("teacher.lesson_detail", lesson_id=lesson_id))


# --- Вопросы теста -----------------------------------------------------

@teacher_bp.route("/tasks/<int:task_id>/questions/add", methods=["POST"])
def add_question(task_id):
    task = _get_owned_task(task_id)
    if task.type != TaskType.QUIZ:
        abort(400)

    form = QuizQuestionForm()
    if form.validate_on_submit():
        question = QuizQuestion(task_id=task.id, text=form.text.data.strip(), order_index=len(task.questions))
        db.session.add(question)
        db.session.flush()

        for text, key in (
            (form.choice1.data, "1"),
            (form.choice2.data, "2"),
            (form.choice3.data, "3"),
            (form.choice4.data, "4"),
        ):
            if text and text.strip():
                db.session.add(
                    QuizChoice(question_id=question.id, text=text.strip(), is_correct=(key == form.correct_choice.data))
                )
        db.session.commit()
        flash("Вопрос добавлен.", "success")
    else:
        flash("Проверьте правильность заполнения вопроса (обязательны текст и минимум 2 варианта).", "danger")
    return redirect(url_for("teacher.task_detail", task_id=task.id))


@teacher_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
def delete_question(question_id):
    question = QuizQuestion.query.get_or_404(question_id)
    task = _get_owned_task(question.task_id)
    db.session.delete(question)
    db.session.commit()
    flash("Вопрос удалён.", "info")
    return redirect(url_for("teacher.task_detail", task_id=task.id))


# --- Тест-кейсы для заданий по коду --------------------------------------

@teacher_bp.route("/tasks/<int:task_id>/testcases/add", methods=["POST"])
def add_testcase(task_id):
    task = _get_owned_task(task_id)
    if task.type != TaskType.CODE:
        abort(400)

    form = CodeTestCaseForm()
    if form.validate_on_submit():
        db.session.add(
            CodeTestCase(
                task_id=task.id,
                stdin_data=form.stdin_data.data or "",
                expected_output=form.expected_output.data.strip(),
                is_sample=form.is_sample.data,
            )
        )
        db.session.commit()
        flash("Тест-кейс добавлен.", "success")
    else:
        flash("Укажите ожидаемый вывод для тест-кейса.", "danger")
    return redirect(url_for("teacher.task_detail", task_id=task.id))


@teacher_bp.route("/testcases/<int:testcase_id>/delete", methods=["POST"])
def delete_testcase(testcase_id):
    testcase = CodeTestCase.query.get_or_404(testcase_id)
    task = _get_owned_task(testcase.task_id)
    db.session.delete(testcase)
    db.session.commit()
    flash("Тест-кейс удалён.", "info")
    return redirect(url_for("teacher.task_detail", task_id=task.id))


# --- Просмотр решений учеников -------------------------------------------

@teacher_bp.route("/tasks/<int:task_id>/submissions")
def task_submissions(task_id):
    task = _get_owned_task(task_id)
    submissions = Submission.query.filter_by(task_id=task.id).order_by(Submission.submitted_at.desc()).all()
    return render_template("teacher/task_submissions.html", task=task, submissions=submissions)


@teacher_bp.route("/submissions/<int:submission_id>")
def submission_detail(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    task = _get_owned_task(submission.task_id)
    return render_template("teacher/submission_detail.html", submission=submission, task=task)
