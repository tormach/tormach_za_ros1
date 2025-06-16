import QtQuick
import pathpilot.core
import pathpilot.controls

PathPilotButtonWithLed {
  id: root
  property bool running: false
  property bool paused: false

  text: qsTr("Cycle Start")
  font.pixelSize: Fonts.leftPanel.size1
  horizontalAlignment: Text.AlignHCenter
  bigLed: true

  led.value: (root.paused && blinkTimer.valueOnOff) || root.running

  Timer {
    id: blinkTimer
    property bool valueOnOff: false
    interval: 500
    repeat: true
    running: root.paused

    onTriggered: valueOnOff = !valueOnOff
  }
}
