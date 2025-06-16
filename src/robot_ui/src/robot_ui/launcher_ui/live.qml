import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtCore
import pathpilot.core
import pathpilot.development
import pathpilot.file
import pathpilot.controls

ApplicationWindow {
  id: root
  title: "Live Coding for PathPilot"
  width: Config.data.window?.defaultWidth ?? 1920
  height: Config.data.window?.defaultHeight ?? 1080
  visible: true
  flags: liveCoding.flags
  visibility: liveCoding.visibility

  Component.onCompleted: {
    for (var i = 0; i < Qt.application.screens.length; ++i) {
      var screen = Qt.application.screens[i];
      if (screen.serialNumber === windowSettings.screen) {
        root.screen = screen;
        return;
      }
    }
  }

  Component.onDestruction: {
    windowSettings.screen = root.screen.serialNumber;
  }

  LiveCodingPanel {
    id: liveCoding
    anchors.fill: parent
  }

  Settings {
    id: windowSettings
    category: "window"
    property alias width: root.width
    property alias height: root.height
    property alias x: root.x
    property alias y: root.y
    property alias visibility: liveCoding.visibility
    property alias flags: liveCoding.flags
    property alias hideToolBar: liveCoding.hideToolBar
    property string screen: ""
  }
}
