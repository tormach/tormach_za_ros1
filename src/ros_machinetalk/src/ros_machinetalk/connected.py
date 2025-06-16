import rospy
from std_msgs.msg import Bool


class ConnectedBase:
    _TOPIC_NAME = 'connected'


class ConnectedPublisher(ConnectedBase):
    def __init__(self, services):
        self._pub = rospy.Publisher(
            self._TOPIC_NAME, Bool, queue_size=1, latch=True
        )

        self._services = services
        self._status = {s: False for s in services}

    def start(self):
        self._pub.publish(False)

    def stop(self):
        self._pub.publish(False)

    def set_status(self, status, service):
        self._status[service] = status
        self._pub.publish(all(self._status.values()))


class ConnectedSubscriber(ConnectedBase):
    def __init__(self, uuid):
        topic_name = 'machinetalk/instance_{uuid}/{topic}'.format(
            uuid=uuid.replace('-', '_'), topic=self._TOPIC_NAME
        )
        self._sub = rospy.Subscriber(
            topic_name, Bool, self._on_connected_updated
        )

        self._connected = False
        # Callback called when the connected state changes, new state as argument
        self.on_connected_changed = []

    @property
    def connected(self):
        return self._connected

    def stop(self):
        self._sub.unregister()

    def _on_connected_updated(self, msg):
        self._connected = msg.data
        for cb in self.on_connected_changed:
            cb(self._connected)
