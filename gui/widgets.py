"""
Пользовательские виджеты для интерфейса
"""
import customtkinter as ctk
import tkinter as tk  # Добавляем для контекстного меню
from typing import Optional, Callable

class DownloadProgressFrame(ctk.CTkFrame):
    """Фрейм с прогресс баром для отображения загрузки"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Название файла
        self.title_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        self.title_label.pack(fill="x", padx=5, pady=(5, 2))

        # Прогресс бар
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=5, pady=2)
        self.progress_bar.set(0)

        # Статус и проценты
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=5, pady=(0, 5))

        self.status_label = ctk.CTkLabel(
            info_frame,
            text="Ожидание...",
            font=ctk.CTkFont(size=10),
            anchor="w"
        )
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(
            info_frame,
            text="0%",
            font=ctk.CTkFont(size=10),
            anchor="e"
        )
        self.percent_label.pack(side="right")

        # Скрываем по умолчанию
        self.pack_forget()

    def show(self, title: str):
        """Показывает прогресс бар с заголовком"""
        self.title_label.configure(text=title)
        self.progress_bar.set(0)
        self.status_label.configure(text="Подготовка...")
        self.percent_label.configure(text="0%")
        self.pack(fill="x", padx=10, pady=5)

    def hide(self):
        """Скрывает прогресс бар"""
        self.pack_forget()

    def update_progress(self, value: int, status: str = None):
        """Обновляет прогресс"""
        progress = value / 100
        self.progress_bar.set(progress)
        self.percent_label.configure(text=f"{value}%")

        if status:
            self.status_label.configure(text=status)

        self.update_idletasks()

    def set_status(self, status: str):
        """Устанавливает статус"""
        self.status_label.configure(text=status)
        self.update_idletasks()

class ProgressCell(ctk.CTkFrame):
    """Виджет для отображения прогресса загрузки в таблице"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Прогресс бар
        self.progress_bar = ctk.CTkProgressBar(self, width=100)
        self.progress_bar.pack(side="left", padx=(0, 5))
        self.progress_bar.set(0)

        # Метка с процентами
        self.percent_label = ctk.CTkLabel(self, text="0%", width=35)
        self.percent_label.pack(side="left")

    def set_progress(self, value: float):
        """Устанавливает прогресс (от 0 до 1)"""
        self.progress_bar.set(value)
        self.percent_label.configure(text=f"{int(value * 100)}%")


class StatusBadge(ctk.CTkLabel):
    """Виджет для отображения статуса с цветом"""

    STATUS_COLORS = {
        "в очереди": ("gray", "light gray"),
        "загружается": ("orange", "yellow"),
        "готово": ("green", "light green"),
        "ошибка": ("red", "#FFB6C1"),
        "остановлено": ("gray", "light gray"),
    }

    def __init__(self, master, status: str = "в очереди", **kwargs):
        super().__init__(master, text=status, **kwargs)
        self.update_status(status)

    def update_status(self, status: str):
        """Обновляет статус и цвет"""
        self.configure(text=status)

        if status in self.STATUS_COLORS:
            fg_color, text_color = self.STATUS_COLORS[status]
            self.configure(fg_color=fg_color, text_color=text_color)
        else:
            self.configure(fg_color="gray", text_color="white")


