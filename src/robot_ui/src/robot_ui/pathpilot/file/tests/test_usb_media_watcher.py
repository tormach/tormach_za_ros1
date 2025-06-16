import os
import pytest


@pytest.fixture
def watcher():
    from robot_ui.pathpilot.file import UsbMediaWatcher

    UsbMediaWatcher.CHECK_INTERVAL_MS = 10

    return UsbMediaWatcher()


@pytest.mark.dependency()
def test_empty_mount_directory_is_detected_as_not_mounted(
    watcher, tmpdir, qtbot
):
    watcher.path = str(tmpdir)

    assert not watcher.usbMounted
    assert watcher.usbPath == ""
    assert watcher.mediaName == ""


def test_when_folder_is_added_to_mount_directory_usb_media_is_detected(
    watcher,
    tmpdir,
    qtbot,
):
    watcher.path = str(tmpdir)

    with qtbot.waitSignal(
        watcher.usbMountedChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        sub_path = tmpdir.mkdir("dear")

    assert watcher.usbMounted
    assert watcher.usbPath == str(sub_path)
    assert watcher.mediaName == "dear"


def test_when_folder_is_removed_from_mount_directory_usb_media_is_removed(
    watcher, tmpdir, qtbot
):
    sub_path = str(tmpdir.mkdir("happen"))
    watcher.path = str(tmpdir)

    with qtbot.waitSignal(
        watcher.usbMountedChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        os.rmdir(sub_path)

    assert not watcher.usbMounted
    assert watcher.usbPath == ""
    assert watcher.mediaName == ""
