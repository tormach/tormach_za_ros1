from moveit_msgs.msg import RobotTrajectory
from trajectory_msgs.msg import JointTrajectory

from .move_commands import MoveCommand
from ..program_interpreter import InterpreterProcess
from ..program_interpreter.interpreter import ProgramPause
from ..rpl import Command

import rospy


class ExecuteTrajectory(Command, MoveCommand):
    name = 'execute_trajectory'

    def __init__(
        self,
        trajectory: JointTrajectory,
        v: float = None,
        retime: bool = False,
        velocity_scale: float = 1.0,
    ):
        """
        The execute trajectory command executes a ROS JointTrajectory. Before
        running the joint trajectory, the robot moves to the start joint position
        using a joint move command.
        :param velocity_scale: move velocity scaling factor 0.0 - 1.0
        :param trajectory: a ROS joint trajectory
        :param retime: Enable retiming the trajectory to make use of the velocity scaling.

        :param v: move velocity scaling factor 0.0 - 1.0

            .. deprecated:: 3.1.1
                use velocity_scale instead
        """
        Command.__init__(self)
        MoveCommand.__init__(self)

        if v is not None:
            rospy.logwarn(
                "Argument \"v\" is deprecated, "
                "use \"velocity\" argument instead."
            )
            velocity_scale = v

        self.trajectory = trajectory
        self.velocity_scale = velocity_scale
        self.retime = retime

    def execute(self) -> None:
        self._move_to_start_point()
        self._execute_trajectory()

    def _move_to_start_point(self):
        plan = None
        target = self.trajectory.points[0].positions
        while InterpreterProcess.spin_pause():
            try:
                self._update_vel_accel(
                    accel_scale=1.0,
                    velocity_scale=self.velocity_scale,
                    use_feedrate=False,
                )
                if plan:
                    plan = self._moveit.recompute_trajectory(
                        plan,
                        self._final_accel_scale,
                        self._final_velocity_scale,
                    )
                else:
                    plan = self._plan_and_wait(
                        target, self._moveit.PTP_MOVE_PLANNER
                    )
                if plan:
                    self._execute_and_wait(plan)
                break
            except ProgramPause as e:
                rospy.loginfo(f'Paused moving to trajectory start:  {e}')
                plan = None  # Discard plan after pause

    def _execute_trajectory(self):
        plan = RobotTrajectory(joint_trajectory=self.trajectory)
        first_run = True
        while InterpreterProcess.spin_pause():
            if self.retime:
                try:
                    self._update_vel_accel(
                        accel_scale=1.0,
                        velocity_scale=self.velocity_scale,
                        use_feedrate=False,
                    )
                    if first_run:
                        plan = self._moveit.retime_trajectory(
                            plan,
                            self._final_accel_scale,
                            self._final_velocity_scale,
                        )
                        first_run = False
                    else:
                        plan = self._moveit.recompute_trajectory(
                            plan,
                            self._final_accel_scale,
                            self._final_velocity_scale,
                        )
                    self._execute_and_wait(plan)
                    break
                except ProgramPause as e:
                    rospy.loginfo(f'Paused executing trajectory:  {e}')
                    plan = None  # Discard plan after pause
            else:
                self._execute_and_wait(plan)
                break

    def __str__(self):
        return (
            f'{self.name}: total points={len(self.trajectory.points)} '
            f'v={self.velocity_scale} retime={self.retime}'
        )
