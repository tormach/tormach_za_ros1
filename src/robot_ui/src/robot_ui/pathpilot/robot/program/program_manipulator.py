import contextlib
from uuid import uuid4

from PySide6.QtCore import Property, Signal, Slot, QObject
from PySide6.QtQml import QJSValue, QmlElement

from .manipulator_interface import Command, CommandError
from .robot_program import RobotProgram
from .waypoints_manipulator import WaypointsManipulator

from ...qt_helpers import MultiSlot

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class RemoveBlockCommand(Command):
    def __init__(self, block_uuid):
        self.block_uuid = block_uuid

    def execute(self, program):
        block = program.get_block(self.block_uuid)
        if not block:
            raise CommandError('Cannot remove non-existent block.')
        program.remove_block(block)


class MoveBlockCommand(Command):
    def __init__(self, block_uuid, target_uuid, before):
        self.block_uuid = block_uuid
        self.target_uuid = target_uuid
        self.before = before

    def execute(self, program):
        block = program.get_block(self.block_uuid)
        target_block = program.get_block(self.target_uuid)
        if not (block and target_block):
            raise CommandError(
                'Cannot move block because block or target does not exist.'
            )
        if block.parent == target_block.parent:
            row = block.parent.children.index(block)
            target_row = target_block.parent.children.index(target_block)
            if (
                (self.before and target_row == (row + 1))
                or (not self.before and target_row == (row - 1))
                or (target_row == row)
            ):
                return  # NOOP command, doesn't change anything
        if not program.move_block(block, target_block, self.before):
            raise CommandError('Moving block not possible.')


class UpdateBlockCommand(Command):
    def __init__(self, block_uuid, properties):
        self.block_uuid = block_uuid
        self.properties = properties

    def execute(self, program):
        block = program.get_block(self.block_uuid)
        if not block:
            raise CommandError(
                'Cannot update block because target does not exist.'
            )

        def rollback_changes():
            for key_ in rollbacks:
                try:
                    setattr(block, key_, rollbacks[key_])
                except AttributeError:
                    pass

        rollbacks = {}
        for key in self.properties:
            value = self.properties[key]
            try:
                old_value = getattr(block, key)
                program.update_block(block, key, value)
            except AttributeError as e:
                rollback_changes()
                raise CommandError(
                    f'Cannot update block, setting {key} failed: {e}'
                )
            else:
                rollbacks[key] = old_value


class CreateBlockCommand(Command):
    def __init__(self, target_uuid, type_, before):
        self.target_uuid = target_uuid
        self.new_uuid = str(uuid4())
        self.type = type_
        self.before = before

    def execute(self, program):
        target_block = program.get_block(self.target_uuid)
        program.create_block(
            target_block=target_block,
            type_=self.type,
            uuid=self.new_uuid,
            before=self.before,
        )


class CreateChildBlockCommand(Command):
    def __init__(self, parent_uuid, type_):
        self.parent_uuid = parent_uuid
        self.new_uuid = str(uuid4())
        self.type = type_

    def execute(self, program):
        parent_block = program.get_block(self.parent_uuid)
        if not parent_block:
            raise CommandError(
                'Cannot create child block because target does not exist.'
            )
        program.create_child_block(
            parent_block=parent_block, type_=self.type, uuid=self.new_uuid
        )


class CreateGroupBlockCommand(Command):
    def __init__(self, group_block_uuid, type_, append):
        self.group_block_uuid = group_block_uuid
        self.new_uuid = str(uuid4())
        self.type = type_
        self.append = append

    def execute(self, program):
        group_block = program.get_block(self.group_block_uuid)
        if not group_block:
            raise CommandError(
                'Cannot create group block because target does not exist.'
            )
        program.create_group_block(
            group_block=group_block,
            type_=self.type,
            uuid=self.new_uuid,
            append=self.append,
        )


