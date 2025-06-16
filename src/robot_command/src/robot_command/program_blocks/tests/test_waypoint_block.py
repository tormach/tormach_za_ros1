import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, WaypointBlock, UserCodeBlock
from robot_command.program_blocks.waypoint_block import TargetType
from movej_ik_server.arm_configs import ArmConfigType


@pytest.fixture
def program():
    prog = RobotProgram(inspector_blocks=(UserCodeBlock,))
    prog.linear_unit_decimals = 2
    prog.angular_unit_decimals = 2
    return prog


def test_waypoint_with_exact_pose_target_is_written_correctly(program):
    root = RootBlock(None, program)
    block = WaypointBlock(None, root)

    block.name = 'oxyaphia'
    block.target = [933.85, 562.01, 311.68, 923.33, 769.44, 722.91]
    block.target_type = TargetType.Pose
    block.arm_config = ArmConfigType.NUT
    block.rev_count = 0
    output = ''.join(block.write())

    assert (
        output
        == 'oxyaphia = p[933.85, 562.01, 311.68, 923.33, 769.44, 722.91, NUT, 0]\n'
    )
    assert True


def test_waypoint_with_exact_pose_target_and_frame_is_written_correctly(
    program,
):
    root = RootBlock(None, program)
    block = WaypointBlock(None, root)

    block.name = 'oxyaphia'
    block.target = [933.85, 562.01, 311.68, 923.33, 769.44, 722.91]
    block.target_type = TargetType.Pose
    block.arm_config = ArmConfigType.NUT
    block.frame = "sample"
    block.rev_count = 0
    output = ''.join(block.write())

    assert (
        output
        == 'oxyaphia = p[933.85, 562.01, 311.68, 923.33, 769.44, 722.91, "sample", NUT, 0]\n'
    )

    assert True


def test_number_pose_values_arm_config_rev_count_are_parsed_correctly(program):
    module = parso.parse('waypoint_1 = p[1.0, 2, 3.0, 4, 5.0, 6, NUT, 0]\n')
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaypointBlock)
    assert result.target == pytest.approx([1.0, 2, 3.0, 4, 5.0, 6])
    assert result.arm_config == ArmConfigType.NUT
    assert result.rev_count == 0
    assert result.name == 'waypoint_1'
    assert result._target_type == TargetType.Pose


def test_number_pose_values_arm_config_rev_count_and_frame_are_parsed_correctly(
    program,
):
    module = parso.parse(
        'waypoint_1 = p[1.0, 2, 3.0, 4, 5.0, 6, "my_frame_name", NUT, 0]\n'
    )
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaypointBlock)
    assert result.target == pytest.approx([1.0, 2, 3.0, 4, 5.0, 6])
    assert result.frame == 'my_frame_name'
    assert result.arm_config == ArmConfigType.NUT
    assert result.rev_count == 0
    assert result.name == 'waypoint_1'
    assert result._target_type == TargetType.Pose


def test_number_pose_values_are_parsed_correctly(program):
    module = parso.parse('waypoint_1 = p[1.0, 2, 3.0, 4, 5.0, 6,]\n')
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaypointBlock)
    assert result.target == pytest.approx([1.0, 2, 3.0, 4, 5.0, 6])
    assert result.name == 'waypoint_1'
    assert result._target_type == TargetType.Pose


def test_number_pose_values_and_frame_is_parsed_correctly(program):
    module = parso.parse(
        'hay = p[327.38, 735.97, 696.67, 991.39, 939.39, 895.31, "song"]\n'
    )
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaypointBlock)
    assert result.target == pytest.approx(
        [327.38, 735.97, 696.67, 991.39, 939.39, 895.31]
    )
    assert result.name == 'hay'
    assert result._target_type == TargetType.Pose
    assert result.frame == 'song'


def test_number_joint_values_are_parsed_correctly(program):
    module = parso.parse(
        'knubbier=j[708.18, -117.47, 711.81, 646.62, -950.74, 44.23]\n'
    )
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaypointBlock)
    assert result.target == pytest.approx(
        [708.18, -117.47, 711.81, 646.62, -950.74, 44.23]
    )
    assert result.name == 'knubbier'
    assert result._target_type == TargetType.Joints


@pytest.mark.parametrize(
    'test_input',
    [
        'break = p[256.79, 495.84, 264.94, 543.15, 777.40]\n',
        'tempt = p[57.53, 733.93, 307.43, 915.48, 477.28, 396.41, 980.15]\n',
        'fond = j[649.29, 913.84, 972.86, 966.46, 355.63, 598.75, "beak"]\n',
    ],
)
def test_incorrect_list_sizes_are_not_detected_as_waypoint(program, test_input):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input', ['grow = p[0, 0.0, 0, pi, pi / 2.0, -pi]\n']
)
def test_non_number_waypoint_values_are_not_detected_as_waypoint(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input',
    [
        'print("hello world")\n',
        'foo.x += [12.3]\n',
        'var_1 = 10\n',
        'new_vise_zero = (1234).foo()\n',
    ],
)
def test_other_command_is_not_mistaken_as_waypoint(program, test_input):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 0


def test_waypoint_with_missing_type_is_ignored(program):
    module = parso.parse(
        'scallops = [183.18, 680.38, 684.51, 817.20, 627.01, 852.73]\n'
    )
    root = RootBlock(module, program)

    result = [n for n in WaypointBlock.read(module.children[0], root)]

    assert len(result) == 0


def test_waypoint_with_pose_target_is_written_correctly(program):
    root = RootBlock(None, program)
    block = WaypointBlock(None, root)

    block.name = 'oxyaphia'
    block.target = [933.85, 562.01, 311.68, 923.33, 769.44, 722.91]
    block.target_type = TargetType.Pose
    output = ''.join(block.write())

    assert (
        output
        == 'oxyaphia = p[933.85, 562.01, 311.68, 923.33, 769.44, 722.91]\n'
    )


def test_waypoint_with_pose_target_and_frame_is_written_correctly(program):
    root = RootBlock(None, program)
    block = WaypointBlock(None, root)

    block.name = 'many'
    block.target = [144.91, 267.6, 327.88, 503.26, 947.13, 704.59]
    block.target_type = TargetType.Pose
    block.frame = 'heighten'
    output = ''.join(block.write())

    assert (
        output
        == 'many = p[144.91, 267.60, 327.88, 503.26, 947.13, 704.59, "heighten"]\n'
    )


def test_waypoint_with_joints_target_is_written_correctly(program):
    root = RootBlock(None, program)
    block = WaypointBlock(None, root)

    block.name = 'foxbane'
    block.target = [485.96, -181.39, 776.56, 456, 224.40, -201.09]
    block.target_type = TargetType.Joints
    output = ''.join(block.write())

    assert (
        output
        == 'foxbane = j[485.96, -181.39, 776.56, 456.00, 224.40, -201.09]\n'
    )
