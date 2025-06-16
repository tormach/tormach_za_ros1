#include "movej_ik_server/opw_solver.h"

geometry_msgs::Pose interpolatePose(const geometry_msgs::Pose& start,
                                    const geometry_msgs::Pose& end, double t)
{
  // Ensure t is within the range [0, 1]
  t = std::max(0.0, std::min(1.0, t));

  geometry_msgs::Pose interpolated;

  // Linear interpolation for position
  interpolated.position.x =
      start.position.x + t * (end.position.x - start.position.x);
  interpolated.position.y =
      start.position.y + t * (end.position.y - start.position.y);
  interpolated.position.z =
      start.position.z + t * (end.position.z - start.position.z);

  // Spherical linear interpolation (slerp) for orientation
  tf2::Quaternion q1, q2;
  tf2::fromMsg(start.orientation, q1);
  tf2::fromMsg(end.orientation, q2);

  tf2::Quaternion q_interpolated = q1.slerp(q2, t);
  q_interpolated.normalize();

  interpolated.orientation = tf2::toMsg(q_interpolated);

  return interpolated;
}

int signum(int val)
{
  return (val > 0) - (val < 0);
}

OpwSolver::OpwSolver()
{
  za6_opw_params_ = make_za6<double>();
  tool_frame_ = Eigen::Matrix4d::Identity();

  std::string movej_ik_switch;
  ros::param::get("/movej_ik_switch", movej_ik_switch);
  if (std::string("bio").compare(movej_ik_switch))
  {
    this->solver_switch = true;
  }
  else if ((std::string("nonbio").compare(movej_ik_switch)))
  {
    this->solver_switch = false;
  }
  else
  {
    throw std::logic_error("Unknown mojej_ik_switch value!");
  }
}

OpwSolver::OpwSolver(planning_scene_monitor::PlanningSceneMonitorPtr psm)
  : psm_(psm)
{
  const robot_model::RobotModelConstPtr& robot_model_ =
      psm_->getStateMonitor()->getCurrentState()->getRobotModel();
  za6_opw_params_ = make_za6<double>();
  tool_frame_ = Eigen::Matrix4d::Identity();

  std::string movej_ik_switch;
  ros::param::get("/movej_ik_switch", movej_ik_switch);
  if (std::string("bio").compare(movej_ik_switch))
  {
    this->solver_switch = true;
  }
  else
  {
    this->solver_switch = false;
  }
}

bool OpwSolver::is_solution_within_bounds(const JointArray& solution) const
{
  // Create a new robot state based on the current state of the robot
  moveit::core::RobotStatePtr robot_state =
      psm_->getStateMonitor()->getCurrentState();

  // pick the joint model group for the manipulator
  const moveit::core::JointModelGroup* joint_model_group =
      robot_state->getJointModelGroup("manipulator");

  // Convert array to vector
  std::vector<double> solution_vector(solution.begin(), solution.end());

  // Set the joint values of the robot state
  robot_state->setJointGroupPositions(joint_model_group, solution_vector);

  // Check if the joint values are within bounds
  const std::vector<const moveit::core::JointModel*>& joint_models =
      joint_model_group->getActiveJointModels();
  for (const auto& joint_model : joint_models)
  {
    if (!robot_state->satisfiesPositionBounds(joint_model))
    {
      return false;
    }
  }

  return true;
}

