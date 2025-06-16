cmake_minimum_required(VERSION 3.0.2)
project(robot_common)

# Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS rospy)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#
# The catkin_package macro generates cmake config files for your package

catkin_package()

#
# Install ##
#

# Mark executable scripts (Python etc.) for installation
# in contrast to setup.py, you can choose the destination
#install(PROGRAMS scripts/something
#        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

# Install other files
#install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/lib_test.launch)
endif()
