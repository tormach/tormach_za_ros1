import os
import rospy

from hal_hw_interface import hal, loadrt_local, rtapi

from .hal_plumber_base import HALPlumberBase


class HALPlumber(HALPlumberBase):
    """
    This does the top-level configuration, including running the joint-level
    configuration from the HALJointPlumber class; subclass for specific drives
    """

    # Subclasses must define these
    mode_name = "Invalid"
    joint_plumber_class = None

    def __init__(
        self,
        cgname,
        joint_config,
        thread_name,
        thread_period,
        prefix='',
        create_hal_hw_interface=False,
        create_sampler=False,
        unsafe_velocity_limit=0.1,
    ):
        super().__init__(thread_name, thread_period, prefix)
        self.cgname = cgname
        self.joint_config = joint_config
        self.create_hal_hw_interface = create_hal_hw_interface
        self.create_sampler = create_sampler
        self.unsafe_velocity_limit = unsafe_velocity_limit

        self.joints = [
            self.joint_plumber_class(
                thread_name, thread_period, jconfig, prefix
            )
            for jconfig in joint_config.values()
        ]

    @property
    def num_joints(self):
        return len(self.joints)

    def setup_hal(self):
        # This represents the high-level work of setting up HAL
        # - Initialize plumbing
        self.init_plumbing()

        # - Set up safety input max_vel_safety scaling
        self.setup_drive_safety()
        # - Load the 402 manager
        self.load_402_mgr()
        # - Load the hal_hw_interface comp
        if self.create_hal_hw_interface:
            self.load_hal_hw_interface()
        # - Top-level drive set-up (in subclasses)
        self.setup_drive()
        # - Per-joint set-up
        for joint in self.joints:
            joint.setup_hal()

        # - Quick stop drives upon fault
        self.setup_quick_stop()
        # - Load the latency comp
        self.setup_latency()
        # - Load the multilatency comp
        self.setup_multilatency()
        # - Load the sampler comp
        if self.create_sampler:
            self.setup_samplers()
        # - Load wait_hal_settle comp
        self.setup_wait_hal_settle()

        # - Set up thread, add functions, start thread
        self.instantiate_threads()

    def init_plumbing(self):
        # Load locally-build icomps; instances to be created later
        pr = self.Prio
        loadrt_local("pll")
        loadrt_local("latency")
        loadrt_local("qc")
        loadrt_local("multilatency")
        loadrt_local("joint_helper")
        loadrt_local("wait_hal_settle")

        # create the signals to be linked to the hal_hw_interface pins
        self.newsig("reset", hal.HAL_BIT)
        self.newsig("probe_signal_active_low", hal.HAL_BIT)
        self.newsig("probe_actual", hal.HAL_BIT)
        self.newsig("quick_stop", hal.HAL_BIT)
        self.newsig("soft_stop", hal.HAL_BIT)
        self.newsig("controller_error_code", hal.HAL_S32)

        self.newsig('tcp_lin_pos_from_start', hal.HAL_FLOAT)
        self.newsig('tcp_lin_vel', hal.HAL_FLOAT)
        self.newsig('tcp_rot_pos_from_start', hal.HAL_FLOAT)
        self.newsig('tcp_rot_vel', hal.HAL_FLOAT)

        # Joint helper
        for joint in self.joints:
            jh_name = f"joint_helper.{joint.jname_raw()}"
            joint_helper = self.newinst("joint_helper", jh_name)
            self.func_config(
                f"{joint_helper.name}.update-fb",
                pr.FB_CHAIN + 10 + 0.1 * joint.num,
            )
            self.func_config(
                f"{joint_helper.name}.update-cmd",
                pr.CMD_CHAIN + 20 + 0.1 * joint.num,
            )
            self.newsig(joint.jname("counter"), hal.HAL_FLOAT).link(
                f"{joint_helper.name}.counterf"
            )

        # multilatency
        self.newsig("cycle-start-time-s", hal.HAL_S32)
        self.newsig("cycle-start-time-ns", hal.HAL_S32)
        self.newsig("read-exec-time", hal.HAL_S32)
        self.newsig("write-exec-time", hal.HAL_S32)
        self.newsig("cycle-exec-time", hal.HAL_S32)

        # latency
        self.newsig("curr_period", hal.HAL_S32)
        self.newsig("curr_periodf", hal.HAL_FLOAT)

        # Debugging
        num_joints = len(self.joints)
        base_name = f"sum{num_joints}.joint_helper.counter"
        sumn = self.newinst("sumn", base_name, pincount=num_joints)
        self.func_config(f"{sumn.name}.funct", pr.CMD_CHAIN + 21)
        for joint in self.joints:
            self.signal(joint.jname("counter")).link(
                sumn.pin(f"in{joint.num-1}")
            )
        conv = self.newinst('conv_float_s32', f'{base_name}.out')
        self.func_config(f"{conv.name}.funct", pr.CMD_CHAIN + 22)
        self.newsig("counterf", hal.HAL_FLOAT).link(conv.pin("in"))
        self.newsig("counter", hal.HAL_S32).link(conv.pin("out"))

    def setup_drive_safety(self):
        # Desired behavior:
        # - Safety input high:  Drives run at full speed at next motion
        # - Safety input low, falling edge:  Drives quick stop
        # - Safety input low:
        #   - Enabling input low:  Drives cannot start
        #   - Enabling input high:  Drives can start & run at 10% speed

        loadrt_local("drive_safety")
        drive_safety = self.newinst(
            "drive_safety", "drive_safety", drivecount=self.num_joints
        )
        self.func_config(
            f"{drive_safety.name}.funct", self.Prio.SAFETY_CHAIN + 10
        )

        #  Safety input signal:  Safe high
        safety_input_sig = self.newsig("safety_input", hal.HAL_BIT)
        safety_input_sig.link(drive_safety.pin("safety-input"))
        safety_input_sig.set(1)  # For sim

        #  Enabling (deadman) device input:  Enable high
        enabling_input_sig = self.newsig("enabling_input", hal.HAL_BIT)
        enabling_input_sig.link(drive_safety.pin("enabling-input"))
        enabling_input_sig.set(1)  # For sim

        #  Velocity safety scale:  reduce velocity when safety input low
        drive_safety.pin("unsafe-vel-limit").set(self.unsafe_velocity_limit)
        max_vel_scale_sig = self.newsig("max_vel_safety_scale", hal.HAL_FLOAT)
        max_vel_scale_sig.link(drive_safety.pin("vel-limit"))

        # State command for 402_mgr
        sc_sig = self.newsig("state_cmd", hal.HAL_U32)
        sc_sig.link(drive_safety.pin("state-cmd"))

        # External quick stop signal
        qs_sig = self.signal("quick_stop")
        qs_sig.link(drive_safety.pin("quick-stop"))

        # External soft stop signal
        ss_sig = self.signal("soft_stop")
        ss_sig.link(drive_safety.pin("soft-stop"))

    def load_402_mgr(self):
        # Load user comp from ROS package
        comp_name = f"{self.prefix}hal_402_mgr"
        cmd = (
            f"rosrun --debug hal_402_device_mgr hal_402_mgr --name {comp_name}"
        )
        if self.mode_name != 'sim':
            cmd += " --no-sim"
        rospy.loginfo(f"Starting hal_402_mgr component, cmd: '{cmd}'")
        manager = hal.loadusr(
            cmd, wait=True, wait_name=comp_name, wait_timeout=20.0
        )
        rospy.loginfo("Successfully started hal_402_mgr component")

        # Link quick_stop input, reset output, state_cmd IO signals
        self.signal("quick_stop").link(manager.pin("quick_stop"))
        reset_sig = self.signal("reset")
        reset_sig.link(manager.pin("reset"))
        sc_sig = self.signal("state_cmd")
        sc_sig.link(manager.pin("state-cmd"))

    def load_hal_hw_interface(self):
        hal_hw_interface = rtapi.loadrt(
            f'{os.environ["COMP_DIR"]}/hal_hw_interface'
        )

        # Just get the existing signal and link it
        safety_signal = self.signal("safety_input")  # Gets the existing signal
        safety_signal.link(hal_hw_interface.pin("safety_input"))

        enabling_signal = self.signal(
            "enabling_input"
        )  # Gets the existing signal
        enabling_signal.link(hal_hw_interface.pin("enabling_input"))

        # Run the hal_hw_interface function right in the middle
        self.func_config(
            f"{hal_hw_interface.name}.funct", self.Prio.ROS_CONTROL
        )

    def setup_drive(self):
        # Override in classes that need a drive setup routine
        raise RuntimeError("Subclasses must implement setup_drive() method")

    def setup_quick_stop(self):
        raise NotImplementedError

    def setup_latency(self):
        latency = self.newinst("latency", "latency")
        self.func_config(f"{latency.name}.funct", self.Prio.CMD_CHAIN + 30)
        self.signal("curr_period").link(latency.pin("curr-period"))
        self.signal("curr_periodf").link(latency.pin("curr-periodf"))

    def setup_multilatency(self):
        pr = self.Prio
        multilatency = self.newinst("multilatency", "multilatency")
        self.func_config(f"{multilatency.name}.cycle-start", pr.LIST_HEAD)
        self.func_config(
            f"{multilatency.name}.read-start", pr.DRIVE_READ_FB - 1
        )
        self.func_config(f"{multilatency.name}.read-end", pr.DRIVE_READ_FB + 1)
        self.func_config(
            f"{multilatency.name}.write-start", pr.DRIVE_WRITE_CMD - 1
        )
        self.func_config(
            f"{multilatency.name}.write-end", pr.DRIVE_WRITE_CMD + 20
        )
        self.func_config(f"{multilatency.name}.cycle-end", pr.LIST_TAIL)

        self.signal("cycle-start-time-s").link(multilatency.pin("time-s"))
        self.signal("cycle-start-time-ns").link(multilatency.pin("time-ns"))
        self.signal("cycle-exec-time").link(multilatency.pin("cycle-exec-time"))
        self.signal("read-exec-time").link(multilatency.pin("read-exec-time"))
        self.signal("write-exec-time").link(multilatency.pin("write-exec-time"))

    def setup_samplers(self):
        sampler_sigs = [
            "counter",
            "cycle-start-time-s",
            "cycle-start-time-ns",
            "cycle-exec-time",
            "read-exec-time",
            "write-exec-time",
        ]
        if self.mode_name == "EtherCAT":
            sampler_sigs += [
                "joint{0}_drive_pos_cmd_s32",
                "joint{0}_drive_pos_err_s32",
                "joint{0}_drive_pos_fb_s32",
            ]
        # cfg=[fbsu]+
        n_drvs = 6
        depths = "depth=" + ",".join(("1000",) * n_drvs)
        cfgs = "cfg=" + ",".join(("s" * len(sampler_sigs),) * n_drvs)
        sampler = rtapi.loadrt("sampler", depths, cfgs)
        for dnum in range(n_drvs):
            prio = self.Prio.DRIVE_READ_FB + 90 + dnum
            # sampler = f"sampler.{dnum}"
            self.func_config(f"{sampler.name}.{dnum}", prio)
            for ix, sig in enumerate(sampler_sigs):
                name = sig.format(dnum + 1)
                self.signal(name).link(sampler.pin(f"{dnum}.pin.{ix}"))
            sampler.pin(f"{dnum}.enable").set(0)

    def setup_wait_hal_settle(self):
        wait_hal_settle = self.newinst("wait_hal_settle", "wait_hal_settle")
        self.func_config(
            f"{wait_hal_settle.name}.funct", self.Prio.LIST_TAIL - 1
        )
        self.newsig("wait_cycles", hal.HAL_U32).link(
            wait_hal_settle.pin("wait-cycles")
        )

    def instantiate_threads(self):
        # Init HAL thread, maybe setting cgroup
        kwargs = {}
        if self.cgname is not None:
            kwargs["cgname"] = self.cgname
        rtapi.newthread(self.thread_name, self.thread_period, fp=True, **kwargs)
        # Add functions to thread in correct order
        for joint in self.joints:
            self.thread_functs.update(joint.thread_functs)
        self.add_funcs()
        self.signal("curr_period").link(f"{self.thread_name}.curr-period")
