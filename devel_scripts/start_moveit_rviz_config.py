#!/usr/bin/env python
from sh import roslaunch

from launcher import start_process, terminate_processes, wait_loop

if __name__ == '__main__':
    start_process(
        roslaunch,
        'za6_robot moveit_planning_execution.launch rviz:="true"',
    )
    wait_loop()
    terminate_processes()
