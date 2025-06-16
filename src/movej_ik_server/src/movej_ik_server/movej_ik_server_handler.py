import numbers
import rospy

from movej_ik_server.arm_configs import JointConfig

from movej_ik_server_msgs.srv import (
    MovejUserIKService,
    MovejClosestIKService,
    GetArmConfigService,
)

from movej_ik_server_msgs.msg import (
    ArmConfigs,
    IKSolverError,
    IKSolverWarning,
)

robot_configs = {
    "NUT": ArmConfigs.NUT,  # shoulder left, elbow up, wrist non-flipped
    "NDT": ArmConfigs.NDT,  # shoulder left, elbow down, wrist non-flipped
    "NUB": ArmConfigs.NUB,  # shoulder right, elbow up, wrist non-flipped
    "NDB": ArmConfigs.NDB,  # shoulder right, elbow down, wrist non-flipped
    "FUT": ArmConfigs.FUT,  # shoulder left, elbow up, wrist flipped
    "FDT": ArmConfigs.FDT,  # shoulder left, elbow down, wrist flipped
    "FUB": ArmConfigs.FUB,  # shoulder right, elbow up, wrist flipped
    "FDB": ArmConfigs.FDB,  # shoulder right, elbow down, wrist flipped
}

inverted_robot_configs = {v: k for k, v in robot_configs.items()}


def log_warning(code):
    warning_messages = {
        IKSolverWarning.ARM_CONFIG_CHANGED: "ARM_CONFIG_CHANGED WARNING.",
        IKSolverWarning.REV_COUNT_CHANGED: "REV_COUNT_CHANGED WARNING.",
        IKSolverWarning.START_POSE_WRIST_NEAR_SINGULARITY: "START_POSE_WRIST_NEAR_SINGULARITY WARNING.\n-- EXTENDED INFO --\nWrist at the start pose is close to singularity.\nIgnoring analytical model IK computation for the start pose and using current joint values to compute the closest goal IK solution.",
        IKSolverWarning.START_POSE_SHOULDER_NEAR_SINGULARITY: "START_POSE_SHOULDER_NEAR_SINGULARITY WARNING.",
        IKSolverWarning.START_POSE_SHOULDER_NEAR_SINGULARITY: "START_POSE_SHOULDER_NEAR_SINGULARITY WARNING.",
        IKSolverWarning.REQUESTED_CONFIG_NEAR_SINGULARITY: "REQUESTED_CONFIG_NEAR_SINGULARITY WARNING.",
    }

    if code in warning_messages:
        rospy.loginfo(warning_messages[code])
    else:
        rospy.logwarn("Unknown warning code: %s", code)


def log_error(code):
    error_messages = {
        IKSolverError.NO_ANALYTICAL_SOLUTION: "NO_ANALYTICAL_SOLUTION ERROR.\n-- EXTENDED INFO --\nProvided pose is outside of the robot's workspace. Change the pose, user frame or tool frame. Check if the system units are correct.",
        IKSolverError.NO_NUMERICAL_SOLUTION: "NO_NUMERICAL_SOLUTION ERROR.",
        IKSolverError.INVALID_CONFIG_CANDIDATES: "INVALID_CONFIG_CANDIDATES ERROR.\n-- EXTENDED INFO --\nChange the arm configuration string or the revolution count number.\nAllowed arm configurations are: NUT, FUT, NDT, FDT, NUB, FUB, NDB, FDB.\nAllowed J6 revolution count values are: -1, 0, 1.\n\nNote that some of these arm configurations and revolution count values may be not reachable.",
        IKSolverError.SOLUTION_OUTSIDE_JOINT_LIMITS: "SOLUTION_OUTSIDE_JOINT_LIMITS ERROR.\n-- EXTENDED INFO --\nChange the arm configuration or revolution count setting to a different value.",
        IKSolverError.UNREACHABLE_REV_COUNT: "UNREACHABLE_REV_COUNT ERROR.\n-- EXTENDED INFO --\nThis revolution count number is not reachable for the pose you specified.\nTry using another revolution count value from the set of -1, 0, or 1.",
        IKSolverError.POSE_NO_LONGER_REACHABLE: "POSE_NO_LONGER_REACHABLE ERROR.",
        IKSolverError.WRIST_NEAR_SINGULARITY: "WRIST_NEAR_SINGULARITY ERROR.\n-- EXTENDED INFO --\nWrist is too close to singuarity which might result in an unstable solution.\nConsider adjusting the pose or using movej(j[]) to reach it.",
        IKSolverError.FATAL_ANALYTICAL_NUMERICAL_MISMATCH: "FATAL_ANALYTICAL_NUMERICAL_MISMATCH ERROR.\n-- EXTENDED INFO --\nIK solution is unstable.\nConsider moving the goal pose a bit further from the singularity.",
        IKSolverError.START_POSE_FAILURE: "START_POSE_FAILURE ERROR.",
        IKSolverError.GOAL_POSE_FAILURE: "GOAL_POSE_FAILURE ERROR.",
        IKSolverError.GET_CONFIG_FAILURE: "GET_CONFIG_FAILURE ERROR.",
        IKSolverError.EFFECTOR_POSE_UNAVAILABLE: "EFFECTOR_POSE_UNAVAILABLE ERROR.",
        IKSolverError.JOINTS_STATE_UNAVAILABLE: "JOINTS_STATE_UNAVAILABLE ERROR.",
        IKSolverError.CACHED_JOINTS_INVALID_SIZE: "CACHED_JOINTS_INVALID_SIZE ERROR.",
    }

    # Check if the error code exists in the dictionary
    if code in error_messages:
        rospy.logerr(error_messages[code])
    else:
        rospy.logerr("Unknown error code: %s", code)


