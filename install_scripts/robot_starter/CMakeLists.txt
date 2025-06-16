cmake_minimum_required(VERSION 3.20)

project(TormachPathPilotRobotLauncher LANGUAGES NONE)

include(GNUInstallDirs)

# Input source files
set(TPPR_Launch_starter
    ${CMAKE_CURRENT_SOURCE_DIR}/src/launch-pathpilot-launcher.in)
set(TPPR_Launch_starter_Desktop
    ${CMAKE_CURRENT_SOURCE_DIR}/src/robot-launcher.desktop.in)
set(Tormach_PathPilot_icon ${CMAKE_CURRENT_SOURCE_DIR}/src/icons/pathpilot.svg)
set(Tormach_icon ${CMAKE_CURRENT_SOURCE_DIR}/src/icons/tormach.svg)
set(TPP_Menu ${CMAKE_CURRENT_SOURCE_DIR}/src/tormach.menu)
set(TPP_Directory ${CMAKE_CURRENT_SOURCE_DIR}/src/tormach.directory)
set(TPPR_starter_splash_install_prefix "opt/pathpilot/venvs")
set(TPPR_pathpilotrobotstarter_preinst
    ${CMAKE_CURRENT_SOURCE_DIR}/debian/pathpilotrobotstarter.preinst.in)
set(TPPR_pathpilotrobotstarter_postinst
    ${CMAKE_CURRENT_SOURCE_DIR}/debian/pathpilotrobotstarter.postinst.in)

# Sizes of PNG icons to create
set(_icon_sizes
    "8"
    "16"
    "20"
    "22"
    "24"
    "32"
    "36"
    "40"
    "42"
    "48"
    "60"
    "64"
    "72"
    "80"
    "96"
    "128"
    "192"
    "256"
    "384"
    "512")

find_program(_rsvg_convert "rsvg-convert" REQUIRED)

set(_TPPR_Launch_starter_Desktop_generatred
    "${CMAKE_CURRENT_BINARY_DIR}/build/robot-launcher.desktop")
configure_file(${TPPR_Launch_starter_Desktop}
               ${_TPPR_Launch_starter_Desktop_generatred})

set(TPPR_Launch_starter_generated
    "${CMAKE_CURRENT_BINARY_DIR}/build/launch-pathpilot-launcher")
set(PATHPILOT_ROBOT_STARTER_SPLASH
    "/${TPPR_starter_splash_install_prefix}/robot_splash/bin/robot_starter_splash"
)
configure_file(${TPPR_Launch_starter} ${TPPR_Launch_starter_generated} @ONLY
               NEWLINE_STYLE UNIX NO_SOURCE_PERMISSIONS)

foreach(_icon IN ITEMS "${Tormach_icon}" "${Tormach_PathPilot_icon}")
  foreach(_size ${_icon_sizes})
    set(_geometry_${size} "${_size}x${_size}")
    set(_destination_${_size}
        "${CMAKE_CURRENT_BINARY_DIR}/build/icons/hicolor/${_geometry_${size}}/apps"
    )
    cmake_path(GET _icon STEM ${_icon}_filename)
    set(_destination_${_size}_${_icon}
        "${_destination_${_size}}/${${_icon}_filename}.png")

    add_custom_command(
      OUTPUT "${_destination_${_size}_${_icon}}"
      COMMAND ${CMAKE_COMMAND} "-E" "make_directory" "${_destination_${_size}}"
      COMMAND
        ${_rsvg_convert} "--keep-aspect-ratio" "--format" "png" "--width"
        "${_size}" "--height" "${_size}" "--output"
        "${_destination_${_size}_${_icon}}" "${_icon}"
      COMMENT "Generating the ${_geometry_${size}} icon '${${_icon}_filename}'."
    )

    add_custom_target(ICON_${${_icon}_filename}_${_size} ALL
                      DEPENDS "${_destination_${_size}_${_icon}}")

    install(
      FILES "${_destination_${_size}_${_icon}}"
      DESTINATION
        "${CMAKE_INSTALL_DATAROOTDIR}/icons/hicolor/${_geometry_${size}}/apps"
      RENAME "${${_icon}_filename}.png"
      COMPONENT Executables)
  endforeach()
