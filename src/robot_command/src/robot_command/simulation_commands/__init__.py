from .movel import MoveL
from .movej import MoveJ
from .movef import MoveF
from .movec import MoveC
from .set_digital_out import SetDigitalOut
from .get_digital_in import GetDigitalIn
from .sync import Sync
from .sleep import Sleep
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


def init():
    pass


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
    GetActiveToolFrame,
    GetToolFrame,
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
]
