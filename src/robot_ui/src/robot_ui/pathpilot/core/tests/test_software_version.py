import sh

import pytest
from robot_ui.pathpilot.core import SoftwareVersion

robot_packages = [
    (None, 'za', 'ZA6'),
    (None, '', 'Unknown robot model'),
    (None, 'Winter', 'Unknown robot model'),
    (None, None, 'Unknown robot model'),
    ('ZA6 Simulation', 'za', 'ZA6 Simulation'),
    ('ZA6', None, 'ZA6'),
    ('ZA6 Mastering', None, 'ZA6 Mastering'),
]

image_versions = [
    (
        'dist',
        '1.0.0',
        None,
        '1cf0c208',
        '1.0.0+1cf0c208',
        'Unofficial release',
        None,
        None,
    ),
    (
        'dist',
        '1.0.0',
        'Spring Bloom',
        '1cf0c208',
        '1.0.0',
        'Spring Bloom',
        None,
        None,
    ),
    (
        'dist',
        '1.a.0',
        'Spring Bloom',
        '1cf0c208',
        'Unknown version',
        'Spring Bloom',
        None,
        None,
    ),
    (
        'dist',
        '1.a.0',
        None,
        '1cf0c208',
        'Unknown version',
        'Unofficial release',
        None,
        None,
    ),
    (
        'dist',
        None,
        'Spring Bloom',
        '1cf0c208',
        'Unknown version',
        'Spring Bloom',
        None,
        None,
    ),
    (
        'dist',
        None,
        None,
        '1cf0c208',
        'Unknown version',
        'Unofficial release',
        None,
        None,
    ),
    (
        'devel',
        '1.0.0',
        None,
        '1cf0c208',
        '1.0.0+1cf0c209',
        'summer/breeze',
        'summer/breeze',
        '1cf0c209',
    ),
    (
        'devel',
        '1.0.0',
        None,
        '1cf0c208',
        '1.0.0+Unknown SHA',
        'summer/breeze',
        'summer/breeze',
        None,
    ),
    (
        'devel',
        '1.0.0',
        None,
        '1cf0c208',
        '1.0.0+Unknown SHA',
        'Unofficial release',
        None,
        None,
    ),
    (
        'devel',
        '1.0.0',
        'Spring Bloom',
        '1cf0c208',
        '1.0.0+1cf0c209',
        'summer/breeze',
        'summer/breeze',
        '1cf0c209',
    ),
    (
        'devel',
        '1.0.0',
        'Spring Bloom',
        '1cf0c208',
        '1.0.0+Unknown SHA',
        'summer/breeze',
        'summer/breeze',
        None,
    ),
    (
        'devel',
        '1.0.0',
        'Spring Bloom',
        '1cf0c208',
        '1.0.0+Unknown SHA',
        'Unofficial release',
        None,
        None,
    ),
]


@pytest.mark.parametrize(
    "robot_configuration,robot_package,shown_robot", robot_packages
)
@pytest.mark.parametrize(
    'image_type,'
    'release_version,'
    'release_codename,'
    'git_rev,shown_version,'
    'shown_codename,'
    'real_branch,'
    'real_git_sha',
    image_versions,
)
def test_public_release_version_image(
    robot_configuration,
    robot_package,
    shown_robot,
    image_type,
    release_version,
    release_codename,
    git_rev,
    shown_version,
    shown_codename,
    real_branch,
    real_git_sha,
    monkeypatch,
    qtbot,
):
    if release_codename is not None:
        monkeypatch.setenv('RELEASE_CODENAME', release_codename)
    else:
        monkeypatch.delenv('RELEASE_CODENAME', raising=False)
    if release_version is not None:
        monkeypatch.setenv('RELEASE_VERSION', release_version)
    else:
        monkeypatch.delenv('RELEASE_VERSION', raising=False)
    if image_type is not None:
        monkeypatch.setenv('IMAGE_TYPE', image_type)
    else:
        monkeypatch.delenv('IMAGE_TYPE', raising=False)
    if git_rev is not None:
        monkeypatch.setenv('GIT_REV', git_rev)
    else:
        monkeypatch.delenv('GIT_REV', raising=False)
    if robot_configuration is not None:
        monkeypatch.setenv('ROBOT_CONFIGURATION', robot_configuration)
    else:
        monkeypatch.delenv('ROBOT_CONFIGURATION', raising=False)
    if robot_package is not None:
        monkeypatch.setenv('ROBOT_MODEL', robot_package)
    else:
        monkeypatch.delenv('ROBOT_MODEL', raising=False)

    def mockgit(*args, **kwargs):
        if {'branch', '--show-current'}.issubset(args):
            return real_branch
        if {'rev-parse', '--short', 'HEAD'}.issubset(args):
            return real_git_sha

    monkeypatch.setattr(sh, 'git', mockgit)

    version = SoftwareVersion()

    assert version.version == shown_version
    assert version.codename == shown_codename
    assert version.robot == shown_robot

    monkeypatch.undo()
