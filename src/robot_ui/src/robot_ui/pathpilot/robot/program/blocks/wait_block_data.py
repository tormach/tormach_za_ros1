from PySide6.QtCore import QEnum, Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.wait_block import WaitType

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class WaitBlockData(BlockData):
    """
    Provides a read-only interface to a wait block in QML.
    """

    QEnum(WaitType)

    waitTypeChanged = Signal()
    sleepTimeChanged = Signal()
    digitalInNrChanged = Signal()
    digitalInNameChanged = Signal()
    digitalInStateChanged = Signal()
    optionalChanged = Signal()
    activeChanged = Signal()

    TYPES = 'wait'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.waitTypeChanged)
        self.dataChanged.connect(self.sleepTimeChanged)
        self.dataChanged.connect(self.digitalInNrChanged)
        self.dataChanged.connect(self.digitalInNameChanged)
        self.dataChanged.connect(self.digitalInStateChanged)
        self.dataChanged.connect(self.optionalChanged)
        self.dataChanged.connect(self.activeChanged)

    @Property(int, notify=waitTypeChanged)
    def waitType(self):
        return self._get_block_data('wait_type', WaitType.Sleep, self.TYPES)

    @Property(float, notify=sleepTimeChanged)
    def sleepTime(self):
        return self._get_block_data('sleep_time', 0.0, self.TYPES)

    @Property(int, notify=digitalInNrChanged)
    def digitalInNr(self):
        return self._get_block_data('digital_in_nr', 0.0, self.TYPES)

    @Property(str, notify=digitalInNameChanged)
    def digitalInName(self):
        return self._get_block_data('digital_in_name', '', self.TYPES)

    @Property(bool, notify=digitalInStateChanged)
    def digitalInState(self):
        return self._get_block_data('digital_in_state', 0.0, self.TYPES)

    @Property(bool, notify=optionalChanged)
    def optional(self):
        return self._get_block_data('optional', False, self.TYPES)

    @Property(bool, notify=activeChanged)
    def active(self):
        return self._get_block_data('active', False, self.TYPES)
