cmake_minimum_required(VERSION 3.0.2)
project(za6_tools)

find_package(catkin REQUIRED)
catkin_package(CATKIN_DEPENDS xacro)

install(DIRECTORY config meshes urdf
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
