import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.development
import pathpilot.robot
import pathpilot.robot.preview
import pathpilot.robot.jog
import pathpilot.handlers

RowLayout {
  id: root
  default property alias buttonData: alienContainer.data
  property alias controlData: controlContainer.data

  signal moveToMarkerRequested(Pose pose)
  spacing: Sizes.singleSpacing

  ColumnLayout {
    RowLayout {
      Layout.fillHeight: true

      ColumnLayout {
        id: controlContainer
        visible: children.length > 0
      }

      RvizPreviewController {
        Layout.fillWidth: true
        Layout.fillHeight: true
        mode: PreviewMode.Interactive
      }
    }

    RowLayout {
      Layout.fillHeight: false

      JointJog {
        Layout.fillWidth: true
      }

      PathPilotButton {
        Layout.preferredWidth: 180
        Layout.fillHeight: true
        enabled: !Handlers.program.programPausedActive
        text: qsTr("New waypoint\nfrom current\nPosition")
        horizontalAlignment: Text.AlignHCenter
        onClicked: {
          Handlers.conversational.requestAddWaypoint();
        }
        PathPilotToolTip {
          itemId: "msg_new_waypoint_from_current_position"
          y: 10
          notchPosY: 6
        }
      }

      InteractiveJogButtons {
        id: interactiveJogButtons
        Layout.fillHeight: true
        markerOpsChecked: true

        Binding {
          target: interactiveJog
          property: "visible"
          value: interactiveJogButtons.markerOpsChecked
        }
      }
    }
  }

  ColumnLayout {
    Layout.fillWidth: false

    CartesianJog {
      id: cartesianJog
      Layout.fillHeight: true
      visible: !interactiveJog.visible
    }

    InteractiveJog {
      id: interactiveJog
      Layout.preferredWidth: cartesianJog.implicitWidth
      visible: false
    }

    Spacer {
      Layout.fillWidth: true
      visible: alienContainer.children.length > 0
    }

    RowLayout {
      id: alienContainer
      visible: children.length > 0
    }
  }
}
