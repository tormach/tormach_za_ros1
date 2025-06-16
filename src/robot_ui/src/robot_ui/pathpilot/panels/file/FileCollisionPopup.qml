import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property var collisions: []
  property int maxDisplayFiles: 30

  signal accepted

  onOpened: cancelButton.forceActiveFocus()

  readonly property QtObject _d: QtObject {
    id: d

    function formatText(collisions) {
      var text = qsTr("The following %1 files will be overwritten by the operation:").arg(collisions.length);
      for (var i = 0; i < Math.min(collisions.length, root.maxDisplayFiles); ++i) {
        text += "\n" + collisions[i];
      }
      if (collisions.length > root.maxDisplayFiles) {
        text += "\n...";
      }
      return text;
    }
  }

  RowLayout {
    Icon {
      id: image
      icon: Icons.popup.warning
    }

    PathPilotLabel {
      text: d.formatText(root.collisions)
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
      icon_: Icons.filepanel.copy
      onClicked: {
        root.close();
        root.accepted();
      }
    }
  }
}
