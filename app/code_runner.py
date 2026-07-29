"""Запуск пользовательского Python-кода для проверки практических заданий.

ВАЖНО: изоляция здесь базовая (отдельный процесс, ограничение по времени,
изолированный режим интерпретатора `-I`). Этого достаточно для закрытого
учебного окружения (студенты доверенные, доступ не публичный), но это
НЕ полноценная песочница для выполнения произвольного кода из открытого
интернета. Для промышленного использования потребовался бы Docker/gVisor
и т.п. — сознательно опущено, так как выходит за рамки учебного задания.
"""

import os
import subprocess
import sys
import tempfile


class CodeRunResult:
    def __init__(self, success, stdout, stderr, timed_out=False):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.timed_out = timed_out


def run_python_code(code, stdin_data="", timeout=5):
    """Выполняет код в отдельном процессе и возвращает результат."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp_file:
            tmp_file.write(code)
            tmp_path = tmp_file.name

        proc = subprocess.run(
            [sys.executable, "-I", tmp_path],
            input=stdin_data or "",
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CodeRunResult(success=(proc.returncode == 0), stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired:
        return CodeRunResult(
            success=False, stdout="", stderr="Превышено время выполнения (timeout).", timed_out=True
        )
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def check_task_solution(code, test_cases, timeout=5):
    """Прогоняет код по списку тест-кейсов (CodeTestCase).

    Возвращает (passed, total, details) — количество пройденных тестов,
    общее число тестов и подробности по каждому из них.
    """
    details = []
    passed = 0
    for case in test_cases:
        result = run_python_code(code, stdin_data=case.stdin_data or "", timeout=timeout)
        actual = (result.stdout or "").strip()
        expected = (case.expected_output or "").strip()
        ok = result.success and actual == expected
        if ok:
            passed += 1
        details.append(
            {
                "input": case.stdin_data or "",
                "expected": expected,
                "actual": actual,
                "stderr": result.stderr or "",
                "passed": ok,
                "is_sample": case.is_sample,
            }
        )
    return passed, len(test_cases), details
