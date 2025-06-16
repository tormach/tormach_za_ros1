from PySide6.QtCore import QEnum, Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.comment_block import CommentType

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class CommentBlockData(BlockData):
    """
    Provides a read-only interface to a comment block in QML.
    """

    QEnum(CommentType)

    commentTypeChanged = Signal()
    textChanged = Signal()

    TYPES = 'comment'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.textChanged)

    @Property(int, notify=commentTypeChanged)
    def commentType(self):
        return self._get_block_data(
            'comment_type', CommentType.LineComment, self.TYPES
        )

    @Property(str, notify=textChanged)
    def text(self):
        return self._get_block_data('text', '', self.TYPES)
