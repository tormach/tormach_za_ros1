import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.development
import pathpilot.handlers
import pathpilot.file

ColumnLayout {
  id: root
  property bool programLoadingEnabled: false

  property alias navigation: fileSystemBrowser.navigation
  property alias selection: fileSystemBrowser.fileSelection
  property alias fileOperations: fileOperationsGroup.fileOperations
  property alias fileBrowser: fileSystemBrowser

  function focusFilter() {
    fileOperationsGroup.focusFilter();
  }

  LocalFileSystemBrowser {
    id: fileSystemBrowser
    Layout.fillHeight: true
    Layout.fillWidth: true
    fileFilter: ".*" + fileOperationsGroup.filterString + ".*"
    filterDirs: true

    onFileSelected: function (path) {
      if (root.programLoadingEnabled) {
        d.loadProgram(path);
      }
    }
    onFolderSelected: function (path) {
      fileSystemBrowser.clearSelection();
      fileSystemBrowser.navigation.currentPath = path;
    }
  }

  PathPilotLabel {
    Layout.fillWidth: true
    horizontalAlignment: Text.AlignLeft
    font.family: Fonts.font2
    font.pixelSize: Fonts.filePanel.size3
    text: (fileSystemBrowser.rootPath) ? qsTr("Free space: %1").arg(FileUtils.humanReadableBytes(FileUtils.getFreeDiskSpace(fileSystemBrowser.rootPath))) : ""
  }

  LocalFileOperationsButtonGroup {
    id: fileOperationsGroup
    Layout.fillWidth: true
    selection: fileSystemBrowser.fileSelection
  }
}
