import QtQuick
import pathpilot.base
import pathpilot.core
import pathpilot.controls
import pathpilot.screens.main
import launcher_ui.screens 1.0

Rectangle {
  id: root
  property string title: qsTr("PathPilot Robot Launcher") + " " + SoftwareVersion.version + " " + SoftwareVersion.codename
  width: 1280
  height: 1000
  visible: true
  color: Colors.gray5

  ScaleContainer {
    anchors.fill: parent
    minAspectRatio: 10 / 10
    maxAspectRatio: 25 / 10
    referenceWidth: 1200

    LauncherScreen {
      id: ui
      anchors.fill: parent
    }
  }
}