bool OpwSolver::is_shoulder_config_valid(const JointArray& solution) const
{
  // in this function the value of J1 is ignored
  // because it does not affect the shoulder configuration
  auto solution_copy = solution;
  solution_copy[0] = 0.0;

  // run forward kinematics to get the Cartesian pose of the flange
  Eigen::Transform<double, 3, Eigen::Isometry> flange_pose =
      opw_kinematics::forward(za6_opw_params_, solution_copy);

  Eigen::Matrix4d flange_to_wrist_center_transform =
      Eigen::Matrix4d::Identity();
  flange_to_wrist_center_transform(2, 3) = -za6_opw_params_.c4;

  // find the Cartesian pose of the wrist center
  Eigen::Matrix4d wrist_center_transform =
      flange_pose.matrix() * flange_to_wrist_center_transform;
  double x_wrist_center = wrist_center_transform(0, 3);

  // find the Cartesian pose of the tool tip
  Eigen::Matrix4d effector_pose_matrix = flange_pose.matrix() * tool_frame_;
  double x_effector = effector_pose_matrix(0, 3);

  // return true if both wrist center and endeffector
  // are both on the same mid plane ( devided by J1 z axis)
  return (x_wrist_center > 0.0 && x_effector > 0.0) ||
         (x_wrist_center < 0.0 && x_effector < 0.0);
}

std::optional<std::array<JointArray, 8>>
OpwSolver::get_all_ik(const Eigen::Isometry3d& pose) const
{
  std::array<JointArray, 8> sols;
  sols = opw_kinematics::inverse(za6_opw_params_, pose);
  reorder_shoulder_solutions(sols);

  bool exist_valid_sol = false;
  for (auto& sol : sols)
  {
    if (opw_kinematics::isValid(sol))
    {
      exist_valid_sol = true;
      opw_kinematics::harmonizeTowardZero(sol);
    }
  }

  if (exist_valid_sol)
  {
    return sols;
  }

  return std::nullopt;
}

double OpwSolver::distance(const JointArray& a, const JointArray& b) const
{
  double cost = 0.0;
  for (int i = 0; i < a.size(); ++i)
    cost += std::abs(b[i] - a[i]);
  return cost;
}

// bool OpwSolver::closest_joint_pose(const JointArray& seed_joints,
//                                    const geometry_msgs::Pose& pose,
//                                    const int& config_constraint,
//                                    JointArray& opw_solution,
//                                    JointArray& bioik_solution, int&
//                                    solution_id, int& rev_count) const

// user_joint_pose is a special case of closest_joint_pose
// user_joint_pose

// bool OpwSolver::go_to_closest(const JointArray& seed_joints,
//                                    const geometry_msgs::Pose& pose,
//                                    IKSolution& solution) const
//                                    {
//                                    const int config_constraint = -1;
//                                    // call closest_joint_pose
//                                    }

// camelCase
// snake_case
// auto [a, b, c] = fun(x);
// without C++17?

