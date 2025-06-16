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
  title: qsTr("Loop")

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    readonly property ProgramManipulator manipulator: Handlers.conversational.manipulator
    property alias condition: conditionInput.text
    property alias count: countInput.text
    property alias variable: variableInput.text

    function prepareBlockData(type) {
      return {
        "condition": d.condition,
        "loop_type": type,
        "count": Number(count),
        "variable": variable
      };
    }

    function addBlock(blockUuid) {
      d.manipulator.beginGroup();
      var uuid = d.manipulator.createBlock(blockUuid, "loop");
      if (whileRadioButton.checked) {
        d.manipulator.updateBlock(uuid, prepareBlockData(LoopBlockData.WhileLoop));
      } else {
        d.manipulator.updateBlock(uuid, prepareBlockData(LoopBlockData.ForRangeLoop));
      }
      d.manipulator.createChildBlock(uuid, "pass");
      d.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
    }

    function updateBlock() {
      if (whileRadioButton.checked) {
        d.manipulator.updateBlock(blockData.uuid, prepareBlockData(LoopBlockData.WhileLoop));
      } else {
        d.manipulator.updateBlock(blockData.uuid, prepareBlockData(LoopBlockData.ForRangeLoop));
      }
      Handlers.conversational.endEditing();
    }

    function cancelEditing() {
      Handlers.conversational.endEditing();
    }

    function startEditing() {
      Handlers.conversational.startEditing();
      if (blockData.loopType === LoopBlockData.WhileLoop) {
        whileRadioButton.checked = true;
        d.condition = blockData.condition;
      } else {
        forRadioButton.checked = true;
        d.count = blockData.count;
        d.variable = blockData.variable;
      }
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if (type === "loop") {
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

  LoopBlockData {
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
        id: whileRadioButton
        ButtonGroup.group: selectionButtonGroup
        checked: true
        text: qsTr("While")
      }

      PathPilotTextField {
        id: conditionInput
        implicitWidth: 300
        enabled: whileRadioButton.checked
        text: "True"

        function validateText() {
          error = !syntaxValidator.validate(text, 0);
        }

        onTextChanged: validateText()
      }
    }

    RowLayout {
      PathPilotRadioButton {
        id: forRadioButton
        ButtonGroup.group: selectionButtonGroup
        text: qsTr("Loop")
      }

      PathPilotTextField {
        id: countInput
        implicitWidth: 50
        enabled: forRadioButton.checked
        validator: RegularExpressionValidator {
          regularExpression: /[0-9]+/
        }
        text: "5"
      }

      Item {
        width: 3
      }

      PathPilotLabel {
        text: qsTr("times, using variable:")
      }

      Item {
        width: 3
      }

      PathPilotTextField {
        id: variableInput
        implicitWidth: 200
        enabled: forRadioButton.checked
        text: "i"
        validator: RegularExpressionValidator {
          regularExpression: /[a-zA-Z_][a-zA-Z_0-9 ]*/
        }

        function validateText() {
          error = !syntaxValidator.validate(text, 0);
        }

        onTextEdited: {
          text = text.replace(/\s/g, '_');
          validateText();
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
      addUpdateEnabled: (!conditionInput.error && whileRadioButton.checked) || (countInput.acceptableInput && !variableInput.error && forRadioButton.checked)

      onAddClicked: function (uuid) {
        d.addBlock(uuid);
      }
      onUpdateClicked: d.updateBlock()
      onCancelClicked: d.cancelEditing()
    }
  }
}
