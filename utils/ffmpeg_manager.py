"""
Менеджер для работы с FFmpeg
Автоматически скачивает FFmpeg при отсутствии
"""
import os
import sys
import zipfile
import tarfile
import platform
import subprocess
import requests
import time
from pathlib import Path
from typing import Optional, Tuple
from config import BASE_DIR

class FFmpegManager:
    """Класс для управления FFmpeg"""

    def __init__(self, logger=None):
        self.logger = logger
        self.ffmpeg_dir = BASE_DIR / "ffmpeg"
        self.ffmpeg_path = self._get_ffmpeg_path()
        self.ffprobe_path = self._get_ffprobe_path()

    def _get_ffmpeg_path(self) -> Optional[Path]:
        """Возвращает путь к ffmpeg"""
        system = platform.system().lower()

        if system == "windows":
            return self.ffmpeg_dir / "bin" / "ffmpeg.exe"
        elif system == "darwin":  # macOS
            return self.ffmpeg_dir / "bin" / "ffmpeg"
        else:  # Linux
            return self.ffmpeg_dir / "ffmpeg"

    def _get_ffprobe_path(self) -> Optional[Path]:
        """Возвращает путь к ffprobe"""
        system = platform.system().lower()

        if system == "windows":
            return self.ffmpeg_dir / "bin" / "ffprobe.exe"
        elif system == "darwin":  # macOS
            return self.ffmpeg_dir / "bin" / "ffprobe"
        else:  # Linux
            return self.ffmpeg_dir / "ffprobe"

    def get_download_url(self) -> Tuple[str, str]:
        """
        Возвращает URL для скачивания FFmpeg в зависимости от платформы

        Returns:
            Tuple[str, str]: (url, имя_файла)
        """
        system = platform.system().lower()

        # Актуальные ссылки на FFmpeg builds
        if system == "windows":
            # BtbN builds (более надежные)
            return (
                "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
                "ffmpeg-windows.zip"
            )
        elif system == "darwin":  # macOS
            # Static builds для macOS
            return (
                "https://evermeet.cx/ffmpeg/ffmpeg-7.0.zip",
                "ffmpeg-macos.zip"
            )
        else:  # Linux
            # Static builds для Linux
            return (
                "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
                "ffmpeg-linux.tar.xz"
            )

    def check_ffmpeg(self) -> bool:
        """
        Проверяет наличие FFmpeg в системе или в локальной папке

        Returns:
            bool: True если FFmpeg доступен
        """
        # Сначала проверяем в системном PATH
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)
            if result.returncode == 0:
                if self.logger:
                    self.logger.info("✅ FFmpeg найден в системе")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass

        # Проверяем в локальной папке
        if self.ffmpeg_path and self.ffmpeg_path.exists():
            try:
                result = subprocess.run([str(self.ffmpeg_path), '-version'],
                                      capture_output=True,
                                      text=True,
                                      timeout=5)
                if result.returncode == 0:
                    if self.logger:
                        self.logger.info(f"✅ FFmpeg найден локально: {self.ffmpeg_path}")

                    # Добавляем в PATH для этого сеанса
                    os.environ["PATH"] = str(self.ffmpeg_path.parent) + os.pathsep + os.environ["PATH"]
                    return True
            except (subprocess.TimeoutExpired, Exception):
                pass

        return False

    def download_ffmpeg(self, progress_callback=None) -> bool:
        """
        Скачивает FFmpeg

        Args:
            progress_callback: Функция для отображения прогресса (принимает значение от 0 до 100)

        Returns:
            bool: True если успешно
        """
        try:
            # Создаем директорию
            self.ffmpeg_dir.mkdir(exist_ok=True)

            # Получаем URL для скачивания
            url, filename = self.get_download_url()
            zip_path = self.ffmpeg_dir / filename

            if self.logger:
                self.logger.info(f"📥 Скачиваю FFmpeg с {url}")

            # Скачиваем файл с таймаутом
            response = requests.get(url, stream=True, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if response.status_code != 200:
                if self.logger:
                    self.logger.error(f"❌ Ошибка скачивания: HTTP {response.status_code}")
                return False

            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            last_progress = 0

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size:
                            progress = int(downloaded / total_size * 100)
                            # Обновляем только если прогресс изменился
                            if progress != last_progress:
                                progress_callback(progress)
                                last_progress = progress

            if self.logger:
                self.logger.info(f"📦 Распаковываю FFmpeg...")

            # Распаковываем в зависимости от типа файла
            if filename.endswith('.zip'):
                success = self._extract_zip(zip_path)
            elif filename.endswith('.tar.xz'):
                success = self._extract_tar_xz(zip_path)
            else:
                success = False

            # Удаляем архив
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except:
                    pass

            if not success:
                if self.logger:
                    self.logger.error("❌ Ошибка при распаковке FFmpeg")
                return False

            # Проверяем результат
            if self.check_ffmpeg():
                if self.logger:
                    self.logger.success("✅ FFmpeg успешно установлен")
                return True
            else:
                if self.logger:
                    self.logger.error("❌ Не удалось установить FFmpeg")
                return False

        except requests.exceptions.Timeout:
            if self.logger:
                self.logger.error("❌ Таймаут при скачивании FFmpeg")
            return False
        except requests.exceptions.ConnectionError:
            if self.logger:
                self.logger.error("❌ Ошибка подключения. Проверьте интернет")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Ошибка при скачивании FFmpeg: {e}")
            return False

    def _extract_zip(self, zip_path: Path) -> bool:
        """Распаковывает ZIP архив"""
        try:
            import zipfile

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Проверяем, есть ли вложенная папка
                file_list = zip_ref.namelist()
                top_level = set(f.split('/')[0] for f in file_list if '/' in f)

                if len(top_level) == 1 and list(top_level)[0]:
                    # Есть корневая папка, извлекаем с переименованием
                    temp_dir = self.ffmpeg_dir / "temp"
                    temp_dir.mkdir(exist_ok=True)
                    zip_ref.extractall(temp_dir)

                    # Перемещаем файлы
                    extracted_dir = temp_dir / list(top_level)[0]
                    if extracted_dir.exists():
                        for item in extracted_dir.iterdir():
                            target = self.ffmpeg_dir / item.name
                            if target.exists():
                                if target.is_dir():
                                    # Если папка существует, перемещаем содержимое
                                    for subitem in item.iterdir():
                                        subitem.rename(target / subitem.name)
                                else:
                                    target.unlink()
                                    item.rename(target)
                            else:
                                item.rename(target)

                    # Удаляем временную папку
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                else:
                    # Нет корневой папки, извлекаем напрямую
                    zip_ref.extractall(self.ffmpeg_dir)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка распаковки ZIP: {e}")
            return False

    def _extract_tar_xz(self, tar_path: Path) -> bool:
        """Распаковывает tar.xz архив"""
        try:
            import tarfile

            with tarfile.open(tar_path, 'r:xz') as tar:
                # Проверяем корневую папку
                members = tar.getmembers()
                if members and '/' not in members[0].name:
                    # Есть корневая папка
                    temp_dir = self.ffmpeg_dir / "temp"
                    temp_dir.mkdir(exist_ok=True)
                    tar.extractall(temp_dir)

                    # Перемещаем файлы
                    extracted_dirs = list(temp_dir.iterdir())
                    if extracted_dirs:
                        extracted_dir = extracted_dirs[0]
                        for item in extracted_dir.iterdir():
                            target = self.ffmpeg_dir / item.name
                            if target.exists():
                                if target.is_dir():
                                    for subitem in item.iterdir():
                                        subitem.rename(target / subitem.name)
                                else:
                                    target.unlink()
                                    item.rename(target)
                            else:
                                item.rename(target)

                    # Удаляем временную папку
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                else:
                    tar.extractall(self.ffmpeg_dir)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Ошибка распаковки TAR: {e}")
            return False


class FFmpegProgress:
    """Класс для отображения прогресса скачивания FFmpeg в GUI"""

    def __init__(self, parent_window, logger):
        self.parent = parent_window
        self.logger = logger
        self.progress_window = None
        self.progress_bar = None
        self.label = None
        self.status_label = None
        self.percent_label = None

    def show_progress(self):
        """Показывает окно прогресса"""
        import tkinter as tk
        from tkinter import ttk

        self.progress_window = tk.Toplevel(self.parent)
        self.progress_window.title("Установка FFmpeg")
        self.progress_window.geometry("450x250")
        self.progress_window.transient(self.parent)
        self.progress_window.grab_set()
        self.progress_window.focus_force()

        # Центрируем окно
        self.progress_window.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (450 // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (250 // 2)
        self.progress_window.geometry(f"+{x}+{y}")

        # Заголовок
        title_label = tk.Label(
            self.progress_window,
            text="Установка FFmpeg",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=(20, 10))

        # Иконка
        icon_label = tk.Label(
            self.progress_window,
            text="🎬",
            font=("Arial", 32)
        )
        icon_label.pack()

        # Описание
        self.label = tk.Label(
            self.progress_window,
            text="Подготовка к скачиванию FFmpeg...",
            wraplength=400,
            font=("Arial", 12)
        )
        self.label.pack(pady=10)

        # Прогресс бар
        self.progress_bar = ttk.Progressbar(
            self.progress_window,
            length=350,
            mode='determinate'
        )
        self.progress_bar.pack(pady=10)
        self.progress_bar['value'] = 0

        # Проценты
        self.percent_label = tk.Label(
            self.progress_window,
            text="0%",
            font=("Arial", 12, "bold")
        )
        self.percent_label.pack()

        # Статус
        self.status_label = tk.Label(
            self.progress_window,
            text="",
            font=("Arial", 11),
            fg="gray"
        )
        self.status_label.pack(pady=5)

        # Кнопка отмены
        self.cancel_btn = tk.Button(
            self.progress_window,
            text="Отмена",
            command=self.on_close,
            bg="red",
            fg="white",
            width=15,
            height=1
        )
        self.cancel_btn.pack(pady=10)

        self.progress_window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Обновляем UI
        self.progress_window.update()

    def update_progress(self, value: int):
        """Обновляет прогресс"""
        if self.progress_bar:
            self.progress_bar['value'] = value
            self.percent_label.configure(text=f"{value}%")
            self.progress_window.update()

    def set_status(self, text: str):
        """Обновляет статус"""
        if self.label:
            self.label.configure(text=text)
            self.progress_window.update()

    def set_detailed_status(self, text: str):
        """Обновляет детальный статус"""
        if self.status_label:
            self.status_label.configure(text=text)
            self.progress_window.update()

    def on_close(self):
        """Закрытие окна"""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None

    def close(self):
        """Закрывает окно прогресса"""
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None