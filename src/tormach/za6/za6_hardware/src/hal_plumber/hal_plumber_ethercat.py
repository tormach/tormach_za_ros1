import rospy

from hal_hw_interface import hal, rtapi

from .hal_plumber import HALPlumber
from .hal_joint_plumber_ethercat import HALJointPlumberEtherCAT


class HALPlumberEtherCAT(HALPlumber):
    mode_name = "EtherCAT"
    joint_plumber_class = HALJointPlumberEtherCAT

    def __init__(self, lcec_config_file, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lcec_config_file = lcec_config_file

    def setup_drive(self):
        # Configure lcec component
        rospy.loginfo(f"Loading LCEC with config file {self.lcec_config_file}")
        # load ethercat config parser
        hal.loadusr(
            f"lcec_conf {self.lcec_config_file}", wait=True, wait_timeout=10.0
        )
        # load ethercat realtime module
        rtapi.loadrt("lcec")

        # Read fb at beginning of cycle, write cmd at end
        self.func_config("lcec.0.read", self.Prio.DRIVE_READ_FB)
        self.func_config("lcec.0.write", self.Prio.DRIVE_WRITE_CMD)

    def setup_quick_stop(self):
        ext_fault = self.newinst(
            "ornv2", "ext_fault", pincount=(self.num_joints)
        )
        self.func_config(
            f"{ext_fault.name}.funct", self.Prio.DRIVE_READ_FB + 25
        )
        s = self.newsig("ext_fault", hal.HAL_BIT)
        s.link(ext_fault.pin("out"))
        s.link(self.comp("drive_safety").pin("quick-stop-ext"))
        # for joint in self.joints:
        #    s = hal.newsig('joint' + str(joint.num) + '_error', hal.HAL_BIT)
        #    s.link("joint" + str(joint.num) + "_ppi.error")
        #    s.link("ext_fault.in" + str(joint.slavenum))
