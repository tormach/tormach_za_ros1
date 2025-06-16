#!/usr/bin/env python
#
# Generate ROS package dependency list from our custom packages in
# this repo and those listed in tormach-distribution.yaml
#
# This must be run at the base directory of the workspace

# FIXME Other pkgs to add:
# - rosdoc_lite
# - jog_arm

import os
import yaml
from rosdistro import Distribution, DistributionFile
import xml.etree.ElementTree as ET
from catkin_pkg.packages import find_packages
from rosinstall_generator.generator import generate_rosinstall, sort_rosinstall
from rosdistro.manifest_provider.github import URLError

import logging

logging.basicConfig(level=logging.DEBUG)


class RosinstallUpdater:
    URL_RETRIES = 5
    CUSTOM_PACKAGES = [
        # These depend on rviz, installed in the ros_custom build stages
        'moveit_ros_visualization',
        'moveit_ros_robot_interaction',
    ]
    EXCLUDE_PACKAGES = [
        'prbt_pg70_support',
        'prbt_moveit_config',
        'prbt_support',
    ]
    ROS_DISTRO = os.environ.get('ROS_DISTRO')

    DISTRO_FILE_DATA = dict(
        release_platforms={'ubuntu': ['focal']},
        repositories=dict(
            rviz=dict(
                # Customized for QtQuick
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    # Tormach repo @feature/alex/rob-838-keyboard-shortcuts
                    url='https://github.com/tormach/rviz.git',
                    version='add3b3f3763ee3c04f6b180afa63211b2b828c7c',
                ),
                status='maintained',
            ),
            moveit=dict(
                # Custom branch does four things:
                # - Update moveit_setup_assistant for our custom rviz
                # - support planning and tool frame update in moveit_servo
                # - add support for tool offsets in rviz interactive marker
                # - add retime trajectory service capability
                # - add experimental pipelines patch
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='git@bitbucket.org:tormachinc/moveit.git',
                    # Alex's pipeline changes + tweaks to TOTG to detect smaller angle changes
                    # Rebased to latest upstream, branch, fix for rviz plugin memory leak
                    #   alex/2023-12-12-fix-rviz-memory-leak
                    version='931bf848246e2e8b62afabdf35f3c08ad738e027',
                ),
                status='maintained',
            ),
            moveit_msgs=dict(
                # adds requirement for retime trajectory
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='git@bitbucket.org:tormachinc/moveit_msgs.git',
                    # modifications for PILZ planner params
                    # Rebased to latest upstream, branch
                    #   alex/2023-03-31_rebase_onto_latest_upstream
                    version='072f721d26a00687bbc2fe4ff7681cfa51b27177',
                ),
                status='maintained',
            ),
            moveit_resources=dict(
                # moveit_resources_prbt_pg70_support not released yet
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='https://github.com/ros-planning/moveit_resources.git',
                    version='master',
                ),
                status='maintained',
            ),
            rqt_launch=dict(
                # broken upstream
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='git@bitbucket.org:tormachinc/rqt_launch.git',
                    version='main',
                ),
                status='maintained',
            ),
            bio_ik=dict(
                # not yet released for noetic
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='https://github.com/TAMS-Group/bio_ik.git',
                    version='cda1dac0b8c722aaae400fc3de33502efb1225f0',
                ),
                status='maintained',
            ),
            ros_controllers=dict(
                # modified joint_trajectory_controller
                # includes rob-603-dynamic-velocity-scale feature
                # includes rob-1012 joint jerk fix: compensated quintic trajectory timestamps
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='git@bitbucket.org:tormachinc/ros_controllers.git',
                    version='5d9b63ecb4578a54e290401813b08e096e1f030a',
                ),
                status='maintained',
            ),
            redis_store=dict(
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='git@bitbucket.org:tormachinc/redis_store.git',
                    version='953b87bc',
                ),
                status='maintained',
            ),
            hal_ros_control=dict(
                # includes rob-603-dynamic-velocity-scale feature
                # includes rob-937 velocity scale cap at safety input trip
                # includes rob-610 dry-run-switching
                # includes rob-1003 trajecotry slowdown and delayed stop hotfix
                # includes maxvel slider glitch fix
                # includes rob-1012 joint jerk fix: compensated quintic trajectory timestamps
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='git@bitbucket.org:tormachinc/hal_ros_control.git',
                    version='bc715a2e76836cbf2c263be2ff3d6b798debd6ed',
                ),
                status='maintained',
            ),
            actionlib=dict(
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='https://github.com/tormach/actionlib.git',
                    # noetic-devel-no-goal-tracking-error
                    version='5c6fd3d1f32b4e044cae41946ae949d9589b0e4c',
                ),
                status='maintained',
            ),
            ydlidar_ros_driver=dict(
                source=dict(
                    test_pull_requests=True,
                    type='git',
                    url='git@bitbucket.org:tormachinc/ydlidar_ros_driver.git',
                    version='715557cb4466aebc5040eea82f16e9c027f140d9',
                ),
                status='maintained',
            ),
        ),
        type='distribution',
        version=2,
    )

    def __init__(self):
        self.rosinstall_data = []

    def gen_distribution(self):
        # Create rviz, hal_hw_interface, redis_store distributions
        logging.info("Setting up distribution object")
        self.distro_file = DistributionFile(
            self.ROS_DISTRO, self.DISTRO_FILE_DATA
        )
        self.distro = Distribution(self.distro_file)

    def read_remote_package_xmls(self):
        self.package_xml_dict = {}
        for p in self.distro.repositories:
            logging.info("Reading distro xml files for %s" % p)
            for i in range(self.URL_RETRIES):
                try:
                    xmls = self.distro.get_source_repo_package_xmls(p)
                    break
                except URLError:
                    # Only raise URL errors on the last try
                    if i == self.URL_RETRIES - 1:
                        raise
                    else:
                        logging.warn("Error loading URL; retrying")
                except Exception:
                    raise
            self.package_xml_dict.update(xmls)

    def extract_deps_from_xmls(self):
        logging.info("Extracting deps from packages")
        self.remote_deps = set()
        for p in self.package_xml_dict:
            root = ET.fromstring(self.package_xml_dict[p][1].encode('utf-8'))
            for child in root:
                if not child.tag.endswith('depend'):
                    continue
                dep = child.text
                logging.debug(
                    "Adding dep %s from package %s type %s"
                    % (dep, p, child.tag)
                )
                self.remote_deps.add(dep)
        # Remove the inputs
        self.custom_distro_packages = set(self.package_xml_dict.keys())
        logging.info("Remote deps:  %s" % ' '.join(list(self.remote_deps)))
        logging.info(
            "Customized distro packages to exclude:  %s"
            % ' '.join(list(self.custom_distro_packages))
        )

    def gen_remote_deps(self):
        self.gen_distribution()
        self.read_remote_package_xmls()
        self.extract_deps_from_xmls()

    def gen_local_deps(self):
        packages = find_packages('src')
        self.local_deps = set()
        for pkg in packages.values():
            for d in (
                pkg.build_depends + pkg.buildtool_depends + pkg.run_depends
            ):
                self.local_deps.add(d.name)
        # Prune packages in src/ directory
        self.local_packages = set(packages.keys())
        logging.info("Local deps:  %s" % ' '.join(list(self.local_deps)))
        logging.info(
            "Local excludes:  %s" % ' '.join(list(self.local_packages))
        )

    def run_rosinstall_generator(
        self, dep_list, excludes=list(), deps=True, max_tries=3
    ):
        # This fails often with e.g.
        #     IOError: CRC check failed 0xc303deac != 0x8e2a726aL
        while max_tries > 0:
            try:
                self.rosinstall_data = generate_rosinstall(
                    self.ROS_DISTRO,
                    dep_list,
                    deps=deps,
                    wet_only=True,
                    tar=True,
                    excludes=excludes,
                )
                break
            except OSError:
                logging.info("IOError reading distro; retrying")
                max_tries -= 1

    def remove_custom_distros(self):
        logging.info("Removing upstream source repos customized here")
        to_pop = []  # Don't pop while scanning array
        for i, repo in enumerate(self.rosinstall_data):
            repo_type = list(repo.keys())[0]
            if (
                repo[repo_type]['local-name']
                in self.DISTRO_FILE_DATA['repositories']
            ):
                to_pop.append(i)
        for i in to_pop:
            repo = self.rosinstall_data.pop(i)
            repo_type = repo.keys()[0]
            logging.info("  Removed repo %s" % repo[repo_type]['local-name'])

    def add_custom_distros(self):
        logging.info("Adding custom source repos:")
        for repo_name, repo_data in self.DISTRO_FILE_DATA[
            'repositories'
        ].items():
            source_data = repo_data['source']
            repo = {
                source_data['type']: {
                    'local-name': repo_name,
                    'uri': source_data['url'],
                    'version': source_data['version'],
                }
            }
            logging.info("  %s" % repo_name)
            self.rosinstall_data.append(repo)

    def dump_rosinstall(self, image_name):
        fname = '%s.rosinstall' % self.ROS_DISTRO
        logging.info("Dumping final file %s" % fname)
        data_sorted = sort_rosinstall(self.rosinstall_data)
        with open(fname, 'w') as f:
            yaml.dump(data_sorted, stream=f, default_flow_style=False)

    @property
    def dep_list(self):
        return sorted(
            (self.local_deps | self.remote_deps)
            - (self.local_packages | self.custom_distro_packages)
        )

    def update_base(self):
        # Generate a .rosinstall file with deps for local packages and
        # deps for custom repos
        self.gen_remote_deps()
        self.gen_local_deps()
        logging.info("Extracted deps:  %s" % " ".join(self.dep_list))
        self.run_rosinstall_generator(
            self.dep_list, excludes=self.CUSTOM_PACKAGES + self.EXCLUDE_PACKAGES
        )
        self.remove_custom_distros()
        self.dump_rosinstall('ros_base')

    def update_custom(self):
        # Generate a .rosinstall file for just custom repos
        # self.run_rosinstall_generator(
        #     self.CUSTOM_PACKAGES, excludes=self.EXCLUDE_PACKAGES, deps=False
        # )
        self.add_custom_distros()
        self.dump_rosinstall('ros_custom')


if __name__ == "__main__":
    # RosinstallUpdater().update_base()
    RosinstallUpdater().update_custom()
