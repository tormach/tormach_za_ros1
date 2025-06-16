import rospy
import threading
import time

from pymachinetalk.application import ApplicationStatus
from ros_machinetalk_msgs.msg import (
    StatusTaskMsg,
    StatusIOMsg,
    StatusPoseMsg,
    StatusToolDataMsg,
    StatusMotionAxisMsg,
    StatusMotionMsg,
    StatusInterpMsg,
    StatusConfigMsg,
    StatusConfigAxisMsg,
    StatusMsg,
)


class StatusBase:
    """Base class for translating Machinetalk status messages into ROS
    messages
    """

    msg_type = None
    attr_type_map = []

    def status_msg(self, status_in):
        """Walk through an incoming Machinetalk message and translate
        attributes over to an outgoing ROS message
        """
        # The outgoing message object
        status_out = self.msg_type()

        def get_value(key_, val_):
            """Return a value, either a plain value or a submessage"""
            # FIXME rewrite to use the value type as the key, and get
            # rid of attr_type_map
            if key_ in self.attr_type_map:
                # A submessage
                obj = self.attr_type_map[key_]()
                return obj.status_msg(val_)
            elif (
                hasattr(val_, 'id_map')
                and len(val_.id_map) == 2
                and val_.id_map[1] == 'index'
            ):
                return val_.id_map[2]
            elif isinstance(val_, str):
                return val_
            else:
                # Plain value
                return val_

        for key in status_in.id_map.values():
            # Skip echo_serial_number attribute
            if key == 'echo_serial_number':
                continue

            # Copy the attribute value or list of values
            try:  # FIXME work around missing index in status tool_data message
                val = getattr(status_in, key)
                if isinstance(val, list):
                    # List of values
                    setattr(status_out, key, [get_value(key, v) for v in val])
                else:
                    # Simple value
                    setattr(status_out, key, get_value(key, val))
            except AttributeError:
                # print "AttributeError:  %s" % e
                pass

        return status_out


class StatusTask(StatusBase):
    msg_type = StatusTaskMsg
    constant_prefixes = ['EMC_TASK_']


class StatusPose(StatusBase):
    msg_type = StatusPoseMsg


class StatusToolData(StatusBase):
    msg_type = StatusToolDataMsg
    attr_type_map = dict(offset=StatusPose)


class StatusIO(StatusBase):
    msg_type = StatusIOMsg
    attr_type_map = dict(tool_offset=StatusPose, tool_table=StatusToolData)


class StatusMotionAxis(StatusBase):
    msg_type = StatusMotionAxisMsg


class StatusMotion(StatusBase):
    msg_type = StatusMotionMsg
    attr_type_map = dict(
        actual_position=StatusPose,
        axis=StatusMotionAxis,
        dtg=StatusPose,
        g5x_offset=StatusPose,
        g92_offset=StatusPose,
        joint_actual_position=StatusPose,
        joint_position=StatusPose,
        position=StatusPose,
        probed_position=StatusPose,
    )
    constant_prefixes = ['MOTION_']


class StatusInterp(StatusBase):
    msg_type = StatusInterpMsg
    constant_prefixes = ['EMC_TASK_', 'EMC_INTERP_', 'CANON_UNITS_']


class StatusConfigAxis(StatusBase):
    msg_type = StatusConfigAxisMsg


class StatusConfig(StatusBase):
    msg_type = StatusConfigMsg
    attr_type_map = dict(axis=StatusConfigAxis)


class Status(StatusBase):
    _topic_name = "status"

    msg_type = StatusMsg
    attr_type_map = dict(
        task=StatusTask,
        io=StatusIO,
        motion=StatusMotion,
        interp=StatusInterp,
        config=StatusConfig,
    )

    def status_msg(self, status_in):
        status_out = self.msg_type()
        for a in ('io', 'task', 'motion', 'interp', 'config'):
            setattr(
                status_out,
                a,
                self.attr_type_map[a]().status_msg(getattr(status_in, a)),
            )
        return status_out


class StatusPublisher(Status):
    def __init__(
        self,
        service_discovery,
        timer_interval=0.1,
        update_cb=None,
        status_cb=None,
        debug=False,
    ):
        self.sd = service_discovery
        self.timer_interval = timer_interval
        self.update_cb = update_cb
        self.status_cb = status_cb
        self.debug = debug

        # Set up Machinetalk
        self.status_in = ApplicationStatus(debug=self.debug)
        self.status_in.on_synced_changed.append(self._on_status_synced)
        self.sd.register(self.status_in)

        # ROS publisher
        self.publisher = rospy.Publisher(
            self._topic_name, self.msg_type, queue_size=1, latch=True
        )

    def _start_timer(self):
        self.timer = threading.Timer(self.timer_interval, self.update)
        self.timer.start()

    def _stop_timer(self):
        if getattr(self, 'timer', None):
            self.timer.cancel()
            self.timer = None

    def _on_status_synced(self, synced):
        """When synced, cyclically run update()"""
        if synced:
            rospy.loginfo(
                "Machinetalk status now synched, uri %s"
                % (self.status_in.status_uri or "NONE")
            )
            self._start_timer()
        else:
            rospy.loginfo("Machinetalk status now NOT synched")
            self._stop_timer()

        if self.status_cb:
            self.status_cb(synced)

    def update(self):
        if not self.status_in.synced:
            return

        # Write messages
        msg = self.status_msg(self.status_in)
        self.publisher.publish(msg)

        # Run external update cb
        if self.update_cb is not None:
            self.update_cb()

        # Set new timer
        self._start_timer()

    def stop(self):
        self._stop_timer()


class StatusSubscriber(Status):
    def __init__(self, uuid):
        topic_name = 'machinetalk/instance_{uuid}/{topic}'.format(
            uuid=uuid.replace('-', '_'), topic=self._topic_name
        )
        self.s = rospy.Subscriber(topic_name, self.msg_type, self._callback)
        self.msg = None

    def _callback(self, msg):
        self.msg = msg

    @property
    def task(self):
        return None if self.msg is None else self.msg.task

    @property
    def io(self):
        return None if self.msg is None else self.msg.io

    @property
    def motion(self):
        return None if self.msg is None else self.msg.motion

    @property
    def interp(self):
        return None if self.msg is None else self.msg.interp

    @property
    def config(self):
        return None if self.msg is None else self.msg.config

    @property
    def synced(self):
        return self.msg is not None

    def stop(self):
        self.s.unregister()

    def wait_for_first_update(self, timeout=10):
        start_time = time.time()
        while True:
            elapsed_time = time.time() - start_time
            if self.msg is not None:
                break
            if elapsed_time >= timeout:
                raise TimeoutError("Timeout waiting for first update")
            rospy.sleep(0.1)
