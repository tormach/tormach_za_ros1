from PySide6.QtCore import Signal, Property
from PySide6.QtQml import QmlElement

from .block_data import BlockData

QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class SubProgramBlockData(BlockData):
    """
    Provides a read-only interface to program block and call block in QML.
    """

    nameChanged = Signal()
    subProgramNamesChanged = Signal()
    quickcallableSubProgramNamesChanged = Signal()

    TYPES = 'subprogram', 'call'

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.dataChanged.connect(self.nameChanged)
        self.dataChanged.connect(self.subProgramNamesChanged)
        self.dataChanged.connect(self.quickcallableSubProgramNamesChanged)

    @Property(str, notify=nameChanged)
    def name(self):
        return self._get_block_data('name', '', self.TYPES)

    @Property('QStringList', notify=subProgramNamesChanged)
    def subProgramNames(self):
        return self._get_subprogram_names(lambda n: n.type == 'subprogram')

    @Property('QStringList', notify=quickcallableSubProgramNamesChanged)
    def quickcallableSubProgramNames(self):
        def hasValidParameters(n):
            valid = False

            # Allow case where all parameters have defaults
            if n.defaults is not None and n.parameters is not None:
                valid = all(
                    default is not None for default in n.defaults
                ) and len(n.defaults) == len(n.parameters)

            return valid

        return self._get_subprogram_names(
            lambda n: n.type == 'subprogram' and hasValidParameters(n)
        )

    def _get_subprogram_names(self, filter_func):
        if self._program is None:
            return []
        root_block = self._program.root_block
        if root_block is None:
            return []
        return sorted([n.name for n in root_block.children if filter_func(n)])
