import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  implicitWidth: 600

  PathPilotLabel {
    text: qsTr("Keyboard Shortcuts")
  }

  GridLayout {
    Layout.fillWidth: true
    columns: 6

    Repeater {
      model: [qsTr("X+"), qsTr("X-"), qsTr("Y+"), qsTr("Y-"), qsTr("Z+"), qsTr("Z-"), qsTr("A+"), qsTr("A-"), qsTr("B+"), qsTr("B-"), qsTr("C+"), qsTr("C-")]

      PathPilotLabel {
        Layout.column: 0
        Layout.row: index
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: modelData
      }
    }

    Repeater {
      model: [qsTr("Right / →"), qsTr("Left / ←"), qsTr("Up / ↑"), qsTr("Down / ↓"), qsTr("Page Up"), qsTr("Page Down"), qsTr("Period / ."), qsTr("Comma / ,"), qsTr("Apostrophe / '"), qsTr("Semicolon / ;"), qsTr("Bracket Right / ]"), qsTr("Bracket Left / [")]

      PathPilotLabel {
        Layout.column: 1
        Layout.row: index
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: modelData
      }
    }

    Repeater {
      model: 6

      PathPilotLabel {
        Layout.column: 2
        Layout.row: index
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: qsTr("Select Joint %1").arg(index + 1)
      }
    }

    Repeater {
      model: 6

      PathPilotLabel {
        Layout.column: 3
        Layout.row: index
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: "%1".arg(index + 1)
      }
    }

    Repeater {
      model: [qsTr("Joint Jog -"), qsTr("Joint Jog +")]

      PathPilotLabel {
        Layout.column: 2
        Layout.row: index + 6
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: modelData
      }
    }

    Repeater {
      model: ["9", "0"]

      PathPilotLabel {
        Layout.column: 3
        Layout.row: index + 6
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: modelData
      }
    }

    Repeater {
      model: [qsTr("Rapid"), qsTr("Toggle Continuous"), qsTr("Toggle Jog Frame"), qsTr("Cycle Step Size"), qsTr("Decrease Jog Velocity"), qsTr("Increase Jog Velocity")]

      PathPilotLabel {
        Layout.column: 4
        Layout.row: index
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: modelData
      }
    }

    Repeater {
      model: [qsTr("Shift"), qsTr("c"), qsTr("f"), qsTr("s"), qsTr("q"), qsTr("w")]

      PathPilotLabel {
        Layout.column: 5
        Layout.row: index
        Layout.fillWidth: true
        font.family: Fonts.font2
        font.pixelSize: Fonts.rightPanel.size1
        text: modelData
      }
    }
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotIconButton {
      id: closeButton
      text: qsTr("Close")
      onClicked: {
        root.close();
      }
    }
  }
}
