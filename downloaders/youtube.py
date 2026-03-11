"""
Загрузчик для YouTube
"""
import yt_dlp
from pathlib import Path
from typing import Optional, Dict, Any
from .base import BaseDownloader
from utils.file_handler import FileHandler

class YouTubeDownloader(BaseDownloader):
    """Класс для скачивания видео с YouTube"""

    def __init__(self, logger):
        super().__init__(logger)
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'progress_hooks': [self.progress_hook],
        }
        self.ffmpeg_path = None
        self.ffprobe_path = None

    def is_supported(self, url: str) -> bool:
        """Проверяет, является ли ссылка YouTube URL"""
        youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com', 'youtube.com/shorts']
        return any(domain in url.lower() for domain in youtube_domains)

    def set_ffmpeg_path(self, ffmpeg_path: str, ffprobe_path: str = None):
        """
        Устанавливает путь к FFmpeg

        Args:
            ffmpeg_path: Путь к ffmpeg
            ffprobe_path: Путь к ffprobe (опционально)
        """
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

        # Обновляем опции yt-dlp
        if ffmpeg_path:
            ffmpeg_dir = str(Path(ffmpeg_path).parent)
            self.ydl_opts['ffmpeg_location'] = ffmpeg_dir

            if ffprobe_path:
                self.ydl_opts['ffprobe_location'] = ffprobe_path

            self.logger.info(f"FFmpeg настроен: {ffmpeg_dir}")

    def progress_hook(self, d):
        """Хук для отслеживания прогресса загрузки"""
        if self.is_stopped():
            raise Exception("Download stopped by user")

        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes'] > 0:
                progress = int(d['downloaded_bytes'] / d['total_bytes'] * 100)
                self.update_progress(progress)
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                progress = int(d['downloaded_bytes'] / d['total_bytes_estimate'] * 100)
                self.update_progress(progress)

            # Обновляем статус с информацией о скорости и размере
            status_parts = ["Загрузка..."]

            if 'speed' in d and d['speed']:
                speed_mb = d['speed'] / 1024 / 1024
                status_parts.append(f"{speed_mb:.1f} MB/s")

            if 'eta' in d and d['eta']:
                eta = d['eta']
                if eta < 60:
                    status_parts.append(f"{eta} сек")
                else:
                    status_parts.append(f"{eta//60} мин {eta%60} сек")

            self.set_status(" | ".join(status_parts))

        elif d['status'] == 'finished':
            self.set_status("Обработка видео...")
            self.update_progress(100)

    def _get_format_string(self, max_quality: bool, format_type: str) -> str:
        """
        Возвращает строку формата для yt-dlp

        Args:
            max_quality: True для максимального качества
            format_type: 'mp4', 'best' или 'audio'

        Returns:
            str: Строка формата для yt-dlp
        """
        if format_type == 'audio':
            # Только аудио
            if max_quality:
                return 'bestaudio/best'
            else:
                return 'worstaudio/worst'
        elif format_type == 'best':
            # Лучший доступный формат
            return 'bestvideo+bestaudio/best'
        else:  # mp4
            # MP4 видео
            if max_quality:
                # Ищем лучшее MP4 видео
                return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                # Худшее MP4 видео
                return 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst'

    def _get_postprocessors(self, format_type: str) -> list:
        """
        Возвращает пост-процессоры для обработки видео

        Args:
            format_type: 'mp4', 'best' или 'audio'

        Returns:
            list: Список пост-процессоров
        """
        postprocessors = []

        if format_type == 'audio':
            # Конвертируем в MP3
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            })
        else:
            # Конвертируем в MP4 если нужно
            postprocessors.append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            })

        # Добавляем метаданные
        postprocessors.append({
            'key': 'FFmpegMetadata',
            'add_metadata': True,
        })

        # Добавляем обложку для аудио
        if format_type == 'audio':
            postprocessors.append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            })

        return postprocessors

    def download(self, url: str, download_dir: Path, **kwargs) -> Optional[Path]:
        """
        Скачивает видео с YouTube

        Args:
            url: Ссылка на видео
            download_dir: Директория для сохранения
            **kwargs:
                max_quality (bool): Максимальное качество
                format (str): Формат (mp4, best, audio)
                ffmpeg_location (str): Путь к FFmpeg

        Returns:
            Optional[Path]: Путь к скачанному файлу
        """
        temp_dir = None
        try:
            self.reset_stop_flag()
            self.set_status("Подготовка...")
            self.update_progress(0)

            # Получаем параметры
            max_quality = kwargs.get('max_quality', True)
            format_type = kwargs.get('format', 'mp4')
            ffmpeg_location = kwargs.get('ffmpeg_location')

            # Создаем временную директорию
            temp_dir = download_dir / 'temp'
            temp_dir.mkdir(exist_ok=True)

            # Формируем имя файла
            output_template = str(temp_dir / '%(title)s.%(ext)s')

            # Настраиваем опции для yt-dlp
            opts = self.ydl_opts.copy()
            opts.update({
                'format': self._get_format_string(max_quality, format_type),
                'outtmpl': output_template,
                'postprocessors': self._get_postprocessors(format_type),
                'writethumbnail': format_type == 'audio',  # Сохраняем обложку для аудио
                'embedthumbnail': format_type == 'audio',  # Встраиваем обложку в аудио
                'addmetadata': True,  # Добавляем метаданные
            })

            # Добавляем путь к FFmpeg если указан
            if ffmpeg_location:
                opts['ffmpeg_location'] = ffmpeg_location
            elif self.ffmpeg_path:
                opts['ffmpeg_location'] = str(Path(self.ffmpeg_path).parent)

            self.logger.info(f"🎬 Начинаю загрузку с YouTube: {url}")
            self.logger.info(f"📊 Качество: {'максимальное' if max_quality else 'минимальное'}, Формат: {format_type}")

            with yt_dlp.YoutubeDL(opts) as ydl:
                # Получаем информацию о видео
                self.set_status("Получение информации...")
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise Exception("Не удалось получить информацию о видео")

                # Проверяем возрастные ограничения
                if info.get('age_limit', 0) > 0:
                    self.logger.warning("⚠️ Видео имеет возрастные ограничения")

                title = info.get('title', 'video')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Неизвестный автор')

                # Форматируем длительность
                if duration > 0:
                    minutes = duration // 60
                    seconds = duration % 60
                    duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "неизвестно"

                self.logger.info(f"📹 Название: {title}")
                self.logger.info(f"👤 Автор: {uploader}")
                self.logger.info(f"⏱️ Длительность: {duration_str}")

                # Проверяем доступные форматы
                if 'formats' in info:
                    formats_count = len(info['formats'])
                    self.logger.info(f"📦 Доступно форматов: {formats_count}")

                # Скачиваем видео
                if not self.is_stopped():
                    self.set_status("Скачивание...")
                    ydl.download([url])

                    # Ищем скачанный файл
                    downloaded_files = list(temp_dir.glob("*"))

                    if not downloaded_files:
                        raise Exception("Файл не был скачан")

                    # Берем самый свежий файл
                    downloaded_file = max(downloaded_files, key=lambda p: p.stat().st_mtime)

                    # Определяем целевое расширение
                    if format_type == 'audio':
                        target_ext = '.mp3'
                    else:
                        target_ext = '.mp4'

                    # Формируем конечное имя файла
                    safe_title = FileHandler.sanitize_filename(title)
                    final_filename = f"{safe_title}{target_ext}"

                    # Создаем поддиректорию для YouTube если нужно
                    youtube_dir = download_dir / 'youtube'
                    youtube_dir.mkdir(exist_ok=True)

                    # Получаем уникальное имя файла
                    final_path = FileHandler.get_unique_filename(youtube_dir, final_filename)

                    # Перемещаем файл
                    if downloaded_file.suffix != target_ext:
                        # Если расширение не совпадает, возможно файл уже обработан
                        # Ищем файл с правильным расширением во временной папке
                        processed_files = list(temp_dir.glob(f"*{target_ext}"))
                        if processed_files:
                            downloaded_file = processed_files[0]

                    downloaded_file.rename(final_path)

                    # Получаем размер файла
                    file_size = FileHandler.get_file_size(final_path)

                    self.logger.success(f"✅ Видео сохранено: {final_path.name} ({file_size})")
                    self.set_status("Готово")

                    return final_path

            return None

        except Exception as e:
            if "Download stopped by user" in str(e):
                self.logger.warning("⏹️ Загрузка остановлена пользователем")
            else:
                self.handle_error(e, f"при загрузке {url}")

                # Дополнительная информация об ошибке
                if 'Unsupported URL' in str(e):
                    self.logger.error("❌ Неподдерживаемый URL или видео недоступно")
                elif 'Video unavailable' in str(e):
                    self.logger.error("❌ Видео недоступно (возможно, удалено или с ограничениями)")
                elif 'ffmpeg' in str(e).lower():
                    self.logger.error("❌ Ошибка FFmpeg. Убедитесь, что FFmpeg установлен правильно")

            return None
        finally:
            # Очищаем временную директорию
            if temp_dir and temp_dir.exists():
                try:
                    for file in temp_dir.glob("*"):
                        file.unlink()
                    temp_dir.rmdir()
                except Exception as e:
                    self.logger.warning(f"Не удалось очистить временную папку: {e}")

            self.update_progress(0)
            self.set_status("idle")

    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о видео без скачивания

        Args:
            url: Ссылка на видео

        Returns:
            Optional[Dict]: Информация о видео или None
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(url, download=False)

                if info:
                    return {
                        'title': info.get('title'),
                        'uploader': info.get('uploader'),
                        'duration': info.get('duration'),
                        'view_count': info.get('view_count'),
                        'like_count': info.get('like_count'),
                        'description': info.get('description'),
                        'upload_date': info.get('upload_date'),
                        'thumbnail': info.get('thumbnail'),
                        'categories': info.get('categories'),
                        'tags': info.get('tags'),
                    }
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации: {e}")
            return None