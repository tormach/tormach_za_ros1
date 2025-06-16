import pytest
from PySide6.QtGui import QValidator

from robot_ui.pathpilot.core import SyntaxValidator


@pytest.mark.parametrize('test_input', ['5', 'x + y', 'hutment()'])
def test_validator_validates_correct_input(test_input):
    validator = SyntaxValidator()

    input_pos = len(test_input) - 1
    state, input_, pos = validator.validateFull(test_input, input_pos)

    assert state == QValidator.Acceptable
    assert pos == input_pos


@pytest.mark.parametrize(
    'test_input', ['hutre(', '3 +', '(00q32', '', ' ', 'as + 1']
)
def test_validator_invalidates_incorrect_input(test_input):
    validator = SyntaxValidator()

    input_pos = len(test_input) - 1
    state, input_, pos = validator.validateFull(test_input, input_pos)

    assert state == QValidator.Invalid
    assert pos == input_pos
