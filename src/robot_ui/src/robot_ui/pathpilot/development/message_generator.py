from enum import IntEnum
from PySide6.QtCore import (
    QObject,
    Signal,
    Property,
    Slot,
    QTimer,
    QEnum,
)
from PySide6.QtQml import QmlElement

import rospy

from ..qt_helpers import ensure_cleanup

DEFAULT_MESSAGE_INTERVAL_MS = 1000

QML_IMPORT_NAME = 'pathpilot.development'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


class VerbosityLevel(IntEnum):
    Debug = rospy.DEBUG
    Info = rospy.INFO
    Warn = rospy.WARN
    Error = rospy.ERROR
    Fatal = rospy.FATAL


@QmlElement
class MessageGenerator(QObject):
    QEnum(VerbosityLevel)

    runningChanged = Signal(bool)
    messageChanged = Signal(str)
    intervalChanged = Signal(int)
    verbosityChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._message = ''
        self._running = False
        self._verbosity = VerbosityLevel.Info

        self._timer = QTimer(self)
        self._timer.setInterval(DEFAULT_MESSAGE_INTERVAL_MS)
        self._timer.timeout.connect(self._send_message)

        self.runningChanged.connect(self._start_stop_timer)
        ensure_cleanup(self._shutdown)

    @Property(bool, notify=runningChanged)
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        if value == self._running:
            return
        self._running = value
        self.runningChanged.emit(value)

    @Property(int, notify=intervalChanged)
    def interval(self):
        return self._timer.interval()

    @interval.setter
    def interval(self, value):
        if value == self._timer.interval():
            return
        self._timer.setInterval(value)
        self.intervalChanged.emit(value)

    @Property(str, notify=messageChanged)
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        if value == self._message:
            return
        self._message = value
        self.messageChanged.emit(value)

    @Property(int, notify=verbosityChanged)
    def verbosity(self):
        return self._verbosity

    @verbosity.setter
    def verbosity(self, value):
        if value == self._verbosity:
            return
        self._verbosity = VerbosityLevel(value)
        self.verbosityChanged.emit(value)

    @Slot()
    def _start_stop_timer(self):
        if self._running:
            self._timer.start()
        else:
            self._timer.stop()

    @Slot()
    def _shutdown(self):
        self._running = False
        self._start_stop_timer()

    @Slot()
    def _send_message(self):
        switch = {
            VerbosityLevel.Debug: rospy.logdebug,
            VerbosityLevel.Info: rospy.loginfo,
            VerbosityLevel.Warn: rospy.logwarn,
            VerbosityLevel.Error: rospy.logerr,
            VerbosityLevel.Fatal: rospy.logfatal,
        }
        switch[self._verbosity](self._message)
