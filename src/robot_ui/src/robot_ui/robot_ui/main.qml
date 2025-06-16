import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
import pathpilot.core
import pathpilot.screens
import pathpilot.robot.preview
import pathpilot.handlers

ApplicationWindow {
  id: appWindow
  property int showTime: 200

  visible: true
  flags: (Handlers.app?.applicationWindowFlags ?? Qt.Window) | Qt.FramelessWindowHint
  visibility: Handlers.app?.applicationWindowVisibility ?? Window.Maximized
  title: (mainAppLoader.item != undefined) ? mainAppLoader.item.title : "Loading"

  Binding {
    target: Handlers.app
    property: "applicationWindowVisibility"
    value: Window.Maximized
  }

  Binding {
    target: Handlers.app
    property: "applicationWindowFlags"
    value: Qt.Window | (Handlers.program?.programRunning ? Qt.WindowStaysOnTopHint : 0)
  }

  Settings {
    id: windowSettings
    category: "window"
    property alias width: appWindow.width
    property alias height: appWindow.height
    property alias x: appWindow.x
    property alias y: appWindow.y
  }

  // Loaders for the main application and the splash screen.
  Loader {
    id: mainAppLoader
    property string errorString: ""
    anchors.fill: parent
    active: false
    source: Qt.resolvedUrl("TopLevel.qml")
    onStatusChanged: {
      if (status !== Loader.Error) {
        return;
      }
      mainAppLoader.errorString = mainAppLoader.sourceComponent.errorString();
    }
  }

  Loader {
    id: errorLoader
    anchors.fill: parent
    anchors.margins: Sizes.singleSpacing
    sourceComponent: errorComponent
    active: mainAppLoader.status == Loader.Error
  }

  Loader {
    id: splashScreenLoader
    sourceComponent: splashScreenComponent
    width: parent.width
    height: parent.height
  }

  Component {
    id: splashScreenComponent
    SplashScreen {
    }
  }

  Component {
    id: errorComponent
    ColumnLayout {
      Text {
        id: errorLabel
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        text: qsTr("We are sorry, loading the Robot UI failed, please report the following errors:")
      }

      Rectangle {
        Layout.fillHeight: true
        Layout.fillWidth: true
        color: Colors.white1
        border.color: Colors.black1
        border.width: Sizes.thinBorder
        radius: Sizes.smallRadius

        TextArea {
          id: errorTextArea
          anchors.fill: parent
          wrapMode: Text.Wrap
          text: mainAppLoader.errorString
        }
      }
    }
  }

  // Timers for starting to load the main application and eventually deleting
  // the splash screen.
  Timer {
    id: firstPhaseTimer
    property int phase: 0
    interval: 50
    running: true
    repeat: false

    onTriggered: {
      if (!mainAppLoader.Loading) {
        mainAppLoader.active = true;
        secondPhaseTimer.start();
      }
    }
  }

  Timer {
    id: secondPhaseTimer
    property int phase: 0
    interval: appWindow.showTime
    running: false
    repeat: true

    onTriggered: {
      if (phase == 0) {
        if (mainAppLoader.Loading) {
          return;
        }
        if (splashScreenLoader.item) {
          splashScreenLoader.item.loadingProgress = 0.75;
        }

        // Set the phase for deletion.
        phase += 1;
      } else if (phase == 1) {
        // Hide the splash screen.
        if (splashScreenLoader.item) {
          splashScreenLoader.item.opacity = 0;
        }
        phase += 1;
      } else {
        // Delete the splash screen.
        // By setting the source property to an empty string destroys
        // the loaded item.
        splashScreenLoader.source = "";
        secondPhaseTimer.stop();
      }
    }
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
