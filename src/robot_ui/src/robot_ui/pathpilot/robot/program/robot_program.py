from PySide6.QtCore import Signal, Property
from PySide6.QtQml import QmlElement, QmlUncreatable
from copy import deepcopy

from robot_command.robot_program import RobotProgram as Program
from .waypoints import Waypoints

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlUncreatable("RobotProgram is not creatable in QML")
class RobotProgram(Waypoints, Program):
    """Wraps the pure Python object to enable signals and QML compatibility."""

    reset = Signal()
    blockAboutToBeCreated = Signal(str, bool)
    blockCreated = Signal(str, str, bool)
    childBlockAboutToBeCreated = Signal(str)
    childBlockCreated = Signal(str, str)
    blockAboutToBeRemoved = Signal(str)
    blockRemoved = Signal(str)
    blockUpdated = Signal(str, str)
    blockAboutToBeMoved = Signal(str, str, bool)
    blockMoved = Signal(str, str, bool)
    blockAboutToBeCopied = Signal(str, str, bool)
    blockCopied = Signal(str, str, bool)
    updated = Signal()
    linearUnitChanged = Signal()
    angularUnitChanged = Signal()
    timeUnitChanged = Signal()
    headerAutoUpdatedChanged = Signal()
    linearUnitDecimalsChanged = Signal(int)
    angularUnitDecimalsChanged = Signal(int)

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.reset.connect(self.linearUnitChanged)
        self.reset.connect(self.angularUnitChanged)
        self.reset.connect(self.timeUnitChanged)
        self.reset.connect(self.headerAutoUpdatedChanged)
        self.blockCreated.connect(self.updated)
        self.childBlockCreated.connect(self.updated)
        self.blockRemoved.connect(self.updated)
        self.blockUpdated.connect(self.updated)
        self.blockMoved.connect(self.updated)
        self.blockCopied.connect(self.updated)

    def reset_data(self, **kwargs):
        super().reset_data(**kwargs)
        self.reset.emit()
        self.updated.emit()

    @Property(str, notify=linearUnitChanged)
    def linearUnit(self):
        return self.linear_unit

    @linearUnit.setter
    def linearUnit(self, value):
        if value == self.linear_unit:
            return
        self.reset_data(linear_unit=value)

    @Property(str, notify=angularUnitChanged)
    def angularUnit(self):
        return self.angular_unit

    @angularUnit.setter
    def angularUnit(self, value):
        if value == self.angular_unit:
            return
        self.reset_data(angular_unit=value)

    @Property(str, notify=timeUnitChanged)
    def timeUnit(self):
        return self.time_unit

    @timeUnit.setter
    def timeUnit(self, value):
        if value == self.time_unit:
            return
        self.reset_data(time_unit=value)

    @Property(int, notify=linearUnitDecimalsChanged)
    def linearUnitDecimals(self):
        return self.linear_unit_decimals

    @linearUnitDecimals.setter
    def linearUnitDecimals(self, value):
        if value == self.linear_unit_decimals:
            return
        self.linear_unit_decimals = value
        self.linearUnitDecimalsChanged.emit(value)

    @Property(int, notify=angularUnitDecimalsChanged)
    def angularUnitDecimals(self):
        return self.angular_unit_decimals

    @angularUnitDecimals.setter
    def angularUnitDecimals(self, value):
        if value == self.angular_unit_decimals:
            return
        self.angular_unit_decimals = value
        self.angularUnitDecimalsChanged.emit(value)

    @Property(bool, notify=headerAutoUpdatedChanged)
    def headerAutoUpdated(self):
        return self.header_auto_updated

    def _create_block(self, target_block, type_, uuid, before):
        self.blockAboutToBeCreated.emit(target_block.uuid, before)
        new_block = super()._create_block(
            target_block, type_, uuid=uuid, before=before
        )
        self.blockCreated.emit(target_block.uuid, new_block.uuid, before)
        return new_block

    def _create_child_block(self, parent_block, type_, uuid=None):
        self.childBlockAboutToBeCreated.emit(parent_block.uuid)
        new_block = super()._create_child_block(parent_block, type_, uuid=uuid)
        self.childBlockCreated.emit(parent_block.uuid, new_block.uuid)
        return new_block

    def _remove_block(self, block):
        uuid = block.uuid
        self.blockAboutToBeRemoved.emit(uuid)
        super()._remove_block(block)
        self.blockRemoved.emit(uuid)

    def _update_block(self, block, property_, value):
        super()._update_block(block, property_, value)
        self.blockUpdated.emit(block.uuid, property_)

    def _move_block(self, block, target_block, before):
        block_uuid = block.uuid
        target_uuid = target_block.uuid
        self.blockAboutToBeMoved.emit(block_uuid, target_uuid, before)
        super()._move_block(block, target_block, before)
        self.blockMoved.emit(block_uuid, target_uuid, before)

    def _copy_block(self, block, target_block, uuid, before):
        block_uuid = block.uuid
        target_uuid = target_block.uuid
        self.blockAboutToBeCopied.emit(block_uuid, target_uuid, before)
        new_block = super()._copy_block(block, target_block, uuid, before)
        self.blockCopied.emit(target_uuid, new_block.uuid, before)
        return new_block

    def __deepcopy__(self, memo):
        clone = self.__class__()
        for key, val in self.__dict__.items():
            clone.__dict__ = deepcopy(self.__dict__, memo)
