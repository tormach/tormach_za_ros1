import QtQuick
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.hal

Item {
  id: root
  property int nr: 1
  property color ledColor: Colors.green1
  property bool ledSynced: halPin.synced
  property alias led: led
  property alias topic: halPin.topic
  implicitWidth: 45
  implicitHeight: 40

  Led {
    id: led
    anchors.centerIn: parent
    anchors.horizontalCenterOffset: 8
    height: root.height * 0.55
    width: height
    activeColor: root.ledSynced ? root.ledColor : Colors.yellow1
    value: halPin.value || !root.ledSynced
  }

  PathPilotLabel {
    anchors.left: parent.left
    anchors.leftMargin: Sizes.singleMargin
    anchors.verticalCenter: parent.verticalCenter
    font.pixelSize: Fonts.statusPanel.size1
    text: (halPin.direction === Hal.In) ? qsTr("In") : qsTr("Out")
  }

  HalPin {
    id: halPin
    type: Hal.Bit
    direction: Hal.In
  }
}
