from enum import IntEnum, auto
from PySide6.QtCore import QObject, QEnum, Property, Signal, Slot
from PySide6.QtQml import QmlElement

import rospy
from robot_command_msgs.msg import InterpreterState
import robot_command_msgs.srv as srv

from ...qt_helpers import MultiSlot, ensure_cleanup


INTERPRETER_STATE_TOPIC = '/robot_command/interpreter_state'
RUN_COMMAND_SERVICE = '/robot_command/run_command'
LOAD_PROGRAM_SERVICE = '/robot_command/load_program'
UNLOAD_PROGRAM_SERVICE = '/robot_command/unload_program'
EXECUTE_MDI_SERVICE = '/robot_command/execute_mdi'
RELOAD_INTERPRETER_SERVICE = '/robot_command/reload_interpreter'
START_SUBPROGRAM_SERVICE = '/robot_command/start_subprogram'

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramInterpreter(QObject):
    class State(IntEnum):
        UndefinedState = auto()
        IdleState = auto()
        StoppedState = auto()
        RunningState = auto()
        PausedState = auto()
        PausedActiveState = auto()
        RuntimeErrorState = auto()
        LoadErrorState = auto()

    class Context(IntEnum):
        UndefinedContext = auto()
        ProgramContext = auto()
        MdiContext = auto()

    _STATE_MAP = {
        InterpreterState.STATE_UNDEFINED: State.UndefinedState,
        InterpreterState.STATE_IDLE: State.IdleState,
        InterpreterState.STATE_STOPPED: State.StoppedState,
        InterpreterState.STATE_PAUSED: State.PausedState,
        InterpreterState.STATE_PAUSED_ACTIVE: State.PausedActiveState,
        InterpreterState.STATE_RUNNING: State.RunningState,
        InterpreterState.STATE_RUNTIME_ERROR: State.RuntimeErrorState,
        InterpreterState.STATE_LOAD_ERROR: State.LoadErrorState,
    }

    _CONTEXT_MAP = {
        InterpreterState.CONTEXT_UNDEFINED: Context.UndefinedContext,
        InterpreterState.CONTEXT_PROGRAM: Context.ProgramContext,
        InterpreterState.CONTEXT_MDI: Context.MdiContext,
    }

    QEnum(State)

    interpreterStateChanged = Signal()
    interpreterContextChanged = Signal()
    commandError = Signal(str, arguments=['message'])

    def __init__(self, parent=None):
        super().__init__(parent)

        self._interpreter_state = self.State.UndefinedState
        self._interpreter_context = self.Context.UndefinedContext

        self._sub = rospy.Subscriber(
            INTERPRETER_STATE_TOPIC,
            InterpreterState,
            self._on_interpreter_update_received,
        )

        self._run_command_srv = rospy.ServiceProxy(
            RUN_COMMAND_SERVICE, srv.RunCommand
        )
        self._start_subprogram_srv = rospy.ServiceProxy(
            START_SUBPROGRAM_SERVICE, srv.StartSubprogram
        )
        self._load_program_srv = rospy.ServiceProxy(
            LOAD_PROGRAM_SERVICE, srv.LoadProgram
        )
        self._unload_program_srv = rospy.ServiceProxy(
            UNLOAD_PROGRAM_SERVICE, srv.UnloadProgram
        )
        self._execute_mdi_srv = rospy.ServiceProxy(
            EXECUTE_MDI_SERVICE, srv.ExecuteMDI
        )
        self._reload_interpreter_srv = rospy.ServiceProxy(
            RELOAD_INTERPRETER_SERVICE, srv.ReloadInterpreter
        )

        ensure_cleanup(self._shutdown)

    @Property(int, notify=interpreterStateChanged)
    def interpreterState(self):
        return self._interpreter_state

    @Property(int, notify=interpreterContextChanged)
    def interpreterContext(self):
        return self._interpreter_context

    def _on_interpreter_update_received(self, msg):
        if msg.state == InterpreterState.STATE_UNDEFINED:
            return

        try:
            new_state = self._STATE_MAP[msg.state]
            if new_state != self._interpreter_state:
                self._interpreter_state = new_state
                self.interpreterStateChanged.emit()
        except KeyError:
            rospy.logwarn(
                self.tr(
                    "Unknown interpreter state received: %s. Ignoring."
                ).format(msg.state)
            )

        try:
            new_context = self._CONTEXT_MAP[msg.context]
            if new_context != self._interpreter_context:
                self._interpreter_context = new_context
                self.interpreterContextChanged.emit()
        except KeyError:
            rospy.logwarn(
                self.tr(
                    "Unknown interpreter context received: %s. Ignoring."
                ).format(msg.context)
            )

    @Slot(str, result=bool)
    def loadProgram(self, path):
        try:
            result = self._load_program_srv(path)
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(result=bool)
    def unloadProgram(self):
        try:
            result = self._unload_program_srv()
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(result=bool)
    def startProgram(self):
        try:
            result = self._run_command_srv(srv.RunCommandRequest.COMMAND_START)
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(str, result=bool)
    @Slot(str, bool, result=bool)
    def startSubprogram(self, name, loop=False):
        try:
            result = self._start_subprogram_srv(name, loop)
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(result=bool)
    def stopProgram(self):
        try:
            result = self._run_command_srv(srv.RunCommandRequest.COMMAND_STOP)
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @MultiSlot([None, bool], result=bool)
    def pauseProgram(self, active=False):
        try:
            result = self._run_command_srv(
                srv.RunCommandRequest.COMMAND_PAUSE_ACTIVE
                if active
                else srv.RunCommandRequest.COMMAND_PAUSE
            )
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(result=bool)
    def continueProgram(self):
        try:
            result = self._run_command_srv(
                srv.RunCommandRequest.COMMAND_CONTINUE
            )
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(result=bool)
    def stepProgram(self):
        try:
            result = self._run_command_srv(srv.RunCommandRequest.COMMAND_STEP)
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(str, result=bool)
    def executeMDI(self, command):
        try:
            result = self._execute_mdi_srv(command.strip())
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot(result=bool)
    @Slot(bool, result=bool)
    @Slot(bool, bool, result=bool)
    def reload(self, reload_program=True, only_if_required=False):
        try:
            result = self._reload_interpreter_srv(
                reload_program=reload_program, only_if_required=only_if_required
            )
        except rospy.ServiceException as e:
            self.commandError.emit(str(e))
            return False
        else:
            return result.success

    @Slot()
    def _shutdown(self):
        self._sub.unregister()
