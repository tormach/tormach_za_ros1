from PySide6.QtCore import QEnum, Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.notify_block import NotifyType

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class NotifyBlockData(BlockData):
    """
    Provides a read-only interface to a notify block in QML.
    """

    QEnum(NotifyType)

    notifyTypeChanged = Signal()
    messageChanged = Signal()
    imagePathChanged = Signal()

    TYPES = 'notify'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.notifyTypeChanged)
        self.dataChanged.connect(self.messageChanged)
        self.dataChanged.connect(self.imagePathChanged)

    @Property(int, notify=notifyTypeChanged)
    def notifyType(self):
        return self._get_block_data(
            'notify_type', NotifyType.Notification, self.TYPES
        )

    @Property(str, notify=messageChanged)
    def message(self):
        return self._get_block_data('message', '', self.TYPES)

    @Property(str, notify=imagePathChanged)
    def imagePath(self):
        return self._get_block_data('image_path', '', self.TYPES)
