import shlex
import logging

from PySide6.QtCore import (
    QObject,
    QProcess,
    QTimer,
    Slot,
    Property,
    Signal,
)
from PySide6.QtQml import QmlElement

from robot_ui.pathpilot.qt_helpers import ensure_cleanup

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class RosLauncher(QObject):
    """
    Launches ROS launch files.
    """

    KILL_TIMEOUT_MS = 5000

    runningChanged = Signal(bool)
    rosPackageChanged = Signal(str)
    executableChanged = Signal(str)
    argsChanged = Signal(str)

    logger = logging.getLogger('launcher.roslauncher')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._package = ''
        self._executable = ''
        self._args = ''
        self._running = False

        self._process = QProcess()
        self._process.setProcessChannelMode(QProcess.ForwardedChannels)
        self._process.started.connect(self._on_started)
        self._process.finished.connect(self._on_finished)

        self._kill_timer = QTimer(self)
        self._kill_timer.setInterval(self.KILL_TIMEOUT_MS)
        self._kill_timer.timeout.connect(self._kill_process)

        ensure_cleanup(self.stop)

    @Slot()
    def start(self):
        line = f'{self._package} {self._executable} {self._args}'
        self.logger.info("Launch command:  '%s'" % line)
        self._process.start('roslaunch', shlex.split(line))

    @Slot()
    def stop(self):
        if not self._running:
            return
        self.logger.warning("Terminating executable %s" % self._executable)
        self._process.terminate()
        self._kill_timer.start()

    def _on_started(self):
        self._running = True
        self.runningChanged.emit(True)
        self.logger.info("Executable %s now running" % self._executable)

    def _on_finished(self, _exit_code, _exit_status):
        self._running = False
        self.runningChanged.emit(True)
        self._kill_timer.stop()
        self.logger.info(
            "Executable %s exited code %s, status %s"
            % (self._executable, _exit_code, _exit_status)
        )

    def _kill_process(self):
        self.logger.warning("Timeout; killing executable %s" % self._executable)
        self._process.kill()

    @Property(bool, notify=runningChanged)
    def running(self):
        return self._running

    @Property(str, notify=executableChanged)
    def executable(self):
        return self._executable

    @executable.setter
    def executable(self, value):
        if value == self._executable:
            return
        self._executable = value
        self.executableChanged.emit(value)

    @Property(str, notify=rosPackageChanged)
    def rosPackage(self):
        return self._package

    @rosPackage.setter
    def rosPackage(self, value):
        if value == self._package:
            return
        self._package = value
        self.rosPackageChanged.emit(value)

    @Property(str, notify=argsChanged)
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if value == self._args:
            return
        self._args = value
        self.argsChanged.emit(value)
