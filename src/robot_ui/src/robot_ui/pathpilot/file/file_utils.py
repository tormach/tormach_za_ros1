import os
import subprocess

from PySide6.QtCore import QObject, QUrl, Slot, Property
from PySide6.QtQml import QJSValue, QmlElement, QmlSingleton

USER_MEDIA_MOUNT_PATH = os.path.join('/media', os.environ['USER'])

QML_IMPORT_NAME = 'pathpilot.file'
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0


def human_readable_bytes(num):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}B"
        num /= 1024.0
    return "{:.1f}{}B".format(num, 'Yi')


def get_disk_free_space_bytes(path):
    try:
        result = subprocess.check_output(
            f"df --output=avail '{path}'", shell=True
        )
        freebytestr = result.splitlines()[1].strip()
        freebytes = float(freebytestr) * 1024.0  # df reports in 1K blocks
        return freebytes
    except subprocess.CalledProcessError:
        return 0


@QmlElement
@QmlSingleton
class FileUtils(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    @Slot(str, result=float)
    def getFreeDiskSpace(self, path):
        return get_disk_free_space_bytes(path)

    @Slot(float, result=str)
    def humanReadableBytes(self, num):
        return human_readable_bytes(num)

    @Slot(str, result=QUrl)
    def localPathToUrl(self, path):
        if path == '':
            return QUrl()  # empy path would be resolved to working directory!
        abspath = os.path.abspath(os.path.expanduser(path))
        return QUrl.fromLocalFile(abspath)

    @Property(str, constant=True)
    def userMediaMountPath(self):
        return USER_MEDIA_MOUNT_PATH


def get_files_from_qml_data(data):
    files = data.toVariant() if isinstance(data, QJSValue) else data
    return files or []
