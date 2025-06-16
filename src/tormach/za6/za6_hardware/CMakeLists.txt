cmake_minimum_required(VERSION 3.0.2)
project(za6_hardware)

#* Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS hal_hw_interface rospy)

# Find Machinekit HAL
find_package(HAL)
include(UseHALComp)

# Install packages with setup.py
catkin_python_setup()

#
# catkin specific configuration
#
catkin_package(CATKIN_DEPENDS hal_hw_interface rospy)

# Header files
# - Specify additional header locations
include_directories(${HAL_INCLUDE_PATH} ${catkin_INCLUDE_DIRS})

#
# Build HAL components
#

hal_add_instcomp(src/limit3v3)
hal_add_instcomp(src/ppi)
hal_add_instcomp(src/pll)
hal_add_instcomp(src/est)
hal_add_instcomp(src/latency)
hal_add_instcomp(src/qc)
hal_add_instcomp(src/multilatency)
hal_add_instcomp(src/joint_helper)
hal_add_instcomp(src/wait_hal_settle)

#
# Install
#

# Install python executables
catkin_install_python(
  PROGRAMS
  scripts/dry_run_switcher
  scripts/run_sim_ui.py
  scripts/ecat_pcap_decode.py
  scripts/halsampler_decode.py
  DESTINATION
  ${CATKIN_PACKAGE_BIN_DESTINATION})

# Install other files
install(DIRECTORY config halfiles launch
        DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
