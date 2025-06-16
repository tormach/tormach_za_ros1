# Helper scripts for development

Start the Python scripts from the root directory like so:

```bash
python scripts/start_moveit_config.py
```

The scripts require the [sh](https://amoffat.github.io/sh/) Python module:

```bash
pip install sh
```

## Workspace
To setup the ROS workspace you can use the `ros_workspace.sh` script.

```bash
source ros_workspace.sh`
```

## Control

* `start_moveit_config.py`: starts Machinekit + MoveIt
* `start_moveit_rviz_config.py`: starts Machinekit + MoveIt + RViz
* `start_jogging.py`: start the jog_arm and joy config

## GUI
*Prerequisite:* MoveIt MoveGroup up and running.

* `start_live_coding.py`: start the live coding GUI
* `start_robot_ui.py`: start the Robot GUI as it would be started normally

## Program
* `start_program_interpreter`: start the program interpreter standalone
