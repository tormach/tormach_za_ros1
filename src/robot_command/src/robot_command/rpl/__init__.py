import inspect
import rospy

from .command import (  # noqa: F401
    AsyncCommand,
    CommandInterpreter,
    Command,
    ScopedCommand,
    ProgramPosition,
)
from .joints import JointsFactory, Joints  # noqa: F401
from .pose import PoseFactory, Pose  # noqa: F401
from .exceptions import (  # noqa: F401
    RobotProgramError,
    MoveError,
    MoveExecutionError,
    MovePlanningError,
    PathToleranceError,
    GoalToleranceError,
    ProbeError,
    ProbeUnexpectedContactError,
    ProbeContactAtStartError,
    ProbeFailedError,
    PathPilotError,
    PathPilotInstanceNotConnectedError,
    PathPilotInstanceNotFoundError,
)
from .types import InterruptSource  # noqa: F401
from movej_ik_server.arm_configs import JointConfig

for name in JointConfig.__members__.keys():
    globals()[name] = JointConfig[name]

p = PoseFactory()
j = JointsFactory()
_interpreter = CommandInterpreter()
rpl_program_start = _interpreter.rpl_program_start
rpl_main_program_start = _interpreter.rpl_main_program_start
rpl_main_program_end = _interpreter.rpl_main_program_end
print = rospy.loginfo


def init_rpl_interpreter(interpreter):
    _interpreter.register_commands(interpreter)
    _interpreter.register_commands_to_namespace(globals())
    _interpreter.init_commands(interpreter)


# in case this module is imported by the sphinx build, let's add the docstrings
# and function signatures of the execution commands
def _create_doc_commands():
    from ..execution_commands import commands

    for cmd in commands:

        def funct():
            pass

        funct.__doc__ = cmd.__init__.__doc__
        sig = inspect.signature(cmd.__init__)
        params = sig.parameters.copy()
        del params["self"]
        ret = inspect.signature(cmd.execute).return_annotation
        sig = sig.replace(parameters=params.values(), return_annotation=ret)
        funct.__signature__ = sig
        globals()[cmd.name] = funct

    Pose.__module__ = __name__
    Joints.__module__ = __name__


_stack = inspect.stack(0)
for _frame in _stack:
    if _frame.filename.endswith(
        ('sphinx/cmd/build.py', 'robot_command/doc/generate_stubs.py')
    ):
        _create_doc_commands()
        break
del _stack

# TODO:
# threads
# custom functions
# tags
