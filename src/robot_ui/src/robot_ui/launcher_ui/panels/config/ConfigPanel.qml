import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import launcher_ui.logic 1.0
import QtScxml

Item {
  id: root
  property StateMachine stateMachine
  property Item buttonContainer

  property RobotUILauncher robotLauncher

  readonly property QtObject d: QtObject {

    function selectConfig(ppLaunchArgs, osLaunchArgs) {
      robotLauncher.configureRun(ppLaunchArgs, osLaunchArgs);
      robotLauncher.start();
      stateMachine.submitEvent("config_selected");
    }
    function testAgain() {
      stateMachine.submitEvent("config_check_again");
    }
  }

  ConfigModel {
    id: configModel

    onCheckCompleted: {
      stateMachine.submitEvent("config_check_done");
    }
  }

  ColumnLayout {
    id: configCheckPanel
    anchors.fill: parent
    visible: root.stateMachine?.configCheck ?? false

    onVisibleChanged: {
      if (visible) {
        configModel.loadConfigs();
      }
    }

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Checking available configurations...")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    VerticalFiller {
    }
  }

  ColumnLayout {
    id: configSelectPanel
    anchors.fill: parent
    visible: root.stateMachine?.configFound ?? false

    RowLayout {
      ColumnLayout {
        PathPilotLabel {
          text: qsTr("Configs able to run:")
        }

        ConfigListView {
          id: configListView
          Layout.fillWidth: true
          Layout.fillHeight: true
          Layout.preferredWidth: 500
          model: configModel
        }
      }

      ColumnLayout {
        id: errorColumn
        visible: configModel.errorStatus
        PathPilotLabel {
          text: qsTr("Error status:")
        }

        Rectangle {
          Layout.fillHeight: true
          Layout.fillWidth: true
          Layout.preferredWidth: 300
          border.width: Sizes.halfMargin
          border.color: Colors.gray1

          ScrollView {
            id: view
            anchors.fill: parent

            TextArea {
              wrapMode: Text.WordWrap
              font.pixelSize: Fonts.launcher.size1
              font.family: Fonts.font2
              readOnly: true
              selectByMouse: true
              selectByKeyboard: true
              selectionColor: Colors.green2
              textFormat: Text.StyledText
              text: configModel.errorStatus
            }
          }
        }
      }
    }
  }

  RowLayout {
    visible: root.visible
    parent: root.buttonContainer

    PathPilotButton {
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Start")
      enabled: configListView.currentIndex > -1
      visible: root.stateMachine?.configFound ?? false

      onClicked: d.selectConfig(configListView.pathPilotRobotLaunchArguments, configListView.robotOperatingSystemLaunchArguments)
    }

    PathPilotButton {
      horizontalAlignment: Text.AlignHCenter
      text: qsTr("Retest")
      visible: root.stateMachine?.configFound ?? false

      onClicked: d.testAgain()
    }
  }
}
