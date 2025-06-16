from enum import auto, IntEnum


class InterruptSource(IntEnum):
    """
    Interrupt source type.

    **DigitalInput:** React to a change on a digital input pin.

    **UserIo:** React to a change on a user IO pin. (triggered by HAL)

    **Program:** React to a program interrupt. (e.g. a ROS topic)
    """

    DigitalInput = auto()
    UserIo = auto()
    Program = auto()
