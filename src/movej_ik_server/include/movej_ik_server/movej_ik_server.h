#ifndef MOVEJ_IK_SERVER_H
#define MOVEJ_IK_SERVER_H

#include <numeric>
#include <optional>
#include <ros/ros.h>
#include <memory>
#include <std_msgs/String.h>
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/TransformStamped.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <bitset>

#include <geometry_msgs/Pose.h>
#include <Eigen/Geometry>

#include <moveit/planning_scene_monitor/planning_scene_monitor.h>
#include <moveit/robot_state/robot_state.h>

#include <opw_kinematics/opw_kinematics.h>
#include "opw_kinematics/opw_utilities.h"

#include <movej_ik_server_msgs/MovejClosestIKService.h>
#include <movej_ik_server_msgs/MovejUserIKService.h>
#include <movej_ik_server_msgs/GetArmConfigService.h>
#include <movej_ik_server_msgs/SetArmConfigConstraintsService.h>

#include <movej_ik_server_msgs/IKSolverError.h>
#include <movej_ik_server_msgs/IKSolverWarning.h>
#include <movej_ik_server_msgs/ArmConfigs.h>

#include "movej_ik_server/opw_solver.h"
#include "movej_ik_server/trpl_pose.h"

// #include <opw_kinematics/opw_kinematics.h>
// #include "opw_kinematics/opw_utilities.h"

/**
 * @class MoveJIKServer
 * @brief provides ROS interface for inverse kinematics (IK) solutions for a
 * robotic manipulator.
 */
class MoveJIKServer
{
public:
  /**
   * @brief Constructor.
   */
  MoveJIKServer();

  /**
   * @brief handle service request for closest IK solution.
   * @param req Service request containing the desired pose.
   * @param res Service response containing the computed joint values.
   * @return True if the operation was successful, false otherwise.
   */
  bool handle_closest_ik_service(
      movej_ik_server_msgs::MovejClosestIKService::Request& req,
      movej_ik_server_msgs::MovejClosestIKService::Response& res);

  /**
   * @brief handle service request for IK solution for user-specified arm config
   * and revolution count.
   * @param req Service request containing the desired pose.
   * @param res Service response containing the computed joint values.
   * @return True if the operation was successful, false otherwise.
   */
  bool handle_user_ik_service(
      movej_ik_server_msgs::MovejUserIKService::Request& req,
      movej_ik_server_msgs::MovejUserIKService::Response& res);

  /**
   * @brief describe the arm configuration for requested joint values
   * @param req Service request containing joint values.
   * @param res Service response containing arm configuration and revolution
   * count.
   * @return True if the operation was successful, false otherwise.
   */
  bool handle_arm_config_service(
      movej_ik_server_msgs::GetArmConfigService::Request& req,
      movej_ik_server_msgs::GetArmConfigService::Response& res);

  bool handle_arm_config_constraint_service(
      movej_ik_server_msgs::SetArmConfigConstraintsService::Request& req,
      movej_ik_server_msgs::SetArmConfigConstraintsService::Response& res);

private:
  /**
   * @brief Callback function for tool frame subscriber.
   * @param msg Message containing the name of the active tool frame.
   */
  void tool_frame_callback(const std_msgs::String::ConstPtr& msg);

  /**
   * @brief Computes the transform between flange and tool frame.
   * @param relative_transform Resulting transform.
   * @return True if the operation was successful, false otherwise.
   */
  bool calculate_transform(Eigen::Isometry3d& relative_transform);

  /**
   * @brief Retrieves current joint values using MoveIt API.
   * @return joint_values Vector if the operation was successful, false
   * otherwise.
   */
  std::optional<JointArray> get_current_joint_values() const;

  /**
   * @brief Retrieves current end effector pose.
   * @param end_effector_pose ros pose be filled with position and quaternion
   * values.
   * @return True if the operation was successful, false otherwise.
   */
  //   bool get_current_end_effector_pose(geometry_msgs::Pose&
  //   end_effector_pose);
  std::optional<geometry_msgs::Pose> get_current_end_effector_pose() const;

  std::optional<geometry_msgs::Pose>
  get_end_effector_pose(const JointArray& joints) const;

  // ROS variables
  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
  ros::Subscriber tool_frame_subscriber_;
  ros::ServiceServer closest_ik_service_;
  ros::ServiceServer user_ik_service;
  ros::ServiceServer arm_config_service;
  ros::ServiceServer arm_config_constraint_service;

  // Planning scene for MoveIt
  planning_scene_monitor::PlanningSceneMonitorPtr psm;

  // Tool frame ID
  std::string tool_frame;

  // Use Fanuc naming convention for arm configurations
  const std::vector<std::string> arm_config_names = { "NUT", "NDT", "NUB",
                                                      "NDB", "FUT", "FDT",
                                                      "FUB", "FDB" };

  // Initialize allowing all arm configurations
  uint8_t allowed_constraints = 0b11111111;

public:
  // OPW kinematics solver
  // OpwSolver ik_solver;
  std::unique_ptr<OpwSolver> ik_solver;
};

#endif  // MOVEJ_IK_SERVER_H
