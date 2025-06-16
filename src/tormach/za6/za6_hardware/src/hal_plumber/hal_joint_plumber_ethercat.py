from math import pi

from hal_hw_interface import hal

from .hal_joint_plumber import HALJointPlumber


class HALJointPlumberEtherCAT(HALJointPlumber):
    # Quick stop chain:
    #
    # When any drive faults, force low QUICK STOP bit 2 of all drives
    # control word.  The hal_402_mgr is then responsible for stopping
    # enabled drives and waiting for the command to reset the fault.
    #
    # Control word quick stop can be high only if:
    # - no drives in fault AND
    # - hal_402_mgr control word quick stop bit is high
    #
    # Components:
    # - any_fault:  or, 6-inputs, SAFETY_CHAIN + 50
    # - any_fault_s32:  conv_bit_s32, SAFETY_CHAIN + 60
    # - control-word_mask:  muxn_u32, pincount=2, SAFETY_CHAIN + 70
    # - *-control-word_safe:  bitwise, SAFETY_CHAIN + 80
    # - *-cw_bits:  bitslice, SAFETY_CHAIN + 90
    #
    # signal                -> comp/pin                   -> signal
    # ------                   --------                      ------
    #                          lcec.0.*.fault -------------> *-fault
    # *-fault -------------+-> any_fault ------------------> any_fault
    # quick_stop ---------/
    # any_fault ----------\
    # 0xffff --------------+-> control-word_mask ----------> control-word_mask
    # 0xfffb -------------/
    #                          hal_402_mgr.*-control-word -> *-control-word
    # control-word_mask --+--> *-control-word_safe --------> *-control-word_safe
    # *-control-word ----<
    #                     \--> *-cw_bits ------------------> *-cw_bit_*
    # *-control-word      ---> lcec.0.*.control-word
    #
    #
    # Feedback chain:
    #
    # signal                -> comp/pin                   -> signal
    # ------                   --------                      ------
    #                      lcec.0.*.position-actual-value -> drive_pos_fb_s32
    # drive_pos_fb_s32      -> joint_helper.*.fb_in
    #                          joint_helper.*.fb_out      -> drive_pos_fb
    # drive_pos_fb          -> fb_pll.pos-in
    #                          fb_pll.pos-out             -> pos_fb
    # pos_fb                -> qc.pos-fb
    #                          fb_pll.vel-out             -> vel_fb
    # vel_fb                -> qc.vel-fb
    #                          fb_pll.acc-out             -> acc_fb
    # acc_fb                -> qc.acc-fb
    # torque_fb             -> qc.torque-fb
    #               lcec.0.*.following-error-actual-value -> drive_pos_err_s32
    # drive_pos_err_s32     -> joint_helper.*.ferror_in
    #                          joint_helper.*.ferror_out  -> pos_err
    #
    # function                 prio
    # --------                 ----
    #                          DRIVE_READ_FB = 100
    # lcec.0.read              DRIVE_READ_FB
    #                          FB_CHAIN = 400
    # fb_pll.funct             FB_CHAIN + 3
    # joint_helper.update_fb   FB_CHAIN + 10
    #
    #
    # Command chain:
    #
    # signal                -> comp/pin                   -> signal
    # ------                   --------                      ------
    # ros_pos_cmd           -> cmd_pll.pos-in
    #                          cmd_pll.pos-out            -> pos_cmd_pll
    # pos_cmd_pll           -> qc.pos-in
    #                          qc.pos-out                 -> pos_cmd
    # pos_cmd               -> joint_helper.*.cmd_in
    #                          joint_helper.*.cmd_out     -> drive_pos_cmd_s32
    # drive_pos_cmd_s32     -> lcec.0.%i.position-reference
    # ros_vel_cmd           -> cmd_pll.vel-in
    #                          cmd_pll.vel-out            -> vel_cmd_pll
    # vel_cmd_pll           -> qc.vel-in
    #                          qc.vel-out                 -> vel_cmd
    # ros_acc_cmd           -> cmd_pll.acc-in
    #                          cmd_pll.acc-out            -> acc_cmd_pll
    # acc_cmd_pll           -> qc.acc-in
    #                          qc.acc-out                 -> acc_cmd
    #                          qc.torque-ff               -> torque_cmd
    #
    # function                 prio
    # --------                 ----
    #                          CMD_CHAIN = 700
    # cmd_pll.funct            CMD_CHAIN + 1
    # qc.funct                 CMD_CHAIN + 2
    # joint_helper.update_cmd  CMD_CHAIN + 20
    # lcec.0.write             DRIVE_WRITE_CMD (900)
    #
    #
    # 402 mgr chain:
    #
    # - Pins with names from lcec_to_402_mgr_pins on hal_402_mgr.drive* and
    #   lcec.0.* connected

    # 2^23 / (2*Pi) = 1335088.42886
    encoder_ticks_per_rev = pow(2, 23) / (2 * pi)

    def connect_drive(self):
        jhelper = self.comp(f"joint_helper.{self.jname_raw()}")
        # fb from drive
        self.newsig("drive_pos_fb_s32", hal.HAL_S32)  # Unscaled pos fb
        self.newsig("drive_pos_fb", hal.HAL_FLOAT)  # Scaled pos fb
        self.newsig("drive_pos_err_s32", hal.HAL_S32)

        # ???
        # self.newsig('torque_cmd', hal.HAL_FLOAT)
        # self.newsig('load', hal.HAL_FLOAT)
        # self.newsig('inertia', hal.HAL_FLOAT)
        # self.newsig('friction', hal.HAL_FLOAT)
        # self.newsig('damping', hal.HAL_FLOAT)
        self.newsig("curr_periodf", hal.HAL_FLOAT)
        self.newsig("counter", hal.HAL_S32)

        # cmd to drive
        self.newsig("drive_pos_cmd_s32", hal.HAL_S32)
        self.newsig("pos_cmd_pll", hal.HAL_FLOAT)
        self.newsig("vel_cmd_pll", hal.HAL_FLOAT)
        self.newsig("acc_cmd_pll", hal.HAL_FLOAT)

        # calculate vel and acc cmd from pos cmd
        cmd_pll = self.newinst("pll", "cmd_pll")
        self.func_config(f"{cmd_pll.name}.funct", self.Prio.CMD_CHAIN + 1)

        qc = self.newinst("qc", "qc")
        self.func_config(f"{qc.name}.funct", self.Prio.CMD_CHAIN + 2)

        # set joint scale
        jhelper.pin("gain").set(self.encoder_ticks_per_rev * self.gear_ratio)

        # load parameters from hardware_settings.yaml
        cmd_pll.pin("bandwidth").set(self.cmd_bandwidth)
        cmd_pll.pin("max-pos").set(self.max_pos)
        cmd_pll.pin("min-pos").set(self.min_pos)
        cmd_pll.pin("max-vel").set(self.max_vel * 20.0)
        cmd_pll.pin("max-acc").set(self.max_acc * 20.0)
        cmd_pll.pin("mode").set(2)

        self.signal("cw_bit_enable_operation").link(cmd_pll.pin("en"))
        self.signal("ros_pos_cmd").link(cmd_pll.pin("pos-in"))
        self.signal("ros_vel_cmd").link(cmd_pll.pin("vel-in"))
        self.signal("ros_acc_cmd").link(cmd_pll.pin("acc-in"))

        self.signal("pos_cmd_pll").link(cmd_pll.pin("pos-out"))
        self.signal("vel_cmd_pll").link(cmd_pll.pin("vel-out"))
        self.signal("acc_cmd_pll").link(cmd_pll.pin("acc-out"))
        self.signal("pos_cmd_pll").link(qc.pin("pos-in"))
        self.signal("vel_cmd_pll").link(qc.pin("vel-in"))
        self.signal("acc_cmd_pll").link(qc.pin("acc-in"))
        self.signal("pos_cmd").link(qc.pin("pos-out"))
        self.signal("pos_fb").link(qc.pin("pos-fb"))
        self.signal("vel_cmd").link(qc.pin("vel-out"))
        self.signal("vel_fb").link(qc.pin("vel-fb"))
        self.signal("acc_cmd").link(qc.pin("acc-out"))
        self.signal("acc_fb").link(qc.pin("acc-fb"))
        self.signal("torque_cmd").link(qc.pin("torque-ff"))
        self.signal("torque_fb").link(qc.pin("torque-fb"))
        self.signal("curr_periodf").link(qc.pin("periodf"))
        self.signal("cw_bit_enable_operation").link(qc.pin("enable"))
        qc.pin("max-pos").set(0.0)
        qc.pin("min-pos").set(0.0)
        qc.pin("max-vel").set(self.max_vel)
        qc.pin("max-acc").set(self.max_acc)

        # calculate vel and acc fb from pos fb
        fb_pll = self.newinst("pll", "fb_pll")
        self.func_config(f"{fb_pll.name}.funct", self.Prio.FB_CHAIN + 3)

        # load parameters from hardware_settings.yaml
        fb_pll.pin("bandwidth").set(self.fb_bandwidth)
        fb_pll.pin("max-pos").set(-1.0)
        fb_pll.pin("min-pos").set(1.0)
        fb_pll.pin("max-vel").set(self.max_vel * 10)
        fb_pll.pin("max-acc").set(self.max_acc * 50)
        fb_pll.pin("mode").set(3)

        self.signal("cw_bit_enable_operation").link(fb_pll.pin("en"))
        self.signal("drive_pos_fb").link(fb_pll.pin("pos-in"))
        self.signal("pos_fb").link(fb_pll.pin("pos-out"))
        self.signal("vel_fb").link(fb_pll.pin("vel-out"))
        self.signal("acc_fb").link(fb_pll.pin("acc-out"))
        self.signal("curr_periodf").link(fb_pll.pin("periodf"))

        # joint feedforward parameter estimation
        # self.newinst("est", "est")
        # self.func_config("est.funct", self.Prio.CMD_CHAIN + 3)

        # self.pin('est.load').set(self.load)
        # self.pin('est.inertia').set(self.inertia)
        # self.pin('est.friction').set(self.friction)
        # self.pin('est.damping').set(self.damping)
        # self.pin('est.load-in').set(self.load)
        # self.pin('est.inertia-in').set(self.inertia)
        # self.pin('est.friction-in').set(self.friction)
        # self.pin('est.damping-in').set(self.damping)
        # self.pin('est.clear').set(self.online_estimation <= 0.0)
        # self.pin('est.max-delta').set(0.25)  # allow +-25% estimation
        # self.pin('est.ji').set(0.0)  # disable inertia estimation
        # self.pin('est.li').set(0.0)  # disable load estimation

        # self.signal("cw_bit_enable_operation").link(self.pin("est.en"))
        # self.signal("load").link(self.pin("est.load"))
        # self.signal("inertia").link(self.pin("est.inertia"))
        # self.signal("friction").link(self.pin("est.friction"))
        # self.signal("damping").link(self.pin("est.damping"))
        # self.signal("vel_cmd").link(self.pin("est.vel-fb"))
        # self.signal("acc_cmd").link(self.pin("est.acc-fb"))
        # self.signal("torque_loop_cmd").link(self.pin("est.torque-fb"))
        # hal.Signal("curr_periodf").link(self.pin("est.periodf"))

        # control loop
        # self.newinst("ppi", "ppi")
        # self.func_config("ppi.funct", self.Prio.CMD_CHAIN + 4)

        # load parameters from hardware_settings.yaml
        # self.pin('ppi.pos-p').set(self.pos_p)
        # self.pin('ppi.vel-p').set(self.vel_p)
        # self.pin('ppi.vel-i').set(self.vel_i)
        # self.pin('ppi.acc-p').set(self.acc_p)
        # self.pin('ppi.acc-i').set(self.acc_i)
        # self.pin('ppi.pos-g').set(self.pos_g)
        # self.pin('ppi.max-pos').set(self.max_pos)
        # self.pin('ppi.min-pos').set(self.min_pos)
        # self.pin('ppi.max-vel').set(self.max_vel * 1.1)
        # self.pin('ppi.max-acc').set(self.max_acc * 1.1)
        # self.pin('ppi.max-torque').set(self.max_torque)
        # self.pin('ppi.torque-boost').set(self.torque_boost)
        # self.pin('ppi.max-pos-error').set(0.1)
        # self.pin('ppi.max-vel-error').set(0.3)
        # self.pin('ppi.max-sat').set(0.5)

        # self.signal("cw_bit_enable_operation").link(self.pin("ppi.en"))
        # self.link_signal('pos_cmd', 'ppi.pos-ff')
        # self.link_signal('vel_cmd', 'ppi.vel-ff')
        # self.link_signal('acc_cmd', 'ppi.acc-ff')
        # self.link_signal('pos_fb', 'ppi.pos-fb')
        # self.link_signal('vel_fb', 'ppi.vel-fb')
        # self.link_signal('acc_fb', 'ppi.acc-fb')
        # self.link_signal('torque_cmd', 'ppi.torque-cmd')
        # self.signal("load").link(self.pin("ppi.load"))
        # self.signal("inertia").link(self.pin("ppi.inertia"))
        # self.signal("friction").link(self.pin("ppi.friction"))
        # self.signal("damping").link(self.pin("ppi.damping"))
        # self.signal("torque_loop_cmd").link(self.pin("ppi.torque-loop-cmd"))
        # hal.Signal("curr_periodf").link(self.pin("ppi.periodf"))

        # connect drive
        self.signal("pos_cmd").link(jhelper.pin("cmd-in"))
        self.signal("drive_pos_cmd_s32").link(jhelper.pin("cmd-out"))
        self.signal("drive_pos_cmd_s32").link(
            f"lcec.0.{self.slavenum}.position-reference"
        )
        self.signal("vel_cmd").link(
            f"lcec.0.{self.slavenum}.velocity-reference"
        )
        self.signal("torque_cmd").link(
            f"lcec.0.{self.slavenum}.torque-reference"
        )

        self.signal("torque_fb").link(
            f"lcec.0.{self.slavenum}.torque-actual-value"
        )

        self.signal("drive_pos_fb_s32").link(
            f"lcec.0.{self.slavenum}.position-actual-value"
        )
        self.signal("drive_pos_fb_s32").link(jhelper.pin("fb-in"))
        self.signal("status-word").link(jhelper.pin("status-word"))
        self.signal("drive_pos_fb").link(jhelper.pin("fb-synth-out"))

        self.signal("drive_pos_err_s32").link(
            f"lcec.0.{self.slavenum}.following-error-actual-value"
        )
        self.signal("drive_pos_err_s32").link(jhelper.pin("ferror-in"))

        # Connect ferror signals for halscope
        # - ferror tolerance:  Set to 110% maxvel period delta
        update_period = self.thread_period / 1e9
        tolerance_factor = 1.10
        p = jhelper.pin("ferror-tol")
        p.set(self.max_vel * update_period * tolerance_factor)
        # - Connect ferror tolerance exceeded, drive ferror, cmd-fb diff signals
        p = jhelper.pin("ferror-tol-exc")
        self.newsig("ferror_tol_exc", hal.HAL_BIT).link(p)
        p = jhelper.pin("ferror-out")
        self.signal("drive_pos_err").link(p)
        p = jhelper.pin("cmd-fb-diff")
        self.newsig("cmd_fb_diff", hal.HAL_FLOAT).link(p)

        # Drive control:  Link lcec pins to 402_mgr
        for name in (
            "control-word",
            "status-word",
            "drive-mode-cmd",
            "drive-mode-fb",
            "aux-error-code",
            "slave-online",
            "slave-oper",
            "slave-state-init",
            "slave-state-preop",
            "slave-state-safeop",
            "slave-state-op",
        ):
            self.signal(name).link(f"lcec.0.{self.slavenum}.{name}")

        # Debugging
        self.signal("counter").link(f"lcec.0.{self.slavenum}.counter")
