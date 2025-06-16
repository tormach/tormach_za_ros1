#include "movej_ik_server/movej_ik_server.h"

constexpr char LOGNAME[] = "movej_ik_server";

void print_joint_values(const std::string& variable_name,
                        const std::array<double, 6>& joint_values)
{
  std::ostringstream joint_values_stream;

  for (const auto& val : joint_values)
  {
    joint_values_stream << val << ' ';
  }

  ROS_WARN("%s: %s", variable_name.c_str(), joint_values_stream.str().c_str());
}

MoveJIKServer::MoveJIKServer()
  : psm(new planning_scene_monitor::PlanningSceneMonitor("robot_description"))
  , tf_listener_(tf_buffer_)
{
  ros::NodeHandle node_handle;

  psm->startStateMonitor();    // Ensure robot state is being monitored and
                               // updated
  ros::Duration(1.0).sleep();  // Allow some time for updates to come in

  // Pass the planning scene monitor to the OPW kinematics solver
  // This allows the solver to access the robot model and planning scene
  ik_solver = std::make_unique<OpwSolver>(psm);

  // Listen to the active tool frame topic
  tool_frame_subscriber_ =
      node_handle.subscribe("/tool_frames/active_frame", 1,
                            &MoveJIKServer::tool_frame_callback, this);

  closest_ik_service_ = node_handle.advertiseService(
      "movej_closest_ik_service", &MoveJIKServer::handle_closest_ik_service,
      this);

  user_ik_service = node_handle.advertiseService(
      "movej_user_ik_service", &MoveJIKServer::handle_user_ik_service, this);

  arm_config_service = node_handle.advertiseService(
      "arm_config_service", &MoveJIKServer::handle_arm_config_service, this);

  arm_config_constraint_service = node_handle.advertiseService(
      "arm_config_constraint_service",
      &MoveJIKServer::handle_arm_config_constraint_service, this);

  std::vector<std::string> allowed_arm_config_names;
  ros::param::get("allowed_arm_configs", allowed_arm_config_names);

  if (allowed_arm_config_names.size() == 0)
  {
    ROS_ERROR("No allowed arm configurations specified. Exiting.");
    return;
  }

  std::unordered_map<std::string, uint8_t> armConfigMap;
  armConfigMap["NUT"] = ArmConfigs::NUT;
  armConfigMap["NDT"] = ArmConfigs::NDT;
  armConfigMap["NUB"] = ArmConfigs::NUB;
  armConfigMap["NDB"] = ArmConfigs::NDB;
  armConfigMap["FUT"] = ArmConfigs::FUT;
  armConfigMap["FDT"] = ArmConfigs::FDT;
  armConfigMap["FUB"] = ArmConfigs::FUB;
  armConfigMap["FDB"] = ArmConfigs::FDB;

  allowed_constraints = 0;

  for (const auto& arm_config_name : allowed_arm_config_names)
  {
    auto arm_config = armConfigMap.find(arm_config_name);
    if (arm_config == armConfigMap.end())
    {
      ROS_ERROR("Invalid arm config name: %s", arm_config_name.c_str());
      return;
    }
    ROS_WARN("Adding to valid arm configurations: %s", arm_config_name.c_str());
    allowed_constraints |= arm_config->second;
  }
}

void MoveJIKServer::tool_frame_callback(const std_msgs::String::ConstPtr& msg)
{
  tool_frame = msg->data;
  Eigen::Isometry3d relative_transform;
  calculate_transform(relative_transform);
  this->ik_solver->set_tool_frame(relative_transform.matrix());
}

bool MoveJIKServer::calculate_transform(Eigen::Isometry3d& relative_transform)
{
  geometry_msgs::TransformStamped transform_stamped;
  try
  {
    transform_stamped =
        tf_buffer_.lookupTransform("flange", tool_frame, ros::Time(0));
  }
  catch (tf2::TransformException& ex)
  {
    ROS_WARN("%s", ex.what());
    ros::Duration(1.0).sleep();
    return false;
  }
  relative_transform = tf2::transformToEigen(transform_stamped.transform);
  return true;
}

