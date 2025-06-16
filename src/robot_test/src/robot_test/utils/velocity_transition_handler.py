import rospy
from std_msgs.msg import Float64


class VelocityTransitionHandler:
    def __init__(self):
        # Check if ROS node is already initialized
        if not rospy.core.is_initialized():
            # Initialize ROS node if not already done
            rospy.init_node('velocity_transition_node', anonymous=True)

        # Create a ROS publisher
        self.pub = rospy.Publisher(
            '/velocity_transition_time', Float64, queue_size=10
        )

    def set_transition_time(self, float_value):
        # Validate the float value
        if float_value < 0.0:
            print("Error: Value must be greater than or equal to 0.0")
            return

        # Create a message object for the ROS topic
        msg = Float64()
        msg.data = float_value

        # Publish the value to the ROS topic
        self.pub.publish(msg)
        print(f"Published value {float_value} to /velocity_transition_time")


if __name__ == '__main__':
    # Command-line argument simulation for testing; Replace this part as per your need
    float_value = float(input("Enter a float value: "))

    # Create an instance of the class
    velocity_trans = VelocityTransitionHandler()

    # Call the method to set velocity transition time
    velocity_trans.set_velocity_transition_time(float_value)
