import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls

PathPilotPopup {
  id: root
  property alias name: textInput.text
  readonly property string path: d.dir + name
  property string originalPath: ""

  signal accepted(string path, string name)

  onOpened: {
    d.name = d.extractName(root.originalPath);
    d.dir = d.extractDir(root.originalPath);
    root.name = d.name;
    textInput.forceActiveFocus();
  }

  QtObject {
    id: d
    property string name: ""
    property string dir: ""

    function extractName(path) {
      return path.slice(path.lastIndexOf("/") + 1);
    }

    function extractDir(path) {
      return path.slice(0, path.lastIndexOf("/") + 1);
    }
  }

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
      text: qsTr("File with same name already exists in this\nlocation. Rename, overwrite or cancel?")
    }
  }

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
      implicitWidth: 120
      text: qsTr("Cancel")
      onClicked: root.close()
    }

    PathPilotIconButton {
      id: overwriteButton
      implicitWidth: 160
      labelColor: Colors.red1
      enabled: root.name !== ""
      text: qsTr("Overwrite")
      icon_: Icons.filepanel.save
      onClicked: {
        root.close();
        root.name = d.name;
        root.accepted(root.path, root.name);
      }
    }

    PathPilotIconButton {
      id: okButton
      implicitWidth: 120
      enabled: (root.name !== "") && (root.name !== d.name)
      text: qsTr("Save")
      icon_: Icons.filepanel.saveAs
      onClicked: {
        root.close();
        root.accepted(root.path, root.name);
      }
    }
  }
}
