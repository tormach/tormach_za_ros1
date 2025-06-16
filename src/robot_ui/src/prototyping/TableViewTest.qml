import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQml.Models
import pathpilot.core
import pathpilot.controls
import pathpilot.file
import Qt.labs.qmlmodels

Item {
  id: root

  RowLayout {
    anchors.fill: parent

    FileSystemBrowser {
      id: fsBrowser
      Layout.fillHeight: true
      Layout.fillWidth: true
      Layout.preferredWidth: 500
      rootPath: Config.data.programHomePath
    }
  }

  Timer {
    interval: 1000
    running: false
    repeat: true
    onTriggered: fsBrowser.moveToSelected()
  }
}