IKSolution OpwSolver::solve_closest_ik(
    const JointArray& current_joints, const geometry_msgs::Pose& current_pose,
    const geometry_msgs::Pose& goal_pose,
    const ConfigConstraint& goal_config_constraint) const
{
  std::vector<int> warnings = {};

  // Solve the OPW solution for the current pose
  // this is required for computing the closes goal joint pose
  IKSolution current_solution{};

  // current_solution =
  //     closest_joint_pose(current_joints, current_pose, ConfigConstraint{});
  // if (!current_solution)
  // {
  // IKSolution local_solution = closest_joint_pose(current_joints, goal_pose,
  //                                         goal_config_constraint);

  // // TODO: try to resolve angle mismatch if it happened or near singularity
  // goal by just iteratively solving the IK on the line

  // current_solution.add_error_code(IKSolverError::START_POSE_FAILURE);
  // return current_solution;
  // }

  if (is_wrist_near_singularity(current_joints))
  {
    // Note that starting at the singularity is not a fatal error
    // As opposed to ending at the singularity
    warnings.push_back(IKSolverWarning::START_POSE_WRIST_NEAR_SINGULARITY);
    // put true joint values to opw solution and skip computing opw
    current_solution.opw = current_joints;
  }
  else
  {
    current_solution =
        closest_joint_pose(current_joints, current_pose, ConfigConstraint{});
    // if (!current_solution)
    // {
    // IKSolution local_solution = closest_joint_pose(current_joints, goal_pose,
    //                                         goal_config_constraint);

    // // TODO: try to resolve angle mismatch if it happened or near singularity
    // goal by just iteratively solving the IK on the line if (!local_solution
    // || is_opw_bioik_mismatch_fatal(local_solution) ||
    // is_wrist_near_singularity(local_solution.bioik) ||
    // is_wrist_near_singularity(local_solution.opw))
    // {
    //   // JointArray new_seed = current_joints;
    //   std::optional<JointArray> new_seed = current_joints;
    //   int max_iter = 1000;

    //   for (int t = 1; t <= max_iter; t += 1)
    //   {
    //     double factor = static_cast<double>(t) / max_iter;

    //     geometry_msgs::Pose interpolated = interpolatePose(current_pose,
    //     goal_pose, factor);

    //     Eigen::Isometry3d interpolated_eigen;
    //     tf2::convert(interpolated, interpolated_eigen);

    //     std::optional<JointArray> new_bioik_solution =
    //     iterative_ik(*new_seed, interpolated_eigen); if (new_bioik_solution)
    //     {
    //       new_seed = new_bioik_solution;
    //     }
    //     else {
    //       new_seed = std::nullopt;
    //       break;
    //     }
    //   }
    //   if(new_seed)
    //   {
    //     local_solution.is_valid = true;
    //     local_solution.bioik = *new_seed;
    //     local_solution.opw = *new_seed;
    //     local_solution.warning_codes = warnings;
    //     return local_solution;
    //   }
    // }
    // current_solution.add_error_code(IKSolverError::START_POSE_FAILURE);
    // return current_solution;
    // }
  }

  // if (!local_solution || is_opw_bioik_mismatch_fatal(local_solution) ||
  // is_wrist_near_singularity(local_solution.bioik) ||
  // is_wrist_near_singularity(local_solution.opw))
  // {
  // JointArray new_seed = current_joints;

  IKSolution solution = closest_joint_pose(current_solution.opw, goal_pose,
                                           goal_config_constraint);

  if (!solution || is_opw_bioik_mismatch_fatal(solution) ||
      is_wrist_near_singularity(solution.bioik) ||
      is_wrist_near_singularity(solution.opw))
  {
    IKSolution local_solution{};

    std::optional<JointArray> new_seed = current_joints;
    int max_iter = 100;

    int failed_attempts = 0;
    int allowed_failed_attempts = 10;

    geometry_msgs::Pose current_pose_copiable = current_pose;

    for (int t = 1; t <= max_iter && failed_attempts < allowed_failed_attempts;
         t += 1)
    {
      double factor = static_cast<double>(t) / max_iter;

      geometry_msgs::Pose interpolated =
          interpolatePose(current_pose_copiable, goal_pose, factor);

      Eigen::Isometry3d interpolated_eigen;
      tf2::convert(interpolated, interpolated_eigen);

      std::optional<JointArray> new_bioik_solution =
          iterative_ik(*new_seed, interpolated_eigen);
      if (new_bioik_solution)
      {
        new_seed = new_bioik_solution;

        if (abs(new_seed.value()[3]) > M_PI / 2)
        {
          auto current_joints_copiable = current_joints;
          for (auto& item : current_joints_copiable)
          {
            item += ((rand() % 101 - 50) / 100.0) * 0.2;
          }
          // run forward kinematics to get the Cartesian pose of the flange
          current_pose_copiable =
              get_end_effector_pose(current_joints_copiable).value();
          t = 1;
          new_seed = current_joints;
          failed_attempts++;
        }
      }
      else
      {
        auto current_joints_copiable = current_joints;
        for (auto& item : current_joints_copiable)
        {
          item += ((rand() % 101 - 50) / 100.0) * 0.2;
        }
        // run forward kinematics to get the Cartesian pose of the flange
        current_pose_copiable =
            get_end_effector_pose(current_joints_copiable).value();
        t = 1;
        new_seed = current_joints;
        failed_attempts++;

        ROS_ERROR("Failed IK search at iteration: %d Trying again.",
                  failed_attempts);

        if (failed_attempts > allowed_failed_attempts)
        {
          ROS_ERROR("Could not find valid IK with randomizer.");
          new_seed = std::nullopt;
          break;
        }
      }
    }
    if (new_seed)
    {
      ROS_ERROR("SUCCESS at attempt: %d", failed_attempts);
      local_solution.is_valid = true;
      local_solution.bioik = *new_seed;
      local_solution.opw = *new_seed;
      local_solution.warning_codes = warnings;
      return local_solution;
    }
  }
  // }

  // print_joint_values("current_joints", current_joints);
  // print_joint_values("current_opw_solution", current_solution.opw);
  // print_joint_values("current_bioik_solution", current_solution.bioik);

  // TODO: try to resolve angle mismatch if it happened or near singularity goal
  // by just iteratively solving the IK on the line if (!solution ||
  // is_opw_bioik_mismatch_fatal(solution) ||
  // is_wrist_near_singularity(solution.bioik) ||
  // is_wrist_near_singularity(solution.opw))
  // {
  //   // JointArray new_seed = current_joints;
  //   std::optional<JointArray> new_seed = current_joints;
  //   int max_iter = 1000;

  //   for (int t = 1; t <= max_iter; t += 1)
  //   {
  //     double factor = static_cast<double>(t) / max_iter;

  //     geometry_msgs::Pose interpolated = interpolatePose(current_pose,
  //     goal_pose, factor);

  //     Eigen::Isometry3d interpolated_eigen;
  //     tf2::convert(interpolated, interpolated_eigen);

  //     std::optional<JointArray> new_bioik_solution = iterative_ik(*new_seed,
  //     interpolated_eigen); if (new_bioik_solution)
  //     {
  //       new_seed = new_bioik_solution;
  //     }
  //     else {
  //       new_seed = std::nullopt;
  //       break;
  //     }
  //   }
  //   if(new_seed)
  //   {
  //     solution.is_valid = true;
  //     solution.bioik = *new_seed;
  //     solution.opw = *new_seed;
  //     solution.warning_codes = warnings;
  //     return solution;
  //   }
  // }

  // if at least one error exists in the solution
  if (!solution)
  {
    solution.add_error_code(IKSolverError::GOAL_POSE_FAILURE);
    solution.warning_codes = warnings;
    return solution;
  }

  const double j6_position = solution.bioik[5];
  // if commanded revolution count is outside the joint limits
  if ((goal_config_constraint.rev_count == std::vector<int>{ -1 } &&
       j6_position > -M_PI) ||
      (goal_config_constraint.rev_count == std::vector<int>{ 1 } &&
       j6_position < M_PI))
  {
    // detailed information that J6 position (related to rev_count)
    // is causing the solution to be outside the joint limits
    solution.add_error_code(IKSolverError::UNREACHABLE_REV_COUNT);
    solution.add_error_code(IKSolverError::GOAL_POSE_FAILURE);

    // more general information that the solution is outside the joint limits
    // solution.add_error_code(IKSolverError::SOLUTION_OUTSIDE_JOINT_LIMITS);

    return solution;
  }

  // check for large deviation between OPW and BIO IK solutions
  if (is_opw_bioik_mismatch_fatal(solution))
  {
    solution.add_error_code(IKSolverError::FATAL_ANALYTICAL_NUMERICAL_MISMATCH);
    solution.add_error_code(IKSolverError::GOAL_POSE_FAILURE);
    solution.warning_codes = warnings;
    return solution;
  }

  if (is_wrist_near_singularity(solution.bioik))
  {
    // this is a fatal error for ending move close to singularity
    solution.add_error_code(IKSolverError::WRIST_NEAR_SINGULARITY);
    solution.add_error_code(IKSolverError::GOAL_POSE_FAILURE);
    solution.warning_codes = warnings;
    return solution;
  }

  solution.is_valid = true;
  solution.warning_codes = warnings;
  return solution;
}

