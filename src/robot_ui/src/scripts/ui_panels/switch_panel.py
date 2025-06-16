#! /usr/bin/env python

import rospy
import unique_id
import constants

from robot_ui_msgs.srv import SwitchPanel, SwitchPanelRequest
from robot_ui_msgs.msg import Panels

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


class SwitchPanelsRequester:
    def __init__(self):
        self.panels_locked = False
        self.identifier = unique_id.uuid.UUID(constants.client_uuid)
        self.sos_service = None
        self.locked_topic = None

    def _on_lock_changed(self, data):
        self.panels_locked = bool(data)

    def start_node(self):
        # init a node as usual
        rospy.init_node(f"switch_panel_service_client_{constants.client_uuid}")

        # wait for this sevice to be running
        rospy.wait_for_service(constants.switch_panel_service)

        # Create the connection to the service. Remember it's a Trigger service
        self.sos_service = rospy.ServiceProxy(
            constants.switch_panel_service, SwitchPanel
        )

    def stop_node(self):
        self.sos_service.close()

        self.sos_service = None

    def __enter__(self):
        self.start_node()

        return self

    def __exit__(self, type, value, traceback):
        self.stop_node()

    def switch_panel(self, new_panel: int):
        # Create an object of the type TriggerRequest. We nned a TriggerRequest for a Trigger service
        sos = SwitchPanelRequest()
        sos.identifier = unique_id.toMsg(self.identifier)
        sos.new_panel = Panels(data=new_panel)

        # Now send the request through the connection
        result = self.sos_service(sos)

        # Done
        logger.info(
            f"Switching request {'' if result.result else 'un'}successful."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--switch", "-s", type=int)
    args = parser.parse_args()

    with SwitchPanelsRequester() as switcher:
        switcher.switch_panel(args.switch)


if __name__ == "__main__":
    main()
