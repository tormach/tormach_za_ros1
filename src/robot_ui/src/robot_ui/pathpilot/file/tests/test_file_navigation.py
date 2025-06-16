import os

import pytest

from robot_ui.pathpilot.file import FileNavigation


@pytest.fixture
def directory(tmpdir):
    sub = tmpdir.mkdir('subdir1')
    sub.mkdir('subdir2')
    return tmpdir


def test_moving_back_moves_to_containing_directory(directory):
    path = str(directory)
    subpath = os.path.join(path, 'subdir1')
    navigation = FileNavigation(home_path=path, current_path=subpath)

    navigation.navigateBack()

    assert navigation.currentPath == path


def test_moving_back_does_not_move_beyond_home_directory(directory):
    path = str(directory)
    navigation = FileNavigation(home_path=path + '/', current_path=path)

    navigation.navigateBack()

    assert navigation.currentPath == path


def test_setting_paths_expands_the_paths():
    path = '~/foo'
    subpath = os.path.join(path, 'subdir1')
    navigation = FileNavigation(home_path=path, current_path=subpath)

    assert '~' not in navigation.homePath
    assert '~' not in navigation.currentPath
    assert navigation.homePath in navigation.currentPath


def test_disabling_absolute_property_leaves_paths_untouched():
    path = 'chair'
    subpath = os.path.join(path, 'press')
    navigation = FileNavigation(
        home_path=path, current_path=subpath, absolute=False
    )

    assert navigation.homePath == path
    assert navigation.currentPath == subpath


def test_empty_path_is_not_expanded():
    navigation = FileNavigation(home_path='', current_path='')

    assert navigation.homePath == ''
    assert navigation.currentPath == ''
