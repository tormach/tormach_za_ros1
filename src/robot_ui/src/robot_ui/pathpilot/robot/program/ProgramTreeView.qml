import QtQuick
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.program
import pathpilot.robot
import "."

PathPilotTreeView {
  id: root

  signal dragAndDropCompleted(string sourceUuid, string targetUuid)

  property bool readOnly: false
  property int copyPasteCommand: ProgramCopyPaste.NoCommand
  property string copyPasteSourceUuid: ""

  treeView {
    columnWidthProvider: function (column) {
      if (column == 0) {
        return root.width;
      }
      return 0;
    }
  }
  enableMultiSelection: false // not implemented yet

  readonly property QtObject _d: QtObject {
    id: d

    function expandRows(parent: var, first: int, last: int) {
      var row = -1;
      for (let i = first; i <= last; ++i) {
        let index = root.model.index(i, 0, parent);
        row = root.treeView.rowAtIndex(index);
        root.treeView.expand(row);
      }
    }
  }

  Component.onCompleted: expandDelayTimer.start()

  Connections {
    target: root.model

    function onModelReset() {
      expandDelayTimer.start();
    }

    function onRowsInserted(parent: var, first: int, last: int) {
      insertDelayTimer.parent = parent;
      insertDelayTimer.first = first;
      insertDelayTimer.last = last;
      insertDelayTimer.restart();
    }
  }

  Timer {
    /* need to use this timer to make expanding work */
    id: expandDelayTimer
    interval: 10
    repeat: false
    onTriggered: root.treeView.expandRecursively()
  }

  Timer {
    id: insertDelayTimer
    property var parent
    property int first: 0
    property int last: 0
    interval: 10
    repeat: false
    onTriggered: d.expandRows(parent, first, last)
  }

  delegate: ProgramTreeViewDelegate {
    copyPasteCommand: root.copyPasteCommand
    copyPasteSourceUuid: root.copyPasteSourceUuid
  }

  Rectangle {
    id: dragItem
    anchors.left: parent.left
    anchors.right: parent.right
    height: 40
    color: Colors.cyan1
    opacity: 0.3
    visible: false
    Drag.active: visible
    Drag.source: mouseArea
    Drag.hotSpot.x: width / 2
    Drag.hotSpot.y: height / 2
  }

  MouseArea {
    id: mouseArea
    anchors.fill: parent
    enabled: root.readOnly
  }
}
