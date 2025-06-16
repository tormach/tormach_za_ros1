import rospy
from machinetalk.protobuf.types_pb2 import (
    MT_EMC_OPERATOR_TEXT,
    MT_EMC_NML_TEXT,
    MT_EMC_NML_DISPLAY,
    MT_EMC_NML_ERROR,
    MT_EMC_OPERATOR_DISPLAY,
    MT_EMC_OPERATOR_ERROR,
)

from pymachinetalk.application import ApplicationError


class ErrorPublisher:
    """Base class for translating Machinetalk error messages to ROS log / error messages."""

    def __init__(
        self, service_discovery, timer_interval=0.1, status_cb=None, debug=False
    ):
        self.sd = service_discovery
        self.timer_interval = timer_interval
        self.status_cb = status_cb
        self.debug = debug

        self.error_in = ApplicationError(debug=self.debug)
        self.error_in.on_error_message_received.append(
            self._on_error_message_received
        )
        self.error_in.on_connected_changed.append(self._on_error_connected)
        self.sd.register(self.error_in)

    def _on_error_connected(self, connected):
        if self.status_cb:
            self.status_cb(connected)

    def _on_error_message_received(self, _, rx):
        if self.debug:
            print(f'received {rx}')
        switch = {
            MT_EMC_NML_TEXT: lambda note: rospy.logdebug(note),
            MT_EMC_NML_DISPLAY: lambda note: rospy.logdebug(note),
            MT_EMC_NML_ERROR: lambda note: rospy.loginfo(note),
            MT_EMC_OPERATOR_TEXT: lambda note: rospy.logwarn(note),
            MT_EMC_OPERATOR_DISPLAY: lambda note: rospy.logwarn(note),
            MT_EMC_OPERATOR_ERROR: lambda note: rospy.logerr(note),
        }
        for line in rx.note:
            switch.get(rx.type, lambda _: None)(line)
