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
    readonly property var digitalOutputs: Handlers.state.digitalIOs.digitalOutputs
    property int setType: SetBlockData.SetDigitalOut
    property bool digitalOutState: false
    property int digitalOutNr: 0
    property string digitalOutName: ""

    function getComboBoxTexts(ios) {
      var names = [];
      for (var i = 0; i < ios.length; ++i) {
        if (ios[i].name !== "") {
          names.push("%1 - %2".arg(ios[i].number).arg(ios[i].name));
        } else {
          names.push(String(ios[i].number));
        }
      }
      return names;
    }

    function selectDigitalOutput() {
      if (d.digitalOutName !== "") {
        for (var i = 0; i < d.digitalOutputs.length; ++i) {
          var output = d.digitalOutputs[i];
          if (output.name === d.digitalOutName) {
            digitalOutputCombo.currentIndex = output.number - 1;
            return;
          }
        }
      } else {
        digitalOutputCombo.currentIndex = d.digitalOutNr - 1;
        return;
      }
      // force update
      digitalOutputCombo.currentIndex = -1;
      digitalOutputCombo.currentIndex = 0;
    }

    function prepareBlockData() {
      return {
        "set_type": d.setType,
        "digital_out_nr": d.digitalOutNr,
        "digital_out_name": d.digitalOutName,
        "digital_out_state": d.digitalOutState
      };
    }

    function addBlock(blockUuid) {
      Handlers.conversational.manipulator.beginGroup();
      var uuid = Handlers.conversational.manipulator.createBlock(blockUuid, "set");
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
      d.setType = blockData.setType;
      if (d.setType === SetBlockData.SetDigitalOut) {
        d.digitalOutNr = blockData.digitalOutNr;
        d.digitalOutName = blockData.digitalOutName;
        d.digitalOutState = blockData.digitalOutState;
        d.selectDigitalOutput();
      }
    }
  }

  Connections {
    target: Handlers.conversational

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if (type == "set") {
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

  SetBlockData {
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
      PathPilotRadioButton {
        ButtonGroup.group: selectionButtonGroup
        checked: d.setType === SetBlockData.SetDigitalOut
        text: qsTr("Set Digital Output")
        onClicked: d.setType = SetBlockData.SetDigitalOut
      }

      PathPilotComboBox {
        id: digitalOutputCombo
        model: d.getComboBoxTexts(d.digitalOutputs)
        currentIndex: 0
        implicitWidth: 300

        Binding {
          target: d
          property: "digitalOutNr"
          value: digitalOutputCombo.currentIndex + 1
        }

        Binding {
          target: d
          property: "digitalOutName"
          value: digitalOutputCombo.currentIndex > -1 ? d.digitalOutputs[digitalOutputCombo.currentIndex].name : ""
        }
      }

      PathPilotRadioButton {
        ButtonGroup.group: onOffGroup
        text: qsTr("Low")
        checked: d.digitalOutState === false
        onClicked: d.digitalOutState = false
      }

      PathPilotRadioButton {
        ButtonGroup.group: onOffGroup
        text: qsTr("High")
        checked: d.digitalOutState === true
        onClicked: d.digitalOutState = true
      }

      ButtonGroup {
        id: onOffGroup
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

        onAddClicked: function (uuid) {
          d.addBlock(uuid);
        }
        onUpdateClicked: d.updateBlock()
        onCancelClicked: d.cancelEditing()
      }
    }
  }
}
