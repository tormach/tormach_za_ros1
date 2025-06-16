import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.controls
import pathpilot.core
import pathpilot.conversational
import pathpilot.robot
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import pathpilot.handlers

ConversationalItem {
  id: root

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    readonly property ProgramManipulator manipulator: Handlers.conversational.manipulator
    readonly property var variableNames: blockData.variableNames
    property alias text: textArea.text

    function prepareBlockData() {
      var numLines = d.text.split(/\r\n|\r|\n/).length;
      var commentType = numLines > 1 ? CommentBlockData.BlockComment : CommentBlockData.LineComment;
      return {
        "comment_type": commentType,
        "text": d.text
      };
    }

    function addBlock(blockUuid) {
      d.manipulator.beginGroup();
      var uuid = "";
      uuid = d.manipulator.createBlock(blockUuid, "comment");
      d.manipulator.updateBlock(uuid, prepareBlockData());
      d.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
    }

    function updateBlock() {
      d.manipulator.updateBlock(blockData.uuid, prepareBlockData());
      Handlers.conversational.endEditing();
    }

    function cancelEditing() {
      Handlers.conversational.endEditing();
    }

    function startEditing() {
      Handlers.conversational.startEditing();
      d.text = blockData.text;
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if (type === "comment") {
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

  CommentBlockData {
    id: blockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    anchors.leftMargin: Sizes.doubleMargin
    spacing: Sizes.singleSpacing

    VerticalFiller {
    }

    RowLayout {
      PathPilotLabel {
        text: qsTr("Comment")
      }

      Flickable {
        id: flickable
        width: textArea.width
        implicitWidth: textArea.implicitWidth
        Layout.preferredHeight: textArea.Layout.preferredHeight
        contentWidth: textArea.width
        contentHeight: textArea.Layout.preferredHeight
        clip: true

        TextArea.flickable: PathPilotTextArea {
          id: textArea
          implicitWidth: 600
          width: 600
          Layout.preferredHeight: 150
          text: ""
          wrapMode: TextArea.Wrap
          background: Rectangle {
          }
        }
        ScrollBar.vertical: ScrollBar {
        }
      }
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
