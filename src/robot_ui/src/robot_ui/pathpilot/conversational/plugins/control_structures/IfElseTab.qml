import QtQuick
import QtQuick.Controls
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.conversational
import pathpilot.robot.program
import pathpilot.robot.program.blocks
import pathpilot.handlers

SubNotebookTab {
  id: root
  title: qsTr("If / Then / Else")

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    readonly property ProgramManipulator manipulator: Handlers.conversational.manipulator
    readonly property string type: ifRadioButton.checked ? "if" : (elseIfRadioButton.checked ? "elif" : "else")
    property alias condition: conditionInput.text

    function prepareBlockData(type) {
      return {
        "condition": d.condition,
        "type": type
      };
    }

    function addBlock(blockUuid) {
      d.manipulator.beginGroup();
      var uuid = "";
      if (d.type === "if") {
        uuid = d.manipulator.createBlock(blockUuid, "if");
      } else if (d.type === "elif") {
        uuid = d.manipulator.createGroupBlock(blockUuid, "if", false);
      } else {
        uuid = d.manipulator.createGroupBlock(blockUuid, "if", true);
        d.manipulator.updateBlock(uuid, {
            "group_fixed": true
          });
      }
      d.manipulator.updateBlock(uuid, prepareBlockData(d.type));
      d.manipulator.createChildBlock(uuid, "pass");
      d.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
    }

    function updateBlock() {
      d.manipulator.updateBlock(blockData.uuid, prepareBlockData(d.type));
      Handlers.conversational.endEditing();
    }

    function cancelEditing() {
      Handlers.conversational.endEditing();
    }

    function startEditing() {
      Handlers.conversational.startEditing();
      d.condition = blockData.condition;
      if (blockData.type === "if") {
        ifRadioButton.checked = true;
      } else if (blockData.type === "elif") {
        elseIfRadioButton.checked = true;
      }
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if ((type === "if") || (type === "elif")) {
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

  IfBlockData {
    id: blockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  SyntaxValidator {
    id: syntaxValidator
  }

  VerticalFiller {
  }

  ColumnLayout {
    RowLayout {

      PathPilotRadioButton {
        id: ifRadioButton
        ButtonGroup.group: selectionButtonGroup
        checked: true
        enabled: !d.editBlockMode
        text: qsTr("If")
      }

      PathPilotRadioButton {
        id: elseIfRadioButton
        ButtonGroup.group: selectionButtonGroup
        enabled: blockData.typeMatches && !d.editBlockMode
        text: qsTr("Else If")

        onEnabledChanged: {
          if (!d.editBlockMode && checked && !enabled) {
            ifRadioButton.checked = true;
          }
        }
      }

      PathPilotTextField {
        id: conditionInput
        implicitWidth: 300
        enabled: ifRadioButton.checked || elseIfRadioButton.checked
        text: "True"

        function validateText() {
          error = !syntaxValidator.validate(text, 0);
        }

        onTextChanged: validateText()
      }
    }

    RowLayout {
      PathPilotRadioButton {
        id: elseRadioButton
        ButtonGroup.group: selectionButtonGroup
        enabled: blockData.typeMatches && !blockData.hasElse && !d.editBlockMode
        text: qsTr("Else")

        onEnabledChanged: {
          if (!d.editBlockMode && checked && !enabled) {
            ifRadioButton.checked = true;
          }
        }
      }
    }

    ButtonGroup {
      id: selectionButtonGroup
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
      addUpdateEnabled: !conditionInput.error || elseRadioButton.checked

      onAddClicked: function (uuid) {
        d.addBlock(uuid);
      }
      onUpdateClicked: d.updateBlock()
      onCancelClicked: d.cancelEditing()
    }
  }
}
