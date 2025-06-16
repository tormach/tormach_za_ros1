import logging

from PySide6.QtCore import QObject, Signal
from PySide6.QtQml import QmlElement, QmlSingleton

from pp_ros_launch.launcher.updates import Updater as PPUpdater

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class Updater(QObject):
    imageSelected = Signal()

    logger = logging.getLogger('launcher.updater')

    def __init__(self, parent=None):
        super().__init__(parent)

    @qasync.asyncSlot(str)
    async def setImage(self, image_name: str) -> None:
        if image_name is None or '':
            raise RuntimeError("Image name is empty!")
        self.logger.info(f"Setting Docker image tag {image_name}")
        await PPUpdater.set_image(image_name)
        self.imageSelected.emit()
