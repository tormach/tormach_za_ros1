import sys
import rospy

from robot_command.program_interpreter import InterpreterProcess
from ..program_interpreter.interpreter import ProgramPause
from ..rpl import Command
from ..interfaces.notification_interface import (
    NotificationInterfaceSingleton,
    NotificationResponse,
)
from .constants import SYNC_TIME


class Input(Command):
    name = 'input'

    def __init__(self, message: str, default: str = "", image_path: str = ""):
        """
        Creates a popup input dialog on the robot UI.

        The ``message`` argument text is shown to the user.

        The ``option`` default argument can be used to set the default input text.

        The optional ``image_path`` argument can be used to display an informational
        image along with the message.

        :param message: Message text to display in the popup.
        :param default: The default input value.
        :param image_path: Optional path to an image file to displayed in the popup.
        :return: User input text or None if cancelled

        **Examples**

        .. code-block:: python

            user_input = input("How many parts should be made?", default="5")
            n = int(user_input)
        """
        super().__init__()
        self._notifications = NotificationInterfaceSingleton()

        if not isinstance(message, str):
            raise TypeError('Message text must be specified as first argument.')

        self.message = message
        self.default = default
        self.image_path = image_path

    def execute(self) -> float:
        rospy.logdebug(
            'executing input: "{}" {} "{}"'.format(
                self.message, self.default, self.image_path
            )
        )
        self._notifications.user_input_message(
            message=self.message,
            default=self.default,
            image_path=self.image_path,
        )
        try:
            while InterpreterProcess.spin_command():
                if (
                    self._notifications.message_response
                    == NotificationResponse.ABORT
                ):
                    raise sys.exit(0)
                elif (
                    self._notifications.message_response
                    == NotificationResponse.OK
                ):
                    return self._notifications.user_input
                rospy.sleep(SYNC_TIME)
        except ProgramPause as e:
            rospy.loginfo(f'Paused reading input dialog:  {e}')
            return  # not reachable, pause cannot be pressed with message active
        finally:
            self._notifications.deactivate_message()

    def __str__(self):
        return '{}: "{}" {} "{}"'.format(
            self.name, self.message, self.default, self.image_path
        )
