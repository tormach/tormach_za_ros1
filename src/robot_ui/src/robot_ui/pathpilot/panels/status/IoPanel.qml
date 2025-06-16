import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.handlers

PathPilotPanel {
  id: root

  QtObject {
    id: d
    readonly property var digitalInputs: Handlers.state.digitalIOs.digitalInputs
    readonly property var digitalOutputs: Handlers.state.digitalIOs.digitalOutputs
    readonly property var digitalInputNames: Handlers.state.digitalIOs.digitalInputNames
    readonly property var digitalOutputNames: Handlers.state.digitalIOs.digitalOutputNames
  }

  ColumnLayout {
    anchors.fill: parent
    anchors.margins: Sizes.doubleSpacing
    spacing: Sizes.doubleSpacing

    PathPilotLabel {
      text: qsTr("Digital I/O")
    }

    Spacer {
      Layout.fillWidth: true
    }

    RowLayout {
      Layout.fillWidth: true

      HalPinLed {
        id: probe_led
        implicitHeight: probeLabel.height
        topic: "hal_io/probe_in"
      }

      PathPilotLabel {
        id: probeLabel
        Layout.fillWidth: true
        text: qsTr("Probe")
        horizontalAlignment: Text.AlignHLeft
      }
    }

    PathPilotNotebook {
      Layout.fillWidth: true
      Layout.fillHeight: true
      alignment: Qt.AlignTop

      PathPilotNotebookTab {
        id: notebookTab1
        title: qsTr("I/O 1-8")
        enabled: Handlers.app.modifyIosAllowed

        Loader {
          sourceComponent: ioPanelComponent
          onLoaded: {
            item.parent = notebookTab1;
          }
        }
      }

      PathPilotNotebookTab {
        id: notebookTab2
        title: qsTr("I/O 9-16")
        enabled: Handlers.app.modifyIosAllowed

        Loader {
          sourceComponent: ioPanelComponent
          onLoaded: {
            item.parent = notebookTab2;
            item.ioOffset = 8;
          }
        }
      }
    }

    Component {
      id: ioPanelComponent

      Rectangle {
        id: ioGrid
        property int ioOffset: 0
        property int ioStride: 8
        anchors.fill: parent
        anchors.margins: Sizes.thinBorder
        color: Colors.gray5

        GridLayout {
          columns: 2
          anchors.fill: parent
          anchors.margins: Sizes.singleMargin

          Repeater {
            id: inRepeater
            model: d.digitalInputs.slice(ioGrid.ioOffset, ioGrid.ioOffset + ioGrid.ioStride)

            RowLayout {
              Layout.row: index + 1
              Layout.column: 0

              DigitalInputLed {
                topic: modelData.topic
                nr: modelData.number
              }

              PathPilotTextField {
                id: inputTextField
                Layout.fillWidth: true
                implicitWidth: 120
                horizontalAlignment: Text.AlignLeft
                readOnly: [15, 16].includes(modelData.number)

                validator: RegularExpressionValidator {
                  regularExpression: /([a-zA-Z_][A-Za-z0-9_ ]*)?/
                }

                Binding {
                  target: inputTextField
                  property: "text"
                  value: modelData.name
                }

                function validateText() {
                  error = text != "" && !inputNameValidator.validate(text, 0);
                }

                onEditingFinished: {
                  if (error) {
                    text = modelData.name;
                    error = false;
                    return;
                  }
                  if (text == modelData.name) {
                    return;
                  }
                  modelData.name = text;
                }

                onTextEdited: {
                  text = text.replace(/\s/g, '_');
                  validateText();
                }

                NameValidator {
                  id: inputNameValidator
                  names: d.digitalInputNames
                  ignoredName: modelData.name
                }
              }
            }
          }

          Repeater {
            id: outRepeater
            model: d.digitalOutputs.slice(ioGrid.ioOffset, ioGrid.ioOffset + ioGrid.ioStride)

            RowLayout {
              Layout.row: index + 1
              Layout.column: 1

              DigitalOutputButton {
                topic: modelData.topic
                nr: modelData.number
              }

              PathPilotTextField {
                id: outputTextField
                Layout.fillWidth: true
                implicitWidth: 120
                horizontalAlignment: Text.AlignLeft

                validator: RegularExpressionValidator {
                  regularExpression: /([a-zA-Z_][A-Za-z0-9_ ]*)?/
                }

                Binding {
                  target: outputTextField
                  property: "text"
                  value: modelData.name
                }

                function validateText() {
                  error = text != "" && !outputNameValidator.validate(text, 0);
                }

                onEditingFinished: {
                  if (error) {
                    text = modelData.name;
                    error = false;
                    return;
                  }
                  if (text == modelData.name) {
                    return;
                  }
                  modelData.name = text;
                }

                onTextEdited: {
                  text = text.replace(/\s/g, '_');
                  validateText();
                }

                NameValidator {
                  id: outputNameValidator
                  names: d.digitalOutputNames
                  ignoredName: modelData.name
                }
              }
            }
          }
        }
      }
    }
  }
}
