import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.file
import pathpilot.logging
import pathpilot.handlers

RowLayout {
  id: root
  property FileSelection selection: null
  readonly property bool pathValid: selection !== undefined
  readonly property bool fileSelected: selection && selection.files !== undefined && selection.files.length > 0
  readonly property bool singleSelection: selection && selection.files !== undefined && selection.files.length == 1
  property alias filterString: filterTextField.text

  function focusFilter() {
    filterTextField.forceActiveFocus();
  }

  readonly property FileOperations fileOperations: FileOperations {
    id: fileOperations
    path: root.pathValid ? root.selection.path : ""
    files: root.selection ? root.selection.files : []

    function checkCurrentProgram() {
      for (var i = 0; i < fileOperations.files.length; ++i) {
        var path = fileOperations.path + "/" + fileOperations.files[i];
        if (path === Handlers.program.info.path) {
          return true;
        }
      }
    }
  }

  PathPilotIconButton {
    implicitWidth: 150
    text: qsTr("New")
    icon_: Icons.filepanel.folder
    enabled: root.pathValid
    onClicked: newFolderPopup.open()
    PathPilotToolTip {
      itemId: "msg_create_new_folder"
    }
  }

  PathPilotIconButton {
    implicitWidth: 150
    text: qsTr("Rename")
    icon_: Icons.filepanel.rename
    enabled: pathValid && singleSelection
    onClicked: {
      fileRenamePopup.text = root.selection.files[0];
      fileRenamePopup.open();
    }
    PathPilotToolTip {
      itemId: "msg_raname_file"
    }
  }

  PathPilotIconButton {
    implicitWidth: 150
    text: qsTr("Delete")
    icon_: Icons.filepanel.delete_
    enabled: root.fileSelected
    onClicked: deleteFilePopup.open()
    PathPilotToolTip {
      itemId: "msg_delete_file"
    }
  }

  HorizontalFiller {
  }

  PathPilotTextField {
    id: filterTextField
    horizontalAlignment: Text.AlignLeft
    rightPadding: filterIcon.width + Sizes.halfMargin

    Icon {
      id: filterIcon
      anchors.right: parent.right
      anchors.rightMargin: Sizes.halfMargin
      anchors.verticalCenter: parent.verticalCenter
      icon: Icons.filepanel.filter
    }
    PathPilotToolTip {
      itemId: "msg_search_for_file"
    }
  }

  FileNamePopup {
    id: fileRenamePopup
    onAccepted: function (name) {
      if (Handlers.program.programLoaded && fileOperations.checkCurrentProgram()) {
        Logging.log(qsTr("Cannot rename currently loaded robot program: %1").arg(Handlers.program.info.name), LogLevel.Warn);
        return;
      }
      if (!fileOperations.rename(name)) {
        Logging.log(qsTr("Couldn't rename file or folder %1").arg(name), LogLevel.Error);
      }
      Handlers.program.info.refreshRecentFiles();
    }
  }

  FileNamePopup {
    id: newFolderPopup
    onAccepted: function (name) {
      if (!fileOperations.createFolder(name)) {
        Logging.log(qsTr("Couldn't create folder %1").arg(name), LogLevel.Error);
      }
    }
  }

  DeleteFilePopup {
    id: deleteFilePopup
    fileCount: root.selection ? root.selection.fileCount : 0
    folderCount: root.selection ? root.selection.folderCount : 0
    onAccepted: {
      if (Handlers.program.programLoaded && fileOperations.checkCurrentProgram()) {
        Logging.log(qsTr("Cannot delete currently loaded robot program: %1").arg(Handlers.program.info.name), LogLevel.Warn);
        return;
      }
      if (!fileOperations.deleteAll()) {
        Logging.log(qsTr("Couldn't delete all files."), LogLevel.Error);
      }
      Handlers.program.info.refreshRecentFiles();
    }
  }
}
