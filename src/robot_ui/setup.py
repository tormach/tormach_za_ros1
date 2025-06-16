# ! DO NOT MANUALLY INVOKE THIS setup.py, USE CATKIN INSTEAD

from catkin_pkg.python_setup import generate_distutils_setup
from distutils.core import setup

import os
import re
from distutils.command.install_lib import install_lib
from distutils import log

# Replacement for setuptools.find_packages() and
# setup(include_package_data=[...]); setuptools isn't recommended with
# catkin[1], and spews warnings
#
# [1]: http://docs.ros.org/melodic/api/catkin/html/user_guide/setup_dot_py.html
#
# _________________________________________________________________________
# Warnings   << robot_ui:install [...]/logs/robot_ui/build.install.008.log
# zip_safe flag not set; analyzing archive contents...
# robot_ui.pathpilot.base.resource_paths: module references __file__
# robot_ui.pathpilot.development.project_browser: module references __file__
# cd [...]/build/robot_ui; catkin build --get-env robot_ui | catkin env -si  /usr/bin/make install; cd -
# .........................................................................


def find_packages(path):
    return [
        re.sub('^[^A-z0-9_]+', '', root[len(path) + 1 :].replace('/', '.'))
        for root, dirs, files in os.walk(path)
        if '__init__.py' in files and not root.endswith('/tests')
    ]


def find_data():
    topdir = 'src/robot_ui'
    res = set()
    for root, dirs, files in os.walk(topdir):
        subdir = root[len(topdir) + 1 :]
        for f in files:
            if f == 'qmldir':
                res.add(subdir + '/qmldir')
            for ext in (
                '.png',
                '.jpg',
                '.svg',
                '.svgz',
                '.qml',
                '.ttf',
                '.qm',
                '.json',
                '.scxml',
                '.yaml',
                '.stl',
            ):
                if f.endswith(ext):
                    res.add(f'{subdir}/*{ext}')
            if subdir.startswith('pathpilot/robot/program/templates/'):
                res.add(f'{subdir}/{f}')
    return {'robot_ui': list(res)}


# Catkin build runs something like this:
#
# python setup.py \
#     build --build-base ${CMAKE_CURRENT_SOURCE_DIR} \
#     install \
#     $DESTDIR_ARG \
#     --install-layout=deb --prefix=${CMAKE_INSTALL_PREFIX} \
#     --install-scripts=${CMAKE_INSTALL_PREFIX}/${CATKIN_GLOBAL_BIN_DESTINATION}

# In setuptools, convert this to a binary-only distribution by
# replacing that with something like this:
#
# python setup.py \
#     build --build-base ${CMAKE_CURRENT_BINARY_DIR} \
#     bdist_egg --exclude-source-files --dist-dir=@GEN_DIR@/egg
# easy_install \
#     --no-deps --prefix=${CMAKE_INSTALL_PREFIX} --always-unzip \
#     --script-dir="${CMAKE_INSTALL_PREFIX}/${CATKIN_GLOBAL_BIN_DESTINATION}" \
#     ${PROJECT_NAME}-*-py*.egg


class InstallLibSourceless(install_lib):
    def remove_uncompiled_python(self, package):
        path = os.path.join(self.install_dir, package.replace('.', '/'))
        log.info("Removing uncompiled python sources in " + path)
        for f in os.listdir(path):
            file_path = os.path.join(path, f)
            if os.path.isdir(file_path):
                continue
            if f == '__init__.py':
                continue
            if not f.endswith('.py'):
                continue
            if not os.path.exists(file_path + 'c'):
                continue  # Don't erase uncompiled sources
            os.unlink(file_path)

    def run(self):
        install_lib.run(self)
        for p in self.distribution.packages:
            self.remove_uncompiled_python(p)


# fetch values from package.xml
setup_args = generate_distutils_setup(
    packages=find_packages('src'),
    package_dir={'': 'src'},
    # Patch install_lib command
    cmdclass=dict(install_lib=InstallLibSourceless),
    package_data=find_data(),
)

setup(**setup_args)
