import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
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
    property alias position: positionSlider.value
    property alias effort: effortSlider.value
    property alias wait: waitCheckBox.checked

    function prepareBlockData() {
      return {
        "position": d.position,
        "effort": d.effort.toFixed(2),
        "wait": d.wait
      };
    }

    function addBlock(blockUuid) {
      Handlers.conversational.manipulator.beginGroup();
      var uuid = Handlers.conversational.manipulator.createBlock(blockUuid, "actuate_gripper");
      Handlers.conversational.manipulator.updateBlock(uuid, prepareBlockData());
      Handlers.conversational.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
    }

    function updateBlock() {
      Handlers.conversational.manipulator.updateBlock(blockData.uuid, prepareBlockData());
      Handlers.conversational.endEditing();
    }

    function cancelEditing() {
      Handlers.conversational.endEditing();
    }

    function startEditing() {
      Handlers.conversational.startEditing();
      d.position = blockData.position;
      d.effort = blockData.effort;
      d.wait = blockData.wait;
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6

    function onEditingRequested(type) {
      if (type == "actuate_gripper") {
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

  GripperBlockData {
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

    PathPilotLabel {
      text: qsTr("Set Gripper Position")
    }

    RowLayout {
      Layout.fillHeight: true

      PathPilotButton {
        text: qsTr("Open")
        onClicked: {
          d.position = 1.0;
          d.effort = 1.0;
        }
      }

      PathPilotButton {
        text: qsTr("Soft Close")
        onClicked: {
          d.position = 0.0;
          d.effort = 0.2;
        }
      }

      PathPilotButton {
        text: qsTr("Hard Close")
        onClicked: {
          d.position = 0.0;
          d.effort = 1.0;
        }
      }

      PathPilotButton {
        text: qsTr("Release")
        onClicked: {
          d.position = 1.0;
          d.effort = 0.0;
        }
      }
    }

    GridLayout {
      Layout.fillHeight: false
      columns: 2
      PathPilotLabel {
        text: qsTr("Position")
      }

      PathPilotSlider {
        id: positionSlider
      }

      PathPilotLabel {
        text: qsTr("Effort")
      }

      PathPilotSlider {
        id: effortSlider
        value: 0.2
      }
    }

    RowLayout {
      Layout.fillHeight: false
      PathPilotCheckBox {
        id: waitCheckBox
        text: qsTr("Wait until completed")
        checked: true
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
