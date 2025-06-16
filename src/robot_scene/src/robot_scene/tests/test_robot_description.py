import os

import pytest

from robot_scene.robot_description import (
    RobotDescription,
    XacroReadError,
    UrdfReadError,
)


@pytest.fixture
def sample_urdf():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    urdf_file = os.path.join(current_dir, 'sample.urdf')
    with open(urdf_file) as f:
        return f.read()


def test_reading_urdf_from_data_works(sample_urdf):
    description = RobotDescription()

    description.read(sample_urdf)

    assert len(description.visual_meshes) == 4
    assert len(description.collision_meshes) == 4
    assert len(description.joints) == 4


def test_identifying_base_joint_works(sample_urdf):
    description = RobotDescription()

    description.read(sample_urdf)

    base_joint = description.joints['world-frame']
    assert base_joint.is_base
    assert base_joint is description.base_joint


def test_reading_non_existent_file_throws_error():
    description = RobotDescription()

    with pytest.raises(XacroReadError):
        description.read_from_xacro("ZpSU")


def test_reading_broken_urdf_throws_error():
    description = RobotDescription()

    with pytest.raises(UrdfReadError):
        description.read("jLr")
