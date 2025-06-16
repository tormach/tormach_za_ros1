import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property int count: 1

  signal accepted

  onOpened: cancelButton.forceActiveFocus()

  RowLayout {
    Icon {
      id: image
      icon: Icons.popup.warning
    }

    PathPilotLabel {
      text: {
        var framesText = root.count > 1 ? qsTr("frames") : qsTr("frame");
        return qsTr("Removing %1 %2, are you sure?").arg(root.count).arg(framesText);
      }
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
