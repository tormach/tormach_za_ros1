import pytest
from unittest.mock import MagicMock

from robot_command.waypoint import TargetType
from robot_command.global_waypoints import GlobalWaypoints


@pytest.fixture
def waypoints():
    waypoints = GlobalWaypoints()
    waypoints._config = MagicMock()
    waypoints._config.on_update_received = []
    return waypoints


@pytest.fixture
def waypoints_subscribed():
    waypoints = GlobalWaypoints(subscribe=True)
    cbs = waypoints._config.on_update_received
    waypoints._config = MagicMock()
    waypoints._config.on_update_received = cbs
    return waypoints


def test_reading_waypoints_from_store_works(waypoints):
    waypoints._config.get_param.return_value = {
        "mutatis": ["POSE", [514, -187, 780, 524, -584, 835]],
        "carpale": ["JOINTS", [-373, 103, -632, 507, 850, 603]],
    }

    waypoints.read_from_store()

    assert len(waypoints.waypoints) == 2
    assert waypoints.waypoints[0].name == "mutatis"
    assert waypoints.waypoints[0].target_type == TargetType.Pose
    assert waypoints.waypoints[0].target == [514, -187, 780, 524, -584, 835]
    assert waypoints.waypoints[1].name == "carpale"
    assert waypoints.waypoints[1].target_type == TargetType.Joints
    assert waypoints.waypoints[1].target == [-373, 103, -632, 507, 850, 603]


def test_writing_waypoints_to_store_works(waypoints):
    waypoints._config.get_param.return_value = {}

    waypoint = waypoints.create_waypoint()
    waypoint.name = 'nooklike'
    waypoint.target_type = TargetType.Pose
    waypoint.target = [689, -151, 437, -914, 28, 641]

    waypoint = waypoints.create_waypoint()
    waypoint.name = 'oodlins'
    waypoint.target_type = TargetType.Joints
    waypoint.target = [29, 703, 437, 614, 742, 899]

    waypoints.write_to_store()

    assert waypoints._config.set_param.call_count == 2
    assert (
        waypoints._config.set_param.mock_calls[0][1][0]
        == 'global_waypoints/nooklike'
    )
    assert waypoints._config.set_param.mock_calls[0][1][1] == [
        "POSE",
        [689, -151, 437, -914, 28, 641],
    ]
    assert (
        waypoints._config.set_param.mock_calls[1][1][0]
        == 'global_waypoints/oodlins'
    )
    assert waypoints._config.set_param.mock_calls[1][1][1] == [
        "JOINTS",
        [29, 703, 437, 614, 742, 899],
    ]


def test_additional_waypoints_are_removed_from_store(waypoints):
    waypoints._config.get_param.return_value = {
        "novative": ["POSE", [514, -187, 780, 524, -584, 835]]
    }

    waypoint = waypoints.create_waypoint()
    waypoint.name = 'clepsine'
    waypoint.target_type = TargetType.Pose
    waypoint.target = [923, 259, 658, 211, 79, 151]

    waypoints.write_to_store()

    assert waypoints._config.delete_param.call_count == 1
    assert (
        waypoints._config.delete_param.mock_calls[0][1][0]
        == 'global_waypoints/novative'
    )


@pytest.fixture
def sample_waypoints(waypoints):
    waypoint = waypoints.create_waypoint()
    waypoint.name = 'exergues'
    waypoint.target_type = TargetType.Joints
    waypoint.target = [487, 689, 276, 173, 201, 412]
    return waypoints


def test_copying_the_global_waypoints_creates_a_deepcopy_of_the_waypoints(
    sample_waypoints,
):
    sample_waypoints._config.get_param.return_value = {}
    waypoints = GlobalWaypoints()

    sample_waypoints.copy_data_to(waypoints)

    assert len(waypoints.waypoints) == 1
    assert waypoints.waypoints[0] is not sample_waypoints.waypoints[0]


def test_copying_the_global_waypoints_does_not_change_the_uuids_of_the_waypoints(
    sample_waypoints,
):
    sample_waypoints._config.get_param.return_value = {}
    waypoints = GlobalWaypoints()

    sample_waypoints.copy_data_to(waypoints)

    assert len(waypoints.waypoints) == 1
    assert waypoints.waypoints[0].uuid == sample_waypoints.waypoints[0].uuid


def test_config_updated_triggers_read_from_store(waypoints_subscribed):
    for cb in waypoints_subscribed._config.on_update_received:
        cb(GlobalWaypoints.NAMESPACE, None)

    assert (
        waypoints_subscribed._config.get_param.mock_calls[0][1][0]
        == GlobalWaypoints.NAMESPACE
    )
