from collections import defaultdict
from typing import Optional

from PySide6.QtCore import Property, Signal, Slot, QObject
from PySide6.QtQml import QmlElement

from robot_command.program_blocks import RPLBlockWalker
from robot_command.program_blocks.set_block import SetType
from robot_command.program_blocks.wait_block import WaitType
from robot_command.program_blocks.frame_block import FrameType
from robot_command.program_blocks.move_block import MoveBlock

from .waypoints import Waypoints
from .robot_program import RobotProgram
from .program_warning import ProgramWarning

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramValidator(QObject):
    _global_waypoints: Optional[Waypoints]
    _program: Optional[RobotProgram]

    programChanged = Signal()
    globalWaypointsChanged = Signal(Waypoints)
    validChanged = Signal(bool)
    warningsChanged = Signal()
    digitalInputNamesChanged = Signal()
    digitalOutputNamesChanged = Signal()
    userFrameNamesChanged = Signal()
    toolFrameNamesChanged = Signal()
    mainLoopWarningEnabledChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._program: RobotProgram = None
        self._global_waypoints: Waypoints = None
        self._valid = True
        self._warnings = {}
        self._digital_input_names = []
        self._digital_output_names = []
        self._user_frame_names = []
        self._tool_frame_names = []
        self._main_loop_warning_enabled = False

    @Property(QObject, notify=programChanged)  # RobotProgram
    def program(self):
        return self._program

    @program.setter
    def program(self, value):
        if value == self._program:
            return
        self._program = value
        self.programChanged.emit()

    @Property(QObject, notify=globalWaypointsChanged)  # Waypoints
    def globalWaypoints(self):
        return self._global_waypoints

    @globalWaypoints.setter
    def globalWaypoints(self, value):
        if value == self._global_waypoints:
            return
        self._global_waypoints = value
        self.globalWaypointsChanged.emit(value)

    @Property(bool, notify=validChanged)
    def valid(self):
        return self._valid

    @valid.setter
    def valid(self, value):
        if value == self._valid:
            return
        self._valid = value
        self.validChanged.emit(value)

    @Property('QVariant', notify=warningsChanged)
    def warnings(self):
        return self._warnings

    @Property(list, notify=digitalInputNamesChanged)
    def digitalInputNames(self):
        return self._digital_input_names

    @digitalInputNames.setter
    def digitalInputNames(self, value):
        if value == self._digital_input_names:
            return
        self._digital_input_names = value
        self.digitalInputNamesChanged.emit()

    @Property(list, notify=digitalOutputNamesChanged)
    def digitalOutputNames(self):
        return self._digital_output_names

    @digitalOutputNames.setter
    def digitalOutputNames(self, value):
        if value == self._digital_output_names:
            return
        self._digital_output_names = value
        self.digitalOutputNamesChanged.emit()

    @Property(list, notify=userFrameNamesChanged)
    def userFrameNames(self):
        return self._user_frame_names

    @userFrameNames.setter
    def userFrameNames(self, value):
        if value == self._user_frame_names:
            return
        self._user_frame_names = value
        self.userFrameNamesChanged.emit()

    @Property(list, notify=toolFrameNamesChanged)
    def toolFrameNames(self):
        return self._tool_frame_names

    @toolFrameNames.setter
    def toolFrameNames(self, value):
        if value == self._tool_frame_names:
            return
        self._tool_frame_names = value
        self.toolFrameNamesChanged.emit()

    @Property(bool, notify=mainLoopWarningEnabledChanged)
    def mainLoopWarningEnabled(self):
        return self._main_loop_warning_enabled

    @mainLoopWarningEnabled.setter
    def mainLoopWarningEnabled(self, value):
        if value == self._main_loop_warning_enabled:
            return
        self._main_loop_warning_enabled = value
        self.mainLoopWarningEnabledChanged.emit(value)

    @Slot()
    def analyzeProgram(self):
        if self._program is None or self._program.root_block is None:
            return
        warnings = defaultdict(list)
        waypoints = {w.name: w for w in self._program.waypoints}
        root_block = self._program.root_block
        subprograms = {
            n.name: n for n in root_block.children if n.type == 'subprogram'
        }

        def chain():
            yield from self._find_duplicate_names(subprograms, waypoints)
            yield from self._find_local_waypoints_shadowing_global_waypoints(
                waypoints
            )
            yield from self._find_shadowing_builtin(subprograms, waypoints)
            yield from self._find_missing_waypoints(root_block, waypoints)
            yield from self._find_missing_digital_ios(root_block)
            yield from self._find_missing_user_frames(self._program)
            yield from self._find_missing_tool_frames(self._program)
            yield from self._find_missing_main_function(root_block)
            yield from self._find_first_line_movel(root_block)
            if self._main_loop_warning_enabled:
                yield from self._find_main_endless_loop(root_block)

        for uuid, warning in chain():
            warnings[uuid].append(warning)

        self._warnings = dict(warnings)
        self.warningsChanged.emit()

        valid = len(warnings) == 0
        if valid != self._valid:
            self._valid = valid
            self.validChanged.emit(valid)

    def _find_missing_waypoints(self, root_block, waypoints):
        used_waypoints = defaultdict(list)
        for block in RPLBlockWalker(root_block):
            if block.type in ('movel', 'movef', 'movej') and isinstance(
                block.waypoint, str
            ):
                used_waypoints[block.waypoint].append(block)
        waypoint_names = set(waypoints.keys())
        if self._global_waypoints:
            waypoint_names |= {
                f'"{wp.name}"' for wp in self._global_waypoints.waypoints
            }
        missing_waypoints = used_waypoints.keys() - waypoint_names
        for name in missing_waypoints:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.MissingName,
                message=self.tr(
                    "Move command contains missing waypoint \"{0}\"."
                ).format(name.replace('"', '')),
            )
            for block in used_waypoints[name]:
                yield block.uuid, warning

    def _find_local_waypoints_shadowing_global_waypoints(self, waypoints):
        if not self._global_waypoints:
            return
        waypoint_names = set(waypoints.keys())
        global_waypoint_names = {
            wp.name for wp in self._global_waypoints.waypoints
        }
        duplicate_names = waypoint_names & global_waypoint_names
        for name in duplicate_names:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.DuplicateName,
                message=self.tr(
                    "Local waypoint name \"{0}\" duplicates global waypoint name."
                ).format(name),
            )
            yield waypoints[name].uuid, warning

    def _find_shadowing_builtin(self, subprograms, waypoints):
        name_intersection = waypoints.keys() & __builtins__.keys()
        for name in name_intersection:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.ShadowsPythonKeyword,
                message=self.tr(
                    "Waypoint name \"{0}\" is shadowing a Python keyword."
                ).format(name),
            )
            yield waypoints[name].uuid, warning
        name_intersection = subprograms.keys() & __builtins__.keys()
        for name in name_intersection:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.ShadowsPythonKeyword,
                message=self.tr(
                    "Subprogram name \"{0}\" is shadowing a Python keyword."
                ).format(name),
            )
            yield subprograms[name].uuid, warning

    def _find_duplicate_names(self, subprograms, waypoints):
        name_intersection = waypoints.keys() & subprograms.keys()
        for name in name_intersection:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.DuplicateName,
                message=self.tr(
                    "Subprogram \"{0}\" and waypoint have the same name."
                ).format(name),
            )
            yield subprograms[name].uuid, warning
            warning = ProgramWarning(
                type_=ProgramWarning.Types.DuplicateName,
                message=self.tr(
                    "Waypoint \"{0}\" and subprogram have the same name."
                ).format(name),
            )
            yield waypoints[name].uuid, warning

    def _find_missing_digital_ios(self, root_block):
        set_blocks = defaultdict(list)
        for block in RPLBlockWalker(root_block):
            if (
                block.type == 'set'
                and block.set_type == SetType.SetDigitalOut
                and block.digital_out_name
            ):
                set_blocks[block.digital_out_name].append(block)
        missing_names = set_blocks.keys() - set(self._digital_output_names)
        for name in missing_names:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.MissingName,
                message=self.tr(
                    "Set command contains missing digital output name \"{0}\"."
                ).format(name),
            )
            for block in set_blocks[name]:
                yield block.uuid, warning
        wait_blocks = {
            block.digital_in_name: block
            for block in RPLBlockWalker(root_block)
            if block.type == 'wait'
            and block.wait_type == WaitType.WaitForDigitalIn
            and block.digital_in_name
        }
        missing_names = wait_blocks.keys() - set(self._digital_input_names)
        for name in missing_names:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.MissingName,
                message=self.tr(
                    "Wait command contains missing digital input name \"{0}\"."
                ).format(name),
            )
            yield wait_blocks[name].uuid, warning

    def _find_missing_user_frames(self, program):
        frame_names = set(self._user_frame_names)
        waypoint_frames = defaultdict(list)
        for wp in program.waypoints:
            if wp.frame:
                waypoint_frames[wp.frame].append(wp)
        missing_names = waypoint_frames.keys() - frame_names
        for name in missing_names:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.MissingName,
                message=self.tr(
                    "User frame \"{0}\" used in waypoint is not defined"
                ).format(name),
            )
            for block in waypoint_frames[name]:
                yield block.uuid, warning

        frame_blocks = defaultdict(list)
        for block in RPLBlockWalker(program.root_block):
            if (
                block.type == 'frame'
                and block.frame_type == FrameType.ChangeUserFrame
                and block.name
            ):
                frame_blocks[block.name].append(block)
        missing_names = frame_blocks.keys() - frame_names
        for name in missing_names:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.MissingName,
                message=self.tr(
                    "User frame \"{0}\" used in change user frame command "
                    "is not defined"
                ).format(name),
            )
            for block in frame_blocks[name]:
                yield block.uuid, warning

    def _find_missing_tool_frames(self, program):
        frame_names = set(self._tool_frame_names)
        frame_blocks = defaultdict(list)
        for block in RPLBlockWalker(program.root_block):
            if (
                block.type == 'frame'
                and block.frame_type == FrameType.ChangeToolFrame
                and block.name
            ):
                frame_blocks[block.name].append(block)
        missing_names = frame_blocks.keys() - frame_names
        for name in missing_names:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.MissingName,
                message=self.tr(
                    "Tool frame \"{0}\" used in change tool frame command "
                    "is not defined."
                ).format(name),
            )
            for block in frame_blocks[name]:
                yield block.uuid, warning

    def _get_main_block(self, root_block):
        return next(
            (
                block
                for block in RPLBlockWalker(root_block)
                if block.type == 'mainprogram'
            ),
            None,
        )

    def _find_missing_main_function(self, root_block):
        if (self._get_main_block(root_block)) is None:
            warning = ProgramWarning(
                type_=ProgramWarning.Types.MissingFunction,
                message=self.tr("The robot programs main function is missing."),
            )
            yield root_block.uuid, warning

    def _find_main_endless_loop(self, root_block):
        if (main_block := self._get_main_block(root_block)) is None:
            return  # error already reported by other validator
        for block in main_block.children:
            if block.type == 'wait' and block.wait_type == WaitType.Exit:
                return
        warning = ProgramWarning(
            type_=ProgramWarning.Types.EndlessMainLoop,
            message=self.tr(
                "The robot program is missing an exit() statement "
                "and therefore will loop forever.\n"
                " \u21B3 You can disable this warning in the settings tab."
            ),
        )
        yield main_block.uuid, warning

    def _find_first_line_movel(self, root_block):
        if (main_block := self._get_main_block(root_block)) is None:
            return  # error already reported by other validator
        # find first move command and check it's type
        for block in RPLBlockWalker(main_block):
            if block.type in MoveBlock.MOVE_TYPES:
                if block.type == 'movel':
                    warning = ProgramWarning(
                        type_=ProgramWarning.Types.FirstLineMovel,
                        message=self.tr(
                            "The robot program starts with a movel command.\n"
                            "This is not recommended."
                        ),
                    )
                    yield block.uuid, warning
                return
