import pytest
from unittest.mock import MagicMock

from robot_command.interfaces import global_waypoint_interface
from robot_command.rpl import Pose, Joints
from robot_command.rpl.units import ureg


@pytest.fixture
def waypoint_interface():
    global_waypoint_interface.GlobalWaypointInterfaceSingleton._instance = None
    interface = global_waypoint_interface.GlobalWaypointInterfaceSingleton()
    interface._instance._config = MagicMock()
    return interface


def test_getting_global_pose_waypoint_works(waypoint_interface):
    waypoint_interface._config.get_param.return_value = [
        "POSE",
        [368.44, -612.34, 76.93, 517.06, -748.71, 92.50],
    ]

    pose = waypoint_interface.get_global_waypoint('sluggard')

    assert isinstance(pose, Pose)
    assert pose.x.magnitude == pytest.approx(368.44)
    assert pose.x.units == ureg.meters
    assert pose.y.magnitude == pytest.approx(-612.34)
    assert pose.y.units == ureg.meters
    assert pose.z.magnitude == pytest.approx(76.93)
    assert pose.z.units == ureg.meters
    assert pose.a.magnitude == pytest.approx(517.06)
    assert pose.a.units == ureg.radian
    assert pose.b.magnitude == pytest.approx(-748.71)
    assert pose.b.units == ureg.radian
    assert pose.c.magnitude == pytest.approx(92.50)
    assert pose.c.units == ureg.radian


def test_getting_global_joints_waypoint_works(waypoint_interface):
    waypoint_interface._config.get_param.return_value = [
        "JOINTS",
        [920.00, 54.21, -640.51, 671.22, 530.15, -983.97],
    ]

    joints = waypoint_interface.get_global_waypoint('accise')

    assert isinstance(joints, Joints)
    assert joints.j1.magnitude == pytest.approx(920.00)
    assert joints.j1.units == ureg.radian
    assert joints.j2.magnitude == pytest.approx(54.21)
    assert joints.j2.units == ureg.radian
    assert joints.j3.magnitude == pytest.approx(-640.51)
    assert joints.j3.units == ureg.radian
    assert joints.j4.magnitude == pytest.approx(671.22)
    assert joints.j4.units == ureg.radian
    assert joints.j5.magnitude == pytest.approx(530.15)
    assert joints.j5.units == ureg.radian
    assert joints.j6.magnitude == pytest.approx(-983.97)
    assert joints.j6.units == ureg.radian


def test_setting_global_pose_waypoint_works(waypoint_interface):
    pose = Pose(-76.68, 999.77, -624.53, 835.34, 545.13, 956.08)

    waypoint_interface.set_global_waypoint('oxyaphia', pose)

    result = waypoint_interface._config.set_param.call_args[0]
    assert len(result) == 2
    name, entry = result
    assert name == 'global_waypoints/oxyaphia'
    assert entry[0] == 'POSE'
    assert entry[1] == pose.to_list()


def test_setting_global_joints_waypoint_works(waypoint_interface):
    joints = Joints(-987.36, 266.78, 545.17, 238.99, 687.66, 905.20)

    waypoint_interface.set_global_waypoint('gotched', joints)

    result = waypoint_interface._config.set_param.call_args[0]
    assert len(result) == 2
    name, entry = result
    assert name == 'global_waypoints/gotched'
    assert entry[0] == 'JOINTS'
    assert entry[1] == joints.to_list()
