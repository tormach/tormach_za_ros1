import QtQuick
import QtQuick.Controls
import Qt.labs.qmlmodels
import pathpilot.core
import pathpilot.controls
import pathpilot.models

Rectangle {
  id: root
  signal doubleClicked(int row)
  signal doubleClickedDelayed(int row)
  signal rightClicked(int row)
  signal pressAndHold(int row)

  color: Colors.white1
  clip: true

  property alias delegate: tree.delegate
  property alias model: tree.model
  property alias selection: tree.selectionModel
  property alias treeView: tree
  property alias selectedRows: d.selectedRows
  property alias currentRow: tree.currentRow
  readonly property alias rowCount: tree.rows

  property bool enableSelection: true
  property bool enableMultiSelection: true

  readonly property QtObject _d: QtObject {
    id: d

    readonly property Timer delayTimer: Timer {
      property var cb: function () {}
      onTriggered: cb()
    }

    readonly property RangeSelector _selector: RangeSelector {
      id: rangeSelector
      model: root.selection
    }

    property var selectedRows: []
    property int currentRow: tree.rowAtIndex(root.selection.currentIndex)

    function updateSelectedRows() {
      let rows = [];
      let indizes = root.selection.selectedIndexes;
      for (var i = 0; i < indizes.length; ++i) {
        rows.push(tree.rowAtIndex(indizes[i]));
      }
      d.selectedRows = rows;
    }

    function delay(delayTime: int, cb: var) {
      let timer = d.delayTimer;
      timer.stop();
      timer.interval = delayTime;
      timer.repeat = false;
      timer.cb = cb;
      timer.start();
    }
  }

  Connections {
    target: root.selection
    ignoreUnknownSignals: true
    function onSelectionChanged() {
      d.updateSelectedRows();
    }
    function onCleared() {
      d.updateSelectedRows();
    }
  }

  // prevents accidental double click on item when window/popup is closed
  onDoubleClicked: function (row) {
    d.delay(100, function () {
        root.doubleClickedDelayed(row);
      });
  }

  Keys.onDownPressed: function (event) {
    if ((root.currentRow > -1) && (root.currentRow < (root.rowCount - 1))) {
      root.selectRow(root.currentRow + 1, event.modifiers);
      tree.positionViewAtRow(root.currentRow, TreeView.AlignCenter);
    }
  }

  Keys.onUpPressed: function (event) {
    if (root.currentRow > 0) {
      root.selectRow(root.currentRow - 1, event.modifiers);
      tree.positionViewAtRow(root.currentRow, TreeView.AlignCenter);
    }
  }

  function selectRow(row: int, modifiers: int) {
    if (!root.enableSelection) {
      return;
    }
    var flags = ItemSelectionModel.Rows;
    if (root.enableMultiSelection && (modifiers & Qt.ControlModifier)) {
      flags |= ItemSelectionModel.Select;
    } else if (root.enableMultiSelection && (modifiers & Qt.ShiftModifier)) {
      flags |= ItemSelectionModel.Select;
      if (row < d.currentRow) {
        rangeSelector.selectRange(tree.index(row, 0), tree.index(d.currentRow, 0), flags);
      }
      if (d.currentRow > -1 && row > d.currentRow) {
        rangeSelector.selectRange(tree.index(d.currentRow, 0), tree.index(row, 0), flags);
      }
    } else {
      flags |= ItemSelectionModel.ClearAndSelect;
    }
    let index = tree.index(row, 0);
    root.selection.setCurrentIndex(index, flags);
  }

  TreeView {
    id: tree
    anchors.fill: parent
    columnSpacing: 0
    rowSpacing: 0
    selectionBehavior: TableView.SelectionDisabled
    keyNavigationEnabled: false
    reuseItems: false

    ScrollBar.horizontal: ScrollBar {
      policy: ScrollBar.AlwaysOff
    }

    ScrollBar.vertical: ScrollBar {
      snapMode: ScrollBar.SnapAlways
      policy: ScrollBar.AlwaysOn
    }
  }
}
