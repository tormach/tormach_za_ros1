import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property alias text: textInput.text

  signal accepted(string name)

  onOpened: textInput.forceActiveFocus()

  RowLayout {
    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
      text: qsTr("Name:")
    }
    PathPilotTextField {
      id: textInput
      Layout.fillWidth: true
      implicitWidth: 300

      Keys.onReturnPressed: okButton.forceActiveFocus()
      Keys.onEnterPressed: okButton.forceActiveFocus()
    }
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotButton {
      id: cancelButton
      text: qsTr("Cancel")
      onClicked: root.close()
    }

    PathPilotIconButton {
      id: okButton
      enabled: root.text !== ""
      text: qsTr("OK")
      icon_: Icons.filepanel.rename
      onClicked: {
        root.close();
        root.accepted(textInput.text);
      }
    }
  }
}
