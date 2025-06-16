import pytest

from robot_command import RobotProgram
from robot_command.program_blocks import WaypointBlock, UserCodeBlock, RootBlock
from robot_command.waypoint import Waypoint, TargetType


@pytest.fixture
def root_node():
    program = RobotProgram(inspector_blocks=(UserCodeBlock,))
    return RootBlock(None, program)


def test_converting_waypoint_node_with_pose_target_to_node_works(root_node):
    node = WaypointBlock(
        node=None,
        parent=root_node,
        name='corky',
        target=[215.11, -963, 414.14, -703.77, 853.75, 251],
        frame='beyond',
        target_type=TargetType.Pose,
    )

    waypoint = Waypoint.from_waypoint_block(node)

    assert waypoint.target == [215.11, -963, 414.14, -703.77, 853.75, 251]
    assert waypoint.target is not node.target
    assert waypoint.target_type == TargetType.Pose
    assert waypoint.name == 'corky'
    assert waypoint.frame == 'beyond'


def test_converting_waypoint_node_with_joints_target_to_node_works(root_node):
    node = WaypointBlock(
        node=None,
        parent=root_node,
        name='linalols',
        target=[-919.96, 52.11, 619, 405.52, -532.80, 428.18],
        target_type=TargetType.Joints,
    )

    waypoint = Waypoint.from_waypoint_block(node)

    assert waypoint.target == [-919.96, 52.11, 619, 405.52, -532.80, 428.18]
    assert waypoint.target is not node.target
    assert waypoint.target_type == TargetType.Joints
    assert waypoint.name == 'linalols'


def test_converting_waypoint_with_joints_target_to_waypoint_node_works(
    root_node,
):
    waypoint = Waypoint(
        name='artsy',
        target=[611, 606.71, -496.34, 632.65, 880.4, 781.34],
        target_type=TargetType.Joints,
    )

    node = waypoint.to_waypoint_block(root_node)

    assert node.name == 'artsy'
    assert node.target == [611, 606.71, -496.34, 632.65, 880.4, 781.34]
    assert node.target is not waypoint.target
    assert node.target_type == TargetType.Joints


def test_converting_waypoint_with_pose_target_to_waypoint_node_works(root_node):
    waypoint = Waypoint(
        name='nell',
        target=[720.52, -101, 999.73, 511.20, -550.38, 744.63],
        target_type=TargetType.Pose,
        frame='frequent',
    )

    node = waypoint.to_waypoint_block(root_node)

    assert node.name == 'nell'
    assert node.target == [720.52, -101, 999.73, 511.20, -550.38, 744.63]
    assert node.target is not waypoint.target
    assert node.target_type == TargetType.Pose
    assert node.frame == 'frequent'
