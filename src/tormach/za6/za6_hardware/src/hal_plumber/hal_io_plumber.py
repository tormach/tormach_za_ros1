from time import sleep

import rospy
from hal_hw_interface import hal
from hal_402_device_mgr.hal_402_mgr import Hal402Mgr

from .helpers import wait_for_param


class HALIoPlumber:
    def __init__(self, prefix):
        self.prefix = prefix
        self.hal_io = hal.components['hal_io']
        self.reset_douts = False
        self.propagate_state_cmd = False
        self._din_pins = {}
        self._dout_pins = {}
        self._dout_fb_pins = {}

    def signal(self, name, type_=None):
        if type_ is None:
            return hal.Signal(f"{self.prefix}{name}")
        else:
            return hal.Signal(f"{self.prefix}{name}", type_)

    def _link_hal_mgr_pins(self):
        rospy.loginfo("Connecting hal_mgr pins")

        state_cmd = self.hal_io.pin('state_cmd')
        state_cmd_sig = self.signal('state_cmd')
        if state_cmd.signal:
            old_sig = state_cmd.signal
            state_cmd.unlink()
            if self.propagate_state_cmd:
                rospy.loginfo("Propagating state_cmd state")
                value = old_sig.get()
                if value == Hal402Mgr.Command.FAULT:
                    value = Hal402Mgr.Command.STOP
                    rospy.loginfo("state_cmd is FAULT, setting to STOP")
                state_cmd_sig.set(value)
        state_cmd.link(state_cmd_sig)

        rospy.loginfo("Finished connecting hal_mgr pins")

    def _link_controller_pins(self):
        # Controller error code
        cec_pin = self.hal_io.pin('controller_error_code')
        cec_pin.unlink()
        cec_pin.link(self.signal('controller_error_code'))

        # Link probe pin polarity selection to hal_hw_interface
        probe_al_pin = self.hal_io.pin('probe_active_low')
        probe_al_pin.unlink()
        probe_al_sig = self.signal('probe_signal_active_low')
        probe_al_pin.link(probe_al_sig)
        probe_in_pin = self.hal_io.pin('probe_in')
        probe_in_pin.unlink()
        probe_in_pin.link(self.signal('probe_actual'))
        saved_probe_passive = wait_for_param('/user_config/probe/passive', 20)
        rospy.loginfo(
            "Restoring saved probe polarity setting: "
            f"{'passive' if saved_probe_passive else 'active'}"
        )
        probe_al_sig.set(saved_probe_passive)

    def _link_safety_input_pins(self):
        rospy.loginfo('Connecting hal pins for safety input')

        safety_input = self.hal_io.pin('safety_input')
        safety_input.unlink()
        safety_input.link(self.signal('safety_input'))

        enabling_input = self.hal_io.pin('enabling_input')
        enabling_input.unlink()
        enabling_input.link(self.signal('enabling_input'))

        max_vel_safety_scale = self.hal_io.pin('max_vel_safety_scale')
        max_vel_safety_scale.unlink()
        max_vel_safety_scale.link(self.signal('max_vel_safety_scale'))

        quick_stop = self.hal_io.pin('quick_stop')
        quick_stop.unlink()
        quick_stop.link(self.signal('quick_stop'))

        rospy.loginfo('Finished connecting hal pins for safety input')

    def _link_io_pins(self):
        rospy.loginfo('Linking digital io pins')
        for pin, signal in self._dout_pins.items():
            pin.unlink()
        if self.reset_douts:
            for pin, signal in self._dout_fb_pins.items():
                pin.set(signal.get())
            rospy.loginfo('Resetting all digital outputs')
            self._reset_and_wait()
        for pin, signal in self._dout_pins.items():
            pin.link(signal)
        for pin, signal in self._din_pins.items():
            pin.unlink()
            pin.link(signal)
        rospy.loginfo('Finished linking digital io pins')

    def _reset_and_wait(self):
        reset_pin = self.hal_io.pin('reset')
        reset_pin.set(True)
        while reset_pin.get():
            sleep(0.01)

    def activate(self):
        self._link_io_pins()
        self._link_safety_input_pins()
        self._link_hal_mgr_pins()
        self._link_controller_pins()


class HALIoPlumberSim(HALIoPlumber):
    def __init__(self, prefix='', create_rcomp=True):
        super().__init__(prefix=prefix)
        self.create_rcomp = create_rcomp

        self._setup_sim_pins()

    def _setup_sim_pins(self):
        if self.create_rcomp:
            # mirror hal_io digital io pins to rcomp
            rospy.loginfo('Creating io-rcomp HAL remote component')
            rcomp = hal.RemoteComponent('io-rcomp', timer=100)
        for pin in self.hal_io.pins():
            name = '.'.join(pin.name.split('.')[1:])
            if not name.startswith('digital_') or name.endswith('_fb'):
                continue
            signal = self.signal(name, hal.HAL_BIT)
            if self.create_rcomp:
                rcomp.newpin(
                    name,
                    pin.type,
                    hal.HAL_IN if pin.dir is hal.HAL_OUT else hal.HAL_IO,
                )
                rcomp.pin(name).link(signal)
            # defer linking to activate method
            if 'out' in name:
                self._dout_pins[pin] = signal
                self._dout_fb_pins[self.hal_io.pin(f'{name}_fb')] = signal
            else:
                self._din_pins[pin] = signal
        if self.create_rcomp:
            rcomp.ready()
            rospy.loginfo('io-rcomp HAL remote component ready')

        self.signal('safety_input').set(True)
        self.signal('enabling_input').set(True)


