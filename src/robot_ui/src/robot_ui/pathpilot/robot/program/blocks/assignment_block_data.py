from PySide6.QtCore import Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.rpl_block import RPLBlockScopeWalker

from .block_data import BlockData, IndexInvalidError

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class AssignmentBlockData(BlockData):
    """
    Provides a read-only interface to a assignment block in QML.
    """

    nameChanged = Signal()
    operatorChanged = Signal()
    expressionChanged = Signal()
    variableNamesChanged = Signal()

    TYPES = 'assignment'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.nameChanged)
        self.dataChanged.connect(self.operatorChanged)
        self.dataChanged.connect(self.expressionChanged)
        self.dataChanged.connect(self.variableNamesChanged)

    @Property(str, notify=nameChanged)
    def name(self):
        return self._get_block_data('name', '', self.TYPES)

    @Property(str, notify=operatorChanged)
    def operator(self):
        return self._get_block_data('operator', '=', self.TYPES)

    @Property(str, notify=expressionChanged)
    def expression(self):
        return self._get_block_data('expression', '', self.TYPES)

    @Property('QStringList', notify=variableNamesChanged)
    def variableNames(self):
        try:
            block = BlockData._get_block(self, self._uuid)
        except IndexInvalidError:
            return []
        except Exception:  # weirdly, the previous exception doesn't work
            return []

        return list(
            {
                n.name
                for n in RPLBlockScopeWalker(block)
                if n.type == 'assignment'
            }
        )