std::optional<JointArray> MoveJIKServer::get_current_joint_values() const
{
  robot_state::RobotStatePtr current_state =
      psm->getStateMonitor()->getCurrentState();

  if (!current_state)
  {
    ROS_WARN("Current robot state is not available.");
    return std::nullopt;
  }

  std::vector<double> joint_values_vec;
  current_state->copyJointGroupPositions("manipulator", joint_values_vec);

  if (joint_values_vec.size() != 6)
  {
    ROS_WARN("Current joint values vector is not size 6.");
    return std::nullopt;
  }

  JointArray current_joints;
  std::copy_n(joint_values_vec.begin(), 6, current_joints.begin());

  // print_joint_values("current_joints", current_joints);

  return current_joints;
}

bool MoveJIKServer::handle_closest_ik_service(
    movej_ik_server_msgs::MovejClosestIKService::Request& req,
    movej_ik_server_msgs::MovejClosestIKService::Response& res)
{
  // ROS_WARN("ENTER HANDLE CLOSEST IK SERVICE");
  std::optional<JointArray> current_joints = get_current_joint_values();
  if (!current_joints)
  {
    // ROS_WARN("Failed to get current joint values.");
    res.error_codes = { IKSolverError::JOINTS_STATE_UNAVAILABLE,
                        IKSolverError::START_POSE_FAILURE };
    return true;
  }

  std::optional<geometry_msgs::Pose> current_pose =
      MoveJIKServer::get_current_end_effector_pose();
  if (!current_pose)
  {
    // ROS_WARN("Failed to get current end effector pose.");
    res.error_codes = { IKSolverError::EFFECTOR_POSE_UNAVAILABLE,
                        IKSolverError::START_POSE_FAILURE };
    return true;
  }

  const geometry_msgs::Pose goal_pose = req.pose;

  // X movej(p[x,y,z,a,b,c])
  // movej(p[x,y,z,a,b,c, "NUT"])
  // movej(p[x,y,z,a,b,c, "*UT"])
  // movej(p[x,y,z,a,b,c, "*UT", 0])
  // movej(p[x,y,z,a,b,c, "NUT", 0])

  // With constraints:
  // X movej(p[x,y,z,a,b,c])
  // movej(p[x,y,z,a,b,c, "NUT"])
  // movej(p[x,y,z,a,b,c, "*UT"])
  // movej(p[x,y,z,a,b,c, "*UT", 0])
  // movej(p[x,y,z,a,b,c, "NUT", 0])

  // TODO: decide if error should be thrown for configurations out of scope

  uint8_t allowed_arm_config_mask;

  if (req.arm_config == ArmConfigs::ANY_ARM_CONFIG)
  {
    allowed_arm_config_mask = allowed_constraints;
  }
  else
  {
    allowed_arm_config_mask = req.arm_config;
  }

  // TODO: remove
  // if(!allowed_arm_config_mask) {
  //     ROS_WARN("Requested config is not in the allowed_configs set!");
  // }

  // TODO: optional, to be removed
  // if(req.arm_config != ArmConfigs::ANY_ARM_CONFIG && req.arm_config ^
  // allowed_arm_config_mask) {
  //     ROS_WARN("There exist some request_config not in the allowed_configs
  //     set!");
  // }

  ConfigConstraint goal_config_constraint;
  if (req.rev_count == ArmConfigs::ANY_REV_COUNT)
  {
    // constrain only arm configuration
    goal_config_constraint = ConfigConstraint{ allowed_arm_config_mask };
  }
  else
  {
    // constrain both arm configuration and revolution count
    goal_config_constraint =
        ConfigConstraint{ allowed_arm_config_mask, req.rev_count };
  }

  if (!goal_config_constraint)
  {
    ROS_WARN("Goal config constraint is empty.");
    res.error_codes = { IKSolverError::INVALID_CONFIG_CANDIDATES,
                        IKSolverError::GOAL_POSE_FAILURE };
    return true;
  }

  IKSolution solution = ik_solver->solve_closest_ik(
      *current_joints, *current_pose, goal_pose, goal_config_constraint);

  // print_joint_values("opw_solution", solution.opw);
  // print_joint_values("bioik_solution", solution.bioik);

  if (!solution.warning_codes.empty())
  {
    res.success = true;
    res.warning_codes = solution.warning_codes;
  }

  if (!solution.error_codes.empty())
  {
    res.success = false;
    res.error_codes = solution.error_codes;
  }
  else
  {
    std::vector<double> bioik_solution_vec;
    bioik_solution_vec.assign(solution.bioik.begin(), solution.bioik.end());
    res.joint_values = bioik_solution_vec;
    res.arm_config = (1 << solution.arm_config);
    res.rev_count = solution.rev_count;
    res.success = true;
  }

  return true;
}

