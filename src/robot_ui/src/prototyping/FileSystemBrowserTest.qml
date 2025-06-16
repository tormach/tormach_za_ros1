import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.file
import pathpilot.development

UnscaledTestBase {
  id: root

  RowLayout {
    anchors.fill: parent

    FlatFileSystemModel {
      id: model
      rootPath: DevelopmentPaths.programPath
    }

    FileSystemBrowser {
      id: browser1
      Layout.fillWidth: true
      Layout.fillHeight: true
      fileSystemModel: model
      onFolderSelected: function (path) {
        model.rootPath = path;
      }
    }

    TreeFileSystemBrowser {
      id: browser2
      Layout.fillWidth: true
      Layout.fillHeight: true
      rootPath: Config.data.programHomePath
    }
  }
}
