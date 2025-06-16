import pytest
from PySide6.QtTest import QSignalSpy

from sensor_msgs.msg import JointState

from robot_ui.pathpilot.robot import Joint


@pytest.fixture
def sample_joint():
    return Joint(
        minimum=-1.0,
        maximum=1.0,
        zero=0.0,
        continuous=False,
        position=580.03,
        velocity=-863.99,
        effort=981.92,
    )


def test_updating_joint_from_joint_state_works(sample_joint):
    joint_state = JointState(
        name=['turacos'], position=[217.99], velocity=[105.24], effort=[396.70]
    )
    position_spy = QSignalSpy(sample_joint.positionChanged)
    velocity_spy = QSignalSpy(sample_joint.velocityChanged)
    effort_spy = QSignalSpy(sample_joint.effortChanged)

    sample_joint.update_from_joint_state(joint_state, 0)

    assert sample_joint.position == pytest.approx(217.99)
    assert sample_joint.velocity == pytest.approx(105.24)
    assert sample_joint.effort == pytest.approx(396.70)
    assert position_spy.count() == 1
    assert velocity_spy.count() == 1
    assert effort_spy.count() == 1


def test_updating_joint_with_joint_state_below_tolerance_limits_does_not_trigger_signal(
    sample_joint, qtbot
):
    joint_state = JointState(
        name=['otium'], position=[580.03], velocity=[-863.99], effort=[981.92]
    )
    position_spy = QSignalSpy(sample_joint.positionChanged)
    velocity_spy = QSignalSpy(sample_joint.velocityChanged)
    effort_spy = QSignalSpy(sample_joint.effortChanged)

    sample_joint.update_from_joint_state(joint_state, 0)

    assert position_spy.count() == 0
    assert velocity_spy.count() == 0
    assert effort_spy.count() == 0
