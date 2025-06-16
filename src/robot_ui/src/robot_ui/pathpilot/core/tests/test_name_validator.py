import pytest
from PySide6.QtGui import QValidator

from robot_ui.pathpilot.core import NameValidator


@pytest.mark.parametrize('test_input', ['waypoint_1', '_foo', 'fendy'])
def test_validator_validates_correct_input(test_input):
    validator = NameValidator()

    input_pos = len(test_input) - 1
    state, input_, pos = validator.validateFull(test_input, input_pos)

    assert state == QValidator.Acceptable
    assert pos == input_pos


@pytest.mark.parametrize('test_input', ['24_bar', '#4442', '"ada"', "asd asd"])
def test_validator_invalidates_incorrect_input(test_input):
    validator = NameValidator()

    input_pos = len(test_input) - 1
    state, input_, pos = validator.validateFull(test_input, input_pos)

    assert state == QValidator.Invalid
    assert pos == input_pos


def test_validator_invalidates_existing_name():
    validator = NameValidator()
    validator.names = ['dihalo', 'orlando']

    input_pos = 0
    state, input_, pos = validator.validateFull('dihalo', input_pos)

    assert state == QValidator.Invalid
    assert pos == input_pos


def test_validator_validates_existing_name_when_ignored():
    validator = NameValidator()
    validator.names = ['squads', 'waypoint_1']
    validator.ignoredName = 'waypoint_1'

    input_pos = 0
    state, input_, pos = validator.validateFull('waypoint_1', input_pos)

    assert state == QValidator.Acceptable
    assert pos == input_pos


def test_validator_validates_input_when_name_does_not_exist():
    validator = NameValidator()
    validator.names = ['congo', 'caleche', 'chebulic']

    input_pos = 0
    state, input_, pos = validator.validateFull('prolix3', input_pos)

    assert state == QValidator.Acceptable
    assert pos == input_pos


def test_validator_generates_default_name_when_no_name_exists():
    validator = NameValidator()
    validator.defaultPrefix = 'waypoint_'

    name = validator.generateDefaultName()

    assert name == 'waypoint_1'


def test_validator_increases_number_when_name_exists():
    validator = NameValidator()
    validator.names = ['waypoint_1']
    validator.defaultPrefix = 'waypoint_'

    name = validator.generateDefaultName()

    assert name == 'waypoint_2'
