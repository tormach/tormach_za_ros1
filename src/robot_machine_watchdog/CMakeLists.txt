cmake_minimum_required(VERSION 3.0.2)
project(robot_machine_watchdog)

find_package(catkin REQUIRED COMPONENTS robot_command ${PROJECT_NAME}_msgs
                                        rospy sensor_msgs std_msgs)

catkin_python_setup()

catkin_package(CATKIN_DEPENDS robot_command ${PROJECT_NAME}_msgs rospy
               sensor_msgs std_msgs)

include_directories(${catkin_INCLUDE_DIRS})

catkin_install_python(
  PROGRAMS ${PROJECT_NAME}/watchdog_node.py ${PROJECT_NAME}/hal_utils.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
