import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.controls
import pathpilot.core
import pathpilot.conversational
import pathpilot.file
import pathpilot.robot
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import pathpilot.robot.program.notification
import pathpilot.handlers

ConversationalItem {
  id: root

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    property int notifyType: NotifyBlockData.Notification
    property alias message: messageTextArea.text
    property alias imagePath: imagePathEdit.text

    function prepareBlockData() {
      return {
        "notify_type": d.notifyType,
        "message": d.message,
        "image_path": d.imagePath
      };
    }

    function addBlock(blockUuid) {
      Handlers.conversational.manipulator.beginGroup();
      var uuid = Handlers.conversational.manipulator.createBlock(blockUuid, "notify");
      Handlers.conversational.manipulator.updateBlock(uuid, prepareBlockData());
      Handlers.conversational.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
    }

    function updateBlock() {
      Handlers.conversational.manipulator.updateBlock(blockData.uuid, prepareBlockData());
      Handlers.conversational.endEditing();
    }

    function cancelEditing() {
      conversationalHandler.endEditing();
    }

    function startEditing() {
      conversationalHandler.startEditing();
      d.notifyType = blockData.notifyType;
      d.message = blockData.message;
      d.imagePath = blockData.imagePath;
    }
  }

  Connections {
    target: conversationalHandler

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if (type == "notify") {
        d.startEditing();
        root.forceFocus();
      }
    }

    function onEditingStopped() {
      if (root.focused) {
        root.releaseFocus();
      }
    }
  }

  NotifyBlockData {
    id: blockData
    uuid: conversationalHandler.selectedBlockUuid
    program: conversationalHandler.program
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    anchors.leftMargin: Sizes.doubleMargin
    spacing: Sizes.singleSpacing

    RowLayout {
      spacing: Sizes.doubleSpacing

      ColumnLayout {
        Layout.fillWidth: false
        spacing: Sizes.singleSpacing

        VerticalFiller {
        }

        RowLayout {
          PathPilotRadioButton {
            ButtonGroup.group: selectionButtonGroup
            checked: d.notifyType === NotifyBlockData.Notification
            text: qsTr("Notification")
            onClicked: d.notifyType = NotifyBlockData.Notification
          }

          PathPilotRadioButton {
            ButtonGroup.group: selectionButtonGroup
            checked: d.notifyType === NotifyBlockData.Warning
            text: qsTr("Warning")
            onClicked: d.notifyType = NotifyBlockData.Warning
          }

          PathPilotRadioButton {
            ButtonGroup.group: selectionButtonGroup
            checked: d.notifyType === NotifyBlockData.Error
            text: qsTr("Error")
            onClicked: d.notifyType = NotifyBlockData.Error
          }
        }

        PathPilotLabel {
          Layout.preferredWidth: 500
          Layout.preferredHeight: 80
          font.family: Fonts.font2
          font.pixelSize: Fonts.conversationalPanel.size1
          wrapMode: Text.WordWrap
          horizontalAlignment: Text.AlignLeft
          verticalAlignment: Text.AlignTop
          text: {
            if (d.notifyType === NotifyBlockData.Notification) {
              return qsTr("Shows a notification popup message. The program continues without interruption.");
            } else if (d.notifyType === NotifyBlockData.Warning) {
              return qsTr("Shows a warning popup message. The program is paused and will resume when the operator presses \"OK\" or abort when the operator presses \"Abort\".");
            } else {
              return qsTr("Shows an error popup message. The program is stopped and aborted when the operator presses \"Abort\"");
            }
          }
        }

        PathPilotLabel {
          text: qsTr("Message")
        }

        Flickable {
          id: flickable
          width: messageTextArea.width
          implicitWidth: messageTextArea.implicitWidth
          Layout.preferredHeight: messageTextArea.Layout.preferredHeight
          contentWidth: messageTextArea.width
          contentHeight: messageTextArea.height
          clip: true
          TextArea.flickable: PathPilotTextArea {
            id: messageTextArea
            Layout.preferredHeight: 150
            Layout.fillWidth: true
            text: ""
            wrapMode: TextArea.Wrap
          }
          ScrollBar.vertical: ScrollBar {
          }
        }

        PathPilotLabel {
          text: qsTr("Image")
        }

        PathPilotTextField {
          id: imagePathEdit
          Layout.fillWidth: true
          font.pixelSize: Fonts.conversationalPanel.size2
          horizontalAlignment: Text.AlignLeft
          readOnly: true
        }

        RowLayout {
          PathPilotButton {
            Layout.fillWidth: true
            text: qsTr("Select")
            onClicked: openFilePopup.open()

            OpenFilePopup {
              id: openFilePopup
              fileFilter: ".*(\\.png|\\.jpg|\\.gif)"
              onAccepted: function (path, name) {
                imagePathEdit.text = path;
              }
            }
          }
          PathPilotButton {
            Layout.fillWidth: true
            text: qsTr("Remove")
            onClicked: imagePathEdit.text = ""
          }
        }

        VerticalFiller {
        }
      }

      ColumnLayout {
        PopupPreview {
          Layout.fillWidth: true
          Layout.fillHeight: true

          NotificationPopupContent {
            id: notificationPopup
            message: d.message
            imagePath: d.imagePath
            notifyType: d.notifyType
          }
        }
      }
    }

    ButtonGroup {
      id: selectionButtonGroup
    }

    VerticalFiller {
    }

    RowLayout {
      HorizontalFiller {
      }
      ConversationalButtons {
        editBlockMode: d.editBlockMode
        blockData: blockData

        onAddClicked: function (uuid) {
          d.addBlock(uuid);
        }
        onUpdateClicked: d.updateBlock()
        onCancelClicked: d.cancelEditing()
      }
    }
  }
}
