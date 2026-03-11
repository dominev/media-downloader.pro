"""
Инициализация GUI модуля
"""
from .app import DownloaderApp
from .frames import SettingsFrame, InstagramAuthFrame, QueueFrame
from .widgets import URLInput, LogViewer, StatusBadge, ProgressCell

__all__ = [
    'DownloaderApp',
    'SettingsFrame',
    'InstagramAuthFrame',
    'QueueFrame',
    'URLInput',
    'LogViewer',
    'StatusBadge',
    'ProgressCell'
]