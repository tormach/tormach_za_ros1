from robot_command.rpl import *
set_units("mm", "deg", "s")

def main():
    for i in range(10):
        sleep(0.5)
        joints = get_joint_values()
        joints.j1 += 0.01 if i < 5 else -0.01
        movel(joints)
