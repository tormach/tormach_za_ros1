from robot_command.rpl import (
    movej,
    sleep,
    j,
    set_units,
)
from machinekit import hal

set_units("mm", "deg")

zero = j[0.0, 0.0, 0.0, 90.0, 0.0, 0.0]


def main():
    movej(zero)
    sleep(2.0)

    # set max position offset [rad]
    hal.Pin("joint6_qc.max-pos").set(0.5)
    hal.Pin("joint6_qc.min-pos").set(-0.5)

    while True:
        # set max velocity offset [rad/s]
        hal.Pin("joint6_qc.max-vel").set(3.14)

        # set max accelaration offset [rad/s²]
        hal.Pin("joint6_qc.max-acc").set(10)

        # velocity offset demo
        timer = 4.0
        while timer > 0:
            # feed the watchdog [s]
            hal.Pin("joint6_qc.watchdog").set(0.25)

            # set veloctiy offset [rad/s]
            # this will change ext_pos_offset
            if timer > 2:
                hal.Pin("joint6_qc.ext-vel-offset").set(0.1)
            else:
                hal.Pin("joint6_qc.ext-vel-offset").set(-0.2)

            sleep(0.1)
            timer -= 0.1

        # wait for watchdog
        # this will clear any velocity and position offset
        # the robot moves back to the starting position with max-vel and max-acc
        sleep(1)

        # position offset demo
        # feed the watchdog [s]
        hal.Pin("joint6_qc.watchdog").set(1.5)

        # set postion offset [rad]
        hal.Pin("joint6_qc.ext-pos-offset").set(0.25)

        # wait for move
        sleep(1)

        # feed the watchdog [s]
        hal.Pin("joint6_qc.watchdog").set(2)

        # update limits
        hal.Pin("joint6_qc.max-vel").set(1)
        hal.Pin("joint6_qc.max-acc").set(5)

        # set postion offset [rad]
        hal.Pin("joint6_qc.ext-pos-offset").set(-0.25)

        # wait for watchdog
        # this will clear any velocity and position offset
        # the robot moves back to the start position with max-vel and max-acc
        sleep(3)

        # repeat

    exit()
