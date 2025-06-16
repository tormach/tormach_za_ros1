import os

import pytest
from ros_pytest_qt import QtQuickTestWindow

MODULE_PATH = os.path.realpath(os.path.dirname(__file__))


@pytest.fixture
def scale_window():
    import robot_ui.pathpilot.core  # noqa F401

    window = QtQuickTestWindow(visible=True, path=MODULE_PATH)
    window.load_data(
        '''\
import QtQuick 2.0
import pathpilot.core 1.0

Item {
  objectName: "container"
  scale: 0.4

  ScaleDetection {
  }
}
'''
    )
    return window


def test_scale_detection_detects_scale_of_container(scale_window, qtbot):
    scale_detection = scale_window.item(class_='ScaleDetection')

    assert scale_detection._window == scale_window.window
    assert scale_detection.scale == pytest.approx(0.4)


def test_update_forces_update_of_scale(scale_window, qtbot):
    container = scale_window.item(name='container')
    scale_detection = scale_window.item(class_='ScaleDetection')

    container.setProperty('scale', 0.6)
    scale_detection.update()
    assert scale_detection.scale == pytest.approx(0.6)
