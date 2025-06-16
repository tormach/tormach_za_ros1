import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers

PathPilotPanel {
  id: root

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    spacing: Sizes.doubleSpacing

    PathPilotLabel {
      text: qsTr("Commissioning")
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotDelayButton {
      Layout.fillWidth: true
      text: qsTr("Zero All Joints")
      enabled: Handlers.state.driveHome.canEffect

      onActivated: Handlers.state.driveHome.effectCmd()

      PathPilotToolTip {
        itemId: "msg_zero_all_joints"
      }
    }

    PathPilotDelayButton {
      Layout.fillWidth: true
      enabled: Handlers.state.driveStop.canEffect
      text: qsTr("Power Off")
      onActivated: Handlers.state.driveStop.effectCmd()
      PathPilotToolTip {
        itemId: "msg_power_off"
      }
    }

    VerticalFiller {
    }
  }
}
