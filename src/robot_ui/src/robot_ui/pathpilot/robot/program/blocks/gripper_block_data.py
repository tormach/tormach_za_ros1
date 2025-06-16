from PySide6.QtCore import Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks import GripperBlock
from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class GripperBlockData(BlockData):
    """
    Provides a read-only interface to gripper block in QML.
    """

    positionChanged = Signal()
    effortChanged = Signal()
    waitChanged = Signal()

    TYPES = ('actuate_gripper',)

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.dataChanged.connect(self.positionChanged)
        self.dataChanged.connect(self.effortChanged)
        self.dataChanged.connect(self.waitChanged)

    @Property(float, notify=positionChanged)
    def position(self):
        return self._get_block_data(
            'position', GripperBlock.DEFAULT_POSITION, self.TYPES
        )

    @Property(float, notify=effortChanged)
    def effort(self):
        return self._get_block_data(
            'effort', GripperBlock.DEFAULT_EFFORT, self.TYPES
        )

    @Property(float, notify=waitChanged)
    def wait(self):
        return self._get_block_data(
            'wait', GripperBlock.DEFAULT_WAIT, self.TYPES
        )
