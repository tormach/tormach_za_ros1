// src/lidar_simulator_simple_scan.cpp
#include <ros/ros.h>
#include "lidar_simulator/lidar_simulator.h"
#include <iostream>
#include <vector>
#include <fstream>
#include <cmath>

Eigen::Isometry3d createBiasFrame(double bias_x, double bias_y, double bias_z)
{
  Eigen::Isometry3d bias_frame = Eigen::Isometry3d::Identity();
  bias_frame = bias_frame *
               Eigen::AngleAxisd(bias_z, Eigen::Vector3d::UnitZ()) *
               Eigen::AngleAxisd(bias_x, Eigen::Vector3d::UnitX()) *
               Eigen::AngleAxisd(bias_y, Eigen::Vector3d::UnitY());
  return bias_frame;
}

int main(int argc, char** argv)
{
  ros::init(argc, argv, "lidar_simulator_simple_scan");
  ros::NodeHandle nh;

  lidar_simulator::LidarSpec spec;
  spec.field_of_view = 100.0;
  spec.num_rays = 160;
  lidar_simulator::LidarSimulator simulator(spec);

  // Create table plane
  lidar_simulator::Plane table_plane;
  table_plane.normal = Eigen::Vector3d::UnitZ();
  table_plane.width = 1.45;
  table_plane.height = 1.45;
  table_plane.pose = Eigen::Isometry3d::Identity();
  table_plane.pose.translation() = Eigen::Vector3d(0.0, 0.0, 0.0);
  simulator.addPlane(table_plane);

  // Add a plane
  lidar_simulator::Plane plane3;
  plane3.normal = Eigen::Vector3d::UnitZ();
  plane3.width = 0.119;
  plane3.height = 0.1018;
  // plane3.pose = Eigen::Isometry3d::Identity() * Eigen::AngleAxisd(M_PI / 24,
  // Eigen::Vector3d::UnitZ());
  plane3.pose = Eigen::Isometry3d::Identity();
  plane3.pose.translation() = Eigen::Vector3d(0.6, 0.0, 0.0381);
  simulator.addPlane(plane3);

  std::cout << "Plane 3: " << std::endl << plane3.pose.matrix() << std::endl;

  // Define bias angles (you can adjust these values as needed)
  double bias_x = M_PI / 60.0;
  double bias_y = M_PI / 60.0;
  double bias_z = M_PI / 60.0;  // 3 degrees error around z-axis

  // Create the bias frame
  Eigen::Isometry3d bias_frame = createBiasFrame(bias_x, bias_y, bias_z);

  // Create the T matrix (similar to the one in poseCallback)
  Eigen::Matrix4f T = Eigen::Matrix4f::Identity();
  T.block<3, 3>(0, 0) << 0, -1, 0, -1, 0, 0, 0, 0, -1;

  // Convert T to Eigen::Isometry3d
  Eigen::Isometry3d T_isometry;
  T_isometry.matrix() = T.cast<double>();

  // Optionally rotate the sensor by 180 deg
  Eigen::Isometry3d rotation_z =
      Eigen::Isometry3d(Eigen::AngleAxisd(M_PI, Eigen::Vector3d::UnitZ()));
  T_isometry = T_isometry * rotation_z;

  Eigen::Matrix3d R;
  R << 0, 1, 0, 0, 0, 1, 1, 0, 0;

  // Create homogeneous transformation matrix with R as rotation component and
  // no translation
  Eigen::Isometry3d R_isometry = Eigen::Isometry3d::Identity();
  R_isometry.linear() = R;

  // Define the start and end points of the linear path
  Eigen::Vector3d start_point(0.5, 0, 0.1031);
  Eigen::Vector3d end_point(0.7, 0, 0.1031);

  // Calculate the number of steps (0.5mm increments)
  double step_size = 0.0005;  // 0.5mm
  int num_steps = std::ceil((end_point - start_point).norm() / step_size);

  // Vector to store all points from all scans
  std::vector<std::vector<Eigen::Vector3d>> all_scans;

  for (int i = 0; i <= num_steps; ++i)
  {
    double t = static_cast<double>(i) / num_steps;
    Eigen::Vector3d current_position =
        start_point + t * (end_point - start_point);

    // Create the lidar pose as an Isometry3d
    Eigen::Isometry3d lidar_pose = Eigen::Isometry3d::Identity();
    lidar_pose.translation() = current_position;

    lidar_pose = lidar_pose * T_isometry * bias_frame * R_isometry;

    // std::vector<Eigen::Vector3d> points = simulator.detectPoints(lidar_pose);
    std::vector<Eigen::Vector3d> local_points =
        simulator.detectPointsLocal(lidar_pose);

    Eigen::Isometry3d lidar_pose_known_to_system =
        Eigen::Isometry3d::Identity();
    lidar_pose_known_to_system.translation() = current_position;
    lidar_pose_known_to_system =
        lidar_pose_known_to_system * T_isometry * R_isometry;

    // TODO: implement the transformation of the `local_points` that are
    // expressed wrt `lidar_pose_known_to_system` into the world frame, such
    // that `points` are produced
    // hint: `lidar_pose_known_to_system` is expressed with respect to the
    // world frame
    std::vector<Eigen::Vector3d> points;
    for (const auto& local_point : local_points)
    {
      Eigen::Vector3d world_point = lidar_pose_known_to_system * local_point;
      points.push_back(world_point);
    }

    all_scans.push_back(points);

    std::cout << "LiDAR pose at step " << i << ":" << std::endl
              << lidar_pose.matrix() << std::endl;
    std::cout << "Detected points: " << points.size() << std::endl;
    std::cout << "----------------------" << std::endl;
  }

  // Flatten the vector of vectors and save to CSV
  std::ofstream csv_file("synthetic_lidar_points_pass_2.csv");
  // std::ofstream csv_file("synthetic_lidar_points_pass_1.csv");
  if (!csv_file.is_open())
  {
    std::cerr << "Failed to open file for writing." << std::endl;
    return 1;
  }

  // Write CSV header
  csv_file << "x,y,z" << std::endl;

  // Write all points to the CSV file
  for (const auto& scan : all_scans)
  {
    for (const auto& point : scan)
    {
      csv_file << point.x() << "," << point.y() << "," << point.z()
               << std::endl;
    }
  }

  csv_file.close();
  std::cout << "CSV file 'synthetic_lidar_points.csv' has been created."
            << std::endl;

  return 0;
}