IKSolution OpwSolver::closest_joint_pose(
    const JointArray& seed_joints, const geometry_msgs::Pose& pose,
    const ConfigConstraint constraint) const
{
  IKSolution solution;
  Eigen::Isometry3d pose_desired_eigen;
  tf2::fromMsg(pose, pose_desired_eigen);

  // solve all OPW IK (8 solutions)
  auto opw_candidates = get_all_ik(pose_desired_eigen);

  if (!opw_candidates)
  {
    // ROS_WARN("No OPW IK solution found for the desired pose");
    solution.add_error_code(IKSolverError::NO_ANALYTICAL_SOLUTION);
    return solution;
  }

  // auto candidate_configs = create_candidate_configs(constraint);
  if (!constraint)
  {
    // ROS_WARN("No valid candidate configs found in the closestJointPose "
    //          "function");
    solution.add_error_code(IKSolverError::INVALID_CONFIG_CANDIDATES);
    return solution;
  }

  // initialize variables for finding the closest OPW solution
  double lowest_cost = std::numeric_limits<double>::max();
  bool valid_candidate_found = false;

  for (auto i : constraint.config)
  {
    if (!opw_kinematics::isValid(opw_candidates.value()[i]) ||
        !is_solution_within_bounds(opw_candidates.value()[i]))
    {
      continue;  // Skip to the next iteration if the candidate is not valid
    }

    // explore robot configurations with different rev count state
    for (int offset_index : constraint.rev_count)
    {
      auto candidate_opw_solution = opw_candidates.value()[i];
      candidate_opw_solution[5] += 2 * M_PI * signum(offset_index);

      if (this->solver_switch)
      {
        std::optional<JointArray> current_bioik_solution =
            iterative_ik(candidate_opw_solution, pose_desired_eigen);

        if (!current_bioik_solution ||
            !is_solution_within_bounds(*current_bioik_solution))
        {
          continue;
        }

        double current_cost = distance(seed_joints, candidate_opw_solution);
        if (current_cost < lowest_cost)
        {
          lowest_cost = current_cost;
          solution.opw = candidate_opw_solution;
          solution.bioik = *current_bioik_solution;
          solution.arm_config = i;
          solution.rev_count = offset_index;
        }
      }
      else
      {
        if (!is_solution_within_bounds(candidate_opw_solution))
        {
          continue;
        }
        double current_cost = distance(seed_joints, candidate_opw_solution);
        if (current_cost < lowest_cost)
        {
          lowest_cost = current_cost;
          solution.opw = candidate_opw_solution;
          solution.bioik = candidate_opw_solution;
          solution.arm_config = i;
          solution.rev_count = offset_index;
        }
      }

      valid_candidate_found = true;
    }
  }

  // If no valid candidate is found, throw an exception
  if (!valid_candidate_found)
  {
    solution.add_error_code(IKSolverError::SOLUTION_OUTSIDE_JOINT_LIMITS);
    return solution;
  }
  solution.is_valid = true;
  return solution;
}

