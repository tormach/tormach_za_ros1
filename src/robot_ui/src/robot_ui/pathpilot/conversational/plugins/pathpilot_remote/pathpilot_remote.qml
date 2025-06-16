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
import pathpilot.robot.machinetalk
import pathpilot.plugins.pathpilot
import pathpilot.handlers

ConversationalItem {
  id: root

  QtObject {
    id: d
    readonly property bool editBlockMode: Handlers.conversational.editingActive
    readonly property var digitalOutputs: Handlers.state.digitalIOs.digitalOutputs
    property int commandType: PathPilotBlockData.MdiCommand
    property alias commandLine: commandLineTextField.text
    property alias instance: instanceComboBox.currentText
    property alias instanceSpecified: instanceCheckBox.checked
    property var pathpilotStateNames: [qsTr("Ready"), qsTr("Idle"), qsTr("Disconnected"), qsTr("Estop"), qsTr("Running")]
    property var pathpilotStates: ["ready", "idle", "disconnected", "estop", "running"]
    property string pathpilotState: pathpilotStates[pathpilotStateComboBox.currentIndex]

    function selectInstance(instance) {
      var model = selectedInstanceModel;
      for (var i = 0; i < model.rowCount(); ++i) {
        var index = model.index(i, 0);
        var name = model.data(index, MachinetalkInstanceListModel.NameRole);
        if (instance === name) {
          instanceComboBox.currentIndex = i;
          return;
        }
      }
      instanceComboBox.currentIndex = 0;
    }

    function selectState(state) {
      for (var i = 0; i < d.pathpilotStates.length; ++i) {
        var name = d.pathpilotStates[i];
        if (state == name) {
          pathpilotStateComboBox.currentIndex = i;
          return;
        }
      }
      pathpilotStateComboBox.currentIndex = 0;
    }

    function prepareBlockData() {
      return {
        "command_type": d.commandType,
        "command_line": d.commandLine,
        "instance": d.instanceSpecified ? d.instance : "",
        "state": d.pathpilotState
      };
    }

    function addBlock(blockUuid) {
      Handlers.conversational.manipulator.beginGroup();
      var uuid = Handlers.conversational.manipulator.createBlock(blockUuid, "pathpilot");
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
      d.commandType = blockData.commandType;
      if (d.commandType === PathPilotBlockData.MdiCommand) {
        d.commandLine = blockData.commandLine;
      }
      d.instanceSpecified = blockData.instance !== "";
      d.selectInstance(blockData.instance);
      d.selectState(blockData.state);
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if (type == "pathpilot") {
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

  PathPilotBlockData {
    id: blockData
    uuid: Handlers.conversational.selectedBlockUuid
    program: Handlers.conversational.program
  }

  FilteredInstanceModel {
    id: selectedInstanceModel
    source: Handlers.state.machinetalk.instanceModel
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.singleMargin
    anchors.leftMargin: Sizes.doubleMargin
    spacing: Sizes.singleSpacing

    RowLayout {
      spacing: Sizes.doubleSpacing

      ColumnLayout {
        spacing: Sizes.singleSpacing
        VerticalFiller {
        }

        RowLayout {
          PathPilotRadioButton {
            id: mdiCommandRadioButton
            ButtonGroup.group: selectionButtonGroup
            checked: d.commandType === PathPilotBlockData.MdiCommand
            text: qsTr("MDI Command")
            onClicked: d.commandType = PathPilotBlockData.MdiCommand
          }

          PathPilotTextField {
            id: commandLineTextField
            implicitWidth: 400
            horizontalAlignment: Text.AlignLeft
            enabled: mdiCommandRadioButton.checked
          }
        }

        PathPilotRadioButton {
          id: cycleStartRadioButton
          ButtonGroup.group: selectionButtonGroup
          checked: d.commandType === PathPilotBlockData.CycleStartCommand
          text: qsTr("Cycle Start")
          onClicked: d.commandType = PathPilotBlockData.CycleStartCommand
        }
        PathPilotRadioButton {
          id: abortRadioButton
          ButtonGroup.group: selectionButtonGroup
          checked: d.commandType === PathPilotBlockData.AbortCommand
          text: qsTr("Abort")
          onClicked: d.commandType = PathPilotBlockData.AbortCommand
        }

        RowLayout {
          PathPilotRadioButton {
            id: waitForStateRadioButton
            ButtonGroup.group: selectionButtonGroup
            checked: d.commandType === PathPilotBlockData.WaitForState
            text: qsTr("Wait for State")
            onClicked: d.commandType = PathPilotBlockData.WaitForState
          }

          PathPilotComboBox {
            id: pathpilotStateComboBox
            enabled: waitForStateRadioButton.checked
            model: d.pathpilotStateNames
            currentIndex: 0
          }
        }

        ButtonGroup {
          id: selectionButtonGroup
        }

        VerticalFiller {
        }
      }

      ColumnLayout {
        VerticalFiller {
        }

        RowLayout {
          spacing: Sizes.doubleSpacing
          PathPilotCheckBox {
            id: instanceCheckBox
            text: qsTr("Instance:")
          }

          PathPilotComboBox {
            id: instanceComboBox
            enabled: instanceCheckBox.checked
            model: selectedInstanceModel
            textRole: "name"
          }
        }

        VerticalFiller {
        }
      }
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
