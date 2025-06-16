from .deprecated_command import deprecated_command
from .movel import MoveL
from .movej import MoveJ
from .movef import MoveF
from .movec import MoveC
from .get_digital_in import GetDigitalIn
from .set_digital_out import SetDigitalOut
from .sleep import Sleep
from .sync import Sync
from .notify import Notify
from .input import Input
from .pathpilot_mdi import PathPilotMdi
from .pathpilot_cycle_start import PathPilotCycleStart
from .pathpilot_abort import PathPilotAbort
from .get_joint_values import GetJointValues
from .get_pose import GetPose
from .pause import Pause
from .set_user_frame import SetUserFrame
from .set_tool_frame import SetToolFrame
from .get_user_frame import GetUserFrame
from .get_active_user_frame import GetActiveUserFrame
from .get_tool_frame import GetToolFrame
from .get_active_tool_frame import GetActiveToolFrame
from .change_user_frame import ChangeUserFrame
from .change_tool_frame import ChangeToolFrame
from .user_frame import UserFrame
from .get_pathpilot_state import GetPathPilotState
from .set_units import SetUnits
from .get_units import GetUnits
from .set_path_blending import SetPathBlending
from .set_machine_frame import SetMachineFrame
from .get_global_waypoint import GetGlobalWaypoint
from .set_global_waypoint import SetGlobalWaypoint
from .set_param import SetParam
from .get_param import GetParam
from .delete_param import DeleteParam
from .load_trajectory import LoadTrajectory
from .execute_trajectory import ExecuteTrajectory
from .save_trajectory import SaveTrajectory
from .probe_cycle import ProbeCycle
from .to_local_pose import ToLocalPose
from .register_interrupt import RegisterInterrupt
from .trigger_interrupt import TriggerInterrupt
from .actuate_gripper import ActuateGripper
from .get_gripper_position import GetGripperPosition
from ..interfaces import (  # noqa: F401
    RosNodeInterfaceSingleton,
    MoveItInterfaceSingleton,
    HalIoInterfaceSingleton,
    NotificationInterfaceSingleton,
    MachinetalkInterfaceSingleton,
    UserFrameInterfaceSingleton,
    ToolFrameInterfaceSingleton,
    ConfigInterfaceSingleton,
    JointsToPoseInterfaceSingleton,
    GlobalWaypointInterfaceSingleton,
    MachineMaxvelInterfaceSingleton,
    SafetyInputInterfaceSingleton,
    InterruptInterfaceSingleton,
    GripperInterfaceSingleton,
    MoveTypeInterfaceSingleton,
    FeedholdInterfaceSingleton,
    LidarServiceHandler,
)
from .allowed_configurations import AllowedConfigurations


def init():
    RosNodeInterfaceSingleton()  # init ROS node
    MoveItInterfaceSingleton()  # init moveit
    HalIoInterfaceSingleton()  # init HAL IO
    InterruptInterfaceSingleton()  # init interrupts
    NotificationInterfaceSingleton()  # init notifications
    MachinetalkInterfaceSingleton()  # init ros_machinetalk
    # init frames
    user_frames = UserFrameInterfaceSingleton()
    ToolFrameInterfaceSingleton(tf_buffer=user_frames.tf_buffer)
    ConfigInterfaceSingleton()  # init config
    JointsToPoseInterfaceSingleton()  # init joints to pose conversion
    GlobalWaypointInterfaceSingleton()  # global waypoints
    MachineMaxvelInterfaceSingleton()  # maxvel interp cbs
    SafetyInputInterfaceSingleton()  # safety input interp cbs
    GripperInterfaceSingleton()  # interface for electric grippers
    MoveTypeInterfaceSingleton()  # move types for velocity scale in ROS controller
    FeedholdInterfaceSingleton()  # passing gentle traj slowdown to ROS controller
    LidarServiceHandler()  # turn off lidar data collection state at program pause/stop


commands = [
    MoveL,
    MoveJ,
    MoveF,
    MoveC,
    ProbeCycle,
    GetDigitalIn,
    SetDigitalOut,
    Sync,
    Sleep,
    Notify,
    Input,
    PathPilotMdi,
    PathPilotCycleStart,
    PathPilotAbort,
    GetJointValues,
    GetPose,
    Pause,
    SetUserFrame,
    SetToolFrame,
    GetUserFrame,
    GetActiveUserFrame,
    GetToolFrame,
    GetActiveToolFrame,
    ChangeUserFrame,
    ChangeToolFrame,
    UserFrame,
    GetPathPilotState,
    GetGlobalWaypoint,
    SetGlobalWaypoint,
    SetUnits,
    GetUnits,
    SetPathBlending,
    SetMachineFrame,
    SetParam,
    GetParam,
    DeleteParam,
    LoadTrajectory,
    ExecuteTrajectory,
    SaveTrajectory,
    ToLocalPose,
    RegisterInterrupt,
    TriggerInterrupt,
    ActuateGripper,
    GetGripperPosition,
    AllowedConfigurations,
    deprecated_command(SetUserFrame, 'set_work_offset'),
    deprecated_command(SetToolFrame, 'set_tool_offset'),
    deprecated_command(GetUserFrame, 'get_work_offset'),
    deprecated_command(GetToolFrame, 'get_tool_offset'),
    deprecated_command(ChangeUserFrame, 'change_work_offset'),
    deprecated_command(ChangeToolFrame, 'change_tool_offset'),
    deprecated_command(SetMachineFrame, 'set_machine_offset'),
    deprecated_command(UserFrame, 'work_offset'),
]
