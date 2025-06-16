cmake_minimum_required(VERSION 3.0.2)
project(pp_ros_launch)

#* Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS rospy)

# Use setup.py
catkin_python_setup()

#**********************************
#* catkin specific configuration **
#**********************************
catkin_package(CATKIN_DEPENDS rospy)

#************
#* Install **
#************

# Install python executables
catkin_install_python(PROGRAMS scripts/run_pp_ros scripts/pp_launcher_listener
                      DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/test.launch)
endif()
