#include <ros/ros.h>
#include <tf2_ros/transform_listener.h>
#include <geometry_msgs/TransformStamped.h>
#include <iostream>

int main(int argc, char** argv)
{
  ros::init(argc, argv, "test_frame_listening");
  ros::NodeHandle nh;

  tf2_ros::Buffer tfBuffer;
  tf2_ros::TransformListener tfListener(tfBuffer);

  ros::Rate rate(20.0);  // 20 Hz, adjust as needed

  while (ros::ok())
  {
    try
    {
      geometry_msgs::TransformStamped transformStamped =
          tfBuffer.lookupTransform("world", "tool0", ros::Time(0));

      // Print the transform
      std::cout << "Translation: x: "
                << transformStamped.transform.translation.x
                << ", y: " << transformStamped.transform.translation.y
                << ", z: " << transformStamped.transform.translation.z
                << std::endl;
      std::cout << "Rotation: x: " << transformStamped.transform.rotation.x
                << ", y: " << transformStamped.transform.rotation.y
                << ", z: " << transformStamped.transform.rotation.z
                << ", w: " << transformStamped.transform.rotation.w
                << std::endl;
      std::cout << "---" << std::endl;
    }
    catch (tf2::TransformException& ex)
    {
      ROS_WARN_THROTTLE(1, "Could not transform from 'world' to 'tool0': %s",
                        ex.what());
    }

    rate.sleep();
    ros::spinOnce();
  }

  return 0;
}
