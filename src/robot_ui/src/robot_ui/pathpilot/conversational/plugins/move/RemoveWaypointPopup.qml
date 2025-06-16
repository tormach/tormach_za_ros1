import QtQuick 2.3
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.2
import QtQuick.Window 2.0
import pathpilot.core 1.0
import pathpilot.controls 1.0

PathPilotPopup {
  id: root
  signal accepted
  onOpened: cancelButton.forceActiveFocus()

  ColumnLayout {
    spacing: 20
    RowLayout {
      Icon {
        id: image
        icon: Icons.popup.warning
      }
      PathPilotLabel {
        text: qsTr("Removing a global waypoint is irreversible,\nare you sure?")
        font.family: Fonts.font2
        font.pixelSize: Fonts.filePanel.size1
        font.bold: true
      }
    }

    RowLayout {
      HorizontalFiller {
      }
      PathPilotIconButton {
        id: cancelButton
        text: qsTr("Cancel")
        onClicked: root.close()
      }
      PathPilotIconButton {
        id: okButton
        labelColor: Colors.red1
        text: qsTr("OK")
        icon_: Icons.filepanel.delete_
        onClicked: {
          root.close();
          root.accepted();
        }
      }
    }
  }
}
