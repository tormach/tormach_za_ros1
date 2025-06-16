import pytest

from robot_ui.pathpilot.robot.program import RobotProgram
from robot_ui.pathpilot.robot.program.blocks import AssignmentBlockData

from robot_command.testing.program_test_data import DummyBlock
from robot_command.program_blocks import (
    RootBlock,
    ProgramBlock,
    AssignmentBlock,
)


@pytest.fixture
def robot_program():
    """
    - root
     - 0 mainprogram
      - 0 assign x
      - 1 assign x
      - 2 assign y
    """
    program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), program)
    main_block = ProgramBlock(
        DummyBlock((0, 0), (20, 0)), root_block, type_='mainprogram'
    )
    root_block.add_child(main_block)
    main_block.add_child(
        AssignmentBlock(DummyBlock((1, 0), (2, 0)), main_block, name='x')
    )
    main_block.add_child(
        AssignmentBlock(DummyBlock((2, 0), (3, 0)), main_block, name='x')
    )
    main_block.add_child(
        AssignmentBlock(DummyBlock((3, 0), (4, 0)), main_block, name='y')
    )
    program.reset_data(root_block=root_block)

    return program


def test_variable_names_are_empty_when_program_is_invalid():
    block_data = AssignmentBlockData()

    block_data.program = None

    assert block_data.variableNames == []


def test_variable_names_are_correct_when_program_is_valid(robot_program):
    block_data = AssignmentBlockData()

    block_data.program = robot_program
    block_data.uuid = robot_program.root_block.children[0].children[2].uuid

    assert sorted(block_data.variableNames) == ['x', 'y']
