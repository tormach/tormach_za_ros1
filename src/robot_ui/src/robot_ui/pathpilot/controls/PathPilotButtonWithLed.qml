import QtQuick
import pathpilot.core

PathPilotButton {
  id: root
  readonly property color ledColor: Colors.green1
  property bool ledActive: true
  property bool ledSynced: true
  property bool bigLed: false
  property alias led: led

  Led {
    id: led
    anchors.right: parent.right
    anchors.top: parent.top
    anchors.rightMargin: root.bigLed ? 4 : 5
    anchors.topMargin: root.bigLed ? 4 : 5
    height: root.bigLed ? 16 : 12
    width: height
    activeColor: root.ledSynced ? root.ledColor : Colors.yellow1
    value: root.checked || !root.ledSynced
    enabled: root.ledActive
  }
}
