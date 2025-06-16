from PySide6.QtCore import QEnum, Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.frame_block import FrameType
from robot_command.program_blocks.rpl_block import RPLBlockScopeWalker

from .block_data import BlockData, IndexInvalidError

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FrameBlockData(BlockData):
    """
    Provides a read-only interface to frame block in QML.
    """

    QEnum(FrameType)

    frameTypeChanged = Signal()
    nameChanged = Signal()
    poseChanged = Signal()
    positionChanged = Signal()
    orientationChanged = Signal()
    lastFrameChanged = Signal()

    TYPES = 'frame'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.frameTypeChanged)
        self.dataChanged.connect(self.nameChanged)
        self.dataChanged.connect(self.poseChanged)
        self.dataChanged.connect(self.positionChanged)
        self.dataChanged.connect(self.orientationChanged)
        self.dataChanged.connect(self.lastFrameChanged)

    @Property(int, notify=frameTypeChanged)
    def frameType(self):
        return self._get_block_data(
            'frame_type', FrameType.ChangeUserFrame, self.TYPES
        )

    @Property(str, notify=nameChanged)
    def name(self):
        return self._get_block_data('name', '', self.TYPES)

    @Property('QVariant', notify=poseChanged)
    def pose(self):
        return self._get_block_data('pose', '', self.TYPES)

    @Property('QVariant', notify=positionChanged)
    def position(self):
        return self._get_block_data('position', '', self.TYPES)

    @Property('QVariant', notify=orientationChanged)
    def orientation(self):
        return self._get_block_data('orientation', '', self.TYPES)

    @Property(str, notify=lastFrameChanged)
    def lastFrame(self):
        try:
            block = self._get_block(self._uuid)
        except IndexInvalidError:
            return ''
        except Exception:  # hotfix, the previous exception doesn't work
            return ''

        for n in RPLBlockScopeWalker(block, reverse=True):
            if n.type == 'frame' and n.frame_type == FrameType.ChangeUserFrame:
                return n.name
        return ''
