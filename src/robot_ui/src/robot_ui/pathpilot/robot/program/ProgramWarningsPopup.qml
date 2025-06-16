import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.handlers

PathPilotPopup {
  id: root
  signal continueClicked
  signal abortClicked

  property int _width: 800
  spacing: Sizes.singleSpacing

  readonly property QtObject _d: QtObject {
    id: d
    readonly property var warnings: Handlers.conversational.programWarnings
    property var messages: []
  }

  onOpened: {
    var messages = [];
    for (var key in d.warnings) {
      var values = d.warnings[key];
      for (var i = 0; i < values.length; ++i) {
        messages.push(values[i].message);
      }
    }
    d.messages = messages;
  }

  ColumnLayout {
    Layout.preferredWidth: _width
    RowLayout {
      Icon {
        icon: Icons.popup.warning
      }

      PathPilotLabel {
        text: qsTr("Program  warnings")
      }
    }

    PathPilotLabel {
      Layout.fillWidth: true
      font.family: Fonts.font2
      font.pixelSize: Fonts.conversationalPopups.size2
      font.bold: true
      horizontalAlignment: Text.AlignLeft
      wrapMode: Text.Wrap
      text: qsTr("The program contains errors. It is recommended to fix these issues before continuing.")
    }

    Rectangle {
      Layout.fillWidth: true
      Layout.preferredHeight: 400
      radius: Sizes.smallRadius
      border.color: Colors.gray3
      border.width: Sizes.thinBorder

      ScrollView {
        anchors.fill: parent

        PathPilotTextArea {
          id: messageTextArea
          implicitWidth: 0
          implicitHeight: 0
          text: d.messages.join("\n")
          wrapMode: TextArea.Wrap
          background: Item {
          }
        }
      }
    }

    RowLayout {
      HorizontalFiller {
      }

      PathPilotButton {
        id: abortButton
        implicitWidth: 120
        text: qsTr("Abort")
        onClicked: {
          root.close();
          root.abortClicked();
        }
      }

      PathPilotButton {
        id: okButton
        implicitWidth: 120
        text: qsTr("Continue")
        onClicked: {
          root.close();
          root.continueClicked();
        }
      }
    }
  }
}
