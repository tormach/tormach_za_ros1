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

  EULAAgreement {
    id: eulaAgreement

    onEulaAgreed: {
      stateMachine.submitEvent("agreed_to_eula");
    }
    onEulaChanged: {
      stateMachine.submitEvent("display_eula");
    }
  }

  ColumnLayout {
    id: checkEULAPanel
    anchors.fill: parent
    visible: root.stateMachine?.checkEULA ?? false

    onVisibleChanged: {
      if (visible) {
        eulaAgreement.check_eula();
      }
    }

    VerticalFiller {
    }

    PathPilotLabel {
      Layout.alignment: Qt.AlignHCenter
      text: qsTr("Checking for EULA agreement...")
    }

    PathPilotBusyIndicator {
      Layout.alignment: Qt.AlignHCenter
    }

    VerticalFiller {
    }
  }

  ColumnLayout {
    id: displayEULAPanel
    anchors.fill: parent
    visible: root.stateMachine?.displayEULA ?? false

    PathPilotLabel {
      text: qsTr("License Agreement")
    }

    Rectangle {
      Layout.fillWidth: true
      Layout.fillHeight: true
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
          textFormat: Text.RichText
          text: eulaAgreement.eula
        }
      }
    }
  }

  PathPilotButton {
    visible: displayEULAPanel.visible
    parent: root.buttonContainer
    text: qsTr("Agree to EULA")
    onClicked: {
      eulaAgreement.agree_to_eula();
    }
  }
}
