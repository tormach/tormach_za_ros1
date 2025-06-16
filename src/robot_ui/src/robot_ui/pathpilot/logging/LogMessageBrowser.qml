import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.logging
import pathpilot.models
import Qt.labs.qmlmodels

PathPilotTableView {
  id: root
  property alias logFilter: messageLogger.filter
  property alias highestSeverity: messageDataModel.highestSeverity
  model: sortFilterModel
  fillColumn: 1
  sortIndicatorColumn: 2
  sortIndicatorOrder: Qt.DescendingOrder

  function removeAll() {
    messageDataModel.removeAll();
  }

  rowHeightProvider: function (row) {
    return Math.max(sortFilterModel.rowHeight(row, MessageDataModel.MessageRole, root.font) + 10, root.rowHeight);
  }

  readonly property QtObject _d: QtObject {
    id: d

    property string severityString: ""
    property string message: ""
    property string extendedInfo: ""
    property bool hasExtendedInfo: extendedInfo.length > 0

    readonly property Timer delayTimer: Timer {
      property var cb: function () {}
      onTriggered: cb()
    }

    function delay(delayTime, cb) {
      var timer = d.delayTimer;
      timer.interval = delayTime;
      timer.repeat = false;
      timer.cb = cb;
      timer.start();
    }

    function extractRowData(row) {
      // note: column may change if reordered by user
      let severityCol = sortFilterModel.fields.indexOf(MessageDataModel.SeverityRole);
      d.severityString = root.model.data(root.model.index(row, severityCol), Qt.DisplayRole);
      d.message = root.model.data(root.model.index(row, 0), MessageDataModel.MessageRole);
      d.extendedInfo = root.model.data(root.model.index(row, 0), MessageDataModel.ExtendedInfoRole);
    }

    function copyRowDataToClipboard() {
      clipboardHelper.text = "%1: %2\n%3".arg(d.severityString).arg(d.message).arg(d.extendedInfo);
      clipboardHelper.selectAll();
      clipboardHelper.copy();
    }

    readonly property TextInput clipboardHelper: TextInput {
      visible: false
    }
  }

  MessageDataModel {
    id: messageDataModel
  }

  SortFilterProxyModel {
    id: sortFilterModel
    source: messageDataModel
    fields: [MessageDataModel.SeverityRole, MessageDataModel.MessageRole, MessageDataModel.TimestampRole, MessageDataModel.NodeRole]
    columnWidthOverrides: {
      "severity": 80,
      "node": 250,
      "timestamp": 250
    }
    headerTitles: {
      "message": qsTr("Message"),
      "severity": qsTr("Severity"),
      "node": qsTr("Node"),
      "timestamp": qsTr("Timestamp"),
      "topics": qsTr("Topics"),
      "location": qsTr("Location"),
      "id": qsTr("Id")
    }
    onRowsInserted: {
      if (root.sortIndicatorOrder === Qt.AscendingOrder) {
        d.delay(10, root.moveToEnd);
      } else {
        d.delay(10, root.moveToStart);
      }
    }
  }

  MessageLogger {
    id: messageLogger
    topics: ["rosout_agg"]
    ready: true
    model: messageDataModel

    filter.severityThreshold: LogLevel.Error
  }

  Menu {
    id: contextMenu

    MenuItem {
      text: qsTr("Copy to clipboard")
      onClicked: d.copyRowDataToClipboard()
    }

    MenuItem {
      text: qsTr("Show more details...")
      visible: d.hasExtendedInfo
      height: visible ? implicitHeight : 0
      onClicked: {
        extendedInfoPopup.open();
      }
    }

    Connections {
      target: root

      function onRightClicked(row) {
        d.extractRowData(row);
        contextMenu.popup();
      }
      function onDoubleClicked(row) {
        d.extractRowData(row);
        if (d.hasExtendedInfo) {
          extendedInfoPopup.open();
        }
      }
    }
  }

  LogMessagePopup {
    id: extendedInfoPopup
    severityString: d.severityString
    message: d.message
    extendedInfo: d.extendedInfo
  }

  delegate: DelegateChooser {
    role: "type"

    DelegateChoice {
      roleValue: "message"
      PathPilotTableViewDelegateBase {
        id: item
        readonly property int index: row
        readonly property string severity: model.severity
        readonly property string extendedInfo: model.extended
        property bool extendedVisible: false
        table: root

        Label {
          anchors.fill: parent
          anchors.leftMargin: Sizes.singleMargin
          anchors.rightMargin: Sizes.singleMargin
          font: root.font
          verticalAlignment: Text.AlignVCenter
          text: item.extendedInfo ? model.message + " ..." : model.message
          elide: Text.ElideRight
          wrapMode: Text.WordWrap
          color: (item.severity >= LogLevel.Error ? Colors.red1 : (item.severity == LogLevel.Warn ? Colors.orange1 : item.textColor))
        }
      }
    }

    DelegateChoice {
      PathPilotTableViewDelegateBase {
        id: item
        readonly property string severity: model.severity
        table: root

        Text {
          anchors.fill: parent
          anchors.leftMargin: Sizes.singleMargin
          anchors.rightMargin: Sizes.singleMargin
          font: root.font
          verticalAlignment: Text.AlignVCenter
          text: model.display
          elide: Text.ElideRight
          wrapMode: Text.WordWrap
          color: (item.severity >= LogLevel.Error ? Colors.red1 : (item.severity == LogLevel.Warn ? Colors.orange1 : item.textColor))
        }
      }
    }
  }
}
