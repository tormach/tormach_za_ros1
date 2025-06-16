import os
import rospy

from hal_plumber import HALPlumberSim, HALPlumberEtherCAT


#####################################
# Sim mode or real hardware?
sim_mode = rospy.get_param("/hal_hardware/sim_mode", True)
# Path for halfiles
halpath = rospy.get_param("/hal_mgr/hal_file_dir")
# For locating sim_startup_selector
os.environ["PATH"] = f"{os.environ['PATH']}:{halpath}"

# read joint configuration from ROS parameters
jconfig_raw = rospy.get_param("/hardware_settings")

# Read max vel safety scale from config, used as unsafe velocity limit
unsafe_velocity_limit = rospy.get_param(
    "/hardware_interface/max_vel_safety_scale", 0.1
)

# Turn params into dict of dicts
joint_config = {
    k: {
        item_key: item_value
        for var_item in v
        for item_key, item_value in var_item.items()
    }
    for k, v in jconfig_raw.items()
}

# First create dry-run HAL config as thread period might be slower
dry_run_config = dict(
    joint_config=joint_config,  # per-joint configuration
    cgname=rospy.get_param("/hal_mgr/rt_cgname", None),
    thread_name="robot_sim_thread",
    thread_period=1e6,
    prefix='dr_',  # prefix for HAL components and signals
    unsafe_velocity_limit=unsafe_velocity_limit,
)
dry_run_hp = HALPlumberSim(**dry_run_config)
rospy.loginfo(f"Starting dry run HAL config in {dry_run_hp.mode_name} mode")
dry_run_hp.setup_hal()

# Now create real HAL config
config = dict(
    joint_config=joint_config,  # per-joint configuration
    cgname=rospy.get_param("/hal_mgr/rt_cgname", None),
    thread_name="robot_hw_thread",
    thread_period=1e6,
    # create HAL sampler and hw interface once
    create_sampler=True,
    create_hal_hw_interface=True,
    unsafe_velocity_limit=unsafe_velocity_limit,
)
if not sim_mode:  # select EtherCAT or sim mode
    # EtherCAT
    # LCEC config file
    config["lcec_config_file"] = os.path.join(
        halpath, rospy.get_param("hal_mgr/lcec_config_file")
    )
    config['prefix'] = 'hw_'
    hp = HALPlumberEtherCAT(**config)
else:
    config['prefix'] = 'sm_'
    hp = HALPlumberSim(**config)
rospy.loginfo(f"Starting HAL in {hp.mode_name} mode")
hp.setup_hal()
