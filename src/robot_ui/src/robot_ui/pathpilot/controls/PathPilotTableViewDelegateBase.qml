import QtQuick
import pathpilot.core

Rectangle {
  id: root
  signal clicked
  // FIXME: fix implicitely exposed row property
  property Item table: null
  readonly property bool selected: table.selectedRows.includes(row)
  color: root.selected ? Colors.green2 : ((row % 2 == 0) ? Colors.white1 : Colors.gray6)
  property color textColor: (model && model.modified) ? Colors.green3 : (root.selected ? table.selectedTextColor : table.textColor)
  default property alias contentData: content.data
  property alias selectionEnabled: mouseArea.enabled

  Item {
    id: content
    anchors.fill: parent
  }

  Rectangle {
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.left: parent.right
    width: Sizes.thinBorder
    color: parent.color
  }

  MouseArea {
    id: mouseArea
    anchors.fill: parent
    height: parent.height
    width: parent.width
    z: 1
    acceptedButtons: Qt.LeftButton | Qt.RightButton

    onClicked: function (mouse) {
      table.forceActiveFocus();
      if (mouse.button == Qt.LeftButton) {
        table.selectRow(row, mouse.modifiers);
        root.clicked();
      } else {
        table.rightClicked(row);
      }
    }

    onDoubleClicked: table.doubleClicked(row)
  }
}
