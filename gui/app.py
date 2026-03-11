"""
Главное окно приложения
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
from queue import Queue
from typing import Optional, List, Dict
import time
import sys
import os

from config import APP_NAME, APP_VERSION, APP_GEOMETRY, THEME, DEFAULT_DOWNLOAD_DIR
from .frames import SettingsFrame, InstagramAuthFrame, QueueFrame
from .widgets import URLInput, LogViewer, DownloadProgressFrame
from utils.logger import Logger
from utils.platform_detector import PlatformDetector
from utils.file_handler import FileHandler
from utils.ffmpeg_manager import FFmpegManager, FFmpegProgress
from downloaders import YouTubeDownloader, VKDownloader, TelegramDownloader, InstagramDownloader


class DownloaderApp(ctk.CTk):
    """Главное окно приложения"""

    def __init__(self, has_ffmpeg=False):
        super().__init__()

        # Настройка окна
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry(APP_GEOMETRY)
        self.minsize(800, 600)

        # Настройка темы
        ctk.set_appearance_mode(THEME["appearance_mode"])
        ctk.set_default_color_theme(THEME["color_theme"])

        # Инициализация компонентов
        self.logger = Logger()
        self.platform_detector = PlatformDetector()
        self.download_queue = Queue()
        self.active_downloads = []
        self.running = False
        self.stop_flag = False
        self.has_ffmpeg = has_ffmpeg

        # Инициализация FFmpeg менеджера
        self.ffmpeg_manager = FFmpegManager(self.logger)

        # Инициализация загрузчиков
        self.downloaders = {
            'youtube': YouTubeDownloader(self.logger),
            'vk': VKDownloader(self.logger),
            'telegram': TelegramDownloader(self.logger),
            'instagram': InstagramDownloader(self.logger),
        }

        # Словарь для отслеживания прогресса загрузок
        self.download_progress = {}

        # Создание интерфейса
        self.setup_ui()

        # Настройка логгера
        self.logger.add_callback(self.log_viewer.add_line)

        # Приветственное сообщение
        self.logger.info(f"🎥 {APP_NAME} v{APP_VERSION} запущен")
        self.logger.info(f"📂 Папка загрузок по умолчанию: {DEFAULT_DOWNLOAD_DIR}")

        # Проверяем FFmpeg
        self.check_ffmpeg_on_startup()

        self.logger.info("💡 Выберите папку для сохранения и вставьте ссылки")

        # Обработка закрытия окна
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Запускаем обновление статуса
        self.update_status_loop()

    def setup_ui(self):
        """Создание пользовательского интерфейса"""

        # Основной контейнер с прокруткой
        self.main_container = ctk.CTkScrollableFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. Верхняя панель с заголовком
        self.create_header()

        # 2. Поле ввода URL
        self.create_url_input()

        # 3. Папка сохранения
        self.create_folder_selector()

        # 4. Прогресс бар загрузки
        self.create_progress_frame()

        # 5. Настройки
        self.create_settings()

        # 6. Instagram авторизация
        self.create_instagram_auth()

        # 7. Кнопки управления
        self.create_control_buttons()

        # 8. Очередь загрузок
        self.create_queue_display()

        # 9. Лог
        self.create_log_display()

        # 10. Статус бар
        self.create_status_bar()

    def create_header(self):
        """Создает заголовок"""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="🎥 Media Downloader Pro",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(side="left")

        version = ctk.CTkLabel(
            header_frame,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        version.pack(side="left", padx=5)

        # Индикатор FFmpeg
        ffmpeg_status = ctk.CTkLabel(
            header_frame,
            text="✅ FFmpeg" if self.has_ffmpeg else "⚠️ FFmpeg",
            font=ctk.CTkFont(size=12),
            text_color="green" if self.has_ffmpeg else "orange"
        )
        ffmpeg_status.pack(side="right", padx=5)

    def create_url_input(self):
        """Создает поле ввода URL"""
        url_frame = ctk.CTkFrame(self.main_container)
        url_frame.pack(fill="x", pady=5)

        # Заголовок
        ctk.CTkLabel(
            url_frame,
            text="🔗 Ссылки на контент:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Подсказка
        hint = ctk.CTkLabel(
            url_frame,
            text="Поддерживаются: YouTube, VK, Telegram, Instagram Stories",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        hint.pack(anchor="w", padx=10, pady=(0, 5))

        # Поле ввода
        self.url_input = URLInput(
            url_frame,
            height=80,
            placeholder="Вставьте ссылки (по одной на строку)"
        )
        self.url_input.pack(fill="x", padx=10, pady=10)

    def create_folder_selector(self):
        """Создает выбор папки"""
        folder_frame = ctk.CTkFrame(self.main_container)
        folder_frame.pack(fill="x", pady=5)

        # Заголовок
        ctk.CTkLabel(
            folder_frame,
            text="📁 Папка сохранения:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Поле и кнопка
        input_frame = ctk.CTkFrame(folder_frame, fg_color="transparent")
        input_frame.pack(fill="x", padx=10, pady=10)

        self.folder_path = ctk.CTkEntry(
            input_frame,
            placeholder_text="Выберите папку для сохранения"
        )
        self.folder_path.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Устанавливаем папку по умолчанию
        self.folder_path.insert(0, str(DEFAULT_DOWNLOAD_DIR))

        self.folder_button = ctk.CTkButton(
            input_frame,
            text="📁 Обзор",
            width=80,
            command=self.choose_folder
        )
        self.folder_button.pack(side="right")

        # Кнопка открыть папку
        self.open_folder_btn = ctk.CTkButton(
            input_frame,
            text="📂 Открыть",
            width=80,
            command=self.open_download_folder,
            fg_color="gray"
        )
        self.open_folder_btn.pack(side="right", padx=5)

    def create_progress_frame(self):
        """Создает фрейм с прогресс баром"""
        from .widgets import DownloadProgressFrame
        self.progress_frame = DownloadProgressFrame(self.main_container)
        self.progress_frame.pack(fill="x", pady=5)
        self.progress_frame.hide()  # Скрываем по умолчанию

    def create_settings(self):
        """Создает настройки"""
        self.settings_frame = SettingsFrame(self.main_container)
        self.settings_frame.pack(fill="x", pady=5)

    def create_instagram_auth(self):
        """Создает блок авторизации Instagram"""
        self.instagram_frame = InstagramAuthFrame(self.main_container)
        self.instagram_frame.pack(fill="x", pady=5)

    def create_control_buttons(self):
        """Создает кнопки управления"""
        button_frame = ctk.CTkFrame(self.main_container)
        button_frame.pack(fill="x", pady=10)

        # Левая группа кнопок
        left_buttons = ctk.CTkFrame(button_frame, fg_color="transparent")
        left_buttons.pack(side="left", padx=10, pady=10)

        self.add_queue_btn = ctk.CTkButton(
            left_buttons,
            text="➕ Добавить в очередь",
            command=self.add_to_queue,
            width=150,
            height=35,
            font=ctk.CTkFont(size=13)
        )
        self.add_queue_btn.pack(side="left", padx=5)

        self.download_btn = ctk.CTkButton(
            left_buttons,
            text="⬇️ Скачать всё",
            command=self.start_downloads,
            width=150,
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="green"
        )
        self.download_btn.pack(side="left", padx=5)

        # Правая группа кнопок
        right_buttons = ctk.CTkFrame(button_frame, fg_color="transparent")
        right_buttons.pack(side="right", padx=10, pady=10)

        self.stop_btn = ctk.CTkButton(
            right_buttons,
            text="⏹️ Стоп",
            command=self.stop_downloads,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="red",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)

        self.clear_btn = ctk.CTkButton(
            right_buttons,
            text="🗑️ Очистить",
            command=self.clear_all,
            width=100,
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="gray"
        )
        self.clear_btn.pack(side="left", padx=5)

        # Кнопка настроек FFmpeg
        self.ffmpeg_btn = ctk.CTkButton(
            right_buttons,
            text="🎬 FFmpeg",
            command=self.manage_ffmpeg,
            width=80,
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="purple" if not self.has_ffmpeg else "green"
        )
        self.ffmpeg_btn.pack(side="left", padx=5)

    def create_queue_display(self):
        """Создает отображение очереди"""
        self.queue_frame = QueueFrame(self.main_container)
        self.queue_frame.pack(fill="both", expand=True, pady=5)

    def create_log_display(self):
        """Создает отображение лога"""
        log_frame = ctk.CTkFrame(self.main_container)
        log_frame.pack(fill="x", pady=5)

        # Заголовок
        ctk.CTkLabel(
            log_frame,
            text="📋 Лог операций:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))

        # Лог
        self.log_viewer = LogViewer(
            log_frame,
            height=120,
            wrap="word"
        )
        self.log_viewer.pack(fill="x", padx=10, pady=10)

    def create_status_bar(self):
        """Создает строку состояния"""
        self.status_bar = ctk.CTkLabel(
            self,
            text=" Готов к работе",
            anchor="w",
            font=ctk.CTkFont(size=11),
            fg_color=("gray85", "gray25"),
            height=25
        )
        self.status_bar.pack(side="bottom", fill="x")

    def choose_folder(self):
        """Выбирает папку для сохранения"""
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=self.folder_path.get() or str(Path.home())
        )
        if folder:
            self.folder_path.delete(0, "end")
            self.folder_path.insert(0, folder)
            self.logger.info(f"📁 Папка сохранения: {folder}")

    def open_download_folder(self):
        """Открывает папку загрузок в проводнике"""
        folder = self.folder_path.get()
        if folder and Path(folder).exists():
            import subprocess
            import platform

            system = platform.system()
            try:
                if system == "Windows":
                    os.startfile(folder)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", folder])
                else:  # Linux
                    subprocess.run(["xdg-open", folder])
            except Exception as e:
                self.logger.error(f"Не удалось открыть папку: {e}")

    def add_to_queue(self):
        """Добавляет URL в очередь"""
        urls = self.url_input.get_urls()

        if not urls:
            messagebox.showwarning(
                "Нет ссылок",
                "Вставьте ссылки для добавления в очередь"
            )
            return

        # Фильтруем валидные URL
        valid_urls = []
        invalid_urls = []

        for url in urls:
            if self.platform_detector.is_valid_url(url):
                valid_urls.append(url)
            else:
                invalid_urls.append(url)

        if invalid_urls:
            self.logger.warning(f"❌ Некорректные URL: {', '.join(invalid_urls[:3])}")
            if len(invalid_urls) > 3:
                self.logger.warning(f"   и еще {len(invalid_urls) - 3}")

        if valid_urls:
            self.queue_frame.add_items(valid_urls)
            self.logger.info(f"✅ Добавлено в очередь: {len(valid_urls)} ссылок")

            # Очищаем поле ввода
            self.url_input.delete("0.0", "end")
        else:
            messagebox.showerror(
                "Ошибка",
                "Нет валидных ссылок для добавления"
            )

    def start_downloads(self):
        """Запускает загрузки"""
        if self.running:
            return

        items = self.queue_frame.get_items()
        if not items:
            messagebox.showwarning(
                "Очередь пуста",
                "Добавьте ссылки в очередь для загрузки"
            )
            return

        # Проверяем папку сохранения
        download_dir = Path(self.folder_path.get())
        try:
            FileHandler.ensure_directory(download_dir)
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось создать папку сохранения:\n{e}"
            )
            return

        # Запускаем загрузки в отдельном потоке
        self.running = True
        self.stop_flag = False

        # Обновляем состояние кнопок
        self.download_btn.configure(state="disabled", text="⬇️ Загрузка...")
        self.stop_btn.configure(state="normal")
        self.add_queue_btn.configure(state="disabled")

        # Показываем прогресс бар
        total_items = len(items)
        self.progress_frame.show(f"Загрузка 1/{total_items}")

        # Запускаем поток загрузки
        self.download_thread = threading.Thread(
            target=self.download_worker,
            args=(download_dir,),
            daemon=True
        )
        self.download_thread.start()

        self.logger.info("🚀 Запуск загрузок...")
        self.update_status_bar()

    def download_worker(self, download_dir: Path):
        """Рабочий поток для загрузок"""
        items = self.queue_frame.get_items()
        total_items = len(items)

        for i, item in enumerate(items):
            if self.stop_flag:
                break

            url = item["url"]
            platform = item["platform"]

            # Обновляем прогресс бар
            current = i + 1
            self.progress_frame.title_label.configure(text=f"Загрузка {current}/{total_items}")
            self.progress_frame.set_status(f"Загрузка с {platform.upper()}...")
            self.progress_frame.update_progress(int((i) / total_items * 100))

            # Обновляем статус в очереди
            self.queue_frame.update_item_status(i, "загружается", 0)
            self.logger.info(f"⬇️ [{current}/{total_items}] Загрузка: {url}")

            # Получаем загрузчик
            downloader = self.downloaders.get(platform)
            if not downloader:
                self.queue_frame.update_item_status(i, "ошибка")
                self.logger.error(f"❌ Неподдерживаемая платформа: {platform}")
                continue

            # Получаем настройки
            settings = self.settings_frame.get_settings()

            # Добавляем информацию о FFmpeg если есть
            if self.has_ffmpeg and self.ffmpeg_manager.ffmpeg_path:
                settings['ffmpeg_location'] = str(self.ffmpeg_manager.ffmpeg_path.parent)

            # Дополнительные параметры для Instagram
            kwargs = settings.copy()
            if platform == 'instagram':
                login, password = self.instagram_frame.get_credentials()
                kwargs['login'] = login
                kwargs['password'] = password

                if not login or not password:
                    self.logger.warning("⚠️ Для Instagram stories требуется авторизация")

            # Создаем поддиректорию для платформы
            try:
                platform_dir = FileHandler.create_dated_subdirectory(download_dir, platform)
            except Exception as e:
                self.logger.error(f"❌ Не удалось создать директорию: {e}")
                self.queue_frame.update_item_status(i, "ошибка")
                continue

            # Загружаем
            try:
                # Функция для обновления прогресса из загрузчика
                def update_progress(progress):
                    self.after(0, lambda: self.progress_frame.update_progress(progress))
                    self.queue_frame.update_item_status(i, "загружается", progress)

                # Добавляем callback в kwargs
                kwargs['progress_callback'] = update_progress

                result = downloader.download(url, platform_dir, **kwargs)

                # Обновляем статус
                if result:
                    self.queue_frame.update_item_status(i, "готово", 100)
                    self.logger.success(f"✅ [{current}/{total_items}] Загрузка завершена: {result.name}")
                else:
                    self.queue_frame.update_item_status(i, "ошибка")
                    self.logger.error(f"❌ [{current}/{total_items}] Ошибка загрузки")

            except Exception as e:
                self.queue_frame.update_item_status(i, "ошибка")
                self.logger.error(f"❌ [{current}/{total_items}] Критическая ошибка: {e}")

        # Завершение
        self.running = False

        # Скрываем прогресс бар
        self.progress_frame.hide()

        # Обновляем UI в главном потоке
        self.after(0, self.on_downloads_finished)

    def on_downloads_finished(self):
        """Вызывается после завершения всех загрузок"""
        self.download_btn.configure(state="normal", text="⬇️ Скачать всё")
        self.stop_btn.configure(state="disabled")
        self.add_queue_btn.configure(state="normal")

        if self.stop_flag:
            self.logger.info("⏹️ Загрузки остановлены пользователем")
        else:
            # Проверяем статистику
            items = self.queue_frame.get_items()
            total = len(items)
            successful = sum(1 for item in items if item['status'] == 'готово')
            failed = sum(1 for item in items if item['status'] == 'ошибка')

            if successful > 0:
                self.logger.success(f"✅ Успешно загружено: {successful} из {total}")
            if failed > 0:
                self.logger.warning(f"⚠️ Ошибок: {failed} из {total}")

        self.update_status_bar()

    def stop_downloads(self):
        """Останавливает загрузки"""
        self.stop_flag = True
        for downloader in self.downloaders.values():
            downloader.stop()

        self.logger.warning("⏹️ Останавливаю загрузки...")
        self.stop_btn.configure(state="disabled")

    def clear_all(self):
        """Очищает все"""
        if self.running:
            messagebox.showwarning(
                "Загрузка выполняется",
                "Дождитесь завершения загрузок или остановите их"
            )
            return

        if messagebox.askyesno(
            "Очистка",
            "Очистить очередь и лог?"
        ):
            self.queue_frame.clear_queue()
            self.log_viewer.clear()
            self.logger.info("🧹 Очередь и лог очищены")

    def manage_ffmpeg(self):
        """Управление FFmpeg"""
        if self.has_ffmpeg:
            # Показываем информацию о FFmpeg
            ffmpeg_path = self.ffmpeg_manager.ffmpeg_path
            version = self.get_ffmpeg_version()
            messagebox.showinfo(
                "FFmpeg установлен",
                f"✅ FFmpeg найден по пути:\n{ffmpeg_path}\n\n"
                f"📊 Версия: {version}"
            )
        else:
            # Предлагаем скачать
            answer = messagebox.askyesno(
                "FFmpeg не найден",
                "❌ FFmpeg необходим для конвертации видео и аудио.\n\n"
                "Без FFmpeg:\n"
                "• Видео может сохраняться в нестандартных форматах\n"
                "• Конвертация аудио будет недоступна\n"
                "• Некоторые видео могут не скачаться\n\n"
                "Хотите скачать FFmpeg автоматически?\n"
                "(~20 МБ, займет 2-5 минут)",
                icon="question"
            )

            if answer:
                self.download_ffmpeg()

    def check_ffmpeg_on_startup(self):
        """Проверяет FFmpeg при запуске и предлагает скачать если отсутствует"""
        if self.has_ffmpeg:
            self.logger.info("✅ FFmpeg найден в системе")
            return

        self.logger.warning("⚠️ FFmpeg не найден. Некоторые функции могут работать ограниченно.")

        # Спрашиваем пользователя
        answer = messagebox.askyesno(
            "FFmpeg не найден",
            "FFmpeg необходим для конвертации видео и аудио.\n\n"
            "Без FFmpeg:\n"
            "• Видео может сохраняться в нестандартных форматах\n"
            "• Конвертация аудио будет недоступна\n"
            "• Некоторые видео могут не скачаться\n\n"
            "Хотите скачать FFmpeg автоматически?\n"
            "(~20 МБ, займет 2-5 минут)",
            icon="warning"
        )

        if answer:
            self.download_ffmpeg()
        else:
            self.logger.warning("Продолжаем без FFmpeg. Конвертация будет недоступна.")

    def download_ffmpeg(self):
        """Скачивает FFmpeg с отображением прогресса"""
        from utils.ffmpeg_manager import FFmpegProgress

        # Создаем окно прогресса
        progress = FFmpegProgress(self, self.logger)
        progress.show_progress()

        def update_progress(value):
            """Обновляет прогресс"""
            try:
                self.after(0, lambda: progress.update_progress(value))
            except:
                pass

        def set_status(text):
            """Обновляет статус"""
            try:
                self.after(0, lambda: progress.set_status(text))
            except:
                pass

        def set_detailed_status(text):
            """Обновляет детальный статус"""
            try:
                self.after(0, lambda: progress.set_detailed_status(text))
            except:
                pass

        def download_thread():
            """Поток для скачивания"""
            try:
                set_status("Скачивание FFmpeg...")
                set_detailed_status("Подключение к серверу...")

                # Скачиваем FFmpeg с callback прогресса
                success = self.ffmpeg_manager.download_ffmpeg(update_progress)

                if success:
                    set_status("✅ FFmpeg успешно установлен!")
                    set_detailed_status("Готов к использованию")
                    self.has_ffmpeg = True
                    self.logger.success("✅ FFmpeg успешно установлен")

                    # Обновляем настройки загрузчиков
                    self.update_downloaders_ffmpeg()

                    # Обновляем цвет кнопки
                    self.ffmpeg_btn.configure(fg_color="green")

                    # Даем время увидеть сообщение об успехе
                    self.after(2000, progress.close)
                else:
                    # Если не удалось установить, но FFmpeg мог уже быть скачан
                    # Проверяем еще раз
                    if self.ffmpeg_manager.check_ffmpeg():
                        set_status("✅ FFmpeg уже установлен!")
                        set_detailed_status("Готов к использованию")
                        self.has_ffmpeg = True
                        self.logger.success("✅ FFmpeg уже был установлен")
                        self.ffmpeg_btn.configure(fg_color="green")
                        self.after(2000, progress.close)
                    else:
                        set_status("❌ Ошибка при установке FFmpeg")
                        set_detailed_status("Проверьте подключение к интернету")
                        self.logger.error("❌ Не удалось установить FFmpeg")
                        self.after(3000, progress.close)

            except Exception as e:
                # Проверяем, может FFmpeg уже установлен несмотря на ошибку
                if self.ffmpeg_manager.check_ffmpeg():
                    set_status("✅ FFmpeg успешно установлен!")
                    set_detailed_status("Готов к использованию")
                    self.has_ffmpeg = True
                    self.logger.success("✅ FFmpeg успешно установлен")
                    self.ffmpeg_btn.configure(fg_color="green")
                    self.after(2000, progress.close)
                else:
                    set_status(f"❌ Ошибка: {str(e)}")
                    set_detailed_status("Произошла непредвиденная ошибка")
                    self.logger.error(f"❌ Ошибка при установке FFmpeg: {e}")
                    self.after(3000, progress.close)

        # Запускаем скачивание в отдельном потоке
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

    def update_downloaders_ffmpeg(self):
        """Обновляет загрузчики с учетом наличия FFmpeg"""
        if self.has_ffmpeg and self.ffmpeg_manager.ffmpeg_path:
            ffmpeg_path = str(self.ffmpeg_manager.ffmpeg_path)
            ffprobe_path = str(self.ffmpeg_manager.ffprobe_path) if self.ffmpeg_manager.ffprobe_path else None

            # Для YouTube загрузчика
            if 'youtube' in self.downloaders:
                self.downloaders['youtube'].set_ffmpeg_path(ffmpeg_path, ffprobe_path)

            self.logger.info("✅ Загрузчики обновлены для работы с FFmpeg")

    def get_ffmpeg_version(self) -> str:
        """Получает версию FFmpeg"""
        try:
            import subprocess
            if self.ffmpeg_manager.ffmpeg_path and self.ffmpeg_manager.ffmpeg_path.exists():
                result = subprocess.run(
                    [str(self.ffmpeg_manager.ffmpeg_path), '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Первая строка содержит версию
                    first_line = result.stdout.split('\n')[0]
                    return first_line
        except Exception as e:
            self.logger.error(f"Ошибка получения версии FFmpeg: {e}")
        return "Неизвестно"

    def update_status_bar(self):
        """Обновляет строку состояния"""
        queue_count = len(self.queue_frame.get_items())
        status = f" Загрузка..." if self.running else " Готов к работе"
        ffmpeg_status = "✅ FFmpeg" if self.has_ffmpeg else "⚠️ FFmpeg"
        self.status_bar.configure(
            text=f"{status} | В очереди: {queue_count} | {ffmpeg_status}"
        )

    def update_status_loop(self):
        """Периодически обновляет строку состояния"""
        self.update_status_bar()
        self.after(1000, self.update_status_loop)  # Обновляем каждую секунду

    def on_closing(self):
        """Обработка закрытия окна"""
        if self.running:
            if not messagebox.askyesno(
                "Выход",
                "Загрузка ещё выполняется. Прервать и выйти?"
            ):
                return
            self.stop_downloads()

        self.destroy()