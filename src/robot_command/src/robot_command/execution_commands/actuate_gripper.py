import contextlib
import rospy

from .constants import SYNC_TIME
from ..program_interpreter import InterpreterProcess
from ..program_interpreter.interpreter import ProgramPause, ProgramExit
from ..rpl import Command
from ..interfaces import GripperInterfaceSingleton
from ..rpl.exceptions import ActuateGripperError


class ActuateGripper(Command):
    name = 'actuate_gripper'

    def __init__(self, position: float, effort: float = 0.2, wait: bool = True):
        """
        Actuate the gripper to a given position.

        :param position: Target gripper position in range 0.0 to 1.0.
        :param effort: Effort for the actuation in range 0.0 to 1.0.
        :param wait: Wait for the gripper to reach the target position.

        **Examples**

        .. code-block:: python

            actuate_gripper(0.5) # actuate to 50% position
            actuate_gripper(1.0, 0.3) # actuate to 100% position with 30% effort
            actuate_gripper(0.0, wait=True) # actuate to 0% position and wait for completion
        """
        super().__init__()

        self._verify_arguments(effort, position, wait)

        self._gripper = GripperInterfaceSingleton()
        if not self._gripper.configured:
            raise RuntimeError("No gripper configured on this system.")

        self.position = position
        self.effort = effort
        self.wait = wait

    @staticmethod
    def _verify_arguments(effort, position, wait):
        if (
            not isinstance(position, (float, int))
            or position > 1.0
            or position < 0.0
        ):
            raise TypeError(
                "Actuate gripper requires a number "
                "between 0 and 1.0 as position argument"
            )
        if not isinstance(effort, (float, int)) or effort > 1.0 or effort < 0.0:
            raise TypeError(
                "Actuate gripper requires a number "
                "between 0 and 1.0 as effort argument"
            )
        if not isinstance(wait, bool):
            raise TypeError(
                "Actuate gripper requires a boolean " "as wait argument"
            )

    def execute(self):
        rospy.logdebug(
            f'executing {self.name} command: '
            f'pos={self.position} effort={self.effort} wait={self.wait}'
        )
        while InterpreterProcess.spin_pause():
            with contextlib.suppress(ProgramPause):
                self._execute_command()
                if self.wait:
                    self._wait_until_complete()
                break

    def _execute_command(self):
        self._gripper.goto_position(
            position=self.position * 100.0,
            effort=self.effort * 100.0,
            wait=False,
        )

    def _wait_until_complete(self):
        try:
            while InterpreterProcess.spin_command():
                if not self._gripper.command_active:
                    (
                        reached,
                        effort,
                        position,
                        stalled,
                    ) = self._gripper.command_result
                    message = (
                        f"Actuate gripper reached={reached}, stalled={stalled},"
                        f" position={position}, effort={effort}"
                    )
                    if not self._gripper.success:
                        raise ActuateGripperError(message)
                    rospy.loginfo(message)
                    break
                rospy.sleep(SYNC_TIME)
        except (ProgramExit, ProgramPause) as e:
            self._gripper.stop()
            while self._gripper.command_active:
                rospy.sleep(SYNC_TIME)
            raise e

    def __str__(self):
        return (
            f'{self.name}: '
            f'pos={self.position} effort={self.effort} wait={self.wait}'
        )
