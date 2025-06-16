import time
import threading
import rospy
from PySide6.QtCore import QCoreApplication


def waiter():
    class Waiter:
        def __init__(self):
            self._received = []
            self._messages = []
            self.condition = lambda x: False
            self._lock = threading.Lock()

        @property
        def success(self):
            with self._lock:
                return True in self._received

        @property
        def messages(self):
            with self._lock:
                return self._messages

        @property
        def received(self):
            with self._lock:
                return self._received

        def callback(self, data):
            with self._lock:
                self._messages.append(data)
                self._received.append(self.condition(data))

        def wait(self, timeout):
            timeout_t = time.time() + timeout
            QCoreApplication.processEvents()
            while (
                not rospy.is_shutdown()
                and not self.success
                and time.time() < timeout_t
            ):
                QCoreApplication.processEvents()
                time.sleep(0.1)

        def reset(self):
            with self._lock:
                self._received = []
                self._messages = []

        def __repr__(self):
            return '<Waiter: (success={}, messages={}>'.format(
                self.success, self.messages
            )

    return Waiter()
