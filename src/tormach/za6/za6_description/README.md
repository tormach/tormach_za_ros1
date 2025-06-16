# `za6_description` package

Contains URDF files and meshes for the ZA robot.

http://wiki.ros.org/xacro
http://wiki.ros.org/urdf
http://docs.ros.org/kinetic/api/moveit_tutorials/html/doc/urdf_srdf/urdf_srdf_tutorial.html

## `za6_robot` package and MoveIt! Setup Assistant

- Run the demo
  - `roslaunch za6_moveit_config demo.launch`
  - This doesn't depend on any robot hardware, and is useful to check
    URDFs and planning configuration
- Re-run the `moveit_setup_assistant`
  - `roslaunch za6_moveit_config setup_assistant.launch`
  - To ease future regeneration, note changes in the below section
    "`za6_moveit_config` package creation from scratch"


## Xacro operations

- Convert xacro to URDF
  `rosrun xacro xacro -o /tmp/za6.urdf \
      $(rospack find za6_description)/urdf/za6.xacro`

- Verify URDF
  - `check_urdf /tmp/za6.urdf`

- Visualize URDF structure
  - `urdf_to_graphiz /tmp/za6.urdf; evince za6.pdf`

- Convert to Collada format
  - `rosrun collada_urdf urdf_to_collada /tmp/za6.urdf /tmp/za6.dae`
  - Note:  OpenRAVE no longer available in ROS Noetic:
    https://index.ros.org/p/openrave/

## `za6_moveit_config` package creation from scratch

See the [MoveIt! Setup Assistant tutorial][msa_tut]

- Build workspace to pick up `za6_description` package
- Verify URDFs (see below)
- Run `roslaunch moveit_setup_assistant setup_assistant.launch`
- "Start" tab:
  - Select "Create New Moveit Configuration Package"
  - Load the `src/tormach/za6_description/urdf/za6.xacro` URDF model
  - Add optional xacro arguments: "tool:=none stand:=none"
  - Click "Load Files"
- "Self-Collisions" tab:  Adds `disable_collisions` elements to SRDF
  - Click "Generate Collision Matrix"
  - Optionally, disable additional collisions
    - Click "show enabled pairs"
    - Disable additional collisions:
      - base -> 2, 2 -> 4, 4 -> 6 can't collide with joint limits in
        effect (coarse collision models?)
- "Virtual Joints" tab:  Adds `virtual_joint` element to SRDF
  - Click "Add Virtual Joint"
    - "Virtual Joint Name" "world"
    - "Parent Link" "world"
    - "Child Link" "world"
    - "Joint Type" "fixed"
    - Click "Save"
- "Planning Groups" tab:  Adds `group` element to SRDF
  - Add `manipulator` group:  Click "Add Group"
    - "Group Name" "manipulator"
    - "Kinematics Solver" "bio_ik/BioIKKinematicsPlugin"
    - "Group Default Planner" "RRT"
    - Click "Add Kin. Chain"
      - Base Link:  "base_link"
      - Tip Link:  "tool0"
      - Click "Save"
  - Add `manipulator_global` group:  Click "Add Group"
    - "Group Name" "manipulator"
    - "Kinematics Solver" "bio_ik/BioIKKinematicsPlugin"
    - "Group Default Planner" "RRT"
    - Click "Add Kin. Chain"
      - Base Link:  "base_link"
      - Tip Link:  "tool0"
      - Click "Save"
  - Add `manipulator_tcp` group:  Click "Add Group"
    - "Group Name" "manipulator"
    - "Kinematics Solver" "None"
    - "Group Default Planner" "None"
    - Click "Add Kin. Chain"
    - Base Link:  "base_link"
    - Tip Link:  "tool0"
    - Click "Save"
- "Robot Poses" tab:  Adds `group_state` element to SRDF
  - Click "Add Pose"
    - "Pose Name" "all-zeros"
    - Leave other setting default
    - Click "Save"
- "End Effectors" tab:  (Skip)
- "Passive Joints" tab:  (Skip)
- "ROS Control" tab:  Configures `ros_controllers.yaml` file
  - Click "Add Controller"
    - "Controller Name" "position_trajectory_controller"
    - "Controller Type" "position_controllers/JointTrajectoryController"
    - Click "Add Individual Joints"
      - Select "joint_[1-6]"
      - Click ">" to add
      - Click "Save"
- "Simulation" tab:  (Skip)
- "3D Perception" tab:  (Skip)
- "Author information" tab:
  - Enter name and email
- "Configuration Files" tab:
  - "Configuration Package Save Path"
    "[...]/src/tormach/borunte_moveit_config" (Create directory first)
  - Click "Generate Package"
    - Click "Ok" at "Incomplete" warning
  - Click "Exit Setup Assistant"

After `catkin build && devel/setup.bash`, test:
```
roslaunch za6_moveit_config demo.launch
```



[msa_tut]: http://docs.ros.org/kinetic/api/moveit_tutorials/html/doc/setup_assistant/setup_assistant_tutorial.html

## Verify URDFs

```
MODEL=za6
for TOOL in \
    none \
    hand_e \
    ; do
  for STAND in \
      none \
      prototype \
      ; do

      echo -e "\n\n**** ${MODEL}.xacro tool=${TOOL} stand=${STAND} ****\n"
      rosrun xacro xacro tool:=${TOOL} stand:=${STAND} \
          `rospack find ${MODEL}_description`/urdf/${MODEL}.xacro -o /tmp/test.urdf
      check_urdf /tmp/test.urdf
      cp `rospack find ${MODEL}_moveit_config`/config/${MODEL}.srdf `rospack find ${MODEL}_robot`/config/${MODEL}_${TOOL}_${STAND}.srdf
      rosrun moveit_setup_assistant collisions_updater --verbose --trials 10000 --min-collision-fraction 0.95 --urdf /tmp/test.urdf --srdf `rospack find ${MODEL}_robot`/config/${MODEL}_${TOOL}_${STAND}.srdf
    done
done
```
