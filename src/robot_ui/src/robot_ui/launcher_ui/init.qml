import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtCore
import Qt.labs.platform
import pathpilot.core
import pathpilot.screens
import launcher_ui.panels.shutdown 1.0
import launcher_ui.panels.running 1.0

ApplicationWindow {
  id: appWindow
  property int showTime: 200

  visible: true
  width: 1280
  height: 800

  visibility: Window.Windowed
  flags: Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMaximizeButtonHint
  title: (mainAppLoader.item != undefined) ? mainAppLoader.item.title : qsTr("Loading")

  readonly property QtObject d: QtObject {

    function setVisibility() {
      if (appWindow.visibility === Window.Hidden) {
        appWindow.show();
        appWindow.raise();
        appWindow.requestActivate();
      } else {
        appWindow.hide();
      }
    }
  }

  Settings {
    id: windowSettings
    category: "window"
    property alias width: appWindow.width
    property alias height: appWindow.height
    property alias x: appWindow.x
    property alias y: appWindow.y
  }

  SystemTrayIcon {
    id: systemTrayIcon
    icon.source: programIconPath
    tooltip: qsTr("PathPilot Robot Launcher") + " " + SoftwareVersion.version
    visible: RunningSingleton.running

    menu: Menu {
      title: qsTr("PathPilot Robot Launcher")

      MenuItem {
        id: hideWindowTrayMenuItem
        text: qsTr("Hide window")
        visible: appWindow.visibility !== Window.Hidden
        onTriggered: appWindow.hide()
      }
      MenuSeparator {
        visible: hideWindowTrayMenuItem.visible
      }
      MenuItem {
        id: shutdownTrayMenuItem
        text: qsTr("Shutdown")

        onTriggered: ShutdownSingleton.requestShutdown()
      }
    }

    onVisibleChanged: {
      appWindow.d.setVisibility();
    }

    onActivated: {
      appWindow.d.setVisibility();
    }
  }

  // Loaders for the main application and the splash screen.
  Loader {
    id: mainAppLoader
    anchors.fill: parent
    onLoaded: {
      focus = true;
    }

    Connections {
      target: mainAppLoader.item
      ignoreUnknownSignals: true
      function onRobotRunningChanged() {
        systemTrayIcon.visible = true;
      }
    }
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
        mainAppLoader.source = Qt.resolvedUrl("main.qml");
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
}
