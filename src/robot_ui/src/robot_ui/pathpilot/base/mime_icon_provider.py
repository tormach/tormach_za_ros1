import os

from PySide6.QtCore import QMimeDatabase, QSize, QByteArray
from PySide6.QtGui import QIcon
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtWidgets import QFileIconProvider


class MimeIconProvider(QQuickImageProvider):
    """
    Provides icons/images based on the MIME type of a file.
    """

    def __init__(self, theme="oxygen"):
        super().__init__(QQuickImageProvider.Pixmap)

        self._mime_db = QMimeDatabase()
        self._provider = QFileIconProvider()

        QIcon.setThemeName(theme)

    def requestPixmap(self, id_: str, size: QSize, requested_size: QSize):
        width = requested_size.width() if requested_size.width() > 0 else 64
        height = width
        if id_.startswith('/'):
            if not os.path.exists(id_):
                icon = self._provider.icon(QFileIconProvider.File)
            elif os.path.isdir(id_):
                icon = self._provider.icon(QFileIconProvider.Folder)
            else:
                mime = self._mime_db.mimeTypeForFile(id_)
                if QIcon.hasThemeIcon(mime.iconName()):
                    icon = QIcon.fromTheme(mime.iconName())
                else:
                    icon = self._provider.icon(QFileIconProvider.File)
        else:
            if id_.endswith('/'):
                icon = self._provider.icon(QFileIconProvider.Folder)
            else:
                mime = self._mime_db.mimeTypeForFileNameAndData(
                    id_, QByteArray(b" ")
                )
                if QIcon.hasThemeIcon(mime.iconName()):
                    icon = QIcon.fromTheme(mime.iconName())
                else:
                    icon = self._provider.icon(QFileIconProvider.File)

        size.setWidth(width)
        size.setHeight(height)
        return icon.pixmap(width, height)
