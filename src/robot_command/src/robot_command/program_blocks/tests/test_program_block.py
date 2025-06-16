import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import (
    RootBlock,
    ProgramBlock,
    UserCodeBlock,
    RPLBlock,
)


@pytest.fixture
def sample_program():
    return '''\
def main():
    print('hello world')
    '''


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


def test_main_program_is_detected_when_function_name_is_main(
    sample_program, program
):
    module = parso.parse(sample_program)
    root = RootBlock(module, program)
    program.reset_data(name='sample_program')

    result = [n for n in ProgramBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, ProgramBlock)
    assert result.name == 'sample_program'
    assert len(result.children) > 0


@pytest.fixture
def sub_program():
    return '''\
def pimelate():
    print('hello world')
    '''


def test_sub_program_is_detected_when_function_name_is_not_main(
    sub_program, program
):
    module = parso.parse(sub_program)
    root = RootBlock(module, program)
    program.reset_data(name='something')

    result = [n for n in ProgramBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, ProgramBlock)
    assert result.name == 'pimelate'
    assert len(result.children) > 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('def growth(fine):\n    print("foo")\n', ('growth', ['fine'], [None])),
        (
            'def coarse(ill=41.29):\n    print("foo")\n',
            ('coarse', ['ill'], ['41.29']),
        ),
        (
            'def further(variety, manage="tough"):\n    print("foo")\n',
            ('further', ['variety', 'manage'], [None, '"tough"']),
        ),
        (
            'def guard(obedient=None):\n    print("foo")\n',
            ('guard', ['obedient'], ['None']),
        ),
    ],
)
def test_sub_program_with_parameters_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)
    program.reset_data(name='something')

    result = [n for n in ProgramBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, ProgramBlock)
    assert result.name == expected[0]
    assert len(result.children) > 0
    assert result.parameters == expected[1]
    assert result.defaults == expected[2]


def test_program_is_not_detected_when_function_is_on_wrong_level(
    sample_program, program
):
    module = parso.parse(sample_program)
    root = RootBlock(module, program)
    usercode = UserCodeBlock(None, root)
    program.reset_data(name='sample_program')

    result = [n for n in ProgramBlock.read(module.children[0], usercode)]

    assert len(result) == 0


def test_main_program_is_written_with_correct_name(sample_program, program):
    module = parso.parse(sample_program)
    root = RootBlock(module, program)
    program.reset_data(name='sample_program')
    block = ProgramBlock(module.children[0], root)
    root.add_child(block)
    program.reset_data(name='my_program')

    result = ''.join(block.write())

    assert result.startswith('def main():\n')


def test_sub_program_is_written_with_correct_name(sub_program, program):
    module = parso.parse(sub_program)
    root = RootBlock(module, program)
    block = ProgramBlock(None, root, type_='subprogram')
    root.add_child(block)
    block.name = 'tholeite'

    result = ''.join(block.write())

    assert result.endswith('def tholeite():\n')


def test_sub_program_with_parameters_is_written_correctly(sub_program, program):
    module = parso.parse(sub_program)
    root = RootBlock(module, program)
    block = ProgramBlock(
        None,
        root,
        type_='subprogram',
        name='green',
        parameters=['limit', 'fry', 'simple', 'garden'],
        defaults=[None, None, "178", '"ZB12B"'],
    )
    root.add_child(block)

    result = ''.join(block.write())

    assert result == 'def green(limit, fry, simple=178, garden="ZB12B"):\n'


def test_sub_program_is_prefixed_with_newline_when_not_first_block_in_program(
    sub_program, program
):
    module = parso.parse(sub_program)
    root = RootBlock(module, program)
    some_block = RPLBlock(None, root)
    root.add_child(some_block)
    block = ProgramBlock(None, root, type_='subprogram')
    root.add_child(block)
    block.name = 'lately'

    result = ''.join(block.write())

    assert result.startswith('\ndef')
