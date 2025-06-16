#include <ros/ros.h>
#include "workpiece_visualizer/BoxVisualizer.h"
#include <workpiece_visualizer_msgs/LoadFromCSV.h>
#include <workpiece_visualizer_msgs/SetObject.h>
#include <workpiece_visualizer_msgs/UpdatePose.h>
#include <workpiece_visualizer_msgs/SetColor.h>
#include <workpiece_visualizer_msgs/SetWorkpieceDimensions.h>
#include <std_srvs/Empty.h>

class BoxVisualizerServer
{
public:
  BoxVisualizerServer(ros::NodeHandle& nh) : box_visualizer_(nh)
  {
    load_csv_service_ = nh.advertiseService(
        "load_objects_from_csv",
        &BoxVisualizerServer::loadObjectsFromCSVCallback, this);
    move_object_down_service_ = nh.advertiseService(
        "move_object_down", &BoxVisualizerServer::moveObjectDownCallback, this);
    set_color_service_ = nh.advertiseService(
        "set_workpiece_color", &BoxVisualizerServer::setWorkpieceColorCallback,
        this);
    update_pose_service_ = nh.advertiseService(
        "update_pose", &BoxVisualizerServer::updatePoseCallback, this);
    set_dimensions_service_ = nh.advertiseService(
        "set_workpiece_dimensions",
        &BoxVisualizerServer::setWorkpieceDimensionsCallback, this);
    remove_all_objects_service_ = nh.advertiseService(
        "remove_all_objects", &BoxVisualizerServer::removeAllObjectsCallback,
        this);
  }

private:
  BoxVisualizer box_visualizer_;
  ros::ServiceServer load_csv_service_;
  ros::ServiceServer move_object_down_service_;
  ros::ServiceServer set_color_service_;
  ros::ServiceServer update_pose_service_;
  ros::ServiceServer set_dimensions_service_;
  ros::ServiceServer remove_all_objects_service_;

  bool loadObjectsFromCSVCallback(
      workpiece_visualizer_msgs::LoadFromCSV::Request& req,
      workpiece_visualizer_msgs::LoadFromCSV::Response& res)
  {
    box_visualizer_.loadObjectsFromCSV(req.filename);
    res.success = true;
    return true;
  }

  bool
  moveObjectDownCallback(workpiece_visualizer_msgs::SetObject::Request& req,
                         workpiece_visualizer_msgs::SetObject::Response& res)
  {
    if (req.id < 0)
    {
      // Use pose-based targeting
      box_visualizer_.moveObjectDownByPose(req.pose);
      box_visualizer_.setWorkpieceColor(
          box_visualizer_.findClosestObject(req.pose), "GRAY");
    }
    else
    {
      // Use direct ID targeting
      box_visualizer_.moveObjectDown(req.id);
      box_visualizer_.setWorkpieceColor(req.id, "GRAY");
    }
    res.success = true;
    return true;
  }

  bool
  setWorkpieceColorCallback(workpiece_visualizer_msgs::SetColor::Request& req,
                            workpiece_visualizer_msgs::SetColor::Response& res)
  {
    box_visualizer_.setWorkpieceColor(req.id, req.color);
    res.success = true;
    return true;
  }

  bool updatePoseCallback(workpiece_visualizer_msgs::UpdatePose::Request& req,
                          workpiece_visualizer_msgs::UpdatePose::Response& res)
  {
    box_visualizer_.updateWorkpiecePose(req.id, req.new_pose);
    res.success = true;
    return true;
  }

  bool setWorkpieceDimensionsCallback(
      workpiece_visualizer_msgs::SetWorkpieceDimensions::Request& req,
      workpiece_visualizer_msgs::SetWorkpieceDimensions::Response& res)
  {
    box_visualizer_.setWorkpieceDimensions(req.x, req.y, req.z);
    res.success = true;
    return true;
  }

  bool removeAllObjectsCallback(std_srvs::Empty::Request& req,
                                std_srvs::Empty::Response& res)
  {
    box_visualizer_.removeAllObjects();
    return true;
  }
};

int main(int argc, char** argv)
{
  ros::init(argc, argv, "box_visualizer_server");
  ros::NodeHandle nh;

  BoxVisualizerServer server(nh);

  ROS_INFO("Box Visualizer Server is ready.");
  ros::spin();

  return 0;
}
