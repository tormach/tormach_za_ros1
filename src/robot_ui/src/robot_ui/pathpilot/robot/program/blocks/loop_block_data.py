from PySide6.QtCore import QEnum, Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.loop_block import LoopType

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class LoopBlockData(BlockData):
    """
    Provides a read-only interface to loop block in QML.
    """

    QEnum(LoopType)

    loopTypeChanged = Signal()
    variableChanged = Signal()
    countChanged = Signal()
    conditionChanged = Signal()

    TYPES = 'loop'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.loopTypeChanged)
        self.dataChanged.connect(self.variableChanged)
        self.dataChanged.connect(self.countChanged)
        self.dataChanged.connect(self.conditionChanged)

    @Property(int, notify=loopTypeChanged)
    def loopType(self):
        return self._get_block_data('loop_type', LoopType.WhileLoop, self.TYPES)

    @Property(str, notify=variableChanged)
    def variable(self):
        return self._get_block_data('variable', '', self.TYPES)

    @Property(int, notify=countChanged)
    def count(self):
        return self._get_block_data('count', 0, self.TYPES)

    @Property(str, notify=conditionChanged)
    def condition(self):
        return self._get_block_data('condition', '', self.TYPES)
