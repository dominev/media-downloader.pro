"""
Загрузчик для Telegram
"""
import os
import asyncio
from pathlib import Path
from typing import Optional
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from .base import BaseDownloader
from utils.file_handler import FileHandler
from config import TELEGRAM_CONFIG


class TelegramDownloader(BaseDownloader):
    """Класс для скачивания медиа из Telegram"""

    def __init__(self, logger):
        super().__init__(logger)
        self.client = None
        self.api_id = TELEGRAM_CONFIG.get('api_id')
        self.api_hash = TELEGRAM_CONFIG.get('api_hash')
        self.session_name = TELEGRAM_CONFIG.get('session_name', 'telegram_session')

    def is_supported(self, url: str) -> bool:
        """Проверяет, является ли ссылка Telegram URL"""
        telegram_domains = ['t.me', 'telegram.me']
        return any(domain in url.lower() for domain in telegram_domains)

    def configure(self, api_id: int, api_hash: str):
        """
        Настройка API параметров

        Args:
            api_id: API ID из my.telegram.org
            api_hash: API Hash из my.telegram.org
        """
        self.api_id = api_id
        self.api_hash = api_hash

    async def _download_async(self, url: str, download_dir: Path) -> Optional[Path]:
        """
        Асинхронная загрузка из Telegram

        Args:
            url: Ссылка на сообщение с медиа
            download_dir: Директория для сохранения

        Returns:
            Optional[Path]: Путь к скачанному файлу
        """
        try:
            if not self.api_id or not self.api_hash:
                self.logger.error("Не настроены API параметры для Telegram")
                return None

            # Создаем клиент
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start()

            self.logger.info("Подключение к Telegram...")

            # Извлекаем информацию из ссылки
            # Формат: https://t.me/username/123 или https://t.me/c/1234567890/123
            path_parts = url.rstrip('/').split('/')

            if 'c' in path_parts:
                # Это ссылка на закрытый канал
                chat_id = int(path_parts[path_parts.index('c') + 1])
                message_id = int(path_parts[-1])
                chat = await self.client.get_entity(chat_id)
            else:
                # Публичный канал
                username = path_parts[-2]
                message_id = int(path_parts[-1])
                chat = await self.client.get_entity(username)

            # Получаем сообщение
            message = await self.client.get_messages(chat, ids=message_id)

            if not message or not message.media:
                self.logger.error("В сообщении нет медиа")
                return None

            # Определяем тип медиа и скачиваем
            if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                # Создаем директорию для Telegram
                telegram_dir = download_dir / 'telegram'
                telegram_dir.mkdir(exist_ok=True)

                self.set_status("Скачивание...")
                self.update_progress(50)

                # Скачиваем файл
                path = await message.download_media(file=str(telegram_dir))

                if path:
                    filepath = Path(path)

                    # Очищаем имя файла если нужно
                    safe_name = FileHandler.sanitize_filename(filepath.name)
                    if safe_name != filepath.name:
                        new_path = filepath.parent / safe_name
                        filepath.rename(new_path)
                        filepath = new_path

                    self.update_progress(100)
                    self.set_status("Готово")

                    size = FileHandler.get_file_size(filepath)
                    self.logger.success(f"Файл сохранён: {filepath.name} ({size})")

                    return filepath

            return None

        except Exception as e:
            self.handle_error(e, f"при загрузке из Telegram {url}")
            return None
        finally:
            if self.client:
                await self.client.disconnect()

    def download(self, url: str, download_dir: Path, **kwargs) -> Optional[Path]:
        """
        Скачивает медиа из Telegram

        Args:
            url: Ссылка на сообщение с медиа
            download_dir: Директория для сохранения
            **kwargs: api_id (int), api_hash (str)

        Returns:
            Optional[Path]: Путь к скачанному файлу
        """
        # Обновляем API параметры если переданы
        api_id = kwargs.get('api_id')
        api_hash = kwargs.get('api_hash')

        if api_id and api_hash:
            self.configure(api_id, api_hash)

        self.reset_stop_flag()
        self.set_status("Подготовка...")
        self.update_progress(0)

        # Запускаем асинхронную загрузку
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(self._download_async(url, download_dir))
            return result
        except Exception as e:
            self.handle_error(e, f"при загрузке из Telegram {url}")
            return None
        finally:
            loop.close()
            self.update_progress(0)
            self.set_status("idle")