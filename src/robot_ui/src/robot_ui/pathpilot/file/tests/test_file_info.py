import os

import pytest


@pytest.fixture
def info():
    from robot_ui.pathpilot.file.file_info import FileInfo

    return FileInfo()


def test_absolute_path_is_resolved_from_user_path(info):
    info.path = '~/foo/bar'

    assert info.absolutePath == '{}/foo/bar'.format(os.path.expanduser('~'))


def test_non_existing_file_is_detected_as_non_existing_and_non_file(info):
    info.path = 'pWIekdzo'

    assert info.isFile is False
    assert info.exists is False


def test_existing_file_is_detected_as_file_that_exists(info, tmpdir):
    f = tmpdir.join('27putdC')
    f.write('k8XnqcF2')

    info.path = str(f)

    assert info.isFile is True
    assert info.exists is True
