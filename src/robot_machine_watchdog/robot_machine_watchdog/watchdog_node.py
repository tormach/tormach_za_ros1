#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import JointState
from robot_command.execution_commands.pathpilot_abort import PathPilotAbort
from robot_machine_watchdog_msgs.srv import (
    SetWatchdogMode,
    SetWatchdogModeResponse,
)
from robot_machine_watchdog_msgs.srv import (
    CheckTorqueSafetyStatus,
    CheckTorqueSafetyStatusResponse,
)


class RobotMachineWatchdogNode:
    def __init__(self):
        rospy.init_node('robot_machine_watchdog')
        self.rate = rospy.Rate(50)  # 50 Hz to match the topic rate
        self.torque_thresh = rospy.get_param('~torque_threshold', 20)
        # Variables for watchdog state
        self.enable_watchdog = False
        self.reference_torques = None
        self.first_measurement = True
        self.safety_status = True  # Initialize safety status as True

        # Setup the services
        self.set_watchdog_service = rospy.Service(
            'set_robot_machine_watchdog_mode',
            SetWatchdogMode,
            self.handle_set_watchdog_mode,
        )
        self.check_safety_service = rospy.Service(
            'check_torque_safety_status',
            CheckTorqueSafetyStatus,
            self.handle_check_torque_safety_status,
        )

        # Subscribe to joint_states topic
        self.joint_states_sub = rospy.Subscriber(
            '/joint_states', JointState, self.joint_states_callback
        )

        # Initialize PathPilotAbort
        self.pathpilot_abort = PathPilotAbort()
        rospy.loginfo("Robot Machine Watchdog node initialized")

    def handle_set_watchdog_mode(self, req):
        self.enable_watchdog = req.active_status
        if self.enable_watchdog:
            self.torque_thresh = req.torque_thresh
            self.first_measurement = True
            self.safety_status = (
                True  # Clear any existing errors when watchdog is stopped
            )
            rospy.loginfo(
                f"Watchdog activated with threshold {self.torque_thresh}"
            )
        else:
            self.reference_torques = None
            rospy.loginfo("Watchdog deactivated")
        return SetWatchdogModeResponse(success=True)

    def handle_check_torque_safety_status(self, req):
        return CheckTorqueSafetyStatusResponse(
            safety_status=self.safety_status, success=True
        )

    def joint_states_callback(self, msg):
        if not self.enable_watchdog:
            return
        current_torques = msg.effort[:6]  # We only need the first 6 joints
        if self.first_measurement:
            self.reference_torques = current_torques
            self.first_measurement = False
            rospy.loginfo("Reference torques captured")
            return

        torque_exceeded = False
        for ref, current in zip(self.reference_torques, current_torques):
            if abs(current - ref) > self.torque_thresh:
                torque_exceeded = True
                break

        if torque_exceeded:
            rospy.logwarn(
                "Collision detected! Issuing pathpilot_abort command."
            )
            try:
                self.pathpilot_abort.execute()
                rospy.logerr("Torque threshold exceeded. Aborting operation.")
                self.safety_status = False  # Set safety status to False when overtorque error occurs
            except Exception as e:
                rospy.logerr(f"Failed to execute pathpilot_abort: {str(e)}")
            self.enable_watchdog = False  # Disable watchdog after abort

    def run(self):
        while not rospy.is_shutdown():
            self.rate.sleep()


if __name__ == '__main__':
    try:
        node = RobotMachineWatchdogNode()
        node.run()
    except rospy.ROSInterruptException:
        pass
