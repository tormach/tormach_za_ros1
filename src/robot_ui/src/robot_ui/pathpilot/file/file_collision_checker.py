import os.path

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement

from .file_utils import get_files_from_qml_data

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FileCollisionChecker(QObject):
    sourceSelectionChanged = Signal()
    targetSelectionChanged = Signal()
    hasCollisionsChanged = Signal(bool)
    collisionsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._source_selection = None
        self._target_selection = None
        self._has_collisions = False
        self._collisions = []

    @Property('QVariant', notify=sourceSelectionChanged)
    def sourceSelection(self):
        return self._source_selection

    @sourceSelection.setter
    def sourceSelection(self, value):
        if value == self._source_selection:
            return
        self._source_selection = value
        self.sourceSelectionChanged.emit()

    @Property('QVariant', notify=targetSelectionChanged)
    def targetSelection(self):
        return self._target_selection

    @targetSelection.setter
    def targetSelection(self, value):
        if value == self._target_selection:
            return

        self._target_selection = value
        self.targetSelectionChanged.emit()

    @Property(bool, notify=hasCollisionsChanged)
    def hasCollisions(self):
        return self._has_collisions

    @Property('QVariant', notify=collisionsChanged)
    def collisions(self):
        return self._collisions

    @Slot()
    def update(self):
        if self._source_selection is None or self._target_selection is None:
            return

        self._collisions = []

        def compare_folder_items(source_path, target_path, source_files=None):
            source_files = (
                self._source_selection.listdir(source_path)
                if source_files is None
                else source_files
            )
            target_files = self._target_selection.listdir(target_path)
            intersection = set(source_files).intersection(set(target_files))
            for name in sorted(intersection):
                sub_source_path = os.path.join(source_path, name)
                sub_target_path = os.path.join(target_path, name)
                if self._source_selection.isdir(sub_source_path):
                    if self._target_selection.isdir(sub_target_path):
                        compare_folder_items(sub_source_path, sub_target_path)
                    else:
                        self._collisions.append(sub_target_path)
                else:
                    self._collisions.append(sub_target_path)

        compare_folder_items(
            self._source_selection.path,
            self._target_selection.path,
            source_files=get_files_from_qml_data(self._source_selection.files),
        )

        self._has_collisions = len(self._collisions) > 0
        self.hasCollisionsChanged.emit(self._has_collisions)
        self.collisionsChanged.emit()
