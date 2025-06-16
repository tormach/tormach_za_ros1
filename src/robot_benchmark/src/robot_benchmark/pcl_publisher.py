import rospy
from sensor_msgs.msg import PointCloud2, PointField, struct


class PclPublisher:
    PCL_TOPIC = '/ik_benchmark/result_points'

    def __init__(self, base_frame):
        self._base_frame = base_frame
        self._pcl_pub = rospy.Publisher(
            self.PCL_TOPIC, PointCloud2, queue_size=10
        )

    def shutdown(self):
        self._pcl_pub.unregister()

    def publish(self, results, publish_failed=True, publish_succeeded=True):
        rgb_points = PointCloud2()
        rgb_points.header.stamp = rospy.get_rostime()
        rgb_points.header.frame_id = self._base_frame
        rgb_points.height = 1
        rgb_points.is_dense = False
        rgb_points.is_bigendian = False
        rgb_points.fields.append(
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1)
        )
        rgb_points.fields.append(
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1)
        )
        rgb_points.fields.append(
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1)
        )
        rgb_points.fields.append(
            PointField(
                name="rgb", offset=16, datatype=PointField.FLOAT32, count=1
            )
        )
        rgb_points.point_step = 32
        rgb_points.row_step = rgb_points.point_step * rgb_points.width
        buffer = []
        count = 0
        for pose, result in results:
            if result and not publish_succeeded:
                continue
            if not (result or publish_failed):
                continue
            count += 1
            buffer.append(
                struct.pack(
                    'ffffBBBBIII',
                    pose.pose.position.x,
                    pose.pose.position.y,
                    pose.pose.position.z,
                    1.0,
                    0,
                    255 if result else 0,
                    255 if not result else 0,
                    0,
                    0,
                    0,
                    0,
                )
            )
        rgb_points.data = b"".join(buffer)
        rgb_points.width = count

        self._pcl_pub.publish(rgb_points)
