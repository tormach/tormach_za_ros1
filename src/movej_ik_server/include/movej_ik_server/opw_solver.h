#include <optional>
#include <vector>
#include <tuple>

#include <ros/ros.h>
#include <std_msgs/String.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_eigen/tf2_eigen.h>
#include <geometry_msgs/Pose.h>
#include <optional>

// required for interpolation
#include <geometry_msgs/Pose.h>
#include <tf2/LinearMath/Transform.h>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>

#include <geometry_msgs/TransformStamped.h>
#include <moveit/robot_state/robot_state.h>
#include <moveit/planning_scene_monitor/planning_scene_monitor.h>
#include <moveit/robot_model/joint_model_group.h>

#include <opw_kinematics/opw_kinematics.h>
#include "opw_kinematics/opw_utilities.h"

#include <movej_ik_server_msgs/IKSolverError.h>
#include <movej_ik_server_msgs/IKSolverWarning.h>

#include "movej_ik_server/trpl_pose.h"

constexpr int JOINTS_SIZE = 6;
using JointArray = std::array<double, JOINTS_SIZE>;
using namespace movej_ik_server_msgs;

/**
 * @class ConfigConstraint
 * @brief Stores configuration constraints used in the inverse kinematics
 * solution search for a 6-DOF manipulator.
 */
// struct ConfigConstraint
// {
//   std::optional<int> config;
//   std::optional<int> rev_count;

//   ConfigConstraint() = default;
//   ConfigConstraint(std::optional<int> config, std::optional<int> rev_count)
//     : config(config), rev_count(rev_count)
//   {
//   }
//   ConfigConstraint(std::optional<int> config) : config(config)
//   {
//   }
// };

struct ConfigConstraint
{
  std::vector<int> config = { 0, 1, 2, 3, 4, 5, 6, 7 };
  std::vector<int> rev_count = { -1, 0, 1 };

  std::vector<int> resolve_mask(uint8_t arm_config_mask) const
  {
    std::vector<int> mask;
    for (int i = 0; i < 8; ++i)
    {
      if (arm_config_mask & (1 << i))
      {
        mask.push_back(i);
      }
    }
    return mask;
  }

  ConfigConstraint() = default;
  explicit ConfigConstraint(uint8_t arm_config_mask)
  {
    config = resolve_mask(arm_config_mask);
  }
  explicit ConfigConstraint(uint8_t arm_config_mask, int rev_count)
    : rev_count({ rev_count })
  {
    config = resolve_mask(arm_config_mask);
  }
  explicit operator bool() const
  {
    return !config.empty() && !rev_count.empty();
  }
};

/**
 * @class IKSolution
 * @brief Stores inverse kinematics solution of a 6-DOF manipulator.
 */
struct IKSolution
{
  IKSolution() = default;

  explicit IKSolution(int err_code)
  {
    error_codes.push_back(err_code);
  };

  explicit IKSolution(const int err_code, const std::vector<int>& warning_codes)
    : warning_codes(warning_codes)
  {
    error_codes.push_back(err_code);
  };

  bool is_valid = false;  // consider removal
  std::optional<bool> is_user_specification_coherent;
  bool has_cache = false;

  JointArray opw;
  JointArray bioik;
  int arm_config = -1;
  int rev_count = -1;

  std::vector<int> error_codes;
  std::vector<int> warning_codes;

  explicit operator bool() const
  {
    return error_codes.empty();
  }

  void add_error_code(const int code)
  {
    if (code > 100)
    {
      ROS_ERROR("IKSolution::add_error_code: code %d is not an error code",
                code);
      return;
    }
    error_codes.push_back(code);
  }
  void add_warning_code(const int code)
  {
    if (code < 100)
    {
      ROS_ERROR("IKSolution::add_warning_code: code %d is not a warning code",
                code);
      return;
    }
    warning_codes.push_back(code);
  }
};

/**
 * @class OpwSolver
 * @brief Provides inverse kinematics (IK) solutions for a 6-DOF manipulator.
 *
 * @details Uses OPW Kinematics (analytical solution) and BioIK (numerical
 * solution) to find arm configurations and joint values for a given Cartesian
 * pose. and accomodate for robot model inaccuracies (quasi-spherical wrist
 * structure). Depends on MoveIt for robot model and planning scene.
 */
class OpwSolver
{
public:
  OpwSolver();

  /**
   * @brief Constructor.
   * @param psm A pointer to MoveIt planning scene monitor.
   */
  explicit OpwSolver(planning_scene_monitor::PlanningSceneMonitorPtr psm);

  // std::optional<std::tuple<std::vector<int>, std::vector<int>>>
  // create_candidate_configs(const ConfigConstraint constraint) const;

  /**
   * @brief Check if given joint values satisfy the robot's joint limits.
   * @param joints The joint values to check [rad].
   * @return True if the joint values are within the joint limits, false
   * otherwise.
   */
  bool is_solution_within_bounds(const JointArray& solution) const;

  /**
   * @brief Check if opw_kinematics shoulder configuration satisfies convention
   * used by FANUC.
   * @param solution robot joint values [rad].
   * @return True if conventions concurr.
   *
   * @details FANUC assumes shoulder "T" or configuration when end effector
   * point is in front of the z1 axis. OPW assumes shoulder "T" when wrist
   * center point is in front of the z1 axis. There are poses where one of these
   * points is in front of the z1 axis and the other is not. This method detects
   * such cases and modifies the opw_kinematics solution to match FANUC
   * convention.
   * @todo consider modifying opw_kinematics package logic
   */
  bool is_shoulder_config_valid(const JointArray& solution) const;

