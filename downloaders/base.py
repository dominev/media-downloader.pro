"""
Базовый класс для всех загрузчиков
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
import threading
from utils.logger import Logger


class BaseDownloader(ABC):
    """Абстрактный базовый класс для загрузчиков"""

    def __init__(self, logger: Logger):
        """
        Инициализация базового загрузчика

        Args:
            logger: Экземпляр логгера
        """
        self.logger = logger
        self._stop_flag = False
        self._lock = threading.Lock()
        self._progress = 0
        self._status = "idle"

    @abstractmethod
    def download(self, url: str, download_dir: Path, **kwargs) -> Optional[Path]:
        """
        Основной метод загрузки (должен быть переопределен)

        Args:
            url: Ссылка на контент
            download_dir: Директория для сохранения
            **kwargs: Дополнительные параметры

        Returns:
            Optional[Path]: Путь к скачанному файлу или None
        """
        pass

    @abstractmethod
    def is_supported(self, url: str) -> bool:
        """
        Проверяет, поддерживается ли URL этим загрузчиком

        Args:
            url: Ссылка для проверки

        Returns:
            bool: True если поддерживается
        """
        pass

    def stop(self):
        """Останавливает загрузку"""
        with self._lock:
            self._stop_flag = True
            self._status = "stopped"
        self.logger.warning("Загрузка остановлена пользователем")

    def reset_stop_flag(self):
        """Сбрасывает флаг остановки"""
        with self._lock:
            self._stop_flag = False

    def is_stopped(self) -> bool:
        """Проверяет, была ли остановлена загрузка"""
        with self._lock:
            return self._stop_flag

    def update_progress(self, progress: int):
        """Обновляет прогресс загрузки"""
        with self._lock:
            self._progress = progress

    def get_progress(self) -> int:
        """Возвращает текущий прогресс"""
        with self._lock:
            return self._progress

    def set_status(self, status: str):
        """Устанавливает статус загрузки"""
        with self._lock:
            self._status = status

    def get_status(self) -> str:
        """Возвращает текущий статус"""
        with self._lock:
            return self._status

    def handle_error(self, error: Exception, context: str = ""):
        """
        Обрабатывает ошибку загрузки

        Args:
            error: Исключение
            context: Контекст ошибки
        """
        error_msg = f"Ошибка {context}: {str(error)}"
        self.logger.error(error_msg)
        self.set_status("error")