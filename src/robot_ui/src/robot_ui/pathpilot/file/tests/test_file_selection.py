import os

import pytest

from robot_ui.pathpilot.file import FileSelection


@pytest.fixture
def directory(tmpdir):
    tmpdir.join('file1.py').write('coffee')
    tmpdir.join('file2.py').write('tea')
    subdir = tmpdir.mkdir('subdir')
    subdir.join('file3.tmp').write('mate')
    subdir.mkdir('subdir2')
    return tmpdir


def test_files_and_folders_are_counted_correctly(directory):
    selection = FileSelection()
    selection.path = str(directory)
    selection.files = ['subdir', 'file1.py']

    assert selection.fileCount == 2
    assert selection.folderCount == 2


def test_program_path_and_program_selected_is_updated_when_exactly_one_file_is_selected(
    directory,
):
    selection = FileSelection()
    selection.path = str(directory)
    selection.files = ['file2.py']

    assert selection.programPath == os.path.join(str(directory), 'file2.py')
    assert selection.programSelected is True


def test_program_path_and_program_stay_empty_when_multiple_files_selected(
    directory,
):
    selection = FileSelection()
    selection.path = str(directory)
    selection.files = ["care.py", "nuisance.py"]

    assert selection.programPath == ""
    assert selection.programSelected is False
