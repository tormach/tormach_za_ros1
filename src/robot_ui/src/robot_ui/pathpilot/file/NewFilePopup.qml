import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.file

PathPilotPopup {
  id: root
  property string homePath: Config.data.programHomePath
  property string defaultName: ""
  readonly property string path: fileNavigation.currentPath + "/" + name
  readonly property string name: d.name.endsWith(extension) ? d.name : d.name + extension
  property string extension: ".py"
  property string fileFilter: ".*\\.py"
  property string title: qsTr("Choose a program file name.")

  signal accepted(string path, string name)

  implicitHeight: 800
  implicitWidth: 800

  onOpened: {
    d.name = root.defaultName;
    fileSystemBrowser.clearSelection();
    fileNavigation.navigateHome();
    textInput.forceActiveFocus();
  }

  QtObject {
    id: d
    property alias name: textInput.text
  }

  FileNavigation {
    id: fileNavigation
    homePath: root.homePath
    currentPath: homePath
  }

  FileOperations {
    id: fileOperations
    path: fileNavigation.currentPath
  }

  FileNamePopup {
    id: newFolderPopup
    scale: root.scale
    onAccepted: function (name) {
      fileOperations.createFolder(name);
    }
  }

  PathPilotLabel {
    text: root.title
    font.family: Fonts.font2
    font.pixelSize: Fonts.filePanel.size1
    font.bold: true
  }

  RowLayout {
    Layout.fillWidth: true

    PathPilotLabel {
      text: qsTr("Name:")
      font.family: Fonts.font2
      font.pixelSize: Fonts.filePanel.size1
      font.bold: true
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
    Layout.fillWidth: true

    PathPilotIconButton {
      text: qsTr("Back")
      icon_: Icons.filepanel.back
      onClicked: fileNavigation.navigateBack()
    }

    PathPilotIconButton {
      text: qsTr("Home")
      icon_: Icons.filepanel.home
      onClicked: fileNavigation.navigateHome()
    }

    PathPilotIconButton {
      text: qsTr("New Folder")
      implicitWidth: 160
      icon_: Icons.filepanel.folder
      onClicked: newFolderPopup.open()
    }

    VerticalFiller {
    }
  }

  LocalFileSystemBrowser {
    id: fileSystemBrowser
    Layout.fillWidth: true
    Layout.fillHeight: true

    rootPath: visible ? fileNavigation.currentPath : "" // safe some resources when not visible
    enableMultiSelection: false
    fileFilter: root.fileFilter

    function updateFileName() {
      if (currentRow < 0) {
        return;
      }
      if (!fileSystemBrowser.isDir(currentRow)) {
        d.name = fileSystemBrowser.getFileName(currentRow);
      }
    }

    onFolderSelected: function (path) {
      fileNavigation.currentPath = path;
      fileSystemBrowser.clearSelection();
    }
    onFileSelected: okButton.clicked()
    onCurrentRowChanged: updateFileName()
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
      enabled: d.name !== ""
      text: qsTr("Save")
      icon_: Icons.filepanel.save
      onClicked: {
        root.close();
        root.accepted(root.path, root.name);
      }
    }
  }
}
