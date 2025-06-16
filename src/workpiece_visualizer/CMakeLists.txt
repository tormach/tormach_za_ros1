cmake_minimum_required(VERSION 3.0.2)
project(workpiece_visualizer)
find_package(
  catkin REQUIRED COMPONENTS geometry_msgs roscpp tf2 tf2_geometry_msgs
                             visualization_msgs ${PROJECT_NAME}_msgs)
catkin_package(
  INCLUDE_DIRS
  include
  LIBRARIES
  ${PROJECT_NAME}
  CATKIN_DEPENDS
  geometry_msgs
  roscpp
  tf2
  tf2_geometry_msgs
  visualization_msgs
  ${PROJECT_NAME}_msgs)
include_directories(include ${catkin_INCLUDE_DIRS})
add_library(${PROJECT_NAME} src/BoxVisualizer.cpp)
add_executable(${PROJECT_NAME}_node src/main.cpp)
add_executable(${PROJECT_NAME}_server src/box_visualizer_server.cpp)
target_link_libraries(${PROJECT_NAME}_node ${PROJECT_NAME} ${catkin_LIBRARIES})
target_link_libraries(${PROJECT_NAME}_server ${PROJECT_NAME}
                      ${catkin_LIBRARIES})
install(
  TARGETS ${PROJECT_NAME} ${PROJECT_NAME}_node ${PROJECT_NAME}_server
  ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
  RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY include/${PROJECT_NAME}/
        DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION})
install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
