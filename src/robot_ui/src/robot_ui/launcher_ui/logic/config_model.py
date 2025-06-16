import logging
from enum import IntEnum, auto
from collections import namedtuple
from pp_ros_launch.system import SystemChecks
from pp_ros_launch.launcher.updates import Updater

from PySide6.QtCore import (
    QAbstractItemModel,
    QByteArray,
    QModelIndex,
    Qt,
    QThread,
    QEnum,
    Signal,
    Slot,
    Property,
)
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

Config = namedtuple('Config', 'name pprlaunch_args roslaunch_args')


@QmlElement
class ConfigModel(QAbstractItemModel):
    class Roles(IntEnum):
        NameRole = Qt.UserRole
        PPRLArgsRole = auto()
        ROSLArgsRole = auto()

    QEnum(Roles)

    _ROLE_NAMES = {
        Roles.NameRole: QByteArray(b'name'),
        Roles.PPRLArgsRole: QByteArray(b'pprlargs'),
        Roles.ROSLArgsRole: QByteArray(b'roslargs'),
    }

    checkCompleted = Signal()
    defaultIndexChanged = Signal(int)
    errorChanged = Signal(str)

    logger = logging.getLogger('launcher.config')

    def __init__(self, parent=None):
        super().__init__(parent)

        self._configs = []
        self._default_index = 0
        self._error_message = ''

    def _clean_state(self) -> None:
        self._error_message = ''
        self.errorChanged.emit(self.errorStatus)
        self._configs = []

    @Slot()
    def loadConfigs(self):
        self.logger.info("Checking system and loading configurations...")
        self.beginResetModel()
        self._clean_state()

        class CheckThread(QThread):
            checkingComplete = Signal()
            logger = logging.getLogger('launcher.config.check')

            checkComplete = Signal(list, str)

            def __init__(self):
                super().__init__()
                self._system_checks = SystemChecks()

            def _print_dict(self, printee: dict, depth: int = 0) -> str:
                retstring = ''
                _newline = '\n'
                _depth = depth
                for key, value in printee.items():
                    retstring += f"{_depth*'    '}{str(key).replace('_',' ').upper()}: {str(value) + _newline if not isinstance(value,dict) else _newline + self._print_dict(value, _depth+1)}"
                return retstring

            def run(self) -> None:
                self._system_checks.clear_cache()
                checks = self._system_checks
                av_configs, messages = checks.available_configurations()
                staged_image_version = Updater.get_set_image_main_number()
                if isinstance(staged_image_version, str):
                    staged_image_version = int(staged_image_version)

                configs = []

                for key, value in av_configs.items():
                    pprlaunch_args, roslaunch_args = value
                    configs.append(
                        Config(
                            name=key,
                            pprlaunch_args=pprlaunch_args,
                            roslaunch_args=roslaunch_args,
                        )
                    )
                error_message = ''
                if messages:
                    # There was an error:
                    error_message = self._print_dict(messages)
                if not configs:
                    error_message += self.tr("No runnable configuration found!")

                if self._system_checks.logs():
                    self.logger.info(self._system_checks.logs())

                self.checkComplete.emit(configs, error_message)

        self._check_thread = CheckThread()
        self._check_thread.checkComplete.connect(self._on_check_complete)
        self._check_thread.start()

    def _on_check_complete(self, configurations: list, error_msg: str) -> None:
        self.logger.info("Checking for configurations finished!")
        self._default_index = 0
        self._configs = configurations
        if error_msg != '':
            self._error_message = error_msg
            self.errorChanged.emit(self.errorStatus)
        self.defaultIndexChanged.emit(self._default_index)
        self.endResetModel()
        self._check_thread.wait()
        del self._check_thread
        self._check_thread = None

        self.checkCompleted.emit()

    @Property(int, notify=defaultIndexChanged)
    def defaultIndex(self):
        return self._default_index

    def data(self, index, role):
        if not index.isValid():
            return None

        if not 0 <= index.row() < len(self._configs):
            return None

        config = self._configs[index.row()]
        switch = {
            Qt.DisplayRole: lambda: config.name,
            self.Roles.NameRole: lambda: config.name,
            self.Roles.PPRLArgsRole: lambda: config.pprlaunch_args,
            self.Roles.ROSLArgsRole: lambda: config.roslaunch_args,
        }
        return switch.get(role, lambda: None)()

    def roleNames(self):
        return self._ROLE_NAMES

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        try:
            item = self._configs[row]
        except IndexError:
            return QModelIndex()
        else:
            return self.createIndex(row, column, item)

    def parent(self, _index):
        return QModelIndex()

    def columnCount(self, _parent):
        return len(self._ROLE_NAMES)

    def rowCount(self, parent=QModelIndex()):
        if parent == QModelIndex():
            return len(self._configs)
        else:
            return 0

    @Property(str, notify=errorChanged)
    def errorStatus(self) -> str:
        return self._error_message
