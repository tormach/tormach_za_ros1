#! /usr/bin/env python

import rospy
import unique_id
import constants
from robot_ui_msgs.srv import LockPanel, LockPanelRequest

# from robot_ui_msgs.msg import Panels
from std_msgs.msg import Bool

import rosgraph.roslogging as _rl
import rospy.impl.rosout as _ro

import argparse
import logging
from pathlib import Path

logger = logging.getLogger(f"{Path(__file__).name}")
logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logging.root.setLevel(logging.INFO)

logger.addHandler(_rl.RosStreamHandler())
logger.addHandler(_ro.RosOutHandler())


class LockPanelsRequester:
    def __init__(self):
        self.panels_locked = False
        self.identifier = unique_id.uuid.UUID(constants.client_uuid)
        self.sos_service = None
        self.locked_topic = None

    def _on_lock_changed(self, data):
        self.panels_locked = bool(data)

    def start_node(self):
        # init a node as usual
        rospy.init_node(f"lock_panel_service_client_{constants.client_uuid}")

        # wait for this sevice to be running
        rospy.wait_for_service(constants.lock_panel_service)

        # Create the connection to the service. Remember it's a Trigger service
        self.sos_service = rospy.ServiceProxy(
            constants.lock_panel_service, LockPanel
        )
        self.locked_topic = rospy.Subscriber(
            constants.panels_locked_topic, Bool, self._on_lock_changed
        )

    def stop_node(self):
        self.sos_service.close()
        self.locked_topic.unregister()

        self.sos_service = None
        self.locked_topic = None

    def __enter__(self):
        self.start_node()

        return self

    def __exit__(self, type, value, traceback):
        self.stop_node()

    def lock_panels(self, lock: bool):
        # Create an object of the type TriggerRequest. We nned a TriggerRequest for a Trigger service
        sos = LockPanelRequest()
        sos.identifier = unique_id.toMsg(self.identifier)
        sos.lock = lock

        # Now send the request through the connection
        result = self.sos_service(sos)

        # Done
        logger.info(
            f"Locking request {'' if result.result else 'un'}successful."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", "-l", action="store_true", default=False)
    args = parser.parse_args()

    with LockPanelsRequester() as locker:
        locker.lock_panels(args.lock)


if __name__ == "__main__":
    main()