  /**
   * @brief Run iterative BIoIK solver to find joint values for a given pose.
   * @param new_seed The seed joint values for the iterative solver [rad].
   * @param desired_pose The Cartesian pose to find joint values for.
   * @param .
   * @return joints_solution The joint values if a solution was found,
   * std::nullopt otherwise.
   */
  std::optional<JointArray> iterative_ik(
      const JointArray new_seed, const Eigen::Isometry3d desired_pose) const;

  /**
   * @brief Get all analytical solutions for a spherical-wrist manipulator.
   * @param pose The Cartesian pose to find joint values for.
   * @return sols The joint values solutions [rad].
   */
  std::optional<std::array<JointArray, 8>>
  get_all_ik(const Eigen::Isometry3d& pose) const;

  /**
   * @brief Get a scalar joint travel cost between two robot joint poses.
   * @param a first robot joint pose [rad].
   * @param b second robot joint pose [rad].
   * @return cost absolute scalar value [rad].
   * @todo consider using different cost factors for different joints
   */
  double distance(const JointArray& a, const JointArray& b) const;

  /**
   * @brief Get the IK solution with joint values that are the closest to the
   * current robot joint pose.
   * @param seed_joints the reference pose (usually the current robot joints
   * pose).
   * @param pose the goal pose to solve IK for.
   * @param constraint ConfigConstraint restricts the closest IK search to a
   * desired arm configuration and/or desired J6 revolution count.
   * @return IK solution object with joint values, arm
   * configuration, and potential error messages.
   * @todo discuss the possible need for caching these moves
   */
  IKSolution closest_joint_pose(const JointArray& seed_joints,
                                const geometry_msgs::Pose& pose,
                                const ConfigConstraint constraint) const;

  /**
   * @brief Get the closest IK solution to a specified start joint pose
   * option: restrict the closest search to revolution count for a specified arm
   * configuration.
   * @param current_joints start joint pose of the move.
   * @param current_pose start end-effector pose of the move.
   * @param goal_pose final end-effector pose of the move.
   * @param goal_config_constraing configurations allowed for closest search.
   * @return IKSolution object with solution data.
   * @todo discuss the solutoin caching for these moves
   */
  IKSolution solve_closest_ik(
      const JointArray& current_joints, const geometry_msgs::Pose& current_pose,
      const geometry_msgs::Pose& goal_pose,
      const ConfigConstraint& goal_config_constraint) const;

  /**
   * @brief Get the IK solution for a specified arm configuration and J6
   * revolution count.
   * @param pose trpl pose to solve IK for.
   * @return IKSolution object with solution data.
   * @todo discuss the solutoin caching for these moves
   */
  IKSolution solve_user_ik(const TrplPose& pose) const;

  /**
   * @brief Get the IK solution for a specified arm configuration and J6
   * revolution count when previous IK result is present.
   * @param pose TRPL Pose to solve IK for.
   * @return IKSolution object with solution data.
   * @todo discuss the solutoin caching for these moves
   */
  IKSolution solve_user_ik_cache(const TrplPose& pose) const;

  /**
   * @brief Get the IK solution for a specified arm configuration and J6
   * revolution count when previous IK result is NOT present.
   * @param pose TRPL Pose to solve IK for.
   * @return IKSolution object with solution data.
   * @todo discuss the solutoin caching for these moves
   */
  IKSolution solve_user_ik_nocache(const TrplPose& pose) const;

  /**
   * @brief Set the tool frame matrix (used when the frame changes in ROS).
   * @param tool_frame the new tool frame matrix.
   */
  void set_tool_frame(const Eigen::Matrix4d& tool_frame);

  /**
   * @brief Initialize ZA6 OPW model parameters.
   * @todo initialize from ROS parameters
   */
  template <typename T>
  opw_kinematics::Parameters<T> make_za6();

  /**
   * @brief Reorder the opw_kinematics solutions to match FANUC conventions.
   * Eliminates discrepancies between FANUC convention for shoulder config.
   * @param sols the opw_kinematics solutions to reorder.
   */
  void reorder_shoulder_solutions(std::array<JointArray, 8>& sols) const;

  /**
   * @brief Check if wrist J5 joint is very close to 0 deg value.
   * Singularities affect convergence of solver and cause discrepancies between
   * Analytical and Numerical IK solutions for our different models.
   * @param joints the JointArray of robot joint positions.
   */
  bool is_wrist_near_singularity(const JointArray& joints) const;

  bool is_opw_bioik_mismatch_fatal(const IKSolution& solution) const;

  void update_opw_params();

  std::optional<geometry_msgs::Pose>
  get_end_effector_pose(const JointArray& joints) const;

  std::optional<std::tuple<uint8_t, int>>
  joints_to_arm_config(const JointArray& joints) const;

  opw_kinematics::Parameters<double> za6_opw_params_;

private:
  const int min_rev_count = -1;
  const int max_rev_count = 1;
  // const moveit::core::JointModelGroup* joint_model_group_;
  // robot_state::RobotStatePtr current_state_;
  planning_scene_monitor::PlanningSceneMonitorPtr psm_;
  const robot_model::RobotModelConstPtr robot_model_;
  Eigen::Matrix4d tool_frame_;
  bool solver_switch;
};
