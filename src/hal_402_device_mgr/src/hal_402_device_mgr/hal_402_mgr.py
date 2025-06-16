import rospy
import hal
import traceback
import time
from enum import IntEnum
from fysom import FysomGlobalMixin, FysomGlobal, Canceled
from .params import EtherCATDriveRedisGUIDParams, EtherCATROSParams

from .pins import HALPins

from hal_402_device_mgr.hal_402_drive import Drive402


class Hal402Timeout(RuntimeError):
    pass


class Hal402Mgr(FysomGlobalMixin):
    default_control_mode = 'MODE_CSP'
    ros_param_base = 'hal_402_device_mgr'
    init_timeout = 30.0  # seconds
    goal_state_timeout = 5.0  # seconds

    pin_specs = {
        # IO pin for command request and feedback
        'state-cmd': dict(ptype=hal.HAL_U32, pdir=hal.HAL_IO),
        # IN pin set high when external quick stop triggered
        'quick_stop': dict(ptype=hal.HAL_BIT, pdir=hal.HAL_IN),
        # OUT pin set high for two update cycles around drive enable
        # transition
        'reset': dict(ptype=hal.HAL_BIT, pdir=hal.HAL_OUT),
    }

    ####################################################
    # Initialization

    def __init__(self, compname='hal_402_mgr', sim=True):
        self.state = 'init_command'
        self.command = 'init'
        self.sim = sim
        super().__init__()
        self.compname = compname

    # To be called by external code
    def init(self):
        # Init ROS
        self.init_ros()
        # Init HAL component and common pins
        self.hal_comp_init()
        # Init drive objects and drive pins
        self.create_drives()
        # Mark HAL comp ready
        self.hal_comp_ready()

    def init_ros(self):
        # Init ROS node, shutdown callback, rate object
        rospy.init_node(self.compname)
        rospy.on_shutdown(self.call_cleanup)
        self.update_rate = rospy.get_param(
            f'{self.ros_param_base}/update_rate', 10
        )
        self.rate = rospy.Rate(self.update_rate)
        rospy.loginfo(f"Initialized '{self.compname}' ROS node")

    def hal_comp_init(self):
        # Init HAL userland component
        self.comp = hal.component(self.compname)
        rospy.loginfo(f"Initialized '{self.compname}' HAL component")
        self.pins = HALPins(self.comp, self.pin_specs)
        self.pins.init_pins()

    def hal_comp_ready(self):
        self.comp.ready()
        rospy.loginfo("%s: HAL component ready" % self.compname)

    def create_drives(self):
        self.drives = []
        drive_config = rospy.get_param(f'{self.ros_param_base}/drives', None)
        if drive_config is None:
            rospy.logerr(f"No drive config in {self.ros_param_base}/drives")
            return

        # self.sim = rospy.get_param("/hal_hardware/sim_mode", True)

        num_drives = len(drive_config)
        mode = "sim" if self.sim else "real-hardware"
        rospy.loginfo(f"Configuring {num_drives} {mode}-mode drives")

        drives = {}
        for drive_name in drive_config.keys():
            # Create drives from ROS parameters; read drive attributes
            # one at a time to create meaningful errors without extra
            # code
            base_param = f"{self.ros_param_base}/drives/{drive_name}"
            drive_obj = Drive402(
                drive_name=drive_name,
                drive_type=rospy.get_param(f"{base_param}/type"),
                slave_number=rospy.get_param(f"{base_param}/slave_number"),
                comp=self.comp,
                sim=self.sim,
            )
            drive_obj.init()
            drives[drive_obj.slave_number] = drive_obj
            rospy.loginfo(f"Initialized drive instance {drive_obj.drive_name}")
        self.drives = [drives[i] for i in sorted(drives.keys())]

    ####################################################
    # Drive state FSM

    GSM = FysomGlobal(
        initial=dict(state='init_command', event='init_command', defer=False),
        events=[
            # Init state:  From initial state
            # - init_1:  (Nothing) Wait for drives to come online
            # - init_2:  Check and update drive params
            # - init_complete:  Done
            dict(name='init_command', src='init_command', dst='init_1'),
            dict(name='init_2', src='init_1', dst='init_2'),
            dict(name='init_complete', src='init_2', dst='init_complete'),
            # Fault state:  From any state
            # - fault:  done
            dict(name='fault_command', src='*', dst='fault_1'),
            dict(name='fault_complete', src='fault_1', dst='fault_complete'),
            # Start state:  From any state but 'start*'
            # - start_1:  Switch all drives to SWITCHED ON
            # - start_2:  Set all drive control modes to default
            # - start_3:  Switch all drives to OPERATION ENABLED
            # - start_complete:  Done
            dict(name='start_command', src='*', dst='start_1'),
            dict(name='start_2', src='start_1', dst='start_2'),
            dict(name='start_3', src='start_2', dst='start_3'),
            dict(name='start_complete', src='start_3', dst='start_complete'),
            # Stop state:  From any state but 'stop*'
            # - stop_1:  Put all drives in SWITCH ON DISABLED and CSP mode
            # - stop_complete:  Done
            dict(name='stop_command', src='*', dst='stop_1'),
            dict(name='stop_complete', src='stop_1', dst='stop_complete'),
            # Home state:  From only 'stop_complete'
            # - home_1:  Set all drive control modes to HM
            # - home_2:  Switch all drives to OPERATION ENABLED
            # - home_3:  Set home flag
            # - home_complete:  Done; issue 'stop' command
            dict(name='home_command', src='*', dst='home_1'),
            dict(name='home_2', src='home_1', dst='home_2'),
            dict(name='home_3', src='home_2', dst='home_3'),
            dict(name='home_complete', src='home_3', dst='home_complete'),
        ],
        state_field='state',
    )

    #
    # Init command
    #
    def on_before_init_command(self, e):
        return self.fsm_check_command(e, timeout=self.init_timeout)

    def on_enter_init_1(self, e):
        rospy.loginfo('Waiting for drives to come online before init')

    def on_before_init_2(self, e):
        if self.fsm_check_drives_online(e, 'INIT'):
            rospy.loginfo("All drives online; proceeding with init")
            return True
        else:
            return False

    def on_enter_init_2(self, e):
        self.initialize_drives()

    def on_before_init_complete(self, e):
        if self.all_drives_initialized():
            return True
        try:
            self.timer_check_overrun('Initializing drives')
        except Hal402Timeout as exc:
            # If drives don't come online within a timeout, just exit
            raise rospy.exceptions.ROSInterruptException(str(exc))
        return False

    def on_enter_init_complete(self, e):
        self.fsm_finalize_command(e)
        # Automatically return to SWITCH ON DISABLED after init
        self.command = 'stop'

    #
    # Fault command
    #
    def on_before_fault_command(self, e):
        if self.fsm_check_command(e):
            rospy.logerr('Entering fault state')
            return True
        else:
            return False

    def on_enter_fault_1(self, e):
        return self.fsm_set_drive_goal_state(e, 'FAULT')

    def on_before_fault_complete(self, e):
        return self.fsm_check_drive_goal_state(e, 'FAULT')

    def on_enter_fault_complete(self, e):
        self.fsm_finalize_command(e)

    #
    # Start command
    #
    def on_before_start_command(self, e):
        return self.fsm_check_command(e)

    def on_enter_start_1(self, e):
        # Set reset pin during transition to SWITCHED ON
        e.reset_pin = True
        self.fsm_set_drive_goal_state(e, 'SWITCHED ON')

    def on_before_start_2(self, e):
        if not self.all_drives_status_flags(VOLTAGE_ENABLED=True):
            self.timer_check_overrun("No voltage at drive motor power inputs")
            return False
        return self.fsm_check_drive_goal_state(e, 'SWITCHED ON')

    def on_enter_start_2(self, e):
        # Clear reset pin in OPERATION ENABLED
        e.reset_pin = False
        mode = self.default_control_mode
        self.fsm_set_drive_control_mode(e, mode)
        self.fsm_set_brake_override(e, override=False)

    def on_before_start_3(self, e):
        mode = self.default_control_mode
        return self.fsm_check_drive_control_mode(e, mode)

    def on_enter_start_3(self, e):
        self.fsm_set_drive_goal_state(e, 'OPERATION ENABLED')

    def on_before_start_complete(self, e):
        return self.fsm_check_drive_goal_state(e, 'OPERATION ENABLED')

    def on_enter_start_complete(self, e):
        self.fsm_finalize_command(e)

    #
    # Stop command
    #
    def on_before_stop_command(self, e):
        return self.fsm_check_command(e)

    def on_enter_stop_1(self, e):
        # Zero out command & feedback differences to give operator
        # confidence turning on machine
        e.reset_pin = True
        return self.fsm_set_drive_goal_state(e, 'SWITCH ON DISABLED')

    def on_before_stop_complete(self, e):
        return self.fsm_check_drive_goal_state(e, 'SWITCH ON DISABLED')

    def on_enter_stop_complete(self, e):
        e.reset_pin = False
        self.fsm_finalize_command(e)

    #
    # Home command
    #
    def on_before_home_command(self, e):
        if not e.src == 'stop_complete':
            rospy.logwarn("Unable to home when drives not stopped")
            return False
        return self.fsm_check_command(e)

    def on_enter_home_1(self, e):
        rospy.logwarn(
            "Starting drive homing, do not press Reset or power-cycle drives until complete"
        )
        self.fsm_set_drive_control_mode(e, 'MODE_HM')
        # Don't allow brakes to disengage to prevent joint position change
        self.fsm_set_brake_override(e, override=True)
        # Clear multi-turn data to prevent overflows
        self.fsm_clear_encoder_multiturn_data(e)
        # Zero home offset
        self.fsm_zero_home_offset(e)
        # Restart timer; that took a while
        self.timer_start()

    def on_before_home_2(self, e):
        return self.fsm_check_drive_control_mode(e, 'MODE_HM')

    def on_enter_home_2(self, e):
        self.fsm_set_drive_goal_state(e, 'OPERATION ENABLED')

    def on_before_home_3(self, e):
        if not self.all_drives_status_flags(VOLTAGE_ENABLED=True):
            self.timer_check_overrun("No voltage at drive motor power inputs")
            return False
        return self.fsm_check_drive_goal_state(e, 'OPERATION ENABLED')

    def on_enter_home_3(self, e):
        # MODE_HM:  OPERATION_MODE_SPECIFIC_1 = HOMING_START
        rospy.loginfo("Setting all drives control word HOMING_START flag")
        self.set_drive_control_flags(OPERATION_MODE_SPECIFIC_1=True)

    def on_before_home_complete(self, e):
        if self.all_drives_status_flags(HOMING_COMPLETED=True):
            rospy.loginfo("All drives status word HOMING_COMPLETED flag set")
            return True
        self.timer_check_overrun("waiting on drives HOMING_COMPLETED flags")
        # Cancel event
        rospy.loginfo(
            "Homing sequence waiting on drives HOMING_COMPLETED flags"
        )
        return False

    def on_enter_home_complete(self, e):
        if not self.sim and self.drive_params.model_id == (
            0x00100000,
            0x000C010D,
        ):  # SV660N
            # Re-write params:  SV660N clears 200D-12h and 60FE-02h after reset
            self.drive_params.write()
            # Restart timer; writing drive params takes time
            self.timer_start()
        self.fsm_finalize_command(e)
        # Automatically return to SWITCH ON DISABLED after homing
        self.command = 'stop'
        rospy.logwarn("Homing sequence complete, press Reset to continue.")

    #
    # All states
    #
    def on_change_state(self, e):
        # This runs after every `on_enter_*`; attrs of e set there (or
        # `on_before_*`) will be present here

        # Set/clear reset pin
        self.pins.reset.set(getattr(e, 'reset_pin', False))
        if self.pins.reset.changed:
            rospy.loginfo(f'Reset pin set to {self.pins.reset.get()}')
            self.pins.reset.write()  # Set now to effect reset early

    #
    # Helpers
    #
    class Command(IntEnum):
        INIT = 0
        STOP = 1
        START = 2
        HOME = 3
        FAULT = 4

    cmd_name_to_int_map = {cmd.name.lower(): cmd.value for cmd in Command}
    cmd_int_to_name_map = {cmd.value: cmd.name.lower() for cmd in Command}

    def timer_start(self, timeout=None):
        if timeout is None:
            timeout = self.goal_state_timeout
        self._timeout = time.time() + timeout

    def timer_check_overrun(self, msg):
        if not hasattr(self, '_timeout') or time.time() <= self._timeout:
            return

        msg = f'{self.command} timeout:  {msg}'
        self.command = 'fault'
        del self._timeout
        raise Hal402Timeout(msg)

    @classmethod
    def fsm_command_from_event(cls, e):
        return e.dst.split('_')[0]

    def fsm_check_drives_online(self, e, state):
        return self.all_drives_operational()

    def fsm_check_command(self, e, timeout=None):
        cmd_name = self.fsm_command_from_event(e)
        if (
            e.src.startswith('init') and e.src != 'init_complete'
        ) and cmd_name != 'init':
            # Don't preempt init (fault)
            rospy.loginfo(f"Ignoring {cmd_name} command in init state {e.src}")
            return False
        elif e.src != f'{cmd_name}_command' and e.src.startswith(cmd_name):
            # Already running
            rospy.logwarn(f"Ignoring {cmd_name} command from state {e.src}")
            return False
        else:
            rospy.loginfo(f"Received {cmd_name} command:  {e.msg}")
            self.command = cmd_name
            self.timer_start(timeout=timeout or self.goal_state_timeout)
            return True

    def fsm_check_drive_goal_state(self, e, state):
        if self.all_drives_goal_state_reached(state):
            return True
        self.timer_check_overrun(f"waiting on drives to reach {state}")
        # Cancel event
        return False

    def fsm_set_drive_goal_state(self, e, state):
        cmd_name = self.fsm_command_from_event(e)
        rospy.loginfo(f"{cmd_name} command:  setting drive goal state {state}")
        self.set_drive_goal_state(state)

    def fsm_check_drive_control_mode(self, e, mode):
        if self.all_drives_mode(mode):
            return True
        self.timer_check_overrun(f"waiting on drives to enter mode {mode}")
        # Cancel event
        return False

    def fsm_set_drive_control_mode(self, e, mode):
        cmd_name = self.fsm_command_from_event(e)
        rospy.loginfo(f"{cmd_name} command:  Setting drive mode {mode}")
        self.set_drive_control_mode(mode)

    def fsm_set_brake_override(self, e, override):
        cmd_name = self.fsm_command_from_event(e)
        rospy.loginfo(f"{cmd_name} command:  Setting brake override {override}")
        self.set_brake_override(override)

    def fsm_clear_encoder_multiturn_data(self, e):
        cmd_name = self.fsm_command_from_event(e)
        rospy.loginfo(f"{cmd_name} command:  Clearing encoder multi-turn data")
        self.clear_encoder_multiturn_data()

    def fsm_zero_home_offset(self, e):
        cmd_name = self.fsm_command_from_event(e)
        rospy.loginfo(f"{cmd_name} command:  Zeroing home offset")
        self.zero_home_offset()

    def fsm_finalize_command(self, e):
        cmd_name = self.fsm_command_from_event(e)
        self.pins.state_cmd.set(self.cmd_name_to_int_map[cmd_name])
        rospy.loginfo(f"Command {cmd_name} completed")

    ####################################################
    # Execution

    def run(self):
        while not rospy.is_shutdown():
            try:
                self.update()
                self.rate.sleep()
            except rospy.exceptions.ROSInterruptException as e:
                rospy.loginfo(f"ROSInterruptException: {e}")
                break
            except Hal402Timeout as e:
                rospy.logerr(e)
            except Exception:
                # Ignore other exceptions & enter fault mode in
                # hopes we can recover
                rospy.logerr('Ignoring unexpected exception; details:')
                for line in traceback.format_exc().splitlines():
                    rospy.logerr(line)
                self.command = 'fault'

    def call_cleanup(self):
        # need to unload the userland component here?
        rospy.loginfo("Stopping ...")
        rospy.loginfo("Stopped")

    fsm_next_state_map = dict(
        # Map current command to dict of {current_state:next_event}
        # names; `None` means arrived
        init=dict(
            init_1='init_2',
            init_2='init_complete',
            init_complete=None,
        ),
        start=dict(
            start_1='start_2',
            start_2='start_3',
            start_3='start_complete',
            start_complete=None,
        ),
        stop=dict(
            stop_1='stop_complete',
            stop_complete=None,
        ),
        home=dict(
            home_1='home_2',
            home_2='home_3',
            home_3='home_complete',
            home_complete=None,
        ),
        fault=dict(
            fault_1='fault_complete',
            fault_complete=None,
        ),
    )

    def update(self):
        # Read all input pins and update state machine
        self.pins.read_all()
        self.read_drives_state()

        # Check for incoming command on state-cmd pin
        if self.pins.state_cmd.changed:
            # Other commands from state-cmd pin; can't override fault
            cmd = self.cmd_int_to_name_map[self.pins.state_cmd.get()]
            msg = 'state-cmd pin changed'
        else:
            cmd = None

        # Special cases where 'fault' overrides current command:
        if self.state.startswith('init'):
            # Fault isn't allowed to override init; don't spam logs about
            # ignoring 'fault' cmd
            pass
        elif not self.all_drives_operational():
            # Some drives not online operational
            cmd = 'fault'
            fds = self.drives_operational(negate=True)
            fd_names = ', '.join(d.drive_name for d in fds)
            msg = f'Drives ({fd_names}) not online and operational'
        elif self.any_drives_in_state('FAULT') and cmd not in ('stop', 'start'):
            # Some drives in FAULT but no recovery command
            cmd = 'fault'
            fds = self.drives_in_state('FAULT')
            fd_names = ', '.join(d.drive_name for d in fds)
            msg = f'Drives ({fd_names}) in FAULT state'
        elif self.pins.quick_stop.get() and self.command != 'fault':
            # Quick stop pin high; treat this as a fault command
            cmd = 'fault'
            msg = 'quick_stop pin high'
        elif not self.all_drives_voltage_enabled() and self.command not in (
            'stop',
            'fault',
        ):
            # Some drives have no motor power
            cmd = 'fault'
            msg = 'voltage_enabled bit low:  no motor power at drive'

        if cmd is not None and cmd != self.command:
            # Received new command to stop/start/home/fault.  Try it
            # by triggering the FSM event; a Canceled exception means
            # it can't be done, so ignore it.
            event = f'{cmd}_command'
            try:
                self.trigger(event, msg=msg)
            except Canceled:
                rospy.loginfo(f'Unable to honor {event} command')

        # Attempt automatic transition to next state; if not possible,
        # `on_before_{event}()` method will cause Canceled exception
        event = self.automatic_next_event()
        if event is not None:
            try:
                self.trigger(
                    event, msg=f'Automatic transition from {self.state} state'
                )
            except Canceled:
                rospy.logdebug(f'Cannot transition to next state {event}')

        # Write all output pins and let drives do their thing
        self.pins.write_all()
        self.write_drives_state()

    def automatic_next_event(self):
        state_map = self.fsm_next_state_map[self.command]
        event = state_map.get(self.state, f'{self.command}_command')
        return event

    ####################################################
    # Drive helpers

    def initialize_drives(self):
        if self.sim:
            rospy.loginfo("Not initializing drives in sim mode")
            return

        # Ensure drive parameters are up to date
        rospy.loginfo("Initializing drives")
        # - Read params from ROS param server
        params_group = rospy.get_param(
            f"{self.ros_param_base}/ethercat_drive_params_group"
        )
        params_in = EtherCATROSParams(params_group)
        params_in.read()

        # - Write params out to drives
        params_out = EtherCATDriveRedisGUIDParams.copy(
            params_in,
            params_in.xml_fname,
            params_in.master,
            params_in.positions,
        )

        # - Be sure drive params are in NV mode
        #   FIXME  This is not the intended behavior forever
        for d in self.drives:
            dnum = d.slave_number
            if not params_out.get_params_nv(dnum):
                rospy.loginfo(f"    Drive {dnum} params set non-volatile on")
                params_out.set_params_nv(dnum)

        rospy.loginfo("- Updating drive params")
        params_out.write()

        # - Set drive UUID and put drive params in volatile mode
        rospy.loginfo("- Checking drive UUIDs and non-volatile settings")
        for d in self.drives:
            dnum = d.slave_number
            if not params_out.get_guid(dnum):
                params_out.set_guid(dnum)
                uuid = params_out.get_guid(dnum)
                rospy.loginfo(f"    Drive {dnum} GUID set to {uuid}")
            if not params_out.get_params_nv(dnum):
                params_out.set_params_nv(dnum)
                rospy.loginfo(f"    Drive {dnum} params set non-volatile on")

        # - Save drive params object for later use
        self.drive_params = params_out

    def all_drives_initialized(self):
        # FIXME:  Perform init checks here
        return True

    def read_drives_state(self):
        for drive in self.drives:
            drive.read_state()

    def write_drives_state(self):
        for drive in self.drives:
            drive.write_state()

    def set_drive_goal_state(self, goal_state):
        for drive in self.drives:
            drive.set_goal_state(goal_state)
            drive.set_control_flags()

    def set_drive_control_mode(self, mode):
        mode = Drive402.normalize_control_mode(mode)
        for drive in self.drives:
            drive.set_control_mode(mode)

    def set_brake_override(self, override):
        if self.sim:
            rospy.loginfo("Sim mode:  Not setting brake override")
            return
        for drive in self.drives:
            dnum = drive.slave_number
            self.drive_params.set_brake_func(dnum, on=not override)

    def clear_encoder_multiturn_data(self):
        if self.sim:
            rospy.loginfo("Sim mode:  Not resetting encoder multiturn data")
            return
        for drive in self.drives:
            dnum = drive.slave_number
            rospy.loginfo(f"- Resetting encoder & drive {dnum}")
            self.drive_params.clear_encoder_multiturn_data(dnum)

    def zero_home_offset(self):
        if self.sim:
            rospy.loginfo("Sim mode:  Not zeroing home offset")
            return
        for drive in self.drives:
            dnum = drive.slave_number
            rospy.loginfo(f"- Zeroing home offset, drive {dnum}")
            self.drive_params.zero_home_offset(dnum)

    def set_drive_control_flags(self, **flags):
        for drive in self.drives:
            drive.set_control_flags(**flags)

    def all_drives_mode(self, mode):
        mode = Drive402.normalize_control_mode(mode)
        for drive in self.drives:
            if drive.get_control_mode() != mode:
                return False
        return True

    def all_drives_status_flags(self, **flags):
        for drive in self.drives:
            for flag, val in flags.items():
                if drive.get_status_flag(flag) != val:
                    return False
        return True

    def drives_operational(self, negate=False):
        # Return list of operational drives (online & slave-oper)
        status = not negate
        return [d for d in self.drives if d.operational is status]

    def all_drives_operational(self):
        # Check if all drives are operational (no drives not operational!)
        return len(self.drives_operational(negate=True)) == 0

    def all_drives_voltage_enabled(self, negate=False):
        status = not negate
        return [d for d in self.drives if d.voltage_enabled is status]

    def drives_in_state(self, state, negate=False):
        # Return list of drives with matching state
        if negate:
            return [d for d in self.drives if d.state != state]
        else:
            return [d for d in self.drives if d.state == state]

    def any_drives_in_state(self, state):
        # check if any drives have the matching state
        return len(self.drives_in_state(state)) > 0

    def all_drives_in_state(self, state):
        # check if all drives have the matching state
        return len(self.drives_in_state(state, negate=True)) == 0

    def all_drives_goal_state_reached(self, state):
        for drive in self.drives:
            if not drive.operational:
                return False
            if not drive.get_goal_state() == state:
                return False
            if not drive.is_goal_state_reached():
                return False
        return True
