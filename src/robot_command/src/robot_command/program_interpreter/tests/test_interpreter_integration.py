import os
import time

import pytest

from robot_command.program_interpreter import (
    ProgramInterpreter,
    InterpreterState,
    InterpreterContext,
    ProgramState,
    ProgramPosition,
    ProgramError,
    MdiSyntaxError,
    ProgramSyntaxError,
)

WAIT_TIMEOUT_S = 20.0
SETTLE_TIME_S = 0.7
POLL_INTERVAL_S = 0.01


def write_program(tmpdir, source, name):
    path = os.path.join(str(tmpdir), name)
    with open(path, 'w') as f:
        f.write(source)
    return path


def wait_for_commands(commands, received_commands, timeout=WAIT_TIMEOUT_S):
    start = time.time()
    while commands != received_commands:
        if time.time() - start > timeout:
            raise TimeoutError(
                f"Timeout waiting for commands {commands} in {received_commands}"
            )
        if len(received_commands) > len(commands):
            raise ValueError(
                f"Received more commands than expected: {received_commands} expected: {commands}"
            )
        time.sleep(POLL_INTERVAL_S)
    received_commands.clear()


def wait_for_num_positions(num_positions, positions, timeout=WAIT_TIMEOUT_S):
    start = time.time()
    while len(positions) < num_positions:
        if time.time() - start > timeout:
            raise TimeoutError(
                f"Timeout waiting for {num_positions} positions in {positions}"
            )
        time.sleep(POLL_INTERVAL_S)


def wait_for_num_errors(num_errors, errors, timeout=WAIT_TIMEOUT_S):
    start = time.time()
    while num_errors < len(errors):
        if time.time() - start > timeout:
            raise TimeoutError(
                f"Timeout waiting for {num_errors} errors in {errors}"
            )
        time.sleep(POLL_INTERVAL_S)


def append_state(msg, program_states, positions=None, errors=None):
    if isinstance(msg, ProgramState):
        program_states.append((msg.state, msg.context))
    elif positions is not None and isinstance(msg, ProgramPosition):
        positions.append(msg)
    elif errors is not None and isinstance(msg, ProgramError):
        errors.append(msg)


def assert_file_content(
    tmpdir,
    filename,
    expected_text,
    assert_message=None,
    timeout_s=WAIT_TIMEOUT_S,
):
    file_path = str(tmpdir / filename)
    if not assert_message:
        assert_message = f"File '{filename}' does not exist"

    start_time = time.time()
    content_found = False

    while True:
        if os.path.exists(file_path):
            with open(file_path) as f:
                content = f.read()
                if content == expected_text:
                    content_found = True
                    break

        if time.time() - start_time > timeout_s or timeout_s == 0:
            break

        time.sleep(POLL_INTERVAL_S)
    if not content_found:
        if not os.path.exists(file_path):
            raise AssertionError(assert_message)
        else:
            raise AssertionError(
                f"Timeout reached. Expected '{expected_text}' in {filename}, but got '{content}'"
            )


@pytest.fixture
def sample_program(tmpdir):
    source = '''\
import time

def main():
    # just use print for testing
    print(1)
    print(2)
    print(3)
    time.sleep(0.01)
'''
    return write_program(tmpdir, source, 'sample_program.py')


@pytest.fixture
def interpreter():
    return ProgramInterpreter()


