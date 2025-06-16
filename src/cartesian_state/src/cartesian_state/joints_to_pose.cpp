//
// Created by alexander on 09/08/18.
//

#include "cartesian_state/joints_to_pose.h"
#include <ros/ros.h>
#include <rosparam_shortcuts/rosparam_shortcuts.h>
#include <moveit/robot_model_loader/robot_model_loader.h>
#include <moveit/robot_state/robot_state.h>
#include <tf_conversions/tf_eigen.h>

static const char* const NODE_NAME = "joints_to_pose";

// MAIN
int main(int argc, char** argv)
{
  ros::init(argc, argv, NODE_NAME);

  cartesian_state::JointsToPose joints_to_pose;

  return 0;
}

namespace cartesian_state
{
JointsToPose::JointsToPose() : has_joint_state_(false)
{
  ros::NodeHandle n;

  readParameters(n);
  createInterface(n);
  loadKinematicModel();

  ros::spin();
}

void JointsToPose::readParameters(const ros::NodeHandle& n)
{
  std::size_t error = 0;

  std::string parameter_ns;
  ros::param::param("~parameter_ns", parameter_ns, std::string(NODE_NAME));

  ros::NodeHandle rpnh(n, parameter_ns);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "joint_topic",
                                    parameters_.joint_topic);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "planning_frame_topic",
                                    parameters_.planning_frame_topic);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "tool_frame_topic",
                                    parameters_.tool_frame_topic);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "pose_topic",
                                    parameters_.pose_topic);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "world_pose_topic",
                                    parameters_.world_pose_topic);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "move_group_name",
                                    parameters_.move_group_name);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "base_link_name",
                                    parameters_.base_link_name);
  error += !rosparam_shortcuts::get(parameter_ns, rpnh, "target_link_name",
                                    parameters_.target_link_name);
  if (!rosparam_shortcuts::get(parameter_ns, rpnh, "joint_name_prefix",
                               parameters_.joint_name_prefix))
  {
    parameters_.joint_name_prefix = "joint_";
  }
  if (!rosparam_shortcuts::get(parameter_ns, rpnh, "enable_service",
                               parameters_.enable_service))
  {
    parameters_.enable_service = true;
  }

  planning_frame_id_ = parameters_.base_link_name;
  tool_frame_id_ = parameters_.target_link_name;

  if (error)
  {
    ROS_FATAL_STREAM("Parameters missing, shutting down");
  }
  rosparam_shortcuts::shutdownIfError(parameter_ns, error);
}

void JointsToPose::loadKinematicModel()
{
  robot_model_loader_ = robot_model_loader::RobotModelLoader("robot_"
                                                             "description");
  robot_state_ =
      std::make_shared<robot_state::RobotState>(robot_model_loader_.getModel());
}

void JointsToPose::createInterface(ros::NodeHandle& n)
{
  joints_sub_ =
      n.subscribe(parameters_.joint_topic, 1, &JointsToPose::jointsCB, this);
  planning_frame_sub_ = n.subscribe(parameters_.planning_frame_topic, 1,
                                    &JointsToPose::planningFrameCB, this);
  tool_frame_sub_ = n.subscribe(parameters_.tool_frame_topic, 1,
                                &JointsToPose::toolFrameCB, this);
  pose_pub_ =
      n.advertise<geometry_msgs::PoseStamped>(parameters_.pose_topic, 1);
  world_pose_pub_ =
      n.advertise<geometry_msgs::PoseStamped>(parameters_.world_pose_topic, 1);

  if (parameters_.enable_service)
  {
    get_pose_srv_ = n.advertiseService("joints_to_pose/get_pose",
                                       &JointsToPose::getPoseCB, this);
    get_current_pose_srv_ =
        n.advertiseService("joints_to_pose/get_current_pose",
                           &JointsToPose::getCurrentPoseCB, this);
    get_current_joint_values_srv_ =
        n.advertiseService("joints_to_pose/get_current_joint_values",
                           &JointsToPose::getCurrentJointValuesCB, this);
  }
}

void JointsToPose::jointsCB(const sensor_msgs::JointStateConstPtr& msg)
{
  bool found = false;
  for (const auto& name : msg->name)
  {
    if (name.rfind(parameters_.joint_name_prefix, 0) == 0)
    {
      found = true;
      break;
    }
  }
  if (!found)
  {
    return;
  }
  {
    std::lock_guard<std::mutex> lock(update_mutex_);
    joint_state_.header = msg->header;
    joint_state_.name.clear();
    joint_state_.position.clear();
    for (std::size_t i = 0; i < msg->name.size(); ++i)
    {
      if (msg->name.at(i).rfind(parameters_.joint_name_prefix, 0) != 0)
      {
        continue;
      }
      joint_state_.name.push_back(msg->name.at(i));
      joint_state_.position.push_back(msg->position.at(i));
    }
    has_joint_state_ = true;
  }
  publishPoses();
}

