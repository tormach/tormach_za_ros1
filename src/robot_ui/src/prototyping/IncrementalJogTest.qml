import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.preview
import pathpilot.robot.jog
import pathpilot.panels.center
import pathpilot.handlers

ScaleContainer {
  id: root

  Rectangle {
    anchors.fill: parent
    color: Colors.gray1
  }

  QtObject {
    id: d
    property double stepSize: 0.001
    property string jogType: "Joints"
  }

  RowLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin

    RvizPreviewController {
      id: controller
      Layout.fillWidth: true
      Layout.fillHeight: true
      mode: PreviewMode.View
    }

    ColumnLayout {
      Layout.fillWidth: false
      Layout.preferredWidth: 400

      RowLayout {
        PathPilotRadioButton {
          id: stepOneButton
          text: "0.1"
          onClicked: d.stepSize = 0.1
        }
        PathPilotRadioButton {
          id: stepTwoButton
          text: "0.01"
          onClicked: d.stepSize = 0.01
        }
        PathPilotRadioButton {
          id: stepThreeButton
          checked: true
          text: "0.001"
          onClicked: d.stepSize = 0.001
        }
      }
      RowLayout {
        PathPilotRadioButton {
          text: "Cartesian"
          onClicked: d.jogType = "Cartesian"
        }
        PathPilotRadioButton {
          text: "Joints"
          checked: true
          onClicked: d.jogType = "Joints"
        }
      }

      Repeater {
        id: repeater
        model: ["X", "Y", "Z", "A", "B", "C"]

        RowLayout {
          visible: d.jogType === "Cartesian"
          property string axis: repeater.model[index]

          PathPilotButton {
            text: axis + "-"
            enabled: !Handlers.jog.interactiveMove.active
            onClicked: Handlers.jog.incremental.cartesian.step(axis, -d.stepSize)
          }

          PathPilotButton {
            text: axis + "+"
            enabled: !Handlers.jog.interactiveMove.active
            onClicked: Handlers.jog.incremental.cartesian.step(axis, d.stepSize)
          }
        }
      }

      Repeater {
        id: repeater2
        model: 6

        RowLayout {
          visible: d.jogType === "Joints"

          PathPilotButton {
            text: "J%1-".arg(index + 1)
            enabled: !Handlers.jog.interactiveMove.active
            onClicked: Handlers.jog.incremental.joints.step(index, -d.stepSize)
          }

          PathPilotButton {
            text: "J%1+".arg(index + 1)
            enabled: !Handlers.jog.interactiveMove.active
            onClicked: Handlers.jog.incremental.joints.step(index, d.stepSize)
          }
        }
      }

      AxisDroPanel {
        Layout.fillWidth: true
        Layout.fillHeight: true
      }

      JointDroPanel {
        Layout.fillWidth: true
        Layout.fillHeight: true
      }
    }
  }
}
