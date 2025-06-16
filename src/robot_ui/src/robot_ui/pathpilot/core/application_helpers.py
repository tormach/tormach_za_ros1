import os
import shlex

import rospy

from PySide6.QtCore import QObject, Slot, QUrl, QProcess
from PySide6.QtGui import QDesktopServices
from PySide6.QtQml import QmlSingleton, QmlElement, qmlEngine

from ..qt_helpers import MultiSlot

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
@QmlSingleton
class ApplicationHelpers(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._processes = []

    @Slot(QUrl, result=bool)
    def openUrlWithDefaultApplication(self, url):
        return QDesktopServices.openUrl(url)

    @Slot()
    def clearQmlComponentCache(self):
        qmlEngine(self).clearComponentCache()
        # maybe qmlClearTypeRegistrations

    @Slot(str)
    def runSystemCommand(self, command):
        proc = QProcess(self)

        def output_error(error):
            if proc not in self._processes:
                return
            switch = {
                QProcess.FailedToStart: self.tr("failed to start"),
                QProcess.Crashed: self.tr("crashed"),
                QProcess.Timedout: self.tr("timed out"),
                QProcess.WriteError: self.tr("write error"),
                QProcess.ReadError: self.tr("read error"),
                QProcess.UnknownError: self.tr("unknown error"),
            }
            error_string = proc.errorString()
            rospy.logerr(
                self.tr("Command {0} {1}: {2}").format(
                    command, switch.get(error, ''), error_string
                )
            )
            if proc in self._processes:
                self._processes.remove(proc)

        def finished(exit_code, exit_status):
            if proc not in self._processes:
                return
            switch = {
                QProcess.NormalExit: self.tr("exited"),
                QProcess.CrashExit: self.tr("crashed"),
            }
            log = (
                rospy.logerr
                if exit_status == QProcess.CrashExit
                else rospy.loginfo
            )
            log(
                self.tr("Command {0} {1} with exit code {2}").format(
                    command, switch.get(exit_status, ''), exit_code
                )
            )
            if proc in self._processes:
                self._processes.remove(proc)

        proc.errorOccurred.connect(output_error)
        proc.finished.connect(finished)
        cmd = shlex.split(command)
        proc.start(os.path.expanduser(cmd[0]), cmd[1:])
        self._processes.append(proc)

    @MultiSlot(str, [None, str], result=str)
    def getEnvVar(self, name, default=None):
        return os.environ.get(name, default)
