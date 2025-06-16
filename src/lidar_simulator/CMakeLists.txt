cmake_minimum_required(VERSION 3.0.2)
project(lidar_simulator)

find_package(
  catkin REQUIRED
  COMPONENTS geometry_msgs
             ${PROJECT_NAME}_msgs
             roscpp
             sensor_msgs
             std_msgs
             std_srvs
             tf2
             tf2_ros)

find_package(Eigen3 REQUIRED)

catkin_package(
  INCLUDE_DIRS
  include
  LIBRARIES
  ${PROJECT_NAME}
  CATKIN_DEPENDS
  geometry_msgs
  ${PROJECT_NAME}_msgs
  roscpp
  sensor_msgs
  std_msgs
  std_srvs
  tf2
  tf2_ros
  DEPENDS
  EIGEN3)

include_directories(include ${catkin_INCLUDE_DIRS} ${EIGEN3_INCLUDE_DIR})

add_library(${PROJECT_NAME} src/${PROJECT_NAME}.cpp)

add_executable(${PROJECT_NAME}_wrapper_node
               src/${PROJECT_NAME}_wrapper_node.cpp)
target_link_libraries(${PROJECT_NAME}_wrapper_node ${catkin_LIBRARIES}
                      ${PROJECT_NAME})

add_executable(${PROJECT_NAME}_wrapper_node_interactive
               src/${PROJECT_NAME}_wrapper_node_interactive.cpp)
target_link_libraries(${PROJECT_NAME}_wrapper_node_interactive
                      ${catkin_LIBRARIES} ${PROJECT_NAME})

install(TARGETS ${PROJECT_NAME}_wrapper_node
                ${PROJECT_NAME}_wrapper_node_interactive
        RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

install(
  TARGETS ${PROJECT_NAME}
  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_GLOBAL_BIN_DESTINATION})

install(
  DIRECTORY include/${PROJECT_NAME}/
  DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
  FILES_MATCHING
  PATTERN "*.h")

# Add this section to install Python scripts
catkin_install_python(PROGRAMS scripts/${PROJECT_NAME}_handler.py DESTINATION
                      ${CATKIN_PACKAGE_BIN_DESTINATION})
