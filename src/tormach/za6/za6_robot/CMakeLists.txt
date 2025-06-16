cmake_minimum_required(VERSION 3.0.2)
project(za6_robot)

find_package(catkin REQUIRED COMPONENTS srdfdom)

# catkin specific configuration
catkin_package()

# Install python executables
catkin_install_python(PROGRAMS scripts/reset_param_defaults DESTINATION
                      ${CATKIN_PACKAGE_BIN_DESTINATION})

# Install other files
install(DIRECTORY config launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
