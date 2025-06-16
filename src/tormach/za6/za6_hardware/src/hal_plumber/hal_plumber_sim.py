from hal_hw_interface import hal

from .hal_plumber import HALPlumber
from .hal_joint_plumber_sim import HALJointPlumberSim


class HALPlumberSim(HALPlumber):
    mode_name = "sim"
    joint_plumber_class = HALJointPlumberSim

    def setup_drive(self):
        # See HALJointPlumberSim.connect_drive() for info

        # sim_start_pos signal:  when True, load start position
        # - oneshot for triggering load once at startup
        sim_start_pos = self.newinst("oneshot", "sim_start_pos")
        self.func_config(f"{sim_start_pos.name}.funct", self.Prio.DRIVE_READ_FB)
        # - go high for a short time, only once
        sim_start_pos.pin("width").set(0.1)
        sim_start_pos.pin("retriggerable").set(False)
        sim_start_pos.pin("in").set(True)
        # - signal will connect to sim_drive.load and to sim_pos_sel input
        ssp_sig = self.newsig("sim_start_pos", hal.HAL_BIT)
        ssp_sig.link(sim_start_pos.pin("out"))

        # sim_pos_sel signal:  switch btw. start and ROS cmd positions
        conv = self.newinst("conv_bit_s32", "sim_pos_sel")
        self.func_config(f"{conv.name}.funct", self.Prio.DRIVE_READ_FB + 21)
        ssp_sig.link(conv.pin("in"))
        # - signal will connect to sim_pos_channel inputs
        sps_sig = self.newsig("sim_pos_sel", hal.HAL_S32)
        sps_sig.link(conv.pin("out"))
        # - signal for reseting sim joint position
        self.newsig("sim_pos_load", hal.HAL_BIT)

    def setup_quick_stop(self):
        pass
