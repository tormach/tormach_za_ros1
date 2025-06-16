from hal_hw_interface import rtapi, hal

from .hal_plumber_base import HALPlumberBase


class HALJointPlumber(HALPlumberBase):
    """
    Base class for per-joint HAL configuration. Subclass for specific drives.
    """

    # ========== Feedback chain:
    #
    # - The pos_fb etc. signal inputs come from drive subclasses
    #
    # signal                -> comp/pin                   -> signal
    # ------                   --------                      ------
    # pos_fb                -> hal_hw_interface.*.pos-fb
    # vel_fb                -> hal_hw_interface.*.vel-fb
    # torque_fb             -> hal_hw_interface.*.torque-fb
    #
    #
    # ========== Command chain:
    #
    # - The ros_pos_cmd signal output goes to drive subclasses
    #
    # signal                -> comp/pin                   -> signal
    # ------                   --------                      ------
    #                          hal_hw_interface.*.pos-cmd -> pos_cmd
    #
    #
    # ========== Reset:
    #
    # - The hal_402_mgr sets the reset signal high from just before
    #   enabling the drives to just after.
    #
    # - The reset signal connects to the hal_hw_interface reset pin to
    #   set command to feedback.
    #
    # - The reset signal connects to the jlimits.load pin to set
    #   output to input.
    #
    # ========== Safety input chain
    #
    # signal                -> comp/pin                  -> signal
    # ------                   --------                     ------
    # (TBD)
    #
    def __init__(self, thread_name, thread_period, config, prefix):
        super().__init__(thread_name, thread_period, prefix)
        # set self.num, self.slavenum etc. from config
        # full list in hardware_settings.yaml
        for k, v in config.items():
            setattr(self, k, v)

    #########################
    # Convenience functions to save repeatedly typing and reading
    # `f"joint{self.num}_foo"`
    def jname_raw(self):
        return f"joint{self.num}"

    def jname(self, suffix=None):
        return (
            f"{self.prefix}{self.jname_raw()}{f'_{suffix}' if suffix else ''}"
        )

    def newinst(self, comp_name, suffix, *args, **kwargs):
        return rtapi.newinst(comp_name, self.jname(suffix), *args, **kwargs)

    def newsig(self, suffix, haltype):
        return hal.newsig(self.jname(suffix), haltype)

    def pin(self, suffix):
        return hal.Pin(self.jname(suffix))

    def link_pin(self, from_suffix, to_suffix):
        self.pin(from_suffix).link(self.jname(to_suffix))

    def signal(self, suffix):
        return hal.Signal(self.jname(suffix))

    def global_signal(self, name):
        return super().signal(name)

    def link_global_signal(self, signal, *pin_suffixes):
        if isinstance(signal, str):
            signal = self.global_signal(signal)
        for s in pin_suffixes:
            signal.link(self.jname(s))

    def link_signal(self, sig_suffix, *pin_suffixes):
        self.link_global_signal(self.signal(sig_suffix), *pin_suffixes)

    def set_pin(self, suffix, value):
        self.pin(suffix).set(value)

    def set_signal(self, suffix, value):
        self.signal(suffix).set(value)

    def get_pin(self, suffix):
        return self.pin(suffix).get()

    def func_config(self, base_name, base_prio):
        name = base_name  # self.jname(base_name)
        prio = base_prio + (0.1 * self.num)
        super().func_config(name, prio)

    #########################
    # Set up HAL for a joint

    def setup_hal(self):
        # This represents the high-level work of per-joint HAL setup
        # of feedback and command pipeline comps, signals, settings
        #
        # Set up feedback and command pipeline comps, signals, settings
        self.init_plumbing()
        # - Connect drive-specific config
        self.connect_drive()
        self.init_max_vel_safety()
        # - Per-joint misc stuff
        # self.setup_jlimits()
        # - Drive-specific final operations, optionally implemented in
        #   subclasses
        self.finish_config()

    cw_bits = [
        "switch_on",
        "enable_voltage",
        "quick_stop",
        "enable_operation",
        "mode_1",
        "mode_2",
        "mode_3",
        "fault_reset",
        "halt",
        # Bits 9-15 reserved
    ]

    def init_plumbing(self):
        # joint limits
        # self.newinst("limit3v3", "jlimits")
        # Safety input
        self.newsig("max_vel_safety", hal.HAL_FLOAT)

        self.newsig("ros_pos_cmd", hal.HAL_FLOAT)
        self.newsig("ros_vel_cmd", hal.HAL_FLOAT)
        self.newsig("ros_acc_cmd", hal.HAL_FLOAT)
        self.newsig("pos_fb", hal.HAL_FLOAT)
        self.newsig("vel_fb", hal.HAL_FLOAT)
        self.newsig("torque_fb", hal.HAL_FLOAT)

        self.newsig("pos_cmd_drive", hal.HAL_S32)
        self.newsig("pos_cmd_drive_echo", hal.HAL_S32)
        self.newsig("pos_cmd", hal.HAL_FLOAT)
        self.newsig("drive_pos_err", hal.HAL_FLOAT)
        self.newsig("vel_cmd", hal.HAL_FLOAT)
        self.newsig("acc_cmd", hal.HAL_FLOAT)
        self.newsig("acc_fb", hal.HAL_FLOAT)
        self.newsig("torque_cmd", hal.HAL_FLOAT)

        # Drive control:  Link hal_402_mgr pins to signals
        # - raw_control-word sig:  raw control-word
        drive_safety = self.comp("drive_safety")
        hal_402_mgr = self.comp("hal_402_mgr")
        cwr_sig = self.newsig("raw_control-word", hal.HAL_U32)
        cwr_sig.link(hal_402_mgr.pin(f"drive_{self.num}.control-word"))
        cwr_sig.link(drive_safety.pin(f"raw-control-word{self.slavenum}"))
        # - control-word sig:  raw control-word w/emergency stop override
        cw_sig = self.newsig("control-word", hal.HAL_U32)
        cw_sig.link(drive_safety.pin(f"control-word{self.slavenum}"))
        cw_sig.link(hal_402_mgr.pin(f"drive_{self.num}.control-word-fb"))
        # - status-word, drive-mode-cmd, drive-mode-fb, aux-error-code:
        #   link hal_402_mgr pins to signals
        for name in (
            "status-word",
            "drive-mode-cmd",
            "drive-mode-fb",
            "aux-error-code",
        ):
            sig = self.newsig(name, hal.HAL_U32)
            sig.link(hal_402_mgr.pin(f"drive_{self.num}.{name}"))
        for name in (
            "slave-online",
            "slave-oper",
            "slave-state-init",
            "slave-state-preop",
            "slave-state-safeop",
            "slave-state-op",
        ):
            sig = self.newsig(name, hal.HAL_BIT)
            sig.link(hal_402_mgr.pin(f"drive_{self.num}.{name}"))
        # - status-word:  link to drive_safety
        sw_sig = self.signal("status-word")
        sw_sig.link(drive_safety.pin(f"status-word{self.slavenum}"))
        # - control-word bits:  break out (safe) control word bits into signals
        cw_bits = self.newinst("bitslicev2", "cw_bits", pincount=9)
        self.func_config(f"{cw_bits.name}.funct", self.Prio.SAFETY_CHAIN + 90)
        cw_sig.link(cw_bits.pin("in"))
        for idx, name in enumerate(self.cw_bits):
            s = self.newsig(f"cw_bit_{name}", hal.HAL_BIT)
            s.link(cw_bits.pin(f"out-{idx:02d}"))

    def init_max_vel_safety(self):
        # Set up joint max_vel_safety signal from the configured joint
        # max_vel * global max_vel_safety_scale signal.
        # max_vel_safety_scale is normally 1.0, and changes to
        # something closer to 0.0 when the safety_input goes low.
        max_vel_safety = self.newinst("mult2v2", "max_vel_safety")

        self.global_signal("max_vel_safety_scale").link(
            max_vel_safety.pin("in0")
        )
        max_vel_safety.pin("in1").set(self.max_vel)
        self.signal("max_vel_safety").link(max_vel_safety.pin("out"))

        self.func_config(
            f"{max_vel_safety.name}.funct", self.Prio.SAFETY_CHAIN + 20
        )

    def connect_drive(self):
        # Override in classes
        raise RuntimeError("Subclasses must implement connect_drive() method")

    def finish_config(self):
        pass
