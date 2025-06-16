cmake_minimum_required(VERSION 3.0.2)
project(robot_benchmark)

# Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS moveit_commander robot_command rospy)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#
# The catkin_package macro generates cmake config files for your package

catkin_package(CATKIN_DEPENDS rospy)

#
# Install ##
#

catkin_install_python(PROGRAMS scripts/ik_benchmark DESTINATION
                      ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#
# Testing ##
#

#if(CATKIN_ENABLE_TESTING)
#  find_package(rostest REQUIRED)
#  find_package(ros_pytest REQUIRED)
#  add_rostest(tests/lib_test.launch)
#endif()
