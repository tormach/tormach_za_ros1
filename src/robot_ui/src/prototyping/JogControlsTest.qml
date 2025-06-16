import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCore
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.preview
import pathpilot.robot.jog
import pathpilot.panels.center
import pathpilot.handlers
import pathpilot.panels.jog

ScaledTestBase {
  id: root

  QtObject {
    id: d
    readonly property CartesianState cartesianState: Handlers.state.cartesianState
    readonly property JointState jointState: Handlers.state.jointState
    property bool jointJogActive: false
  }

  Settings {
    // super convenient during development
    property alias jointJogActive: d.jointJogActive
  }

  ColumnLayout {
    anchors.left: parent.left
    anchors.top: parent.top
    anchors.margins: Sizes.doubleMargin

    RowLayout {

      PathPilotRadioButton {
        id: frameJogRadio
        text: "Cartesian"
        checked: !d.jointJogActive
        onClicked: d.jointJogActive = false
      }

      PathPilotRadioButton {
        id: jointJogRadio
        text: "Joint"
        checked: d.jointJogActive
        onClicked: d.jointJogActive = true
      }
    }

    CartesianJog {
      visible: frameJogRadio.checked
      enabled: false
      linearVelocity: velocitySlider.value
      angularVelocity: velocitySlider.value
    }

    JointJog {
      visible: jointJogRadio.checked
      velocity: velocitySlider.value
    }

    JogWarningIndicator {
      id: jogWarningIndicator
    }

    PathPilotSlider {
      id: velocitySlider
      from: 0.0
      to: 1.0
      value: 0.5
    }
  }

  AxisDroPanel {
    id: axisDro
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.margins: Sizes.doubleMargin
    width: 250
    height: 400
  }

  RowLayout {
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.margins: Sizes.doubleMargin
    spacing: Sizes.doubleSpacing

    Repeater {
      model: d.jointState.joints.length
      ColumnLayout {
        PathPilotLabel {
          text: "Joint " + (index + 1)
        }
        PathPilotLabel {
          text: "Min: " + d.jointState.joints[index].minimum
        }
        PathPilotLabel {
          text: "Zero: " + d.jointState.joints[index].zero
        }
        PathPilotLabel {
          text: "Pos: " + d.jointState.joints[index].position.toFixed(4)
        }
        PathPilotLabel {
          text: "Vel: " + d.jointState.joints[index].velocity.toFixed(4)
        }
        PathPilotLabel {
          text: "Max: " + d.jointState.joints[index].maximum
        }
      }
    }
  }

  RvizPreviewController {
    id: preview
    anchors.right: parent.right
    anchors.topMargin: parent.Sizes.doubleMargin
    anchors.margins: Sizes.doubleMargin
    width: 700
    height: 700
  }

  InteractiveMarker {
    id: interactiveMarker
    fixedFrame: Config.data.preview.fixedFrame
    markerName: "EE:goal_" + Config.data.preview.toolFrame
  }

  ColumnLayout {
    id: interactiveLayout
    anchors.right: preview.left
    anchors.verticalCenter: parent.verticalCenter
    anchors.margins: Sizes.doubleMargin

    GridLayout {
      columns: 4
      PathPilotLabel {
        text: "X"
      }
      PathPilotDroField {
        id: xDroField
        onValueUpdated: interactiveMarker.pose.position.x = value
        Binding {
          target: xDroField
          property: "value"
          value: interactiveMarker.pose.axisPositions.x
        }
      }
      PathPilotLabel {
        text: "A"
      }
      PathPilotDroField {
        id: aDroField
        value: interactiveMarker.pose.axisPositions.a
      }
      PathPilotLabel {
        text: "Y"
      }
      PathPilotDroField {
        id: yDroField
        value: interactiveMarker.pose.axisPositions.y
      }
      PathPilotLabel {
        text: "B"
      }
      PathPilotDroField {
        id: bDroField
        value: interactiveMarker.pose.axisPositions.b
      }
      PathPilotLabel {
        text: "Z"
      }
      PathPilotDroField {
        id: zDroField
        value: interactiveMarker.pose.axisPositions.z
      }
      PathPilotLabel {
        text: "C"
      }
      PathPilotDroField {
        id: cDroField
        value: interactiveMarker.pose.axisPositions.c
      }
    }

    PathPilotButton {
      text: qsTr("Move to Marker")
      Layout.fillWidth: true
      onClicked: d.cartesianState.executeMove(interactiveMarker.pose)
    }
  }
}