def test_stepping_stopped_program_works(interpreter, sample_program):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(sample_program)
    wait_for_commands(
        [(InterpreterState.Idle, None), (InterpreterState.Stopped, None)],
        states,
    )
    interpreter.step_program()
    wait_for_commands(
        [
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.Paused, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands(
        [
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.Stopped, None),
        ],  # running from on_abort
        states,
    )
    wait_for_num_positions(4, positions)
    interpreter.stop()

    assert positions[0].line_number == 0
    assert positions[0].filename == ''
    assert positions[1].line_number == 0
    assert positions[1].filename == sample_program
    assert positions[2].line_number == 5
    assert positions[3].line_number == 6


def test_starting_and_stopping_program_works(interpreter, sample_program):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(sample_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()

    assert len(positions) >= 3


def test_stop_command_is_prioritized_over_pause_command(
    interpreter, sample_program
):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(sample_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    with interpreter.command_lock:
        interpreter.pause_program()
        interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


@pytest.mark.parametrize('active', [True, False], ids=['active pause', 'pause'])
def test_pause_or_pause_active_and_running_program_works(
    interpreter, sample_program, active
):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(sample_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.pause_program(active=active)
    interpreter.continue_program()
    wait_for_commands(
        [
            (
                (
                    InterpreterState.PausedActive
                    if active
                    else InterpreterState.Paused
                ),
                InterpreterContext.Program,
            ),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


def test_reloading_program_works(interpreter, sample_program):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(sample_program)
    interpreter.load_program(sample_program)
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
        ],
        states,
    )
    wait_for_num_positions(3, positions)
    interpreter.stop()

    assert positions[0].line_number == 0
    assert positions[0].filename == ''
    assert positions[1].line_number == 0
    assert positions[1].filename == sample_program
    assert positions[2].line_number == 0
    assert positions[2].filename == sample_program


def test_unloading_program_in_stopped_state_works(interpreter, sample_program):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(sample_program)
    interpreter.unload_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Idle, None),
        ],
        states,
    )
    wait_for_num_positions(3, positions)
    interpreter.stop()

    assert positions[0].line_number == 0
    assert positions[0].filename == ''
    assert positions[1].line_number == 0
    assert positions[1].filename == sample_program
    assert positions[2].line_number == 0
    assert positions[2].filename == ''


def test_executing_mdi_command_in_idle_state_works(interpreter):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.execute_mdi_command('print(\'hello\')')
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Running, InterpreterContext.MDI),
            (InterpreterState.Idle, None),
        ],
        states,
    )
    interpreter.stop()


def test_executing_mdi_command_in_stopped_state_works(
    interpreter, sample_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(sample_program)
    interpreter.execute_mdi_command('print(\'world\')')
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.MDI),
            (InterpreterState.Stopped, None),
        ],
        states,
    )
    interpreter.stop()


def test_failing_mdi_command_reports_syntax_error(interpreter):
    states = []
    errors = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, errors=errors
    )

    interpreter.start()
    interpreter.execute_mdi_command('foobar ?/!')
    wait_for_commands([(InterpreterState.Idle, None)], states)
    wait_for_num_errors(1, errors)
    interpreter.stop()

    assert len(errors) == 1
    assert errors[0].type == MdiSyntaxError


@pytest.fixture
def exiting_program(tmpdir):
    source = '''\
import sys
def main():
    print('exiting now')
    sys.exit(1)
    '''
    return write_program(tmpdir, source, 'exiting_program.py')


def test_system_exit_triggered_by_user_results_in_stopped_state(
    interpreter, exiting_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(exiting_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.Stopped, None),
        ],
        states,
    )

    assert (
        interpreter._worker_process.is_alive()
    )  # verify process was not terminated
    interpreter.stop()


@pytest.fixture
def error_program(tmpdir):
    source = '''\
def main():
    5 / 0
    '''
    return write_program(tmpdir, source, 'error_program.py')


def test_error_in_program_results_in_error_state_and_can_be_reset(
    interpreter, error_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(error_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.RuntimeError, None),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


@pytest.fixture
def syntax_error_program(tmpdir):
    source = '''\
def main():
    !#@)(@
    '''
    return write_program(tmpdir, source, 'syntax_error_program.py')


@pytest.mark.dependency()
def test_syntax_error_in_program_results_load_error_state_and_syntax_error(
    interpreter, syntax_error_program
):
    states = []
    errors = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, errors=errors
    )

    interpreter.start()
    interpreter.load_program(syntax_error_program)
    wait_for_commands(
        [(InterpreterState.Idle, None), (InterpreterState.LoadError, None)],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Idle, None)], states)
    interpreter.stop()

    assert len(errors) == 1
    assert errors[0].type == ProgramSyntaxError


