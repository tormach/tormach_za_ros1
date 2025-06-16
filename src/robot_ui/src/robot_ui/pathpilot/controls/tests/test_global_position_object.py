import pytest

from PySide6 import QtQuick

from PySide6.QtCore import QPointF
from PySide6.QtGui import QGuiApplication


from robot_ui.pathpilot.controls import (
    GlobalPositionController,
    GlobalPositionObject,
)


@pytest.fixture(scope="session")
def qapp_cls():
    return QGuiApplication


@pytest.fixture
def quick_item(qtbot):
    class MockedQuickItem(QtQuick.QQuickItem):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.position_offset = QPointF(0, 0)
            self.position_scale = 1.0
            self._visible = False

        def mapFromScene(self, point):
            return (
                point / self.position_scale
                - self.position_offset
                - QPointF(self.x(), self.y())
            )

        def mapToScene(self, point):
            return (
                point * self.position_scale
                + self.position_offset
                + QPointF(self.x(), self.y())
            )

        # for some reason setVisible doesn't work on mocked items
        def setVisible(self, value: bool) -> None:
            self._visible = value

        def isVisible(self) -> bool:
            return self._visible

    return MockedQuickItem


def test_position_and_size_update_is_propagated_correctly(quick_item):
    controlled_item = quick_item()
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item

    source_item.setX(100)
    source_item.setY(140)
    source_item.setWidth(23)
    source_item.setHeight(10)

    assert controlled_item.x() == 100
    assert controlled_item.y() == 140
    assert controlled_item.width() == 23
    assert controlled_item.height() == 10


def test_scale_factor_is_detected_and_propagated_correctly(quick_item):
    controlled_item = quick_item()
    source_item = quick_item()
    source_item.position_scale = 0.5
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item

    source_item.setWidth(100)
    source_item.setHeight(200)

    assert controlled_item.width() == 50
    assert controlled_item.height() == 100
    assert pos_object.scale == pytest.approx(0.5)


def test_position_is_only_updated_when_controller_is_active(quick_item):
    controlled_item = quick_item()
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item

    controller.active = False
    source_item.setX(100)

    assert controlled_item.x() == 0


def test_controlled_item_becomes_visible_when_controller_is_active(quick_item):
    controlled_item = quick_item()
    controlled_item.setVisible(False)
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item

    controller.active = True

    assert controlled_item.isVisible()

    controller.active = False

    assert not controlled_item.isVisible()


def test_object_is_inactive_per_default():
    pos_object = GlobalPositionObject()

    assert not pos_object.active


def test_object_becomes_active_when_controller_is_active():
    pos_object = GlobalPositionObject()
    controller = GlobalPositionController()
    controller.target = pos_object

    controller.active = True

    assert pos_object.active

    controller.active = False

    assert not pos_object.active


def test_controlled_item_becomes_invisible_when_controller_is_inactive(
    quick_item,
):
    controlled_item = quick_item()
    controlled_item.setVisible(True)
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item

    controller.active = False

    assert not controlled_item.isVisible()


def test_object_only_accepts_position_changes_of_first_active_object(
    quick_item,
):
    controlled_item = quick_item()
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item
    controller.active = False
    source_item2 = quick_item()
    controller2 = GlobalPositionController()
    controller2.target = pos_object
    controller2.source = source_item2
    controller.active = False

    controller2.active = True
    controller.active = True

    source_item2.setX(10)
    source_item.setX(20)

    assert controlled_item.x() == 10


def test_initial_position_is_used(quick_item):
    controlled_item = quick_item()
    controlled_item.setVisible(True)
    source_item = quick_item()
    source_item.setX(10)
    source_item.setY(15)
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object

    controller.source = source_item

    assert controlled_item.x() == 10
    assert controlled_item.y() == 15


def test_if_target_is_connected_last_it_still_gets_position_and_size_of_controller(
    quick_item,
):
    controlled_item = quick_item()
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item

    controller.active = True
    source_item.setX(10)
    source_item.setY(15)
    pos_object.target = controlled_item

    assert controlled_item.x() == 10
    assert controlled_item.y() == 15


def test_mapping_to_global_position_works(quick_item):
    controlled_item = quick_item()
    controlled_item.setVisible(True)
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item

    source_item.position_offset = QPointF(5, 10)
    controlled_item.position_offset = QPointF(5, 5)
    source_item.setX(5)
    source_item.setY(10)

    assert controlled_item.x() == 5
    assert controlled_item.y() == 15


def test_position_updates_correctly_when_multiple_controllers_change_state(
    quick_item,
):
    controlled_item = quick_item()
    source_item = quick_item()
    pos_object = GlobalPositionObject()
    pos_object.target = controlled_item
    controller = GlobalPositionController()
    controller.target = pos_object
    controller.source = source_item
    controller.active = True
    source_item2 = quick_item()
    controller2 = GlobalPositionController()
    controller2.target = pos_object
    controller2.source = source_item2
    controller2.active = True

    source_item.setX(10)
    source_item2.setX(20)

    assert controlled_item.x() == 10

    controller.active = False

    assert controlled_item.x() == 20
