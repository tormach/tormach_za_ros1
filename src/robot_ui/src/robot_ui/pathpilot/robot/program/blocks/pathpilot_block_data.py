from PySide6.QtCore import QEnum, Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.pathpilot_block import CommandType

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class PathPilotBlockData(BlockData):
    """
    Provides a read-only interface to a pathpilot block in QML.
    """

    QEnum(CommandType)

    commandTypeChanged = Signal()
    commandLineChanged = Signal()
    instanceChanged = Signal()
    stateChanged = Signal()

    TYPES = 'pathpilot'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.commandTypeChanged)
        self.dataChanged.connect(self.commandLineChanged)
        self.dataChanged.connect(self.instanceChanged)
        self.dataChanged.connect(self.stateChanged)

    @Property(int, notify=commandTypeChanged)
    def commandType(self):
        return self._get_block_data(
            'command_type', CommandType.MdiCommand, self.TYPES
        )

    @Property(str, notify=commandLineChanged)
    def commandLine(self):
        return self._get_block_data('command_line', '', self.TYPES)

    @Property(str, notify=instanceChanged)
    def instance(self):
        return self._get_block_data('instance', '', self.TYPES)

    @Property(str, notify=stateChanged)
    def state(self):
        return self._get_block_data('state', '', self.TYPES)
