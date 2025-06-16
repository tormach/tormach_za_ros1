import pytest
from PySide6.QtCore import QObject
from PySide6.QtTest import QSignalSpy

from robot_ui.pathpilot.core.global_object import GlobalObject


@pytest.fixture
def foo():
    return True


def test_default_value_of_global_object_is_none():
    obj = GlobalObject()

    assert obj.object is None


def test_assigning_value_to_global_object_makes_the_value_available_to_others():
    obj1 = GlobalObject(name="foo")
    obj2 = GlobalObject(name="foo")
    target = QObject()

    obj1.object = target

    assert obj2.object is target


def test_assigning_values_to_multiple_global_objects_updates_values_of_others():
    obj1_1 = GlobalObject(name="QXLM")
    obj2_1 = GlobalObject(name="4ZQZUEI")
    obj1_2 = GlobalObject(name="QXLM")
    obj2_2 = GlobalObject(name="4ZQZUEI")
    target1 = QObject()
    target2 = QObject()

    obj1_1.object = target1
    obj2_2.object = target2

    assert obj1_2.object is target1
    assert obj2_1.object is target2


def test_assigning_object_before_name_still_makes_value_available_to_others():
    obj1 = GlobalObject(name="foo")
    obj2 = GlobalObject()
    target = QObject()

    obj2.object = target
    obj2.name = "foo"

    assert obj1.object is target


def test_assigning_value_to_global_object_emits_object_changed_signal():
    obj1 = GlobalObject(name="reded")
    obj2 = GlobalObject(name="reded")
    target = QObject()
    spy = QSignalSpy(obj2.objectChanged)

    obj1.object = target

    assert spy.count() == 1


def test_when_target_object_is_destroyed_global_object_returns_none():
    obj1 = GlobalObject(name="bar")
    target = QObject()
    obj1.object = target

    del target

    assert obj1.object is None