IKSolution OpwSolver::solve_user_ik(const TrplPose& pose) const
{
  // validate user arm configuration and revolution count input
  // TODO: handle invalid binary arm_config mask
  if (pose.rev_count < -1 || pose.rev_count > 1)
  {
    return IKSolution{ IKSolverError::INVALID_CONFIG_CANDIDATES };
  }

  IKSolution solution{};
  if (pose.cached_joints.has_value())
  {
    solution = solve_user_ik_cache(pose);
  }
  else
  {
    solution = solve_user_ik_nocache(pose);
  }

  if (!solution)
  {
    solution.add_error_code(IKSolverError::GOAL_POSE_FAILURE);
  }
  return solution;
}

// *** Handle TrplPose with cached joints ***
// NOTE: This feature is implemented but currently not used
// Search for the closest configuration for goal pose using cached joints
// for this pose passed to this function in the TrplPose object
IKSolution OpwSolver::solve_user_ik_cache(const TrplPose& pose) const
{
  if (!pose.cached_joints)
  {
    ROS_ERROR("Called user_joint_pose_cache() with a TrplPose object that does "
              "not have a cached joint solution.");
  }

  // check if the cached joints have size of 6
  if (pose.cached_joints->size() != 6)
  {
    ROS_ERROR("Cached joints vector does not have size 6.");
    return IKSolution{ IKSolverError::CACHED_JOINTS_INVALID_SIZE };
  }

  IKSolution verified_solution =
      closest_joint_pose(*pose.cached_joints, pose.pose, ConfigConstraint{});

  if (!verified_solution)
  {
    verified_solution.add_error_code(IKSolverError::POSE_NO_LONGER_REACHABLE);
    return verified_solution;
  }

  // if the closest configuration is different from the one selected by the
  // user, then a tool_frame or user_frame has alternated the waypoint
  if (pose.solution_id == verified_solution.arm_config &&
      pose.rev_count == verified_solution.rev_count)
  {
    verified_solution.is_valid = true;
    verified_solution.is_user_specification_coherent = true;
    verified_solution.has_cache = true;
    return verified_solution;
  }

  if (pose.solution_id != verified_solution.arm_config)
  {
    verified_solution.add_warning_code(IKSolverWarning::ARM_CONFIG_CHANGED);
  }
  if (pose.rev_count != verified_solution.rev_count)
  {
    verified_solution.add_warning_code(IKSolverWarning::REV_COUNT_CHANGED);
  }
  verified_solution.is_valid = true;
  verified_solution.is_user_specification_coherent = false;
  verified_solution.has_cache = true;
  return verified_solution;
}

