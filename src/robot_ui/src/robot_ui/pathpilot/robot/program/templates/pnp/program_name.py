from robot_command.rpl import *

set_units("mm", "deg")

def main():
    movel("home")
    set_digital_out("gripper", False)
    sleep(2.0)
    movel("pickup")
    set_digital_out("gripper", True)
    sleep(2.0)
