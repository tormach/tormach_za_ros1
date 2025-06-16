from pp_ros_launch.launcher.updates import Updater
import logging
from . import qt_launcher_image_version_helper

from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
)
from PySide6.QtQml import QmlElement

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class EULAAgreement(QObject):
    eulaAgreed = Signal()
    eulaChanged = Signal(str)

    logger = logging.getLogger('launcher.eula_checker')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._default_version_image = None

    @qasync.asyncSlot()
    async def check_eula(self) -> None:
        self.logger.warning('Checking for EULA agreement on default image')
        if await Updater.check_eula_agreement():
            self.eulaAgreed.emit()
            self.logger.debug("EULA was already agreed upon!")
        else:
            self._default_version_image = await Updater.get_default_image()
            self.eulaChanged.emit(self.eula)
            self.logger.warning(
                f"User has to agree to EULA of {self._default_version_image.version} version first!"
            )

    @qasync.asyncSlot()
    async def agree_to_eula(self) -> None:
        if self._default_version_image is None:
            logging.error(
                'Trying to agree to EULA of non existing version image!'
            )
            return
        logging.warning(
            f'User agreed to the EULA of version {self._default_version_image.version}'
        )
        await Updater.agree_with_eula()
        self.eulaAgreed.emit()

    @Property(str, notify=eulaChanged)
    def eula(self) -> str:
        return qt_launcher_image_version_helper.get_eula(
            self._default_version_image, self
        )
