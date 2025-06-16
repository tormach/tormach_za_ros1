from .rpl_block import (  # noqa: F401
    RPLBlock,
    RPLBlockWalker,
    RPLBlockRootWalker,
)
from .root_block import RootBlock  # noqa: F401
from .endofprogram_block import EndOfProgramBlock  # noqa: F401
from .program_block import ProgramBlock
from .move_block import MoveBlock
from .rplimport_block import RPLImportBlock
from .usercode_block import UserCodeBlock
from .waypoint_block import WaypointBlock

from .pass_block import PassBlock
from .wait_block import WaitBlock
from .set_block import SetBlock
from .if_block import IfBlock
from .loop_block import LoopBlock
from .disabled_block import DisabledBlock
from .notify_block import NotifyBlock
from .pathpilot_block import PathPilotBlock
from .call_block import CallBlock
from .assignment_block import AssignmentBlock
from .frame_block import FrameBlock
from .comment_block import CommentBlock
from .units_block import UnitsBlock
from .gripper_block import GripperBlock

# nodes to be used for parsing
# for best performance sort with ascending order of
# probability to appear in robot program
registered_blocks = (
    MoveBlock,
    WaypointBlock,
    WaitBlock,
    SetBlock,
    AssignmentBlock,
    PathPilotBlock,
    NotifyBlock,
    PassBlock,
    DisabledBlock,
    IfBlock,
    LoopBlock,
    FrameBlock,
    GripperBlock,
    UnitsBlock,
    CallBlock,
    CommentBlock,
    ProgramBlock,
    RPLImportBlock,
    UserCodeBlock,
)
