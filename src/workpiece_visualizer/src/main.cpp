#include <ros/ros.h>
#include "workpiece_visualizer/BoxVisualizer.h"

int main(int argc, char** argv)
{
  ros::init(argc, argv, "workpiece_visualizer_node");
  ros::NodeHandle nh;
  BoxVisualizer boxVisualizer(nh);

  // Load objects from CSV file
  boxVisualizer.loadObjectsFromCSV("path/to/your/csv/file.csv");

  // Example usage of the interface
  boxVisualizer.setWorkpieceColor(0, "YELLOW");
  boxVisualizer.moveObjectDown(1);
  boxVisualizer.setWorkpieceColor(0, "GRAY");

  ros::spin();

  return 0;
}
