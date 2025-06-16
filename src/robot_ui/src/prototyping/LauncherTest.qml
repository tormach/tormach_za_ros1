import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.hal
import launcher_ui.logic 1.0

ScaledTestBase {
  id: root
  referenceWidth: 700

  RosLauncher {
    id: launcher
    executable: "moveit_planning_execution.launch"
    rosPackage: "za6_robot"
    args: 'rviz:="false"'
  }

  HalStatus {
    id: halStatus
  }

  Row {
    spacing: 10
    anchors.centerIn: parent

    PathPilotButton {
      text: !launcher.running ? "Start" : "Stop"
      onClicked: !launcher.running ? launcher.start() : launcher.stop()
    }

    PathPilotCheckBox {
      text: "Running"
      checked: halStatus.ready

      MouseArea {
        anchors.fill: parent
      }
    }
  }
}
