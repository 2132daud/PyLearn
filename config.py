import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Базовая конфигурация приложения.

    Настройки минимальны и достаточны для учебного проекта: используется
    SQLite (файл в папке instance/) и секретный ключ, который в реальном
    развёртывании нужно задавать через переменную окружения SECRET_KEY.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "app.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Ограничения для запуска пользовательского Python-кода из заданий.
    CODE_EXECUTION_TIMEOUT = int(os.environ.get("CODE_EXECUTION_TIMEOUT", "5"))  # секунд
    MAX_CODE_LENGTH = int(os.environ.get("MAX_CODE_LENGTH", "20000"))  # символов
