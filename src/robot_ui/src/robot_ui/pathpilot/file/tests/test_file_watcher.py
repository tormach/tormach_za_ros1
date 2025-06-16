import os

import pytest
from PySide6.QtCore import QUrl


@pytest.fixture
def watcher():
    from robot_ui.pathpilot.file.file_watcher import FileWatcher

    FileWatcher.CHECK_INTERVAL_MS = 10

    return FileWatcher()


def test_creating_and_writing_file_in_directory_emits_signal(
    qtbot, tmpdir, watcher
):
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True
    watcher.recursive = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        f = tmpdir.join('test.txt')
        f.write('foo')


def test_changing_file_emits_signal(qtbot, tmpdir, watcher):
    f = tmpdir.join('test.txt')
    f.write('foo')
    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(f))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        f.write('bar')


def test_creating_and_writing_file_on_filter_list_doesnt_emit_signal(
    qtbot, tmpdir, watcher
):
    watcher.nameFilters = ['.#*']
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True
    watcher.recursive = False

    with qtbot.assertNotEmitted(
        watcher.fileChanged, wait=watcher.CHECK_INTERVAL_MS * 2
    ):
        f = tmpdir.join('.#test.txt')
        f.write('foo')


def test_renaming_file_emits_signal(qtbot, tmpdir, watcher):
    f = tmpdir.join('supp')
    f.write('pncp0A')
    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        os.rename(str(f), os.path.join(str(tmpdir), 'energist'))


def test_deleting_file_emits_signal(qtbot, tmpdir, watcher):
    f = tmpdir.join('lowered')
    f.write('pncp0A')
    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        os.remove(str(f))


def test_deleting_directory_emits_signal(qtbot, tmpdir, watcher):
    subdir = tmpdir.mkdir('flukily')
    f = subdir.join("yeasts")
    f.write(
        "Wlb2Msh"
    )  # need to create a file inside the tmpdir to force creation
    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        os.remove(str(f))
        os.rmdir(str(subdir))


def test_creating_file_in_subdirectory_emits_signal(qtbot, tmpdir, watcher):
    subdir = tmpdir.mkdir('sub')
    watcher.recursive = True
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        f = subdir.join('hagglers.foo')
        f.write('DNsqu')


def test_symlink_behavior(qtbot, tmpdir, watcher):
    real_file = tmpdir.join('real.txt')
    real_file.write('real content')

    symlink_path = os.path.join(str(tmpdir), 'symlink.txt')
    os.symlink(str(real_file), symlink_path)

    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        with open(symlink_path, 'w') as f:
            f.write('new content')


def test_case_sensitivity(qtbot, tmpdir, watcher):
    f = tmpdir.join('TeSt.txt')
    f.write('foo')

    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        os.rename(str(f), os.path.join(str(tmpdir), 'test.txt'))


def test_rapid_file_changes(qtbot, tmpdir, watcher):
    f = tmpdir.join('rapid.txt')
    f.write('initial content')

    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(f))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        for i in range(100):
            f.write(f'content {i}')


def test_change_file_attributes(qtbot, tmpdir, watcher):
    f = tmpdir.join('attr.txt')
    f.write('content')

    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        os.chmod(str(f), 0o444)  # changing to readonly


def test_nested_directory_behavior(qtbot, tmpdir, watcher):
    deep_dir = tmpdir.mkdir('dir1').mkdir('dir2').mkdir('dir3')

    watcher.recursive = True
    watcher.fileUrl = QUrl('file://' + str(tmpdir))
    watcher.enabled = True

    with qtbot.waitSignal(
        watcher.fileChanged, timeout=watcher.CHECK_INTERVAL_MS * 2
    ):
        f = deep_dir.join('nested.txt')
        f.write('content')


def test_disabling_watcher(qtbot, tmpdir, watcher):
    f = tmpdir.join('test.txt')
    f.write('foo')

    watcher.recursive = False
    watcher.fileUrl = QUrl('file://' + str(f))
    watcher.enabled = False

    with qtbot.assertNotEmitted(
        watcher.fileChanged, wait=watcher.CHECK_INTERVAL_MS * 2
    ):
        f.write('bar')
