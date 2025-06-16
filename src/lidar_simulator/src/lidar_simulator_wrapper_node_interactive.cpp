#include <ros/ros.h>
#include <geometry_msgs/PoseStamped.h>
#include <sensor_msgs/PointCloud.h>
#include <tf2_eigen/tf2_eigen.h>
#include "lidar_simulator/lidar_simulator.h"
#include <geometry_msgs/Pose.h>
#include <lidar_simulator_msgs/AddLidarObject.h>
#include <lidar_simulator_msgs/RemoveLidarObject.h>
#include <lidar_simulator_msgs/ReportPoses.h>
#include <std_srvs/Empty.h>

class LidarSimulatorWrapperInteractive
{
public:
  LidarSimulatorWrapperInteractive() : nh_("~")
  {
    // Initialize LidarSimulator
    lidar_simulator::LidarSpec spec;
    spec.field_of_view = 100.0;
    spec.num_rays = 160;
    simulator_ = std::make_unique<lidar_simulator::LidarSimulator>(spec);

    // Set up subscriber and publisher
    pose_sub_ =
        nh_.subscribe("/pose_states_throttle", 1,
                      &LidarSimulatorWrapperInteractive::poseCallback, this);
    pointcloud_pub_ = nh_.advertise<sensor_msgs::PointCloud>("/point_cloud", 1);

    // Set up services
    add_object_service_ = nh_.advertiseService(
        "add_lidar_object",
        &LidarSimulatorWrapperInteractive::addObjectCallback, this);
    remove_object_service_ = nh_.advertiseService(
        "remove_lidar_object",
        &LidarSimulatorWrapperInteractive::removeObjectCallback, this);
    remove_all_objects_service_ = nh_.advertiseService(
        "remove_all_lidar_objects",
        &LidarSimulatorWrapperInteractive::removeAllObjectsCallback, this);
    report_poses_service_ = nh_.advertiseService(
        "report_poses", &LidarSimulatorWrapperInteractive::reportPosesCallback,
        this);

    // Initialize bias angles
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

  bool addObjectCallback(lidar_simulator_msgs::AddLidarObject::Request& req,
                         lidar_simulator_msgs::AddLidarObject::Response& res)
  {
    lidar_simulator::Plane new_plane;
    new_plane.normal = Eigen::Vector3d::UnitZ();
    new_plane.width = req.size_x;
    new_plane.height = req.size_y;

    Eigen::Isometry3d plane_pose;
    tf2::fromMsg(req.pose, plane_pose);
    new_plane.pose = plane_pose;

    simulator_->addPlane(new_plane);
    planes_.push_back(new_plane);

    res.success = true;
    res.message = "Object added successfully";
    return true;
  }

  bool
  removeObjectCallback(lidar_simulator_msgs::RemoveLidarObject::Request& req,
                       lidar_simulator_msgs::RemoveLidarObject::Response& res)
  {
    if (planes_.empty())
    {
      res.success = false;
      res.message = "No objects to remove";
      return true;
    }

    Eigen::Vector3d target_position;
    tf2::fromMsg(req.pose.position, target_position);

    double min_distance = std::numeric_limits<double>::max();
    size_t closest_index = 0;

    for (size_t i = 0; i < planes_.size(); ++i)
    {
      double distance =
          (planes_[i].pose.translation() - target_position).norm();
      if (distance < min_distance)
      {
        min_distance = distance;
        closest_index = i;
      }
    }

    // Remove the plane from the simulator
    simulator_->removePlane(planes_[closest_index]);

    // Remove the plane from our vector
    planes_.erase(planes_.begin() + closest_index);

    res.success = true;
    res.message = "Closest object removed successfully";
    return true;
  }

  bool removeAllObjectsCallback(std_srvs::Empty::Request& req,
                                std_srvs::Empty::Response& res)
  {
    // Remove all planes from the simulator
    for (const auto& plane : planes_)
    {
      simulator_->removePlane(plane);
    }

    // Clear the vector of planes
    planes_.clear();

    ROS_INFO("All lidar objects have been removed");
    return true;
  }

  bool reportPosesCallback(lidar_simulator_msgs::ReportPoses::Request& req,
                           lidar_simulator_msgs::ReportPoses::Response& res)
  {
    for (const auto& plane : planes_)
    {
      geometry_msgs::Pose pose;
      tf2::convert(plane.pose, pose);
      res.poses.push_back(pose);
    }
    return true;
  }

  ros::NodeHandle nh_;
  ros::Subscriber pose_sub_;
  ros::Publisher pointcloud_pub_;
  ros::ServiceServer add_object_service_;
  ros::ServiceServer remove_object_service_;
  ros::ServiceServer remove_all_objects_service_;
  ros::ServiceServer report_poses_service_;
  std::unique_ptr<lidar_simulator::LidarSimulator> simulator_;
  std::vector<lidar_simulator::Plane> planes_;

  // Bias angles
  double bias_x_, bias_y_, bias_z_;
};

int main(int argc, char** argv)
{
  // ros::init(argc, argv, "lidar_simulator_wrapper_interactive");
  ros::init(argc, argv, "lidar_simulator_wrapper");
  LidarSimulatorWrapperInteractive wrapper;
  ros::spin();
  return 0;
}
