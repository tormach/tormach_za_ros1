import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtQuick import QQuickImageProvider

from .resource_paths import TOOL_TIP_IMAGE_PATH


class ToolTipImageProvider(QQuickImageProvider):
    """
    Provides tool tip images using the tool tip manager.
    """

    def __init__(self):
        super().__init__(QQuickImageProvider.Pixmap)

    def requestPixmap(self, id_: str, size: QSize, requested_size: QSize):
        image_path = os.path.join(TOOL_TIP_IMAGE_PATH, id_)
        if os.path.exists(image_path):
            pixmap = QPixmap()
            pixmap.load(image_path)
            requested = False
            if requested_size.width() > 0:
                requested = True
                width = requested_size.width()
            else:
                width = pixmap.size().width()
            if requested_size.height() > 0:
                requested = True
                height = requested_size.height()
            else:
                height = pixmap.size().height()
            if requested:
                pixmap = pixmap.scaled(
                    width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
        else:
            width = requested_size.width() if requested_size.width() > 0 else 64
            height = (
                requested_size.height() if requested_size.height() > 0 else 64
            )
            pixmap = QPixmap(width, height)
            painter = QPainter(pixmap)
            painter.fillRect(
                2, 2, max(1, width - 4), max(1, height - 4), Qt.white
            )
            painter.setPen(Qt.black)
            painter.drawText(width / 2, 2 * height / 3, "?")

        size.setWidth(width)
        size.setHeight(height)
        return pixmap
