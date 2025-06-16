import os
import pathlib
from threading import Lock
import robot_command_msgs.srv as srv
import rospy
import time
from robot_command_msgs.msg import InterpreterState, ProgramPosition


class ProgramLauncher:
    LOAD_PROGRAM_SERVICE = '/robot_command/load_program'
    UNLOAD_PROGRAM_SERVICE = '/robot_command/unload_program'
    RUN_COMMAND_SERVICE = '/robot_command/run_command'
    INTERPRETER_STATE_TOPIC = '/robot_command/interpreter_state'
    PROGRAM_POSITION_TOPIC = '/robot_command/program_position'
    SERVICE_TIMEOUT_S = 10.0
    CHECK_INTERVAL_S = 0.1
    INTERPRETER_READY_WAIT_TIMEOUT_S = 10.0
    PROGRAM_EXECUTE_TIMEOUT_S = 60.0 * 5.0

    def __init__(self):
        self._interpreter_state = InterpreterState.STATE_UNDEFINED
        self._interpreter_state_history = []
        self._program_path = ''
        self._state_lock = Lock()
        self._path_lock = Lock()

        self._load_program_srv = rospy.ServiceProxy(
            self.LOAD_PROGRAM_SERVICE, srv.LoadProgram
        )
        self._unload_program_srv = rospy.ServiceProxy(
            self.UNLOAD_PROGRAM_SERVICE, srv.UnloadProgram
        )
        self._run_command_srv = rospy.ServiceProxy(
            self.RUN_COMMAND_SERVICE, srv.RunCommand
        )
        self._load_program_srv.wait_for_service(
            rospy.Duration.from_sec(self.SERVICE_TIMEOUT_S)
        )

        self._subs = []
        self._subs.append(
            rospy.Subscriber(
                self.INTERPRETER_STATE_TOPIC,
                InterpreterState,
                self._on_interpreter_update_received,
            )
        )
        self._subs.append(
            rospy.Subscriber(
                self.PROGRAM_POSITION_TOPIC,
                ProgramPosition,
                self._on_program_position_update_received,
            )
        )

    @property
    def interpreter_state(self):
        with self._state_lock:
            return self._interpreter_state

    @property
    def program_path(self):
        with self._path_lock:
            return self._program_path

    @property
    def _state_history(self):
        with self._state_lock:
            return self._interpreter_state_history

    def stop(self):
        for sub in self._subs:
            sub.unregister()

    def load(self, path):
        ready_states = (
            InterpreterState.STATE_IDLE,
            InterpreterState.STATE_STOPPED,
        )
        if self.interpreter_state not in ready_states:
            rospy.loginfo("Interpreter not ready, waiting.")
            if not self._wait_for_states(ready_states):
                rospy.logerr("Interpreter did not become ready, aborting")
                raise RuntimeError("Interpreter not ready")
        rospy.loginfo(f"Loading program {path}")
        if not self._load_program(path):
            raise RuntimeError("Load program failed")
        if not self._wait_for_states((InterpreterState.STATE_STOPPED,), path):
            rospy.logerr("Program was not loaded.")
            raise RuntimeError("Load program failed")

    def cycle_start(self):
        self._clear_interpreter_state_history()
        if self.interpreter_state == InterpreterState.STATE_PAUSED:
            rospy.loginfo("Continuing program")
            if not self._continue_program():
                raise RuntimeError("Continue program failed")
            # TODO: change feedhold, here or in `_continue_program`
        else:
            rospy.loginfo("Starting program")
            if not self._start_program():
                raise RuntimeError("Start program failed")
            # TODO: change feedhold
        if not self._wait_for_history(InterpreterState.STATE_RUNNING):
            raise RuntimeError("Executing program failed")
        completed_states = (
            InterpreterState.STATE_IDLE,
            InterpreterState.STATE_STOPPED,
            InterpreterState.STATE_RUNTIME_ERROR,
            InterpreterState.STATE_PAUSED,
        )
        if self._wait_for_states(
            completed_states, timeout_s=self.PROGRAM_EXECUTE_TIMEOUT_S
        ):
            state = self.interpreter_state
            if state == InterpreterState.STATE_RUNTIME_ERROR:
                rospy.logerr("Error during program execution.")
                return False
            elif state == InterpreterState.STATE_PAUSED:
                rospy.loginfo("Program paused.")
            else:
                rospy.loginfo("Program completed successfully.")
        else:
            rospy.loginfo("Program is still running, aborting.")
        return True

    def unload(self):
        rospy.loginfo("Unloading program")
        if not self._unload_program():
            raise RuntimeError("Unload program failed.")
        if not self._wait_for_states((InterpreterState.STATE_IDLE,)):
            raise RuntimeError("Unload program failed.")

    def abort(self):
        rospy.loginfo("Stopping program")
        if not self._abort_program():
            raise RuntimeError("Stopping program failed.")
        if not self._wait_for_states(
            (InterpreterState.STATE_IDLE, InterpreterState.STATE_STOPPED)
        ):
            raise RuntimeError("Stop program failed.")

    def run_programs_in_path(self, path):
        if self.interpreter_state not in (
            InterpreterState.STATE_STOPPED,
            InterpreterState.STATE_IDLE,
        ):
            rospy.loginfo("Aborting running programs, clearing errors.")
            if not self._abort_program():  # clear errors, stop running programs
                raise RuntimeError("Aborting program failed")

        program_files = self._find_program_files(path)
        rospy.loginfo(f"Found {len(program_files)} program files.")
        for path in program_files:
            self.run_program(path)

    def run_program(self, path):
        self.load(path)
        self.cycle_start()
        self.unload()

    def _load_program(self, path):
        try:
            result = self._load_program_srv.call(path=path)
        except rospy.ServiceException as e:
            rospy.logerr(f"Loading program failed {e}")
            return False
        else:
            return result.success

    def _unload_program(self):
        try:
            result = self._unload_program_srv.call()
        except rospy.ServiceException as e:
            rospy.logerr(f"Unloading program failed {e}")
            return False
        else:
            return result.success

    def _start_program(self):
        try:
            result = self._run_command_srv.call(
                command=srv.RunCommandRequest.COMMAND_START
            )
        except rospy.ServiceException as e:
            rospy.logerr(f"Start program failed {e}")
            return False
        else:
            return result.success

    def _continue_program(self):
        try:
            result = self._run_command_srv.call(
                command=srv.RunCommandRequest.COMMAND_CONTINUE
            )
        except rospy.ServiceException as e:
            rospy.logerr(f"Continue program failed {e}")
            return False
        else:
            return result.success

    def _abort_program(self):
        try:
            self._run_command_srv.call(
                command=srv.RunCommandRequest.COMMAND_STOP
            )
        except rospy.ServiceException as e:
            rospy.logerr(f"Aborting program failed {e}")
            return False
        else:
            # TODO: consider turning on feedhold
            return True

    def _wait_for_states(
        self, states, path=None, timeout_s=INTERPRETER_READY_WAIT_TIMEOUT_S
    ):
        start_time = time.time()
        while self.interpreter_state not in states and (
            path is None or path == self.program_path
        ):
            current_time = time.time()
            if timeout_s and current_time - start_time > timeout_s:
                return False
            rospy.sleep(rospy.Duration.from_sec(self.CHECK_INTERVAL_S))
        return True

    def _wait_for_history(
        self, state, timeout_s=INTERPRETER_READY_WAIT_TIMEOUT_S
    ):
        start_time = time.time()
        while state not in self._state_history:
            current_time = time.time()
            if timeout_s and current_time - start_time > timeout_s:
                return False
            rospy.sleep(rospy.Duration.from_sec(self.CHECK_INTERVAL_S))
        return True

    def _clear_interpreter_state_history(self):
        with self._state_lock:
            del self._interpreter_state_history[:]

    @staticmethod
    def _find_program_files(root_path):
        program_files = []
        for root, dirs, files in os.walk(root_path):
            for file_ in files:
                path = os.path.join(root, file_)
                data = pathlib.Path(path).read_text()
                if 'def main():' in data:
                    program_files.append(path)
        return program_files

    def _on_interpreter_update_received(self, msg):
        with self._state_lock:
            self._interpreter_state = msg.state
            self._interpreter_state_history.append(msg.state)

    def _on_program_position_update_received(self, msg):
        with self._path_lock:
            self._program_path = msg.filename
