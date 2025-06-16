import re

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtGui import QFont, QColor
from PySide6.QtQml import QmlElement

from ..qt_helpers import MultiSlot
from .tool_tip_manager import ToolTipManager, ToolTipData

QML_IMPORT_NAME = 'pathpilot.controls'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ToolTipInfo(QObject):
    """
    Gathers all info required to present a tool tip.
    """

    itemIdChanged = Signal(str)
    headerFontChanged = Signal()
    bodyFontChanged = Signal()
    backgroundColorChanged = Signal()
    shortTextIdChanged = Signal()
    longTextIdChanged = Signal()
    headerColorChanged = Signal()
    bodyColorChanged = Signal()
    longWidthChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._manager = ToolTipManager()
        self._item_id = ''
        self._data = ToolTipData()
        self._img_re = re.compile(r'(<\s*img\s*>(\d+)</\s*img\s*>)')

        self.itemIdChanged.connect(self._fetch_data)

    @Slot(str)
    def _fetch_data(self, id_):
        self._data = self._manager.get_item_data(id_)
        self.headerFontChanged.emit()
        self.bodyFontChanged.emit()
        self.backgroundColorChanged.emit()
        self.shortTextIdChanged.emit()
        self.longTextIdChanged.emit()
        self.headerColorChanged.emit()
        self.bodyColorChanged.emit()

    @MultiSlot(str, [None, str], result=str)
    def prepareBodyText(self, text, header=''):
        matches = self._img_re.findall(text)

        # replace header tokens
        out = text.replace('@@', header)

        # replace img tags
        for complete, n in matches:
            id_ = int(n) - 1
            if not 0 <= id_ < len(self._data.images):
                continue
            image = self._data.images[id_]
            img_tag = (
                '<img src="image://toolTipImageProvider/{}"></img>'.format(
                    image
                )
            )
            out = out.replace(complete, img_tag, 1)

        return out

    @Property(str, notify=itemIdChanged)
    def itemId(self):
        return self._item_id

    @itemId.setter
    def itemId(self, value):
        if value == self._item_id:
            return
        self._item_id = value
        self.itemIdChanged.emit(value)

    @Property(QFont, notify=headerFontChanged)
    def headerFont(self):
        return self._data.header_font

    @Property(QColor, notify=headerColorChanged)
    def headerColor(self):
        return self._data.header_color

    @Property(QColor, notify=bodyColorChanged)
    def bodyColor(self):
        return self._data.body_color

    @Property(QFont, notify=bodyFontChanged)
    def bodyFont(self):
        return self._data.body_font

    @Property(QColor, notify=backgroundColorChanged)
    def backgroundColor(self):
        return self._data.background_color

    @Property(str, notify=shortTextIdChanged)
    def shortTextId(self):
        return self._data.shorttext_id

    @Property(str, notify=longTextIdChanged)
    def longTextId(self):
        return self._data.longtext_id

    @Property(int, notify=longWidthChanged)
    def longWidth(self):
        return self._data.long_width
