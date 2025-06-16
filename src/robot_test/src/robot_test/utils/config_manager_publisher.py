#!/usr/bin/env python3

import rospy
from redis_store_msgs.msg import ParamUpdate
import threading
import time

# TODONAME


class ConfigManagerPublisher:
    """
    Publish a parameter update message to the config manager
    Allow for async delay in publishing the message
    Useful for simulating user actions in UI
    e.g. user changes velocity scale in the middle of a move
    """

    CONFIG_MANAGER_UPDATE_TOPIC = '/config_manager/update'
    CONFIG_MANAGER_NODE = 'config_manager_publisher'

    def __init__(self, logging=False):
        # Initialize ROS node only if it hasn't been initialized yet
        if not rospy.get_published_topics():
            rospy.init_node(self.CONFIG_MANAGER_NODE, anonymous=True)

        self.publisher_ = rospy.Publisher(
            self.CONFIG_MANAGER_UPDATE_TOPIC, ParamUpdate, queue_size=10
        )

        # TODOCHAT: can we better control logging?
        self.logging_ = logging

    def delayed_publish(self, param_name, param_value, delay):
        # throw an exception if the param_value is not a string

        # Sleep for the required delay time
        if delay > 0:
            time.sleep(delay)

        # Create the message object and fill in the details
        update_msg = ParamUpdate()
        update_msg.param_name = param_name
        update_msg.param_value = param_value

        # Publish the message
        self.publisher_.publish(update_msg)

        if self.logging_:
            rospy.loginfo(
                f"Published {param_name} with value {param_value} after {delay} seconds"
            )

    def publish_update(self, param_name, param_value, delay=0):
        # throw an exception if the param_value is not a string
        # TODOCHAT: shall I throw an exception here, or wait until further down?
        if not isinstance(param_value, str):
            raise TypeError("param_value must be a string")

        if delay > 0:
            # Use threading to delay the message publishing
            threading.Thread(
                target=self.delayed_publish,
                args=(param_name, param_value, delay),
            ).start()
        else:
            # Immediate publish if no delay
            self.delayed_publish(param_name, param_value, delay=0)


if __name__ == '__main__':
    try:
        config_manager = ConfigManagerPublisher(logging=True)
        rate = rospy.Rate(1)  # 1 Hz

        while not rospy.is_shutdown():
            config_manager.publish_update(
                "user_config/feedrate", "0.2", delay=1.0
            )
            rate.sleep()

    except rospy.ROSInterruptException:
        pass
