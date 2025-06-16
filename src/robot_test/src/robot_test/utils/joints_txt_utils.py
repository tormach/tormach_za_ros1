import os


def append_joints_pose(filename, joints_pose):
    # Check if file exists, if not create and initialize the list of joints
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            f.write("my_joints = [\n")

    # Open file in append mode and add the new joints pose
    with open(filename, 'a') as f:
        f.write("    " + str(joints_pose) + ',\n')


def close_joints_list(filename):
    if os.path.exists(filename):
        with open(filename) as f:
            lines = f.readlines()

        if lines:
            # Replace the last character (the comma) with a space
            lines[-1] = lines[-1][:-2] + "\n"
            # Add the closing bracket
            lines.append("]")

        with open(filename, 'w') as f:
            f.writelines(lines)
    else:
        print("File doesn't exist.")
