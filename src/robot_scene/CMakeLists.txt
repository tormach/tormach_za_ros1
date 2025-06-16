cmake_minimum_required(VERSION 3.0.2)
project(robot_scene)

find_package(catkin REQUIRED COMPONENTS rospy)

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${PROJECT_SOURCE_DIR}/cmake)

# Install packages with setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#
catkin_package(CATKIN_DEPENDS rospy)

#
# Install ##
#

# Install python executables
catkin_install_python(
  PROGRAMS scripts/tool_scene_sync scripts/machine_scene_sync DESTINATION
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
