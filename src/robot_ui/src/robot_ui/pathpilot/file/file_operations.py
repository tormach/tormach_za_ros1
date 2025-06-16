import os
import shutil

import rospy
from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtQml import QmlElement

from .file_utils import get_files_from_qml_data

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


@QmlElement
class FileOperations(QObject):
    pathChanged = Signal(str)
    filesChanged = Signal()

    def __init__(self, parent=None, path=''):
        super().__init__(parent)

        self._path = path
        self._files = []

    @Property(str, notify=pathChanged)
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value == self._path:
            return
        self._path = value
        self.pathChanged.emit(value)

    @Property(list, notify=filesChanged)
    def files(self):
        return self._files

    @files.setter
    def files(self, value):
        if value == self._files:
            return
        self._files = value
        self.filesChanged.emit()

    @Slot(str, result=bool)
    def createFolder(self, name):
        abs_path = os.path.abspath(os.path.expanduser(self._path))
        try:
            os.mkdir(os.path.join(abs_path, name))
        except OSError as e:
            rospy.logwarn(f"Could not create folder {e}")
            return False
        else:
            return True

    @Slot(result=bool)
    def deleteAll(self):
        all_ok = True
        items = get_files_from_qml_data(self._files)
        for item in items:
            if not item:
                all_ok &= False
                continue
            path = os.path.join(self._path, item)
            abs_path = os.path.abspath(os.path.expanduser(path))
            try:
                if os.path.isdir(abs_path):
                    shutil.rmtree(abs_path)
                else:
                    os.remove(abs_path)
            except OSError as e:
                all_ok &= False
                rospy.logwarn(f"Could not delete file or folder {e}")
                continue
        return all_ok

    @Slot(str, result=bool)
    def rename(self, new_name):
        items = get_files_from_qml_data(self._files)
        if len(items) != 1:
            return False
        old_name = items[0]
        abs_old_name = os.path.abspath(
            os.path.expanduser(os.path.join(self._path, old_name))
        )
        abs_new_name = os.path.abspath(
            os.path.expanduser(os.path.join(self._path, new_name))
        )
        try:
            os.rename(abs_old_name, abs_new_name)
        except OSError as e:
            rospy.logwarn(f"Could not rename file or folder {e}")
            return False
        else:
            return True

    @Slot(str, result=bool)
    def copyTo(self, path):
        if not os.path.exists(path) or not os.path.isdir(path):
            return False
        items = get_files_from_qml_data(self._files)
        all_ok = True
        for item in items:
            if not item:
                all_ok &= False
                continue
            item_path = os.path.join(self._path, item)
            abs_path = os.path.abspath(os.path.expanduser(item_path))
            target_path = os.path.join(path, item)
            abs_target_path = os.path.abspath(os.path.expanduser(target_path))
            try:
                if os.path.isdir(abs_path):
                    shutil.copytree(
                        abs_path, abs_target_path, dirs_exist_ok=True
                    )
                else:
                    shutil.copy2(abs_path, abs_target_path)
            except (shutil.Error, OSError) as e:
                all_ok &= False
                rospy.logwarn(f"Could not copy file or folder {e}")
                continue
        return all_ok

    @Slot(str, result=bool)
    def moveTo(self, path):
        if not os.path.exists(path) or not os.path.isdir(path):
            return False
        items = get_files_from_qml_data(self._files)
        all_ok = True
        for item in items:
            if not item:
                all_ok &= False
                continue
            item_path = os.path.join(self._path, item)
            abs_path = os.path.abspath(os.path.expanduser(item_path))
            target_path = os.path.join(path, item)
            abs_target_path = os.path.abspath(os.path.expanduser(target_path))
            try:
                shutil.move(abs_path, abs_target_path)
            except (shutil.Error, OSError) as e:
                all_ok &= False
                rospy.logwarn(f"Could not move file or folder {e}")
                continue
        return all_ok
