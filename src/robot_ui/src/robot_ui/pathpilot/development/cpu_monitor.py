import os
import psutil

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer
from PySide6.QtQml import QmlElement

DEFAULT_UPDATE_INTERVAL = 1000

QML_IMPORT_NAME = 'pathpilot.development'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class CpuMonitor(QObject):
    updateIntervalChanged = Signal(int)
    usageChanged = Signal(float)

    def __init__(self, parent=None, update_interval=DEFAULT_UPDATE_INTERVAL):
        super().__init__(parent)

        self._update_interval = update_interval
        self._timer = QTimer(self)
        self._proc = psutil.Process(os.getpid())
        self._usage = 0.0

        self.updateIntervalChanged.connect(self._update_timer)
        self._timer.timeout.connect(self._monitor)

        self._update_timer()

    @Property(int, notify=updateIntervalChanged)
    def updateInterval(self):
        return self._update_interval

    @updateInterval.setter
    def updateInterval(self, value):
        if value == self._update_interval:
            return
        self._update_interval = value
        self.updateIntervalChanged.emit(value)

    @Property(float, notify=usageChanged)
    def usage(self):
        return self._usage

    @Slot()
    def _update_timer(self):
        self._timer.stop()
        self._timer.start(self._update_interval)

    @Slot()
    def _monitor(self):
        self._usage = self._proc.cpu_percent()
        self.usageChanged.emit(self._usage)
