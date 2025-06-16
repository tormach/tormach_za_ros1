import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, WaitBlock, UserCodeBlock
from robot_command.program_blocks.wait_block import WaitType


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('sleep(0.01)\n', 0.01),
        ('sleep(227.42)\n', 227.42),
        ('sleep(563)\n', 563),
        ('sleep(secs=359)\n', 359),
    ],
)
def test_sleep_is_detected_correctly_as_wait_block(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaitBlock)
    assert result.wait_type == WaitType.Sleep
    assert result.sleep_time == expected


@pytest.mark.parametrize("test_input", ['sleep()\n', 'wait(0.23)\n'])
def test_invalid_variations_of_sleep_are_not_detected_as_wait_block(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('while get_digital_in(1) is False:\n  sync()\n', (1, '', True)),
        ('while get_digital_in(4) is True:\n  sync()\n', (4, '', False)),
        (
            'while get_digital_in("lucknow") is False:\n  sync()\n',
            (0, 'lucknow', True),
        ),
        (
            'while get_digital_in("dioti") is True:\n  sync()\n',
            (0, 'dioti', False),
        ),
    ],
)
def test_while_with_get_digital_in_is_detected_correctly(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaitBlock)
    assert result.wait_type == WaitType.WaitForDigitalIn
    assert result.digital_in_nr == expected[0]
    assert result.digital_in_name == expected[1]
    assert result.digital_in_state is expected[2]


@pytest.mark.parametrize(
    'test_input',
    [
        'while get_digital_in(1) is False:\n  pass\n',
        'while True:\n  sync()\n',
        'while get_digital_in(10) == True:\n  sync()\n',
        'while some_other_function(-1) is True:\n  sync()\n',
    ],
)
def test_while_without_get_digital_in_is_not_detected_incorrectly(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('pause()\n', (False, False)),
        ('pause(True)\n', (True, False)),
        ('pause(optional=False)\n', (False, False)),
        ('pause(True, True)\n', (True, True)),
        ('pause(active=True)\n', (False, True)),
    ],
)
def test_pause_is_detected_correctly_as_wait_block(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaitBlock)
    assert result.wait_type == WaitType.Pause
    assert result.optional == expected[0]
    assert result.active == expected[1]


@pytest.mark.parametrize("test_input", ['pause("threat")\n', 'pause(0.23)\n'])
def test_invalid_variations_of_pause_are_not_detected_as_wait_block(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize('test_input', ['exit()\n'])
def test_exit_is_detected_correctly_as_wait_block(program, test_input):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, WaitBlock)
    assert result.wait_type == WaitType.Exit


@pytest.mark.parametrize('test_input', ['exit("official")', 'exit(216)'])
def test_invalid_variations_of_exit_are_not_detected_as_wait_block(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in WaitBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected', [(514.05, 'sleep(514.05)\n'), (84, 'sleep(84)\n')]
)
def test_sleep_wait_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = WaitBlock(None, root, sleep_time=test_input)

    block.wait_type = WaitType.Sleep
    output = ''.join(block.write())

    assert output == expected


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ((47, '', True), 'while get_digital_in(47) is False:\n    sync()\n'),
        ((0, '', False), 'while get_digital_in(0) is True:\n    sync()\n'),
        (
            (0, 'pardoner', True),
            'while get_digital_in("pardoner") is False:\n    sync()\n',
        ),
        (
            (0, 'occision', False),
            'while get_digital_in("occision") is True:\n    sync()\n',
        ),
    ],
)
def test_get_digital_in_wait_is_written_correctly(
    program, test_input, expected
):
    root = RootBlock(None, program)
    block = WaitBlock(
        None,
        root,
        digital_in_nr=test_input[0],
        digital_in_name=test_input[1],
        digital_in_state=test_input[2],
    )

    block.wait_type = WaitType.WaitForDigitalIn
    output = ''.join(block.write())

    assert output == expected


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ((True, False), 'pause(optional=True)\n'),
        ((False, False), 'pause()\n'),
        ((False, True), 'pause(active=True)\n'),
    ],
)
def test_pause_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = WaitBlock(None, root, optional=test_input[0], active=test_input[1])

    block.wait_type = WaitType.Pause
    output = ''.join(block.write())

    assert output == expected


def test_exit_is_written_correctly(program):
    root = RootBlock(None, program)
    block = WaitBlock(None, root)

    block.wait_type = WaitType.Exit
    output = ''.join(block.write())

    assert output == 'exit()\n'
