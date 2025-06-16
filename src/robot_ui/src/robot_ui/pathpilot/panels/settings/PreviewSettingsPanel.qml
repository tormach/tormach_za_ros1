import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.robot.preview

PathPilotPanel {
  id: root

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    spacing: Sizes.doubleSpacing

    PathPilotLabel {
      text: qsTr("Preview")
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotCheckBox {
      Layout.fillWidth: true
      text: qsTr("Enable Preview")
      checked: Config.user.preview.enabled

      onClicked: Config.user.preview.enabled = checked
      PathPilotToolTip {
        itemId: "msg_enable_preview"
      }
    }

    PathPilotLabel {
      text: qsTr("Custom RViz Config")
    }

    Spacer {
      Layout.fillWidth: true
    }

    PathPilotTextField {
      Layout.fillWidth: true
      horizontalAlignment: Text.AlignLeft
      text: Config.user.preview.rvizConfig

      onEditingFinished: Config.user.preview.rvizConfig = text
      PathPilotToolTip {
        itemId: "msg_rviz_config_name_input"
      }
    }
    RowLayout {

      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Create from default")

        onClicked: {
          rvizConfig.createUserConfig();
          Config.user.preview.rvizConfig = rvizConfig.target;
        }

        RvizConfig {
          id: rvizConfig
          source: Config.data.preview.rvizConfig
        }
        PathPilotToolTip {
          itemId: "msg_create_from_default"
        }
      }

      PathPilotButton {
        Layout.fillWidth: true
        text: qsTr("Edit in RViz")
        enabled: !rvizProcess.active && Config.user.preview.rvizConfig !== ""

        onClicked: {
          rvizProcess.start();
        }

        SystemProcess {
          id: rvizProcess
          command: "rosrun rviz rviz -s \"\" -d " + Config.user.preview.rvizConfig
          onActiveChanged: {
            if (!active) {
              Handlers.preview.reload();
            }
          }
        }
        PathPilotToolTip {
          itemId: "msg_edit_in_rviz"
        }
      }
    }

    VerticalFiller {
      Layout.fillHeight: true
    }
  }
}
