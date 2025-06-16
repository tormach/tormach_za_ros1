import QtQuick
import pathpilot.core

Rectangle {
  id: root
  signal sorting
  signal dropped(real x)
  property int initialSortOrder: Qt.AscendingOrder
  property alias text: label.text
  property real initialWidth: 100
  property alias font: label.font
  property Item tableView: null
  width: splitter.x + 6
  z: dragHandler.active ? 1 : 0

  function stopSorting() {
    state = "";
  }

  gradient: Gradient {
    GradientStop {
      position: 0.0
      color: Colors.gray4
    }
    GradientStop {
      position: 1.0
      color: Colors.gray1
    }
  }

  Text {
    id: dummyText
    visible: false
    font.pixelSize: Fonts.controls.tableView
    font.family: Fonts.font2
  }

  Text {
    id: label
    anchors.fill: parent
    anchors.leftMargin: Sizes.singleMargin
    verticalAlignment: Text.AlignVCenter
    font: dummyText.font
    elide: Text.ElideRight
    text: tableView.model.headerData(index, Qt.Horizontal)
    color: root.enabled ? Colors.black1 : Colors.gray5
  }

  PathPilotTriangleIndicator {
    id: upDownIndicator
    anchors.verticalCenter: parent.verticalCenter
    anchors.right: parent.right
    anchors.rightMargin: Sizes.singleMargin
    visible: false
  }

  Rectangle {
    id: rightBorder
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.right: parent.right
    anchors.rightMargin: -width
    visible: parent.x + x < parent.parent.width
    width: 1
    color: Colors.gray2
  }

  Rectangle {
    id: leftBorder
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.left: parent.left
    anchors.leftMargin: -width
    visible: parent.x > 0
    width: 1
    color: Colors.gray2
  }

  TapHandler {
    id: tap
    onTapped: nextState()
  }

  Item {
    id: splitter
    x: root.initialWidth - 6
    width: 12
    height: parent.height + 10

    DragHandler {
      yAxis.enabled: false
      xAxis.minimum: 10
    }

    MouseArea {
      anchors.fill: parent
      cursorShape: Qt.SplitHCursor
    }
  }

  DragHandler {
    id: dragHandler
    yAxis.enabled: false
    onActiveChanged: if (!active)
      root.dropped(centroid.scenePosition.x)
  }

  function nextState() {
    if (state == "")
      state = (initialSortOrder == Qt.DescendingOrder ? "down" : "up");
    else if (state == "up")
      state = "down";
    else
      state = "up";
    root.sorting();
  }

  states: [
    State {
      name: "up"
      PropertyChanges {
        target: upDownIndicator
        visible: true
        rotation: 0
      }
    },
    State {
      name: "down"
      PropertyChanges {
        target: upDownIndicator
        visible: true
        rotation: 180
      }
    }
  ]
}
