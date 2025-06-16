import pytest

from robot_ui.pathpilot.robot.program import RobotProgram
from robot_ui.pathpilot.robot.program.blocks import SubProgramBlockData

from robot_command.testing.program_test_data import DummyBlock
from robot_command.program_blocks import RootBlock, ProgramBlock


@pytest.fixture
def robot_program():
    """
    - root
     - 0 subprogram leetle
     - 1 subprogram ioni
     - 2 mainprogram
    """
    program = RobotProgram()
    root_block = RootBlock(DummyBlock((0, 0), (20, 0)), program)
    root_block.add_child(
        ProgramBlock(
            DummyBlock((1, 0), (2, 0)),
            root_block,
            name='leetle',
            type_='subprogram',
        )
    )
    root_block.add_child(
        ProgramBlock(
            DummyBlock((3, 0), (4, 0)),
            root_block,
            name='ioni',
            type_='subprogram',
        )
    )
    root_block.add_child(
        ProgramBlock(
            DummyBlock((5, 0), (20, 0)), root_block, type_='mainprogram'
        )
    )
    program.reset_data(root_block=root_block)

    return program


def test_sub_program_names_are_empty_when_program_is_invalid():
    block_data = SubProgramBlockData()

    block_data.program = None

    assert block_data.subProgramNames == []


def test_sub_program_names_are_correct_when_program_is_valid(robot_program):
    block_data = SubProgramBlockData()

    block_data.program = robot_program

    assert block_data.subProgramNames == ['ioni', 'leetle']
