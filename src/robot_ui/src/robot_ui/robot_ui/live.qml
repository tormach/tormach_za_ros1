import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtCore
import pathpilot.core
import pathpilot.development
import pathpilot.file
import pathpilot.controls
import pathpilot.robot.preview
import pathpilot.handlers

ApplicationWindow {
  id: root
  title: "Live Coding for PathPilot"
  width: Config.data.window.defaultWidth
  height: Config.data.window.defaultHeight
  visible: true
  flags: (Handlers.app?.applicationWindowFlags ?? Qt.Window)
  visibility: (Handlers.app?.applicationWindowVisibility ?? Window.AutomaticVisibility)

  Binding {
    target: Handlers.app
    property: "applicationWindowVisibility"
    value: liveCoding.visibility
  }

  Binding {
    target: Handlers.app
    property: "applicationWindowFlags"
    value: liveCoding.flags
  }

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

  // heavyweight objects which take long to initialize
  StateHandler {
    id: stateHandler
    previewHandler: rvizPreviewObject
    Component.onCompleted: Handlers.state = stateHandler
  }

  JogHandler {
    id: jogHandler
    stateHandler: stateHandler
    Component.onCompleted: Handlers.jog = jogHandler
  }

  RvizPreviewObject {
    id: rvizPreviewObject
    Component.onCompleted: Handlers.preview = rvizPreviewObject
  }
}
