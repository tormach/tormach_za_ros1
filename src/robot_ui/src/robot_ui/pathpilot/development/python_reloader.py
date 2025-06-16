import os
import sys
import signal
import inspect

from PySide6.QtCore import QObject, Slot


class PythonReloader(QObject):
    def __init__(self, main, parent=None):
        super().__init__(parent)
        self._main = main

    @Slot()
    def restart(self):
        handler = signal.getsignal(signal.SIGTERM)
        if handler and handler is not signal.default_int_handler:
            handler(signal.SIGTERM, inspect.currentframe())
        os.execv(self._main, sys.argv)