class CopyBlockCommand(Command):
    def __init__(self, block_uuid, target_uuid, before):
        self.block_uuid = block_uuid
        self.target_uuid = target_uuid
        self.before = before
        self.new_uuid = str(uuid4())

    def execute(self, program):
        block = program.get_block(self.block_uuid)
        target_block = program.get_block(self.target_uuid)
        if not (block and target_block):
            raise CommandError(
                'Cannot copy block because block or target does not exist.'
            )
        program.copy_block(
            block=block,
            target_block=target_block,
            uuid=self.new_uuid,
            before=self.before,
        )


class RenameSubProgramCommand(Command):
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name

    def execute(self, program):
        for block in program.blocks:
            if (
                block.type in ('call', 'subprogram')
                and block.name == self.old_name
            ):
                program.update_block(block, 'name', self.new_name)


@QmlElement
class ProgramManipulator(WaypointsManipulator):
    """Manipulates the robot program and stores the modification history."""

    sourceProgramChanged = Signal()
    modifiedProgramChanged = Signal()

    def __init__(self, parent=None, source_program=None):
        super().__init__(parent)

        self._source: RobotProgram = source_program
        self._modified = RobotProgram()

        self.sourceProgramChanged.connect(self.resetHistory)

    @Property(QObject, notify=sourceProgramChanged)  # RobotProgram
    def sourceProgram(self):
        return self._source

    @sourceProgram.setter
    def sourceProgram(self, value):
        if value == self._source:
            return
        old_value = self._source
        self._source = value
        self.sourceProgramChanged.emit()

        if old_value:
            with contextlib.suppress(RuntimeError):
                old_value.reset.disconnect(self.resetHistory)
        if value:
            value.reset.connect(self.resetHistory)

    @Property(RobotProgram, notify=modifiedProgramChanged)
    def modifiedProgram(self):
        return self._modified

    @modifiedProgram.setter
    def modifiedProgram(self, value):
        if value == self._modified:
            return
        self._modified = value
        self.modifiedProgramChanged.emit()

    @MultiSlot(str, [QJSValue, dict])
    def updateBlock(self, block_uuid, properties):
        properties = (
            properties.toVariant()
            if isinstance(properties, QJSValue)
            else properties
        )

        command = UpdateBlockCommand(
            block_uuid=block_uuid, properties=properties
        )
        self._execute_command(command)

    @MultiSlot(str, str, [None, bool], result=str)
    def createBlock(self, target_uuid, type_, before=False):
        command = CreateBlockCommand(
            target_uuid=target_uuid, type_=type_, before=before
        )
        self._execute_command(command)
        return command.new_uuid

    @Slot(str, str, result=str)
    def createChildBlock(self, parent_uuid, type_):
        command = CreateChildBlockCommand(parent_uuid=parent_uuid, type_=type_)
        self._execute_command(command)
        return command.new_uuid

    @Slot(str, str, bool, result=str)
    def createGroupBlock(self, group_block_uuid, type_, append):
        command = CreateGroupBlockCommand(
            group_block_uuid=group_block_uuid, type_=type_, append=append
        )
        self._execute_command(command)
        return command.new_uuid

    @Slot(str)
    def removeBlock(self, block_uuid):
        command = RemoveBlockCommand(block_uuid=block_uuid)
        self._execute_command(command)

    @MultiSlot(str, str, [None, bool], result=str)
    def moveBlock(self, block_uuid, target_uuid, before=False):
        command = MoveBlockCommand(
            block_uuid=block_uuid, target_uuid=target_uuid, before=before
        )
        self._execute_command(command)
        return command.block_uuid

    @MultiSlot(str, str, [None, bool], result=str)
    def copyBlock(self, block_uuid, target_uuid, before=False):
        command = CopyBlockCommand(
            block_uuid=block_uuid, target_uuid=target_uuid, before=before
        )
        self._execute_command(command)
        return command.new_uuid

    @Slot(str, str)
    def renameSubProgram(self, old_name, new_name):
        if old_name == new_name:
            return
        command = RenameSubProgramCommand(old_name=old_name, new_name=new_name)
        self._execute_command(command)
