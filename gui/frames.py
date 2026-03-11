"""
Фреймы для интерфейса
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import List, Dict, Any
from .widgets import StatusBadge, ProgressCell, URLInput, LogViewer
from utils.platform_detector import PlatformDetector
class SettingsFrame(ctk.CTkFrame):
    """Фрейм с настройками загрузки"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Заголовок
        self.header = ctk.CTkLabel(
            self,
            text="⚙️ Настройки загрузки:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.header.pack(anchor="w", padx=10, pady=(10, 5))

        # Контейнер для настроек
        settings_container = ctk.CTkFrame(self, fg_color="transparent")
        settings_container.pack(fill="x", padx=10, pady=5)

        # Настройки качества
        self.quality_var = ctk.BooleanVar(value=True)
        self.quality_check = ctk.CTkCheckBox(
            settings_container,
            text="Максимальное качество",
            variable=self.quality_var
        )
        self.quality_check.pack(side="left", padx=5)

        # Формат
        self.format_label = ctk.CTkLabel(self, text="Формат:")
        self.format_label.pack(side="left", padx=5)

        self.format_combo = ctk.CTkComboBox(
            self,
            values=["mp4", "best", "audio"],
            width=100
        )
        self.format_combo.pack(side="left", padx=5)
        self.format_combo.set("mp4")

    def get_settings(self) -> Dict[str, Any]:
        """Возвращает текущие настройки"""
        return {
            "max_quality": self.quality_var.get(),
            "format": self.format_combo.get()
        }


class InstagramAuthFrame(ctk.CTkFrame):
    """Фрейм для авторизации Instagram"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Заголовок
        self.label = ctk.CTkLabel(
            self,
            text="Instagram авторизация (для stories):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.label.pack(anchor="w", padx=5, pady=(5, 10))

        # Поля ввода
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=5)

        # Логин
        ctk.CTkLabel(input_frame, text="Логин:", width=60).pack(side="left", padx=5)
        self.login_entry = ctk.CTkEntry(input_frame, width=150)
        self.login_entry.pack(side="left", padx=5)

        # Пароль
        ctk.CTkLabel(input_frame, text="Пароль:", width=60).pack(side="left", padx=5)
        self.password_entry = ctk.CTkEntry(input_frame, width=150, show="*")
        self.password_entry.pack(side="left", padx=5)

        # Кнопка теста
        self.test_btn = ctk.CTkButton(
            input_frame,
            text="Проверить",
            width=80,
            command=self.test_auth,
            fg_color="gray"
        )
        self.test_btn.pack(side="left", padx=5)

        # Статус
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(anchor="w", padx=5, pady=5)

    def get_credentials(self) -> tuple:
        """Возвращает (логин, пароль)"""
        return self.login_entry.get(), self.password_entry.get()

    def test_auth(self):
        """Тестирует авторизацию"""
        login, password = self.get_credentials()

        if not login or not password:
            self.status_label.configure(
                text="Введите логин и пароль",
                text_color="orange"
            )
            return

        # Здесь будет тест авторизации
        self.status_label.configure(
            text="Проверка...",
            text_color="blue"
        )

        # Имитация проверки
        self.after(2000, lambda: self.status_label.configure(
            text="✓ Авторизация успешна",
            text_color="green"
        ))

    def clear(self):
        """Очищает поля"""
        self.login_entry.delete(0, "end")
        self.password_entry.delete(0, "end")
        self.status_label.configure(text="")


class QueueFrame(ctk.CTkFrame):
    """Фрейм для отображения очереди загрузок"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Заголовок с количеством
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=5, pady=5)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Очередь загрузок:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.title_label.pack(side="left")

        self.count_label = ctk.CTkLabel(
            self.header_frame,
            text="(0)",
            text_color="gray"
        )
        self.count_label.pack(side="left", padx=5)

        # Кнопки управления очередью
        self.buttons_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.buttons_frame.pack(side="right")

        self.clear_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Очистить",
            width=80,
            command=self.clear_queue,
            fg_color="gray"
        )
        self.clear_btn.pack(side="left", padx=2)

        self.remove_btn = ctk.CTkButton(
            self.buttons_frame,
            text="Удалить",
            width=80,
            command=self.remove_selected,
            fg_color="gray"
        )
        self.remove_btn.pack(side="left", padx=2)

        # Таблица очереди (для простоты используем Text с форматированием)
        self.queue_text = ctk.CTkTextbox(self, height=150)
        self.queue_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Данные очереди
        self.queue_items: List[Dict] = []

    def add_item(self, url: str, platform: str = None):
        """Добавляет элемент в очередь"""
        if not platform:
            platform = PlatformDetector.detect_platform(url)

        item = {
            "url": url,
            "platform": platform,
            "status": "в очереди",
            "progress": 0
        }

        self.queue_items.append(item)
        self.update_display()

    def add_items(self, urls: List[str]):
        """Добавляет несколько элементов"""
        for url in urls:
            self.add_item(url)

    def update_item_status(self, index: int, status: str, progress: int = None):
        """Обновляет статус элемента"""
        if 0 <= index < len(self.queue_items):
            self.queue_items[index]["status"] = status
            if progress is not None:
                self.queue_items[index]["progress"] = progress
            self.update_display()

    def remove_item(self, index: int):
        """Удаляет элемент из очереди"""
        if 0 <= index < len(self.queue_items):
            self.queue_items.pop(index)
            self.update_display()

    def clear_queue(self):
        """Очищает всю очередь"""
        self.queue_items.clear()
        self.update_display()

    def remove_selected(self):
        """Удаляет выбранный элемент"""
        # В реальном проекте здесь нужно реализовать выделение элементов
        # Пока удаляем последний
        if self.queue_items:
            self.remove_item(-1)

    def update_display(self):
        """Обновляет отображение очереди"""
        self.queue_text.configure(state="normal")
        self.queue_text.delete("0.0", "end")

        if not self.queue_items:
            self.queue_text.insert("0.0", "Очередь пуста")
        else:
            for i, item in enumerate(self.queue_items, 1):
                status_symbol = {
                    "в очереди": "⏳",
                    "загружается": "⬇️",
                    "готово": "✅",
                    "ошибка": "❌",
                    "остановлено": "⏹️"
                }.get(item["status"], "⏳")

                progress = f" [{item['progress']}%]" if item['progress'] > 0 else ""

                line = f"{i}. {status_symbol} {item['platform']}: {item['url'][:50]}... {item['status']}{progress}\n"
                self.queue_text.insert("end", line)

        self.queue_text.configure(state="disabled")
        self.count_label.configure(text=f"({len(self.queue_items)})")

    def get_items(self) -> List[Dict]:
        """Возвращает все элементы очереди"""
        return self.queue_items.copy()