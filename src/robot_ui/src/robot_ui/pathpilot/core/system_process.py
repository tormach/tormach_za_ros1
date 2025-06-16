import contextlib
import os
import signal
import shlex

import rospy

from PySide6.QtCore import (
    QObject,
    Slot,
    Signal,
    Property,
    QProcess,
    QCoreApplication,
)
from PySide6.QtQml import QmlElement

from ..qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'pathpilot.core'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class SystemProcess(QObject):
    """
    Starts, monitors, and stops a system process.

    The process is started when the active property is set to true and stopped
    when the active property is set to false. The command property is used to
    specify the command to run. The command is split into a list of arguments
    using shlex.split().

    Active is set to false when the process exits.
    """

    DEFAULT_SHUTDOWN_TIMEOUT_MS = 5000

    commandChanged = Signal()
    activeChanged = Signal()
    shutdownTimeoutMsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._process = None
        self._command = ""
        self._active = False
        self._shutdown_timeout_ms = self.DEFAULT_SHUTDOWN_TIMEOUT_MS
        self._exiting = False

        ensure_cleanup(self._stop_process)

    @Property(str, notify=commandChanged)
    def command(self):
        return self._command

    @command.setter
    def command(self, value):
        if value == self._command:
            return

        self._command = value
        self.commandChanged.emit()

    @Property(bool, notify=activeChanged)
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        if value == self._active:
            return

        self._active = value
        self.activeChanged.emit()

        if self._active:
            self._start_process()
        else:
            self._stop_process()

    @Property(int, notify=shutdownTimeoutMsChanged)
    def shutdownTimeoutMs(self):
        return self._shutdown_timeout_ms

    @shutdownTimeoutMs.setter
    def shutdownTimeoutMs(self, value):
        if value == self._shutdown_timeout_ms:
            return

        self._shutdown_timeout_ms = value
        self.shutdownTimeoutMsChanged.emit()

    @Slot()
    def start(self):
        self.active = True

    @Slot()
    def stop(self):
        self.active = False

    @Slot()
    def restart(self):
        self.active = False
        self.active = True

    def _start_process(self):
        proc = QProcess(self)
        command = self._command

        if not command:
            rospy.logerr(self.tr("No command specified"))
            self._active = False
            self.activeChanged.emit()
            return

        def output_error(error):
            if proc is not self._process:
                return
            app = QCoreApplication.instance()  # deleted QObject ref
            switch = {
                QProcess.FailedToStart: app.tr("failed to start"),
                QProcess.Crashed: app.tr("crashed"),
                QProcess.Timedout: app.tr("timed out"),
                QProcess.WriteError: app.tr("write error"),
                QProcess.ReadError: app.tr("read error"),
                QProcess.UnknownError: app.tr("unknown error"),
            }
            error_string = proc.errorString()
            rospy.logwarn(
                app.tr("Command {0} {1}: {2}").format(
                    command, switch.get(error, ''), error_string
                )
            )
            if proc is self._process:
                self._process = None
                with contextlib.suppress(RuntimeError):  # deleted QObject ref
                    self.active = False

        def finished(exit_code, exit_status):
            if proc is not self._process:
                return
            app = QCoreApplication.instance()  # deleted QObject ref
            if exit_status == QProcess.CrashExit and not self._exiting:
                message = app.tr("crashed")
                log = rospy.logerr
            else:
                message = app.tr("exited")
                log = rospy.loginfo

            log(
                app.tr("Command {0} {1} with exit code {2}").format(
                    command, message, exit_code
                )
            )
            if proc is self._process:
                self._process = None
                with contextlib.suppress(RuntimeError):  # deleted QObject ref
                    self.active = False

        self._exiting = False
        proc.errorOccurred.connect(output_error)
        proc.finished.connect(finished)
        cmd = shlex.split(command)
        proc.start(os.path.expanduser(cmd[0]), cmd[1:])
        self._process = proc

    @Slot()
    def _stop_process(self):
        if self._process is None:
            return
        self._process.errorOccurred.disconnect()  # ignore errors when killing
        self._exiting = True
        try:
            os.kill(self._process.processId(), signal.SIGINT)
        except ProcessLookupError:
            self._process.kill()
        if not self._process.waitForFinished(self._shutdown_timeout_ms):
            self._process.kill()
        self._process = None
