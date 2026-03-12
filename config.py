import os
from pathlib import Path

# Базовая директория проекта
BASE_DIR = Path(__file__).parent

# Директория для загрузок по умолчанию
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "downloads"

APP_NAME = "Media Downloader Pro"
APP_VERSION = "1.0.0"
APP_GEOMETRY = "900x700"  # Ширина x Высота

# Настройки темы
THEME = {
    "appearance_mode": "dark",  # dark / light / system
    "color_theme": "green",      # blue / green / dark-blue
}

# Настройки загрузчиков
DOWNLOADERS_CONFIG = {
    "max_concurrent_downloads": 3,  # Максимум одновременных загрузок
    "timeout": 30,                   # Таймаут соединения в секундах
    "retries": 3,                     # Количество попыток при ошибке
}

# Настройки для Telegram
TELEGRAM_CONFIG = {
    "api_id": None,  # Заполнить вручную в файле .env или через интерфейс
    "api_hash": None,
    "session_name": "telegram_session",
}

# Настройки логирования
LOG_CONFIG = {
    "max_lines": 1000,  # Максимальное количество строк в логе
    "timestamp_format": "%H:%M:%S",
}

# Поддерживаемые платформы
PLATFORMS = {
    "youtube": ["youtube.com", "youtu.be", "m.youtube.com"],
    "vk": ["vk.com", "vkontakte.ru"],
    "telegram": ["t.me", "telegram.me"],
    "instagram": ["instagram.com", "instagr.am"],
}

# Создаем директорию для загрузок, если её нет
DEFAULT_DOWNLOAD_DIR.mkdir(exist_ok=True)
