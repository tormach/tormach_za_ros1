import QtQuick
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.hal

PathPilotButton {
  id: root
  property int nr: 1
  property color ledColor: Colors.green1
  property bool ledSynced: halPin.synced
  property alias led: led
  property alias topic: halPin.topic
  implicitWidth: 45
  font.pixelSize: Fonts.statusPanel.size1
  labelMargin: 0
  checkable: true

  text: qsTr("Out\n%1").arg(root.nr)

  Led {
    id: led
    anchors.right: parent.right
    anchors.bottom: parent.bottom
    anchors.margins: root.height * 0.15
    width: root.height * 0.35
    height: width
    activeColor: root.ledSynced ? root.ledColor : Colors.yellow1
    value: root.checked || !root.ledSynced
  }

  HalPin {
    id: halPin
    name: "digital_out_%1".arg(root.nr)
    type: Hal.Bit
    direction: Hal.Out
  }

  Binding {
    target: root
    property: "checked"
    value: halPin.value
  }
  Binding {
    target: halPin
    property: "value"
    value: root.checked
  }
}
