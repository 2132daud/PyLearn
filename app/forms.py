"""WTForms-формы приложения."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

from app.models import TaskType, UserRole


class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class RegisterForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField(
        "Повторите пароль", validators=[DataRequired(), EqualTo("password", message="Пароли не совпадают.")]
    )
    submit = SubmitField("Зарегистрироваться")


class CreateTeacherForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Создать учителя")


class UserEditForm(FlaskForm):
    role = SelectField("Роль", choices=UserRole.CHOICES)
    is_active_account = BooleanField("Учётная запись активна")
    submit = SubmitField("Сохранить")


class CourseForm(FlaskForm):
    title = StringField("Название курса", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Описание", validators=[Optional()])
    is_published = BooleanField("Опубликован (виден ученикам)", default=True)
    submit = SubmitField("Сохранить")


class LessonForm(FlaskForm):
    title = StringField("Название урока", validators=[DataRequired(), Length(max=150)])
    content = TextAreaField("Содержание урока (поддерживается Markdown)", validators=[Optional()])
    order_index = IntegerField("Порядковый номер", validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField("Сохранить")


class TaskForm(FlaskForm):
    title = StringField("Название задания", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Описание/условие задания", validators=[Optional()])
    type = SelectField("Тип задания", choices=TaskType.CHOICES)
    order_index = IntegerField("Порядковый номер", validators=[Optional(), NumberRange(min=0)], default=0)
    max_score = IntegerField("Максимальный балл", validators=[Optional(), NumberRange(min=1)], default=10)
    submit = SubmitField("Сохранить")


class QuizQuestionForm(FlaskForm):
    text = TextAreaField("Текст вопроса", validators=[DataRequired()])
    choice1 = StringField("Вариант 1", validators=[DataRequired()])
    choice2 = StringField("Вариант 2", validators=[DataRequired()])
    choice3 = StringField("Вариант 3", validators=[Optional()])
    choice4 = StringField("Вариант 4", validators=[Optional()])
    correct_choice = SelectField(
        "Правильный вариант",
        choices=[("1", "Вариант 1"), ("2", "Вариант 2"), ("3", "Вариант 3"), ("4", "Вариант 4")],
    )
    submit = SubmitField("Добавить вопрос")


class CodeTestCaseForm(FlaskForm):
    stdin_data = TextAreaField("Входные данные (stdin), необязательно", validators=[Optional()])
    expected_output = TextAreaField("Ожидаемый вывод (stdout)", validators=[DataRequired()])
    is_sample = BooleanField("Показывать ученику как пример")
    submit = SubmitField("Добавить тест-кейс")


class CodeSubmitForm(FlaskForm):
    code_text = TextAreaField("Ваш код на Python", validators=[DataRequired()])
    submit = SubmitField("Отправить решение")
