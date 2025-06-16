#include <ros/ros.h>
#include <geometry_msgs/PoseStamped.h>
#include <sensor_msgs/PointCloud.h>
#include <tf2_eigen/tf2_eigen.h>
#include "lidar_simulator/lidar_simulator.h"

class LidarSimulatorWrapper
{
public:
  LidarSimulatorWrapper() : nh_("~")
  {
    // Initialize LidarSimulator
    lidar_simulator::LidarSpec spec;
    spec.field_of_view = 100.0;
    spec.num_rays = 160;
    simulator_ = std::make_unique<lidar_simulator::LidarSimulator>(spec);

    // Create table plane
    lidar_simulator::Plane table_plane;
    table_plane.normal = Eigen::Vector3d::UnitZ();
    table_plane.width = 1.45;
    table_plane.height = 1.45;
    table_plane.pose = Eigen::Isometry3d::Identity();
    table_plane.pose.translation() = Eigen::Vector3d(0.0, 0.0, 0.0);
    simulator_->addPlane(table_plane);

    // Add a plane
    lidar_simulator::Plane plane3;
    plane3.normal = Eigen::Vector3d::UnitZ();
    plane3.width = 0.119;
    plane3.height = 0.1018;
    plane3.pose = Eigen::Isometry3d::Identity() *
                  Eigen::AngleAxisd(M_PI / 24, Eigen::Vector3d::UnitZ());
    plane3.pose.translation() = Eigen::Vector3d(0.6, 0.1, 0.0381);
    simulator_->addPlane(plane3);

    lidar_simulator::Plane plane4;
    plane4.normal = Eigen::Vector3d::UnitZ();
    plane4.width = 0.119;
    plane4.height = 0.1018;
    plane4.pose = Eigen::Isometry3d::Identity() *
                  Eigen::AngleAxisd(0 / 24, Eigen::Vector3d::UnitZ());
    plane4.pose.translation() = Eigen::Vector3d(0.4, 0.3, 0.0381);
    simulator_->addPlane(plane4);

    // Set up subscriber and publisher
    pose_sub_ = nh_.subscribe("/pose_states_throttle", 1,
                              &LidarSimulatorWrapper::poseCallback, this);
    pointcloud_pub_ = nh_.advertise<sensor_msgs::PointCloud>("/point_cloud", 1);

    // Initialize bias angles (you can adjust these values as needed)
    bias_x_ = M_PI / 180.0;  // 1 degree error around x-axis
    bias_y_ = M_PI / 360.0;  // 0.5 degree error around y-axis
    bias_z_ = M_PI / 90.0;   // 2 degrees error around z-axis
                             //
    // reset bias to zero possibly comment this
    bias_x_ = 0.0;
    bias_y_ = 0.0;
    bias_z_ = 0.0;
  }

private:
  void poseCallback(const geometry_msgs::PoseStamped::ConstPtr& msg)
  {
    // Convert PoseStamped to Eigen::Isometry3d
    Eigen::Isometry3d lidar_pose;
    tf2::fromMsg(msg->pose, lidar_pose);

    // Create the bias frame
    Eigen::Isometry3d bias_frame = Eigen::Isometry3d::Identity();
    bias_frame = bias_frame *
                 Eigen::AngleAxisd(bias_z_, Eigen::Vector3d::UnitZ()) *
                 Eigen::AngleAxisd(bias_x_, Eigen::Vector3d::UnitX()) *
                 Eigen::AngleAxisd(bias_y_, Eigen::Vector3d::UnitY());

    // Apply the bias frame to the lidar_pose
    lidar_pose = lidar_pose * bias_frame;

    // Create the 3x3 rotation matrix
    Eigen::Matrix3f R;
    R << 0, 0, 1, -1, 0, 0, 0, -1, 0;

    // Create a 4x4 identity matrix
    Eigen::Matrix4f T = Eigen::Matrix4f::Identity();
    // Set the top-left 3x3 block to our rotation matrix
    T.block<3, 3>(0, 0) = R;

    // Convert T to Eigen::Isometry3d
    Eigen::Isometry3d T_isometry;
    T_isometry.matrix() = T.cast<double>();

    // Postmultiply lidar_pose by the inverse of T
    lidar_pose = lidar_pose * T_isometry.inverse();

    // Generate LiDAR data
    std::vector<Eigen::Vector3d> local_points =
        simulator_->detectPointsLocal(lidar_pose);

    // Create and publish PointCloud message
    sensor_msgs::PointCloud cloud_msg;
    cloud_msg.header = msg->header;
    cloud_msg.points.reserve(local_points.size());
    for (const auto& point : local_points)
    {
      geometry_msgs::Point32 ros_point;
      ros_point.x = point.x();
      ros_point.y = point.y();
      ros_point.z = point.z();
      cloud_msg.points.push_back(ros_point);
    }
    pointcloud_pub_.publish(cloud_msg);
  }

  ros::NodeHandle nh_;
  ros::Subscriber pose_sub_;
  ros::Publisher pointcloud_pub_;
  std::unique_ptr<lidar_simulator::LidarSimulator> simulator_;

  // Bias angles
  double bias_x_, bias_y_, bias_z_;
};

int main(int argc, char** argv)
{
  ros::init(argc, argv, "lidar_simulator_wrapper");
  LidarSimulatorWrapper wrapper;
  ros::spin();
  return 0;
}
