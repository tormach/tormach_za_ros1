cmake_minimum_required(VERSION 3.0.2)
project(gr60_gripper)

# Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS rospy)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#

catkin_package()

#
# Install ##
#

catkin_install_python(
  PROGRAMS
  scripts/gripper
  scripts/gripper_sim
  scripts/gripper_gui
  scripts/gripper_probe
  DESTINATION
  ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch meshes urdf
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  #add_rostest(tests/lib_test.launch)
endif()
