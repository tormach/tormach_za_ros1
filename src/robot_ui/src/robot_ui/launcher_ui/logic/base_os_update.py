from pp_ros_launch.launcher.base_os_updater import standard_update

import logging

from PySide6.QtCore import (
    QObject,
    Signal,
)
from PySide6.QtQml import QmlElement

import qasync

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class BaseOSUpdate(QObject):
    updateFinished = Signal()

    logger = logging.getLogger('launcher.base_os_update')

    def __init__(self, parent=None):
        super().__init__(parent)

    @qasync.asyncSlot()
    async def updateBaseSystem(self) -> None:
        self.logger.info('Starting the Base OS update')
        updated = await standard_update()
        if updated:
            self.logger.info(
                'Base OS update or checking executed successfully!'
            )
        else:
            self.logger.warning('Could not update the base OS!')
        self.updateFinished.emit()
