import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.file
import pathpilot.logging
import pathpilot.handlers
import pathpilot.hub

RowLayout {
  id: root
  property var selection: null
  readonly property bool pathValid: selection && selection.programPath !== ""
  readonly property bool fileSelected: selection && selection.files !== undefined && selection.files.length > 0
  readonly property bool singleSelection: selection && selection.files !== undefined && selection.files.length == 1
  property alias filterString: filterTextField.text
  readonly property HubConnector hubConnector: Handlers.state.hubConnector

  function focusFilter() {
    filterTextField.forceActiveFocus();
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
      root.hubConnector.rename(name);
    }
  }

  FileNamePopup {
    id: newFolderPopup
    onAccepted: function (name) {
      root.hubConnector.createFolder(name);
    }
  }

  DeleteFilePopup {
    id: deleteFilePopup
    fileCount: root.selection ? root.selection.fileCount : 0
    folderCount: root.selection ? root.selection.folderCount : 0
    onAccepted: root.hubConnector.deleteAll()
  }
}
