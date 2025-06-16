import logging
from pp_ros_launch.launcher.rpcinterface import (
    SupervisorClient,
    SupervisorClientError,
)

from PySide6.QtCore import QObject, QTimer, Slot, Property, Signal
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'launcher_ui.logic'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

# FIXME
logging.basicConfig()


@QmlElement
class SupervisorLauncher(QObject):
    """
    Launches supervisord processes.
    """

    MONITOR_INTERVAL_MS = 1000

    processNameChanged = Signal(str)
    argsChanged = Signal(str)
    runningChanged = Signal(bool)
    stoppedChanged = Signal(bool)
    busyChanged = Signal(bool)
    errorChanged = Signal(bool)
    statusChanged = Signal(str)

    logger = logging.getLogger('launcher.supervisor')

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process_name = ''
        self._args = ''
        self._running = False
        self._stopped = True
        self._busy = False
        self._error = False
        self._status = None

        # Set up monitoring timer
        self._monitor_timer = QTimer()
        self._monitor_timer.setInterval(self.MONITOR_INTERVAL_MS)
        self._monitor_timer.timeout.connect(self._monitor_update)
        self.destroyed.connect(lambda: self._monitor_timer.stop())

        self.logger.info("Initialized SupervisorLauncher object")

    @Slot()
    def start(self):
        # FIXME  This needs to run in a non-blocking thread
        self.logger.info("Starting supervisor process %s" % self._process_name)
        try:
            self._client.start_process()
        except SupervisorClientError as e:
            self.logger.critical("Unable to start:  %s" % e.message)
            self._set_state(running=False, stopped=False, error=True)
            return
        self.logger.info("Supervisor process started")
        self._monitor_timer.start()

    @Property(str, notify=processNameChanged)
    def processName(self):
        return self._process_name

    @processName.setter
    def processName(self, value):
        if value == self._process_name:
            return
        self.logger.info(
            "Setting supervisor launcher process name to '%s'" % value
        )

        self._process_name = value
        self.processNameChanged.emit(value)
        self._client = SupervisorClient(value)

    @Property(str, notify=argsChanged)
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if value == self._args:
            return
        self._args = value
        self.argsChanged.emit(value)

    @Property(bool, notify=runningChanged)
    def running(self):
        return self._running

    @Property(bool, notify=stoppedChanged)
    def stopped(self):
        return self._stopped

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=errorChanged)
    def error(self):
        return self._error

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    def _set_state(self, running, stopped, error=None):
        if self._running != running:
            self._running = running
            self.runningChanged.emit(running)
        if self._stopped != stopped:
            self._stopped = stopped
            self.stoppedChanged.emit(stopped)
            if stopped:
                self._monitor_timer.stop()
        if error is not None and self._error != error:
            self._error = error
            self.errorChanged.emit(error)

        # Start busy icon
        if running or stopped:
            if self._busy:
                self._busy = False
                self.busyChanged.emit(False)
        else:
            if not self._busy:
                self._busy = True
                self.busyChanged.emit(True)

    def _monitor_update(self):
        new_status = self._client.process_state
        if self._status == new_status:
            return  # Nothing changed

        self._status = new_status
        self.statusChanged.emit(new_status)
        self.logger.info(
            f"Process {self._process_name} status changed to {new_status}"
        )
        if new_status == "STOPPED":
            self.logger.info(
                "Supervisor process %s exited" % self._process_name
            )
            self._set_state(running=False, stopped=True)
        elif new_status == "STARTING":
            self.logger.info(
                "Supervisor process %s starting" % self._process_name
            )
            self._set_state(running=False, stopped=False)
        elif new_status == "RUNNING":
            self.logger.info(
                "Supervisor process %s running" % self._process_name
            )
            self._set_state(running=True, stopped=False)
        elif new_status == "BACKOFF":
            self.logger.info(
                "Supervisor process %s failed to start" % self._process_name
            )
            self._set_state(running=False, stopped=True, error=True)
        elif new_status == "STOPPING":
            self.logger.info(
                "Supervisor process %s stopping" % self._process_name
            )
            self._set_state(running=False, stopped=False)
        elif new_status == "EXITED":
            self.logger.info(
                "Supervisor process %s exited" % self._process_name
            )
            self._set_state(running=False, stopped=True)
        elif new_status == "FATAL":
            self.logger.info(
                "Supervisor process %s failed to start successfully"
                % self._process_name
            )
            self._set_state(running=False, stopped=True, error=True)
        elif new_status == "UNKNOWN":
            self.logger.info(
                "Supervisor process %s in unknown state" % self._process_name
            )
            self._set_state(running=False, stopped=True, error=True)
        else:
            self.logger.info(
                "Supervisor process %s in unhandled state" % self._process_name
            )
            self._set_state(running=False, stopped=True, error=True)
