from time import sleep

import rospy
from hal_hw_interface import hal


class HALHwInterfacePlumberPart:
    HAL_CYCLE_WAIT_TIME_S = 0.01

    def __init__(self, prefix, num_joints, reset_joints=False):
        self.prefix = prefix
        self.num_joints = num_joints
        self.reset_joints = reset_joints

    def jname(self, num, suffix=None):
        return f"joint{num}{f'_{suffix}' if suffix else ''}"

    def signal(self, name):
        return hal.Signal(f"{self.prefix}{name}")

    def unlink_pin_signal(self, pin):
        if not pin.signal:
            return
        for pin in pin.signal.pins():
            pin.unlink()

    def wait_for_hal(self, num_cycles=5):
        """Makes sure to wait for a minimum number of HAL cycles"""
        wait_cycles_sig = self.signal("wait_cycles")
        wait_cycles_sig.set(num_cycles)
        while wait_cycles_sig.get() > 0:
            sleep(self.HAL_CYCLE_WAIT_TIME_S)

    def connect_hal_hw_interface(self):
        rospy.loginfo("Connecting hal_hw_interface")

        hal_hw_interface = hal.components["hal_hw_interface"]

        rospy.loginfo("Connecting config signals")

        probe_pin = hal_hw_interface.pin("probe-signal-in")
        probe_pin.unlink()
        # Probe hard-coded to DI1 for now; eventually make this programmable
        self.signal("digital_in_1").link(probe_pin)

        probe_al_pin = hal_hw_interface.pin("probe-signal-active-low")
        probe_al_pin.unlink()
        self.signal("probe_signal_active_low").link(probe_al_pin)

        probe_out_pin = hal_hw_interface.pin("probe-out")
        probe_out_pin.unlink()
        self.signal("probe_actual").link(probe_out_pin)

        stop_pin = hal_hw_interface.pin("stop")
        stop_pin.unlink()
        self.signal("soft_stop").link(stop_pin)

        estop_pin = hal_hw_interface.pin("estop")
        estop_pin.unlink()
        self.signal("quick_stop").link(estop_pin)

        # Controller error code signal
        cec_pin = hal_hw_interface.pin("error-code")
        cec_pin.unlink()
        self.signal("controller_error_code").link(cec_pin)

        reset_pin = hal_hw_interface.pin("reset")
        reset_pin.unlink()
        if self.reset_joints:
            rospy.loginfo("Preparing to reset joint positions")
            reset_pin.set(True)
        self.wait_for_hal()

        rospy.loginfo("Connecting Virtual TCP joints")
        # Virtual TCP joints
        tcp_lin_pos = self.signal("tcp_lin_pos_from_start")
        tcp_lin_pos_pin = hal_hw_interface.pin('tcp_lin.pos-cmd')
        self.unlink_pin_signal(tcp_lin_pos_pin)
        tcp_lin_pos.link(tcp_lin_pos_pin)
        tcp_lin_pos.link(hal_hw_interface.pin('tcp_lin.pos-fb'))
        tcp_lin_vel = self.signal("tcp_lin_vel")
        tcp_lin_vel_pin = hal_hw_interface.pin('tcp_lin.vel-cmd')
        self.unlink_pin_signal(tcp_lin_vel_pin)
        tcp_lin_vel.link(tcp_lin_vel_pin)
        tcp_lin_vel.link(hal_hw_interface.pin('tcp_lin.vel-fb'))
        tcp_rot_pos = self.signal("tcp_rot_pos_from_start")
        tcp_rot_pos_pin = hal_hw_interface.pin('tcp_rot.pos-cmd')
        self.unlink_pin_signal(tcp_rot_pos_pin)
        tcp_rot_pos.link(tcp_rot_pos_pin)
        tcp_rot_pos.link(hal_hw_interface.pin('tcp_rot.pos-fb'))
        tcp_rot_vel = self.signal("tcp_rot_vel")
        tcp_rot_vel_pin = hal_hw_interface.pin('tcp_rot.vel-cmd')
        self.unlink_pin_signal(tcp_rot_vel_pin)
        tcp_rot_vel.link(tcp_rot_vel_pin)
        tcp_rot_vel.link(hal_hw_interface.pin('tcp_rot.vel-fb'))

        rospy.loginfo("Connecting joint signals")
        # Joint signals
        # disconnect all joint signals connected to hal_hw_interface
        for i in range(self.num_joints):
            self.connect_joint_signals(num=i + 1, disconnect=True)
        # optionally enable loading joint values from hal_hw_interface to sim
        if not self.reset_joints:
            rospy.loginfo("Loading joint positions to sim config")
            self.signal('sim_pos_load').set(True)
            self.wait_for_hal()  # wait for sim drive comps to update
        # connect command and feedback signals for all joints
        # the order depends on whether we are resetting hal_hw_interface
        for i in range(self.num_joints):
            self.connect_joint_signals(
                num=i + 1, cmd=(not self.reset_joints), fb=self.reset_joints
            )
        self.wait_for_hal()
        for i in range(self.num_joints):
            self.connect_joint_signals(
                num=i + 1, cmd=self.reset_joints, fb=(not self.reset_joints)
            )
        self.wait_for_hal()
        # done loading joint values to sim
        if not self.reset_joints:
            self.signal('sim_pos_load').set(False)
            self.wait_for_hal()

        self.signal("reset").link(reset_pin)

        rospy.loginfo("Finished connecting hal_hw_interface")

    def connect_joint_signals(self, num, disconnect=False, fb=True, cmd=True):
        hal_hw_interface = hal.components["hal_hw_interface"]

        # Joint feedback to ROS
        if fb:
            pos_fb_pin = hal_hw_interface.pin(f"joint_{num}.pos-fb")
            if disconnect:
                pos_fb_pin.unlink()
            else:
                self.signal(self.jname(num, "pos_fb")).link(pos_fb_pin)

            vel_fb_pin = hal_hw_interface.pin(f"joint_{num}.vel-fb")
            if disconnect:
                vel_fb_pin.unlink()
            else:
                self.signal(self.jname(num, "vel_fb")).link(vel_fb_pin)

            eff_fb_pin = hal_hw_interface.pin(f"joint_{num}.eff-fb")
            if disconnect:
                eff_fb_pin.unlink()
            else:
                self.signal(self.jname(num, "torque_fb")).link(eff_fb_pin)

        # ROS commanded position, velocity
        if cmd:
            pos_cmd_pin = hal_hw_interface.pin(f"joint_{num}.pos-cmd")
            if disconnect:
                pos_cmd_pin.unlink()
            else:
                self.signal(self.jname(num, "ros_pos_cmd")).link(pos_cmd_pin)

            vel_cmd_pin = hal_hw_interface.pin(f"joint_{num}.vel-cmd")
            if disconnect:
                vel_cmd_pin.unlink()
            else:
                self.signal(self.jname(num, "ros_vel_cmd")).link(vel_cmd_pin)


class HALHwInterfacePlumber:
    def __init__(self, prefixes, num_joints):
        self.num_joints = num_joints

        self.parts = {
            prefix: HALHwInterfacePlumberPart(
                prefix,
                num_joints,
                reset_joints=prefix != "dr_",  # reset when switching to hw mode
            )
            for prefix in prefixes
        }

    def activate(self, prefix):
        self.parts[prefix].connect_hal_hw_interface()