class HALIoPlumberEtherCAT(HALIoPlumber):
    def __init__(self, prefix='', drive_type='SV660N'):
        super().__init__(prefix=prefix)

        if drive_type == 'SV660N':
            self._setup_lcec_sv660n_pins()
        elif drive_type == 'IS620N':
            self._setup_lcec_is620n_pins()

    def _create_hal_io_pins_from_map(self, signal_to_pin_map):
        for hal_sig_name, pins in signal_to_pin_map.items():
            lcec_pin = hal.Pin(pins[0])
            # by default, io pin name is the same as the signal, unless overridden with a specific name
            hal_io_pin = self.hal_io.pin(pins[1] or hal_sig_name)
            rospy.loginfo(
                f"Linking {hal_sig_name}: {lcec_pin.name} {hal_io_pin.name}"
            )
            hal_sig = self.signal(hal_sig_name, hal.HAL_BIT)
            if 'out' in hal_io_pin.name:
                self._dout_pins[hal_io_pin] = hal_sig
                self._dout_fb_pins[hal.Pin(f'{hal_io_pin.name}_fb')] = hal_sig
            else:
                self._din_pins[hal_io_pin] = hal_sig
            lcec_pin.link(hal_sig)

    def _setup_lcec_is620n_pins(self):
        rospy.loginfo('Connecting IS620N lcec pins')
        is620n_signal_to_pin_map = {
            "enabling_input": ("lcec.0.6.din-14", "digital_in_15"),
            "safety_input": ("lcec.0.6.din-15", "digital_in_16"),
        }
        # add standard io signals
        is620n_signal_to_pin_map.update(
            {f"digital_in_{n+1}": (f"lcec.0.6.din-{n}", "") for n in range(14)}
        )
        is620n_signal_to_pin_map.update(
            {
                f"digital_out_{n+1}": (f"lcec.0.6.dout-{n}", "")
                for n in range(16)
            }
        )
        self._create_hal_io_pins_from_map(is620n_signal_to_pin_map)

        rospy.loginfo('Finished connecting IS602N lcec pins')

    def _setup_lcec_sv660n_pins(self):
        rospy.loginfo('Connecting SV660N lcec pins')
        sv660n_signal_to_pin_map = {
            # Map DIO signals to drive pins according to ethercat.xml and IO integration
            # board
            #
            # Digital inputs:  SV660 has five DIs; use 2-5 on first three drives
            "digital_in_1": ("lcec.0.0.di2", ""),
            "digital_in_2": ("lcec.0.0.di3", ""),
            "digital_in_3": ("lcec.0.0.di4", ""),
            "digital_in_4": ("lcec.0.0.di5", ""),
            "digital_in_5": ("lcec.0.1.di2", ""),
            "digital_in_6": ("lcec.0.1.di3", ""),
            "digital_in_7": ("lcec.0.1.di4", ""),
            "digital_in_8": ("lcec.0.1.di5", ""),
            "digital_in_9": ("lcec.0.2.di2", ""),
            "digital_in_10": ("lcec.0.2.di3", ""),
            "enabling_input": ("lcec.0.2.di4", "digital_in_11"),
            "safety_input": ("lcec.0.2.di5", "digital_in_12"),
            # Digital Outputs:  SV660 has three DOs; DO3 used for brakes
            "digital_out_1": ("lcec.0.0.do1", ""),
            "digital_out_2": ("lcec.0.0.do2", ""),
            "digital_out_3": ("lcec.0.1.do1", ""),
            "digital_out_4": ("lcec.0.1.do2", ""),
            "digital_out_5": ("lcec.0.2.do1", ""),
            "digital_out_6": ("lcec.0.2.do2", ""),
            "digital_out_7": ("lcec.0.3.do1", ""),
            "digital_out_8": ("lcec.0.3.do2", ""),
            "digital_out_9": ("lcec.0.4.do1", ""),
            "digital_out_10": ("lcec.0.4.do2", ""),
            "digital_out_11": ("lcec.0.5.do1", ""),
            "digital_out_12": ("lcec.0.5.do2", ""),
        }
        self._create_hal_io_pins_from_map(sv660n_signal_to_pin_map)
        rospy.loginfo('Finished connecting SV660N lcec pins')
