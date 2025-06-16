cmake_minimum_required(VERSION 3.16)

project(se_jogger)

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

catkin_install_python(PROGRAMS scripts/basic_jogger DESTINATION
                      ${CATKIN_PACKAGE_BIN_DESTINATION})

install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#if(CATKIN_ENABLE_TESTING)
#  find_package(rostest REQUIRED)
#  find_package(ros_pytest REQUIRED)
#  add_rostest(tests/test.launch)
#endif()
