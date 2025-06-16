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

  onVisibleChanged: {
    if (root.visible) {
      nameComboBox.defaultText();
      expressionTextInput.validateText();
    }
  }

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    readonly property ProgramManipulator manipulator: Handlers.conversational.manipulator
    readonly property var variableNames: blockData.variableNames
    property string name: "var_1"
    property string operator: "="
    property alias expression: expressionTextInput.text

    function selectName() {
      nameComboBox.currentIndex = Math.max(nameComboBox.find(d.name), 0);
    }

    function selectOperator() {
      operatorComboBox.currentIndex = Math.max(operatorComboBox.find(d.operator), 0);
    }

    function prepareBlockData() {
      return {
        "name": d.name,
        "operator": operatorComboBox.currentText,
        "expression": d.expression
      };
    }

    function addBlock(blockUuid) {
      d.manipulator.beginGroup();
      var uuid = "";
      uuid = d.manipulator.createBlock(blockUuid, "assignment");
      d.manipulator.updateBlock(uuid, prepareBlockData());
      d.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
      nameComboBox.defaultText();
    }

    function updateBlock() {
      d.manipulator.updateBlock(blockData.uuid, prepareBlockData());
      Handlers.conversational.endEditing();
    }

    function cancelEditing() {
      Handlers.conversational.endEditing();
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if (type === "assignment") {
        Handlers.conversational.startEditing();
        root.forceFocus();
        d.name = blockData.name;
        d.operator = blockData.operator;
        d.expression = blockData.expression;
        nameComboBox.validateText();
        d.selectName();
        d.selectOperator();
      }
    }

    function onEditingStopped() {
      if (root.focused) {
        root.releaseFocus();
        nameComboBox.defaultText();
      }
    }
  }

  AssignmentBlockData {
    id: blockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  NameValidator {
    id: nameValidator
    defaultPrefix: "var_"
  }

  SyntaxValidator {
    id: syntaxValidator
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    anchors.leftMargin: Sizes.doubleMargin
    spacing: Sizes.singleSpacing

    VerticalFiller {
    }

    RowLayout {
      onEnabledChanged: {
        if (enabled) {
          assignRadioButton.checked = true;
        }
      }

      PathPilotRadioButton {
        id: assignRadioButton
        ButtonGroup.group: selectionButtonGroup
        enabled: !d.editBlockMode
        checked: true
        text: qsTr("Assign")
      }

      PathPilotComboBox {
        id: nameComboBox
        implicitWidth: 200
        enabled: assignRadioButton.checked
        model: d.variableNames
        editable: true

        validator: RegularExpressionValidator {
          regularExpression: /[a-zA-Z_][A-Za-z0-9_ ]*/
        }

        function validateText() {
          error = !nameValidator.validate(editText, 0);
          if (!error) {
            error |= !syntaxValidator.validate(editText, 0);
          }
          if (!error) {
            d.name = editText;
          }
        }

        function defaultText() {
          d.name = nameValidator.generateDefaultName();
          nameComboBox.editText = d.name;
        }

        onEditTextChanged: {
          editText = editText.replace(/\s/g, '_');
          validateText();
        }

        onModelChanged: {
          if (model.length === 0) {
            defaultText();
          }
        }

        Binding {
          target: nameComboBox
          property: "editText"
          value: d.name
        }
      }

      PathPilotComboBox {
        id: operatorComboBox
        implicitWidth: 80
        enabled: assignRadioButton.checked
        model: ["=", "+=", "-=", "*=", "/=", "%=", "**=", "//="]
      }

      PathPilotTextField {
        id: expressionTextInput
        implicitWidth: 300
        enabled: assignRadioButton.checked
        text: "0"

        function validateText() {
          error = !syntaxValidator.validate(text, 0);
        }

        onTextChanged: validateText()
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
        addUpdateEnabled: !nameComboBox.error && !expressionTextInput.error && blockData.valid

        onAddClicked: function (uuid) {
          d.addBlock(uuid);
        }
        onUpdateClicked: d.updateBlock()
        onCancelClicked: d.cancelEditing()
      }
    }
  }
}
