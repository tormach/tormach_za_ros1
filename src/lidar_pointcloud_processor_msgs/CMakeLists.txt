cmake_minimum_required(VERSION 3.0.2)
project(lidar_pointcloud_processor_msgs)

find_package(catkin REQUIRED COMPONENTS geometry_msgs message_generation
                                        message_runtime std_msgs)

add_service_files(
  FILES
  EstimateLidarLine.srv
  FindClosestLidarRectangle.srv
  FindHighestLidarZ.srv
  ProcessLidarData.srv
  PurgeLidarData.srv
  RefineLidarLengthDisplacement.srv
  SetDetectorParams.srv
  SetLidarDetectorState.srv)

generate_messages(DEPENDENCIES geometry_msgs std_msgs)

catkin_package(CATKIN_DEPENDS geometry_msgs message_runtime std_msgs)
