"""
Модуль для логирования событий
"""
import time
from datetime import datetime
from typing import List, Callable
from config import LOG_CONFIG


class Logger:
    """Класс для управления логами"""

    def __init__(self, max_lines: int = LOG_CONFIG["max_lines"]):
        self.logs: List[str] = []
        self.max_lines = max_lines
        self.callbacks: List[Callable] = []

    def add_callback(self, callback: Callable):
        """
        Добавляет callback функцию для обновления UI при новом логе

        Args:
            callback: Функция, принимающая строку лога
        """
        self.callbacks.append(callback)

    def info(self, message: str):
        """Добавляет информационное сообщение"""
        self._add_log("INFO", message)

    def error(self, message: str):
        """Добавляет сообщение об ошибке"""
        self._add_log("ERROR", message)

    def success(self, message: str):
        """Добавляет сообщение об успехе"""
        self._add_log("SUCCESS", message)

    def warning(self, message: str):
        """Добавляет предупреждение"""
        self._add_log("WARNING", message)

    def _add_log(self, level: str, message: str):
        """
        Внутренний метод добавления лога

        Args:
            level: Уровень логирования
            message: Сообщение
        """
        timestamp = datetime.now().strftime(LOG_CONFIG["timestamp_format"])
        log_entry = f"[{timestamp}] [{level}] {message}"

        self.logs.append(log_entry)

        # Ограничиваем количество строк
        if len(self.logs) > self.max_lines:
            self.logs.pop(0)

        # Вызываем все callback функции
        for callback in self.callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                print(f"Error in logger callback: {e}")

    def get_logs(self) -> List[str]:
        """Возвращает все логи"""
        return self.logs.copy()

    def clear(self):
        """Очищает логи"""
        self.logs.clear()