import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotPanel {
  id: root

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    spacing: Sizes.doubleSpacing

    PathPilotLabel {
      text: qsTr("Tools")
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotButton {
      Layout.fillWidth: true
      text: qsTr("HAL Scope")

      onClicked: ApplicationHelpers.runSystemCommand("halscope")

      PathPilotToolTip {
        itemId: "msg_tools_hal_scope"

        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    PathPilotButton {
      Layout.fillWidth: true
      text: qsTr("HAL Meter")

      onClicked: ApplicationHelpers.runSystemCommand("halmeter")
      PathPilotToolTip {
        itemId: "msg_tools_hal_meter"

        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    PathPilotButton {
      Layout.fillWidth: true
      text: qsTr("RViz")

      onClicked: ApplicationHelpers.runSystemCommand("rosrun rviz rviz")
      PathPilotToolTip {
        itemId: "msg_tools_rviz"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    PathPilotButton {
      Layout.fillWidth: true
      text: qsTr("RQt GUI")

      onClicked: ApplicationHelpers.runSystemCommand("rosrun rqt_gui rqt_gui")

      PathPilotToolTip {
        itemId: "msg_tools_rqt_gui"
        sidePosition: PathPilotToolTip.Side.Left
      }
    }

    VerticalFiller {
    }
  }
}
