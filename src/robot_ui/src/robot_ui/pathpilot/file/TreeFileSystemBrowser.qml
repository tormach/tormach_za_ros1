import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.models
import pathpilot.file
import pathpilot.controls.treeview

TreeView {
  id: root
  signal folderSelected(string path)
  signal fileSelected(string path)

  property alias rootPath: fileSystemModel.rootPath
  property bool readOnly: false

  model: fileSystemModel
  textColor: Colors.black1
  selectedTextColor: Colors.white1
  ScrollBar.vertical.policy: ScrollBar.AlwaysOn

  TreeFileSystemModel {
    id: fileSystemModel
  }

  TreeViewColumn {
    title: qsTr("Name")
    role: "fileName"
    width: 200
    delegate: Item {
      id: item2
      property color textColor: Colors.black1

      RowLayout {
        anchors.fill: parent
        anchors.leftMargin: Sizes.halfMargin
        spacing: Sizes.singleSpacing

        Image {
          Layout.alignment: Qt.AlignVCenter
          sourceSize.width: item2.height - Sizes.singleMargin
          sourceSize.height: width
          source: model ? "image://mimeIconProvider/" + model.path : ""
        }

        Text {
          Layout.fillWidth: true
          Layout.alignment: Qt.AlignVCenter
          font: root.font
          verticalAlignment: Text.AlignVCenter
          text: styleData.value
          elide: Text.ElideRight
          color: item2.textColor
        }
      }
    }
  }

  TreeViewColumn {
    title: qsTr("Size")
    role: "displaySize"
    delegate: defaultComponent
  }

  TreeViewColumn {
    title: qsTr("Modified")
    role: "displayLastModified"
    delegate: defaultComponent
  }

  Component {
    id: defaultComponent
    Item {
      id: item
      property color textColor: Colors.black1

      Text {
        anchors.fill: parent
        anchors.leftMargin: Sizes.singleMargin
        font: root.font
        verticalAlignment: Text.AlignVCenter
        text: styleData.value
        elide: Text.ElideRight
        color: item.textColor
      }
    }
  }
  MouseArea {
    anchors.fill: parent
    enabled: root.readOnly
  }
}
