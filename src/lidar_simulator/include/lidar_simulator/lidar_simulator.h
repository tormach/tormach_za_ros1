// include/lidar_simulator/lidar_simulator.h
#pragma once

#include <Eigen/Dense>
#include <Eigen/Geometry>
#include <vector>

namespace lidar_simulator
{
struct LidarSpec
{
  double field_of_view;
  int num_rays;
};

struct Plane
{
  Eigen::Vector3d normal;
  double width;
  double height;
  Eigen::Isometry3d pose;
};

class LidarSimulator
{
public:
  LidarSimulator(const LidarSpec& spec);

  void addPlane(const Plane& plane);
  void removePlane(const Plane& plane);
  std::vector<Eigen::Vector3d>
  detectPoints(const Eigen::Isometry3d& lidar_pose);
  std::vector<Eigen::Vector3d>
  detectPointsLocal(const Eigen::Isometry3d& lidar_pose);

private:
  LidarSpec spec_;
  std::vector<Plane> planes_;

  bool rayPlaneIntersection(const Eigen::Vector3d& ray_origin,
                            const Eigen::Vector3d& ray_direction,
                            const Plane& plane,
                            Eigen::Vector3d& intersection_point);
};

}  // namespace lidar_simulator
