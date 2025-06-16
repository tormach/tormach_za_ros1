import pytest
import parso

from robot_command.robot_program import RobotProgram
from robot_command.program_blocks import RootBlock, NotifyBlock, UserCodeBlock
from robot_command.program_blocks.notify_block import NotifyType


@pytest.fixture
def program():
    return RobotProgram(inspector_blocks=(UserCodeBlock,))


@pytest.mark.parametrize(
    'test_input,expected',
    [
        ('notify("reinduce")\n', ("reinduce", NotifyType.Notification, '')),
        (
            'notify("onmun", image_path="/foo/bar")\n',
            ("onmun", NotifyType.Notification, '/foo/bar'),
        ),
        (
            'notify(message="cecum", error=True)\n',
            ("cecum", NotifyType.Error, ''),
        ),
        (
            'notify(message="blusht", warning=True, image_path=\'/tmp/foo\')\n',
            ("blusht", NotifyType.Warning, '/tmp/foo'),
        ),
        (
            'notify(message=\'ringgoer\', warning=True, error=True)\n',
            ("ringgoer", NotifyType.Error, ''),
        ),
        (
            'notify("ability is \\"sweet\\"")\n',
            ('ability is "sweet"', NotifyType.Notification, ''),
        ),
    ],
)
def test_notify_is_correctly_detected_as_notify_block(
    program, test_input, expected
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in NotifyBlock.read(module.children[0], root)]

    assert len(result) == 1
    result = result[0]
    assert isinstance(result, NotifyBlock)
    assert result.message == expected[0]
    assert result.notify_type == expected[1]
    assert result.image_path == expected[2]


@pytest.mark.parametrize(
    "test_input",
    [
        'notify()\n',
        'notify(something="foo")\n',
        'notify("dicentra", other=True)\n',
    ],
)
def test_invalid_variations_of_notify_are_not_detected_as_notify_block(
    program, test_input
):
    module = parso.parse(test_input)
    root = RootBlock(module, program)

    result = [n for n in NotifyBlock.read(module.children[0], root)]

    assert len(result) == 0


@pytest.mark.parametrize(
    'test_input, expected',
    [
        (("egling", NotifyType.Notification, ''), 'notify("egling")\n'),
        (
            ("skeppund", NotifyType.Warning, ''),
            'notify("skeppund", warning=True)\n',
        ),
        (
            ("advancer", NotifyType.Error, '/tmp/something'),
            'notify("advancer", error=True, image_path="/tmp/something")\n',
        ),
        (
            ("omagua", NotifyType.Notification, '/MPXJX'),
            'notify("omagua", image_path="/MPXJX")\n',
        ),
        (
            (r'kingdom with "eggs" and \\ham', NotifyType.Notification, ''),
            'notify("kingdom with \\"eggs\\" and \\\\ham")\n',
        ),
    ],
)
def test_notify_is_written_correctly(program, test_input, expected):
    root = RootBlock(None, program)
    block = NotifyBlock(
        None,
        root,
        message=test_input[0],
        notify_type=test_input[1],
        image_path=test_input[2],
    )

    output = ''.join(block.write())

    assert output == expected
