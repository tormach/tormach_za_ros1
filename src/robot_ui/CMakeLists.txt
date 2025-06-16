cmake_minimum_required(VERSION 3.0.2)
project(robot_ui)

find_package(catkin REQUIRED COMPONENTS robot_command rospy unique_id)

# Install python from setup.py
catkin_python_setup()

#
# catkin specific configuration ##
#

catkin_package()

add_custom_command(
  OUTPUT src/${PROJECT_NAME}/res/pathpilot_en.qm
  COMMAND bash ${CMAKE_CURRENT_SOURCE_DIR}/src/scripts/release_translations.sh
  DEPENDS src/${PROJECT_NAME}/res/pathpilot_en.po)
add_custom_target(translations ALL
                  DEPENDS src/${PROJECT_NAME}/res/pathpilot_en.qm)

#
# Install ##
#

# Mark executable scripts (Python etc.) for installation
# in contrast to setup.py, you can choose the destination
install(PROGRAMS scripts/launcher_ui scripts/${PROJECT_NAME} scripts/window_test
        DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})

# Mark other files for installation (e.g. launch and bag files, etc.)
#install(FILES config.myviz DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

# QML compiled files
# We can compile with QtQuick compiler starting with v. 5.11
#find_package(Qt5QuickCompiler)
#qtquick_compiler_add_resources(RESOURCES src/${PROJECT_NAME}.qrc)

# Install directories
install(DIRECTORY config launch DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})

#
# Testing ##
#

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  find_package(ros_pytest REQUIRED)
  add_rostest(tests/integration_tests.launch)
  add_rostest(tests/lib_test.launch)
endif()
