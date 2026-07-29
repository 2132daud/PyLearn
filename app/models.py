"""Модели базы данных учебной платформы PyLearn."""

import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class UserRole:
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

    ALL = (ADMIN, TEACHER, STUDENT)
    CHOICES = (
        (STUDENT, "Ученик"),
        (TEACHER, "Учитель"),
        (ADMIN, "Админ"),
    )


class TaskType:
    QUIZ = "quiz"
    CODE = "code"

    ALL = (QUIZ, CODE)
    CHOICES = (
        (QUIZ, "Тест (вопросы с вариантами ответов)"),
        (CODE, "Код (проверка по тест-кейсам)"),
    )


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.STUDENT)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses_taught = db.relationship("Course", back_populates="teacher")
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="student", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):  # используется Flask-Login вместо стандартного True
        return self.is_active_account

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def is_teacher(self):
        return self.role == UserRole.TEACHER

    def is_student(self):
        return self.role == UserRole.STUDENT

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("User", back_populates="courses_taught")
    lessons = db.relationship(
        "Lesson", back_populates="course", order_by="Lesson.order_index", cascade="all, delete-orphan"
    )
    enrollments = db.relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

    def lesson_count(self):
        return len(self.lessons)

    def task_count(self):
        return sum(len(lesson.tasks) for lesson in self.lessons)

    def student_count(self):
        return len(self.enrollments)

    def __repr__(self):
        return f"<Course {self.title!r}>"


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")


class Lesson(db.Model):
    __tablename__ = "lessons"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, default="")  # поддерживается markdown
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="lessons")
    tasks = db.relationship(
        "Task", back_populates="lesson", order_by="Task.order_index", cascade="all, delete-orphan"
    )


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lessons.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False, default=TaskType.QUIZ)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    order_index = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=10)

    lesson = db.relationship("Lesson", back_populates="tasks")
    questions = db.relationship(
        "QuizQuestion", back_populates="task", order_by="QuizQuestion.order_index", cascade="all, delete-orphan"
    )
    test_cases = db.relationship("CodeTestCase", back_populates="task", cascade="all, delete-orphan")
    submissions = db.relationship("Submission", back_populates="task", cascade="all, delete-orphan")


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    text = db.Column(db.Text, nullable=False)
    order_index = db.Column(db.Integer, default=0)

    task = db.relationship("Task", back_populates="questions")
    choices = db.relationship(
        "QuizChoice", back_populates="question", order_by="QuizChoice.id", cascade="all, delete-orphan"
    )


class QuizChoice(db.Model):
    __tablename__ = "quiz_choices"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_questions.id"), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    question = db.relationship("QuizQuestion", back_populates="choices")


class CodeTestCase(db.Model):
    __tablename__ = "code_test_cases"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    stdin_data = db.Column(db.Text, default="")
    expected_output = db.Column(db.Text, default="")
    is_sample = db.Column(db.Boolean, default=False)  # видим ли ученику как пример

    task = db.relationship("Task", back_populates="test_cases")


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_correct = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    code_text = db.Column(db.Text, nullable=True)  # для заданий типа "код"
    answers_json = db.Column(db.Text, nullable=True)  # для тестов: {question_id: choice_id}
    feedback = db.Column(db.Text, nullable=True)  # текст/JSON с результатами проверки

    task = db.relationship("Task", back_populates="submissions")
    student = db.relationship("User", back_populates="submissions")

    def answers(self):
        return json.loads(self.answers_json) if self.answers_json else {}