bool MoveJIKServer::handle_user_ik_service(
    movej_ik_server_msgs::MovejUserIKService::Request& req,
    movej_ik_server_msgs::MovejUserIKService::Response& res)
{
  // TODO: handle erroneous arm_configuration mask input
  if (req.rev_count < -1 || req.rev_count > 1)
  {
    // TODO: pass error code to service response
    ROS_ERROR("Handle user IK service: invalid arm config.");
    res.error_codes = { IKSolverError::INVALID_CONFIG_CANDIDATES,
                        IKSolverError::GOAL_POSE_FAILURE };
    return true;
  }

  // ROS_WARN("USER IK SERVICE IS CALLED");
  TrplPose pose = request_to_trpl_pose(req);
  IKSolution solution = ik_solver->solve_user_ik(pose);

  if (!solution)
  {
    res.success = false;
    // ROS_WARN("Failure to find user joint pose.");
    res.error_codes = solution.error_codes;
    res.warning_codes = solution.warning_codes;
  }
  else
  {
    std::vector<double> bioik_solution_vec;
    bioik_solution_vec.assign(solution.bioik.begin(), solution.bioik.end());
    res.joint_values = bioik_solution_vec;
    res.arm_config = (1 << solution.arm_config);
    res.rev_count = solution.rev_count;
    res.warning_codes = solution.warning_codes;
    if (solution.is_user_specification_coherent.has_value())
    {
      res.is_user_specification_coherent =
          solution.is_user_specification_coherent.value();
    }
    res.success = true;
  }
  return true;
}

bool MoveJIKServer::handle_arm_config_service(
    movej_ik_server_msgs::GetArmConfigService::Request& req,
    movej_ik_server_msgs::GetArmConfigService::Response& res)
{
  JointArray requested_joints;
  std::optional<geometry_msgs::Pose> requested_pose;

  if (req.joint_values.size() == 6)
  {
    // Service is called with some goal joint values other than current robot
    // state
    std::copy(req.joint_values.begin(), req.joint_values.end(),
              requested_joints.begin());
    requested_pose = get_end_effector_pose(requested_joints);
  }
  else if (req.joint_values.size() == 0)
  {
    // Service is called with no goal joint values, use current joint values
    std::optional<JointArray> current_joints = get_current_joint_values();
    if (!current_joints.has_value())
    {
      ROS_ERROR("HANDLE ARM CONFIG SERVICE: NO JOINT VALUES");
      res.success = false;
      return true;
    }
    requested_joints = current_joints.value();
    requested_pose = get_current_end_effector_pose();
  }
  // Service is called with invalid goal joint values
  else
  {
    ROS_ERROR("HANDLE ARM CONFIG SERVICE WITH %d VALUES",
              (int)req.joint_values.size());
    res.success = false;
    return true;
  }

  // print_joint_values("requested_joints", requested_joints);

  // Handle the case when the requested joint values are near singularity
  // Use only OPW IK solver to find the arm configuration
  // Configuration is searched with no true robot URDF effector pose
  // This might be sensitive for near-shoulder-singularity poses
  // (arm positioned vertically pointing up)
  // but no effect for wrist or elbow singularities
  if (ik_solver->is_wrist_near_singularity(requested_joints))
  {
    ROS_INFO("ARM CONFIGURATION COMPUTED FOR NEAR-SINGULARITY POSE");
    auto response = ik_solver->joints_to_arm_config(requested_joints);
    if (!response)
    {
      // ROS_WARN("NEAR SINGULARITY returns no solution.");
      res.error_codes = { IKSolverError::SOLUTION_OUTSIDE_JOINT_LIMITS };
      res.success = false;
      return true;
    }

    auto [requested_config, rev_count] = response.value();

    res.arm_config = (1 << requested_config);
    res.rev_count = rev_count;
    res.is_arm_config_valid = bool(res.arm_config & allowed_constraints);
    res.warning_codes = { IKSolverWarning::REQUESTED_CONFIG_NEAR_SINGULARITY };
    res.success = true;

    std::bitset<8> binary_requested_config(res.arm_config);
    std::bitset<8> binary_allowed_constraints(allowed_constraints);

    ROS_INFO("COMPUTED ARM CONFIG AT GOAL: %s",
             binary_requested_config.to_string().c_str());
    ROS_INFO("ALLOWED ARM CONFIGS: %s",
             binary_allowed_constraints.to_string().c_str());

    return true;
  }

  // Handle the regular case: wrist is not near singularity
  // this case uses true robot URDF effector pose to find the arm configuration
  // and the analytical solution
  if (!requested_pose)
  {
    res.error_codes = { IKSolverError::EFFECTOR_POSE_UNAVAILABLE,
                        IKSolverError::GET_CONFIG_FAILURE };
    return false;
  }

  IKSolution solution = ik_solver->closest_joint_pose(
      requested_joints, *requested_pose, ConfigConstraint{});

  if (!solution)
  {
    solution.add_error_code(IKSolverError::GET_CONFIG_FAILURE);
    res.error_codes = solution.error_codes;
    res.warning_codes = solution.warning_codes;
    res.success = false;
    return true;
  }

  // return arm configuration as a bitmask
  res.arm_config = (1 << solution.arm_config);
  res.rev_count = solution.rev_count;
  res.is_arm_config_valid = bool(res.arm_config & allowed_constraints);
  res.success = true;
  return true;
}

