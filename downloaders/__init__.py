"""
Инициализация модуля загрузчиков
"""
from .youtube import YouTubeDownloader
from .vk import VKDownloader
from .telegram import TelegramDownloader
from .instagram import InstagramDownloader

__all__ = [
    'YouTubeDownloader',
    'VKDownloader',
    'TelegramDownloader',
    'InstagramDownloader'
]