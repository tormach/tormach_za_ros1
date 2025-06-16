import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, UserCodeBlock, CommentBlock
from robot_command.program_blocks.comment_block import CommentType


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected', [('"wonder"\n', 'wonder'), ("'suit'\n", 'suit')]
)
def test_line_comment_is_detected_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in CommentBlock.read(module.children[0], root)]

    assert len(result) == 1
    block = result[0]
    assert block.comment_type == CommentType.LineComment
    assert block.text == expected


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('"""everyday\nrefer"""\n', 'everyday\nrefer'),
        ("'''nurse\nfarm \nfirst'''\n", 'nurse\nfarm \nfirst'),
    ],
)
def test_block_comment_is_detected_correctly(program, test_input, expected):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in CommentBlock.read(module.children[0], root)]

    assert len(result) == 1
    block = result[0]
    assert block.comment_type == CommentType.BlockComment
    assert block.text == expected


@pytest.mark.parametrize('test_input', ['pass  # foo\n', '#bar\n'])
def test_other_command_is_not_mistaken_as_comment(program, test_input):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in CommentBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ((CommentType.LineComment, "bargain"), '"bargain"\n'),
        ((CommentType.BlockComment, "cream\ndeep"), '"""cream\ndeep"""\n'),
    ],
)
def test_comment_block_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = CommentBlock(
        None, root, comment_type=test_input[0], text=test_input[1]
    )

    output = '\n'.join(block.write())

    assert output == expected
