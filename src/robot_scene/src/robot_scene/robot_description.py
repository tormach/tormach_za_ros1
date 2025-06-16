import os
from uuid import uuid4

import rospkg
import shlex
import subprocess
from future.backports.urllib.parse import urlparse

import attr
from geometry_msgs.msg import Pose, TransformStamped, Transform
from xml.etree.ElementTree import ParseError
from tf.transformations import quaternion_from_euler
from urdf_parser_py.urdf import URDF

rospack = rospkg.RosPack()


class RobotDescriptionReadError(Exception):
    pass


class XacroReadError(RobotDescriptionReadError):
    pass


class UrdfReadError(RobotDescriptionReadError):
    pass


def resolve_package_url(string):
    url = urlparse(string)
    if url.scheme != 'package':
        return string
    pkg_path = rospack.get_path(url.hostname)
    return os.path.join(pkg_path, url.path[1:])


@attr.s
class Mesh:
    name = attr.ib(type=str)
    origin = attr.ib(type=Pose)
    frame = attr.ib(type=str)
    stl_file = attr.ib(type=str)
    color = attr.ib(type=list)
    unique_name = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.unique_name = f"{self.name}_{uuid4()}"


@attr.s
class Joint:
    name = attr.ib(type=str)
    origin_tf = attr.ib(type=TransformStamped)
    type = attr.ib(type=str)
    axis = attr.ib(type=list)
    translation = attr.ib(type=list, default=[0.0, 0.0, 0.0])
    rotation = attr.ib(type=list, default=[0.0, 0.0, 0.0, 1.0])
    is_base = attr.ib(type=bool, default=False)
    updated = attr.ib(type=bool, default=False)


class RobotDescription:
    def __init__(self, namespace='', base_link='world'):
        self.namespace = namespace
        self.base_link = base_link

        self._visual_meshes = []
        self._collision_meshes = []
        self._joints = {}
        self._initialized = False

    @property
    def base_joint(self):
        return next(
            (joint for joint in self._joints.values() if joint.is_base), None
        )

    @property
    def joints(self):
        return self._joints

    @property
    def visual_meshes(self):
        return self._visual_meshes

    @property
    def collision_meshes(self):
        return self._collision_meshes

    @property
    def initialized(self):
        return self._initialized

    def read_from_xacro(self, file_path):
        # FIXME: could be improved by using xacro Python API
        try:
            process = subprocess.Popen(
                shlex.split(
                    f'xacro --inorder {file_path} prefix:={self.namespace}'
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        except OSError as e:
            raise XacroReadError(str(e)) from e
        out, err = process.communicate()
        if process.returncode != 0:
            raise XacroReadError(f"xacro failed: {err}")

        self.read(out)

    def read(self, description):
        try:
            robot = URDF.from_xml_string(description)
        except ParseError as e:
            raise UrdfReadError(e)

        materials = {}
        for material in robot.materials:
            materials[material.name] = material.color.rgba

        def iterate_links(link_name):
            if link_name not in robot.child_map:
                return
            for joint_name, child_link_name in robot.child_map[link_name]:
                joint = robot.joint_map[joint_name]
                t = TransformStamped()
                t.transform = self._origin_to_transform(joint.origin)
                t.header.frame_id = link_name
                t.child_frame_id = child_link_name
                self._joints[joint_name] = Joint(
                    name=joint_name,
                    origin_tf=t,
                    type=joint.type,
                    axis=joint.axis,
                    is_base=link_name == self.base_link,
                )

                child_link = robot.link_map[child_link_name]
                if visual := child_link.visual:
                    color = (
                        visual.material.color.rgba
                        if visual.material.color
                        else materials[visual.material.name]
                    )

                    stl_file = resolve_package_url(visual.geometry.filename)
                    origin = self._origin_to_pose(visual.origin)
                    self._visual_meshes.append(
                        Mesh(
                            child_link_name,
                            origin,
                            child_link_name,
                            stl_file,
                            color,
                        )
                    )
                if collision := child_link.collision:
                    color = [0.0, 0.0, 0.0, 0.0]
                    stl_file = resolve_package_url(collision.geometry.filename)
                    origin = self._origin_to_pose(collision.origin)
                    self._collision_meshes.append(
                        Mesh(
                            child_link_name,
                            origin,
                            child_link_name,
                            stl_file,
                            color,
                        )
                    )

                iterate_links(child_link_name)

        iterate_links(self.base_link)
        self._initialized = True

    @staticmethod
    def _origin_to_transform(origin):
        t = Transform()
        q = (
            quaternion_from_euler(*origin.rotation)
            if origin.rotation
            else [0, 0, 0, 1]
        )
        p = origin.position or [0, 0, 0]
        t.translation.x = p[0]
        t.translation.y = p[1]
        t.translation.z = p[2]
        t.rotation.x = q[0]
        t.rotation.y = q[1]
        t.rotation.z = q[2]
        t.rotation.w = q[3]
        return t

    @staticmethod
    def _origin_to_pose(origin):
        pose = Pose()
        q = (
            quaternion_from_euler(*origin.rotation)
            if origin.rotation
            else [0, 0, 0, 1]
        )
        p = origin.position or [0, 0, 0]
        pose.position.x = p[0]
        pose.position.y = p[1]
        pose.position.z = p[2]
        pose.orientation.x = q[0]
        pose.orientation.y = q[1]
        pose.orientation.z = q[2]
        pose.orientation.w = q[3]
        return pose
