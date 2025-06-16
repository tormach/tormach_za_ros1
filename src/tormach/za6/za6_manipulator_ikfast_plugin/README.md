# IKFast plugin

The plugin has been generated according to the descriptions found here: <https://ros-planning.github.io/moveit_tutorials/doc/ikfast/ikfast_tutorial.html>

The IK plugin needs to be re-generated when the offsets inside the URDF file change.

## Generate IKFast plugin package from scratch

Inside the development Docker image run:
```
export MYROBOT_NAME=za6
rosrun xacro xacro -o $MYROBOT_NAME.urdf src/tormach/za6_description/urdf/$MYROBOT_NAME.xacro
rosrun collada_urdf urdf_to_collada $MYROBOT_NAME.urdf $MYROBOT_NAME.dae
rosrun moveit_kinematics round_collada_numbers.py $MYROBOT_NAME.dae $MYROBOT_NAME.rounded.dae 5
```

Outside the development Docker image with minimum ROS version melodic run:
```
export MYROBOT_NAME=za6
sudo apt install -y ros-melodic-moveit-kinematics
source /opt/ros/melodic/setup.bash
rosrun moveit_kinematics auto_create_ikfast_moveit_plugin.sh --keep --name $MYROBOT_NAME --iktype Transform6D za6.rounded.dae manipulator base_link tool0
```

The command runs inside another Docker container and generates a new ROS plugin package. Make sure the
tests automatically run after plugin generation succeed.
