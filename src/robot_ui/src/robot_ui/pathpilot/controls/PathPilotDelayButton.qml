import QtQuick
import QtQuick.Window
import QtQuick.Controls
import pathpilot.core
import pathpilot.controls

PathPilotButton {
  id: root
  signal activated

  property real progress: 0.0
  property int delay: 500

  transitions: [
    Transition {
      to: "pressed"
      NumberAnimation {
        property: "progress"
        duration: root.delay
      }
      onRunningChanged: {
        if (!running && root.progress >= 1.0) {
          root.activated();
        }
      }
    },
    Transition {
      to: "aborted"
      NumberAnimation {
        property: "progress"
        duration: 200
      }
    }
  ]

  states: [
    State {
      name: "pressed"
      PropertyChanges {
        target: root
        progress: 1.0
      }
    },
    State {
      name: "aborted"
      PropertyChanges {
        target: root
        progress: 0.0
      }
    },
    State {
      name: "done"
      PropertyChanges {
        target: root
        progress: 0.0
      }
    }
  ]

  Rectangle {
    anchors.top: parent.top
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.rightMargin: 5
    anchors.topMargin: 6
    anchors.bottomMargin: 4
    width: 10
    radius: width / 2
    color: Colors.black1

    Rectangle {
      anchors.fill: parent
      anchors.margins: Sizes.thickBorder
      radius: width / 2
      color: Colors.gray3
    }

    Rectangle {
      anchors.right: parent.right
      anchors.left: parent.left
      anchors.bottom: parent.bottom
      anchors.margins: Sizes.thickBorder
      height: parent.height * root.progress
      radius: width / 2
      color: Colors.green1
    }
  }

  onPressed: root.state = "pressed"
  onReleased: root.state = (root.progress >= 1.0 ? "done" : "aborted")
  onEnabledChanged: {
    if (!enabled) {
      root.state = "done";
    }
  }
  onCanceled: root.state = "aborted"
}