IKSolution OpwSolver::solve_user_ik_nocache(const TrplPose& pose) const
{
  Eigen::Isometry3d pose_desired_eigen;
  tf2::fromMsg(pose.pose, pose_desired_eigen);

  IKSolution solution{};
  std::optional<std::array<JointArray, 8>> opw_candidates =
      get_all_ik(pose_desired_eigen);

  if (!opw_candidates)
  {
    solution.add_error_code(IKSolverError::NO_ANALYTICAL_SOLUTION);
    return solution;
  }

  // possible robot J6 additions with different rev count state
  auto candidate_opw_solution = opw_candidates.value()[pose.solution_id];

  // Use the provided isValid function to check for non-finite values
  if (!opw_kinematics::isValid(candidate_opw_solution))
  {
    solution.add_error_code(IKSolverError::NO_ANALYTICAL_SOLUTION);
    return solution;
  }

  if (is_wrist_near_singularity(candidate_opw_solution))
  {
    solution.add_error_code(IKSolverError::WRIST_NEAR_SINGULARITY);
    return solution;
  }

  // update J6 revolution count
  candidate_opw_solution[5] += 2 * M_PI * signum(pose.rev_count);

  // Possible TODO: handle OPW solution out of bounds that will converge to a
  // valid numerical solution if
  // (!is_solution_within_bounds(candidate_opw_solution))
  //   return false;

  std::optional<JointArray> bioik_goal_joints =
      iterative_ik(candidate_opw_solution, pose_desired_eigen);
  if (!bioik_goal_joints)
  {
    // a rare scenario where OPW solution is valid but BIO IK fails
    solution.add_error_code(IKSolverError::NO_NUMERICAL_SOLUTION);
    return solution;
  }

  const double j6_position = bioik_goal_joints.value()[5];
  // if commanded revolution count is outside the joint limits
  if ((pose.rev_count == -1 && j6_position > -M_PI) ||
      (pose.rev_count == 1 && j6_position < M_PI))
  {
    // detailed information that J6 position (related to rev_count)
    // is causing the solution to be outside the joint limits
    solution.add_error_code(IKSolverError::UNREACHABLE_REV_COUNT);

    // more general information that the solution is outside the joint limits
    // solution.add_error_code(IKSolverError::SOLUTION_OUTSIDE_JOINT_LIMITS);

    return solution;
  }

  // Executed when no errors encountered
  solution.bioik = bioik_goal_joints.value();
  solution.has_cache = true;
  solution.is_user_specification_coherent = true;
  return solution;
}

