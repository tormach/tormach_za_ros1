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
    if (visible) {
      subProgramTextInput.defaultText();
    }
  }

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    readonly property ProgramManipulator manipulator: Handlers.conversational.manipulator
    readonly property string type: newSubProgRadioButton.checked ? "subprogram" : "call"
    readonly property var subProgramNames: blockData.subProgramNames
    property string name: "subprogram_1"
    property string currentName: ""

    function selectSubProgram() {
      subProgramComboBox.currentIndex = -1;
      var newIndex = subProgramComboBox.find(d.name);
      if (newIndex > -1) {
        subProgramComboBox.currentIndex = newIndex;
      } else {
        subProgramComboBox.editText = d.name;
      }
    }

    function prepareBlockData(type) {
      return {
        "name": type === "subprogram" ? d.name : subProgramComboBox.editText,
        "type": type
      };
    }

    function addBlock(blockUuid) {
      d.manipulator.beginGroup();
      var uuid = "";
      var type = d.type;
      if (type === "subprogram") {
        uuid = d.manipulator.createBlock(blockUuid, "program", true);
        d.manipulator.createChildBlock(uuid, "pass");
      } else {
        uuid = d.manipulator.createBlock(blockUuid, "call");
      }
      d.manipulator.updateBlock(uuid, prepareBlockData(type));
      d.manipulator.endGroup();
      Handlers.conversational.selectBlock(uuid);
      subProgramTextInput.defaultText();
    }

    function updateBlock() {
      if (d.type === "subprogram") {
        d.manipulator.renameSubProgram(d.currentName, d.name);
      } else {
        d.manipulator.updateBlock(blockData.uuid, prepareBlockData());
      }
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
      if (type === "call" || type === "subprogram") {
        Handlers.conversational.startEditing();
        root.forceFocus();
        d.name = blockData.name;
        d.currentName = blockData.name;
        callSubProgRadioButton.checked = type === "call";
        newSubProgRadioButton.checked = type === "subprogram";
        subProgramTextInput.validateText();
        d.selectSubProgram();
      }
    }

    function onEditingStopped() {
      if (root.focused) {
        root.releaseFocus();
        d.currentName = "";
        subProgramTextInput.defaultText();
      }
    }
  }

  SubProgramBlockData {
    id: blockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  NameValidator {
    id: nameValidator
    defaultPrefix: "subprogram_"
    names: d.subProgramNames
    ignoredName: d.currentName
  }

  WaypointNameValidator {
    id: waypointNameValidator
    waypoints: Handlers.conversational.program
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
      enabled: !blockData.valid || blockData.level == 1
      onEnabledChanged: {
        if (enabled) {
          newSubProgRadioButton.checked = true;
        }
      }

      PathPilotRadioButton {
        id: newSubProgRadioButton
        ButtonGroup.group: selectionButtonGroup
        enabled: !d.editBlockMode
        checked: true
        text: qsTr("New Subprogram")
      }

      PathPilotTextField {
        id: subProgramTextInput
        implicitWidth: 300
        enabled: newSubProgRadioButton.checked

        validator: RegularExpressionValidator {
          regularExpression: /[a-zA-Z_][A-Za-z0-9_ ]*/
        }

        Binding {
          target: subProgramTextInput
          property: "text"
          value: d.name
        }

        function validateText() {
          error = !nameValidator.validate(text, 0);
          if (!error) {
            error |= !waypointNameValidator.validate(text, 0);
          }
          if (!error) {
            error |= !syntaxValidator.validate(text, 0);
          }
        }

        function defaultText() {
          d.name = nameValidator.generateDefaultName();
        }

        onEditingFinished: d.name = text
        onTextEdited: {
          text = text.replace(/\s/g, '_');
          validateText();
        }
      }
    }

    RowLayout {
      enabled: blockData.valid && blockData.level > 1
      onEnabledChanged: {
        if (enabled) {
          callSubProgRadioButton.checked = true;
        }
      }

      PathPilotRadioButton {
        id: callSubProgRadioButton
        ButtonGroup.group: selectionButtonGroup
        enabled: !d.editBlockMode
        text: qsTr("Call Subprogram")
      }

      PathPilotComboBox {
        id: subProgramComboBox
        implicitWidth: 300
        enabled: callSubProgRadioButton.checked
        model: d.subProgramNames
        editable: true
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
        minimumLevel: d.type === "subprogram" ? 0 : 1
        addUpdateEnabled: d.type === "subprogram" ? !subProgramTextInput.error && blockData.valid : subProgramComboBox.editText !== ""
        onAddClicked: function (uuid) {
          d.addBlock(uuid);
        }
        onUpdateClicked: d.updateBlock()
        onCancelClicked: d.cancelEditing()
      }
    }
  }
}
