import sys
import signal
import logging
import traceback
from pp_ros_launch.launcher.rpcinterface import SupervisorClient
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication


class SignalHandler(QObject):
    SHUTDOWN_CHECK_INTERVAL_MS = 500

    _cbs = {}
    logger = logging.getLogger('launcher.sighandler')

    def __init__(self, parent=None):
        super().__init__(parent)

        # Handle interrupts
        sys.excepthook = self._handle_exception

        # Set signal handler
        signal.signal(signal.SIGINT, self._handle_interrupt)

        # Start a do-nothing periodic timer to catch interrupts from
        # the Python interpreter
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: None)
        self._timer.start(self.SHUTDOWN_CHECK_INTERVAL_MS)

        self.logger.info("Signal handler and event timer initialized")

    @classmethod
    def register_shutdown_callback(cls, name, cb=None, unregister=False):
        if not unregister:
            cls.logger.debug("Registering shutdown callback '%s'" % name)
            cls._cbs[name] = cb
        else:
            cls.logger.debug("Unregistering shutdown callback '%s'" % name)
            cls._cbs.pop(name, None)

    @classmethod
    def shutdown(cls, reason):
        cls.logger.warn("Shutting down:  %s" % reason)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        for name, cb in cls._cbs.items():
            cls.logger.info("Running shutdown cb '%s'" % name)
            cb()
        SupervisorClient.shutdown()
        QApplication.quit()

    def _handle_interrupt(self, signal, args):
        self.shutdown("Received keyboard interrupt")

    def _handle_exception(self, etype, evalue, etraceback):
        if etype is KeyboardInterrupt:
            self._handle_interrupt(signal.SIGINT, None)
            return

        tb = ''.join(traceback.format_exception(etype, evalue, etraceback))
        self.logger.critical(
            f"An unexpected error occurred:\n{evalue}\n\n{tb}\n"
        )
