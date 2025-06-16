cmake_minimum_required(VERSION 3.0.2)
project(robot_frame)

# Find catkin macros and libraries
find_package(
  catkin REQUIRED
  COMPONENTS geometry_msgs
             redis_store
             ${PROJECT_NAME}_msgs
             rospy
             std_msgs
             tf
             tf2_geometry_msgs)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#
# The catkin_package macro generates cmake config files for your package

catkin_package(CATKIN_DEPENDS geometry_msgs ${PROJECT_NAME}_msgs std_msgs tf
               tf2_geometry_msgs)

#
# Install ##
#

# Mark executable scripts (Python etc.) for installation
# in contrast to setup.py, you can choose the destination
install(PROGRAMS scripts/frame_client scripts/frame_node
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

# Install other files
install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/lib_test.launch)
endif()
