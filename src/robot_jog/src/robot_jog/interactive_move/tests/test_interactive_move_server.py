import pytest
import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, Pose
from unittest.mock import MagicMock

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from actionlib_msgs.msg import GoalStatus
from robot_jog_msgs.srv import (
    SetPoseResponse,
    SetJointsResponse,
    SetPoseRequest,
    SetJointsRequest,
)
from robot_jog_msgs.msg import JogExecute
from sensor_msgs.msg import JointState

import robot_common.joint_urdf
from robot_command.interfaces import moveit_interface
from robot_command import interfaces


@pytest.fixture(scope="session", autouse=True)
def ros_node():
    rospy.init_node('test_node', anonymous=True)


@pytest.fixture
def moveit_mock(mocker):  # noqa: F811
    mocker.patch.object(interfaces, 'MoveItInterface')
    mocker.patch.object(interfaces, 'JointsToPoseInterface')
    mocker.patch.object(interfaces, 'IkInterface')
    mocker.patch.object(interfaces, 'UserFrameInterface')
    mocker.patch.object(interfaces, 'ToolFrameInterface')
    mocker.patch.object(interfaces, 'MoveTypeInterface')
    mocker.patch.object(interfaces, 'MoveTypeInterfaceSingleton')
    return interfaces.MoveItInterface()


def patch_rospy():
    rospy.get_param = lambda key, default=None: 1.0  # jog rate
    rospy.Service = MagicMock()
    rospy.Subscriber = MagicMock()
    rospy.Publisher = MagicMock()
    rospy.ServiceProxy = MagicMock()


def patch_tf():
    tf2_ros.Buffer = MagicMock()
    tf2_ros.TransformListener = MagicMock()


def patch_free_joints():
    robot_common.joint_urdf.read_robot_description_free_joints = (
        lambda *_, **__: {}
    )


def patch_moveit_pose(move, pose, position_tolerance, orientation_tolerance):
    move._joints_to_pose.get_current_pose = lambda: pose
    move._moveit.goal_orientation_tolerance = orientation_tolerance
    move._moveit.goal_position_tolerance = position_tolerance


def patch_moveit_joints(move, names, values, tolerance):
    move._joints_to_pose.get_active_joints = lambda: names
    move._joints_to_pose.get_current_joint_state = lambda: JointState(
        name=names, position=values
    )
    move._moveit.goal_joint_tolerance = tolerance


@pytest.fixture
def move(moveit_mock):
    patch_rospy()
    patch_tf()
    patch_free_joints()
    from robot_jog import InteractiveMoveServer

    move = InteractiveMoveServer()
    move._moveit.compare_poses = moveit_interface.MoveItInterface.compare_poses
    move._moveit.compare_joints = (
        moveit_interface.MoveItInterface.compare_joints
    )
    move._moveit.pose_reference_frame = ""
    move._user_frames.active_frame_frame = ""
    move._tool_frames.active_frame = ""
    move._active_pub = MagicMock()
    move._failed_pub = MagicMock()
    move._completed_pub = MagicMock()
    move._target_type = move.JointsTarget
    move._completed = False
    move._start_timeout_timer = lambda: None
    move._start_stop_timer = lambda: None

    def plan_fb(*_args, **_kwargs):
        return True, None, 0.0, 0

    move._moveit.plan = plan_fb

    yield move

    move.shutdown()


@pytest.mark.dependency()
def test_move_is_activated_when_receiving_start(move):
    move._on_jog_execute_received(JogExecute(execute=True))

    assert move._active is True


def test_completed_and_reset_are_cleared_when_pose_is_set(move):
    patch_moveit_pose(move, PoseStamped(), 0.001, 0.01)
    move._completed = True
    move._failed = True

    req = SetPoseRequest(frame_name='', axis_names=[], values=[])
    move._jog_offset_set_pose(req)

    assert not move._completed
    assert not move._failed
    assert move._completed_pub.publish.call_count == 1
    assert move._failed_pub.publish.call_count == 1


def test_moveit_pose_target_is_set_when_setting_offset_pose(move):
    pose = PoseStamped()
    pose.pose.position.x = 10.0
    pose.pose.position.y = 204.90
    pose.pose.position.z = -100.0
    patch_moveit_pose(move, pose, 0.001, 0.01)

    req = SetPoseRequest(
        frame_name='', axis_names=['x', 'z'], values=[999.15, 304.80]
    )
    res = move._jog_offset_set_pose(req)

    assert res == SetPoseResponse(success=True, is_current=False)
    assert isinstance(move._targets[-1], Pose)
    pose = move._targets[-1]
    assert pose.position.x == pytest.approx(1009.15)
    assert pose.position.y == pytest.approx(204.9)
    assert pose.position.z == pytest.approx(204.8)


def test_moveit_pose_target_is_set_when_setting_absolute_pose(move):
    pose = PoseStamped()
    pose.pose.position.x = 31.62
    pose.pose.position.y = 819.47
    pose.pose.position.z = 477.94
    patch_moveit_pose(move, pose, 0.001, 0.01)

    req = SetPoseRequest(
        frame_name='', axis_names=['y', 'x'], values=[-899.88, 510.48]
    )
    res = move._jog_absolute_set_pose(req)

    assert res == SetPoseResponse(success=True)
    assert isinstance(move._targets[-1], Pose)
    pose = move._targets[-1]
    assert pose.position.y == pytest.approx(-899.88)
    assert pose.position.x == pytest.approx(510.48)
    assert pose.position.z == pytest.approx(477.94)


# TODO: test jog moves


