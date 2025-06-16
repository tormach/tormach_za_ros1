import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program.notification
import pathpilot.robot.program

ScaledTestBase {
  id: root

  AddWaypointPopup {
    id: notificationPopup
  }

  Row {
    anchors.centerIn: parent
    spacing: Sizes.singleSpacing

    PathPilotButton {
      implicitWidth: 180
      text: "Add Waypoint"
      onClicked: notificationPopup.open()
    }
  }
}
