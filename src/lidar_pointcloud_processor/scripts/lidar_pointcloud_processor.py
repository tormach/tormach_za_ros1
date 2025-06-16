#!/usr/bin/env python3
# FILE: lidar_pointcloud_processor.py

import rospy
import numpy as np
import matplotlib
import os

import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation, Slerp
from scipy.spatial import ConvexHull
from sensor_msgs.msg import PointCloud
from geometry_msgs.msg import PoseStamped, Pose
from std_msgs.msg import Bool
from lidar_pointcloud_processor_msgs.srv import (
    ProcessLidarData,
    ProcessLidarDataResponse,
    EstimateLidarLine,
    EstimateLidarLineResponse,
    RefineLidarLengthDisplacement,
    RefineLidarLengthDisplacementResponse,
    PurgeLidarData,
    PurgeLidarDataResponse,
    FindHighestLidarZ,
    FindHighestLidarZResponse,
)

from sklearn.cluster import DBSCAN
from datetime import datetime

from lidar_pointcloud_processor_msgs.srv import (
    FindClosestLidarRectangle,
    FindClosestLidarRectangleResponse,
)
from scipy.optimize import minimize

matplotlib.use('Agg')  # Use Agg backend for non-interactive plotting


# Import functions from icp_test.py
def transform_points(points, tx, ty, theta):
    """Vectorized point transformation."""
    cos_theta, sin_theta = np.cos(theta), np.sin(theta)
    rotation_matrix = np.array(
        [[cos_theta, -sin_theta], [sin_theta, cos_theta]]
    )
    return np.dot(points - [tx, ty], rotation_matrix.T)


def cost_function_fixed_size(params, points, width, height):
    """Cost function for fixed-size rectangle fitting."""
    tx, ty, theta = params

    # Transform points to rectangle's coordinate system
    transformed_points = transform_points(points, tx, ty, theta)

    # Calculate distances to rectangle edges
    dx = np.maximum(np.abs(transformed_points[:, 0]) - width / 2, 0)
    dy = np.maximum(np.abs(transformed_points[:, 1]) - height / 2, 0)

    # Calculate point-to-rectangle distances
    distances = np.sqrt(dx**2 + dy**2)

    # Sum of distances
    return np.sum(distances)


def rotation_matrix_to_quaternion(matrix):
    """
    Convert a rotation matrix to a quaternion.
    This function works with older versions of SciPy that don't have Rotation.from_matrix().
    """
    trace = np.trace(matrix)
    if trace > 0:
        S = np.sqrt(trace + 1.0) * 2
        qw = 0.25 * S
        qx = (matrix[2, 1] - matrix[1, 2]) / S
        qy = (matrix[0, 2] - matrix[2, 0]) / S
        qz = (matrix[1, 0] - matrix[0, 1]) / S
    elif matrix[0, 0] > matrix[1, 1] and matrix[0, 0] > matrix[2, 2]:
        S = np.sqrt(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2]) * 2
        qw = (matrix[2, 1] - matrix[1, 2]) / S
        qx = 0.25 * S
        qy = (matrix[0, 1] + matrix[1, 0]) / S
        qz = (matrix[0, 2] + matrix[2, 0]) / S
    elif matrix[1, 1] > matrix[2, 2]:
        S = np.sqrt(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2]) * 2
        qw = (matrix[0, 2] - matrix[2, 0]) / S
        qx = (matrix[0, 1] + matrix[1, 0]) / S
        qy = 0.25 * S
        qz = (matrix[1, 2] + matrix[2, 1]) / S
    else:
        S = np.sqrt(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1]) * 2
        qw = (matrix[1, 0] - matrix[0, 1]) / S
        qx = (matrix[0, 2] + matrix[2, 0]) / S
        qy = (matrix[1, 2] + matrix[2, 1]) / S
        qz = 0.25 * S
    return np.array([qx, qy, qz, qw])


