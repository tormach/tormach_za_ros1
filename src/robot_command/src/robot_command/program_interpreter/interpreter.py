import contextlib
import multiprocessing
import os
import signal
from typing import Any

import sys
import time
import traceback
from multiprocessing import Event, Process
from multiprocessing.managers import SyncManager
from threading import Lock, Thread

import fysom
import rospy

import robot_command.rpl
from robot_command.rpl import init_rpl_interpreter
from .loader import ProgramLoader
from .shared import INTERPRETER_PROCESS_NAME
from .types import (
    InterpreterState,
    InterpreterContext,
    InterpreterCommand,
    ProgramTree,
    ProgramState,
    ProgramCommand,
    ProgramPosition,
    ProgramError,
    ProgramInterrupt,
    MdiSyntaxError,
    ProgramSyntaxError,
    ProgramFileIOError,
    ProgramWrongStateError,
    FSMState,
    InterpreterReloadRequired,
)
from .fsm import FSM
from .reload_checker import ReloadChecker
from .internal_exceptions import ProgramExit, ProgramPause, ProgramUpdate

_QUEUE_CHECK_TIMEOUT = 0.01


class ProgramInterpreter:
    """Runs and manages a single Python RPL interpreter process."""

    def __init__(self, interpreter='simulation'):
        self._worker_process = None
        self._status_thread = None
        self._manager = None
        self._command_queue = None
        self._status_queue = None
        self._interrupt_queue = None
        self._worker_stop_event = Event()
        self._status_stop_event = Event()
        self._loader = ProgramLoader(interpreter)
        self._interpreter = interpreter
        self._state = InterpreterState.Idle
        self._reload_required = False
        self._reload_check_event = Event()

        self._status_update_cb = None
        self._status_update_cb_lock = Lock()

        self._command_lock = None

    @property
    def status_update_cb(self):
        with self._status_update_cb_lock:
            return self._status_update_cb

    @status_update_cb.setter
    def status_update_cb(self, value):
        with self._status_update_cb_lock:
            self._status_update_cb = value

    @property
    def command_lock(self):
        """
        Use this lock to prevent commands from being executed.
        Useful for testing.
        """
        return self._command_lock

    def load_program(self, path):
        rospy.loginfo(f'Interpreter loading program {path}')
        path = os.path.expanduser(path)
        try:
            self._loader.load_program(path)
        except (SyntaxError, OSError) as e:
            if isinstance(e, SyntaxError):
                rospy.loginfo(f'Interpreter syntax error:  {e}')
                error_type = ProgramSyntaxError
            else:
                rospy.loginfo(f'Interpreter file IO error:  {e}')
                error_type = ProgramFileIOError
            with self._status_update_cb_lock:
                self._status_update_cb(ProgramError(error_type, e))
            self._run_command(InterpreterCommand.LoadError, self._loader.path)
            return False
        else:
            self._run_command(
                InterpreterCommand.Load,
                ProgramTree(self._loader.tree, self._loader.path),
            )
            return True

    def unload_program(self):
        rospy.loginfo('Interpreter unloading program')
        self._loader.unload_program()
        self._run_command(InterpreterCommand.Unload)

    def start_program(self):
        self._run_command(InterpreterCommand.Start, ('main', True))

    def start_subprogram(self, name, loop):
        self._run_command(InterpreterCommand.Start, (name, loop))

    def stop_program(self):
        self._run_command(InterpreterCommand.Stop)

    def pause_program(self, active=False, reason=None):
        self._run_command(
            (
                InterpreterCommand.PauseActive
                if active
                else InterpreterCommand.Pause
            ),
            reason,
        )

    def continue_program(self):
        self._run_command(InterpreterCommand.Continue)

    def update_program(self):
        self._run_command(InterpreterCommand.Update)

    def step_program(self):
        if not self._is_program_running():
            self.start_program()
        self._run_command(InterpreterCommand.Step)

    def execute_mdi_command(self, command):
        try:
            tree = self._loader.load_mdi_command(command)
        except SyntaxError as e:
            with self._status_update_cb_lock:
                self._status_update_cb(ProgramError(MdiSyntaxError, e))
        else:
            self._run_command(InterpreterCommand.MDI, tree)

    def check_reload_required(self):
        if self._state not in (InterpreterState.Idle, InterpreterState.Stopped):
            raise ProgramWrongStateError()
        self._reload_check_event.clear()
        self._run_command(InterpreterCommand.ReloadCheck)
        self._reload_check_event.wait()
        return self._reload_required

    def wait_for_program_to_complete(self):
        while self._is_program_running():
            time.sleep(_QUEUE_CHECK_TIMEOUT)

    def start(self):
        if self._worker_process:
            return
        self._status_stop_event.clear()
        self._start_queue_manager()
        self._start_status_thread()
        self._start_worker_process()

    def stop(self):
        if not self._worker_process:
            return
        self.stop_program()  # make sure process is stopped
        self._stop_worker_process()
        self._stop_status_thread()
        self._manager.shutdown()

    def _start_worker_process(self):
        self._worker_stop_event.clear()
        self._worker_process = Process(
            name='InterpreterProcess',
            target=InterpreterProcess.worker,
            args=(
                self._worker_stop_event,
                self._command_queue,
                self._status_queue,
                self._interrupt_queue,
                self._interpreter,
                self._command_lock,
            ),
        )
        # self._worker_process.daemon = True
        self._worker_process.start()

    def _stop_worker_process(self):
        self._worker_stop_event.set()
        self._worker_process.join()
        self._worker_process = None

    def _start_status_thread(self):
        self._status_thread = Thread(
            name='StatusThread',
            target=self._status_thread_worker,
            args=(self._status_stop_event,),
        )
        self._status_thread.daemon = True
        self._status_thread.start()

    def _stop_status_thread(self):
        self._status_stop_event.set()
        self._status_queue.put(None)  # flush blocking thread
        self._status_thread.join()
        self._status_thread = None

    def _start_queue_manager(self):
        self._manager = SyncManager()
        self._manager.start(
            lambda: signal.signal(signal.SIGINT, signal.SIG_IGN)
        )
        self._command_queue = (
            self._manager.list()
        )  # we use list as priority queue
        self._status_queue = self._manager.Queue()
        self._interrupt_queue = self._manager.Queue()
        self._command_lock = self._manager.Lock()

    def _status_thread_worker(self, stop_event):
        # wait for status update callback to be set
        while not stop_event.is_set():
            with self._status_update_cb_lock:
                if self._status_update_cb:
                    break
                time.sleep(_QUEUE_CHECK_TIMEOUT)
                continue
        while not stop_event.is_set():
            data = self._status_queue.get()
            if isinstance(data, ProgramState):
                self._state = data.state
            if isinstance(data, InterpreterReloadRequired):
                self._reload_required = data.required
                self._reload_check_event.set()
                continue
            with self._status_update_cb_lock:
                self._status_update_cb(data)

    def _is_program_running(self):
        return self._state in (
            InterpreterState.Running,
            InterpreterState.Paused,
            InterpreterState.PausedActive,
        )

    def _run_command(self, command, data=None):
        if command is InterpreterCommand.Stop:
            del self._command_queue[:]
        self._command_queue.append(ProgramCommand(command, data))


