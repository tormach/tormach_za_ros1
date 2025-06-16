#ifndef BOX_VISUALIZER_H
#define BOX_VISUALIZER_H

#include <ros/ros.h>
#include <visualization_msgs/MarkerArray.h>
#include <geometry_msgs/Pose.h>
#include <vector>
#include <string>

class BoxVisualizer
{
public:
  explicit BoxVisualizer(ros::NodeHandle& nh,
                         const std::string& custom_namespace = "boxes");
  void loadObjectsFromCSV(const std::string& filename);
  void moveObjectDown(int id);
  void moveObjectDownByPose(const geometry_msgs::Pose& pose);  // New method
  void setWorkpieceColor(int id, const std::string& color);
  void updateWorkpiecePose(int id, const geometry_msgs::Pose& new_pose);
  void setWorkpieceDimensions(double x, double y, double z);
  void removeAllObjects();
  int findClosestObject(const geometry_msgs::Pose& pose) const;  // New method

private:
  enum Color
  {
    GRAY,
    YELLOW,
    RED
  };

  struct Box
  {
    int id;
    geometry_msgs::Pose pose;
    Color color;
    int level;
    bool visible = true;
    double alpha;
  };

  ros::NodeHandle nh_;
  ros::Publisher marker_pub_;
  std::vector<Box> boxes_;
  double workpiece_x_;
  double workpiece_y_;
  double workpiece_z_;
  std::string custom_namespace_;

  void publishMarkers();
  Color stringToColor(const std::string& color);
};

#endif  // BOX_VISUALIZER_H
