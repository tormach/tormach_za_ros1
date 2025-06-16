//
// Created by alexander on 09/08/18.
//

#ifndef CARTESIAN_STATE_JOINTSTOPOSE_H
#define CARTESIAN_STATE_JOINTSTOPOSE_H

#include <mutex>
#include <ros/node_handle.h>
#include <sensor_msgs/JointState.h>
#include <std_msgs/String.h>
#include <moveit/robot_state/robot_state.h>
#include <moveit/robot_model_loader/robot_model_loader.h>
#include <cartesian_state_msgs/GetPose.h>
#include <cartesian_state_msgs/GetCurrentPose.h>
#include <cartesian_state_msgs/GetCurrentJointValues.h>
#include <tf/transform_listener.h>

namespace cartesian_state
{
struct joints_to_pose_paramters
{
  std::string joint_topic;
  std::string planning_frame_topic;
  std::string tool_frame_topic;
  std::string pose_topic;
  std::string world_pose_topic;
  std::string move_group_name;
  std::string base_link_name;
  std::string target_link_name;
  std::string joint_name_prefix;
  bool enable_service;
};

class JointsToPose
{
public:
  explicit JointsToPose();

private:
  joints_to_pose_paramters parameters_;
  std::shared_ptr<robot_state::RobotState> robot_state_;
  ros::Publisher pose_pub_;
  ros::Publisher world_pose_pub_;
  ros::Subscriber joints_sub_;
  ros::Subscriber planning_frame_sub_;
  ros::Subscriber tool_frame_sub_;
  ros::ServiceServer get_pose_srv_;
  ros::ServiceServer get_world_pose_srv_;
  ros::ServiceServer get_current_pose_srv_;
  ros::ServiceServer get_current_joint_values_srv_;
  robot_model_loader::RobotModelLoader robot_model_loader_;
  tf::TransformListener tf_listener_;

  std::string planning_frame_id_;
  std::string tool_frame_id_;
  sensor_msgs::JointState joint_state_;
  bool has_joint_state_;
  std::mutex update_mutex_;

  void readParameters(const ros::NodeHandle& n);

  geometry_msgs::Pose getRobotPose(const std::vector<double>&,
                                   const std::string& tool_frame,
                                   const std::string& base_frame);

  void jointsCB(const sensor_msgs::JointStateConstPtr& msg);

  void planningFrameCB(const std_msgs::StringConstPtr& msg);

  void toolFrameCB(const std_msgs::StringConstPtr& msg);

  void publishPoses();

  bool getPoseCB(cartesian_state_msgs::GetPoseRequest& request,
                 cartesian_state_msgs::GetPoseResponse& response);

  bool getCurrentPoseCB(cartesian_state_msgs::GetCurrentPoseRequest& request,
                        cartesian_state_msgs::GetCurrentPoseResponse& response);

  bool getCurrentJointValuesCB(
      cartesian_state_msgs::GetCurrentJointValuesRequest& request,
      cartesian_state_msgs::GetCurrentJointValuesResponse& response);

  void loadKinematicModel();

  void createInterface(ros::NodeHandle& n);
};
}  // namespace cartesian_state

#endif  // CARTESIAN_STATE_JOINTSTOPOSE_H
