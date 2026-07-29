"""Команды `flask ...` для инициализации БД и наполнения демо-данными."""

import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import (
    CodeTestCase,
    Course,
    Lesson,
    QuizChoice,
    QuizQuestion,
    Task,
    TaskType,
    User,
    UserRole,
)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Создаёт все таблицы базы данных (если их ещё нет)."""
    db.create_all()
    click.echo("База данных инициализирована.")


@click.command("create-admin")
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@with_appcontext
def create_admin_command(username, email, password):
    """Создаёт учётную запись администратора."""
    db.create_all()
    if User.query.filter_by(username=username).first():
        click.echo("Пользователь с таким именем уже существует.")
        return
    admin = User(username=username, email=email.lower(), role=UserRole.ADMIN)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Администратор «{username}» создан.")


@click.command("seed-demo")
@with_appcontext
def seed_demo_command():
    """Заполняет базу демонстрационными данными: учитель, курс, уроки, задания."""
    db.create_all()

    if Course.query.first():
        click.echo("Демо-данные уже существуют, пропускаем.")
        return

    teacher = User.query.filter_by(username="teacher_demo").first()
    if not teacher:
        teacher = User(username="teacher_demo", email="teacher_demo@example.com", role=UserRole.TEACHER)
        teacher.set_password("teacher123")
        db.session.add(teacher)
        db.session.flush()

    course = Course(
        title="Python для начинающих",
        description="Базовый курс по основам языка Python: переменные, ввод/вывод, циклы.",
        teacher_id=teacher.id,
    )
    db.session.add(course)
    db.session.flush()

    lesson1 = Lesson(
        course_id=course.id,
        title="Переменные и типы данных",
        order_index=0,
        content=(
            "# Переменные в Python\n\n"
            "В Python переменную можно создать простым присваиванием:\n\n"
            "```python\nx = 5\nname = \"Иван\"\n```\n\n"
            "Python — язык с динамической типизацией: тип переменной "
            "определяется автоматически, исходя из присвоенного значения."
        ),
    )
    db.session.add(lesson1)
    db.session.flush()

    quiz_task = Task(
        lesson_id=lesson1.id,
        type=TaskType.QUIZ,
        title="Проверь себя: переменные",
        description="Выберите правильный ответ.",
        order_index=0,
        max_score=10,
    )
    db.session.add(quiz_task)
    db.session.flush()

    question = QuizQuestion(task_id=quiz_task.id, text="Как объявить переменную x со значением 10?", order_index=0)
    db.session.add(question)
    db.session.flush()
    db.session.add_all(
        [
            QuizChoice(question_id=question.id, text="x = 10", is_correct=True),
            QuizChoice(question_id=question.id, text="int x = 10", is_correct=False),
            QuizChoice(question_id=question.id, text="var x = 10", is_correct=False),
            QuizChoice(question_id=question.id, text="x := 10", is_correct=False),
        ]
    )

    lesson2 = Lesson(
        course_id=course.id,
        title="Ввод и вывод данных",
        order_index=1,
        content=(
            "# Функции input() и print()\n\n"
            "Считать данные с клавиатуры можно функцией `input()`, "
            "а вывести результат на экран — функцией `print()`.\n\n"
            "```python\nname = input()\nprint(\"Привет,\", name)\n```"
        ),
    )
    db.session.add(lesson2)
    db.session.flush()

    code_task = Task(
        lesson_id=lesson2.id,
        type=TaskType.CODE,
        title="Приветствие по имени",
        description=(
            "Считайте имя пользователя с помощью input() и выведите строку\n"
            "«Привет, <имя>!» (без кавычек, восклицательный знак после имени)."
        ),
        order_index=0,
        max_score=10,
    )
    db.session.add(code_task)
    db.session.flush()

    db.session.add_all(
        [
            CodeTestCase(task_id=code_task.id, stdin_data="Мария", expected_output="Привет, Мария!", is_sample=True),
            CodeTestCase(task_id=code_task.id, stdin_data="Пётр", expected_output="Привет, Пётр!", is_sample=False),
        ]
    )

    # --- Урок 3: условные операторы -------------------------------------

    lesson3 = Lesson(
        course_id=course.id,
        title="Условные операторы if / elif / else",
        order_index=2,
        content=(
            "# Условные операторы\n\n"
            "Конструкция `if / elif / else` позволяет выполнять разный код "
            "в зависимости от условия:\n\n"
            "```python\nage = int(input())\n"
            "if age >= 18:\n"
            "    print(\"Взрослый\")\n"
            "elif age >= 13:\n"
            "    print(\"Подросток\")\n"
            "else:\n"
            "    print(\"Ребёнок\")\n```\n\n"
            "Условием может быть любое выражение, дающее `True` или `False` "
            "(например, `x > 10`, `x == 5`, `name != \"\"`)."
        ),
    )
    db.session.add(lesson3)
    db.session.flush()

    quiz_task2 = Task(
        lesson_id=lesson3.id,
        type=TaskType.QUIZ,
        title="Проверь себя: условия",
        description="Определите, что выведет программа.",
        order_index=0,
        max_score=10,
    )
    db.session.add(quiz_task2)
    db.session.flush()

    question2 = QuizQuestion(
        task_id=quiz_task2.id,
        text=(
            "Что выведет код?\n"
            "x = 5\n"
            "if x > 10:\n"
            "    print(\"A\")\n"
            "elif x > 3:\n"
            "    print(\"B\")\n"
            "else:\n"
            "    print(\"C\")"
        ),
        order_index=0,
    )
    db.session.add(question2)
    db.session.flush()
    db.session.add_all(
        [
            QuizChoice(question_id=question2.id, text="A", is_correct=False),
            QuizChoice(question_id=question2.id, text="B", is_correct=True),
            QuizChoice(question_id=question2.id, text="C", is_correct=False),
            QuizChoice(question_id=question2.id, text="Программа выдаст ошибку", is_correct=False),
        ]
    )

    # --- Урок 4: циклы ---------------------------------------------------

    lesson4 = Lesson(
        course_id=course.id,
        title="Циклы for и while",
        order_index=3,
        content=(
            "# Циклы\n\n"
            "Цикл `for` используется для перебора последовательности:\n\n"
            "```python\nfor i in range(5):\n    print(i)\n```\n\n"
            "Цикл `while` выполняется, пока условие истинно:\n\n"
            "```python\nn = 0\nwhile n < 5:\n    print(n)\n    n += 1\n```"
        ),
    )
    db.session.add(lesson4)
    db.session.flush()

    code_task2 = Task(
        lesson_id=lesson4.id,
        type=TaskType.CODE,
        title="Сумма чисел от 1 до N",
        description=(
            "Считайте с клавиатуры целое число N (input()) и выведите сумму "
            "всех целых чисел от 1 до N включительно."
        ),
        order_index=0,
        max_score=10,
    )
    db.session.add(code_task2)
    db.session.flush()

    db.session.add_all(
        [
            CodeTestCase(task_id=code_task2.id, stdin_data="5", expected_output="15", is_sample=True),
            CodeTestCase(task_id=code_task2.id, stdin_data="1", expected_output="1", is_sample=False),
            CodeTestCase(task_id=code_task2.id, stdin_data="10", expected_output="55", is_sample=False),
        ]
    )

    # --- Урок 5: списки и функции -----------------------------------------

    lesson5 = Lesson(
        course_id=course.id,
        title="Списки и функции",
        order_index=4,
        content=(
            "# Списки и функции\n\n"
            "Список — упорядоченная коллекция элементов:\n\n"
            "```python\nnumbers = [1, 2, 3]\nnumbers.append(4)\nprint(numbers[0])\n```\n\n"
            "Функция оформляется ключевым словом `def`:\n\n"
            "```python\ndef square(x):\n    return x * x\n\nprint(square(5))\n```"
        ),
    )
    db.session.add(lesson5)
    db.session.flush()

    quiz_task3 = Task(
        lesson_id=lesson5.id,
        type=TaskType.QUIZ,
        title="Проверь себя: списки",
        description="Выберите правильный ответ.",
        order_index=0,
        max_score=10,
    )
    db.session.add(quiz_task3)
    db.session.flush()

    question3 = QuizQuestion(
        task_id=quiz_task3.id, text="Как обратиться к первому элементу списка numbers?", order_index=0
    )
    db.session.add(question3)
    db.session.flush()
    db.session.add_all(
        [
            QuizChoice(question_id=question3.id, text="numbers[0]", is_correct=True),
            QuizChoice(question_id=question3.id, text="numbers[1]", is_correct=False),
            QuizChoice(question_id=question3.id, text="numbers.first()", is_correct=False),
            QuizChoice(question_id=question3.id, text="numbers{0}", is_correct=False),
        ]
    )

    code_task3 = Task(
        lesson_id=lesson5.id,
        type=TaskType.CODE,
        title="Максимум в списке",
        description=(
            "Считайте одну строку с числами через пробел (input().split()) "
            "и выведите наибольшее из них."
        ),
        order_index=1,
        max_score=10,
    )
    db.session.add(code_task3)
    db.session.flush()

    db.session.add_all(
        [
            CodeTestCase(task_id=code_task3.id, stdin_data="3 7 2", expected_output="7", is_sample=True),
            CodeTestCase(task_id=code_task3.id, stdin_data="10 -5 8 9", expected_output="10", is_sample=False),
            CodeTestCase(task_id=code_task3.id, stdin_data="1", expected_output="1", is_sample=False),
        ]
    )

    db.session.commit()
    click.echo(
        "Демо-данные добавлены: 5 уроков в курсе «Python для начинающих». "
        "Учитель: teacher_demo / teacher123"
    )
