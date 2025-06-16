cmake_minimum_required(VERSION 3.0.2)
project(tormach_pcnc_1100_support)

find_package(catkin REQUIRED)
catkin_package()

install(DIRECTORY launch meshes urdf
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
