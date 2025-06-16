import pytest

from robot_command.rpl import (
    CommandInterpreter,
    Command,
    AsyncCommand,
    ScopedCommand,
)


@pytest.fixture
def interp():
    return CommandInterpreter()


@pytest.fixture
def sync_command():
    class SomeCommand(Command):
        name = 'sync_command'
        data = []

        def __init__(
            self,
        ):
            super().__init__()
            SomeCommand.data.append('sync_init')

        def execute(self):
            SomeCommand.data.append('sync_executed')

    return SomeCommand


@pytest.fixture
def async_command():
    class SomeAsyncCommand(AsyncCommand):
        name = 'async_command'
        data = []
        is_similar_ = True

        def __init__(self):
            super().__init__()
            SomeAsyncCommand.data.append('async_init')

        def execute(self, sequence=None, last=False):
            SomeAsyncCommand.data.append('async_executed')

        def is_similar(self, other):
            return SomeAsyncCommand.is_similar_

    return SomeAsyncCommand


@pytest.fixture
def scoped_command():
    class SomeScopedCommand(ScopedCommand):
        name = 'scoped_command'
        data = []

        def __init__(self):
            super().__init__()
            SomeScopedCommand.data.append('scoped_init')

        def __enter__(self):
            SomeScopedCommand.data.append('scoped_entered')

        def __exit__(self, type_, value, traceback):
            SomeScopedCommand.data.append('scoped_exited')

    return SomeScopedCommand


@pytest.mark.dependency()
def test_sync_command_is_registered_to_namespace(interp, sync_command):
    namespace = {}

    interp.register_commands('custom', commands=[sync_command])
    interp.register_commands_to_namespace(namespace)

    assert 'sync_command' in namespace


@pytest.mark.dependency()
def test_async_command_is_registered_to_namespace(interp, async_command):
    namespace = {}

    interp.register_commands('custom', commands=[async_command])
    interp.register_commands_to_namespace(namespace)

    assert 'async_command' in namespace


@pytest.mark.dependency()
def test_scoped_command_is_registered_to_namespace(interp, scoped_command):
    namespace = {}

    interp.register_commands('custom', commands=[scoped_command])
    interp.register_commands_to_namespace(namespace)

    assert 'scoped_command' in namespace


@pytest.mark.dependency(
    depends=[
        'test_async_command_is_registered_to_namespace',
        'test_sync_command_is_registered_to_namespace',
    ]
)
def test_async_commands_are_executed_when_sync_command_is_run(
    interp, sync_command, async_command
):
    exec_data = []
    sync_command.data = exec_data
    async_command.data = exec_data
    namespace = {}
    interp.register_commands('custom', commands=[sync_command, async_command])
    interp.register_commands_to_namespace(namespace)

    namespace['async_command']()
    namespace['async_command']()
    namespace['async_command']()
    assert len(exec_data) == 3
    assert exec_data[0] == 'async_init'
    namespace['sync_command']()
    assert len(exec_data) == 8
    assert exec_data[3] == 'async_executed'
    assert exec_data[6] == 'sync_init'
    assert exec_data[-1] == 'sync_executed'


@pytest.mark.dependency(
    depends=[
        'test_async_command_is_registered_to_namespace',
        'test_scoped_command_is_registered_to_namespace',
    ]
)
def test_async_commands_are_executed_when_scoped_command_is_run(
    interp, async_command, scoped_command
):
    exec_data = []
    scoped_command.data = exec_data
    async_command.data = exec_data
    namespace = {}
    interp.register_commands('custom', commands=[scoped_command, async_command])
    interp.register_commands_to_namespace(namespace)

    namespace['async_command']()
    namespace['async_command']()
    assert len(exec_data) == 2
    assert exec_data[0] == 'async_init'
    with namespace['scoped_command']():
        assert len(exec_data) == 6
        assert exec_data[2] == 'async_executed'
        assert exec_data[4] == 'scoped_init'
        assert exec_data[5] == 'scoped_entered'
        namespace['async_command']()
        assert len(exec_data) == 7
    assert exec_data[7] == 'async_executed'
    assert exec_data[-1] == 'scoped_exited'
    assert len(exec_data) == 9


@pytest.mark.dependency(
    depends=['test_async_command_is_registered_to_namespace']
)
def test_async_commands_are_executed_when_async_is_same_condition_is_not_met(
    interp, async_command
):
    exec_data = []
    async_command.data = exec_data
    namespace = {}
    interp.register_commands('custom', commands=[async_command])
    interp.register_commands_to_namespace(namespace)

    namespace['async_command']()
    namespace['async_command']()
    assert len(exec_data) == 2
    assert exec_data[0] == 'async_init'
    async_command.is_similar_ = False
    namespace['async_command']()
    assert len(exec_data) == 5
    assert exec_data[2] == 'async_init'
    assert exec_data[-1] == 'async_executed'


@pytest.mark.dependency(
    depends=['test_async_command_is_registered_to_namespace']
)
def test_async_commands_are_executed_instantly_when_async_disabled(
    interp, async_command
):
    exec_data = []
    async_command.data = exec_data
    namespace = {}
    interp.register_commands('custom', commands=[async_command])
    interp.register_commands_to_namespace(namespace)
    interp.async_enabled = False

    namespace['async_command']()
    assert len(exec_data) == 2
    assert exec_data[0] == 'async_init'
    assert exec_data[1] == 'async_executed'
    namespace['async_command']()
    assert len(exec_data) == 4
    assert exec_data[0] == 'async_init'
    assert exec_data[1] == 'async_executed'
