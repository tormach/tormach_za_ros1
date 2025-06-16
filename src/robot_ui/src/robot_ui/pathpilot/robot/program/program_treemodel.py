import contextlib
from typing import Optional
from enum import IntEnum, auto

from PySide6.QtCore import (
    Signal,
    Property,
    Slot,
    QAbstractItemModel,
    QByteArray,
    QModelIndex,
    Qt,
    QEnum,
    QObject,
)
from PySide6.QtQml import QJSValue, QmlElement

from robot_command.rpl import ProgramPosition

from ...models.model_index_walker import ModelIndexWalker
from .robot_program import RobotProgram

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramTreeModel(QAbstractItemModel):
    class Roles(IntEnum):
        TypeRole = Qt.UserRole
        ModifiedRole = auto()
        UuidRole = auto()
        DisabledRole = auto()
        WarningRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.TypeRole: QByteArray(b'type'),
        Roles.ModifiedRole: QByteArray(b'modified'),
        Roles.UuidRole: QByteArray(b'uuid'),
        Roles.DisabledRole: QByteArray(b'disabled'),
        Roles.WarningRole: QByteArray(b'warning'),
    }

    programChanged = Signal()
    warningsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root_block = None
        self._program: Optional[RobotProgram] = None
        self._position_index_map = {}
        self._uuid_index_map = {}
        self._warnings = {}
        self._block_move_parent = None  # for block move operation

        self.programChanged.connect(self._on_program_reset)

    @Property(QObject, notify=programChanged)  # RobotProgram
    def program(self):
        return self._program

    @program.setter
    def program(self, new_program):
        if new_program == self._program:
            return
        old_program = self._program
        self._program = new_program
        self.programChanged.emit()

        if old_program:
            with contextlib.suppress(RuntimeError):
                old_program.reset.disconnect(self._on_program_reset)
                old_program.blockAboutToBeCreated.disconnect(
                    self._on_block_about_to_be_created
                )
                old_program.blockCreated.disconnect(self._on_block_created)
                old_program.childBlockAboutToBeCreated.disconnect(
                    self._on_child_block_about_to_be_created
                )
                old_program.childBlockCreated.disconnect(
                    self._on_child_block_created
                )
                old_program.blockAboutToBeRemoved.disconnect(
                    self._on_block_about_to_be_removed
                )
                old_program.blockRemoved.disconnect(self._on_block_removed)
                old_program.blockUpdated.disconnect(self._on_block_updated)
                old_program.blockAboutToBeMoved.disconnect(
                    self._on_block_about_to_be_moved
                )
                old_program.blockMoved.disconnect(self._on_block_moved)
                old_program.blockAboutToBeCopied.disconnect(
                    self._on_block_about_to_be_copied
                )
                old_program.blockCopied.disconnect(self._on_block_copied)
        if new_program:
            new_program.reset.connect(self._on_program_reset)
            new_program.blockAboutToBeCreated.connect(
                self._on_block_about_to_be_created
            )
            new_program.blockCreated.connect(self._on_block_created)
            new_program.childBlockAboutToBeCreated.connect(
                self._on_child_block_about_to_be_created
            )
            new_program.childBlockCreated.connect(self._on_child_block_created)
            new_program.blockAboutToBeRemoved.connect(
                self._on_block_about_to_be_removed
            )
            new_program.blockRemoved.connect(self._on_block_removed)
            new_program.blockUpdated.connect(self._on_block_updated)
            new_program.blockAboutToBeMoved.connect(
                self._on_block_about_to_be_moved
            )
            new_program.blockMoved.connect(self._on_block_moved)
            new_program.blockAboutToBeCopied.connect(
                self._on_block_about_to_be_copied
            )
            new_program.blockCopied.connect(self._on_block_copied)

    @Property('QVariant', notify=warningsChanged)
    def warnings(self):
        return self._warnings

    @warnings.setter
    def warnings(self, warnings):
        warnings = (
            warnings.toVariant() if isinstance(warnings, QJSValue) else warnings
        )
        if warnings == self._warnings:
            return

        old_warnings = self._warnings
        self._warnings = warnings
        for uuid in warnings:
            index = self.indexForUuid(uuid)
            if index.isValid():
                self.dataChanged.emit(index, index)
        for uuid in old_warnings.keys() - warnings.keys():
            index = self.indexForUuid(uuid)
            if index.isValid():
                self.dataChanged.emit(index, index)

        self.warningsChanged.emit()

    @Slot()
    def _on_program_reset(self):
        self.beginResetModel()
        self._root_block = self._program.root_block if self._program else None
        self._update_position_index_map()
        self._update_uuid_index_map()
        self.endResetModel()

    @Slot(str, bool)
    def _on_block_about_to_be_created(self, target_uuid, before):
        index = self.indexForUuid(target_uuid)
        row = index.row()
        if not before:
            row += 1
        self.beginInsertRows(index.parent(), row, row)

    @Slot(str, str, bool)
    def _on_block_created(self, _target_uuid, _new_uuid, _before):
        self._update_uuid_index_map()  # NOTE: optimize when necessary
        self.endInsertRows()
        self.layoutChanged.emit()  # workaround for bug in QML TreeView

    @Slot(str)
    def _on_child_block_about_to_be_created(self, parent_uuid):
        index = self.indexForUuid(parent_uuid)
        row = self.rowCount(index)
        self.beginInsertRows(index, row, row)

    @Slot(str, str)
    def _on_child_block_created(self, _parent_uuid, _new_uuid):
        self._update_uuid_index_map()  # NOTE: optimize when necessary
        self.endInsertRows()

    @Slot(str)
    def _on_block_about_to_be_removed(self, block_uuid):
        index = self.indexForUuid(block_uuid)
        row = index.row()
        self.beginRemoveRows(index.parent(), row, row)

    @Slot(str)
    def _on_block_removed(self, block_uuid):
        index = self.indexForUuid(block_uuid)
        rev_map = {v: k for k, v in self._position_index_map.items()}
        if index in rev_map:
            self._position_index_map.pop(rev_map[index])

        self._update_uuid_index_map()  # NOTE: optimize when necessary
        self.endRemoveRows()

    @Slot(str, str)
    def _on_block_updated(self, block_uuid, property_):
        index = self.indexForUuid(block_uuid)
        self.dataChanged.emit(index, index)
        if property_ == 'disabled':
            self._children_data_changed(index)

    def _children_data_changed(self, index):
        children = self.rowCount(index)
        if children == 0:
            return
        first_index = self.index(0, 0, parent=index)
        last_index = self.index(children - 1, 0, parent=index)
        self.dataChanged.emit(first_index, last_index)
        for row in range(children):
            row_index = self.index(row, 0, parent=index)
            self._children_data_changed(row_index)

    def _on_block_about_to_be_moved(self, block_uuid, target_uuid, before):
        index = self.indexForUuid(block_uuid)
        target_index = self.indexForUuid(target_uuid)
        target_row = target_index.row()
        if not before:
            target_row += 1
        self.beginMoveRows(
            index.parent(),
            index.row(),
            index.row(),
            target_index.parent(),
            target_row,
        )
        self._block_move_parent = index.parent()

    def _on_block_moved(self, block_uuid, target_uuid, _before):
        self._update_uuid_index_map()  # NOTE: optimize when necessary
        self.endMoveRows()
        index = self.indexForUuid(block_uuid)
        self.dataChanged.emit(index, index, [self.Roles.ModifiedRole])
        block_parent = self._block_move_parent
        if block_parent.isValid():
            self.dataChanged.emit(
                block_parent, block_parent, [self.Roles.ModifiedRole]
            )
        target_parent = self.indexForUuid(target_uuid).parent()
        if target_parent.isValid() and target_parent is not block_parent:
            self.dataChanged.emit(
                target_parent, target_parent, [self.Roles.ModifiedRole]
            )

    def _on_block_about_to_be_copied(self, _block_uuid, target_uuid, before):
        index = self.indexForUuid(target_uuid)
        row = index.row()
        if not before:
            row += 1
        self.beginInsertRows(index.parent(), row, row)

    def _on_block_copied(self, _target_uuid, _block_uuid, _before):
        self._update_uuid_index_map()  # NOTE: optimize when necessary
        self.endInsertRows()
        self.layoutChanged.emit()  # workaround for bug in QML TreeView

    def _update_position_index_map(self):
        """Create a map between program position and index in the treeview."""
        self._position_index_map = {}
        if not self._root_block:
            return
        filename = self._root_block.program.path

        for index in ModelIndexWalker(self, QModelIndex()):
            block = index.internalPointer()
            start_line = block.node.start_pos[0]
            end_line = max(block.node.end_pos[0] - 1, start_line)
            for linum in range(start_line, end_line + 1):
                position = ProgramPosition(linum, filename)
                if position not in self._position_index_map:
                    self._position_index_map[position] = index

    def index_for_position(self, position):
        return self._position_index_map.get(position, QModelIndex())

    def _update_uuid_index_map(self):
        self._uuid_index_map = {}

        for index in ModelIndexWalker(self, QModelIndex()):
            block = index.internalPointer()
            uuid = block.uuid
            self._uuid_index_map[uuid] = index

    @Slot(str, result=QModelIndex)
    def indexForUuid(self, uuid):
        return self._uuid_index_map.get(uuid, QModelIndex())

    def data(self, index, role):
        if not index.isValid():
            return None

        block = index.internalPointer()

        switch = {
            Qt.DisplayRole: lambda: block.type,
            self.Roles.TypeRole: lambda: block.type,
            self.Roles.ModifiedRole: lambda: block.modified,
            self.Roles.UuidRole: lambda: block.uuid,
            self.Roles.DisabledRole: lambda: block.disabled,
            self.Roles.WarningRole: lambda: self._warnings.get(block.uuid, []),
        }

        return switch.get(role, lambda: None)()

    def roleNames(self):
        return self._ROLE_NAMES

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, _section, orientation, role=Qt.DisplayRole):
        if orientation != Qt.Horizontal:
            return None

        return self._ROLE_NAMES.get(role, '').title()

    def _get_item(self, index):
        if index and index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self._root_block

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self._get_item(parent)
        try:
            child_item = parent_item.children[row]
        except IndexError:
            return QModelIndex()
        else:
            return self.createIndex(row, column, child_item)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item == self._root_block:
            return QModelIndex()

        row = parent_item.parent.children.index(parent_item)
        return self.createIndex(row, 0, parent_item)

    def columnCount(self, _parent):
        return 1  # single column in tree view

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0

        parent_item = (
            parent.internalPointer() if parent.isValid() else self._root_block
        )
        return len(parent_item.children) if parent_item else 0
