cmake_minimum_required(VERSION 3.0.2)
project(lidar_pointcloud_processor)

find_package(catkin REQUIRED COMPONENTS geometry_msgs ${PROJECT_NAME}_msgs
                                        rospy sensor_msgs std_msgs)

catkin_package()

catkin_install_python(PROGRAMS scripts/${PROJECT_NAME}.py DESTINATION
                      ${CATKIN_PACKAGE_BIN_DESTINATION})

include_directories(${catkin_INCLUDE_DIRS})

# Install launch files
install(
  DIRECTORY launch
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  FILES_MATCHING
  PATTERN "*.launch")
