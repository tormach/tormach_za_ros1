import pytest
import rospy
from unittest.mock import MagicMock

from robot_ui.pathpilot.robot.digital_ios import DigitalIOs


@pytest.fixture
def ios():
    ios = DigitalIOs()
    ios._config = MagicMock()
    return ios


@pytest.fixture
def patch_rospy():
    def get_param(key, _):
        if key == 'io/digital_in_names':
            return {'patamar': 1, 'prorump': 3}
        if key == 'io/digital_out_names':
            return {'forehead': 2}
        if key == 'io/digital_in_topics':
            return [
                'hal_io/digital_in_1',
                'hal_io/digital_in_2',
                'hal_io/digital_in_3',
            ]
        if key == 'io/digital_out_topics':
            return ['hal_io/digital_out_1', 'hal_io/digital_out_2']

    rospy.get_param = get_param


def test_reading_ios_from_params_work(ios, patch_rospy):
    ios.update()

    assert len(ios.digitalInputs) == 3
    assert ios.digitalInputs[0].name == 'patamar'
    assert ios.digitalInputs[0].number == 1
    assert ios.digitalInputs[0].topic == 'hal_io/digital_in_1'
    assert ios.digitalInputs[1].name == ''
    assert ios.digitalInputs[1].number == 2
    assert ios.digitalInputs[1].topic == 'hal_io/digital_in_2'
    assert len(ios.digitalOutputs) == 2
    assert ios.digitalOutputs[0].name == ''
    assert ios.digitalOutputs[0].number == 1
    assert ios.digitalOutputs[0].topic == 'hal_io/digital_out_1'
    assert ios.digitalOutputs[1].name == 'forehead'
    assert ios.digitalOutputs[1].number == 2
    assert ios.digitalOutputs[1].topic == 'hal_io/digital_out_2'


def test_updating_digital_in_name_sets_parameter(ios, patch_rospy):
    ios.update()

    ios.digitalInputs[1].name = 'splunt'

    assert ios._config.set_param.call_count == 1
    assert ios._config.set_param.mock_calls[0][1][0] == 'io/digital_in_names'
    assert ios._config.set_param.mock_calls[0][1][1].get('splunt') == 2


def test_updating_digital_out_name_sets_parameter(ios, patch_rospy):
    ios.update()

    ios.digitalOutputs[0].name = 'cameral'

    assert ios._config.set_param.call_count == 1
    assert ios._config.set_param.mock_calls[0][1][0] == 'io/digital_out_names'
    assert ios._config.set_param.mock_calls[0][1][1].get('cameral') == 1


def test_setting_digital_input_name_to_empty_string_clears_parameter(
    ios, patch_rospy
):
    ios.update()

    ios.digitalInputs[0].name = ''

    assert ios._config.set_param.call_count == 1
    assert ios._config.set_param.mock_calls[0][1][0] == 'io/digital_in_names'
    assert ios._config.set_param.mock_calls[0][1][1].get('patamar') is None


def test_setting_digital_output_name_to_empty_string_clears_parameter(
    ios, patch_rospy
):
    ios.update()

    ios.digitalOutputs[1].name = ''

    assert ios._config.set_param.call_count == 1
    assert ios._config.set_param.mock_calls[0][1][0] == 'io/digital_out_names'
    assert ios._config.set_param.mock_calls[0][1][1].get('forehead') is None
