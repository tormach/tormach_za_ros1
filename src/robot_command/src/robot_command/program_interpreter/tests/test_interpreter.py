import pytest
import traceback
import os

import robot_command.rpl
from robot_command.program_interpreter import InterpreterProcess


def test_format_limited_traceback_limits_traceback_to_internal_modules():
    tb = (
        traceback.FrameSummary("something.py", 5, "cool_function"),
        traceback.FrameSummary(
            os.path.join(
                os.path.dirname(robot_command.rpl.__file__), 'file.py'
            ),
            10,
            "name",
        ),
        traceback.FrameSummary(
            os.path.join(
                os.path.dirname(robot_command.rpl.__file__), 'file2.py'
            ),
            20,
            "name2",
        ),
    )

    output = InterpreterProcess.format_limited_traceback(
        ZeroDivisionError, ZeroDivisionError("foo bar"), tb
    )

    lines = output.split("\n")
    assert len(lines) == 3
    assert 'File "something.py", line 5, in cool_function' in lines[0]
    assert "ZeroDivisionError: foo bar" in lines[1]


@pytest.mark.parametrize(
    "source_method, print_method",
    [
        ("on_abort", "on_abort"),
        ("on_pause", "on_pause"),
        ("<module>", "my_program.py"),
    ],
)
def test_format_limited_traceback_limits_traceback_to_robot_program_level(
    source_method, print_method
):
    tb = (
        traceback.FrameSummary("interpreter.py", 1, "launch_program"),
        traceback.FrameSummary("my_program.py", 2, source_method),
        traceback.FrameSummary("something.py", 5, "cool_function"),
    )

    output = InterpreterProcess.format_limited_traceback(
        ZeroDivisionError, ZeroDivisionError("foo bar"), tb
    )

    lines = output.split("\n")
    assert len(lines) == 4
    assert f'File "my_program.py", line 2, in {print_method}' in lines[0]
    assert 'File "something.py", line 5, in cool_function' in lines[1]
    assert "ZeroDivisionError: foo bar" in lines[2]


def test_format_limited_traceback_limits_traceback_of_interrupts():
    tb = (
        traceback.FrameSummary("interpreter.py", 1, "launch_program"),
        traceback.FrameSummary(
            "interpreter.py", 2, InterpreterProcess._process_interrupts.__name__
        ),
        traceback.FrameSummary("my_program.py", 5, "interrupt_handler"),
        traceback.FrameSummary("something.py", 10, "cool_function"),
    )

    output = InterpreterProcess.format_limited_traceback(
        ZeroDivisionError, ZeroDivisionError("foo bar"), tb
    )

    lines = output.split("\n")
    assert len(lines) == 4
    assert 'File "my_program.py", line 5, in interrupt_handler' in lines[0]
    assert 'File "something.py", line 10, in cool_function' in lines[1]
    assert "ZeroDivisionError: foo bar" in lines[2]
