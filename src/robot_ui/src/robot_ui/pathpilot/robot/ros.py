import os

import rospy
import rospkg
from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QmlElement, QmlSingleton
from robot_common.tools import get_param

from ..qt_helpers import MultiSlot

QML_IMPORT_NAME = 'pathpilot.robot'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class ROS(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @MultiSlot(str, [None, 'QVariant'], result='QVariant')
    def getParam(self, name, default=None):
        return get_param(name, default)

    @Slot(result=str)
    def getLogPath(self):
        log_dir = rospkg.get_log_dir()
        run_id = rospy.get_param('/run_id')
        return os.path.join(log_dir, run_id)
