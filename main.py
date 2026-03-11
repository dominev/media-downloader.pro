#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Media Downloader Pro
Главный файл запуска приложения
"""

import sys
import os
import subprocess
import threading
from pathlib import Path

# Добавляем путь к проекту в sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Проверка зависимостей
def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    required_packages = [
        'customtkinter',
        'yt_dlp',
        'instagrapi',
        'telethon',
        'cryptography',
        'PIL',
        'requests'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Отсутствуют необходимые зависимости:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nУстановите их командой:")
        print("   pip install -r requirements.txt")
        return False

    return True


def check_system_ffmpeg():
    """
    Проверяет наличие FFmpeg в системе

    Returns:
        bool: True если FFmpeg доступен
    """
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                                capture_output=True,
                                text=True,
                                timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg найден в системе")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Проверяем в локальной папке проекта
    if os.name == 'nt':
        local_ffmpeg = project_root / "ffmpeg" / "bin" / "ffmpeg.exe"
    else:
        local_ffmpeg = project_root / "ffmpeg" / "ffmpeg"

    if local_ffmpeg.exists():
        try:
            result = subprocess.run([str(local_ffmpeg), '-version'],
                                    capture_output=True,
                                    text=True,
                                    timeout=5)
            if result.returncode == 0:
                print(f"✅ FFmpeg найден локально: {local_ffmpeg}")
                return True
        except (subprocess.TimeoutExpired, Exception):
            pass

    return False


def download_ffmpeg_background():
    """Скачивает FFmpeg в фоновом режиме"""
    try:
        from utils.ffmpeg_manager import FFmpegManager
        import time

        print("📥 FFmpeg не найден. Начинаю автоматическое скачивание в фоне...")

        # Создаем менеджер без GUI
        class DummyLogger:
            def info(self, msg): print(f"ℹ️ {msg}")

            def error(self, msg): print(f"❌ {msg}")

            def success(self, msg): print(f"✅ {msg}")

            def warning(self, msg): print(f"⚠️ {msg}")

        manager = FFmpegManager(DummyLogger())

        # Функция для отображения прогресса в консоли
        def progress_callback(value):
            if value % 10 == 0:  # Показываем каждые 10%
                print(f"   Прогресс: {value}%")

        # Скачиваем
        success = manager.download_ffmpeg(progress_callback)

        if success:
            print("✅ FFmpeg успешно установлен в фоновом режиме!")
        else:
            print("⚠️ Не удалось автоматически скачать FFmpeg. Некоторые функции могут быть недоступны.")

    except Exception as e:
        print(f"⚠️ Ошибка при фоновом скачивании FFmpeg: {e}")
        print("   Продолжаем запуск без FFmpeg")


def main():
    """Главная функция запуска"""

    print("""
    ╔══════════════════════════════════════════╗
    ║     Media Downloader Pro v1.0.0          ║
    ║     Загрузка видео с популярных сайтов   ║
    ╚══════════════════════════════════════════╝
    """)

    # Проверяем зависимости
    if not check_dependencies():
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

    # Проверяем FFmpeg
    has_ffmpeg = check_system_ffmpeg()

    # Если FFmpeg не найден, запускаем фоновое скачивание
    if not has_ffmpeg:
        print("⚠️ FFmpeg не найден. Будет скачан автоматически в фоновом режиме.")
        print("   Программа продолжит работу, а FFmpeg установится параллельно.")

        # Запускаем скачивание в отдельном потоке
        ffmpeg_thread = threading.Thread(target=download_ffmpeg_background, daemon=True)
        ffmpeg_thread.start()
    else:
        print("✅ FFmpeg уже установлен")

    # Создаём необходимые директории
    from config import DEFAULT_DOWNLOAD_DIR
    DEFAULT_DOWNLOAD_DIR.mkdir(exist_ok=True)

    # Запускаем приложение
    try:
        from gui.app import DownloaderApp

        app = DownloaderApp(has_ffmpeg=has_ffmpeg)
        print("✅ Приложение запущено")
        app.mainloop()

    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()