import os

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement

QML_IMPORT_NAME = 'pathpilot.robot.program'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class ProgramUiReader(QObject):
    """Looks for UI files matching a robot program."""

    programPathChanged = Signal(str)
    uiMainPathChanged = Signal(str)
    uiImportPathChanged = Signal(str)
    validChanged = Signal(bool)
    uiTimestampChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._program_path = ''
        self._valid = False
        self._ui_main_path = ''
        self._ui_import_path = ''
        self._ui_timestamp = '0'

        self.programPathChanged.connect(self.reload)

    @Property(str, notify=programPathChanged)
    def programPath(self):
        return self._program_path

    @programPath.setter
    def programPath(self, value):
        if value == self._program_path:
            return
        self._program_path = value
        self.programPathChanged.emit(value)

    @Property(str, notify=uiMainPathChanged)
    def uiMainPath(self):
        return self._ui_main_path

    @Property(str, notify=uiImportPathChanged)
    def uiImportPath(self):
        return self._ui_import_path

    @Property(bool, notify=validChanged)
    def valid(self):
        return self._valid

    @Property(str, notify=uiTimestampChanged)
    def uiTimestamp(self):
        return self._ui_timestamp

    @Slot()
    def reload(self):
        valid = False
        ui_main_path = ''
        ui_import_path = ''
        if self._program_path != '':
            path, ext = os.path.splitext(self._program_path)
            qml_path = path + '.qml'
            if os.path.exists(qml_path):
                ui_main_path = qml_path
                valid = True
            # check if program lives in a directory of the same name
            # if so, use it as ui import path
            program_name = os.path.basename(path)
            program_dir = os.path.dirname(path)
            if program_name == os.path.basename(program_dir):
                ui_import_path = program_dir
            else:
                ui_import_path = ''

        if ui_main_path != self._ui_main_path:
            self._ui_main_path = ui_main_path
            self.uiMainPathChanged.emit(ui_main_path)

        if ui_import_path != self._ui_import_path:
            self._ui_import_path = ui_import_path
            self.uiImportPathChanged.emit(ui_import_path)

        if valid != self._valid:
            self._valid = valid
            self.validChanged.emit(valid)

        if valid:
            if ui_import_path != '':
                last_mod_time = 0
                for f in os.listdir(ui_import_path):
                    if f.endswith('.qml'):
                        mod_time = os.path.getmtime(
                            os.path.join(ui_import_path, f)
                        )
                        if mod_time > last_mod_time:
                            last_mod_time = mod_time
                self._ui_timestamp = str(int(last_mod_time * 1000))
            else:
                self._ui_timestamp = str(
                    int(os.path.getmtime(ui_main_path) * 1000)
                )
        else:
            self._ui_timestamp = '0'
        self.uiTimestampChanged.emit(self._ui_timestamp)