class URLInput(ctk.CTkTextbox):
    """Кастомное поле для ввода URL с подсказкой и поддержкой Ctrl+V"""

    def __init__(self, master, placeholder: str = "Вставьте ссылки (по одной на строку)", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_active = True

        # Привязываем события
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.bind("<Control-v>", self.paste_text)
        self.bind("<Control-V>", self.paste_text)
        self.bind("<Button-3>", self.show_context_menu)
        self.bind("<<Paste>>", self.paste_text)  # Добавляем событие вставки

        # Создаем контекстное меню
        self.context_menu = None
        self.create_context_menu()

        # Показываем placeholder
        self.show_placeholder()

    def create_context_menu(self):
        """Создает контекстное меню"""
        try:
            import tkinter as tk
            self.context_menu = tk.Menu(self, tearoff=0)
            self.context_menu.add_command(label="Вставить", command=self.paste_from_menu, accelerator="Ctrl+V")
            self.context_menu.add_command(label="Копировать", command=self.copy_text, accelerator="Ctrl+C")
            self.context_menu.add_command(label="Вырезать", command=self.cut_text, accelerator="Ctrl+X")
            self.context_menu.add_separator()
            self.context_menu.add_command(label="Выделить всё", command=self.select_all, accelerator="Ctrl+A")
        except:
            pass

    def show_context_menu(self, event):
        """Показывает контекстное меню"""
        if self.context_menu:
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def paste_text(self, event=None):
        """Вставляет текст из буфера обмена"""
        try:
            # Пробуем получить текст из буфера обмена разными способами
            clipboard_text = None

            # Способ 1: через clipboard_get()
            try:
                clipboard_text = self.clipboard_get()
            except:
                pass

            # Способ 2: через tkinter
            if not clipboard_text:
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    root.withdraw()
                    clipboard_text = root.clipboard_get()
                    root.destroy()
                except:
                    pass

            if clipboard_text:
                # Если активен placeholder, очищаем поле
                if self.placeholder_active:
                    self.delete("0.0", "end")
                    self.configure(text_color=("black", "white"))
                    self.placeholder_active = False

                # Вставляем текст в текущую позицию курсора
                self.insert("insert", clipboard_text)

            return "break"  # Предотвращаем дальнейшую обработку события
        except Exception as e:
            print(f"Paste error: {e}")
            return "break"

    def paste_from_menu(self):
        """Вставка из контекстного меню"""
        self.paste_text()

    def copy_text(self):
        """Копирует выделенный текст"""
        try:
            selected_text = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(selected_text)
        except:
            pass

    def cut_text(self):
        """Вырезает выделенный текст"""
        try:
            selected_text = self.selection_get()
            self.clipboard_clear()
            self.clipboard_append(selected_text)
            self.delete("sel.first", "sel.last")
        except:
            pass

    def select_all(self):
        """Выделяет весь текст"""
        self.tag_add("sel", "0.0", "end")

    def show_placeholder(self):
        """Показывает placeholder"""
        self.delete("0.0", "end")
        self.insert("0.0", self.placeholder)
        self.configure(text_color="gray")
        self.placeholder_active = True

    def on_focus_in(self, event):
        """При получении фокуса убираем placeholder"""
        if self.placeholder_active:
            self.delete("0.0", "end")
            self.configure(text_color=("black", "white"))
            self.placeholder_active = False

    def on_focus_out(self, event):
        """При потере фокуса показываем placeholder если поле пустое"""
        if not self.get("0.0", "end").strip():
            self.show_placeholder()

    def get_urls(self) -> list:
        """Возвращает список URL из поля"""
        if self.placeholder_active:
            return []

        text = self.get("0.0", "end").strip()
        # Разделяем по строкам и фильтруем пустые
        urls = [url.strip() for url in text.split('\n') if url.strip()]
        return urls

    def set_urls(self, urls: list):
        """Устанавливает список URL в поле"""
        self.delete("0.0", "end")
        self.insert("0.0", '\n'.join(urls))
        self.configure(text_color=("black", "white"))
        self.placeholder_active = False


class LogViewer(ctk.CTkTextbox):
    """Виджет для отображения логов с автоскроллом"""

    def __init__(self, master, max_lines: int = 1000, **kwargs):
        super().__init__(master, **kwargs)
        self.max_lines = max_lines
        self.lines = []

        # Отключаем редактирование
        self.configure(state="disabled")

    def add_line(self, text: str):
        """Добавляет строку в лог"""
        # Включаем редактирование
        self.configure(state="normal")

        # Добавляем строку
        self.insert("end", text + "\n")
        self.lines.append(text)

        # Ограничиваем количество строк
        if len(self.lines) > self.max_lines:
            self.delete("0.0", "1.0")
            self.lines.pop(0)

        # Скроллим вниз
        self.see("end")

        # Выключаем редактирование
        self.configure(state="disabled")

    def clear(self):
        """Очищает лог"""
        self.configure(state="normal")
        self.delete("0.0", "end")
        self.configure(state="disabled")
        self.lines.clear()