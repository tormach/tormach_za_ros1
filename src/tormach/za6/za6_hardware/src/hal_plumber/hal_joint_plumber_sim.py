from hal_hw_interface import hal

from .hal_joint_plumber import HALJointPlumber


class HALJointPlumberSim(HALJointPlumber):
    # For sim mode, set up components to simulate the drive moving
    # to the commanded position
    #
    # Simulated motion:
    # - A limit3 comp pretends to move to command position
    #   w/velocity and accel limits
    #
    # Enable chain:
    #
    # - When disabled and zero velocity (sim_drive_load and2 comp),
    #   enable sim motion load pin to accommodate startup position changes
    #
    # - This still allows pretending to be real hardware that takes
    #   time to stop after enable goes low
    #
    # - Sim drive operation_enabled set to True; False doesn't make
    #   sense
    #
    # signal                 -> comp/pin            -> signal
    # ------                    --------               ------
    # (N/A)                sim_startup_selector.load -> sim_drive_load
    #
    # sim_drive_load         -> *_sim_drive.load
    #
    # enable                 -> sim_startup_selector.enable

    def connect_drive(self):
        # Set up simulated start position
        sim_pos_channel = self.newinst("muxnv2", "sim_pos_channel")
        # - Net sim start-up position to sim drive input
        sim_cmd_or_start_pos = self.newsig(
            "sim_cmd_or_start_pos", hal.HAL_FLOAT
        )
        sim_cmd_or_start_pos.link(sim_pos_channel.pin("out"))
        # - Selector inputs
        self.global_signal("sim_pos_sel").link(sim_pos_channel.pin("sel"))
        self.signal("ros_pos_cmd").link(sim_pos_channel.pin("in0"))  # cmd pos
        sim_pos_channel.pin("in1").set(
            self.sim_startup_position
        )  # start-up pos

        # - Add update function at drive fb position
        self.func_config(
            f"{sim_pos_channel.name}.funct", self.Prio.DRIVE_READ_FB + 23
        )

        # Set up simulated drive motion
        # - Use limit3 comp
        sim_drive = self.newinst("limit3", "sim_drive")
        # - Sim drive joint limits
        sim_drive.pin("maxv").set(self.max_vel)
        sim_drive.pin("maxa").set(self.max_acc)
        # - Plumb input & output
        sim_drive.pin("in").link(sim_cmd_or_start_pos)
        # self.link_signal("drive_pos_fb", "sim_drive.out")
        self.signal("pos_fb").link(sim_drive.pin("out"))
        self.signal("vel_fb").link(sim_drive.pin("out-vel"))
        # add signal for loading values
        self.global_signal("sim_pos_load").link(sim_drive.pin("load"))

        # - Link start pin to enable_operation
        self.signal("cw_bit_enable_operation").link(sim_drive.pin("start"))
        # - Add update function after sim start position
        self.func_config(
            f"{sim_drive.name}.funct", self.Prio.DRIVE_READ_FB + 30
        )

        # Set up simulated drive state, mode, fault signals
        sw_sig = self.signal("status-word")
        hal_402_mgr = self.comp("hal_402_mgr")
        sw_sig.link(hal_402_mgr.pin(f"drive_{self.num}.status-word-sim"))
        drive_mode_pin = hal_402_mgr.pin(f"drive_{self.num}.drive-mode-fb")
        drive_mode_pin.unlink()
        del hal.signals[self.jname("drive-mode-fb")]
        dmc_sig = self.signal("drive-mode-cmd")
        dmc_sig.link(drive_mode_pin)

        for name, val in {
            "slave-online": True,
            "slave-oper": True,
            "slave-state-init": False,
            "slave-state-preop": False,
            "slave-state-safeop": False,
            "slave-state-op": True,
        }.items():
            self.signal(name).set(val)
