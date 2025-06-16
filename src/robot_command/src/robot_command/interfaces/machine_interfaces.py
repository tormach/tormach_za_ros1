import rospy
from ..program_interpreter import InterpreterProcess, InterpreterState
from . import ConfigInterfaceSingleton, ConfigInterface


class MachineMaxvelInterfaceSingleton:
    MACHINE_STATE_PREFIX = ConfigInterface.MACHINE_STATE_PREFIX
    USER_PREFIX = ConfigInterface.USER_PREFIX
    MACHINE_MAXVEL_LIMITS_PARAM = f'{MACHINE_STATE_PREFIX}/max_velocity_limits'
    MACHINE_MAXVEL_LIMIT_PARAM = f'{MACHINE_STATE_PREFIX}/max_velocity_limit'
    USER_MAXVEL_PARAM = f'{USER_PREFIX}/maximum_velocity'
    USER_FEEDRATE_PARAM = f'{USER_PREFIX}/feedrate'
    # TODO: questions about the applicability of this
    CARTESIAN_MAX_TRANS_VEL_PARAM = (
        '/robot_description_planning/cartesian_limits/max_trans_vel'
    )
    CARTESIAN_MAX_TRANS_ACC_PARAM = (
        '/robot_description_planning/cartesian_limits/max_trans_acc'
    )
    CARTESIAN_MAX_ROT_VEL_PARAM = (
        '/robot_description_planning/cartesian_limits/max_rot_vel'
    )

    _instance = None

    def __new__(cls):
        # Manage singleton
        if cls._instance is not None:
            return cls._instance
        cls._instance = self = super().__new__(cls)

        # Init config interface
        self._config_interface = ConfigInterfaceSingleton()

        # Track old values
        self._old_user_maxvel_limit = None
        self._old_feedrate = None
        self._old_machine_maxvel_limit = None
        self._old_maxvel_limit = None

        self._update_machine_maxvel_limit()
        self._update_user_maxvel_limit()
        self._update_user_feedrate()
        rospy.loginfo("Initialized new MachineMaxvelInterface")
        return self

    def _update_machine_maxvel_limit(self):
        # Check for updates to machine state maxvel param, a
        # composite of other individual machine state maxvel
        # limits (e.g. safety_input)
        machine_maxvel_limits = self._config_interface.get_base_param(
            self.MACHINE_MAXVEL_LIMITS_PARAM, {}
        )
        machine_maxvel_limit = min(list(machine_maxvel_limits.values()) + [1.0])
        if machine_maxvel_limit != self._old_machine_maxvel_limit:
            # Save updated machine state maxvel param
            rospy.loginfo(f"Machine maxvel updated: {machine_maxvel_limit}")
            self._config_interface.set_base_param(
                self.MACHINE_MAXVEL_LIMIT_PARAM, machine_maxvel_limit
            )
            self._old_machine_maxvel_limit = machine_maxvel_limit
            self._update_maxvel()

    def _update_maxvel(self):
        # Whenever machine maxvel or user maxvel changes,
        # update "global" maxvel and run interp callbacks
        maxvel = self.maximum_velocity
        if maxvel != self._old_maxvel_limit:
            rospy.loginfo(f"Global maxvel updated: {maxvel}")
            self._old_maxvel_limit = maxvel

    def _update_user_maxvel_limit(self):
        # Check for updates to user maxvel param
        user_maxvel_limit = self.user_maximum_velocity
        if user_maxvel_limit != self._old_user_maxvel_limit:
            rospy.loginfo(f"User maxvel_limit updated: {user_maxvel_limit}")
            self._old_user_maxvel_limit = user_maxvel_limit
            self._update_maxvel()
        return

    def _update_user_feedrate(self):
        feedrate = self.feedrate

        if feedrate != self._old_feedrate:
            rospy.loginfo(f"Feedrate updated: {feedrate}")
            self._old_feedrate = feedrate
        return

    @property
    def user_maximum_velocity(self):
        return self._config_interface.get_param('maximum_velocity')

    @property
    def machine_maximum_velocity(self):
        return self._config_interface.get_base_param(
            self.MACHINE_MAXVEL_LIMIT_PARAM
        )

    @property
    def maximum_velocity(self):
        return min(self.user_maximum_velocity, self.machine_maximum_velocity)

    @property
    def feedrate(self):
        return self._config_interface.get_param("feedrate")

    @property
    def cartesian_max_trans_velocity(self):
        return self._config_interface.get_base_param(
            self.CARTESIAN_MAX_TRANS_VEL_PARAM
        )

    @property
    def cartesian_max_trans_acceleration(self):
        return self._config_interface.get_base_param(
            self.CARTESIAN_MAX_TRANS_ACC_PARAM
        )

    @property
    def cartesian_max_rot_velocity(self):
        return self._config_interface.get_base_param(
            self.CARTESIAN_MAX_ROT_VEL_PARAM
        )


class SafetyInputInterfaceSingleton:
    MACHINE_STATE_PREFIX = ConfigInterface.MACHINE_STATE_PREFIX
    MACHINE_SAFETY_INPUT_PARAM = f'{MACHINE_STATE_PREFIX}/safety_input'
    MACHINE_ENABLING_INPUT_PARAM = f'{MACHINE_STATE_PREFIX}/enabling_input'

    _instance = None

    def __new__(cls):
        # Manage singleton
        if cls._instance is not None:
            return cls._instance
        cls._instance = self = super().__new__(cls)

        self._config_interface = ConfigInterfaceSingleton()
        self._old_safety_input = self._config_interface.get_base_param(
            self.MACHINE_SAFETY_INPUT_PARAM
        )
        self._old_enabling_input = self._config_interface.get_base_param(
            self.MACHINE_ENABLING_INPUT_PARAM
        )
        self._config_interface.add_update_cb(self._safety_input_updated)

        return self

    def _safety_input_updated(self, key, val):
        if key not in (
            self.MACHINE_SAFETY_INPUT_PARAM,
            self.MACHINE_ENABLING_INPUT_PARAM,
        ):
            return  # N/A

        interp_state = InterpreterProcess.interp_process().current_state

        if key == self.MACHINE_SAFETY_INPUT_PARAM:
            falling_edge = self._old_safety_input and not val
            self._old_safety_input = val

            if not falling_edge:
                return  # Nothing to do

            # Safety input went low and enabling input is already low
            rospy.loginfo("Safety input tripped")
            if (
                not self._config_interface.get_base_param(
                    self.MACHINE_ENABLING_INPUT_PARAM
                )
                and interp_state is InterpreterState.Running
            ):
                InterpreterProcess.pause_command(
                    reason="Safety input tripped while enabling input low"
                )

        if key == self.MACHINE_ENABLING_INPUT_PARAM:
            if self._old_enabling_input == val:
                return  # Value unchanged

            # Enabling input changed
            self._old_enabling_input = val
            if val:
                # Enabling input went high; nothing to do
                return

            # Enabling input went low
            rospy.loginfo("Enabling input tripped")

            # If safety input also low, pause program
            if (
                not self._config_interface.get_base_param(
                    self.MACHINE_SAFETY_INPUT_PARAM
                )
                and interp_state is InterpreterState.Running
            ):
                InterpreterProcess.pause_command(
                    reason="Enabling input tripped while safety input low"
                )