class MovejIkServerHandler:
    def __init__(self):
        self.movej_closest_ik_service_client = rospy.ServiceProxy(
            'movej_closest_ik_service', MovejClosestIKService
        )

        self.movej_user_ik_service_client = rospy.ServiceProxy(
            'movej_user_ik_service', MovejUserIKService
        )

        self.get_arm_config_service_client = rospy.ServiceProxy(
            'arm_config_service', GetArmConfigService
        )

    def movej_user_ik_service_call(self, target, arm_config, rev_count):
        try:
            cached_joints = []
            response = self.movej_user_ik_service_client(
                target, cached_joints, arm_config, rev_count
            )
            if response.warning_codes is not None:
                for warning_code in response.warning_codes:
                    log_warning(warning_code)

            if response.error_codes is not None:
                for error_code in response.error_codes:
                    log_error(error_code)

            return response.joint_values, True
        except rospy.ServiceException as e:
            rospy.logerr("Service call failed: %s" % e)
            return None, False

    def movej_closest_ik_service_call(
        self,
        target,
        arm_config=ArmConfigs.ANY_ARM_CONFIG,
        rev_count=ArmConfigs.ANY_REV_COUNT,
    ):
        try:
            response = self.movej_closest_ik_service_client(
                target, arm_config, rev_count
            )

            if response.warning_codes is not None:
                for warning_code in response.warning_codes:
                    log_warning(warning_code)

            if response.error_codes is not None:
                for error_code in response.error_codes:
                    log_error(error_code)

            return response.joint_values, True
        except rospy.ServiceException as e:
            rospy.logerr("Service call failed: %s" % e)
            return None, False

    def get_arm_config_service_call(
        self,
        joint_values=[],
    ):
        try:
            response = self.get_arm_config_service_client(joint_values)

            if response.warning_codes is not None:
                for warning_code in response.warning_codes:
                    log_warning(warning_code)

            if response.error_codes is not None:
                for error_code in response.error_codes:
                    log_error(error_code)

            return response, True
        except rospy.ServiceException as e:
            rospy.logerr("Service call failed: %s" % e)
            return None, False

    def call_movej_ik_server(self, target):
        """
        Handle movej_ik service request.
        """
        target_ros_pose = target.to_ros_pose()
        success = None
        my_target_joints = None

        if isinstance(target.conf, JointConfig) and isinstance(
            target.rev, numbers.Integral
        ):
            my_target_joints, success = self.movej_closest_ik_service_call(
                target=target_ros_pose,
                arm_config=target.conf.value,
                rev_count=target.rev,
            )
        elif isinstance(target.conf, JointConfig):
            my_target_joints, success = self.movej_closest_ik_service_call(
                target=target_ros_pose,
                arm_config=target.conf.value,
            )
        else:
            my_target_joints, success = self.movej_closest_ik_service_call(
                target=target_ros_pose,
            )

        return my_target_joints, success
