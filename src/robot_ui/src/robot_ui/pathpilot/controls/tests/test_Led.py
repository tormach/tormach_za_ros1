import os

import pytest
from ros_pytest_qt import QtQuickTestWindow
from PySide6.QtGui import QColor, QGuiApplication

MODULE_PATH = os.path.realpath(os.path.dirname(__file__))


@pytest.fixture(scope="session")
def qapp_cls():
    return QGuiApplication


@pytest.fixture
def led_window(qapp):
    window = QtQuickTestWindow(visible=False, path=MODULE_PATH)
    window.load_data('Led {}')
    return window


def test_led_has_on_color_when_value_is_true(led_window):
    led = led_window.item(class_='Led')
    led.onColor = 'red'
    led.offColor = 'blue'
    led.value = True

    assert led.color == QColor('red')


def test_led_has_off_color_when_value_is_false(led_window):
    led = led_window.item(class_='Led')
    led.onColor = 'red'
    led.offColor = 'blue'
    led.value = False

    assert led.color == QColor('blue')
