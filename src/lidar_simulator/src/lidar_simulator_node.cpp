// src/lidar_simulator_node.cpp
#include <ros/ros.h>
#include "lidar_simulator/lidar_simulator.h"
#include <iostream>

int main(int argc, char** argv)
{
  ros::init(argc, argv, "lidar_simulator_node");
  ros::NodeHandle nh;

  lidar_simulator::LidarSpec spec;
  spec.field_of_view = 100.0;
  spec.num_rays = 160;

  lidar_simulator::LidarSimulator simulator(spec);

  // Add some planes
  // lidar_simulator::Plane plane1;
  // plane1.normal = Eigen::Vector3d::UnitZ();
  // plane1.width = 4.0;
  // plane1.height = 3.0;
  // plane1.pose = Eigen::Isometry3d::Identity();
  // plane1.pose.translation() = Eigen::Vector3d(2.0, 0.0, -1.0);
  // simulator.addPlane(plane1);

  // lidar_simulator::Plane plane2;
  // plane2.normal = Eigen::Vector3d::UnitZ();
  // plane2.width = 2.0;
  // plane2.height = 2.0;
  // plane2.pose = Eigen::Isometry3d::Identity();
  // plane2.pose.translation() = Eigen::Vector3d(1.0, 1.0, -0.5);
  // simulator.addPlane(plane2);

  lidar_simulator::Plane plane3;
  plane3.normal = Eigen::Vector3d::UnitZ();
  plane3.width = 300.0;
  plane3.height = 300.0;
  plane3.pose = Eigen::Isometry3d::Identity();
  plane3.pose.translation() = Eigen::Vector3d(0.0, 0.0, -0.1);
  simulator.addPlane(plane3);

  // std::cout << "Plane 1: " << std::endl << plane1.pose.matrix() << std::endl;
  // std::cout << "Plane 2: " << std::endl << plane2.pose.matrix() << std::endl;
  std::cout << "Plane 3: " << std::endl << plane3.pose.matrix() << std::endl;

  // Create a rotation matrix to align LiDAR x-axis with positive world z-axis
  Eigen::Matrix3d rotation;
  rotation << 0, 0, 1, 0, 1, 0, -1, 0, 0;

  // Simulate LiDAR at different poses
  std::vector<Eigen::Isometry3d> lidar_poses;

  // LiDAR at origin
  // Eigen::Isometry3d pose1 = Eigen::Isometry3d::Identity();
  // pose1.linear() = rotation;
  // lidar_poses.push_back(pose1);

  // LiDAR translated
  // Eigen::Isometry3d pose2 = Eigen::Isometry3d::Identity();
  // pose2.linear() = rotation;
  // pose2.translation() = Eigen::Vector3d(0.5, 0.5, 1.0);
  // lidar_poses.push_back(pose2);

  // LiDAR rotated around world z-axis, x-axis pointing up
  Eigen::Isometry3d pose3 = Eigen::Isometry3d::Identity();
  pose3.linear() =
      Eigen::AngleAxisd(M_PI / 4, Eigen::Vector3d::UnitZ()) * rotation;
  pose3.translation() = Eigen::Vector3d(0.0, 0.0, 1.0);
  lidar_poses.push_back(pose3);

  for (const auto& lidar_pose : lidar_poses)
  {
    std::vector<Eigen::Vector3d> points = simulator.detectPoints(lidar_pose);

    std::cout << "LiDAR pose: " << std::endl
              << lidar_pose.matrix() << std::endl;
    std::cout << "Detected points: " << points.size() << std::endl;
    for (const auto& point : points)
    {
      std::cout << point.transpose() << std::endl;
    }
    std::cout << "----------------------" << std::endl;
  }

  for (const auto& lidar_pose : lidar_poses)
  {
    std::vector<Eigen::Vector3d> local_points =
        simulator.detectPointsLocal(lidar_pose);

    std::cout << "LiDAR pose for Local Points: " << std::endl
              << lidar_pose.matrix() << std::endl;
    std::cout << "Detected Local points: " << local_points.size() << std::endl;

    for (const auto& point : local_points)
    {
      std::cout << point.transpose() << std::endl;
    }
    std::cout << "----------------------" << std::endl;
  }

  return 0;
}
