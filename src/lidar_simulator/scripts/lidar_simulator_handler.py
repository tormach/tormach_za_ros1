#!/usr/bin/env python3

import rospy
import math
from geometry_msgs.msg import Pose, Quaternion
from lidar_simulator_msgs.srv import (
    AddLidarObject,
    RemoveLidarObject,
    ReportPoses,
)
from std_srvs.srv import Empty
from tf.transformations import quaternion_from_euler


class LidarSimulatorHandler:
    def __init__(self):
        SIMULATOR_NODE_NAME = 'lidar_simulator_wrapper'
        print("Initializing LidarSimulatorHandler...")

        # Check if a ROS node is already running
        if not rospy.core.is_initialized():
            rospy.init_node('lidar_simulator_handler', anonymous=True)
            print("ROS node 'lidar_simulator_handler' initialized.")
        else:
            print("ROS node already initialized. Using existing node.")

        print("Waiting for add_lidar_object service...")
        rospy.wait_for_service(
            f'{SIMULATOR_NODE_NAME}/add_lidar_object', timeout=10
        )
        print("Waiting for remove_lidar_object service...")
        rospy.wait_for_service(
            f'{SIMULATOR_NODE_NAME}/remove_lidar_object', timeout=10
        )
        print("Waiting for remove_all_lidar_objects service...")
        rospy.wait_for_service(
            f'{SIMULATOR_NODE_NAME}/remove_all_lidar_objects', timeout=10
        )

        print("Creating service proxies...")
        self.add_object = rospy.ServiceProxy(
            f'{SIMULATOR_NODE_NAME}/add_lidar_object', AddLidarObject
        )
        self.remove_object = rospy.ServiceProxy(
            f'{SIMULATOR_NODE_NAME}/remove_lidar_object', RemoveLidarObject
        )
        self.remove_all_objects = rospy.ServiceProxy(
            f'{SIMULATOR_NODE_NAME}/remove_all_lidar_objects', Empty
        )
        print("Initialization complete.")

        print("Waiting for report_poses service...")
        rospy.wait_for_service(
            f'{SIMULATOR_NODE_NAME}/report_poses', timeout=10
        )
        self.report_poses = rospy.ServiceProxy(
            f'{SIMULATOR_NODE_NAME}/report_poses', ReportPoses
        )

    def add_lidar_object(self, pose, size_x, size_y):
        print(
            f"Adding lidar object: pose={pose}, size_x={size_x}, size_y={size_y}"
        )
        try:
            response = self.add_object(pose, size_x, size_y)
            print(
                f"Add object response: success={response.success}, message={response.message}"
            )
            return response.success, response.message
        except rospy.ServiceException as e:
            print(f"Service call failed: {e}")
            return False, f"Service call failed: {e}"

    def add_lidar_objects(self, poses, sizes):
        if len(poses) != len(sizes):
            return False, "Number of poses and sizes must match"

        results = []
        for pose, size in zip(poses, sizes):
            success, message = self.add_lidar_object(pose, size[0], size[1])
            results.append((success, message))

        return results

    def remove_lidar_object(self, pose):
        print(f"Removing lidar object: pose={pose}")
        try:
            response = self.remove_object(pose)
            print(
                f"Remove object response: success={response.success}, message={response.message}"
            )
            return response.success, response.message
        except rospy.ServiceException as e:
            print(f"Service call failed: {e}")
            return False, f"Service call failed: {e}"

    def remove_all_lidar_objects(self):
        print("Removing all lidar objects")
        try:
            self.remove_all_objects()
            print("All objects removed successfully")
            return True, "All objects removed successfully"
        except rospy.ServiceException as e:
            print(f"Service call failed: {e}")
            return False, f"Service call failed: {e}"

    def report_existing_objects(self):
        """
        Request and return the poses of all existing planes in the simulator.

        Returns:
            list: A list of geometry_msgs/Pose objects representing the poses of all planes
        """
        print("Requesting poses of existing objects...")
        try:
            response = self.report_poses()
            print(f"Received {len(response.poses)} poses")
            return response.poses
        except rospy.ServiceException as e:
            print(f"Service call failed: {e}")
            return []


# Example use
if __name__ == '__main__':
    try:
        print("Starting LidarSimulatorHandler...")
        handler = LidarSimulatorHandler()

        print("Removing all existing objects...")
        success, message = handler.remove_all_lidar_objects()
        print(f"Remove all objects result: {success}, {message}")

        print("Preparing poses and sizes for multiple objects...")
        poses = []
        sizes = []

        # Plane3
        table = Pose()
        table.position.x = 0.0
        table.position.y = 0.0
        table.position.z = 0.0
        q3 = quaternion_from_euler(0, 0, 0)  # Roll, Pitch, Yaw
        table.orientation = Quaternion(*q3)
        poses.append(table)
        sizes.append((1.45, 1.45))

        # Plane3
        pose3 = Pose()
        pose3.position.x = 0.6
        pose3.position.y = 0.1
        pose3.position.z = 0.0381
        q3 = quaternion_from_euler(0, 0, math.pi / 24)  # Roll, Pitch, Yaw
        pose3.orientation = Quaternion(*q3)
        poses.append(pose3)
        sizes.append((0.119, 0.1018))

        # Plane4
        pose4 = Pose()
        pose4.position.x = 0.4
        pose4.position.y = 0.3
        pose4.position.z = 0.0381
        q4 = quaternion_from_euler(0, 0, 0)  # Roll, Pitch, Yaw
        pose4.orientation = Quaternion(*q4)
        poses.append(pose4)
        sizes.append((0.119, 0.1018))

        print("Adding all objects...")
        results = handler.add_lidar_objects(poses, sizes)
        for i, (success, message) in enumerate(results):
            print(f"Add plane{i+3} result: {success}, {message}")

        print("Planes added. Press Ctrl+C to exit.")
        rospy.spin()
    except rospy.ROSInterruptException:
        print("Program interrupted before completion")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
