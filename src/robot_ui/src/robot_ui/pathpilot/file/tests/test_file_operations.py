import os

import pytest

from robot_ui.pathpilot.file import FileOperations


@pytest.fixture
def directory(tmpdir):
    dir_ = tmpdir.mkdir("eager")
    dir_.join('file1.py').write('coffee')
    dir_.join('file2.py').write('tea')
    subdir = dir_.mkdir('subdir')
    subdir.join('file3.tmp').write('mate')
    subdir.mkdir('subdir2')
    return dir_


@pytest.fixture
def directory2(tmpdir):
    return tmpdir.mkdir("feel")


def test_creating_a_new_folder_works(directory):
    operations = FileOperations(path=str(directory))

    result = operations.createFolder('new_folder')

    assert 'new_folder' in os.listdir(str(directory))
    assert result is True


def test_creating_new_folder_that_already_exists_fails(directory):
    operations = FileOperations(path=str(directory))

    result = operations.createFolder('subdir')

    assert result is False


def test_deleting_file_and_folder_selection_works(directory):
    operations = FileOperations(path=str(directory))
    operations.files = ['subdir', 'file2.py']

    result = operations.deleteAll()

    files = os.listdir(str(directory))
    assert 'subdir' not in files
    assert 'file2.py' not in files
    assert result is True


def test_deleting_file_that_does_not_exist_fails(directory):
    operations = FileOperations(path=str(directory))
    operations.files = ['notexistent.file']

    result = operations.deleteAll()

    assert result is False


def test_deleting_broken_selection_fails(directory):
    operations = FileOperations(path=str(directory))
    operations.files = [None]

    result = operations.deleteAll()

    assert result is False


def test_renaming_directory_works(directory):
    operations = FileOperations(path=str(directory))
    operations.files = ['subdir']

    result = operations.rename('newname')

    files = os.listdir(str(directory))
    assert 'newname' in files
    assert result is True


def test_renaming_directory_that_does_not_exist_fails(directory):
    operations = FileOperations(path=str(directory))
    operations.files = ['nonexistent']

    result = operations.rename('newname')

    assert result is False


def test_copying_files_and_directories_works(directory, directory2):
    operations = FileOperations(path=str(directory))
    operations.files = ['file1.py', 'subdir']

    result = operations.copyTo(str(directory2))

    assert result is True
    assert str(directory) != str(directory2)
    files = os.listdir(str(directory2))
    assert 'file1.py' in files
    assert 'subdir' in files
    files2 = os.listdir(os.path.join(str(directory2), 'subdir'))
    assert 'file3.tmp' in files2


def test_copying_files_and_directories_that_do_not_exist_fails(
    directory, directory2
):
    operations = FileOperations(path=str(directory))
    operations.files = ["wonder.py"]

    result = operations.copyTo(str(directory2))

    assert result is False


def test_copy_to_path_that_does_not_exist_fails(directory, directory2):
    operations = FileOperations(path=str(directory))
    operations.files = ['file2.py']

    result = operations.copyTo(os.path.join(str(directory2), "dnW"))

    assert result is False


def test_moving_files_and_directories_works(directory, directory2):
    operations = FileOperations(path=str(directory))
    operations.files = ['file1.py', 'subdir']

    result = operations.moveTo(str(directory2))

    assert result is True
    assert str(directory) != str(directory2)
    files = os.listdir(str(directory2))
    assert 'file1.py' in files
    assert 'subdir' in files
    files2 = os.listdir(os.path.join(str(directory2), 'subdir'))
    assert 'file3.tmp' in files2
    files = os.listdir(str(directory))
    assert 'file1.py' not in files
    assert 'subdir' not in files


def test_moving_files_and_directories_that_do_not_exist_fails(
    directory, directory2
):
    operations = FileOperations(path=str(directory))
    operations.files = ["wonder.py"]

    result = operations.moveTo(str(directory2))

    assert result is False


def test_moving_to_path_that_does_not_exist_fails(directory, directory2):
    operations = FileOperations(path=str(directory))
    operations.files = ['file2.py']

    result = operations.moveTo(os.path.join(str(directory2), "dnW"))

    assert result is False
