"""
Модуль для работы с файлами и папками
"""
import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime


class FileHandler:
    """Класс для управления файлами"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Очищает имя файла от недопустимых символов

        Args:
            filename: Исходное имя файла

        Returns:
            str: Безопасное имя файла
        """
        # Заменяем недопустимые символы на подчеркивание
        invalid_chars = r'[<>:"/\\|?*]'
        safe_name = re.sub(invalid_chars, '_', filename)

        # Ограничиваем длину имени
        if len(safe_name) > 200:
            name, ext = os.path.splitext(safe_name)
            safe_name = name[:195] + ext

        return safe_name

    @staticmethod
    def get_unique_filename(directory: Path, filename: str) -> Path:
        """
        Возвращает уникальное имя файла, если файл уже существует

        Args:
            directory: Директория для сохранения
            filename: Желаемое имя файла

        Returns:
            Path: Путь к уникальному файлу
        """
        filepath = directory / filename

        if not filepath.exists():
            return filepath

        # Если файл существует, добавляем номер
        base, ext = os.path.splitext(filename)
        counter = 1

        while True:
            new_filename = f"{base}_{counter}{ext}"
            new_filepath = directory / new_filename
            if not new_filepath.exists():
                return new_filepath
            counter += 1

    @staticmethod
    def ensure_directory(directory: Path) -> Path:
        """
        Создает директорию, если её нет

        Args:
            directory: Путь к директории

        Returns:
            Path: Путь к директории
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def create_dated_subdirectory(base_dir: Path, platform: str) -> Path:
        """
        Создает поддиректорию с датой для платформы

        Args:
            base_dir: Базовая директория
            platform: Название платформы

        Returns:
            Path: Путь к созданной директории
        """
        date_str = datetime.now().strftime("%Y-%m-%d")
        subdir = base_dir / platform / date_str
        return FileHandler.ensure_directory(subdir)

    @staticmethod
    def get_file_size(filepath: Path) -> str:
        """
        Возвращает размер файла в человекочитаемом формате

        Args:
            filepath: Путь к файлу

        Returns:
            str: Размер файла (например, "15.2 MB")
        """
        size = filepath.stat().st_size

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0

        return f"{size:.1f} TB"