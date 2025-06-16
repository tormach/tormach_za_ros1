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
from .signal_handler import SignalHandler

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProcessLauncher(QObject):
    """
    Launches processes.
    """

    KILL_TIMEOUT_MS = 30000  # Matches run_pp_ros setting

    runningChanged = Signal(bool)
    executableChanged = Signal(str)
    argsChanged = Signal(str)
    statusChanged = Signal(str)
    exitedChanged = Signal(bool)

    logger = logging.getLogger('launcher.process')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._executable = ''
        self._args = ''
        self._running = False
        self._exited = False

        self._process = QProcess()
        self._process.setProcessChannelMode(QProcess.ForwardedChannels)
        self._process.started.connect(self._on_started)
        self._process.finished.connect(self._on_finished)

        self._kill_timer = QTimer(self)
        self._kill_timer.setInterval(self.KILL_TIMEOUT_MS)
        self._kill_timer.timeout.connect(self._kill_process)

        ensure_cleanup(self.stop)

        self._update_status('Not started')

    @property
    def commandline(self):
        return f'{self._executable} {self._args}'

    def _update_status(self, status):
        self._status = status
        self.statusChanged.emit(status)

    def _register_shutdown_callback(self, unregister=False):
        SignalHandler.register_shutdown_callback(
            self.commandline, self._shutdown_cb, unregister=unregister
        )

    def _shutdown_cb(self):
        if self._process.processId() == 0:
            self.logger.info(
                "Process already exited in _shutdown_cb; command:  '%s'"
                % self.commandline
            )
        else:
            self.logger.warning(
                "Killing process ID %s; command: '%s'"
                % (self._process.processId(), self.commandline)
            )
            self._process.terminate()

    @Slot()
    def start(self):
        self.logger.info("Starting process; command:  '%s'" % self.commandline)
        self._process.start(self._executable, shlex.split(self._args))
        self._register_shutdown_callback()
        self._update_status('Started...')

    @Slot()
    def stop(self):
        if not self._running:
            return
        self.logger.warning(
            "Terminating process; command:  '%s'" % self.commandline
        )
        self._process.terminate()
        self._kill_timer.start()
        self._update_status('Stopping...')

    def _on_started(self):
        self._running = True
        self.runningChanged.emit(True)
        self.logger.info("Process running; command:  '%s'" % self.commandline)
        self._update_status('Started, please wait')

    def _on_finished(self, _exit_code, _exit_status):
        self._register_shutdown_callback(unregister=True)
        self._running = False
        self.runningChanged.emit(False)
        self._kill_timer.stop()
        self._exited = True
        self.exitedChanged.emit(True)
        self.logger.info(
            "Process exited code %s, status %s; command:  %s"
            % (_exit_code, _exit_status, self.commandline)
        )
        self._update_status('Exited code %s' % _exit_code)

    def _kill_process(self):
        self.logger.warning(
            "Timeout, killing process; command:  %s" % self.commandline
        )
        self._process.kill()
        self._update_status('Failed to exit, killing...')

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @Property(bool, notify=runningChanged)
    def running(self):
        return self._running

    @Property(bool, notify=exitedChanged)
    def exited(self):
        return self._exited

    @Property(str, notify=executableChanged)
    def executable(self):
        return self._executable

    @executable.setter
    def executable(self, value):
        if value == self._executable:
            return
        self._executable = value
        self.executableChanged.emit(value)

    @Property(str, notify=argsChanged)
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if value == self._args:
            return
        self._args = value
        self.argsChanged.emit(value)