bool MoveJIKServer::handle_arm_config_constraint_service(
    movej_ik_server_msgs::SetArmConfigConstraintsService::Request& req,
    movej_ik_server_msgs::SetArmConfigConstraintsService::Response& res)
{
  ROS_INFO("CALLED SERVICE: handle_arm_config_constraint_service.");
  if (req.allowed_arm_configs_mask == 0b00000000)
  {
    ROS_ERROR("Provided arm config constraints are empty. Please provide at "
              "least one allowed arm config.");
    res.success = false;
    return true;
  }

  std::bitset<8> binary_old_allowed_constraints(allowed_constraints);
  ROS_WARN("OLD ALLOWED CONFIG MASK IS: %s",
           binary_old_allowed_constraints.to_string().c_str());

  allowed_constraints = req.allowed_arm_configs_mask;

  std::bitset<8> binary_allowed_constraints(allowed_constraints);
  ROS_WARN("NEW ALLOWED CONFIG MASK IS: %s",
           binary_allowed_constraints.to_string().c_str());

  res.success = true;
  return true;
}

std::optional<geometry_msgs::Pose>
MoveJIKServer::get_current_end_effector_pose() const
{
  moveit::core::RobotStatePtr current_state =
      psm->getStateMonitor()->getCurrentState();
  if (current_state)
  {
    const Eigen::Isometry3d& end_effector_state =
        current_state->getGlobalLinkTransform("flange");
    geometry_msgs::Pose end_effector_pose;
    tf2::convert(end_effector_state, end_effector_pose);
    return end_effector_pose;
  }
  else
  {
    ROS_ERROR("Current robot state is not available.");
    return std::nullopt;
  }
}

std::optional<geometry_msgs::Pose>
MoveJIKServer::get_end_effector_pose(const JointArray& joints) const
{
  // 1. Obtain the current robot state and joint model group
  moveit::core::RobotStatePtr robot_state =
      psm->getStateMonitor()->getCurrentState();
  if (!robot_state)
  {
    ROS_ERROR("Current robot state is not available.");
    return std::nullopt;
  }

  const moveit::core::JointModelGroup* joint_model_group =
      robot_state->getJointModelGroup("manipulator");

  // 2. Set the joint values of the robot state to the desired configuration
  std::vector<double> joint_values(joints.begin(), joints.end());
  robot_state->setJointGroupPositions(joint_model_group, joint_values);

  // 3. Compute the forward kinematics to get the pose of the end effector
  const Eigen::Isometry3d& end_effector_state =
      robot_state->getGlobalLinkTransform("flange");

  geometry_msgs::Pose end_effector_pose;
  tf2::convert(end_effector_state, end_effector_pose);

  return end_effector_pose;
}
