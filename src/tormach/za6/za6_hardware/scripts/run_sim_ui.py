#!/usr/bin/env python
import subprocess
import sys
import time

from machinekit import launcher
import rospkg

PACKAGE_NAME = 'za6_hardware'

rospack = rospkg.RosPack()

try:
    launcher.register_exit_handler()  # enable on ctrl-C, needs to executed after HAL files
    launcher.ensure_mklauncher()  # ensure mklauncher is started
    launcher.start_process(
        f'configserver -n HAL-IO {rospack.get_path(PACKAGE_NAME)}'
    )

    while True:
        launcher.check_processes()
        time.sleep(1)

except subprocess.CalledProcessError:
    launcher.end_session()
    sys.exit(1)
