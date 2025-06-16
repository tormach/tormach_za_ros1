from robot_common.tools import get_param


def filter(caller) -> bool:
    tool = get_param('tool')

    if tool and tool == 'gr60_gripper':
        return False

    return True
