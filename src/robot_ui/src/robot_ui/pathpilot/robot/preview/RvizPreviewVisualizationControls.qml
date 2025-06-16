import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.robot.preview

Window {
  id: rvizControlWindow
  flags: Qt.FramelessWindowHint | Qt.Tool | (Handlers.app?.applicationWindowFlags ?? Qt.Window)
  width: controlLayout.width * Sizes.scale
  height: controlLayout.height * Sizes.scale
  color: "black"

  ColumnLayout {
    id: controlLayout
    anchors.centerIn: parent
    scale: Sizes.scale

    PathPilotIconButton {
      id: toggle_global_waypoints_btn
      icon_: Config.user.preview.showGlobalWaypoints ? Icons.rvizpreview.global : Icons.rvizpreview.globalDisabled
      onClicked: {
        Config.user.preview.showGlobalWaypoints = !Config.user.preview.showGlobalWaypoints;
      }
    }

    PathPilotIconButton {
      id: toggle_program_waypoints_btn
      icon_: Config.user.preview.showProgramWaypoints ? Icons.rvizpreview.program : Icons.rvizpreview.programDisabled
      onClicked: {
        Config.user.preview.showProgramWaypoints = !Config.user.preview.showProgramWaypoints;
      }
    }
  }
}
