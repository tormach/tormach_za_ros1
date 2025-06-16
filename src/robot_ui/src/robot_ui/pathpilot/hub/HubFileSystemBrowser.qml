import QtQuick
import pathpilot.core
import pathpilot.file
import pathpilot.hub

FileSystemBrowser {
  id: root
  property alias rootPath: fileSystemModel.rootPath
  property alias hubConnector: fileSystemModel.hubConnector

  navigation.absolute: false
  navigation.homePath: "gcode"

  fileSelection: root.hubConnector

  Binding {
    target: root.hubConnector
    property: "path"
    value: root.navigation.currentPath
  }

  function reload() {
    fileSystemModel.reload();
  }

  fileSystemModel: HubFileSystemModel {
    id: fileSystemModel
    rootPath: fileSystemBrowser.navigation.currentPath
  }
}
