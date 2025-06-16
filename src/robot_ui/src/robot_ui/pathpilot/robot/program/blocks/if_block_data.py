from PySide6.QtCore import Signal, Property
from PySide6.QtQml import QmlElement

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class IfBlockData(BlockData):
    """
    Provides a read-only interface to move block in QML.
    """

    conditionChanged = Signal()
    hasElseChanged = Signal()

    TYPES = 'if', 'elif', 'else'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.conditionChanged)
        self.dataChanged.connect(self.hasElseChanged)

    @Property(str, notify=conditionChanged)
    def condition(self):
        return self._get_block_data('condition', '', self.TYPES)

    @Property(bool, notify=hasElseChanged)
    def hasElse(self):
        return self._get_block_data('has_else', False, self.TYPES)