class ROSPointCloudProcessor:
    def __init__(self):
        rospy.init_node('pointcloud_processor')

        self.pointclouds = []
        self.poses = []
        self.lidar_status = False
        self.pointcloud_count = 0
        self.total_pointcloud_count = 0
        self.lidar_status_ranges = []
        self.current_range_start = None
        self.first_line_point = None

        self.temp_pointcloud = None
        self.temp_pointcloud_received = False

        # Subscribe to topics
        rospy.Subscriber('/lidar_status', Bool, self.lidar_status_callback)
        rospy.Subscriber('/point_cloud', PointCloud, self.pointcloud_callback)
        rospy.Subscriber(
            '/pose_states_throttle', PoseStamped, self.pose_callback
        )

        # Create services
        rospy.Service(
            'process_pointclouds',
            ProcessLidarData,
            self.process_pointclouds_callback,
        )
        rospy.Service('find_line', EstimateLidarLine, self.find_line)
        rospy.Service(
            'refine_length_displacement',
            RefineLidarLengthDisplacement,
            self.refine_length_displacement,
        )
        rospy.Service(
            'purge_lidar_data', PurgeLidarData, self.purge_lidar_data_callback
        )
        rospy.Service(
            'find_highest_cloud_point',
            FindHighestLidarZ,
            self.find_highest_cloud_point_callback,
        )

        rospy.Service(
            'find_closest_rectangle',
            FindClosestLidarRectangle,
            self.find_closest_rectangle_callback,
        )

    def lidar_status_callback(self, msg):
        if msg.data and not self.lidar_status:
            self.current_range_start = rospy.Time.now()
        elif not msg.data and self.lidar_status:
            self.lidar_status_ranges.append(
                (self.current_range_start, rospy.Time.now())
            )
            self.current_range_start = None
        self.lidar_status = msg.data

    # def pointcloud_callback(self, msg):
    # self.total_pointcloud_count += 1
    # if self.lidar_status:
    # self.pointclouds.append((rospy.Time.now(), msg))
    # self.pointcloud_count += 1

    def pointcloud_callback(self, msg):
        self.total_pointcloud_count += 1
        if self.lidar_status:
            if not self.temp_pointcloud_received:
                self.temp_pointcloud = msg
                self.temp_pointcloud_received = True
            self.pointclouds.append((rospy.Time.now(), msg))
            self.pointcloud_count += 1

    def pose_callback(self, msg):
        self.poses.append((rospy.Time.now(), msg))

    def purge_lidar_data_callback(self, req):
        self.purge_data()
        return PurgeLidarDataResponse(True)

    def purge_data(self):
        self.pointclouds = []
        self.poses = []
        self.pointcloud_count = 0
        self.total_pointcloud_count = 0
        self.lidar_status_ranges = []
        self.first_line_point = None
        rospy.loginfo("Stored pointcloud data has been purged.")

    def interpolate_pose(self, target_time):
        if not self.poses:
            return None

        nearest_poses = sorted(
            self.poses, key=lambda x: abs((x[0] - target_time).to_sec())
        )[:2]

        if len(nearest_poses) < 2:
            return None

        t0, pose0 = nearest_poses[0]
        t1, pose1 = nearest_poses[1]

        if target_time < t0 or target_time > t1:
            return (
                np.array(
                    [
                        pose0.pose.position.x,
                        pose0.pose.position.y,
                        pose0.pose.position.z,
                    ]
                ),
                np.array(
                    [
                        pose0.pose.orientation.x,
                        pose0.pose.orientation.y,
                        pose0.pose.orientation.z,
                        pose0.pose.orientation.w,
                    ]
                ),
            )

        p0 = np.array(
            [
                pose0.pose.position.x,
                pose0.pose.position.y,
                pose0.pose.position.z,
            ]
        )
        p1 = np.array(
            [
                pose1.pose.position.x,
                pose1.pose.position.y,
                pose1.pose.position.z,
            ]
        )

        q0 = np.array(
            [
                pose0.pose.orientation.x,
                pose0.pose.orientation.y,
                pose0.pose.orientation.z,
                pose0.pose.orientation.w,
            ]
        )
        q1 = np.array(
            [
                pose1.pose.orientation.x,
                pose1.pose.orientation.y,
                pose1.pose.orientation.z,
                pose1.pose.orientation.w,
            ]
        )

        t = (target_time - t0).to_sec() / (t1 - t0).to_sec()
        t = max(0, min(t, 1))

        p = p0 + t * (p1 - p0)

        key_rots = Rotation.from_quat([q0, q1])
        key_times = [0, 1]
        slerp = Slerp(key_times, key_rots)
        q = slerp([t])[0].as_quat()

        return p, q

    def interpolate_pointclouds_to_common_frame(self, min_scan_displacement):
        rospy.loginfo("Interpolating pointclouds to common frame...")
        rospy.loginfo(
            f"Total number of /point_cloud messages: {self.total_pointcloud_count}"
        )
        rospy.loginfo(
            f"Number of /point_cloud messages that met the condition (lidar_status == True): {self.pointcloud_count}"
        )

        interpolated_points = []

        last_valid_position = None
        skipped_frames = 0

        for t, pointcloud in self.pointclouds:
            pose = self.interpolate_pose(t)
            if pose is None:
                rospy.logwarn("Skipping a pointcloud due to missing pose data")
                continue

            position, orientation = pose
            rotation = Rotation.from_quat(orientation)

            # ignore lidar frames that are too close (linear distance based) to the previous one
            if (
                last_valid_position is not None
                and np.linalg.norm(position - last_valid_position)
                < min_scan_displacement
            ):
                skipped_frames += 1
                continue

            points = np.array(
                [[-point.y, 0, point.x] for point in pointcloud.points]
            )
            transformed_points = rotation.apply(points) + position

            interpolated_points.extend(transformed_points)

            last_valid_position = position

        if not interpolated_points:
            rospy.logwarn("No points found after interpolation")
            return None

        rospy.loginfo(f"There were {skipped_frames} skipped frames.")
        return np.array(interpolated_points)

    def filter_points_by_z(self, points, min_z, max_z):
        rospy.loginfo(
            f"Filtering points based on z-value range: [{min_z}, {max_z})"
        )

        filtered_points = points[
            (points[:, 2] >= min_z) & (points[:, 2] < max_z)
        ]

        if filtered_points.size == 0:
            rospy.logwarn("No points left after z-value filtering")
            return None

        return filtered_points

    @staticmethod
    def quaternion_to_rotation_matrix(q):
        """Convert a quaternion to a rotation matrix."""
        x, y, z, w = q
        return np.array(
            [
                [
                    1 - 2 * y * y - 2 * z * z,
                    2 * x * y - 2 * z * w,
                    2 * x * z + 2 * y * w,
                ],
                [
                    2 * x * y + 2 * z * w,
                    1 - 2 * x * x - 2 * z * z,
                    2 * y * z - 2 * x * w,
                ],
                [
                    2 * x * z - 2 * y * w,
                    2 * y * z + 2 * x * w,
                    1 - 2 * x * x - 2 * y * y,
                ],
            ]
        )

    def pose_to_matrix(self, pose):
        """Convert a ROS Pose message to a 4x4 transformation matrix."""
        # Extract position
        translation = np.array(
            [pose.position.x, pose.position.y, pose.position.z]
        )

        # Extract rotation
        rotation = Rotation.from_quat(
            [
                pose.orientation.x,
                pose.orientation.y,
                pose.orientation.z,
                pose.orientation.w,
            ]
        )

        # Create 4x4 homogeneous transformation matrix
        matrix = np.eye(4)
        matrix[:3, :3] = (
            rotation.as_dcm()
        )  # Use as_dcm() instead of as_matrix()
        matrix[:3, 3] = translation

        return matrix

    @staticmethod
    def ensure_closed_polygon(points):
        return (
            points
            if np.array_equal(points[0], points[-1])
            else np.vstack([points, points[0]])
        )

    @staticmethod
    def calculate_polygon_centroid(points):
        points = ROSPointCloudProcessor.ensure_closed_polygon(points)
        x, y = points[:, 0], points[:, 1]
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        cx = np.sum((x[:-1] + x[1:]) * (x[:-1] * y[1:] - x[1:] * y[:-1])) / (
            6 * area
        )
        cy = np.sum((y[:-1] + y[1:]) * (x[:-1] * y[1:] - x[1:] * y[:-1])) / (
            6 * area
        )
        return np.array([cx, cy])

    @staticmethod
    def moment_of_inertia(polygon, mass=1):
        polygon = ROSPointCloudProcessor.ensure_closed_polygon(
            np.array(polygon)
        )
        center = ROSPointCloudProcessor.calculate_polygon_centroid(polygon)
        shifted_polygon = polygon - center
        x, y = shifted_polygon[:, 0], shifted_polygon[:, 1]
        x_prev, y_prev = np.roll(x, 1), np.roll(y, 1)
        area = 0.5 * np.abs(np.sum(x * np.roll(y, 1) - y * np.roll(x, 1)))
        Ixx = (mass / (6 * area)) * np.sum(
            (y**2 + y * y_prev + y_prev**2) * (x * y_prev - x_prev * y)
        )
        Iyy = (mass / (6 * area)) * np.sum(
            (x**2 + x * x_prev + x_prev**2) * (x * y_prev - x_prev * y)
        )
        Ixy = (mass / (24 * area)) * np.sum(
            (x * y_prev + 2 * x * y + 2 * x_prev * y_prev + x_prev * y)
            * (x * y_prev - x_prev * y)
        )
        inertia_tensor = np.array([[Ixx, -Ixy], [-Ixy, Iyy]])
        eigenvalues, eigenvectors = np.linalg.eig(inertia_tensor)
        principal_axis = eigenvectors[:, np.argmax(eigenvalues)]
        return center, principal_axis, (Ixx, Iyy, Ixy)

    @staticmethod
    def angle_with_x_axis(vector):
        return np.arctan2(vector[1], vector[0])

    def create_plot(self, X, labels, hull_data, min_z, max_z, cluster_eps):
        fig, ax = plt.subplots(figsize=(12, 8))

        unique_labels = set(labels)
        colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))

        for k, col in zip(unique_labels, colors):
            if k == -1:
                col = [0, 0, 0, 1]
            class_member_mask = labels == k
            xy = X[class_member_mask]
            ax.scatter(
                xy[:, 0],
                xy[:, 1],
                c=[col],
                label=f'Cluster {k}' if k != -1 else 'Noise',
                s=10,
            )

            if k != -1 and k in hull_data:
                data = hull_data[k]
                hull = data['hull']
                for simplex in hull.simplices:
                    ax.plot(xy[simplex, 0], xy[simplex, 1], 'k-')

                center = data['center']
                principal_axis = data['principal_axis']
                ax.plot(
                    center[0], center[1], 'ro', markersize=10
                )  # Plot centroid

                # Plot principal axis as a solid red line
                vector_length = 0.05
                normalized_principal_axis = (
                    principal_axis
                    / np.linalg.norm(principal_axis)
                    * vector_length
                )
                ax.plot(
                    [center[0], center[0] + normalized_principal_axis[0]],
                    [center[1], center[1] + normalized_principal_axis[1]],
                    color='red',
                    linewidth=2,
                )

        ax.set_title(
            f'Pointcloud Segmentation\nZ range: {min_z:.3f} to {max_z:.3f}, Cluster eps: {cluster_eps:.3f}'
        )
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.legend()
        ax.grid(True)
        ax.axis('equal')

        return fig

    def segment_objects(
        self, all_filtered_points, cluster_eps, min_z, max_z, goal_z
    ):
        # Perform DBSCAN clustering
        X = all_filtered_points[:, :2]  # Use only x and y coordinates
        dbscan = DBSCAN(eps=cluster_eps, min_samples=5)
        labels = dbscan.fit_predict(X)

        # Compute convex hulls, centroids, and inertia axes
        hull_data = {}
        object_poses = []
        cluster_points = {}
        for k in set(labels):
            if k != -1:
                cluster_mask = labels == k
                cluster_points[k] = all_filtered_points[cluster_mask]
                cluster_xy = X[cluster_mask]
                if len(cluster_xy) > 2:
                    hull = ConvexHull(cluster_xy)
                    hull_points = cluster_xy[hull.vertices]
                    center, principal_axis, moments = self.moment_of_inertia(
                        hull_points
                    )
                    angle = self.angle_with_x_axis(principal_axis)
                    hull_data[k] = {
                        'hull': hull,
                        'hull_points': hull_points,
                        'center': center,
                        'principal_axis': principal_axis,
                        'moments': moments,
                        'angle': np.degrees(angle),
                    }

                    # Create pose for the object
                    pose = Pose()
                    pose.position.x = center[0]
                    pose.position.y = center[1]

                    pose.position.z = goal_z

                    # Create rotation matrix
                    rotation_matrix = np.eye(3)
                    rotation_matrix[:2, 0] = principal_axis
                    rotation_matrix[:2, 1] = [
                        -principal_axis[1],
                        principal_axis[0],
                    ]  # Perpendicular to principal axis
                    q = rotation_matrix_to_quaternion(rotation_matrix)

                    pose.orientation.x = q[0]
                    pose.orientation.y = q[1]
                    pose.orientation.z = q[2]
                    pose.orientation.w = q[3]

                    object_poses.append(pose)

        return hull_data, object_poses, X, labels, cluster_points

    def process_pointclouds_callback(self, req):
        min_scan_displacement = rospy.get_param(
            '~min_global_scan_displacement', 0.002
        )
        interpolated_points = self.interpolate_pointclouds_to_common_frame(
            min_scan_displacement
        )

        if interpolated_points is None:
            return ProcessLidarDataResponse([], False)

        # TODO: save the pointcloud before filtering

        all_filtered_points = self.filter_points_by_z(
            interpolated_points, req.min_z, req.max_z
        )

        if all_filtered_points is None:
            return ProcessLidarDataResponse([], False)

        # Call segment_objects method
        hull_data, object_poses, X, labels, _ = self.segment_objects(
            all_filtered_points,
            req.cluster_eps,
            req.min_z,
            req.max_z,
            req.goal_z,
        )

        # Create plot
        fig = self.create_plot(
            X, labels, hull_data, req.min_z, req.max_z, req.cluster_eps
        )

        # Save plot as PNG
        save_dir = os.path.expanduser('~/lidar_objects')
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().isoformat()
        filename = f'lidar_objects_{timestamp}.png'
        filepath = os.path.join(save_dir, filename)
        fig.savefig(filepath)
        rospy.loginfo(f"Plot saved as {filepath}")

        # Close the figure to free up memory
        plt.close(fig)

        # Print cluster information
        for k, data in hull_data.items():
            rospy.loginfo(f"\nCluster {k}:")
            rospy.loginfo(
                f"  Centroid: ({data['center'][0]:.4f}, {data['center'][1]:.4f})"
            )
            rospy.loginfo(
                f"  Principal Axis: [{data['principal_axis'][0]:.4f}, {data['principal_axis'][1]:.4f}]"
            )
            rospy.loginfo(f"  Angle with x-axis: {data['angle']:.2f} degrees")
            rospy.loginfo(
                f"  Moments of inertia (Ixx, Iyy, Ixy): {data['moments']}"
            )

        # Purge stored pointcloud data if requested
        if req.purge_after_processing:
            self.pointclouds = []
            self.poses = []
            self.pointcloud_count = 0
            self.total_pointcloud_count = 0
            self.lidar_status_ranges = []
            rospy.loginfo("Stored pointcloud data has been purged.")

        return ProcessLidarDataResponse(object_poses, True)

    def find_line(self, req):
        rospy.loginfo(f"Processing line with ID: {req.line_id}")

        success, average_line_point_now = self.process_line(
            req.min_z,
            req.max_z,
            req.cluster_eps,
            req.enable_plotting_data,
            req.save_figure_to_bitmap_headless,
        )

        if not success:
            return EstimateLidarLineResponse(Pose(), False)

        if req.line_id == 0:
            self.first_line_point = average_line_point_now
            rospy.loginfo(f"Saved first line point: {self.first_line_point}")

            if req.purge_after_processing:
                self.purge_data()

            return EstimateLidarLineResponse(
                self.point_to_pose(average_line_point_now), True
            )

        elif req.line_id == 1:
            rospy.loginfo(f"Saved 2nd line point: {average_line_point_now}")
            if self.first_line_point is None:
                rospy.logwarn(
                    "First line point not found. Please process line 0 first."
                )
                return EstimateLidarLineResponse(Pose(), False)

            middle_point = (self.first_line_point + average_line_point_now) / 2
            direction_vector = self.first_line_point - average_line_point_now
            direction_vector /= np.linalg.norm(direction_vector)

            pose = self.create_pose_from_points(middle_point, direction_vector)

            if req.purge_after_processing:
                self.purge_data()

            return EstimateLidarLineResponse(pose, True)

        else:
            rospy.logwarn(f"Invalid line_id: {req.line_id}")
            return EstimateLidarLineResponse(Pose(), False)

    def process_line(
        self,
        min_z,
        max_z,
        cluster_eps,
        enable_plotting_data,
        save_figure_to_bitmap_headless,
    ):
        interpolated_data = []

        for t, pointcloud in self.pointclouds:
            pose = self.interpolate_pose(t)
            if pose is None:
                continue

            position, orientation = pose

            print(f"Pose is: {pose}")
            rotation = Rotation.from_quat(orientation)

            points = np.array(
                [[-point.y, 0, point.x] for point in pointcloud.points]
            )
            world_points = rotation.apply(points) + position

            filtered_points = world_points[
                (world_points[:, 2] >= min_z) & (world_points[:, 2] < max_z)
            ]

            if filtered_points.size > 0:
                local_points = rotation.inv().apply(filtered_points - position)
                interpolated_data.append((local_points, rotation, position))

        if not interpolated_data:
            rospy.logwarn("No valid data after filtering")
            return False, None

        all_center_points = []

        for local_points, rotation, position in interpolated_data:
            X = local_points[
                :, [0, 2]
            ]  # Use X and Z coordinates for clustering
            dbscan = DBSCAN(eps=cluster_eps, min_samples=5)
            labels = dbscan.fit_predict(X)

            valid_clusters = [k for k in set(labels) if k != -1]
            if not valid_clusters:
                continue

            cluster_centers = []
            for k in valid_clusters:
                cluster_points = X[labels == k]
                min_x = np.min(cluster_points[:, 0])
                max_x = np.max(cluster_points[:, 0])
                center_x = (min_x + max_x) / 2
                center_z = np.mean(
                    cluster_points[:, 1]
                )  # Use mean for Z coordinate
                cluster_centers.append([center_x, center_z])

            closest_cluster = min(cluster_centers, key=lambda c: abs(c[0]))

            center_point = np.array([closest_cluster[0], 0, closest_cluster[1]])
            world_center = rotation.apply(center_point) + position
            all_center_points.append(world_center)

        if not all_center_points:
            rospy.logwarn("No valid clusters found")
            return False, None

        average_point = np.mean(all_center_points, axis=0)

        if enable_plotting_data:
            self.plot_line_data(
                interpolated_data,
                all_center_points,
                average_point,
                save_figure_to_bitmap_headless,
            )

        return True, average_point

    # TODO: test and cleanup, this workpiece refinement method is not effective and not used currently
    def refine_length_displacement(self, req):
        print("Starting refine_length_displacement function")
        min_scan_displacement = 0.002
        interpolated_points = self.interpolate_pointclouds_to_common_frame(
            min_scan_displacement
        )
        print(
            f"Interpolated points: {'Successful' if interpolated_points is not None else 'Failed'}"
        )

        if interpolated_points is None:
            print("Interpolation failed, returning early")
            return RefineLidarLengthDisplacementResponse(Pose(), False)

        all_filtered_points = self.filter_points_by_z(
            interpolated_points, req.min_z, req.max_z
        )
        print(
            f"Filtered points: {'Successful' if all_filtered_points is not None else 'Failed'}"
        )

        if all_filtered_points is None:
            print("Filtering failed, returning early")
            return RefineLidarLengthDisplacementResponse(Pose(), False)

        print("Calling segment_objects method")
        hull_data, object_poses, X, labels, _ = self.segment_objects(
            all_filtered_points,
            req.cluster_eps,
            req.min_z,
            req.max_z,
            req.goal_z,
        )
        print(f"Number of segmented objects: {len(object_poses)}")

        print("Finding closest pose")
        closest_pose_index = min(
            range(len(object_poses)),
            key=lambda i: np.linalg.norm(
                np.array(
                    [
                        object_poses[i].position.x,
                        object_poses[i].position.y,
                        object_poses[i].position.z,
                    ]
                )
                - np.array(
                    [
                        req.initial_object_pose.position.x,
                        req.initial_object_pose.position.y,
                        req.initial_object_pose.position.z,
                    ]
                )
            ),
        )
        print(f"Closest pose index: {closest_pose_index}")

        closest_hull_data = hull_data[
            list(hull_data.keys())[closest_pose_index]
        ]
        print(
            f"Number of points in closest hull: {len(closest_hull_data['hull_points'])}"
        )
        print(f"Shape of hull_points: {closest_hull_data['hull_points'].shape}")

        print("Transforming hull points")
        initial_pose_rotation = Rotation.from_quat(
            [
                req.initial_object_pose.orientation.x,
                req.initial_object_pose.orientation.y,
                req.initial_object_pose.orientation.z,
                req.initial_object_pose.orientation.w,
            ]
        )
        initial_pose_translation = np.array(
            [
                req.initial_object_pose.position.x,
                req.initial_object_pose.position.y,
                req.initial_object_pose.position.z,
            ]
        )
        print(
            f"Shape of initial_pose_translation: {initial_pose_translation.shape}"
        )

        try:
            # Add z=0 to the hull points
            hull_points_3d = np.hstack(
                [
                    closest_hull_data['hull_points'],
                    np.zeros((len(closest_hull_data['hull_points']), 1)),
                ]
            )
            print(f"Shape of hull_points_3d: {hull_points_3d.shape}")

            # Perform the transformation
            transformed_hull_points = initial_pose_rotation.inv().apply(
                hull_points_3d - initial_pose_translation
            )
            print(
                f"Shape of transformed_hull_points: {transformed_hull_points.shape}"
            )
        except Exception as e:
            print(f"Error during hull point transformation: {str(e)}")
            return RefineLidarLengthDisplacementResponse(Pose(), False)

        smallest_x = np.min(transformed_hull_points[:, 0])
        print(f"Smallest x-coordinate: {smallest_x}")

        x_correction = req.search_direction * (
            (req.object_length / 2.0) + smallest_x
        )
        print(f"Calculated x_correction: {x_correction}")

        print("Creating transformation matrices")
        translation_matrix = np.eye(4)
        translation_matrix[0, 3] = x_correction

        initial_pose_matrix = np.eye(4)
        initial_pose_matrix[:3, :3] = (
            initial_pose_rotation.as_dcm()
        )  # Changed from as_matrix() to as_dcm()
        initial_pose_matrix[:3, 3] = initial_pose_translation

        refined_pose_matrix = initial_pose_matrix @ translation_matrix
        print("Refined pose matrix calculated")

        refined_position = refined_pose_matrix[:3, 3]
        refined_rotation = Rotation.from_dcm(
            refined_pose_matrix[:3, :3]
        )  # Changed from from_matrix() to from_dcm()

        print("Creating refined pose")
        refined_pose = Pose()
        refined_pose.position.x = refined_position[0]
        refined_pose.position.y = refined_position[1]
        refined_pose.position.z = refined_position[2]
        refined_quaternion = refined_rotation.as_quat()
        refined_pose.orientation.x = refined_quaternion[0]
        refined_pose.orientation.y = refined_quaternion[1]
        refined_pose.orientation.z = refined_quaternion[2]
        refined_pose.orientation.w = refined_quaternion[3]

        if req.enable_plotting_data:
            print("Plotting refined data")
            self.plot_refined_data(
                all_filtered_points,
                hull_points_3d,
                initial_pose_translation,
                refined_position,
                req.save_figure_to_bitmap_headless,
            )

        if req.purge_after_processing:
            print("Purging data")
            self.purge_data()

        print("Refine_length_displacement function completed successfully")
        return RefineLidarLengthDisplacementResponse(refined_pose, True)

    def create_pose_from_points(self, point, direction_vector):
        pose = Pose()
        pose.position.x = point[0]
        pose.position.y = point[1]
        pose.position.z = point[2]

        x_axis = direction_vector
        z_axis = np.array([0, 0, 1])
        y_axis = np.cross(z_axis, x_axis)

        rotation_matrix = np.column_stack((x_axis, y_axis, z_axis))
        q = rotation_matrix_to_quaternion(rotation_matrix)

        pose.orientation.x = q[0]
        pose.orientation.y = q[1]
        pose.orientation.z = q[2]
        pose.orientation.w = q[3]

        return pose

    def point_to_pose(self, point):
        pose = Pose()
        pose.position.x = point[0]
        pose.position.y = point[1]
        pose.position.z = point[2]
        pose.orientation.w = 1.0  # Identity quaternion
        return pose

    def plot_line_data(
        self, interpolated_data, all_center_points, average_point, save_to_file
    ):
        fig, ax = plt.subplots(figsize=(12, 8))

        for local_points, rotation, position in interpolated_data:
            world_points = rotation.apply(local_points) + position
            ax.scatter(world_points[:, 0], world_points[:, 1], alpha=0.5, s=1)

        center_points = np.array(all_center_points)
        ax.scatter(
            center_points[:, 0],
            center_points[:, 1],
            color='red',
            s=30,
            label='Cluster Centers',
        )
        ax.scatter(
            average_point[0],
            average_point[1],
            color='green',
            s=100,
            label='Average Point',
        )

        ax.set_title('Line Estimation')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.legend()
        ax.grid(True)
        ax.axis('equal')

        if save_to_file:
            save_dir = os.path.expanduser('~/lidar_objects')
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().isoformat()
            filename = f'line_estimation_{timestamp}.png'
            filepath = os.path.join(save_dir, filename)
            fig.savefig(filepath)
            rospy.loginfo(f"Line estimation plot saved as {filepath}")
        else:
            plt.show()

        plt.close(fig)

    def find_highest_cloud_point_callback(self, req):
        self.temp_pointcloud_received = False
        self.lidar_status = True

        # Wait for a pointcloud to be received
        timeout = rospy.Duration(5.0)  # 5 seconds timeout
        start_time = rospy.Time.now()
        while (
            not self.temp_pointcloud_received
            and (rospy.Time.now() - start_time) < timeout
        ):
            rospy.sleep(0.1)

        self.lidar_status = False

        if not self.temp_pointcloud_received:
            rospy.logwarn("Timeout: No pointcloud received")
            return FindHighestLidarZResponse(0.0, False)

        # Transform pointcloud to world frame
        pose = self.interpolate_pose(rospy.Time.now())
        if pose is None:
            rospy.logwarn("Failed to interpolate pose")
            return FindHighestLidarZResponse(0.0, False)

        position, orientation = pose
        rotation = Rotation.from_quat(orientation)

        points = np.array(
            [[-point.y, 0, point.x] for point in self.temp_pointcloud.points]
        )
        transformed_points = rotation.apply(points) + position

        # Find highest Z value
        highest_z = (
            np.max(transformed_points[:, 2])
            if transformed_points.size > 0
            else 0.0
        )

        # Clear temporary pointcloud
        self.temp_pointcloud = None
        self.temp_pointcloud_received = False

        return FindHighestLidarZResponse(highest_z, True)

    def find_closest_rectangle_callback(self, req):
        rospy.loginfo("Processing find_closest_rectangle request")
        min_scan_displacement = rospy.get_param(
            '~min_refine_scan_displacement', 0.0005
        )
        interpolated_points = self.interpolate_pointclouds_to_common_frame(
            min_scan_displacement
        )
        if interpolated_points is None:
            rospy.logwarn("Failed to interpolate pointclouds to common frame")
            return FindClosestLidarRectangleResponse(Pose(), False)

        all_filtered_points = self.filter_points_by_z(
            interpolated_points, req.min_z, req.max_z
        )
        if all_filtered_points is None:
            rospy.logwarn(
                f"No points found within z-range [{req.min_z}, {req.max_z}]"
            )
            return FindClosestLidarRectangleResponse(Pose(), False)

        hull_data, object_poses, X, labels, cluster_points = (
            self.segment_objects(
                all_filtered_points,
                req.cluster_eps,
                req.min_z,
                req.max_z,
                req.goal_z,
            )
        )
        if not object_poses:
            rospy.logwarn(
                "No objects found in the point cloud after segmentation"
            )
            return FindClosestLidarRectangleResponse(Pose(), False)

        # Find the closest pose to the initial pose
        initial_pose_position = np.array(
            [
                req.initial_pose.position.x,
                req.initial_pose.position.y,
                req.initial_pose.position.z,
            ]
        )
        closest_pose_index = min(
            range(len(object_poses)),
            key=lambda i: np.linalg.norm(
                np.array(
                    [
                        object_poses[i].position.x,
                        object_poses[i].position.y,
                        object_poses[i].position.z,
                    ]
                )
                - initial_pose_position
            ),
        )

        closest_cluster_points = cluster_points[
            list(cluster_points.keys())[closest_pose_index]
        ][
            :, :2
        ]  # Only use x and y

        # Prepare initial guess
        initial_rotation = Rotation.from_quat(
            [
                req.initial_pose.orientation.x,
                req.initial_pose.orientation.y,
                req.initial_pose.orientation.z,
                req.initial_pose.orientation.w,
            ]
        )
        initial_euler = initial_rotation.as_euler('xyz')
        initial_guess = [
            req.initial_pose.position.x,
            req.initial_pose.position.y,
            initial_euler[2],
        ]

        # Perform ICP with improved cost function and initial guess
        optimal_params, computation_time = self.fit_rectangle_to_points(
            closest_cluster_points,
            req.rectangle_width,
            req.rectangle_height,
            initial_guess,
        )
        optimal_params[2] = -optimal_params[2]
        optimal_tx, optimal_ty, optimal_theta = optimal_params

        # Create refined pose
        refined_pose = Pose()
        refined_pose.position.x = optimal_tx
        refined_pose.position.y = optimal_ty
        refined_pose.position.z = req.initial_pose.position.z

        # Calculate the rotation using only the optimal theta
        optimal_rotation = Rotation.from_euler('z', optimal_theta)

        refined_quaternion = optimal_rotation.as_quat()
        refined_pose.orientation.x = refined_quaternion[0]
        refined_pose.orientation.y = refined_quaternion[1]
        refined_pose.orientation.z = refined_quaternion[2]
        refined_pose.orientation.w = refined_quaternion[3]

        # Calculate Euler angles for logging
        refined_euler = optimal_rotation.as_euler('xyz', degrees=True)
        rospy.loginfo("Refined pose calculated:")
        rospy.loginfo(
            f"  Position: ({refined_pose.position.x:.4f}, {refined_pose.position.y:.4f}, {refined_pose.position.z:.4f})"
        )
        rospy.loginfo(
            f"  Orientation (Euler angles XYZ): ({refined_euler[0]:.2f}, {refined_euler[1]:.2f}, {refined_euler[2]:.2f}) degrees"
        )

        if req.enable_plotting_data:
            self.plot_icp_results(
                closest_cluster_points,
                req.rectangle_width,
                req.rectangle_height,
                optimal_params,
                initial_guess,
                req.save_figure_to_bitmap_headless,
            )

        if req.purge_after_processing:
            self.purge_data()

        rospy.loginfo(f"ICP computation time: {computation_time:.4f} seconds")
        return FindClosestLidarRectangleResponse(refined_pose, True)

    def fit_rectangle_to_points(self, points, width, height, initial_guess):
        """Fit a fixed-size rectangle to a set of points."""
        start_time = rospy.Time.now()
        bounds = [(None, None), (None, None), (-np.pi, np.pi)]
        result = minimize(
            cost_function_fixed_size,
            initial_guess,
            args=(points, width, height),
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000},
        )
        end_time = rospy.Time.now()

        computation_time = (end_time - start_time).to_sec()

        return result.x, computation_time

    def plot_icp_results(
        self, points, width, height, optimal_params, initial_guess, save_to_file
    ):
        fig, ax = plt.subplots(
            figsize=(12, 14)
        )  # Increased figure height to accommodate additional annotations

        # Plot the input points
        ax.scatter(
            points[:, 0],
            points[:, 1],
            c='blue',
            alpha=0.5,
            label='Points',
            zorder=1,
        )

        # Create the initial centered rectangle
        rectangle = self.create_centered_rectangle(width, height)

        # Plot the initial estimate
        initial_tx, initial_ty, initial_theta = initial_guess
        initial_cos_theta, initial_sin_theta = np.cos(initial_theta), np.sin(
            initial_theta
        )
        initial_rotation_matrix = np.array(
            [
                [initial_cos_theta, -initial_sin_theta],
                [initial_sin_theta, initial_cos_theta],
            ]
        )
        initial_rectangle = np.dot(rectangle, initial_rotation_matrix.T) + [
            initial_tx,
            initial_ty,
        ]
        initial_rectangle_plot = np.vstack(
            [initial_rectangle, initial_rectangle[0]]
        )
        ax.plot(
            initial_rectangle_plot[:, 0],
            initial_rectangle_plot[:, 1],
            'r--',
            label='Initial Estimate',
            linewidth=2,
            zorder=2,
        )

        # Plot the fitted rectangle
        tx, ty, theta = optimal_params
        cos_theta, sin_theta = np.cos(theta), np.sin(theta)
        rotation_matrix = np.array(
            [[cos_theta, -sin_theta], [sin_theta, cos_theta]]
        )
        transformed_rectangle = np.dot(rectangle, rotation_matrix.T) + [tx, ty]
        fitted_rectangle_plot = np.vstack(
            [transformed_rectangle, transformed_rectangle[0]]
        )
        ax.plot(
            fitted_rectangle_plot[:, 0],
            fitted_rectangle_plot[:, 1],
            'g-',
            label='Fitted Rectangle',
            linewidth=2,
            zorder=3,
        )

        ax.legend()
        ax.set_title('ICP Rectangle Fitting Result')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.axis('equal')
        ax.grid(True)

        # Calculate signed errors
        dx = tx - initial_tx
        dy = ty - initial_ty
        dtheta = theta - initial_theta
        # Normalize dtheta to be between -pi and pi
        dtheta = (dtheta + np.pi) % (2 * np.pi) - np.pi

        # Add text annotations below the graph
        annotation_text = (
            f"Initial: ({initial_tx:.3f}, {initial_ty:.3f}, {np.degrees(initial_theta):.1f}°)\n"
            f"Final: ({tx:.3f}, {ty:.3f}, {np.degrees(theta):.1f}°)\n"
            f"Errors:\n"
            f"  Δx: {dx:.3f} m\n"
            f"  Δy: {dy:.3f} m\n"
            f"  Δθ: {np.degrees(dtheta):.1f}°"
        )
        fig.text(
            0.5, 0.01, annotation_text, ha='center', va='bottom', fontsize=10
        )

        # Adjust the layout to make room for the annotation
        plt.tight_layout()
        plt.subplots_adjust(
            bottom=0.2
        )  # Increased bottom margin to accommodate additional text

        if save_to_file:
            save_dir = os.path.expanduser('~/lidar_objects')
            os.makedirs(save_dir, exist_ok=True)
            timestamp = datetime.now().isoformat()
            filename = f'icp_rectangle_fitting_{timestamp}.png'
            filepath = os.path.join(save_dir, filename)
            plt.savefig(filepath, bbox_inches='tight')
            rospy.loginfo(f"ICP rectangle fitting plot saved as {filepath}")
        else:
            plt.show()

        plt.close(fig)

    def create_centered_rectangle(self, width, height):
        half_width = width / 2
        half_height = height / 2
        return np.array(
            [
                [-half_width, -half_height],
                [half_width, -half_height],
                [half_width, half_height],
                [-half_width, half_height],
            ]
        )

    def transform_rectangle(self, rectangle, transform_params):
        tx, ty, theta = transform_params
        return transform_points(rectangle, -tx, -ty, -theta)

    # def transform_points(self, points, tx, ty, theta):
    #     cos_theta, sin_theta = np.cos(theta), np.sin(theta)
    #     rotation_matrix = np.array([[cos_theta, -sin_theta],
    #                                 [sin_theta, cos_theta]])
    #     return np.dot(points + [tx, ty], rotation_matrix.T)

    def distances_point_to_lines(self, points, lines):
        p = points[:, np.newaxis, :]
        a = lines[:, 0]
        b = lines[:, 1]
        ap = p - a
        ab = b - a
        projection = np.sum(ap * ab, axis=2) / np.sum(ab * ab, axis=1)
        projection = np.clip(projection, 0, 1)
        closest = a + projection[:, :, np.newaxis] * ab
        distances = np.linalg.norm(p - closest, axis=2)
        return distances

    def cost_function_vectorized(self, params, points, rectangle_points):
        tx, ty, theta = params
        transformed_rect = self.transform_points(
            rectangle_points, tx, ty, theta
        )
        lines = np.array(
            [transformed_rect, np.roll(transformed_rect, -1, axis=0)]
        ).transpose(1, 0, 2)
        distances = self.distances_point_to_lines(points, lines)
        return np.sum(np.min(distances, axis=1))

    def improved_cost_function(self, params, points, rectangle_points):
        tx, ty, theta = params
        transformed_rect = self.transform_points(
            rectangle_points, tx, ty, theta
        )
        lines = np.array(
            [transformed_rect, np.roll(transformed_rect, -1, axis=0)]
        ).transpose(1, 0, 2)

        # Calculate distances to edges
        distances = self.distances_point_to_lines(points, lines)
        min_distances = np.min(distances, axis=1)

        # Calculate penalty for points inside the rectangle
        inside_points = self.points_inside_rectangle(points, transformed_rect)
        inside_penalty = (
            np.sum(inside_points) * 0.1
        )  # Adjust penalty weight as needed

        # Combine distance cost and inside penalty
        total_cost = np.sum(min_distances) + inside_penalty

        return total_cost

    def points_inside_rectangle(self, points, rectangle):
        # Check if points are inside the rectangle using the point-in-polygon algorithm
        n = len(rectangle)
        inside = np.zeros(len(points), dtype=bool)
        for i, point in enumerate(points):
            j = n - 1
            for k in range(n):
                if (
                    (rectangle[k, 1] > point[1]) != (rectangle[j, 1] > point[1])
                ) and (
                    point[0]
                    < (rectangle[j, 0] - rectangle[k, 0])
                    * (point[1] - rectangle[k, 1])
                    / (rectangle[j, 1] - rectangle[k, 1])
                    + rectangle[k, 0]
                ):
                    inside[i] = not inside[i]
                j = k
        return inside


def main():
    try:
        processor = ROSPointCloudProcessor()  # noqa: F841
        rospy.spin()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
