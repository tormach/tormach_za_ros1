import os

from robot_ui.pathpilot.file.temporary_directory import TemporaryDirectory
from PySide6.QtTest import QSignalSpy

SIGNAL_WAIT_TIMEOUT = 50


def test_temporary_directory_is_created():
    temp_dir = TemporaryDirectory()

    assert temp_dir.path


def test_temporary_directory_is_cleaned_up(qtbot):
    temp_dir = TemporaryDirectory()
    spy = QSignalSpy(temp_dir.destroyed)
    dir_path = temp_dir.path
    file_path = temp_dir.createFilePath("faint")
    with open(file_path, 'w') as f:
        f.write("Df3H")

    temp_dir.deleteLater()
    spy.wait(SIGNAL_WAIT_TIMEOUT)

    assert not os.path.exists(dir_path)
    assert not os.path.exists(file_path)
