import pytest
import rospy
from unittest.mock import MagicMock

# noinspection PyUnresolvedReferences
from pytest_mock import mocker  # noqa: F401

from robot_ui.pathpilot.core import Config


@pytest.fixture  # noqa: F811
def config(mocker):  # noqa: F811
    rospy.get_param = lambda key, default=None: {}
    mocker.patch.object(rospy, 'Subscriber')

    config = Config()
    config._config = MagicMock()

    return config


def test_creating_property_map_from_param_dictionary_works(config):
    params = {
        'immure': 605.73,
        'craterid': 'cPy2FHK',
        'acraze': [445, 288, 269, 738, 243],
        'domus': {'erecter': 'eap'},
    }

    config._update_property_map_recursively(config._data, params)

    assert config.data.value('immure') == 605.73
    assert config.data.value('craterid') == 'cPy2FHK'
    assert config.data.value('acraze') == [445, 288, 269, 738, 243]
    assert config.data.value('domus').value('erecter') == 'eap'


def test_if_keys_imported_from_params_are_camel_cased(config):
    params = {'presbyte_starer': 811}

    config._update_property_map_recursively(config._data, params)

    assert config.data.value('presbyteStarer') == 811


def test_setting_user_value_sets_param(config):
    params = {'moz_art': 306, 'cas_sino': {'stalagma': 'vP1'}}
    config._update_property_map_recursively(
        config._user, params, update_base='user_config'
    )

    config.user.valueChanged.emit(
        'mozArt', 300
    )  # have to simulate change from QML
    config.user.value('casSino').valueChanged.emit('stalagma', 'BN0z')
    config.user.valueChanged.emit('shineNiece', 7)

    assert config._config.set_param.call_count == 3
    assert config._config.set_param.mock_calls[0][1][0] == 'user_config/moz_art'
    assert config._config.set_param.mock_calls[0][1][1] == 300
    assert (
        config._config.set_param.mock_calls[1][1][0]
        == 'user_config/cas_sino/stalagma'
    )
    assert config._config.set_param.mock_calls[1][1][1] == 'BN0z'
    assert (
        config._config.set_param.mock_calls[2][1][0]
        == 'user_config/shine_niece'
    )
    assert config._config.set_param.mock_calls[2][1][1] == 7


def test_value_update_from_param_server_updates_user_config(config):
    params = {'peracut_e': {'raga': 496, 'wi_lier': False}, 'inductee': 506.62}
    config._update_property_map_recursively(
        config._user, params, update_base='user_config'
    )

    config._on_update_received('user_config/peracut_e/raga', 123)
    config._on_update_received('user_config/inductee', '9k7W')
    config._on_update_received('user_config/peracut_e/wi_lier', True)

    assert config.user.value('peracutE').value('raga') == 123
    assert config.user.value('inductee') == '9k7W'
    assert config.user.value('peracutE').value('wiLier') is True


def test_value_update_from_param_server_updates_machine_config(config):
    params = {
        'palaqu_r': {'lambish': 882, 'flagcon_ate': 'pewer'},
        'bustor_clag': 42,
    }
    config._update_property_map_recursively(
        config._machine, params, update_base='machine_state'
    )

    def get_param(key, _default=None):
        if key == 'machine_state/palaqu_r/lambish':
            return 456
        if key == 'machine_state/bustor_clag':
            return 'evil_melon'

    rospy.get_param = get_param
    config._on_update_received('machine_state/palaqu_r/lambish', 456)
    config._on_update_received('machine_state/bustor_clag', 'evil_melon')

    assert config.machine.value('palaquR').value('lambish') == 456
    assert config.machine.value('bustorClag') == 'evil_melon'
