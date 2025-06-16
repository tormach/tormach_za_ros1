import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.handlers

PathPilotPanel {
  id: root

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    spacing: Sizes.singleSpacing

    JogSettingControls {
      id: jogControls
      Layout.fillWidth: true
      Layout.fillHeight: false
    }

    Spacer {
      Layout.fillWidth: true
      visible: gripperControl.visible
    }

    GripperControl {
      id: gripperControl
      visible: ROS.getParam("tool", "") == "gr60_gripper"
    }

    Spacer {
      Layout.fillWidth: true
    }

    SubProgramComboControl {
      id: subPrograms
    }

    VerticalFiller {
    }

    RowLayout {
      Layout.fillWidth: true
      visible: devMode

      PathPilotLabel {
        text: qsTr("Dev Mode:")
      }

      PathPilotButton {
        text: qsTr("Hide Window")
        onClicked: {
          Handlers.app.applicationWindowVisibility = Window.AutomaticVisibility;
          Handlers.app.applicationWindowVisibility = Window.Minimized;
        }
      }
    }

    Spacer {
      Layout.fillWidth: true
    }

    RowLayout {
      Layout.fillWidth: true
      Layout.fillHeight: false

      PathPilotLogo {
        id: logo
        Layout.preferredWidth: 109
      }

      VersionInfo {
        id: info
        Layout.fillWidth: true
      }

      Item {
        Layout.fillWidth: true
      }

      ExitButton {
        id: exitButton
        enabled: Handlers.app.exitAllowed
      }
    }
  }
}
