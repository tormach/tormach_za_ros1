#include "workpiece_visualizer/BoxVisualizer.h"
#include <fstream>
#include <sstream>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#include <limits>
#include <cmath>

BoxVisualizer::BoxVisualizer(ros::NodeHandle& nh,
                             const std::string& custom_namespace)
  : nh_(nh)
  , marker_pub_(nh.advertise<visualization_msgs::MarkerArray>("visualization_"
                                                              "marker_array",
                                                              10))
  , custom_namespace_(custom_namespace)
{
  nh_.param<double>("workpiece_x", workpiece_x_, 0.120);
  nh_.param<double>("workpiece_y", workpiece_y_, 0.1018);
  nh_.param<double>("workpiece_z", workpiece_z_, 0.0381);
  ROS_INFO_STREAM("Workpiece dimensions: " << workpiece_x_ << " x "
                                           << workpiece_y_ << " x "
                                           << workpiece_z_ << " m");
  boxes_.clear();
  ROS_INFO_STREAM(
      "BoxVisualizer initialized with custom namespace: " << custom_namespace_);
}

void BoxVisualizer::removeAllObjects()
{
  ROS_INFO_STREAM("Removing all objects in namespace: " << custom_namespace_);
  visualization_msgs::MarkerArray marker_array;

  // Create a marker to delete all markers in the custom namespace
  visualization_msgs::Marker delete_marker;
  delete_marker.header.frame_id = "world";
  delete_marker.header.stamp = ros::Time::now();
  delete_marker.ns = custom_namespace_;
  delete_marker.action = visualization_msgs::Marker::DELETEALL;
  marker_array.markers.push_back(delete_marker);

  // Publish the delete marker
  marker_pub_.publish(marker_array);

  // Clear the local storage of boxes
  boxes_.clear();
  ROS_INFO_STREAM("All objects removed from namespace: " << custom_namespace_);
}

void BoxVisualizer::loadObjectsFromCSV(const std::string& filename)
{
  // First remove all existing objects
  removeAllObjects();

  ROS_INFO_STREAM("Loading objects from CSV file: " << filename);
  std::ifstream file(filename);
  std::string line;
  std::getline(file, line);  // Skip header line
  int id = 0;
  while (std::getline(file, line))
  {
    std::istringstream iss(line);
    std::string token;
    std::vector<double> values;
    while (std::getline(iss, token, ','))
    {
      values.push_back(std::stod(token));
    }
    if (values.size() == 7)
    {
      Box box;
      box.id = id++;
      box.pose.position.x = values[0];
      box.pose.position.y = values[1];
      box.pose.position.z = values[2] - (workpiece_z_ * 0.5);
      box.pose.orientation.x = values[3];
      box.pose.orientation.y = values[4];
      box.pose.orientation.z = values[5];
      box.pose.orientation.w = values[6];
      box.color = GRAY;
      // int level_now = values[2] / workpiece_z_;
      int level_now = std::ceil(values[2] / workpiece_z_ - 0.5);
      box.level = level_now;
      box.visible = true;
      box.alpha = 1.0;
      boxes_.push_back(box);
      ROS_INFO_STREAM("Loaded box " << box.id << " at position ("
                                    << box.pose.position.x << ", "
                                    << box.pose.position.y << ", "
                                    << box.pose.position.z << ")");
    }
  }
  ROS_INFO_STREAM("Loaded " << boxes_.size() << " boxes from CSV");
  publishMarkers();
}

void BoxVisualizer::moveObjectDown(int id)
{
  ROS_INFO_STREAM("Moving object " << id << " down");
  for (auto& box : boxes_)
  {
    if (box.id == id)
    {
      box.level--;
      if (box.level < 1)
      {
        box.visible = false;
        box.alpha = 1.0;
        ROS_INFO_STREAM("Object " << id
                                  << " is now invisible and fully transparent "
                                     "(below level 1)");
        box.pose.position.z = -100.0;
      }
      else
      {
        box.pose.position.z = workpiece_z_ * box.level - (workpiece_z_ * 0.5);
        ROS_INFO_STREAM("Object " << id << " moved to level " << box.level
                                  << " (z = " << box.pose.position.z << ")");
      }
      break;
    }
  }
  publishMarkers();
}

