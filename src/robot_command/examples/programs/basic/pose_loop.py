from robot_command.rpl import *
set_units("mm", "deg", "s")

def main():
    for i in range(10):
        sleep(0.5)
        pose = get_pose()
        pose.z += 0.01 if i < 5 else -0.01
        movel(pose)
