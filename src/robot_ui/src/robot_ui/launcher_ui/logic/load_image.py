from pp_ros_launch.launcher.updates import Updater, UpdaterException
import logging

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
class LoadImage(QObject):
    loadingLayerNumberChanged = Signal(int)
    loadingLayerProgressChanged = Signal(int)
    validImagesExistChanged = Signal(bool)
    invalidImagesExistChanged = Signal(bool)
    outputErrorExistsChanged = Signal(bool)
    validImagesChanged = Signal(str)
    invalidImagesChanged = Signal(str)
    outputErrorChanged = Signal(str)
    loadCompleted = Signal()
    loadStarted = Signal()

    logger = logging.getLogger('launcher.image_file_loader')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._load_layer_number: int = 0
        self._load_layer_progress: int = 0
        self._valid_images_exist: bool = False
        self._invalid_images_exist: bool = False
        self._output_error_exists: bool = False
        self._valid_images: list = []
        self._invalid_images: list = []
        self._output_error = None
        self._load_thread = None
        self._path = ''
        self.logger.info('Created.')

    @qasync.asyncSlot(str)
    async def startLoading(self, path: str) -> None:
        self.logger.info('Start loading new image.')
        self._zero_all_properties()
        self._path = path
        self.loadStarted.emit()

        output_error: str = ""
        output: dict = dict()
        try:
            output = await Updater.load(path, self.update_status)
        except UpdaterException as e:
            error: str = str(e.args[0])
            # This probably has no place here, however it is
            # so common error and Docker itself
            # refuses to get a proper (human readable) varning:
            # https://github.com/moby/moby/issues/19566
            if error.endswith('no such file or directory'):
                error = self.tr('File specified is not valid Container image!')
            output_error = error
        except RuntimeError as e:
            self.logger.error(f"RuntimeError occured: {e}")

        self.logger.info(f"Loading from file {self._path} finished!")
        vi: list = output.get('valid_images', list())
        ini: list = output.get('error_images', list())
        error: str = output_error if output_error != "" else None

        if vi:
            self._valid_images = vi
            self.validImagesChanged.emit(self.validImages)
            self._valid_images_exist = True
        else:
            self._valid_images_exist = False
        self.validImagesExistChanged.emit(self.validImagesExist)

        if ini:
            self._invalid_images = ini
            self.invalidImagesChanged.emit(self.invalidImages)
            self._invalid_images_exist = True
        else:
            self._invalid_images_exist = False
        self.invalidImagesExistChanged.emit(self.invalidImagesExist)

        if error is not None:
            self._output_error = error
            self.outputErrorChanged.emit(self.outputError)
            self._output_error_exists = True
        else:
            self._output_error_exists = False
        self.outputErrorExistsChanged.emit(self.outputErrorExists)

        self.loadCompleted.emit()

    def update_status(self, layer: int, progress: int):
        self.loadingLayerNumberChanged.emit(layer)
        self.loadingLayerProgressChanged.emit(progress)
        if (layer, progress) != (
            self._load_layer_number,
            self._load_layer_progress,
        ):
            self._load_layer_number = layer
            self._load_layer_progress = progress
            self.logger.debug(
                f"...loading progress:  layer={layer}; progress={progress}"
            )

        self.logger.info(f"Loading Docker image from path {self._path}")

    def _zero_all_properties(self) -> None:
        self._load_layer_number = 0
        self._load_layer_progress = 0
        self._valid_images_exist = False
        self._valid_images_exist = False
        self._output_error_exists = False
        self._valid_images = []
        self._invalid_images = []
        self._output_error = None

        self.loadingLayerNumberChanged.emit(self.layerLoadingNumber)
        self.loadingLayerProgressChanged.emit(self.loadingLayerProgressChanged)
        self.validImagesExistChanged.emit(self.validImagesExist)
        self.invalidImagesExistChanged.emit(self.invalidImagesExist)
        self.outputErrorExistsChanged.emit(self.outputErrorExists)
        self.validImagesChanged.emit(self.validImages)
        self.invalidImagesChanged.emit(self.invalidImages)
        self.outputErrorChanged.emit(self.outputError)

    @Property(bool, notify=validImagesExistChanged)
    def validImagesExist(self) -> bool:
        return self._valid_images_exist

    @Property(bool, notify=invalidImagesExistChanged)
    def invalidImagesExist(self) -> bool:
        return self._invalid_images_exist

    @Property(bool, notify=outputErrorExistsChanged)
    def outputErrorExists(self) -> bool:
        return self._output_error_exists

    @Property(str, notify=validImagesChanged)
    def validImages(self) -> str:
        return '\n'.join(self._valid_images)

    @Property(str, notify=invalidImagesChanged)
    def invalidImages(self) -> str:
        return '\n'.join(self._invalid_images)

    @Property(str, notify=outputErrorChanged)
    def outputError(self) -> str:
        return self._output_error if self._output_error is not None else ''

    @Property(int, notify=loadingLayerNumberChanged)
    def layerLoadingNumber(self) -> int:
        return self._load_layer_number

    @Property(int, notify=loadingLayerProgressChanged)
    def layerLoadingProgress(self) -> int:
        return self._load_layer_progress