void BoxVisualizer::setWorkpieceColor(int id, const std::string& color)
{
  ROS_INFO_STREAM("Setting color of object " << id << " to " << color);
  for (auto& box : boxes_)
  {
    if (box.id == id)
    {
      box.color = stringToColor(color);
      break;
    }
  }
  publishMarkers();
}

void BoxVisualizer::updateWorkpiecePose(int id,
                                        const geometry_msgs::Pose& new_pose)
{
  ROS_INFO_STREAM("Updating pose of object " << id);
  for (auto& box : boxes_)
  {
    if (box.id == id)
    {
      box.pose = new_pose;
      box.pose.position.z -= (workpiece_z_ * 0.5);
      ROS_INFO_STREAM("Updated pose of object "
                      << id << " to (" << new_pose.position.x << ", "
                      << new_pose.position.y << ", " << new_pose.position.z
                      << ")");
      break;
    }
  }
  publishMarkers();
}

void BoxVisualizer::setWorkpieceDimensions(double x, double y, double z)
{
  workpiece_x_ = x;
  workpiece_y_ = y;
  workpiece_z_ = z;
  ROS_INFO_STREAM("Updated workpiece dimensions to: " << x << " x " << y
                                                      << " x " << z << " m");

  // Update z-positions of all boxes based on new workpiece height
  for (auto& box : boxes_)
  {
    if (box.visible)
    {
      box.pose.position.z = workpiece_z_ * box.level - (workpiece_z_ * 0.5);
    }
  }

  publishMarkers();
}

void BoxVisualizer::publishMarkers()
{
  ROS_INFO("Publishing markers");
  visualization_msgs::MarkerArray marker_array;
  int visible_count = 0;
  for (const auto& box : boxes_)
  {
    visualization_msgs::Marker marker;
    marker.header.frame_id = "world";
    marker.header.stamp = ros::Time::now();
    marker.ns = custom_namespace_;
    marker.id = box.id;
    marker.type = visualization_msgs::Marker::CUBE;
    marker.action = visualization_msgs::Marker::ADD;
    marker.pose = box.pose;
    marker.scale.x = workpiece_x_;
    marker.scale.y = workpiece_y_;
    marker.scale.z = workpiece_z_;

    switch (box.color)
    {
      case YELLOW:
        marker.color.r = 1.0;
        marker.color.g = 1.0;
        marker.color.b = 0.0;
        break;
      case RED:
        marker.color.r = 1.0;
        marker.color.g = 0.0;
        marker.color.b = 0.0;
        break;
      case GRAY:
      default:
        marker.color.r = 0.5;
        marker.color.g = 0.5;
        marker.color.b = 0.5;
        break;
    }

    marker.color.a = box.alpha;
    marker.lifetime = ros::Duration();
    marker_array.markers.push_back(marker);
    visible_count++;
  }
  marker_pub_.publish(marker_array);
  ROS_INFO_STREAM("Published " << visible_count
                               << " visible markers under namespace '"
                               << custom_namespace_ << "'");
}

BoxVisualizer::Color BoxVisualizer::stringToColor(const std::string& color)
{
  if (color == "YELLOW")
    return YELLOW;
  if (color == "RED")
    return RED;
  return GRAY;
}

int BoxVisualizer::findClosestObject(const geometry_msgs::Pose& pose) const
{
  if (boxes_.empty())
  {
    return -1;  // Return -1 if no objects exist
  }

  double min_distance = std::numeric_limits<double>::max();
  int closest_id = -1;

  for (const auto& box : boxes_)
  {
    if (!box.visible)
    {
      continue;  // Skip invisible boxes
    }

    // Calculate Euclidean distance between poses
    double dx = box.pose.position.x - pose.position.x;
    double dy = box.pose.position.y - pose.position.y;
    double dz = box.pose.position.z - pose.position.z;
    double distance = std::sqrt(dx * dx + dy * dy + dz * dz);

    if (distance < min_distance)
    {
      min_distance = distance;
      closest_id = box.id;
    }
  }

  return closest_id;
}

void BoxVisualizer::moveObjectDownByPose(const geometry_msgs::Pose& pose)
{
  int closest_id = findClosestObject(pose);
  if (closest_id >= 0)
  {
    moveObjectDown(closest_id);
    ROS_INFO_STREAM("Moving closest object (ID: " << closest_id << ") down");
  }
  else
  {
    ROS_WARN("No visible objects found to move down");
  }
}