endforeach()

cmake_path(REMOVE_EXTENSION TPPR_pathpilotrobotstarter_preinst LAST_ONLY
           OUTPUT_VARIABLE _pathpilotrobotstarter_preinst)
cmake_path(REMOVE_EXTENSION TPPR_pathpilotrobotstarter_postinst LAST_ONLY
           OUTPUT_VARIABLE _pathpilotrobotstarter_postinst)
cmake_path(
  REPLACE_EXTENSION TPPR_pathpilotrobotstarter_postinst LAST_ONLY ".configured"
  OUTPUT_VARIABLE _pathpilotrobotstarter_postinst_configured)

configure_file(${TPPR_pathpilotrobotstarter_preinst}
               ${_pathpilotrobotstarter_preinst} @ONLY)
configure_file(${TPPR_pathpilotrobotstarter_postinst}
               ${_pathpilotrobotstarter_postinst_configured} @ONLY)

file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/python/debian)
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/debian/control
               ${CMAKE_CURRENT_BINARY_DIR}/python/debian/control COPYONLY)

add_custom_target(
  PPR_starter_venv ALL
  COMMENT "Building the PathPilot Robot starter Python virtual environment")

find_package(
  Python 3.6...4.0
  COMPONENTS Interpreter
  REQUIRED)

find_program(BASH "bash" REQUIRED)

add_custom_command(
  TARGET PPR_starter_venv
  COMMAND
    "${CMAKE_COMMAND}" "-E" "env"
    "DH_VIRTUALENV_INSTALL_ROOT=/${TPPR_starter_splash_install_prefix}"
    "dh_virtualenv" "--python" "${Python_EXECUTABLE}" "--builtin-venv"
    "--upgrade-pip" "--use-system-packages" "--install-suffix" "robot_splash"
    "--sourcedirectory=${CMAKE_CURRENT_SOURCE_DIR}/src/starter_splash"
  COMMAND "${CMAKE_COMMAND}" "-E" "rm" "-f" "${_pathpilotrobotstarter_postinst}"
  COMMAND
    "${BASH}" "-c"
    "add_postinst=$(<${CMAKE_CURRENT_BINARY_DIR}/python/debian/pathpilotrobotstarter.postinst.debhelper); postinst=$(<${_pathpilotrobotstarter_postinst_configured}); echo -e \"$postinst;$add_postinst\" >>${_pathpilotrobotstarter_postinst}"
  VERBATIM
  COMMENT "Creating the PathPilot Robot starter Python virtual environment"
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/python)

install(
  DIRECTORY
    "${CMAKE_CURRENT_BINARY_DIR}/python/debian/pathpilotrobotstarter/${TPPR_starter_splash_install_prefix}"
  DESTINATION "/opt/pathpilot"
  USE_SOURCE_PERMISSIONS
  COMPONENT Executables)

install(
  PROGRAMS ${_TPPR_Launch_starter_Desktop_generatred}
  DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/applications"
  COMPONENT Executables)

install(
  FILES ${Tormach_icon}
  DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/icons/hicolor/scalable/apps"
  RENAME "tormach.svg"
  COMPONENT Executables)

install(
  FILES ${Tormach_PathPilot_icon}
  DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/icons/hicolor/scalable/apps"
  RENAME "pathpilot.svg"
  COMPONENT Executables)

install(
  PROGRAMS ${TPPR_Launch_starter_generated}
  DESTINATION "${CMAKE_INSTALL_BINDIR}"
  COMPONENT Executables)

# This will require saner installatiom method once there are more packages
# sharing the same menu
install(
  PROGRAMS ${TPP_Menu}
  DESTINATION "${CMAKE_INSTALL_SYSCONFDIR}/xdg/menus/applications-merged"
  COMPONENT Executables)

install(
  FILES ${TPP_Directory}
  DESTINATION "${CMAKE_INSTALL_DATAROOTDIR}/desktop-directories"
  COMPONENT Executables)
