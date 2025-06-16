cmake_minimum_required(VERSION 3.0.2)
project(pathpilot_lib)

find_package(catkin REQUIRED COMPONENTS)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#

catkin_package()

#
# Install ##
#

#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/lib_test.launch)
endif()