class InterpreterProcess:
    """Manages the execution of an RPL interpreter inside another process"""

    IMPORT_CODE = (
        'from {rpl} import {init_function}\n'
        '{init_function}(\'{interpreter}\')\n'
        'from {rpl} import *\n'
        'from {interp_module} import {program_exit}\n'
    )

    _FSM_TO_REPORT_STATE = {
        FSM.stopped_state: (
            InterpreterState.Stopped,
            None,
        ),
        FSM.running_state: (
            InterpreterState.Running,
            InterpreterContext.Program,
        ),
        FSM.running_step_state: (
            InterpreterState.Running,
            InterpreterContext.Program,
        ),
        FSM.running_on_paused_state: (
            InterpreterState.Running,
            InterpreterContext.Program,
        ),
        FSM.running_on_paused_active_state: (
            InterpreterState.Running,
            InterpreterContext.Program,
        ),
        FSM.running_on_stopped_state: (
            InterpreterState.Running,
            InterpreterContext.Program,
        ),
        FSM.running_on_errored_state: (
            InterpreterState.Running,
            InterpreterContext.Program,
        ),
        FSM.mdi_running_in_stopped_state: (
            InterpreterState.Running,
            InterpreterContext.MDI,
        ),
        FSM.mdi_running_in_idle_state: (
            InterpreterState.Running,
            InterpreterContext.MDI,
        ),
        FSM.paused_state: (
            InterpreterState.Paused,
            InterpreterContext.Program,
        ),
        FSM.paused_active_state: (
            InterpreterState.PausedActive,
            InterpreterContext.Program,
        ),
        FSM.mdi_paused_in_stopped_state: (
            InterpreterState.Paused,
            InterpreterContext.MDI,
        ),
        FSM.mdi_paused_in_idle_state: (
            InterpreterState.Paused,
            InterpreterContext.MDI,
        ),
        FSM.errored_state: (
            InterpreterState.RuntimeError,
            None,
        ),
        FSM.errored_in_idle_state: (
            InterpreterState.RuntimeError,
            None,
        ),
        FSM.error_while_loading_state: (
            InterpreterState.LoadError,
            None,
        ),
        FSM.idle_state: (
            InterpreterState.Idle,
            None,
        ),
    }

    def __init__(
        self,
        stop_event,
        command_queue,
        status_queue,
        interrupt_queue,
        interpreter,
        command_lock,
    ):
        self._reporter = None
        self._stop_event = stop_event
        self._command_queue = command_queue
        self._status_queue = status_queue
        self._interrupt_queue = interrupt_queue
        self.command_lock = command_lock

        self._namespace = {}
        self._interpreter = interpreter
        self._compiled = None
        self._current_state = InterpreterState.Initialized
        self._fresh_path = sys.path[:]
        self._last_position = None
        self._pre_pause_position = None
        self._reload_checker = ReloadChecker()

        self.handle_interrupt = self._default_interrupt_handler
        self.reset_interrupts = self._default_interrupt_reset
        self.on_pause_handler = lambda: None
        self.on_abort_handler = lambda: None

        # fsm state and events defined in external module
        # for easier testing and processing with other tools
        self._fsm = fysom.Fysom(FSM.fsm)
        setattr(self._fsm, f'on_{FSM.init_event}', self._init_event)
        setattr(self._fsm, f'on_{FSM.load_event}', self._load_program)
        setattr(self._fsm, f'on_{FSM.unload_event}', self._unload_program)
        setattr(self._fsm, f'on_{FSM.start_event}', self._start_program)
        setattr(self._fsm, f'on_{FSM.stop_event}', self._stop_program)
        setattr(self._fsm, f'on_{FSM.update_event}', self._update_program)
        setattr(self._fsm, f'on_{FSM.mdi_event}', self._execute_mdi)
        setattr(self._fsm, f'on_{FSM.load_error_event}', self._load_error)
        setattr(
            self._fsm,
            f'on_{FSM.reload_check_event}',
            lambda _: self.update_reload_required(),
        )
        setattr(
            self._fsm,
            f'on_{FSM.stopped_state}',
            lambda _: self.update_reload_required(),
        )

        def report_state(e):
            if e.dst in self._FSM_TO_REPORT_STATE:
                self._report_program_state(*self._FSM_TO_REPORT_STATE[e.dst])
            self._report_fsm_state(e.event, e.src, e.dst)

        self._fsm.onchangestate = report_state

        self._command_switch = {
            InterpreterCommand.Stop: lambda _: self._fsm.stop(),
            InterpreterCommand.Pause: lambda data: self._fsm.pause(reason=data),
            InterpreterCommand.PauseActive: lambda data: self._fsm.pause_active(
                reason=data
            ),
            InterpreterCommand.Continue: lambda _: self._fsm.cont(),
            InterpreterCommand.Update: lambda _: self._fsm.update(),
            InterpreterCommand.Load: lambda data: self._fsm.load(data=data),
            InterpreterCommand.Unload: lambda _: self._fsm.unload(),
            InterpreterCommand.Start: lambda data: self._fsm.start(data=data),
            InterpreterCommand.MDI: lambda data: self._fsm.mdi(command=data),
            InterpreterCommand.LoadError: lambda data: self._fsm.load_error(
                data=data
            ),
            InterpreterCommand.Step: lambda _: self._fsm.step(),
            InterpreterCommand.ReloadCheck: lambda _: self._fsm.reload_check(),
        }
        self._fsm.init()

    @property
    def current_state(self):
        return self._current_state

    @property
    def paused_states(self):
        return FSM.paused_states

    @property
    def pre_paused_states(self):
        return FSM.pre_paused_states

    @property
    def fsm_state(self):
        return self._fsm.current

    @classmethod
    def interp_process(cls):
        return getattr(multiprocessing.current_process(), '_interpreter')

    @staticmethod
    def worker(
        stop_event,
        command_queue,
        status_queue,
        interrupt_queue,
        interpreter,
        command_lock,
    ):
        process = InterpreterProcess(
            stop_event,
            command_queue,
            status_queue,
            interrupt_queue,
            interpreter,
            command_lock,
        )
        process._namespace = {INTERPRETER_PROCESS_NAME: process}
        current_process = multiprocessing.current_process()
        setattr(
            current_process, '_interpreter', process
        )  # to check status from func
        process._load_imports()

        process._report_program_state(InterpreterState.Idle)
        on_abort_triggered = False
        while not stop_event.is_set():
            try:
                # run abort handler here to handle errors and exits
                if on_abort_triggered:
                    process._run_on_abort_handler()
                    on_abort_triggered = False
                # execute next command from queue
                process._churn_and_check_pause()
            except SystemExit:  # exit by user program
                with contextlib.suppress(ProgramExit):
                    try:
                        process._fsm.stop()
                    except fysom.FysomError as e:
                        rospy.logwarn(e)
                # if on_abort_trigger is set, handler was already called
                on_abort_triggered = not on_abort_triggered
            except ProgramExit:  # controlled exit via stop program
                on_abort_triggered = not on_abort_triggered
            except Exception as e:
                # Get the traceback object
                type_, value, tb_raw = sys.exc_info()
                tb = traceback.extract_tb(tb_raw)
                trace = InterpreterProcess.format_limited_traceback(
                    type_, value, tb
                )
                process._fsm.runtime_error()
                if hasattr(e, 'msg'):  # SyntaxError
                    message = e.msg
                elif isinstance(e, ZeroDivisionError):
                    message = e.args[0]
                else:
                    message = str(e)
                message += f'\n-- EXTENDED INFO --\nTraceback: (most recent call last):\n{trace}'
                process._report_error(type(e), message)
                on_abort_triggered = not on_abort_triggered
                rospy.loginfo(
                    "Program errored, full traceback:\n"
                    f"{''.join(traceback.format_tb(tb_raw))}"
                )
            time.sleep(_QUEUE_CHECK_TIMEOUT)

    @staticmethod
    def format_limited_traceback(
        type_, value, tb: traceback.StackSummary
    ) -> str:
        """
        Formats the traceback of the current exception and hide frames of internal modules.
        """
        # look for robot program frame and skip everything before it
        start_index = 0
        for i, frame in enumerate(tb):
            if frame.name == '<module>':
                frame.name = os.path.basename(frame.filename)
                start_index = i
            elif frame.name in ProgramLoader.HANDLER_METHOD_NAMES:
                start_index = i
                break
            elif frame.name == InterpreterProcess._process_interrupts.__name__:
                start_index = i + 1
                break

        # look for internal modules and skip everything after it
        robot_command_path = os.path.dirname(robot_command.rpl.__file__)
        end_index = next(
            (
                i + start_index
                for i, frame in enumerate(tb[start_index:])
                if frame.filename.startswith(robot_command_path)
            ),
            len(tb),
        )

        # print traceback starting from the last found frame
        output = traceback.format_list(tb[start_index:end_index])
        output += traceback.format_exception_only(type_, value)
        return ''.join(output)

    def spin_from_injected(self):
        """
        Queue pause if feedhold active, then churns the command queue and
        blocks as long as the interpreter is in paused state.

        The command is meant to be called by code injected into the robot program between each line.
        """
        self._pause_if_step_running()  # queue pause if feedhold active
        self._spin_while_paused()

    @classmethod
    def spin_command(cls):
        """
        Churns the command queue, but only executes stop, pause and update commands.
        The command is meant to be called by program commands.
        """
        interp_process = cls.interp_process()
        command = interp_process._churn_stop_command()
        if interp_process.fsm_state not in interp_process.pre_paused_states:
            return interp_process.current_state is InterpreterState.Running
        elif command is None:
            raise ProgramPause('Unknown source')
        else:
            raise ProgramPause(command.data)

    @classmethod
    def spin_pause(cls):
        """
        Churns the command queue, executes any command, blocks if in paused state
        returns True when not.
        The command is meant to be used by program commands in combination with a loop.
        :return: always True, blocks if in paused state
        """
        cls.interp_process()._spin_while_paused()
        return True

    @classmethod
    def pause_command(cls, active=False, reason=None):
        """
        Pauses the command interpreter.
        This command is meant to be called by program commands.
        """
        cls.interp_process()._command_queue.insert(
            0,
            ProgramCommand(
                (
                    InterpreterCommand.PauseActive
                    if active
                    else InterpreterCommand.Pause
                ),
                reason,
            ),
        )

    @classmethod
    def update_command(cls):
        """
        Signals the running command to update itself by raising an
        ProgramUpdate exception.
        """
        cls.interp_process()._command_queue.insert(
            0, ProgramCommand(InterpreterCommand.Update, None)
        )

    @classmethod
    def trigger_interrupt(cls, source_id: int, number: int, value: Any):
        """
        Adds a new interrupt signal to the queue.
        This command is meant to be called by program commands.

        :param source_id: the interrupt source id
        :param number: number of the interrupt, e.g. 1 for digital input 1
        :param value: value associated with the interrupt, e.g. True for rising edge
        """
        cls.interp_process()._interrupt_queue.put(
            ProgramInterrupt(source_id, number, value)
        )

    def report_position(self, position):
        self._last_position = position
        self._status_queue.put(ProgramPosition(*position))

    def update_reload_required(self):
        self._reload_checker.update()
        self._status_queue.put(
            InterpreterReloadRequired(required=self._reload_checker.modified)
        )

    def _save_pre_pause_position(self):
        self._pre_pause_position = self._last_position

    def _restore_pre_pause_position(self):
        if self._pre_pause_position is not self._last_position:
            self.report_position(self._pre_pause_position)

    def _spin_while_paused(self):
        """
        Churns the command queue and blocks as long as the interpreter is in paused state.
        """
        was_paused = False
        while True:  # loop ensures queue is churned after on paused
            while self._churn_and_check_pause():  # block while on paused state
                time.sleep(_QUEUE_CHECK_TIMEOUT)
            if self._fsm.current not in self.pre_paused_states:
                if was_paused:  # we transitioned from paused to running
                    self._restore_pre_pause_position()
                break  # done if not transitioning to paused state
            self._save_pre_pause_position()
            self._fsm.next()  # -> running on paused state
            self.on_pause_handler()  # executes pre paused code
            self._fsm.next()  # -> paused state
            was_paused = True  # now we return to the loop start and block

    def _load_imports(self):
        source = self.IMPORT_CODE.format(
            rpl=robot_command.rpl.__name__,
            init_function=init_rpl_interpreter.__name__,
            interpreter=self._interpreter,
            interp_module=__name__,
            program_exit=ProgramExit.__name__,
        )
        compiled = compile(source, 'imports', 'exec')
        exec(compiled, self._namespace)

    def _init_event(self, _):
        self.report_position((0, ''))

    def _load_program(self, e):
        data = e.data
        program_path = os.path.dirname(data.path)
        os.chdir(program_path)  # change working directory
        sys.path = self._fresh_path + [program_path]
        self._compiled = compile(data.tree, data.path, 'exec')
        self.report_position((0, data.path))

    def _load_error(self, e):
        path = e.data
        self.report_position((0, path))

    def _unload_program(self, _):
        self.report_position((0, ''))

    def _start_program(self, e):
        name, loop = e.data
        self.reset_interrupts()
        namespace = self._namespace.copy()
        exec(self._compiled, namespace)
        if loop:
            exec(f'''while True: {name}()\n''', namespace)
        else:
            exec(f'''{name}()\nexit()\n''', namespace)

    def _stop_program(self, _):
        raise ProgramExit()

    def _update_program(self, _):
        raise ProgramUpdate()

    def _execute_mdi(self, e):
        compiled = compile(e.command, 'mdi', 'exec')
        namespace = self._namespace.copy()
        exec(compiled, namespace)
        exec('main()\nexit()\n', namespace)

    def _churn_and_check_pause(self) -> bool:
        """
        Churns and executes the next command in the queue
        and returns True if the interpreter is in paused state.
        """
        command = self._churn_next_command()
        if command is None:
            return self._fsm.current in self.paused_states
        with contextlib.suppress(fysom.FysomError):
            self._command_switch.get(command.command, lambda data: None)(
                command.data
            )
        return self._fsm.current in self.paused_states

    def _churn_stop_command(self):
        command = self._churn_next_command(
            peek=(
                InterpreterCommand.Stop,
                InterpreterCommand.Pause,
                InterpreterCommand.Update,
            )
        )
        if command is None:
            return None

        with contextlib.suppress(fysom.FysomError):
            self._command_switch.get(command.command, lambda data: None)(
                command.data
            )
        return command

    def _churn_next_command(self, peek=None):
        self._process_interrupts()
        with self.command_lock:
            try:
                command = self._command_queue.pop(0)
            except IndexError:
                return None

            if peek is not None and command.command not in peek:
                self._command_queue.insert(0, command)
                return None

        return command

    def _process_interrupts(self):
        while not self._interrupt_queue.empty():
            interrupt = self._interrupt_queue.get()
            self.handle_interrupt(
                interrupt.source_id, interrupt.number, interrupt.value
            )

    def _pause_if_step_running(self):
        if self._fsm.current is FSM.running_step_state:
            self._command_queue.insert(
                0, ProgramCommand(InterpreterCommand.Pause, "step next command")
            )

    def _report_program_state(self, state, context=None):
        if self._current_state == state:
            return
        self._current_state = state
        self._status_queue.put(ProgramState(state, context))

    def _report_fsm_state(self, event, source, destination):
        self._status_queue.put(FSMState(event, source, destination))

    def _report_error(self, type_, message):
        self._status_queue.put(ProgramError(type_, message))

    def _default_interrupt_handler(self, _source_id, _number, _value):
        pass

    def _default_interrupt_reset(self):
        pass

    def _run_on_abort_handler(self):
        if self._fsm.current not in (
            FSM.preparing_on_stopped_state,
            FSM.preparing_on_errored_state,
        ):
            return
        # preparing on stopped/errored -> on stopped/errored state
        self._fsm.next()
        # error or stop event could happen in handler
        # fsm transitions to errored or stopped state in this case
        self.on_abort_handler()
        # if not exception was raised -> stopped/errored state
        self._fsm.next()