// TODO: make this working with a launch file
// template from the opw_kinematics package
template <typename T>
opw_kinematics::Parameters<T> OpwSolver::make_za6()
{
  opw_kinematics::Parameters<T> p;

  ros::param::get("/opw_params/a1", p.a1);
  ros::param::get("/opw_params/a2", p.a2);
  ros::param::get("/opw_params/b", p.b);
  ros::param::get("/opw_params/c1", p.c1);
  ros::param::get("/opw_params/c2", p.c2);
  ros::param::get("/opw_params/c3", p.c3);
  ros::param::get("/opw_params/c4", p.c4);

  T offset2, offset5;
  ros::param::get("/opw_params/offset2", offset2);
  ros::param::get("/opw_params/offset5", offset5);

  p.offsets[2] = offset2;
  p.offsets[5] = offset5;

  return p;
}

// Fix mismatch between OPW arm config implementation and the industry standard
void OpwSolver::reorder_shoulder_solutions(
    std::array<JointArray, 8>& sols) const
{
  std::vector<int> shoulder_front_solution_ids = { 0, 1, 4, 5 };
  for (auto i : shoulder_front_solution_ids)
  {
    // check if the shoulder solution corresponds to the front and back criteria
    // as defined by FANUC configurations
    // If solution exist and does not satisfy the criteria, swap it with the
    // other corresponding solution
    if ((opw_kinematics::isValid(sols[i]) &&
         !is_shoulder_config_valid(sols[i])) ||
        (opw_kinematics::isValid(sols[i + 2]) &&
         !is_shoulder_config_valid(sols[i + 2])))
    {
      std::swap(sols[i], sols[i + 2]);
    }
  }
}

bool OpwSolver::is_wrist_near_singularity(const JointArray& joints) const
{
  const int wrist_joint_num = 4;
  const double wrist_singularity_threshold = 0.0873;
  return std::abs(joints[wrist_joint_num]) < wrist_singularity_threshold;
}

bool OpwSolver::is_opw_bioik_mismatch_fatal(const IKSolution& solution) const
{
  JointArray mismatch;
  std::transform(solution.opw.begin(), solution.opw.end(),
                 solution.bioik.begin(), mismatch.begin(),
                 [](double a, double b) { return std::abs(a - b); });

  double threshold = 0.2;  // rad
  bool isFatal =
      std::any_of(mismatch.begin(), mismatch.end(),
                  [threshold](double val) { return val > threshold; });
  return isFatal;
}

