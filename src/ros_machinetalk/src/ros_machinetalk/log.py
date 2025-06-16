import rospy
from machinetalk.protobuf.types_pb2 import MsgLevel
from pymachinetalk.application import ApplicationLog
from pymachinetalk.application.log import ApplicationLogMessage


class LogPublisher:
    """Base class for translating Machinetalk RT log messages to ROS log messages."""

    def __init__(
        self, service_discovery, timer_interval=0.1, log_cb=None, debug=False
    ):
        self.sd = service_discovery
        self.timer_interval = timer_interval
        self.log_cb = log_cb
        self.debug = debug

        self.log_in = ApplicationLog(debug=self.debug)
        self.log_in.on_message_received.append(self._on_log_message_received)
        self.log_in.on_connected_changed.append(self._on_log_connected)
        self.sd.register(self.log_in)

    def _on_log_connected(self, connected):
        if self.log_cb:
            self.log_cb(connected)

    def _on_log_message_received(self, _, rx: ApplicationLogMessage):
        if self.debug:
            print(f'received log message {rx}')
        # should use rx.timestamp, not sure how to pass to ros
        switch = {
            MsgLevel.RTAPI_MSG_DBG: lambda text: rospy.logdebug(text),
            MsgLevel.RTAPI_MSG_INFO: lambda text: rospy.loginfo(text),
            MsgLevel.RTAPI_MSG_WARN: lambda text: rospy.logwarn(text),
            MsgLevel.RTAPI_MSG_ERR: lambda text: rospy.logerr(text),
        }

        switch.get(rx.level, lambda _: None)(rx.text)
