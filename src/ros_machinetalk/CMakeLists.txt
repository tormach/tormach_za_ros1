cmake_minimum_required(VERSION 3.0.2)
project(ros_machinetalk)

find_package(catkin REQUIRED COMPONENTS ${PROJECT_NAME}_msgs rospy)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${PROJECT_SOURCE_DIR}/cmake)
# find_package(HAL REQUIRED)
# find_package(Avahi REQUIRED)

# Install packages with setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#
catkin_package(
  CATKIN_DEPENDS
  ${PROJECT_NAME}_msgs
  rospy
  # DEPENDS
  # HAL avahi-daemon # apt packages
  # machinetalk-protobuf pymachinetalk # pip packages
)

#
# Install ##
#

# Install python executables
catkin_install_python(
  PROGRAMS
  scripts/machinetalk_client
  scripts/machinetalk_manager
  scripts/machinetalk_node
  scripts/machinekit_ros_log_bridge
  DESTINATION
  ${CATKIN_PACKAGE_BIN_DESTINATION})

# Install launch files
install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/lib_test.launch)
endif()