@pytest.mark.dependency(
    depends=[
        'test_syntax_error_in_program_results_load_error_state_and_syntax_error'
    ]
)
def test_recovering_from_syntax_error_by_loading_valid_program_works(
    interpreter, syntax_error_program, sample_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(syntax_error_program)
    wait_for_commands(
        [(InterpreterState.Idle, None), (InterpreterState.LoadError, None)],
        states,
    )
    interpreter.load_program(sample_program)
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


@pytest.mark.dependency(
    depends=[
        'test_syntax_error_in_program_results_load_error_state_and_syntax_error'
    ]
)
def test_recovering_from_syntax_error_by_resetting_program_works(
    interpreter, syntax_error_program, sample_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(syntax_error_program)
    wait_for_commands(
        [(InterpreterState.Idle, None), (InterpreterState.LoadError, None)],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Idle, None)], states)
    interpreter.stop()


@pytest.mark.dependency(
    depends=[
        'test_syntax_error_in_program_results_load_error_state_and_syntax_error'
    ]
)
def test_recovering_from_syntax_error_by_unloading_program_works(
    interpreter, syntax_error_program, sample_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(syntax_error_program)
    wait_for_commands(
        [(InterpreterState.Idle, None), (InterpreterState.LoadError, None)],
        states,
    )
    interpreter.unload_program()
    wait_for_commands([(InterpreterState.Idle, None)], states)
    interpreter.stop()


@pytest.fixture
def infinite_loop_program(tmpdir):
    source = '''\
def main():
    while True:
        pass
    '''
    return write_program(tmpdir, source, 'infinite_loop_program.py')


def test_infinite_loop_program_can_be_stopped(
    interpreter, infinite_loop_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(infinite_loop_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


def test_calling_commands_not_allowed_in_state_doesnt_crash_program(
    interpreter, sample_program
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.pause_program()
    interpreter.load_program(sample_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.start_program()
    time.sleep(SETTLE_TIME_S)
    assert not states
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.pause_program()
    time.sleep(SETTLE_TIME_S)
    assert not states
    interpreter.stop()


@pytest.fixture
def interrupt_program(tmpdir):
    source = f'''\
from robot_command.program_interpreter.interpreter import InterpreterProcess

def handle_interrupt(source, nr, value):
    with open('{str(tmpdir)}/interrupt.txt', 'w') as f:
        f.write(f'{{source}} {{nr}} {{value}}')

def main():
    process = InterpreterProcess.interp_process()
    process.handle_interrupt = handle_interrupt
    print(1)
    process.trigger_interrupt(129, 385, 322)
    print(2)
    exit()
'''
    return write_program(tmpdir, source, 'sample_program.py')


def test_interrupt_is_queued_and_executed_during_program_run(
    interpreter, interrupt_program, tmpdir
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(interrupt_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.Stopped, None),
        ],
        states,
    )
    time.sleep(SETTLE_TIME_S)
    interpreter.stop()

    assert_file_content(tmpdir, 'interrupt.txt', '129 385 322')


# test error in interrupt handler doesn't crash program
@pytest.fixture
def interrupt_error_program(tmpdir):
    source = f'''\
from robot_command.program_interpreter.interpreter import InterpreterProcess

def handle_interrupt(source, nr, value):
    with open('{str(tmpdir)}/interrupt.txt', 'w') as f:
        f.write('interrupt')
    raise Exception('interrupt error')

def main():
    process = InterpreterProcess.interp_process()
    process.handle_interrupt = handle_interrupt
    print(1)
    process.trigger_interrupt(129, 385, 322)
    print(2)
    exit()
'''
    return write_program(tmpdir, source, 'sample_program.py')


def test_error_in_interrupt_handler_doesnt_crash_program(
    interpreter, interrupt_error_program, tmpdir
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(interrupt_error_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.RuntimeError, None),
        ],
        states,
    )
    interpreter.stop()

    assert_file_content(tmpdir, 'interrupt.txt', 'interrupt')


# test that the abort handler is called when the program is stopped
@pytest.fixture
def abort_handler_program(tmpdir):
    source = f'''\
def on_abort():
    with open('{str(tmpdir)}/abort.txt', 'w') as f:
        f.write('abort')
    print('abort')

def main():
    pass
'''
    return write_program(tmpdir, source, 'abort_handler_program.py')


def test_abort_handler_is_called_when_program_is_stopped(
    interpreter, abort_handler_program, tmpdir
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(abort_handler_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()

    assert_file_content(
        tmpdir, 'abort.txt', 'abort', "abort handler was not called"
    )


# test that the program transitions to the error state if the abort handler contains an error
@pytest.fixture
def abort_handler_program_with_error(tmpdir):
    source = '''\
def on_abort():
    raise Exception('abort')

def main():
    pass
'''
    return write_program(tmpdir, source, 'abort_handler_program_with_error.py')


def test_abort_handler_with_error_transitions_to_error_state(
    interpreter, abort_handler_program_with_error
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(abort_handler_program_with_error)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.RuntimeError, None)], states)
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


# test that the abort handler can be stopped by the user
@pytest.fixture
def abort_handler_program_looping(tmpdir):
    source = '''\
def on_abort():
    while True:
        pass

def main():
    pass
'''
    return write_program(tmpdir, source, 'abort_handler_program_looping.py')


def test_abort_handler_can_be_stopped(
    interpreter, abort_handler_program_looping
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(abort_handler_program_looping)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.stop_program()
    time.sleep(SETTLE_TIME_S)
    assert not states, "abort handler should be still running"
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


# test that the abort handler is called when the program is stopped with an error
@pytest.fixture
def abort_handler_program_with_error_in_program(tmpdir):
    source = f'''\
def on_abort():
    with open('{str(tmpdir)}/abort.txt', 'w') as f:
        f.write('abort')
    print('abort')

def main():
    raise Exception('abort')
'''
    return write_program(
        tmpdir, source, 'abort_handler_program_with_error_in_program.py'
    )


def test_abort_handler_is_called_when_program_is_stopped_with_error(
    interpreter, abort_handler_program_with_error_in_program, tmpdir
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(abort_handler_program_with_error_in_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.RuntimeError, None),
        ],
        states,
    )
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()

    assert_file_content(tmpdir, 'abort.txt', 'abort')


# test that the pause handler is called when the program is paused
@pytest.fixture
def pause_handler_program(tmpdir):
    source = f'''\
def on_pause():
    with open('{str(tmpdir)}/pause.txt', 'w') as f:
        f.write('pause')
    print('pause')

def main():
    pass
'''
    return write_program(tmpdir, source, 'pause_handler_program.py')


def test_pause_handler_is_called_when_program_is_paused(
    interpreter, pause_handler_program, tmpdir
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(pause_handler_program)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.pause_program()
    wait_for_commands(
        [(InterpreterState.Paused, InterpreterContext.Program)], states
    )
    interpreter.stop_program()
    wait_for_commands(
        [
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.Stopped, None),
        ],
        states,
    )
    interpreter.stop()

    assert_file_content(
        tmpdir, 'pause.txt', 'pause', "pause handler was not called"
    )


# test that the program transitions to the error state if the pause handler raises an error
@pytest.fixture
def pause_handler_program_with_error(tmpdir):
    source = f'''\
def on_pause():
    raise Exception('pause')

def on_abort():
    with open('{str(tmpdir)}/abort.txt', 'w') as f:
        f.write('abort')

def main():
    pass
'''
    return write_program(tmpdir, source, 'pause_handler_program_with_error.py')


def test_pause_handler_with_error_transitions_to_error_state_and_calls_on_abort(
    interpreter, pause_handler_program_with_error, tmpdir
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(pause_handler_program_with_error)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.pause_program()
    wait_for_commands([(InterpreterState.RuntimeError, None)], states)
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()

    assert_file_content(tmpdir, 'abort.txt', 'abort', "on_abort was not called")


# test that the pause handler can be stopped by the user
@pytest.fixture
def pause_handler_program_looping(tmpdir):
    source = '''\
def on_pause():
    while True:
        pass

def main():
    pass
'''
    return write_program(tmpdir, source, 'pause_handler_program_looping.py')


def test_pause_handler_can_be_stopped(
    interpreter, pause_handler_program_looping
):
    states = []
    interpreter.status_update_cb = lambda msg: append_state(msg, states)

    interpreter.start()
    interpreter.load_program(pause_handler_program_looping)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    interpreter.pause_program()
    time.sleep(SETTLE_TIME_S)
    assert not states, "pause handler should be still running"
    interpreter.stop_program()
    wait_for_commands([(InterpreterState.Stopped, None)], states)
    interpreter.stop()


@pytest.fixture
def pause_handler_program_sleep(tmpdir):
    source = f'''\
import time
from robot_command.execution_commands.constants import SYNC_TIME
from robot_command.program_interpreter import InterpreterProcess
from robot_command.program_interpreter.interpreter import ProgramPause

def write_to_file(text):
    with open('{str(tmpdir)}/sleep.txt', 'w') as f:
        f.write(text)

def pausable_sleep(secs):
    write_to_file('started sleep')
    wait_time_s = secs
    while InterpreterProcess.spin_pause():
        start_time = time.time()
        try:
            while InterpreterProcess.spin_command():
                current_time = time.time()
                delta = current_time - start_time
                if delta >= wait_time_s:
                    write_to_file('finished sleep')
                    return
                time.sleep(SYNC_TIME)
        except ProgramPause as e:
            wait_time_s = 0.01 # reduce sleep time to speed up test
            write_to_file('paused sleep')
'''
    write_program(tmpdir, source, 'special_lib.py')

    source = f'''\
from special_lib import pausable_sleep

def write_to_file(text):
    with open('{str(tmpdir)}/pause.txt', 'w') as f:
        f.write(text)

def on_pause():
    write_to_file('on_pause')
    print('pause')

def main():
    pausable_sleep(5.0)
    write_to_file('after_sleep')
    exit()
'''
    return write_program(tmpdir, source, 'pause_handler_program_sleep.py')


@pytest.mark.xfail(reason="pause handler breaks intermittently; ROB-900")
def test_pause_or_pause_active_takes_effect_immediately(
    interpreter, pause_handler_program_sleep, tmpdir
):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(pause_handler_program_sleep)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    wait_for_num_positions(3, positions)
    assert positions[-1].line_number == 12  # pausable_sleep
    del positions[:]
    assert_file_content(
        tmpdir, 'sleep.txt', 'started sleep', "my_sleep was not started"
    )  # blocks until text is written

    interpreter.pause_program()
    wait_for_commands(
        [(InterpreterState.Paused, InterpreterContext.Program)], states
    )

    assert_file_content(
        tmpdir, 'pause.txt', 'on_pause', "pause handler was not called"
    )
    assert_file_content(
        tmpdir, 'sleep.txt', 'paused sleep', "my_sleep was not called"
    )

    interpreter.continue_program()
    wait_for_commands(
        [
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.Stopped, None),
        ],
        states,
    )

    assert_file_content(tmpdir, 'pause.txt', 'after_sleep')
    assert_file_content(
        tmpdir,
        'sleep.txt',
        'finished sleep',
    )

    interpreter.stop()


@pytest.mark.xfail(reason="pause handler breaks intermittently; ROB-900")
def test_program_position_is_reported_again_after_pause(
    interpreter, pause_handler_program_sleep, tmpdir
):
    states = []
    positions = []
    interpreter.status_update_cb = lambda msg: append_state(
        msg, states, positions
    )

    interpreter.start()
    interpreter.load_program(pause_handler_program_sleep)
    interpreter.start_program()
    wait_for_commands(
        [
            (InterpreterState.Idle, None),
            (InterpreterState.Stopped, None),
            (InterpreterState.Running, InterpreterContext.Program),
        ],
        states,
    )
    wait_for_num_positions(3, positions)
    assert positions[-1].line_number == 12  # pausable_sleep
    del positions[:]
    assert_file_content(
        tmpdir, 'sleep.txt', 'started sleep', "my_sleep was not started"
    )  # blocks until text is written

    interpreter.pause_program()
    wait_for_commands(
        [(InterpreterState.Paused, InterpreterContext.Program)], states
    )
    wait_for_num_positions(4, positions)

    assert positions[0].line_number == 8  # on_pause handler
    assert positions[0].filename == pause_handler_program_sleep
    del positions[:]

    # this assertion is known to fail occasionally
    assert_file_content(
        tmpdir, 'sleep.txt', 'paused sleep', "my_sleep was not called"
    )  # make sure sleep was called

    interpreter.continue_program()
    wait_for_commands(
        [
            (InterpreterState.Running, InterpreterContext.Program),
            (InterpreterState.Stopped, None),
        ],
        states,
    )
    wait_for_num_positions(4, positions)

    assert positions[0].line_number == 12  # pausable_sleep
    assert positions[0].filename == pause_handler_program_sleep

    interpreter.stop()
