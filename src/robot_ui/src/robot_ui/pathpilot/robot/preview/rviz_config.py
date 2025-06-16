import os
import shutil
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    Property,
    Signal,
    Slot,
    QStandardPaths,
)
from PySide6.QtQml import QmlElement

import rospy
import ruamel.yaml

QML_IMPORT_NAME = 'pathpilot.robot.preview'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class RvizConfig(QObject):
    sourceChanged = Signal()
    targetChanged = Signal()

    CONFIG_NAME_SCHEME = "config_{0}.rviz"

    def __init__(self, parent=None):
        super().__init__(parent)

        self._source = ""
        self._target = ""
        self._user_folder = ""
        self._user_config_path = QStandardPaths.writableLocation(
            QStandardPaths.ConfigLocation
        )

    @Property(str, notify=sourceChanged)
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if value == self._source:
            return

        self._source = value
        self.sourceChanged.emit()

    @Property(str, notify=targetChanged)
    def target(self):
        return self._target

    @Slot()
    def createUserConfig(self):
        if not self.source:
            rospy.logerr(self.tr("No source config set"))
            return

        index = 1
        while True:
            config_name = self.CONFIG_NAME_SCHEME.format(index)
            config_path = Path(self._user_config_path) / config_name
            if not config_path.exists():
                break
            index += 1

        source_path = Path(self.source)
        if not source_path.exists():
            rospy.logerr("Source config does not exist")
            return

        try:
            os.makedirs(config_path.parent, exist_ok=True)
        except OSError as e:
            rospy.logerr(
                self.tr("Failed to create config directory: {}").format(e)
            )
            return

        try:
            shutil.copyfile(source_path, config_path)
        except OSError as e:
            rospy.logerr(self.tr("Failed to copy config file: {}").format(e))
            return

        # Modify Preferences/PromptSaveOnExit to true
        try:
            with open(config_path) as f:
                config = ruamel.yaml.load(f, Loader=ruamel.yaml.RoundTripLoader)
                config['Preferences']['PromptSaveOnExit'] = True
            with open(config_path, 'w') as f:
                ruamel.yaml.dump(config, f, Dumper=ruamel.yaml.RoundTripDumper)
        except OSError as e:
            rospy.logerr(self.tr("Failed to modify config file: {}").format(e))
            return

        self._target = config_path.as_posix()
        self.targetChanged.emit()
