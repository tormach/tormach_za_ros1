#ifndef TRPL_POSE_H
#define TRPL_POSE_H

#include <numeric>
#include <memory>
#include <string>
#include <vector>
#include <algorithm>

#include <movej_ik_server_msgs/MovejUserIKService.h>

#include <geometry_msgs/PoseStamped.h>

struct TrplPose
{
  geometry_msgs::Pose pose;

  bool force_solution_id = false;
  int solution_id = 0;
  bool force_rev_count = false;
  int rev_count = 0;
  std::optional<std::array<double, 6>> cached_joints;

  std::string frame_id;

  TrplPose() = default;

  TrplPose(geometry_msgs::Pose pose, int conf, int rev,
           std::array<double, 6> joints)
    : pose(pose), solution_id(conf), rev_count(rev), cached_joints(joints)
  {
  }
};

inline TrplPose request_to_trpl_pose(
    const movej_ik_server_msgs::MovejUserIKService::Request& req)
{
  TrplPose pose{};
  pose.pose = req.pose;
  pose.rev_count = req.rev_count;

  int bits_found = 0;
  int arm_config_candidate = -1;
  for (int i = 0; i < 8; ++i)
  {
    if (req.arm_config & (1 << i))
    {
      arm_config_candidate = i;
      bits_found++;
    }
  }
  if (bits_found != 1)
  {
    ROS_ERROR("Invalid arm_config: %d", req.arm_config);
    throw std::runtime_error("Invalid arm_config");
  }
  pose.solution_id = arm_config_candidate;

  if (req.cached_joints.size() == 6)
  {
    std::vector<double> cached_joints_vec = req.cached_joints;
    std::array<double, 6> cached_joints;
    std::copy_n(cached_joints_vec.begin(), 6, cached_joints.begin());
    pose.cached_joints = cached_joints;
  }

  return pose;
}

#endif  // MOVEJ_IK_SERVER_H
