cmake_minimum_required(VERSION 3.16)
project(robot_command)

# Find catkin macros and libraries
find_package(
  catkin REQUIRED
  COMPONENTS actionlib_msgs
             geometry_msgs
             moveit_commander
             moveit_msgs
             redis_store
             ${PROJECT_NAME}_msgs
             robot_frame
             ros_machinetalk
             rospy
             std_msgs
             tf
             tf2_geometry_msgs)

find_package(
  Python3
  COMPONENTS Interpreter
  REQUIRED)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#
# The catkin_package macro generates cmake config files for your package

catkin_package(
  CATKIN_DEPENDS
  actionlib_msgs
  geometry_msgs
  moveit_msgs
  ${PROJECT_NAME}_msgs
  std_msgs
  tf
  tf2_geometry_msgs
  uuid_msgs)

set(GENERATED_PYI_FILES
    "${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_PYTHON_DESTINATION}/__init__.pyi"
    "${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_PYTHON_DESTINATION}/calibration/__init__.pyi"
    "${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_PYTHON_DESTINATION}/rpl/__init__.pyi"
)

set(trpl_distributed_program_destination "/opt/pathpilot/robot/programs")

add_custom_command(
  COMMAND
    Python3::Interpreter "${CMAKE_CURRENT_SOURCE_DIR}/doc/generate_stubs.py"
    "-o" "${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_PYTHON_DESTINATION}"
  OUTPUT ${GENERATED_PYI_FILES}
  COMMENT "Generating Python typing .pyi files for the ${PROJECT_NAME}.")

add_custom_target(
  ${PROJECT_NAME}-stubs ALL
  COMMENT "Running ALL type of target ${PROJECT_NAME}-stubs"
  DEPENDS ${GENERATED_PYI_FILES}
  VERBATIM)

#
# Install ##
#

# Mark executable scripts (Python etc.) for installation
# in contrast to setup.py, you can choose the destination
install(PROGRAMS scripts/interpreter_node scripts/worker_node
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

# Install other files
install(DIRECTORY launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
# Keep the "/" at the end of "examples/programs/"!
#catkin_lint: ignore_once wrong_install_destination
install(DIRECTORY examples/programs/
        DESTINATION ${trpl_distributed_program_destination})

# Install the generated .pyi files
foreach(file_to_install ${GENERATED_PYI_FILES})
  # Cannot use the modern cmake_path() function until CMake 3.20
  string(REPLACE "${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_PYTHON_DESTINATION}/"
                 "" relative_file "${file_to_install}")
  get_filename_component(relative_directory_component ${relative_file}
                         DIRECTORY)
  #catkin_lint: ignore_once external_file
  install(
    FILES ${file_to_install}
    DESTINATION
      "${CATKIN_PACKAGE_PYTHON_DESTINATION}/${relative_directory_component}")
endforeach()
#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/lib_test.launch)
endif()
