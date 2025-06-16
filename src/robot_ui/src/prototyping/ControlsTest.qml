import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.base
import pathpilot.core
import pathpilot.controls
import pathpilot.models
import pathpilot.development

ScaledTestBase {
  id: root
  referenceWidth: 700
  minAspectRatio: 10 / 16
  maxAspectRatio: 9 / 16

  Column {
    id: container
    anchors.centerIn: parent
    spacing: Sizes.doubleSpacing
    enabled: enabledCheck.checked

    Led {
      id: led
      activeColor: "green"
      value: true
    }

    Row {
      spacing: Sizes.doubleSpacing
      PathPilotButton {
        id: button
        text: "Button"
        onPressed: console.log("pressed")
        onClicked: console.log("clicked")
        onReleased: console.log("released")
        PathPilotToolTip {
          itemId: "gcode_options_button"
        }
      }
      PathPilotIconButton {
        id: iconButton
        icon_: Icons.program.undo
        PathPilotToolTip {
          itemId: "conv_edit_job_duplicate_button"
          text: qsTr("Undo")
        }
      }
      PathPilotButton {
        text: "Disabled"
        enabled: false
        PathPilotToolTip {
          itemId: "gcode_options_button"
        }
      }
      PathPilotDelayButton {
        text: "Delayed"
        onActivated: console.log("activated")
      }
    }

    Row {
      spacing: Sizes.doubleSpacing
      PathPilotButtonWithLed {
        id: buttonWithLed
        text: "Has LED"
        checkable: true
      }

      PathPilotButtonWithLed {
        text: "big LED"
        bigLed: true
      }

      PathPilotToggleButton {
        text: "two\nleds"
        font.pixelSize: 14
      }
    }

    Row {
      spacing: Sizes.doubleSpacing
      PathPilotIconButton {
        id: buttonWithIcon
        implicitWidth: 140
        text: "With Icon"
        icon_: Icons.filepanel.home
      }
    }

    PathPilotLabel {
      id: text
      text: "User frames"
    }

    Row {
      spacing: Sizes.doubleSpacing

      PathPilotPanel {
        id: panel
        width: 200
        height: 100
      }

      PathPilotBusyIndicator {
        id: busyIndicator
        anchors.verticalCenter: parent.verticalCenter
      }
    }

    Row {
      id: textsRow
      spacing: Sizes.doubleSpacing

      Item {
        width: 1
        height: 1
      } // Not sure why this is necessary

      PathPilotTextField {
        id: textField
        text: "Text Field"
      }

      PathPilotDroField {
        id: droField
      }
    }

    PathPilotTextArea {
      id: textArea
      text: "Multi-line\nText Area"
    }

    PathPilotSlider {
      id: slider
      from: 0.0
      value: 0.5
      to: 1.0
    }

    PathPilotGroupBox {
      title: "Texts"

      Row {
        spacing: Sizes.doubleSpacing

        PathPilotComboBox {
          implicitWidth: 180
          model: ["one", "two", "three", "four", "five"]
        }

        PathPilotComboBox {
          implicitWidth: 180
          textRole: "text"
          model: ListModel {
            ListElement {
              text: "editable"
              foo: 0
            }
            ListElement {
              text: "combo"
            }
            ListElement {
              text: "box"
            }
          }
          editable: true
        }

        PathPilotButton {
          text: "Show Popup"
          implicitWidth: 150
          onClicked: popup.open()
        }
      }
    }

    PathPilotPopup {
      id: popup

      ColumnLayout {
        PathPilotButton {
          text: "Ok"
          onClicked: popup.close()
        }
      }
    }

    Row {
      PathPilotRadioButton {
        id: radioButton
        text: "Top"
        checked: true
      }

      PathPilotRadioButton {
        id: radioButton2
        text: "Bottom"
      }

      PathPilotCheckBox {
        id: checkBox
        text: "Check"
      }
    }

    PathPilotNotebook {
      alignment: radioButton.checked ? Qt.AlignTop : Qt.AlignBottom
      implicitWidth: 550
      implicitHeight: 200

      PathPilotNotebookTab {
        id: tab1
        title: "Title1"

        Rectangle {
          color: "#CCFFFF"
          anchors.fill: parent
        }
      }

      PathPilotNotebookTab {
        id: tab2
        title: "Very Long Title Text That exceeds the Tab Size"

        Rectangle {
          color: "#FFFFCC"
          anchors.fill: parent

          PathPilotButton {
            anchors.centerIn: parent
            text: tab2.focused ? "Unfocus Me" : "Focus Me"
            onClicked: tab2.focused ? tab2.releaseFocus() : tab2.forceFocus()
          }
        }
      }
    }

    PathPilotTableView {
      implicitWidth: 500
      height: 150

      model: SortFilterProxyModel {
        source: dummyModel
        fields: [DummyTableModel.NameRole, DummyTableModel.PhoneRole, DummyTableModel.AgeRole]
        headerTitles: {
          "phone": "Phone Number"
        }
      }

      DummyTableModel {
        id: dummyModel
        inputData: [{
            "name": "Franz",
            "age": 53
          }, {
            "name": "Hugo",
            "phone": 1234676
          }]
      }
    }

    PathPilotButton {
      text: "Low Tooltip"
      PathPilotToolTip {
        itemId: "gcode_options_button"
      }
    }
  }

  CheckBox {
    id: enabledCheck
    checked: true
    text: "Enabled"
  }
}
