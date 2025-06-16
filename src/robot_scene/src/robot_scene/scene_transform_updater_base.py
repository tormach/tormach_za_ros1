import contextlib
import time

import numpy
import pyassimp

import rospy
import tf2_ros
from geometry_msgs.msg import PoseStamped, Point, TransformStamped
from moveit_msgs.msg import (
    PlanningScene,
    CollisionObject,
    AttachedCollisionObject,
    ObjectColor,
    PlanningSceneComponents,
)
from moveit_msgs.srv import ApplyPlanningScene, GetPlanningScene
from rospy import ServiceException
from shape_msgs.msg import Mesh, MeshTriangle
from tf.transformations import (
    translation_matrix,
    quaternion_matrix,
    translation_from_matrix,
    quaternion_from_matrix,
)
from tf2_geometry_msgs import do_transform_pose


class SceneTransformUpdaterBase:
    TF_BUFFER_CACHE_TIME_S = 1200
    TF_LOOKUP_TIMEOUT_S = 0.25
    COLLISION_SUFFIX = '_collision'
    DEFAULT_WAIT_TIMEOUT_S = 10.0
    TF_SYNC_TIME_S = 0.01

    def __init__(self, ns='', use_service=True, cache_tfs=False):
        """
        :param cache_tfs:  Optional caching of already published transforms.
        """
        self._use_service = use_service

        if use_service:
            self._apply_ps_srv = rospy.ServiceProxy(
                f'{ns}apply_planning_scene', ApplyPlanningScene
            )

        else:
            self._scene_pub = rospy.Publisher(
                f'{ns}planning_scene', PlanningScene, queue_size=10
            )

        self._get_ps_srv = rospy.ServiceProxy(
            f'{ns}get_planning_scene', GetPlanningScene
        )

        # initialize tf
        self._tf_broadcaster = tf2_ros.TransformBroadcaster()
        self._tf_buffer = tf2_ros.Buffer(
            cache_time=rospy.Duration.from_sec(self.TF_BUFFER_CACHE_TIME_S)
        )
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer)
        self._cache_tfs = cache_tfs
        if self._cache_tfs:
            self._transforms = {}

        wait_timeout_s = rospy.get_param(
            'ros_wait_timeout_s', self.DEFAULT_WAIT_TIMEOUT_S
        )
        if use_service:
            self._apply_ps_srv.wait_for_service(timeout=wait_timeout_s)
        self._get_ps_srv.wait_for_service(timeout=wait_timeout_s)

    def _transform_mesh_pose(self, description, mesh):
        # note: for some reason planning does not move the object when we
        # just update the frame transform , so we do the transformation
        # ourselves here
        try:
            transform = self._tf_buffer.lookup_transform(
                target_frame=description.base_link,
                source_frame=mesh.frame,
                time=rospy.Time(0),
                timeout=rospy.Duration.from_sec(self.TF_LOOKUP_TIMEOUT_S),
            )
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ) as e:
            rospy.logwarn(
                f"Looking up transform from {mesh.frame} to {description.base_link} failed: {e}"
            )

            return None
        pose = PoseStamped()
        pose.header.stamp = transform.header.stamp
        pose.header.frame_id = mesh.frame
        pose.pose = mesh.origin
        return do_transform_pose(pose, transform)

    @staticmethod
    def _make_mesh(name, pose, frame, filename):
        scene = pyassimp.load(filename)
        if not scene.meshes:
            rospy.logerr('Unable to load mesh')
            return

        mesh = Mesh()
        for face in scene.meshes[0].faces:
            triangle = MeshTriangle()
            if len(face) == 3:
                triangle.vertex_indices = [
                    face[0],
                    face[1],
                    face[2],
                ]
            mesh.triangles.append(triangle)
        for vertex in scene.meshes[0].vertices:
            point = Point()
            point.x = vertex[0]
            point.y = vertex[1]
            point.z = vertex[2]
            mesh.vertices.append(point)
        pyassimp.release(scene)

        o = CollisionObject()
        o.header.frame_id = frame
        o.id = name
        o.meshes.append(mesh)
        if isinstance(pose, PoseStamped):
            o.header.stamp = pose.header.stamp
            o.mesh_poses.append(pose.pose)
        else:
            o.header.stamp = rospy.Time.now()
            o.mesh_poses.append(pose)
        o.pose.orientation.w = 1.0
        o.pose.orientation = o.mesh_poses[0].orientation
        o.pose.position = o.mesh_poses[0].position
        o.mesh_poses = []
        o.operation = o.ADD
        return o

    @staticmethod
    def _make_attached(link_name, obj, touch_links, detach_posture, weight):
        o = AttachedCollisionObject()
        o.link_name = link_name
        o.object = obj
        if touch_links:
            o.touch_links = touch_links
        if detach_posture:
            o.detach_posture = detach_posture
        o.weight = weight
        return o

    @staticmethod
    def _make_color(name, r, g, b, a=0.9):
        color = ObjectColor()
        color.id = name
        color.color.r = r
        color.color.g = g
        color.color.b = b
        color.color.a = a
        return color

    @staticmethod
    def _update_mesh(name, pose, frame):
        o = CollisionObject()
        o.header.frame_id = frame
        o.id = name
        if isinstance(pose, PoseStamped):
            o.header.stamp = pose.header.stamp
            o.mesh_poses.append(pose.pose)
        else:
            o.header.stamp = rospy.Time.now()
            o.mesh_poses.append(pose)
        o.pose.orientation = o.mesh_poses[0].orientation
        o.pose.position = o.mesh_poses[0].position
        o.mesh_poses = []
        o.operation = o.MOVE
        return o

    @staticmethod
    def _remove_mesh(name):
        o = CollisionObject()
        o.header.stamp = rospy.Time.now()
        o.id = name
        o.operation = o.REMOVE
        return o

    @staticmethod
    def _remove_attached_mesh(name="", link_name=""):
        o = AttachedCollisionObject()
        if name:
            o.object.id = name
        if link_name:
            o.link_name = link_name
        o.object.operation = CollisionObject.REMOVE
        return o

    def _get_acm(self):
        request = PlanningSceneComponents(
            components=PlanningSceneComponents.ALLOWED_COLLISION_MATRIX
        )
        response = self._get_ps_srv.call(request)
        return response.scene.allowed_collision_matrix

    def _send_scene_update(
        self,
        collision_objects=None,
        attached_collision_objects=None,
        colors=None,
        acm=None,
    ):
        if not collision_objects:
            collision_objects = []
        if not attached_collision_objects:
            attached_collision_objects = []
        if not colors:
            colors = []

        ps = PlanningScene()
        ps.is_diff = True
        ps.robot_state.is_diff = True

        ps.world.collision_objects += collision_objects
        ps.robot_state.attached_collision_objects += attached_collision_objects
        ps.object_colors += colors
        if acm:
            ps.allowed_collision_matrix = acm

        if self._use_service:
            try:
                resp = self._apply_ps_srv.call(ps)
            except ServiceException as e:
                rospy.logerr(f"Error calling apply planning scene service {e}")
            else:
                if not resp.success:
                    rospy.logerr("Could not apply planning scene diff.")
        else:
            self._scene_pub.publish(ps)

    @staticmethod
    def _calculate_joint_tf(joint):
        origin_tf = joint.origin_tf
        transl_mat = translation_matrix(
            [
                origin_tf.transform.translation.x,
                origin_tf.transform.translation.y,
                origin_tf.transform.translation.z,
            ]
        )
        rot_mat = quaternion_matrix(
            [
                origin_tf.transform.rotation.x,
                origin_tf.transform.rotation.y,
                origin_tf.transform.rotation.z,
                origin_tf.transform.rotation.w,
            ]
        )
        origin_mat = numpy.dot(transl_mat, rot_mat)
        transl_mat = translation_matrix(joint.translation)
        rot_mat = quaternion_matrix(joint.rotation)
        axis_mat = numpy.dot(transl_mat, rot_mat)

        result_mat = numpy.dot(origin_mat, axis_mat)
        translation = translation_from_matrix(result_mat)
        rotation = quaternion_from_matrix(result_mat)
        result_tf = TransformStamped()
        result_tf.header.frame_id = origin_tf.header.frame_id
        result_tf.child_frame_id = origin_tf.child_frame_id
        result_tf.transform.translation.x = translation[0]
        result_tf.transform.translation.y = translation[1]
        result_tf.transform.translation.z = translation[2]
        result_tf.transform.rotation.x = rotation[0]
        result_tf.transform.rotation.y = rotation[1]
        result_tf.transform.rotation.z = rotation[2]
        result_tf.transform.rotation.w = rotation[3]
        return result_tf

    def _add_meshes(
        self,
        description,
        attached=False,
        link_name="",
        touch_links=None,
        detach_posture=None,
        weight=0.0,
    ):
        meshes = []
        colors = []
        acm = self._get_acm()

        for mesh in description.visual_meshes:
            transformed_pose = self._transform_mesh_pose(description, mesh)
            meshes.append(
                self._make_mesh(
                    name=mesh.unique_name,
                    pose=transformed_pose,
                    frame=mesh.frame,
                    filename=mesh.stl_file,
                )
            )
            if not attached:  # FIXME: attached object color can't be set
                colors.append(self._make_color(mesh.unique_name, *mesh.color))
            if mesh.unique_name not in acm.default_entry_names:
                acm.default_entry_names += [mesh.unique_name]
                acm.default_entry_values += [True]

        for mesh in description.collision_meshes:
            transformed_pose = self._transform_mesh_pose(description, mesh)
            name = mesh.unique_name + self.COLLISION_SUFFIX
            meshes.append(
                self._make_mesh(
                    name=name,
                    pose=transformed_pose,
                    frame=mesh.frame,
                    filename=mesh.stl_file,
                )
            )
            colors.append(self._make_color(name, 0.0, 0.0, 0.0, 0.0))
            if mesh.unique_name in acm.default_entry_names:
                i = acm.default_entry_names.index(mesh.unique_name)
                acm.default_entry_values[i] = False

        if not attached:
            self._send_scene_update(
                collision_objects=meshes, colors=colors, acm=acm
            )
        else:
            attached_meshes = []
            for mesh in meshes:
                mesh.header.frame_id = link_name
                a = self._make_attached(
                    link_name, mesh, touch_links, detach_posture, weight
                )
                attached_meshes.append(a)
            self._send_scene_update(
                attached_collision_objects=attached_meshes,
                colors=colors,
                acm=acm,
            )

    def _update_meshes(self, description):
        meshes = []

        for mesh in description.visual_meshes:
            transformed_pose = self._transform_mesh_pose(description, mesh)
            meshes.append(
                self._update_mesh(
                    name=mesh.unique_name,
                    pose=transformed_pose,
                    frame=description.base_link,
                )
            )

        for mesh in description.collision_meshes:
            transformed_pose = self._transform_mesh_pose(description, mesh)
            meshes.append(
                self._update_mesh(
                    name=mesh.unique_name + self.COLLISION_SUFFIX,
                    pose=transformed_pose,
                    frame=description.base_link,
                )
            )

        self._send_scene_update(collision_objects=meshes)

    def _remove_meshes(self, description, attached=False):
        meshes = []
        attached_meshes = []
        for mesh in description.visual_meshes:
            if attached:
                attached_meshes.append(
                    self._remove_attached_mesh(mesh.unique_name)
                )
            else:
                meshes.append(self._remove_mesh(mesh.unique_name))
        for mesh in description.collision_meshes:
            name = mesh.unique_name + self.COLLISION_SUFFIX
            if attached:
                attached_meshes.append(self._remove_attached_mesh(name))
            else:
                meshes.append(self._remove_mesh(name))
        self._send_scene_update(
            collision_objects=meshes, attached_collision_objects=attached_meshes
        )

    def _remove_all_attached_meshes(self, link_name):
        self._send_scene_update(
            attached_collision_objects=[
                self._remove_attached_mesh(link_name=link_name)
            ]
        )

    def _wait_for_transform_published(self, tf):
        start_time = time.time()
        while True:
            with contextlib.suppress(
                tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException,
            ):
                pub_transform = self._tf_buffer.lookup_transform(
                    target_frame=tf.child_frame_id,
                    source_frame=tf.header.frame_id,
                    time=rospy.Time(0),
                )
                t = pub_transform.transform
                # float comparison is legitimate here since we use the same
                # conversion method in offset pub and here
                if (
                    t.translation.x == tf.transform.translation.x
                    and t.translation.y == tf.transform.translation.y
                    and t.translation.z == tf.transform.translation.z
                    and t.rotation.x == tf.transform.rotation.x
                    and t.rotation.y == tf.transform.rotation.y
                    and t.rotation.z == tf.transform.rotation.z
                    and t.rotation.w == tf.transform.rotation.w
                ):
                    break
            current_time = time.time()
            delta = current_time - start_time
            if delta >= self.TF_LOOKUP_TIMEOUT_S:
                return False
            time.sleep(self.TF_SYNC_TIME_S)
        return True

    def _publish_transforms(self, description):
        transforms = []
        stamp = rospy.Time.now()
        for joint in description.joints.values():
            if joint.type in ('prismatic', 'revolute') or joint.is_base:
                result_tf = self._calculate_joint_tf(joint)
            else:
                result_tf = joint.origin_tf
            result_tf.header.stamp = stamp
            transforms.append(result_tf)

        if self._cache_tfs:
            covered = set()
            for tf in transforms:
                self._transforms[tf.child_frame_id] = tf
                covered.add(tf.child_frame_id)
            for child_frame_id in set(self._transforms.keys()) - covered:
                self._transforms[child_frame_id].header.stamp = stamp
            self._tf_broadcaster.sendTransform(list(self._transforms.values()))
        else:
            self._tf_broadcaster.sendTransform(transforms)

        for tf in transforms:
            self._wait_for_transform_published(tf)
