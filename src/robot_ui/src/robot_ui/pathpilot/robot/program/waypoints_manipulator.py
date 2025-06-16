from uuid import uuid4

from PySide6.QtCore import Slot
from PySide6.QtQml import QJSValue

from ...qt_helpers import MultiSlot
from .waypoints import Waypoints
from .manipulator_interface import CommandError, Command, ManipulatorInterface


class RemoveWaypointCommand(Command):
    def __init__(self, waypoint_uuid):
        self.waypoint_uuid = waypoint_uuid

    def execute(self, program):
        waypoint = program.get_waypoint(self.waypoint_uuid)
        if not waypoint:
            raise CommandError('Cannot remove non-existent waypoint.')
        program.remove_waypoint(waypoint)


class UpdateWaypointCommand(Command):
    def __init__(self, waypoint_uuid, properties):
        self.waypoint_uuid = waypoint_uuid
        self.properties = properties

    def execute(self, program):
        waypoint = program.get_waypoint(self.waypoint_uuid)
        if not waypoint:
            raise CommandError(
                'Cannot update waypoint because target does not exist.'
            )

        def rollback_changes():
            for key_ in rollbacks:
                try:
                    setattr(waypoint, key_, rollbacks[key_])
                except AttributeError:
                    pass

        rollbacks = {}
        for key in self.properties:
            value = self.properties[key]
            try:
                old_value = getattr(waypoint, key)
                program.update_waypoint(waypoint, key, value)
            except AttributeError as e:
                rollback_changes()
                raise CommandError(
                    'Cannot update waypoint, setting {} failed: {}'.format(
                        key, e
                    )
                )
            else:
                rollbacks[key] = old_value


class AddWaypointCommand(UpdateWaypointCommand):
    def __init__(self, properties):
        self.new_uuid = str(uuid4())
        super().__init__(self.new_uuid, properties)

    def execute(self, program):
        program.create_waypoint(uuid=self.new_uuid)
        UpdateWaypointCommand.execute(self, program)


class WaypointsManipulator(ManipulatorInterface):
    """Manipulates waypoints and stores the modification history"""

    def __init__(self, parent=None, source=None):
        super().__init__(parent)

        self._source = source
        self._modified = Waypoints()

    @Slot(str)
    def removeWaypoint(self, waypoint_uuid):
        command = RemoveWaypointCommand(waypoint_uuid=waypoint_uuid)
        self._execute_command(command)

    @MultiSlot(str, [QJSValue, dict])
    def updateWaypoint(self, waypoint_uuid, properties):
        properties = (
            properties.toVariant()
            if isinstance(properties, QJSValue)
            else properties
        )
        command = UpdateWaypointCommand(
            waypoint_uuid=waypoint_uuid, properties=properties
        )
        self._execute_command(command)

    @MultiSlot([QJSValue, dict], result=str)
    def addWaypoint(self, properties):
        properties = (
            properties.toVariant()
            if isinstance(properties, QJSValue)
            else properties
        )
        command = AddWaypointCommand(properties=properties)
        self._execute_command(command)
        return command.new_uuid
