#!/usr/bin/env python

import os
from sh import rosrun
from pathlib import Path
import logging

from launcher import (
    start_process,
    terminate_processes,
    wait_loop,
    add_default_arguments,
)

logger = logging.getLogger(f"{Path(__file__).name}")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.root.setLevel(logging.INFO)

if __name__ == '__main__':
    parser = add_default_arguments()

    args = parser.parse_args()

    extended_environment = dict()

    display_env = os.environ.get("DISPLAY", "")
    if display_env.startswith("localhost:") or display_env == "":
        logger.warning("Modifying the DISPLAY environment variable!")

        extended_environment["DISPLAY"] = (
            ":0"  # For forwarded X display, force onboard GPU
        )

    cmd = 'robot_ui launcher_ui'
    if args.live:
        cmd += ' --live'

    start_process(rosrun, cmd, environment=extended_environment)
    wait_loop()
    terminate_processes()
