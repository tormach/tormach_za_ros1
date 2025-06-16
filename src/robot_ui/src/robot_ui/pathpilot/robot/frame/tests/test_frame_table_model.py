import pytest

from PySide6.QtCore import QObject, Signal
from PySide6.QtTest import QSignalSpy, QAbstractItemModelTester

from robot_ui.pathpilot.robot.frame import FrameTableModel


WAIT_TIMEOUT_MS = 100


@pytest.fixture
def simple_frames():
    return {
        "off": {
            'pose': [632.94, 140.52, 688.89, 384.78, 875.28, 804.80],
            'data': {'description': ""},
        },
        "market": {
            'pose': [102.31, 658.62, 337.36, 729.80, 976.96, 804.80],
            'data': {'description': "deaf shop"},
        },
        "plan": {
            'pose': [796.07, 550.16, 361.22, 754.77, 816.17, 958.59],
            'data': {'description': ""},
        },
    }


@pytest.fixture
def frames(simple_frames):
    class FramesMock(QObject):
        framesChanged = Signal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self.frames = simple_frames

    return FramesMock()


def test_creating_list_model_from_frames_works(frames, qtbot):
    model = FrameTableModel()

    model.frames = frames

    assert model.rowCount() == 3
    assert (
        model.data(model.index(0, 0), FrameTableModel.Roles.NameRole)
        == "market"
    )
    assert model.data(
        model.index(0, 0), FrameTableModel.Roles.PoseRole
    ) == pytest.approx([102.31, 658.62, 337.36, 729.80, 976.96, 804.80])
    assert model.data(
        model.index(0, 0), FrameTableModel.Roles.XRole
    ) == pytest.approx(102.31)
    assert model.data(
        model.index(0, 0), FrameTableModel.Roles.YRole
    ) == pytest.approx(658.62)
    assert model.data(
        model.index(0, 0), FrameTableModel.Roles.ZRole
    ) == pytest.approx(337.36)
    assert model.data(
        model.index(0, 0), FrameTableModel.Roles.ARole
    ) == pytest.approx(729.80)
    assert model.data(
        model.index(0, 0), FrameTableModel.Roles.BRole
    ) == pytest.approx(976.96)
    assert model.data(
        model.index(0, 0), FrameTableModel.Roles.CRole
    ) == pytest.approx(804.80)
    assert (
        model.data(model.index(0, 0), FrameTableModel.Roles.DescriptionRole)
        == "deaf shop"
    )
    assert (
        model.data(model.index(1, 0), FrameTableModel.Roles.NameRole) == "off"
    )
    assert model.data(
        model.index(1, 0), FrameTableModel.Roles.PoseRole
    ) == pytest.approx(
        [632.94, 140.52, 688.89, 384.78, 875.28, 804.80],
    )
    assert (
        model.data(model.index(1, 0), FrameTableModel.Roles.DescriptionRole)
        == ""
    )
    assert (
        model.data(model.index(2, 0), FrameTableModel.Roles.NameRole) == "plan"
    )
    assert model.data(
        model.index(2, 0), FrameTableModel.Roles.PoseRole
    ) == pytest.approx([796.07, 550.16, 361.22, 754.77, 816.17, 958.59])
    assert (
        model.data(model.index(2, 0), FrameTableModel.Roles.DescriptionRole)
        == ""
    )


def test_insert_rows_is_emitted_when_row_is_inserted(frames, qtbot):
    model = FrameTableModel()
    spy = QSignalSpy(model.rowsInserted)
    model.frames = frames

    frames.frames["trade"] = {
        'pose': [554.33, 699.95, 532.10, 442.55, 216.74, 938.49]
    }
    frames.framesChanged.emit()

    spy.wait(WAIT_TIMEOUT_MS)
    assert spy.count() == 1
    assert spy.at(0)[1] == 3  # first
    assert spy.at(0)[2] == 3  # last
    assert (
        model.data(model.index(3, 0), FrameTableModel.Roles.NameRole) == "trade"
    )
    assert model.data(
        model.index(3, 0), FrameTableModel.Roles.PoseRole
    ) == pytest.approx(
        [554.33, 699.95, 532.10, 442.55, 216.74, 938.49],
    )


def test_remove_rows_is_emitted_when_row_is_removed(frames, qtbot):
    model = FrameTableModel()
    spy = QSignalSpy(model.rowsRemoved)
    model.frames = frames

    del frames.frames["off"]
    frames.framesChanged.emit()

    spy.wait(WAIT_TIMEOUT_MS)
    assert spy.count() == 1
    assert spy.at(0)[1] == 1  # first
    assert spy.at(0)[2] == 1  # last
    assert (
        model.data(model.index(1, 0), FrameTableModel.Roles.NameRole) == "plan"
    )


def test_data_changed_is_emitted_when_data_is_changed(frames, qtbot):
    model = FrameTableModel()
    spy = QSignalSpy(model.dataChanged)
    model.frames = frames

    frames.frames["plan"] = {
        'pose': [423.33, 465.30, 730.70, 545.08, 441.08, 196.93]
    }
    frames.framesChanged.emit()
    spy.wait(WAIT_TIMEOUT_MS)
    assert spy.count() == 1
    assert spy.at(0)[0].row() == 2  # first
    assert spy.at(0)[0].column() == 0  # first
    assert spy.at(0)[1].row() == 2  # last
    assert spy.at(0)[1].column() == (model.columnCount() - 1)  # last
    assert model.data(
        model.index(2, 0), FrameTableModel.Roles.PoseRole
    ) == pytest.approx(
        [423.33, 465.30, 730.70, 545.08, 441.08, 196.93],
    )


def test_frame_model_implementation(frames):
    model = FrameTableModel()
    model.frames = frames
    _ = QAbstractItemModelTester(
        model, QAbstractItemModelTester.FailureReportingMode.Warning
    )
