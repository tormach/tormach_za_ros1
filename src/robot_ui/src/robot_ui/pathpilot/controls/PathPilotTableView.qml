import QtQuick
import QtQuick.Controls
import QtQml.Models
import pathpilot.core
import pathpilot.controls
import pathpilot.file
import pathpilot.models
import Qt.labs.qmlmodels

Rectangle {
  id: root
  signal doubleClicked(int row)
  signal doubleClickedDelayed(int row)
  signal rightClicked(int row)
  property int rowHeight: 30
  property alias model: table.model
  property alias delegate: table.delegate
  property color textColor: root.enabled ? Colors.black1 : Colors.gray1
  property color selectedTextColor: Colors.white1
  property alias font: dummyText.font
  property int fillColumn: 0
  property int columnMaxWidth: 600

  property int sortIndicatorColumn: 0
  property int sortIndicatorOrder: Qt.AscendingOrder

  property ItemSelectionModel selection: ItemSelectionModel {
    signal selectionChangedFixed
    signal currentIndexChangedFixed
    property int currentRow: -1
    property var sourceIndexes: []
    //property var currentIndexFixed: currentIndex
    model: table.model
    // workaround, selectionChanged is not triggered on clear, trigger manually
    onSelectionChangedFixed: d.updateSelectedRows()
    onCurrentIndexChanged: currentIndexChangedFixed()
    // workaround, currentIndexChanged is not triggered on clear, trigger manually
    onCurrentIndexChangedFixed: currentRow = currentIndex.row

    readonly property RangeSelector _selector: RangeSelector {
      id: rangeSelector
      model: root.selection
    }

    function saveIndexes() {
      var rows = root.selection.selectedRows(0);
      var rowIndizes = [];
      for (var i = 0; i < rows.length; ++i) {
        rowIndizes.push(root.model.mapToSource(rows[i]));
      }
      root.selection.sourceIndexes = rowIndizes;
      root.clearSelection();
    }

    function restoreIndexes() {
      for (var i = 0; i < root.selection.sourceIndexes.length; ++i) {
        var index = root.model.mapFromSource(root.selection.sourceIndexes[i]);
        root.selection.setCurrentIndex(index, ItemSelectionModel.Rows | ItemSelectionModel.Select);
      }
    }
  }
  property bool enableSelection: true
  property bool enableMultiSelection: true
  readonly property alias selectedRows: d.selectedRows
  readonly property int currentRow: root.selection.currentRow
  readonly property alias rowCount: table.rows
  readonly property alias columnCount: table.columns
  property alias rowHeightProvider: table.rowHeightProvider
  color: Colors.white1
  clip: true
  width: 500
  height: 500

  // prevents accidental double click on item when window/popup is closed
  onDoubleClicked: function (row) {
    d.delay(100, function () {
        root.doubleClickedDelayed(row);
      });
  }

  Keys.onEnterPressed: _handleReturn()
  Keys.onReturnPressed: _handleReturn()
  function _handleReturn() {
    if (root.currentRow > -1) {
      d.delay(100, function () {
          root.doubleClickedDelayed(root.currentRow);
        });
    }
  }

  Keys.onDownPressed: function (event) {
    if ((root.currentRow > -1) && (root.currentRow < (root.rowCount - 1))) {
      root.selectRow(root.currentRow + 1, event.modifiers);
      root.moveToSelected();
    }
  }

  Keys.onUpPressed: function (event) {
    if (root.currentRow > 0) {
      root.selectRow(root.currentRow - 1, event.modifiers);
      root.moveToSelected();
    }
  }

  Keys.onPressed: function (event) {
    if ((event.key == Qt.Key_A) && (event.modifiers & Qt.ControlModifier)) {
      root.selectAll();
      return;
    }
    event.accepted = false;
  }

  function moveToBeginning() {
    table.contentY = 0;
  }

  function moveToSelected() {
    if (root.currentRow == -1) {
      root.moveToBeginning();
      return;
    }
    var selectedY = (root.currentRow + 1) * root.rowHeight;
    if (selectedY > (table.contentY + table.height)) {
      table.contentY = selectedY - table.height;
    }
    selectedY -= root.rowHeight;
    if (selectedY < table.contentY) {
      table.contentY = selectedY;
    }
  }

  function moveToEnd() {
    table.contentY = Math.max(0, table.contentHeight - table.height);
  }

  function moveToStart() {
    table.contentY = 0;
  }

  function selectRow(row, modifiers) {
    if (!root.enableSelection) {
      return;
    }
    var flags = ItemSelectionModel.Rows;
    if (root.enableMultiSelection && (modifiers & Qt.ControlModifier)) {
      flags |= ItemSelectionModel.Select;
    } else if (root.enableMultiSelection && (modifiers & Qt.ShiftModifier)) {
      flags |= ItemSelectionModel.Select;
      if (row < root.currentRow) {
        rangeSelector.selectRange(root.model.index(row, 0), root.model.index(root.currentRow, 0), flags);
      }
      if (root.currentRow > -1 && row > root.currentRow) {
        rangeSelector.selectRange(root.model.index(root.currentRow, 0), root.model.index(row, 0), flags);
      }
    } else {
      flags |= ItemSelectionModel.ClearAndSelect;
    }
    var index = root.model.index(row, 0);
    root.selection.setCurrentIndex(index, flags);
    root.selection.selectionChangedFixed();
  }

  function selectLastRow() {
    if (!root.enableSelection) {
      return;
    }
    root.selection.clear();
    if (root.rowCount > 0) {
      var index = root.model.index(root.rowCount - 1, 0);
      root.selection.setCurrentIndex(index, ItemSelectionModel.Rows | ItemSelectionModel.Select);
    }
    root.selection.selectionChangedFixed();
  }

  function selectAll() {
    if (!(root.enableSelection && root.enableMultiSelection)) {
      return;
    }
    var firstIndex = root.model.index(0, 0);
    var lastIndex = root.model.index(root.rowCount - 1, 0);
    rangeSelector.selectRange(firstIndex, lastIndex, ItemSelectionModel.Rows | ItemSelectionModel.Select);
    root.selection.selectionChangedFixed();
  }

  function clearSelection() {
    root.selection.clear();
    root.selection.selectionChangedFixed();
    root.selection.currentIndexChangedFixed();
  }

  function sort() {
    root.model.sort(root.sortIndicatorColumn, root.sortIndicatorOrder);
    d.updateSortIndicators();
  }

  readonly property QtObject _d: QtObject {
    id: d
    readonly property int indicatorSpacing: 30
    property var selectedRows: []
    property bool loaded: false
    property bool firstCellInvalidated: false // part of workaround
    readonly property Timer delayTimer: Timer {
      property var cb: function () {}
      onTriggered: cb()
    }

    function updateSelectedRows() {
      var rows = root.selection.selectedRows(0);
      var rowIndizes = [];
      for (var i = 0; i < rows.length; ++i) {
        rowIndizes.push(rows[i].row);
      }
      d.selectedRows = rowIndizes;
    }

    function updateSortIndicators() {
      {
        for (var i = 0; i < headerRepeater.model; ++i) {
          if (i != root.sortIndicatorColumn) {
            headerRepeater.itemAt(i).stopSorting();
          } else {
            headerRepeater.itemAt(i).state = (root.sortIndicatorOrder == Qt.AscendingOrder ? "up" : "down");
          }
        }
      }
    }

    function delay(delayTime, cb) {
      var timer = d.delayTimer;
      timer.stop();
      timer.interval = delayTime;
      timer.repeat = false;
      timer.cb = cb;
      timer.start();
    }
  }

  Connections {
    target: root.model
    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onModelReset() {
      root.clearSelection();
    }
    function onLayoutAboutToBeChanged() {
      root.forceActiveFocus(); // triggers outstanding editingFinished signals
      selection.saveIndexes();
    }
    function onLayoutChanged() {
      selection.restoreIndexes();
    }
    function onRowsAboutToBeInserted() {
      selection.saveIndexes();
    }
    function onRowsInserted() {
      selection.restoreIndexes();
    }
  }

  Text {
    id: dummyText
    visible: false
    font.pixelSize: Fonts.controls.tableView
    font.family: Fonts.font2
  }

  Row {
    id: header
    width: table.contentWidth
    height: root.rowHeight
    x: -table.contentX
    z: 1
    spacing: Sizes.thinBorder

    function forceLayout() {
      headerRepeater.model = 0;
      headerRepeater.model = table.model.columnCount();
    }

    function columnWidth(column) {
      return Math.min(root.columnMaxWidth, table.model.columnWidth(column, root.font) + d.indicatorSpacing);
    }

    Repeater {
      id: headerRepeater
      model: table.model?.columnCount() ?? 0

      PathPilotTableViewColumnHeading {
        id: heading
        tableView: table
        font: root.font
        initialWidth: {
          if (index == root.fillColumn) {
            var restWidth = 0;
            for (var i = 0; i < headerRepeater.model; ++i) {
              if (i == root.fillColumn) {
                continue;
              }
              restWidth += header.columnWidth(i);
            }
            restWidth += table.columnSpacing * (headerRepeater.model - 1);
            return Math.max(header.columnWidth(root.fillColumn), root.width - restWidth);
          } else {
            return header.columnWidth(index);
          }
        }
        height: parent.height
        initialSortOrder: table.model.initialSortOrder(index)

        onWidthChanged: {
          if (d.loaded)
            table.forceLayout();
        }

        onSorting: {
          root.sortIndicatorColumn = index;
          root.sortIndicatorOrder = state == "up" ? Qt.AscendingOrder : Qt.DescendingOrder;
          root.sort();
        }

        onDropped: function (x) {
          var columnWidths = [];
          for (var i = 0; i < headerRepeater.count; ++i) {
            columnWidths.push(headerRepeater.itemAt(i).width);
          }
          table.model.reorderColumn(index, x, columnWidths);
          header.forceLayout();
        }

        Connections {
          target: table.model
          // ignoreUnknownSignals: true // might need to reactivate with Qt6
          function onHeaderDataChanged() {
            heading.text = table.model.headerData(index, Qt.Horizontal);
          }
        }
      }
    }
  }

  Component.onCompleted: {
    d.loaded = true;
    if (root.sortIndicatorColumn > -1) {
      root.sort();
    }
  }

  Connections {
    target: table
    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onRowsChanged() {
      // workaround for DelegateChooser using wrong choice in first cell
      if (d.firstCellInvalidated || table.rows == 0) {
        return;
      }
      // unfortunately, we need to retrigger loading the cells
      root.model.invalidate();
      d.firstCellInvalidated = true;
    }
  }

  TableView {
    id: table
    anchors.fill: parent
    anchors.topMargin: header.height
    columnSpacing: Sizes.thinBorder
    rowSpacing: 0
    columnWidthProvider: function (column) {
      return headerRepeater.itemAt(column).width;
    }
    rowHeightProvider: function () {
      return root.rowHeight;
    }

    delegate: DelegateChooser {
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

    ScrollBar.horizontal: ScrollBar {
    }

    ScrollBar.vertical: ScrollBar {
      snapMode: ScrollBar.SnapAlways
      policy: ScrollBar.AlwaysOn
    }
  }
}
