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
  readonly property string name: d.name
  property string fileFilter: ".*\\.py"

  signal accepted(string path, string name)
  signal cancelled

  implicitHeight: 800
  implicitWidth: 800

  onOpened: {
    d.name = root.defaultName;
    fileSystemBrowser.clearSelection();
    fileNavigation.navigateHome();
    cancelButton.forceActiveFocus();
  }

  QtObject {
    id: d
    property string name
  }

  FileNavigation {
    id: fileNavigation
    homePath: root.homePath
    currentPath: homePath
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
      onClicked: {
        root.close();
        root.cancelled();
      }
    }

    PathPilotIconButton {
      id: okButton
      enabled: d.name !== ""
      text: qsTr("OK")
      icon_: Icons.filepanel.open
      onClicked: {
        root.close();
        root.accepted(root.path, root.name);
      }
    }
  }
}
