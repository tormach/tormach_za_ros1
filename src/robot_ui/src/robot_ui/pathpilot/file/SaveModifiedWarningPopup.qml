import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property bool autoUpdated: false
  property string operation: "no operation"
  closePolicy: Popup.CloseOnEscape

  signal save
  signal discard
  signal cancel

  onOpened: cancelButton.forceActiveFocus()

  RowLayout {
    Icon {
      id: image
      icon: Icons.popup.warning
    }

    PathPilotLabel {
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
      horizontalAlignment: Text.AlignLeft
      text: {
        var text = "";
        text += qsTr("User input required before %1.\n").arg(root.operation);
        if (root.autoUpdated) {
          text += qsTr("The program structure has been automatically updated.\n");
        } else {
          text += qsTr("The program has unsaved changes.\n");
        }
        text += qsTr("Do you want to save or discard the changes before continuing with the operation?\n");
        return text;
      }
    }
  }

  RowLayout {

    PathPilotButton {
      id: cancelButton
      implicitWidth: 180
      text: qsTr("Cancel Operation")
      onClicked: {
        root.close();
        root.cancel();
      }
    }

    HorizontalFiller {
    }

    PathPilotIconButton {
      id: discardButton
      implicitWidth: 130
      labelColor: Colors.red1
      text: qsTr("Discard")
      icon_: Icons.filepanel.delete_
      onClicked: {
        root.close();
        root.discard();
      }
    }

    PathPilotIconButton {
      id: okButton
      implicitWidth: 120
      text: qsTr("Save")
      icon_: Icons.filepanel.save
      onClicked: {
        root.close();
        root.save();
      }
    }
  }
}
