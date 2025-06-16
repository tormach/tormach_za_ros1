import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property int fileCount: 0
  property int folderCount: 0

  signal accepted

  onOpened: cancelButton.forceActiveFocus()

  QtObject {
    id: d
    function formatText(fileCount, folderCount) {
      var fileText = (fileCount > 1) ? qsTr("files") : qsTr("file");
      var folderText = (folderCount > 1) ? qsTr("folders") : qsTr("folder");
      if ((fileCount > 0) && (folderCount > 0)) {
        return qsTr("Deleting %1 %3 and %2 %4, are you sure?").arg(fileCount).arg(folderCount).arg(fileText).arg(folderText);
      } else if (fileCount > 0) {
        return qsTr("Deleting %1 %2, are you sure?").arg(fileCount).arg(fileText);
      } else {
        return qsTr("Deleting %1 %2, are you sure?").arg(folderCount).arg(folderText);
      }
    }
  }

  RowLayout {
    Icon {
      id: image
      icon: Icons.popup.warning
    }

    PathPilotLabel {
      text: d.formatText(fileCount, folderCount)
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