// TODO: use this function in the linear traversal
std::optional<JointArray> OpwSolver::iterative_ik(
    const JointArray new_seed, const Eigen::Isometry3d desired_pose) const
{
  // Get a RobotState object for the current state of the robot
  moveit::core::RobotStatePtr kinematic_state =
      psm_->getStateMonitor()->getCurrentState();

  // cast new_seed array to an std::vector
  std::vector<double> new_seed_vec(new_seed.begin(), new_seed.end());
  // Set the IK seed state
  kinematic_state->setJointGroupPositions("manipulator", new_seed_vec);

  // Now you can call setFromIK
  const moveit::core::JointModelGroup* joint_model_group =
      kinematic_state->getJointModelGroup("manipulator");

  // TODO: consider adding a limit in BioIK solution search
  // note that the outcome of this is validated later too
  // Convert geometry_msgs::Pose to Eigen::Isometry3d
  // Eigen::Isometry3d desired_pose;
  // tf2::fromMsg(pose, desired_pose);

  // TODO: Set the angular limit from the seed state for seeking a valid
  // iterative IK solution double angular_limit = M_PI / 2;  // equivalent of 3
  // deg

  // Define the callback function
  // moveit::core::GroupStateValidityCallbackFn constraint_fn =
  //     [joint_model_group, new_seed_vec, angular_limit](
  //         moveit::core::RobotState* state, const
  //         moveit::core::JointModelGroup*, const double*
  //         joint_group_variable_values) {
  //       // calculate angular distance from seed state
  //       double angular_distance = 0.0;
  //       for (std::size_t i = 0; i < joint_model_group->getVariableCount();
  //       ++i)
  //       {
  //         angular_distance +=
  //             std::abs(joint_group_variable_values[i] - new_seed_vec[i]);
  //       }
  //       // return whether the state is valid
  //       return angular_distance <= angular_limit;
  //     };

  // // Call setFromIK
  // kinematics::KinematicsQueryOptions options;
  // options.return_approximate_solution = true;
  // bool found_ik = kinematic_state->setFromIK(joint_model_group, desired_pose,
  //                                            0.1, constraint_fn, options);

  bool found_ik =
      kinematic_state->setFromIK(joint_model_group, desired_pose, 0.1,
                                 moveit::core::GroupStateValidityCallbackFn(),
                                 kinematics::KinematicsQueryOptions());

  // Check if IK solution was found
  if (!found_ik)
  {
    return std::nullopt;
  }

  // Extract the IK solution
  JointArray joints_solution;
  std::vector<double> joints_solution_vec;
  kinematic_state->copyJointGroupPositions(joint_model_group,
                                           joints_solution_vec);
  // Convert joints_solution_vec to joint_solution array
  std::copy(joints_solution_vec.begin(), joints_solution_vec.end(),
            joints_solution.begin());

  return joints_solution;
}

void OpwSolver::set_tool_frame(const Eigen::Matrix4d& tool_frame)
{
  tool_frame_ = tool_frame;
}

void OpwSolver::update_opw_params()
{
  this->za6_opw_params_ = make_za6<double>();
}

std::optional<std::tuple<uint8_t, int>>
OpwSolver::joints_to_arm_config(const JointArray& joints) const
{
  Eigen::Transform<double, 3, Eigen::Isometry> flange_pose_eigen =
      opw_kinematics::forward(za6_opw_params_, joints);

  std::optional<std::array<JointArray, 8>> opw_candidates =
      get_all_ik(flange_pose_eigen);

  if (!opw_candidates.has_value())
  {
    ROS_WARN("NO OPW CANDIDATES FOUND");
    return std::nullopt;
  }

  double lowest_cost = std::numeric_limits<double>::max();
  int best_id = -1;
  int best_offset = 0;

  for (int i = 0; i < int(opw_candidates.value().size()); ++i)
  {
    if (!opw_kinematics::isValid(opw_candidates.value()[i]) ||
        !is_solution_within_bounds(opw_candidates.value()[i]))
    {
      continue;  // Skip to the next iteration if the candidate is not valid
    }
    for (auto offset_index : { -1, 0, 1 })
    {
      auto candidate_opw_solution = opw_candidates.value()[i];
      candidate_opw_solution[5] += 2 * M_PI * offset_index;

      if (abs(candidate_opw_solution[5]) > 2 * M_PI)
      {
        continue;
      }

      double current_cost = distance(joints, candidate_opw_solution);
      if (current_cost < lowest_cost)
      {
        lowest_cost = current_cost;
        best_id = i;
        best_offset = offset_index;
      }
    }
  }
  if (best_id == -1)
  {
    ROS_WARN("NO VALID SOLUTIONS FOUND");
    return std::nullopt;
  }
  return { { best_id, best_offset } };
}

std::optional<geometry_msgs::Pose>
OpwSolver::get_end_effector_pose(const JointArray& joints) const
{
  // 1. Obtain the current robot state and joint model group
  moveit::core::RobotStatePtr robot_state =
      psm_->getStateMonitor()->getCurrentState();
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
