import parso
import pytest

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks.rpl_block import INDENTATION_SPACES
from robot_command.program_blocks import RootBlock, CallBlock, UserCodeBlock


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


def test_call_block_without_comment_is_detected_correctly(program):
    module = parso.parse('whare()\n')
    root = RootBlock(module, program)

    result = [n for n in CallBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, CallBlock)
    assert result.name == 'whare'
    assert len(result.arguments) == 0
    assert len(result.keyword_arguments) == 0


@pytest.mark.dependency()
def test_call_block_with_comment_is_detected_correctly(program):
    module = parso.parse('mintage()  # vesanic futter\n')
    root = RootBlock(module, program)

    result = [n for n in CallBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, CallBlock)
    assert result.name == 'mintage'


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('female("century")\n', ('female', ['"century"'], {})),
        ('day(785.43, roll=420)\n', ('day', ['785.43'], {'roll': '420'})),
        (
            'treat(lessen=\'possible\')\n',
            ('treat', [], {'lessen': '\'possible\''}),
        ),
    ],
)
def test_call_block_with_arguments_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in CallBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, CallBlock)
    assert result.name == expected[0]
    assert result.arguments == expected[1]
    assert result.keyword_arguments == expected[2]


def test_call_block_with_unpack_operator_does_not_raise_error(program):
    module = parso.parse("collect(*args, **kwargs)\n")
    root = RootBlock(module, program)

    result = [n for n in CallBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input', ['flower(habit=806.22, "baggage")\n', 'package(\n']
)
def test_other_invalid_commands_are_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in CallBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.dependency(
    depends=["test_call_block_with_comment_is_detected_correctly"]
)
def test_read_call_block_with_comment_is_written_correctly(program):
    module = parso.parse('proxenet() # aal\n')
    root = RootBlock(module, program)
    block = [n for n in CallBlock.read(module.children[0], root)][0]

    output = ''.join(block.write())

    assert output == 'proxenet() # aal\n'


def test_call_block_is_written_correctly(program):
    root = RootBlock(None, program)
    nested_block = UserCodeBlock(None, root)  # for testing indentation
    block = CallBlock(None, nested_block, name='hairband')

    output = ''.join(block.write())

    assert output == INDENTATION_SPACES * ' ' + 'hairband()\n'


def test_call_block_with_arguments_is_written_correctly(program):
    root = RootBlock(None, program)
    block = CallBlock(
        None,
        root,
        name='worse',
        arguments=['650', '"fear"'],
        keyword_arguments={"each": '"noble"'},
    )

    output = ''.join(block.write())

    assert output == 'worse(650, "fear", each="noble")\n'
