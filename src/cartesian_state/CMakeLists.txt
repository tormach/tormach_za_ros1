cmake_minimum_required(VERSION 3.0.2)
project(cartesian_state)

add_compile_options(-std=c++11)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(
  catkin REQUIRED
  COMPONENTS ${PROJECT_NAME}_msgs
             moveit_ros_move_group
             moveit_ros_planning_interface
             roscpp
             rosparam_shortcuts
             sensor_msgs
             tf
             tf_conversions)

find_package(Eigen3 REQUIRED)

catkin_package(
  INCLUDE_DIRS
  include
  CATKIN_DEPENDS
  ${PROJECT_NAME}_msgs
  moveit_ros_move_group
  moveit_ros_planning_interface
  roscpp
  sensor_msgs
  tf
  tf_conversions)

include_directories(include ${catkin_INCLUDE_DIRS} ${Eigen_INCLUDE_DIRS})

add_executable(joints_to_pose include/${PROJECT_NAME}/joints_to_pose.h
                              src/${PROJECT_NAME}/joints_to_pose.cpp)
add_dependencies(joints_to_pose ${catkin_EXPORTED_TARGETS})
target_link_libraries(joints_to_pose ${Eigen_LIBRARIES} ${catkin_LIBRARIES})

install(TARGETS joints_to_pose
        RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(
  DIRECTORY include/${PROJECT_NAME}/
  DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
  FILES_MATCHING
  PATTERN "*.h"
  PATTERN ".svn" EXCLUDE)

# FIXME Are these actually necessary?
# # Install config and launch directories
# install(
#   DIRECTORY
#   config
#   launch
#   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
#   )

#if(CATKIN_ENABLE_TESTING)
#  find_package(rostest)
#  set(UTEST_SRC_FILES test/utest.cpp)
#
#  add_rostest_gtest(compliant_control_utest test/launch/utest.launch ${UTEST_SRC_FILES})
#  target_link_libraries(compliant_control_utest ${catkin_LIBRARIES} ${Boost_LIBRARIES} compliant_control)
#endif()
