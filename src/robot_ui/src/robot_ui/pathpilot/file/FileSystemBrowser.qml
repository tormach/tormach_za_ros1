import QtQuick
import QtQuick.Window
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.models
import pathpilot.file
import Qt.labs.qmlmodels

PathPilotTableView {
  id: root
  signal folderSelected(string path)
  signal fileSelected(string path)

  property alias nameFilters: sortFilterModel.nameFilters
  property alias fileFilter: sortFilterModel.filter
  property alias filterDirs: sortFilterModel.filterDirs
  property var fileSystemModel
  property var fileSelection
  model: sortFilterModel
  font.pixelSize: Fonts.filePanel.size3
  sortIndicatorColumn: 0

  onDoubleClickedDelayed: function (row) {
    d.rowSelected(row);
  }

  Component.onCompleted: sort()

  function getFileName(rowIndex) {
    var index = root.model.index(rowIndex, 0);
    return root.model.data(index, FlatFileSystemModel.FileNameRole);
  }

  function isDir(rowIndex) {
    var index = root.model.index(rowIndex, 0);
    return root.model.data(index, FlatFileSystemModel.IsDirRole);
  }

  function selectFile(path) {
    for (var i = 0; i < root.rowCount; ++i) {
      var index = root.model.index(i, 0);
      var path_ = root.model.data(index, FlatFileSystemModel.PathRole);
      if (root.model.data(index, FlatFileSystemModel.PathRole) == path) {
        root.selectRow(i);
        break;
      }
    }
  }

  readonly property FileNavigation navigation: FileNavigation {
    id: fileNavigation
    currentPath: homePath
  }

  QtObject {
    id: d

    function rowSelected(row) {
      var index = sortFilterModel.index(row, 0);
      var isDir = sortFilterModel.data(index, FlatFileSystemModel.IsDirRole);
      var path = sortFilterModel.data(index, FlatFileSystemModel.PathRole);
      if (isDir) {
        root.folderSelected(path);
      } else {
        root.fileSelected(path);
      }
    }

    function updateSelection(target) {
      var selection = [];
      for (var i = 0; i < target.length; ++i) {
        selection.push(fileSystemBrowser.getFileName(target[i]));
      }
      fileSelection.files = selection;
    }
  }

  Connections {
    target: root.selection
    function onSelectionChangedFixed() {
      d.updateSelection(root.selectedRows);
    }
  }

  FlatFileSystemSortModel {
    id: sortFilterModel
    source: root.fileSystemModel
    onFilterChanged: root.moveToBeginning()
    headerTitles: {
      "fileName": qsTr("Name"),
      "size": qsTr("Size"),
      "lastModified": qsTr("Modified"),
      "isDir": qsTr("Is Directory"),
      "path": qsTr("Path")
    }
  }

  delegate: DelegateChooser {
    role: "type"

    DelegateChoice {
      roleValue: "fileName"
      PathPilotTableViewDelegateBase {
        id: item2
        table: root

        RowLayout {
          anchors.fill: parent
          anchors.leftMargin: Sizes.halfMargin
          spacing: Sizes.singleSpacing

          Image {
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: item2.height - Sizes.singleMargin
            Layout.preferredHeight: width
            sourceSize {
              width: width
              height: height
            }
            source: "image://mimeIconProvider/" + model.path + (model.isDir ? "/" : "")
          }

          Text {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            font: root.font
            verticalAlignment: Text.AlignVCenter
            text: String(model.display)
            elide: Text.ElideRight
            color: item2.textColor
          }
        }
      }
    }

    DelegateChoice {
      PathPilotTableViewDelegateBase {
        id: item
        table: root

        Text {
          anchors.fill: parent
          anchors.leftMargin: Sizes.singleMargin
          font: root.font
          verticalAlignment: Text.AlignVCenter
          text: String(model.display)
          elide: Text.ElideRight
          color: item.textColor
        }
      }
    }
  }
}
