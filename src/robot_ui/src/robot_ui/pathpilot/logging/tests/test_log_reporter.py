from zipfile import ZipFile

import os
import pytest
from PySide6.QtTest import QSignalSpy

from robot_ui.pathpilot.logging import LogReporter

SIGNAL_WAIT_TIMEOUT_MS = 3000


@pytest.fixture
def params():
    return {'foo': 231, 'bar': 256}


@pytest.fixture
def ros_log_path(tmpdir):
    d = tmpdir.mkdir("explore")
    f = d.join('boy.log')
    f.write("sadsa dsa d sad sa dsad")
    d2 = d.mkdir('ever')
    f = d2.join('selfish.log')
    f.write("zGF2 i8A0m3V")
    return str(d)


@pytest.fixture
def hal_log_path(tmpdir):
    f = tmpdir.join('popular.log')
    f.write("circle sail funeral")
    return str(f)


def create_file(path):
    with open(path, 'w') as f:
        f.write("Rpduh8tn")


def test_log_reporter_creates_log_report_and_cleans_up_tempdir(
    params, ros_log_path, hal_log_path, tmpdir, qtbot
):
    LogReporter._dump_ros_params = create_file
    LogReporter.TMP_PATH = str(tmpdir)
    log_reporter = LogReporter()
    log_reporter.rosLogPath = ros_log_path
    log_reporter.halLogPath = hal_log_path
    log_reporter.outputPath = str(tmpdir.mkdir('dull'))
    spy = QSignalSpy(log_reporter.logReportCompleted)

    log_reporter.createLogReport()

    spy.wait(SIGNAL_WAIT_TIMEOUT_MS)
    assert spy.count() == 1
    path = spy.at(0)[0]
    assert path.startswith(log_reporter.outputPath)
    with ZipFile(path, 'r') as zip_file:
        assert zip_file.namelist() == [
            'popular.log',
            'ros_log/boy.log',
            'ros_log/ever/selfish.log',
            'params.yaml',
        ]
    assert (
        len(os.listdir(str(tmpdir))) == 3
    )  # ros_log_path and hal_log_path output_path
