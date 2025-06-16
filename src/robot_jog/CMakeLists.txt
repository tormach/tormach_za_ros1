cmake_minimum_required(VERSION 3.0.2)
project(robot_jog)

# Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS moveit_commander robot_command
                                        ${PROJECT_NAME}_msgs rospy)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#
# The catkin_package macro generates cmake config files for your package

catkin_package(CATKIN_DEPENDS ${PROJECT_NAME}_msgs)

#
# Install ##
#

catkin_install_python(
  PROGRAMS scripts/continuous_jog_frame_node scripts/interactive_jog_node
  scripts/simple_key_jog DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/lib_test.launch)
endif()
