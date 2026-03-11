"""
Загрузчик для VK
"""
import yt_dlp
from pathlib import Path
from typing import Optional
from .base import BaseDownloader
from utils.file_handler import FileHandler


class VKDownloader(BaseDownloader):
    """Класс для скачивания видео с VK"""

    def __init__(self, logger):
        super().__init__(logger)
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'progress_hooks': [self.progress_hook],
        }

    def is_supported(self, url: str) -> bool:
        """Проверяет, является ли ссылка VK URL"""
        vk_domains = ['vk.com', 'vkontakte.ru']
        return any(domain in url.lower() for domain in vk_domains)

    def progress_hook(self, d):
        """Хук для отслеживания прогресса загрузки"""
        if self.is_stopped():
            raise Exception("Download stopped by user")

        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes'] > 0:
                progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                self.update_progress(progress)

    def download(self, url: str, download_dir: Path, **kwargs) -> Optional[Path]:
        """
        Скачивает видео с VK

        Args:
            url: Ссылка на видео
            download_dir: Директория для сохранения
            **kwargs: Не используются

        Returns:
            Optional[Path]: Путь к скачанному файлу
        """
        try:
            self.reset_stop_flag()
            self.set_status("Подготовка...")
            self.update_progress(0)

            # Создаем временную директорию
            temp_dir = download_dir / 'temp'
            temp_dir.mkdir(exist_ok=True)

            # Настраиваем опции для yt-dlp
            opts = self.ydl_opts.copy()
            opts.update({
                'format': 'best[ext=mp4]/best',
                'outtmpl': str(temp_dir / '%(title)s_%(id)s.%(ext)s'),
            })

            self.logger.info(f"Начинаю загрузку с VK: {url}")

            with yt_dlp.YoutubeDL(opts) as ydl:
                # Получаем информацию о видео
                info = ydl.extract_info(url, download=False)
                if info is None:
                    raise Exception("Не удалось получить информацию о видео")

                title = info.get('title', 'vk_video')
                self.logger.info(f"Название: {title}")

                # Скачиваем видео
                if not self.is_stopped():
                    ydl.download([url])

                    # Ищем скачанный файл
                    for file in temp_dir.glob("*"):
                        if file.is_file() and not file.name.startswith('.'):
                            # Очищаем имя файла
                            safe_filename = FileHandler.sanitize_filename(file.name)

                            # Создаем уникальное имя в целевой директории
                            final_path = FileHandler.get_unique_filename(download_dir, safe_filename)

                            # Перемещаем файл
                            file.rename(final_path)

                            self.logger.success(f"Видео сохранено: {final_path.name}")
                            self.set_status("Готово")

                            # Очищаем временную директорию
                            for temp_file in temp_dir.glob("*"):
                                temp_file.unlink()
                            temp_dir.rmdir()

                            return final_path

            return None

        except Exception as e:
            if "Download stopped by user" in str(e):
                self.logger.warning("Загрузка остановлена")
            else:
                self.handle_error(e, f"при загрузке {url}")
            return None
        finally:
            self.update_progress(0)
            self.set_status("idle")