def test_moveit_joint_values_are_set_when_setting_offset_joints(move):
    patch_moveit_joints(
        move,
        ['j1', 'j2', 'j3', 'j4', 'j5', 'j6'],
        [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        0.001,
    )

    req = SetJointsRequest(
        joint_names=['j1', 'j2', 'j3', 'j4', 'j5', 'j6'],
        values=[639.23, 955.85, 183.29, 622.41, 493.98, 874.80],
    )
    res = move._jog_offset_set_joints(req)

    assert res == SetJointsResponse(success=True, is_current=False)
    assert isinstance(move._targets, list)
    values = move._targets
    assert values[0] == pytest.approx(
        [640.23, 957.85, 186.29, 626.41, 498.98, 880.80]
    )


def test_moveit_joint_values_are_set_when_setting_absolute_joints(move):
    patch_moveit_joints(
        move,
        ['j1', 'j2', 'j3', 'j4', 'j5', 'j6'],
        [129.60, 986.45, -600.07, 237.76, 517.77, 698.96],
        0.001,
    )

    req = SetJointsRequest(
        joint_names=['j2', 'j4', 'j1'], values=[-166.05, 183.39, 783.29]
    )
    res = move._jog_absolute_set_joints(req)

    assert res == SetJointsResponse(success=True, is_current=False)
    assert isinstance(move._targets, list)
    values = move._targets
    assert values[0] == pytest.approx(
        [783.29, -166.05, -600.07, 183.39, 517.77, 698.96]
    )


def test_is_current_is_true_when_target_pose_matches_current(move):
    pose = PoseStamped()
    pose.pose.position.x = 337.33
    pose.pose.position.z = 924.63
    pose.pose.orientation.w = 1.0
    patch_moveit_pose(move, pose, 0.1, 0.1)

    req = SetPoseRequest(
        frame_name='', axis_names=['x', 'z'], values=[337.3, 924.6]
    )
    res = move._jog_absolute_set_pose(req)

    assert res == SetPoseResponse(success=True, is_current=True)


def test_is_current_is_true_when_target_joint_values_match_current(move):
    patch_moveit_joints(move, ['j1', 'j2'], [415.23, 400.87], 0.1)

    req = SetJointsRequest(joint_names=['j1', 'j2'], values=[415.25, 400.82])
    res = move._jog_absolute_set_joints(req)

    assert res == SetJointsResponse(success=True, is_current=True)


@pytest.mark.dependency(depends=['test_move_is_activated_when_receiving_start'])
def test_move_is_stopped_and_completed_when_succeeded_is_received(move):
    move._on_jog_execute_received(JogExecute(execute=True))

    move._moveit.execution_status = GoalStatus.SUCCEEDED
    move._on_execution_active_changed(False)

    assert move._active is False
    assert move._completed is True
    assert move._active_pub.publish.call_count == 2
    assert move._completed_pub.publish.call_count == 1


@pytest.mark.dependency(
    name='test_move_is_stopped_and_not_completed_when_move_fails',
    depends=['test_move_is_activated_when_receiving_start'],
)
@pytest.mark.parametrize(
    'status', [GoalStatus.PREEMPTED, GoalStatus.ABORTED, GoalStatus.REJECTED]
)
def test_move_is_stopped_and_not_completed_when_move_fails(move, status):
    move._on_jog_execute_received(JogExecute(execute=True))

    move._moveit.execution_status = status
    move._on_execution_active_changed(False)

    assert move._active is False
    assert move._completed is False
    assert move._failed is True
    assert move._active_pub.publish.call_count == 2
    assert move._failed_pub.publish.call_count == 1


def test_completed_is_not_triggered_when_receiving_success_and_not_active(move):
    move._moveit.execution_status = GoalStatus.SUCCEEDED
    move._on_execution_active_changed(False)

    assert move._completed is False
    assert move._completed_pub.publish.call_count == 0


# @pytest.mark.dependency(
#     depends=[
#         'test_move_is_activated_when_receiving_start',
#         'test_move_is_stopped_and_not_completed_when_move_fails',
#     ]
# )
def test_move_is_restarted_when_start_is_received_again_after_stop(move):
    n_timer_started = 0

    def start_timer():
        nonlocal n_timer_started
        n_timer_started += 1

    move._start_stop_timer = start_timer
    move._on_jog_execute_received(JogExecute(execute=True))
    move._on_jog_execute_received(JogExecute(execute=False))
    move._on_jog_execute_received(JogExecute(execute=True))

    move._moveit.execution_status = GoalStatus.ABORTED
    move._on_execution_active_changed(False)

    # simulate timer tick
    assert n_timer_started == 1
    move._on_stop_timer_tick(None)

    # time.sleep(move.STOP_TIMER_INTERVAL_MS * 2.0)
    assert move._active is True
    assert move._active_pub.publish.call_count == 3


def test_move_is_stopped_after_timeout(move):
    n_timer_started = 0

    def start_timer():
        nonlocal n_timer_started
        n_timer_started += 1

    move._start_timeout_timer = start_timer
    move._on_jog_execute_received(JogExecute(execute=True))

    # simulate timer tick
    assert n_timer_started == 1
    move._on_timeout_timer_tick(None)

    assert move._stop_waiting is True
    assert move._active_pub.publish.call_count == 1


def test_move_is_aborted_when_jog_rate_is_zero(move):
    rospy.get_param = lambda _, __: 0.0
    move._on_jog_execute_received(JogExecute(execute=True))

    assert move._failed is True
    assert move._failed_pub.publish.call_count == 1
