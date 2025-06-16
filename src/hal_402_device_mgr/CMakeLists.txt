cmake_minimum_required(VERSION 3.0.2)
project(hal_402_device_mgr)

#* Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

#* Find catkin macros and libraries
#* if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
#* is used, also find other catkin packages
find_package(catkin REQUIRED COMPONENTS hal_hw_interface rospy)

# Find Machinekit HAL
find_package(HAL)
include(UseHALComp)

# Use setup.py
catkin_python_setup()

#**********************************
#* catkin specific configuration **
#**********************************
catkin_package(CATKIN_DEPENDS hal_hw_interface rospy)

#************
# Build HAL component
#************

# Header files
# - Specify additional header locations
include_directories(${HAL_INCLUDE_PATH} ${catkin_INCLUDE_DIRS})

hal_add_instcomp(src/drive_safety)

#************
#* Install **
#************

# Install python executables
catkin_install_python(PROGRAMS scripts/drive_config scripts/hal_402_mgr
                      DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

#**********
#* Tests **
#**********

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/test.launch)
endif()
