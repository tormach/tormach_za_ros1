import pytest

from PySide6.QtCore import QObject

from robot_ui.pathpilot.robot.hal import HalIoGroup, HalPin


@pytest.mark.dependency()
def test_io_component_per_default_adds_all_hal_pin_children_as_pins():
    component = HalIoGroup()
    pin1 = HalPin(parent=component, name='amigo')
    pin2 = HalPin(parent=component, name='wezen')

    component.update()

    assert len(component.pins) == 2
    assert pin1 in component.pins
    assert pin2 in component.pins


def test_io_component_searches_other_container_for_pins():
    component = HalIoGroup()
    container = QObject()
    pin1 = HalPin(parent=component, name='amigo')
    pin2 = HalPin(parent=container, name='wezen')
    component.containerItem = container

    component.update()

    assert len(component.pins) == 1
    assert pin1 not in component.pins
    assert pin2 in component.pins


@pytest.mark.dependency(
    depends=['test_io_component_per_default_adds_all_hal_pin_children_as_pins']
)
def test_io_component_does_not_add_different_objects_as_pins():
    component = HalIoGroup()
    QObject(parent=component)

    component.update()

    assert len(component.pins) == 0


@pytest.mark.dependency(
    depends=['test_io_component_per_default_adds_all_hal_pin_children_as_pins']
)
def test_io_component_adds_nested_objects_as_pins():
    component = HalIoGroup()
    object1 = QObject(parent=component)
    pin1 = HalPin(name='floruits', parent=object1)

    component.update()

    assert len(component.pins) == 1
    assert pin1 in component.pins


@pytest.mark.dependency(
    depends=['test_io_component_per_default_adds_all_hal_pin_children_as_pins']
)
def test_io_component_does_not_add_disabled_pins_or_pins_without_name():
    component = HalIoGroup()
    HalPin(parent=component)
    HalPin(name='snape', parent=component, enabled=False)

    component.update()

    assert len(component.pins) == 0


@pytest.mark.dependency()
def test_io_component_adds_pins_by_name():
    component = HalIoGroup()
    pin1 = HalPin(parent=component, name='council')
    component.update()

    assert component.pinsByName.value('council') is pin1


@pytest.mark.dependency(depends=['test_io_component_adds_pins_by_name'])
def test_io_component_removes_pin_after_update():
    component = HalIoGroup()
    pin1 = HalPin(parent=component, name='suresby')
    component.update()
    pin1.setParent(None)
    component.update()

    assert component.pinsByName.value('suresby') is None
