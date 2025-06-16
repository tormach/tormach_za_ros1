#!/usr/bin/env python
from sh import rosrun

from launcher import start_process, terminate_processes, wait_loop

if __name__ == '__main__':
    start_process(rosrun, 'za6_hardware run_sim_ui.py')
    wait_loop()
    terminate_processes()
