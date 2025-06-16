#include "lidar_simulator/lidar_simulator.h"
#include <cmath>
#include <limits>
#include <iostream>
#include <algorithm>

namespace lidar_simulator
{
LidarSimulator::LidarSimulator(const LidarSpec& spec) : spec_(spec)
{
}

void LidarSimulator::addPlane(const Plane& plane)
{
  planes_.push_back(plane);
}

void LidarSimulator::removePlane(const Plane& plane)
{
  auto it =
      std::find_if(planes_.begin(), planes_.end(), [&plane](const Plane& p) {
        return p.pose.isApprox(plane.pose) && p.normal.isApprox(plane.normal) &&
               std::abs(p.width - plane.width) < 1e-6 &&
               std::abs(p.height - plane.height) < 1e-6;
      });

  if (it != planes_.end())
  {
    planes_.erase(it);
  }
}

std::vector<Eigen::Vector3d>
LidarSimulator::detectPoints(const Eigen::Isometry3d& lidar_pose)
{
  std::vector<Eigen::Vector3d> points;
  double angle_step = spec_.field_of_view / (spec_.num_rays - 1);
  double start_angle = -spec_.field_of_view / 2;  // Changed to negative

  for (int i = 0; i < spec_.num_rays; ++i)
  {
    double angle =
        (start_angle + i * angle_step) * M_PI / 180.0;  // Changed to addition
    Eigen::Vector3d ray_direction(std::cos(angle), std::sin(angle), 0);
    ray_direction = lidar_pose.rotation() * ray_direction;

    Eigen::Vector3d closest_point;
    double closest_distance = std::numeric_limits<double>::max();

    for (const auto& plane : planes_)
    {
      Eigen::Vector3d intersection_point;
      if (rayPlaneIntersection(lidar_pose.translation(), ray_direction, plane,
                               intersection_point))
      {
        double distance =
            (intersection_point - lidar_pose.translation()).norm();
        if (distance < closest_distance)
        {
          closest_distance = distance;
          closest_point = intersection_point;
        }
      }
    }

    if (closest_distance < std::numeric_limits<double>::max())
    {
      points.push_back(closest_point);
    }
  }

  return points;
}

std::vector<Eigen::Vector3d>
LidarSimulator::detectPointsLocal(const Eigen::Isometry3d& lidar_pose)
{
  // First, get the points in the world frame
  std::vector<Eigen::Vector3d> world_points = detectPoints(lidar_pose);

  // Transform the points to the LiDAR's local frame
  std::vector<Eigen::Vector3d> local_points;
  local_points.reserve(world_points.size());

  Eigen::Isometry3d lidar_pose_inverse = lidar_pose.inverse();

  for (const auto& world_point : world_points)
  {
    Eigen::Vector3d local_point = lidar_pose_inverse * world_point;
    local_points.push_back(local_point);
  }

  return local_points;
}

bool LidarSimulator::rayPlaneIntersection(const Eigen::Vector3d& ray_origin,
                                          const Eigen::Vector3d& ray_direction,
                                          const Plane& plane,
                                          Eigen::Vector3d& intersection_point)
{
  Eigen::Vector3d plane_normal = plane.pose.rotation() * plane.normal;
  Eigen::Vector3d plane_point = plane.pose.translation();

  double denominator = ray_direction.dot(plane_normal);

  if (std::abs(denominator) > 1e-6)
  {
    double t = (plane_point - ray_origin).dot(plane_normal) / denominator;

    if (t >= 0)
    {
      intersection_point = ray_origin + t * ray_direction;

      // Transform intersection point to plane's local coordinates
      Eigen::Vector3d local_point = plane.pose.inverse() * intersection_point;

      // Check if the intersection point is within the plane's boundaries
      if (std::abs(local_point.x()) <= plane.width / 2 &&
          std::abs(local_point.y()) <= plane.height / 2 &&
          std::abs(local_point.z()) < 1e-6)
      {
        return true;
      }
    }
  }
  return false;
}

}  // namespace lidar_simulator
