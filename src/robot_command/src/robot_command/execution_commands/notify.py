import os
from typing import Optional

import sys
import time
import rospy

from robot_command.program_interpreter import InterpreterProcess
from ..program_interpreter.interpreter import ProgramPause
from ..rpl import Command
from ..interfaces.notification_interface import (
    NotificationInterfaceSingleton,
    NotificationResponse,
)
from .constants import SYNC_TIME


class Notify(Command):
    NOTIFY_WAIT_TIME_S = 0.3

    name = 'notify'

    def __init__(
        self,
        message: str,
        warning: bool = False,
        error: bool = False,
        image_path: str = '',
        timeout: Optional[float] = None,
    ):
        """
        Creates a popup notification message on the robot UI.

        The ``message`` argument text is shown to the user.

        By default, the message is displayed as informational and thus will not
        block the program flow. The ``warning`` argument shows a warning message,
        which breaks program flow and can be declined by the operator. The ``error``
        argument shows a blocking error message, which aborts the program.

        The optional ``image_path`` argument can be used to display an informational
        image along with the message

        :param message: Message text to display in the popup.
        :param warning: Set to true if this message is a warning.
        :param error: Set to true if this message is an error message.
        :param image_path: Optional path to an image file to displayed in the popup.
        :param timeout: Optional timeout in seconds.

        **Examples**

        .. code-block:: python

            notify("Hello World!")
            notify("No part found, check the palette.", warning=True)
            notify("This should not happen.", error=True, image_path="./fatal_error.png")
        """
        super().__init__()
        self._notifications = NotificationInterfaceSingleton()

        if not isinstance(message, str):
            raise TypeError('Message text must be specified as first argument.')

        self.message = message
        self.warning = warning
        self.error = error
        self.image_path = (
            os.path.abspath(os.path.expanduser(image_path))
            if image_path
            else ''
        )
        self.timeout = timeout

    def _type_string(self):
        if self.error:
            return "error"
        elif self.warning:
            return "warning"
        else:
            return "notification"

    def execute(self) -> None:
        rospy.logdebug(
            f'executing notify: {self._type_string()} "{self.message}" "{self.image_path}" {self.timeout}'
        )
        if self.error:
            # Ignore timeouts for error dialogs
            self.timeout = None
            self._notifications.error_message(
                message=self.message, image_path=self.image_path
            )
        elif self.warning:
            self._notifications.warning_message(
                message=self.message, image_path=self.image_path
            )
        else:
            self._notifications.notification_message(
                message=self.message, image_path=self.image_path
            )
            time.sleep(self.NOTIFY_WAIT_TIME_S)
            return
        try:
            t0 = time.time()
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
                    return
                elif (
                    self.timeout is not None
                    and (time.time() - t0) > self.timeout
                ):
                    return
                time.sleep(SYNC_TIME)

        except ProgramPause as e:
            rospy.loginfo(f'Paused executing notify:  {e}')
            return  # not reachable, pause cannot be pressed with message active
        finally:
            self._notifications.deactivate_message()

    def __str__(self):
        return '{}: {} "{}" "{}"'.format(
            self.name, self._type_string(), self.message, self.image_path
        )
