cmake_minimum_required(VERSION 3.0.2)
project(movej_ik_server)

add_compile_options(-std=c++17)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(
  catkin REQUIRED
  COMPONENTS geometry_msgs
             message_generation
             moveit_core
             moveit_ros_move_group
             moveit_ros_planning_interface
             ${PROJECT_NAME}_msgs
             roscpp
             rosparam_shortcuts
             sensor_msgs
             std_msgs
             tf
             tf2
             tf2_kdl
             tf_conversions)

find_package(Eigen3 REQUIRED)

find_package(opw_kinematics REQUIRED)

catkin_python_setup()
catkin_package(
  INCLUDE_DIRS
  include
  CATKIN_DEPENDS
  geometry_msgs
  message_runtime
  moveit_ros_move_group
  moveit_ros_planning_interface
  ${PROJECT_NAME}_msgs
  roscpp
  sensor_msgs
  std_msgs
  tf
  tf_conversions)

include_directories(include ${catkin_INCLUDE_DIRS} ${Eigen_INCLUDE_DIRS}
                    ${opw_kinematics_INCLUDE_DIRS})

add_executable(${PROJECT_NAME} src/movej_ik_server.cpp
                               src/movej_ik_server_node.cpp src/opw_solver.cpp)

add_dependencies(${PROJECT_NAME} ${${PROJECT_NAME}_EXPORTED_TARGETS}
                 ${catkin_EXPORTED_TARGETS})

target_link_libraries(${PROJECT_NAME} ${Eigen_LIBRARIES} ${catkin_LIBRARIES})

install(TARGETS ${PROJECT_NAME}
        RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(
  DIRECTORY include/${PROJECT_NAME}/
  DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
  FILES_MATCHING
  PATTERN "*.h"
  PATTERN ".svn" EXCLUDE)

install(DIRECTORY config launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
