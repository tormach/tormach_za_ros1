from PySide6.QtCore import QEnum, Signal, Property
from PySide6.QtQml import QmlElement

from robot_command.program_blocks.set_block import SetType

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class SetBlockData(BlockData):
    """
    Provides a read-only interface to a wait block in QML.
    """

    QEnum(SetType)

    setTypeChanged = Signal()
    digitalOutStateChanged = Signal()
    digitalOutNrChanged = Signal()
    digitalOutNameChanged = Signal()

    TYPES = 'set'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.setTypeChanged)
        self.dataChanged.connect(self.digitalOutNrChanged)
        self.dataChanged.connect(self.digitalOutNameChanged)
        self.dataChanged.connect(self.digitalOutStateChanged)

    @Property(int, notify=setTypeChanged)
    def setType(self):
        return self._get_block_data(
            'set_type', SetType.SetDigitalOut, self.TYPES
        )

    @Property(int, notify=digitalOutNrChanged)
    def digitalOutNr(self):
        return self._get_block_data('digital_out_nr', 0.0, self.TYPES)

    @Property(str, notify=digitalOutNameChanged)
    def digitalOutName(self):
        return self._get_block_data('digital_out_name', '', self.TYPES)

    @Property(bool, notify=digitalOutStateChanged)
    def digitalOutState(self):
        return self._get_block_data('digital_out_state', 0.0, self.TYPES)
