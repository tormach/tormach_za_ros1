import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0
import QtScxml

ColumnLayout {
  id: root
  property StateMachine stateMachine
  property RobotUILauncher robotLauncher

  property Connections connections: Connections {
    target: robotLauncher
    function onRunningChanged() {
      if (robotLauncher.running) {
        stateMachine.submitEvent("robot_started");
      }
    }
    function onExitedChanged() {
      if (robotLauncher.exited) {
        stateMachine.submitEvent("shutdown");
        launchercontrol.shutdown("Robot UI exited");
      }
    }
  }

  LauncherControl {
    id: launchercontrol
  }

  VerticalFiller {
    Layout.fillWidth: true
  }

  PathPilotLabel {
    Layout.alignment: Qt.AlignHCenter
    text: qsTr("Robot UI status:  %1".arg(root.robotLauncher.status))
  }

  VerticalFiller {
  }
}
