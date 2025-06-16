import rospy
from std_msgs.msg import String
from redis_store import ConfigClient
from robot_command.interfaces import ProbeSetupInterfaceSingleton


class JogFrameServer:
    PLANNING_FRAME_TOPIC = 'jog_arm_server/planning_frame'
    COMMAND_FRAME_TOPIC = 'jog_arm_server/command_frame'
    USER_FRAMES_FRAME_TOPIC = 'user_frames/active_frame'
    USE_TOOL_FRAME_PARAM = 'user_config/jog/tool_frame'
    DEFAULT_WAIT_TIMEOUT_S = 30.0
    _UPDATE_FRAME_DELAY_S = 0.1

    def __init__(
        self,
        default_planning_frame='world',
        default_command_frame='world',
        tool_command_frame='tool0',
    ):
        self.default_planning_frame = default_planning_frame
        self.default_command_frame = default_command_frame
        self.tool_command_frame = tool_command_frame
        self._active_user_frame_frame = default_planning_frame
        self._probe = ProbeSetupInterfaceSingleton()

        self._config = ConfigClient(subscribe=True)
        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        self._config.wait_for_service(timeout=wait_timeout_s)
        self._config.on_update_received.append(self._on_config_update_received)

        self._planning_frame_pub = rospy.Publisher(
            self.PLANNING_FRAME_TOPIC, String, latch=True, queue_size=1
        )
        self._command_frame_pub = rospy.Publisher(
            self.COMMAND_FRAME_TOPIC, String, latch=True, queue_size=1
        )

        self._subs = [
            rospy.Subscriber(
                self.USER_FRAMES_FRAME_TOPIC,
                String,
                self._on_user_frame_frame_received,
            )
        ]
        # automatically update frames after startup
        # needs to be delayed in noetic to prevent race condition
        rospy.Timer(
            rospy.Duration.from_sec(self._UPDATE_FRAME_DELAY_S),
            lambda _: self._update_frames(),
            oneshot=True,
        )

    def stop(self):
        for sub in self._subs:
            sub.unregister()
        self._config.stop()

    def _on_user_frame_frame_received(self, msg):
        self._active_user_frame_frame = msg.data
        self._update_frames()

    def _on_config_update_received(self, key, _value):
        if key != self.USE_TOOL_FRAME_PARAM:
            return
        else:
            self._update_frames()

    def _update_frames(self):
        use_tool_frame = self._config.get_param(self.USE_TOOL_FRAME_PARAM)
        if use_tool_frame:
            self._planning_frame_pub.publish(
                String(self.default_planning_frame)
            )
            self._command_frame_pub.publish(String(self.tool_command_frame))
        else:
            self._planning_frame_pub.publish(
                String(self._active_user_frame_frame)
            )
            self._command_frame_pub.publish(String(self.default_command_frame))
