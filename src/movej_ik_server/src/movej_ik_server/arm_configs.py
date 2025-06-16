from enum import Flag
from enum import IntEnum

from movej_ik_server_msgs.msg import ArmConfigs


class ArmConfigType(IntEnum):
    FUT = ArmConfigs.FUT
    NUT = ArmConfigs.NUT
    FDT = ArmConfigs.FDT
    NDT = ArmConfigs.NDT
    FUB = ArmConfigs.FUB
    NUB = ArmConfigs.NUB
    FDB = ArmConfigs.FDB
    NDB = ArmConfigs.NDB
    AnyConfig = ArmConfigs.ANY_ARM_CONFIG

    def __str__(self):
        return self.name


class JointConfig(Flag):
    NUT = ArmConfigs.NUT
    NDT = ArmConfigs.NDT
    NUB = ArmConfigs.NUB
    NDB = ArmConfigs.NDB
    FUT = ArmConfigs.FUT
    FDT = ArmConfigs.FDT
    FUB = ArmConfigs.FUB
    FDB = ArmConfigs.FDB

    NUx = NUT | NUB
    NDx = NDT | NDB
    FUx = FUT | FUB
    FDx = FDT | FDB

    NxT = NUT | NDT
    NxB = NUB | NDT
    FxT = FUT | FDT
    FxB = FUB | FDB

    xUT = NUT | FUT
    xDT = NDT | FDT
    xUB = NUB | FUB
    xDB = NDB | FDB

    Nxx = NUx | NDx
    Fxx = FUx | FDx

    xUx = FUx | NUx
    xDx = FDx | NDx

    xxT = xUT | xDT
    xxB = xUB | xDB

    ALL = xxT | xxB  # equivalent to ArmConfigs.ANY_ARM_CONFIG

    def __and__(self, other):
        raise NotImplementedError(
            "Bitwise AND operation is not supported for JointConfig flags."
        )

    @classmethod
    def _missing_(cls, value):
        if value == 0:
            raise ValueError("Not a valid JointConfig")
        return super()._missing_(value)


arm_config_strings = [str(e.name) for e in JointConfig]
