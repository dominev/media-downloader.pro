"""
Загрузчик для Instagram Stories
"""
import os
import requests
from pathlib import Path
from typing import Optional, List
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from .base import BaseDownloader
from utils.file_handler import FileHandler


class InstagramDownloader(BaseDownloader):
    """Класс для скачивания stories из Instagram"""

    def __init__(self, logger):
        super().__init__(logger)
        self.client = None
        self.user_id = None
        self.username = None
        self.password = None

    def is_supported(self, url: str) -> bool:
        """Проверяет, является ли ссылка Instagram URL"""
        instagram_domains = ['instagram.com', 'instagr.am']
        return any(domain in url.lower() for domain in instagram_domains)

    def login(self, username: str, password: str) -> bool:
        """
        Вход в Instagram

        Args:
            username: Имя пользователя
            password: Пароль

        Returns:
            bool: True если вход успешный
        """
        if not username or not password:
            self.logger.warning("Не указаны логин/пароль для Instagram")
            return False

        try:
            self.client = Client()
            self.client.login(username, password)
            self.user_id = self.client.user_id
            self.username = username
            self.password = password
            self.logger.success(f"Успешный вход в Instagram как {username}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка входа в Instagram: {str(e)}")
            return False

    def _download_story(self, story, download_dir: Path) -> Optional[Path]:
        """
        Скачивает одну историю

        Args:
            story: Объект истории из instagrapi
            download_dir: Директория для сохранения

        Returns:
            Optional[Path]: Путь к скачанному файлу
        """
        try:
            if story.media_type == 1:  # Фото
                url = story.thumbnail_url
                ext = ".jpg"
            elif story.media_type == 2:  # Видео
                url = story.video_url
                ext = ".mp4"
            else:
                return None

            # Скачиваем файл
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # Формируем имя файла
                timestamp = story.taken_at.strftime("%Y%m%d_%H%M%S")
                filename = f"story_{timestamp}_{story.pk}{ext}"

                # Очищаем имя и получаем уникальный путь
                safe_filename = FileHandler.sanitize_filename(filename)
                filepath = FileHandler.get_unique_filename(download_dir, safe_filename)

                # Сохраняем файл
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.is_stopped():
                            return None
                        f.write(chunk)

                return filepath

        except Exception as e:
            self.logger.error(f"Ошибка при скачивании истории: {str(e)}")

        return None

    def download(self, url: str, download_dir: Path, **kwargs) -> Optional[Path]:
        """
        Скачивает stories из Instagram

        Args:
            url: Ссылка на профиль или story
            download_dir: Директория для сохранения
            **kwargs: login (str), password (str)

        Returns:
            Optional[Path]: Путь к скачанному файлу
        """
        try:
            self.reset_stop_flag()
            self.set_status("Подготовка...")
            self.update_progress(0)

            # Проверяем авторизацию
            login = kwargs.get('login', '')
            password = kwargs.get('password', '')

            if login and password:
                if not self.login(login, password):
                    self.logger.error("Не удалось войти в Instagram")
                    return None

            if not self.client:
                self.logger.error("Требуется авторизация для Instagram")
                return None

            # Извлекаем username из URL
            # Поддерживаемые форматы:
            # instagram.com/username/
            # instagram.com/stories/username/
            # instagram.com/username/story_id
            parts = url.rstrip('/').split('/')
            username = None

            for i, part in enumerate(parts):
                if part in ['stories', 'p', 'reel'] and i + 1 < len(parts):
                    username = parts[i + 1]
                    break

            if not username:
                # Пробуем взять последний непустой элемент
                username = parts[-1] if parts[-1] else parts[-2]

            # Получаем user_id по username
            try:
                user_id = self.client.user_id_from_username(username)
                self.logger.info(f"Найдена страница пользователя: {username}")
            except Exception as e:
                self.logger.error(f"Пользователь {username} не найден")
                return None

            # Получаем активные stories
            stories = self.client.user_stories(user_id)

            if not stories:
                self.logger.info(f"У пользователя {username} нет активных stories")
                return None

            self.logger.info(f"Найдено {len(stories)} stories")

            # Создаем поддиректорию для этого пользователя
            user_dir = download_dir / 'instagram' / username
            user_dir.mkdir(parents=True, exist_ok=True)

            downloaded_files = []

            # Скачиваем каждую story
            for i, story in enumerate(stories):
                if self.is_stopped():
                    break

                progress = int((i + 1) / len(stories) * 100)
                self.update_progress(progress)
                self.set_status(f"Скачиваю {i + 1}/{len(stories)}")

                filepath = self._download_story(story, user_dir)
                if filepath:
                    downloaded_files.append(filepath)
                    self.logger.success(f"Сохранено: {filepath.name}")

            if downloaded_files:
                self.logger.success(f"Загружено {len(downloaded_files)} stories")
                self.set_status("Готово")
                return downloaded_files[0] if downloaded_files else None
            else:
                self.logger.warning("Не удалось скачать stories")
                return None

        except LoginRequired:
            self.logger.error("Требуется повторная авторизация в Instagram")
            return None
        except Exception as e:
            self.handle_error(e, f"при загрузке из Instagram {url}")
            return None
        finally:
            self.update_progress(0)
            self.set_status("idle")