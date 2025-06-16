import os
import semver
import sh
import rospy
import re


from PySide6.QtCore import QObject, Property
from PySide6.QtQml import QmlElement, QmlSingleton

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class SoftwareVersion(QObject):
    """Interface for querying and displaying software package version."""

    def __init__(self, parent=None):
        super().__init__(parent)

        git_rev_environment = None
        # Theoretically every image should be either DEVEL or DIST, but logic
        # should survive if no ENV is set with suitable default values
        image_type_evironment = os.getenv('IMAGE_TYPE', None)
        # PRESUMPTION: Only released version images have the RELEASE_CODENAME
        # environment variable set
        codename_environment = (
            os.getenv('RELEASE_CODENAME', None)
            if image_type_evironment == 'dist'
            else None
        )
        if codename_environment:
            self._codename = codename_environment
        else:
            # Development versions of both DIST and DEVEL images
            self._codename = self.tr("Unofficial release")
            git_rev_environment = os.getenv('GIT_REV', None)
            # For development DIST and DEVEL types of image show git SHA
            #   DIST type of image have the GIT_REV set as an environment variable,
            #   in other cases presume that there is a git tree and try to get the SHA
            #   dynamically
            if git_rev_environment is None or image_type_evironment == 'devel':
                try:
                    git_rev_environment = sh.git(
                        'rev-parse',
                        '--short',
                        'HEAD',
                        _cwd=os.path.dirname(os.path.realpath(__file__)),
                        _tty_out=False,
                    ).strip()
                except Exception as e:
                    rospy.logerr(
                        f"Error occured during querying for git SHA: {e}"
                    )
                    git_rev_environment = self.tr("Unknown SHA")

                try:
                    git_branch_name = sh.git(
                        'branch',
                        '--show-current',
                        _cwd=os.path.dirname(os.path.realpath(__file__)),
                        _tty_out=False,
                    ).strip()
                    self._codename = git_branch_name
                except Exception as e:
                    rospy.logerr(
                        f"Error occured during querying for git branch name: {e}"
                    )

        try:
            version_environment = semver.VersionInfo.parse(
                os.environ['RELEASE_VERSION']
            )
        except (ValueError, KeyError) as e:
            rospy.logerr(
                f"Error occured during querying for PathPilot Version: {e}"
            )
            self._version = self.tr("Unknown version")
        else:
            self._version = (
                str(version_environment)
                if codename_environment
                else f"{version_environment}+{git_rev_environment}"
            )

        robot_configuration_environment = os.getenv('ROBOT_CONFIGURATION', None)
        if robot_configuration_environment is not None:
            self._robot = robot_configuration_environment
        else:
            # TODO: Do not have lookup tables strewn in the codebase,
            #       decide on one place and put it there
            robot_model_environment = os.getenv('ROBOT_MODEL', None)
            if robot_model_environment == 'za':
                self._robot = 'ZA6'
            else:
                self._robot = self.tr('Unknown robot model')

        def find_first_za_with_optional_number(text):
            pattern = r'ZA\d*'
            match = re.search(pattern, text)
            return match.group() if match else None

        self._model = (
            find_first_za_with_optional_number(robot_configuration_environment)
            if robot_configuration_environment is not None
            else 'ZA6'
        )

    @Property(str, constant=True)
    def version(self) -> str:
        return self._version if self._version else ''

    @Property(str, constant=True)
    def codename(self) -> str:
        return self._codename if self._codename else ''

    @Property(str, constant=True)
    def robot(self) -> str:
        return self._robot if self._robot else ''

    @Property(str, constant=True)
    def model(self) -> str:
        return self._model if self._model else ''