void JointsToPose::planningFrameCB(const std_msgs::StringConstPtr& msg)
{
  {
    std::lock_guard<std::mutex> lock(update_mutex_);
    planning_frame_id_ = msg->data;
    if (!has_joint_state_)
    {
      return;
    }
  }
  publishPoses();
}

void JointsToPose::toolFrameCB(const std_msgs::StringConstPtr& msg)
{
  {
    std::lock_guard<std::mutex> lock(update_mutex_);
    tool_frame_id_ = msg->data;
    if (!has_joint_state_)
    {
      return;
    }
  }
  publishPoses();
}

void JointsToPose::publishPoses()
{
  const auto pose =
      getRobotPose(joint_state_.position, tool_frame_id_, planning_frame_id_);
  const auto world_pose =
      getRobotPose(joint_state_.position, tool_frame_id_, "");

  geometry_msgs::PoseStamped pose_stamped;
  pose_stamped.header.stamp = joint_state_.header.stamp;
  pose_stamped.pose = pose;
  pose_pub_.publish(pose_stamped);

  geometry_msgs::PoseStamped world_pose_stamped;
  world_pose_stamped.header.stamp = joint_state_.header.stamp;
  world_pose_stamped.pose = world_pose;
  world_pose_pub_.publish(world_pose_stamped);
}

bool JointsToPose::getPoseCB(cartesian_state_msgs::GetPoseRequest& request,
                             cartesian_state_msgs::GetPoseResponse& response)
{
  {
    std::lock_guard<std::mutex> lock(update_mutex_);
    if (!has_joint_state_)
    {
      return false;
    }
  }
  const auto pose = getRobotPose(request.joint_state.position,
                                 request.tool_frame_id, request.base_frame_id);
  response.pose = pose;
  response.success = true;
  return true;
}

geometry_msgs::Pose JointsToPose::getRobotPose(
    const std::vector<double>& position, const std::string& tool_frame,
    const std::string& base_frame)
{
  robot_state_->setJointGroupPositions(parameters_.move_group_name, position);
  const Eigen::Affine3d& link_pose =
      robot_state_->getGlobalLinkTransform(parameters_.target_link_name);

  tf::Transform pose_transform;
  tf::transformEigenToTF(link_pose, pose_transform);

  if (base_frame != parameters_.base_link_name && !base_frame.empty())
  {
    try
    {
      tf::StampedTransform offset_transform;
      tf_listener_.lookupTransform(base_frame, parameters_.base_link_name,
                                   ros::Time(0), offset_transform);
      pose_transform = offset_transform * pose_transform;
    }
    catch (const tf2::LookupException& e)
    {
      ROS_WARN_STREAM_THROTTLE(5, e.what());
    }
  }

  if (tool_frame != parameters_.target_link_name && !tool_frame.empty())
  {
    try
    {
      tf::StampedTransform offset_transform;
      tf_listener_.lookupTransform(parameters_.target_link_name, tool_frame,
                                   ros::Time(0), offset_transform);
      pose_transform = pose_transform * offset_transform;
    }
    catch (const tf2::LookupException& e)
    {
      ROS_WARN_STREAM_THROTTLE(5, e.what());
    }
  }

  tf::Vector3 cartesian_position = pose_transform.getOrigin();
  tf::Quaternion link_orientation = pose_transform.getRotation();
  geometry_msgs::Pose pose;
  pose.position.x = cartesian_position.getX();
  pose.position.y = cartesian_position.getY();
  pose.position.z = cartesian_position.getZ();
  pose.orientation.w = link_orientation.getW();
  pose.orientation.x = link_orientation.getX();
  pose.orientation.y = link_orientation.getY();
  pose.orientation.z = link_orientation.getZ();

  return pose;
}

bool JointsToPose::getCurrentPoseCB(
    cartesian_state_msgs::GetCurrentPoseRequest& request,
    cartesian_state_msgs::GetCurrentPoseResponse& response)
{
  std::lock_guard<std::mutex> lock(update_mutex_);
  response.pose.pose = getRobotPose(
      joint_state_.position, request.tool_frame_id, request.base_frame_id);
  response.pose.header.stamp = joint_state_.header.stamp;
  response.pose.header.frame_id = planning_frame_id_;
  return true;
}

bool JointsToPose::getCurrentJointValuesCB(
    cartesian_state_msgs::GetCurrentJointValuesRequest& request,
    cartesian_state_msgs::GetCurrentJointValuesResponse& response)
{
  std::lock_guard<std::mutex> lock(update_mutex_);
  response.joint_state = joint_state_;
  return true;
}

}  // namespace cartesian_state
