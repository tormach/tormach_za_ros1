import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.panels.main
import pathpilot.handlers
import pathpilot.robot.frame

RowLayout {
  id: root

  Component.onCompleted: {
    nameTextField.text = Config.user.custom.frameName;
  }

  ColumnLayout {
    Layout.fillWidth: false
    Layout.preferredWidth: 500

    PathPilotLabel {
      text: qsTr("Update Tool Frame")
    }

    RowLayout {
      PathPilotLabel {
        text: qsTr("Name:")
      }

      PathPilotTextField {
        id: nameTextField
        readOnly: true
      }
    }

    RowLayout {
      PathPilotLabel {
        text: qsTr("Using")
      }

      PathPilotRadioButton {
        visible: false
        ButtonGroup.group: methodButtonGroup
        text: qsTr("3-Point Method")
        checked: Config.user.custom.calibrationMethod == 3
        onClicked: Config.user.custom.calibrationMethod = 3
      }

      PathPilotRadioButton {
        ButtonGroup.group: methodButtonGroup
        text: qsTr("4-Point Method")
        checked: Config.user.custom.calibrationMethod == 4
        onClicked: Config.user.custom.calibrationMethod = 4
      }

      ButtonGroup {
        id: methodButtonGroup
      }
    }

    PathPilotButton {
      id: dummyButton
      visible: false
    }

    RowLayout {
      spacing: Sizes.doubleMargin

      ColumnLayout {
        spacing: Sizes.doubleMargin

        Repeater {
          model: Config.user.custom.calibrationMethod

          Item {
            Layout.preferredHeight: dummyButton.height
            Layout.preferredWidth: led.implicitWidth

            Led {
              id: led
              anchors.centerIn: parent
              value: Config.user.custom["waypoint%1Set".arg(index + 1)] || Config.user.custom.teachWaypoint == index + 1
              activeColor: Config.user.custom["waypoint%1Set".arg(index + 1)] ? Colors.green1 : Colors.yellow1
            }
          }
        }
      }

      ColumnLayout {
        spacing: Sizes.doubleMargin

        Repeater {
          model: Config.user.custom.calibrationMethod

          PathPilotLabel {
            Layout.preferredHeight: dummyButton.height
            text: qsTr("Waypoint %1".arg(index + 1))
          }
        }
      }

      ColumnLayout {
        spacing: Sizes.doubleMargin

        Repeater {
          model: Config.user.custom.calibrationMethod

          PathPilotButton {
            Layout.preferredWidth: 250
            enabled: Config.user.custom.teachWaypoint == 0
            text: qsTr("Set from Current Position")
            onClicked: {
              Config.user.custom.teachWaypoint = index + 1;
              Handlers.program.continueProgram();
            }
          }
        }
      }
    }

    VerticalFiller {
    }

    RowLayout {
      HorizontalFiller {
      }

      PathPilotButton {
        text: qsTr("Abort")
        onClicked: Handlers.program.stopProgram()
      }

      PathPilotButton {
        text: qsTr("Accept")
        enabled: Config.user.custom.waypointsReady == true && !nameTextField.error
        onClicked: {
          Config.user.custom.frameName = nameTextField.text;
          Config.user.custom.acceptWaypoints = true;
          Handlers.program.continueProgram();
        }
      }
    }
  }

  PreviewPanel {
    Layout.fillWidth: true
    Layout.fillHeight: true
    Layout.preferredWidth: 500
  }
}
