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
    readonly property var digitalInputs: Handlers.state.digitalIOs.digitalInputs
    property double sleepTime: 0.5
    property int waitType: WaitBlockData.Sleep
    property bool digitalInState: false
    property int digitalInNr: 1
    property string digitalInName: ""
    property bool optional: false
    property bool active: false

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

    function selectDigitalInput() {
      if (d.digitalInName !== "") {
        for (var i = 0; i < d.digitalInputs.length; ++i) {
          var input = d.digitalInputs[i];
          if (input.name === d.digitalInName) {
            digitalInputCombo.currentIndex = input.number - 1;
            return;
          }
        }
      } else {
        digitalInputCombo.currentIndex = d.digitalInNr - 1;
        return;
      }
      // force update
      digitalOutputCombo.currentIndex = -1;
      digitalInputCombo.currentIndex = 0;
    }

    function prepareBlockData() {
      return {
        "wait_type": d.waitType,
        "sleep_time": d.sleepTime,
        "digital_in_nr": d.digitalInNr,
        "digital_in_name": d.digitalInName,
        "digital_in_state": d.digitalInState,
        "optional": d.optional,
        "active": d.active
      };
    }

    function addBlock(blockUuid) {
      Handlers.conversational.manipulator.beginGroup();
      var uuid = Handlers.conversational.manipulator.createBlock(blockUuid, "wait");
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
  }

  Connections {
    target: conversationalHandler

    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onEditingRequested(type) {
      if (type == "wait") {
        conversationalHandler.startEditing();
        root.forceFocus();
        d.waitType = blockData.waitType;
        if (d.waitType === WaitBlockData.Sleep) {
          d.sleepTime = blockData.sleepTime;
        } else if (d.waitType === WaitBlockData.Pause) {
          d.optional = blockData.optional;
          d.active = blockData.active;
        } else if (d.waitType === WaitBlockData.WaitForDigitalIn) {
          d.digitalInNr = blockData.digitalInNr;
          d.digitalInName = blockData.digitalInName;
          d.digitalInState = blockData.digitalInState;
          d.selectDigitalInput();
        }
      }
    }

    function onEditingStopped() {
      if (root.focused) {
        root.releaseFocus();
      }
    }
  }

  WaitBlockData {
    id: blockData
    uuid: conversationalHandler.selectedBlockUuid
    program: conversationalHandler.program
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
        id: sleepRadioButton
        ButtonGroup.group: selectionButtonGroup
        checked: d.waitType === WaitBlockData.Sleep
        text: qsTr("Wait for")
        onClicked: d.waitType = WaitBlockData.Sleep
      }

      PathPilotTextField {
        implicitWidth: 80
        enabled: sleepRadioButton.checked
        text: d.sleepTime
        validator: DoubleValidator {
          bottom: 0
        }
        onEditingFinished: d.sleepTime = Number(text)
      }

      PathPilotLabel {
        text: qsTr("Seconds")
      }
    }

    RowLayout {
      PathPilotRadioButton {
        id: digitalInRadioButton
        ButtonGroup.group: selectionButtonGroup
        checked: d.waitType === WaitBlockData.WaitForDigitalIn
        text: qsTr("Wait for Digital Input")
        onClicked: d.waitType = WaitBlockData.WaitForDigitalIn
      }

      PathPilotComboBox {
        id: digitalInputCombo
        enabled: digitalInRadioButton.checked
        model: d.getComboBoxTexts(d.digitalInputs)
        currentIndex: 0
        implicitWidth: 300

        Binding {
          target: d
          property: "digitalInNr"
          value: digitalInputCombo.currentIndex + 1
        }

        Binding {
          target: d
          property: "digitalInName"
          value: digitalInputCombo.currentIndex > -1 ? d.digitalInputs[digitalInputCombo.currentIndex].name : ""
        }
      }

      PathPilotRadioButton {
        ButtonGroup.group: highLowGroup
        enabled: digitalInRadioButton.checked
        text: qsTr("Low")
        checked: d.digitalInState === false
        onClicked: d.digitalInState = false
      }

      PathPilotRadioButton {
        ButtonGroup.group: highLowGroup
        enabled: digitalInRadioButton.checked
        text: qsTr("High")
        checked: d.digitalInState === true
        onClicked: d.digitalInState = true
      }

      ButtonGroup {
        id: highLowGroup
      }

      ButtonGroup {
        id: selectionButtonGroup
      }
    }

    RowLayout {
      PathPilotRadioButton {
        id: pauseRadioButton
        ButtonGroup.group: selectionButtonGroup
        checked: d.waitType === WaitBlockData.Pause && !d.optional
        text: qsTr("Pause")
        onClicked: {
          d.waitType = WaitBlockData.Pause;
          d.optional = false;
        }
      }

      PathPilotRadioButton {
        id: optionalPauseRadioButton
        ButtonGroup.group: selectionButtonGroup
        checked: d.waitType === WaitBlockData.Pause && d.optional
        text: qsTr("Optional Pause")
        onClicked: {
          d.waitType = WaitBlockData.Pause;
          d.optional = true;
        }
      }

      PathPilotCheckBox {
        id: activePauseCheckBox
        checked: d.active
        text: qsTr("Allow Jogging")
        onClicked: {
          d.active = true;
        }
      }
    }

    RowLayout {
      PathPilotRadioButton {
        id: exitRadioButton
        ButtonGroup.group: selectionButtonGroup
        checked: d.waitType === WaitBlockData.Exit
        text: qsTr("Exit Program")
        onClicked: d.waitType = WaitBlockData.Exit
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
