import os
import re
from setuptools import setup


def read(*names, **kwargs):
    try:
        with open(
            os.path.join(os.path.dirname(__file__), *names),
            encoding=kwargs.get("encoding", "utf8"),
        ) as fp:
            return fp.read()
    except OSError:
        return ''


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


long_description = read('README.md')


setup(
    name="robot_command-stubs",
    url="https://tormach.atlassian.net/wiki/spaces/TRB/pages/1930690719/Tormach+Robot+Programming+Language",
    author="Alexander Rössler",
    maintainer="Alexander Rössler",
    maintainer_email="alex@machinekoder.com",
    description="PEP561 stub files for the robot_command package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=find_version('robot_command-stubs', '__init__.pyi'),
    python_requires=">= 3.7",
    package_data={"robot_command-stubs": ['*.pyi']},
    packages=["robot_command-stubs"],
    tests_require=[],
    extras_require={"build": []},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development",
    ],
)
