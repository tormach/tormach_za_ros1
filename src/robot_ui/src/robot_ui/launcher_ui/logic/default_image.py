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
class DefaultImage(QObject):
    loadingCompleted = Signal()
    defaultNotFound = Signal()
    versionChanged = Signal(str)
    codenameChanged = Signal(str)
    descriptionChanged = Signal(str)
    creationDateChanged = Signal(str)
    tagChanged = Signal(str)
    nameChanged = Signal(str)

    logger = logging.getLogger('launcher.default_image')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._default_launcher_image = None

    @qasync.asyncSlot()
    async def loadDefaultImage(self) -> None:
        self.logger.debug("Looking for default image")
        _default_image = await Updater.get_default_image()
        if _default_image is None:
            self.logger.warning("No default image found")
            self.defaultNotFound.emit()
            return
        else:
            self.logger.debug("Default image found")
            self._default_launcher_image = _default_image
        self.loadingCompleted.emit()
        self.versionChanged.emit(self.version)
        self.codenameChanged.emit(self.codename)
        self.descriptionChanged.emit(self.description)
        self.creationDateChanged.emit(self.creationDate)
        self.tagChanged.emit(self.tag)

    @Property(str, notify=versionChanged)
    def version(self) -> str:
        return qt_launcher_image_version_helper.get_version(
            self._default_launcher_image, self
        )

    @Property(str, notify=codenameChanged)
    def codename(self) -> str:
        return qt_launcher_image_version_helper.get_codename(
            self._default_launcher_image, self
        )

    @Property(str, notify=descriptionChanged)
    def description(self) -> str:
        return qt_launcher_image_version_helper.get_description(
            self._default_launcher_image, self
        )

    @Property(str, notify=creationDateChanged)
    def creationDate(self) -> str:
        return qt_launcher_image_version_helper.get_creation_date(
            self._default_launcher_image, self
        )

    @Property(str, notify=tagChanged)
    def tag(self):
        return (
            self._default_launcher_image.tag
            if self._default_launcher_image
            else ""
        )

    @Property(str, notify=nameChanged)
    def name(self):
        return (
            self._default_launcher_image.name
            if self._default_launcher_image
            else ""
        )
