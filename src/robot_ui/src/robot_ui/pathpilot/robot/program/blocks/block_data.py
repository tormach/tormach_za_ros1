import contextlib

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from ..robot_program import RobotProgram


class BlockInvalidError(Exception):
    pass


class IndexInvalidError(BlockInvalidError):
    pass


class TypeInvalidError(BlockInvalidError):
    pass


QML_IMPORT_NAME = 'pathpilot.robot.program.blocks'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class BlockData(QObject):
    """
    Provides a read-only interface to the data of a program block for QML.
    This component is meant to be used in combination with the ProgramTreeModel.
    """

    DEFAULT_POS = {'line': 0, 'column': 0}
    TYPES = ()  # need to be over-written by subclass

    programChanged = Signal()
    uuidChanged = Signal(str)
    typeChanged = Signal()
    nextUuidChanged = Signal()
    previousUuidChanged = Signal()
    validChanged = Signal()
    startPosChanged = Signal()
    endPosChanged = Signal()
    codeChanged = Signal()
    levelChanged = Signal()
    dataChanged = Signal()
    typeMatchesChanged = Signal()
    disabledChanged = Signal()

    def __init__(self, parent=None, uuid='', program=None):
        super().__init__(parent)

        self._uuid = uuid
        self._program: RobotProgram = program

        self.uuidChanged.connect(self.dataChanged)
        self.programChanged.connect(self.dataChanged)
        self.dataChanged.connect(self.typeChanged)
        self.dataChanged.connect(self.nextUuidChanged)
        self.dataChanged.connect(self.previousUuidChanged)
        self.dataChanged.connect(self.validChanged)
        self.dataChanged.connect(self.startPosChanged)
        self.dataChanged.connect(self.endPosChanged)
        self.dataChanged.connect(self.codeChanged)
        self.dataChanged.connect(self.levelChanged)
        self.dataChanged.connect(self.typeMatchesChanged)
        self.dataChanged.connect(self.disabledChanged)

    @Property(QObject, notify=programChanged)  # RobotProgram
    def program(self):
        return self._program

    @program.setter
    def program(self, new_program):
        if new_program == self._program:
            return
        old_program, self._program = self._program, new_program
        self.programChanged.emit()
        if old_program:
            with contextlib.suppress(RuntimeError):
                old_program.blockUpdated.disconnect(self._on_block_updated)
                old_program.blockMoved.disconnect(self._on_block_moved)
                old_program.blockRemoved.disconnect(self._on_block_removed)
                old_program.reset.disconnect(self._on_program_reset)
        if new_program:
            new_program.blockUpdated.connect(self._on_block_updated)
            new_program.blockMoved.connect(self._on_block_moved)
            new_program.blockRemoved.connect(self._on_block_removed)
            new_program.reset.connect(self._on_program_reset)

    @Property(bool, notify=validChanged)
    def valid(self):
        if not self._program:
            return False
        return self._program.get_block(self._uuid) is not None

    @Property(str, notify=typeChanged)
    def type(self):
        return self._get_block_data('type', '')

    @Property(bool, notify=typeMatchesChanged)
    def typeMatches(self):
        try:
            block = self._get_block(self._uuid)
        except IndexInvalidError:
            return False
        else:
            return block.type in self.TYPES

    @Property(str, notify=uuidChanged)
    def uuid(self):
        return self._uuid

    @uuid.setter
    def uuid(self, value):
        if value == self._uuid:
            return
        self._uuid = value
        self.uuidChanged.emit(value)

    @Property(str, notify=nextUuidChanged)
    def nextUuid(self):
        try:
            block = self._get_block(self._uuid)
        except BlockInvalidError:
            return ''
        else:
            parent = block.parent
            row = parent.children.index(block)
            if row >= (len(parent.children) - 1):
                return ''
            return parent.children[row + 1].uuid

    @Property(str, notify=previousUuidChanged)
    def previousUuid(self):
        try:
            block = self._get_block(self._uuid)
        except BlockInvalidError:
            return ''
        else:
            parent = block.parent
            row = parent.children.index(block)
            if row == 0:
                return ''
            return parent.children[row - 1].uuid

    @Property('QVariant', notify=startPosChanged)
    def startPos(self):
        try:
            block = self._get_block(self._uuid)
        except BlockInvalidError:
            return self.DEFAULT_POS

        if not block.block:
            return self.DEFAULT_POS
        pos = block.block.start_pos
        return {'line': pos[0], 'column': pos[1]}

    @Property('QVariant', notify=startPosChanged)
    def endPos(self):
        try:
            block = self._get_block(self._uuid)
        except BlockInvalidError:
            return self.DEFAULT_POS

        if not block.block:
            return self.DEFAULT_POS
        pos = block.block.end_pos
        return {'line': pos[0], 'column': pos[1]}

    @Property(str, notify=codeChanged)
    def code(self):
        try:
            block = self._get_block(self._uuid)
        except BlockInvalidError:
            return ''
        else:
            return ''.join(block.write())

    @Property(int, notify=levelChanged)
    def level(self):
        return self._get_block_data('level', 0)

    @Property(bool, notify=disabledChanged)
    def disabled(self):
        return self._get_block_data('disabled', False)

    @Slot(str, result='QVariant')
    def get(self, item):
        """Returns any block data not provided by the properties."""
        return self._get_block_data(item, None)

    def _get_block_data(self, property_, default, types=None):
        try:
            block = self._get_block(self._uuid, types=types)
            return getattr(block, property_)
        except (BlockInvalidError, AttributeError):
            return default

    def _get_block(self, uuid, type_=None, types=None):
        if not self._program:
            raise IndexInvalidError()
        block = self._program.get_block(uuid)
        if not block:
            raise IndexInvalidError()
        if (type_ and type_ != block.type) or (
            types and block.type not in types
        ):
            raise TypeInvalidError()
        return block

    @Slot(str, str)
    def _on_block_updated(self, uuid, _property):
        if uuid == self._uuid:
            self.dataChanged.emit()

    @Slot(str, str)
    def _on_block_moved(self, uuid, before_uuid):
        if self._uuid not in (uuid, before_uuid):
            return
        self.nextUuidChanged.emit()
        self.previousUuidChanged.emit()
        self.levelChanged.emit()

    @Slot(str)
    def _on_block_removed(self, uuid):
        if uuid == self._uuid:
            self.dataChanged.emit()

    @Slot()
    def _on_program_reset(self):
        self.dataChanged.emit()
