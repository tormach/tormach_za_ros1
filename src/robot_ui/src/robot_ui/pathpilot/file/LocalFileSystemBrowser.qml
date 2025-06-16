import QtQuick
import pathpilot.core
import pathpilot.file

FileSystemBrowser {
  id: root
  property alias rootPath: fileSystemModel.rootPath
  nameFilters: [".directory", ".*", "__pycache__", "*.pyc", "*~"]

  function reload() {
    fileSystemModel.reload();
  }

  onVisibleChanged: {
    if (visible && _d.needsReload) {
      fileSystemModel.reload();
      _d.needsReload = false;
    }
  }

  readonly property QtObject _d: QtObject {
    id: d
    property bool needsReload: false
  }

  fileSystemModel: FlatFileSystemModel {
    id: fileSystemModel
    rootPath: root.navigation.currentPath
  }

  fileSelection: FileSelection {
    id: fileSelection
    path: root.navigation.currentPath
  }

  FileWatcher {
    id: fileWatcher
    recursive: false
    fileUrl: FileUtils.localPathToUrl(fileSystemModel.rootPath)
    enabled: true
    onFileChanged: {
      if (root.visible) {
        fileSystemModel.reload();
      } else {
        _d.needsReload = true;
      }
    }

    nameFilters: root.nameFilters
  }
}
