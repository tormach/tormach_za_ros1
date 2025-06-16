import pytest
import parso

from robot_command.program_blocks.frame_block import FrameType
from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import (
    RootBlock,
    UserCodeBlock,
    FrameBlock,
    PassBlock,
)


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('with user_frame(foo):\n  pass\n', ('foo', '', '')),
        ('with user_frame(position="right"):\n  pass\n', ('', '"right"', '')),
    ],
)
def test_with_frame_is_detected_correctly_as_frame_block(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in FrameBlock.read(module.children[0], root)]

    assert len(result) == 1
    block = result[0]
    assert isinstance(block, FrameBlock)
    assert block.frame_type == FrameType.ScopedUserFrame
    assert block.pose == expected[0]
    assert block.position == expected[1]
    assert block.orientation == expected[2]
    assert len(block.children) == 1


@pytest.mark.parametrize(
    'test_input,expected',
    [
        (
            'change_user_frame("beast")\n',
            ("beast", FrameType.ChangeUserFrame),
        ),
        ('change_user_frame("")\n', ("", FrameType.ChangeUserFrame)),
        (
            'change_tool_frame("descent")\n',
            ("descent", FrameType.ChangeToolFrame),
        ),
    ],
)
def test_change_frame_is_detected_correctly_as_frame_block(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in FrameBlock.read(module.children[0], root)]

    assert len(result) == 1
    block = result[0]
    assert isinstance(block, FrameBlock)
    assert block.frame_type == expected[1]
    assert block.name == expected[0]


@pytest.mark.parametrize(
    'test_input',
    [
        'with user_frame():\n    pass\n',
        'while True:\n    pass\n',
        'while something():\n    pass\n',
        'with open("bla") as f:\n    pass\n',
        'with frame(foo) as o:\n    pass\n',
        'with tool_frame():\n    pass\n',
        'change_tool_frame(234)\n',
    ],
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in FrameBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (
            ("float", '', '', FrameType.ScopedUserFrame, ""),
            'with user_frame(float):\n    pass\n',
        ),
        (
            ('', '', '', FrameType.ChangeUserFrame, "stripe"),
            'change_user_frame("stripe")\n',
        ),
        (
            ('', '', '', FrameType.ChangeUserFrame, ""),
            'change_user_frame("")\n',
        ),
        (
            ('', '', '', FrameType.ChangeToolFrame, "lock"),
            'change_tool_frame("lock")\n',
        ),
    ],
)
def test_frame_block_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = FrameBlock(
        None,
        root,
        pose=test_input[0],
        position=test_input[1],
        orientation=test_input[2],
        frame_type=test_input[3],
        name=test_input[4],
    )
    block.add_child(PassBlock(None, block))

    output = ''.join(block.write())

    assert output == expected
