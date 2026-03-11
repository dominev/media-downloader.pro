"""
Модуль для определения платформы по URL
"""
import re
from config import PLATFORMS


class PlatformDetector:
    """Класс для определения источника контента по ссылке"""

    @staticmethod
    def detect_platform(url: str) -> str:
        """
        Определяет платформу по URL

        Args:
            url: Ссылка на контент

        Returns:
            str: Название платформы (youtube, vk, telegram, instagram) или "unknown"
        """
        url_lower = url.lower()

        for platform, domains in PLATFORMS.items():
            for domain in domains:
                if domain in url_lower:
                    return platform

        # Дополнительная проверка для YouTube Shorts
        if "youtube.com/shorts" in url_lower:
            return "youtube"

        return "unknown"

    @staticmethod
    def extract_video_id(url: str, platform: str) -> str:
        """
        Извлекает ID видео из URL

        Args:
            url: Ссылка на контент
            platform: Платформа

        Returns:
            str: ID видео или пустая строка
        """
        if platform == "youtube":
            # Паттерны для YouTube ID
            patterns = [
                r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})",
                r"(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)

        elif platform == "vk":
            # Паттерн для VK видео
            match = re.search(r"video(-?\d+_\d+)", url)
            if match:
                return match.group(1)

        elif platform == "instagram":
            # Паттерн для Instagram stories/reels
            match = re.search(r"(?:stories|reel|p)\/([a-zA-Z0-9_-]+)", url)
            if match:
                return match.group(1)

        return ""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Проверяет, является ли строка валидным URL

        Args:
            url: Строка для проверки

        Returns:
            bool: True если URL валидный
        """
        url_pattern = re.compile(
            r'^https?://'  # http:// или https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # опциональный порт
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(url_pattern.match(url))