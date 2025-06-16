import QtQuick
import QtQuick.Window
import pathpilot.core
import pathpilot.panels.jog

UnscaledTestBase {
  id: root

  Timer {
    id: toggleTimer
    property bool enableControls: false
    interval: 1000
    repeat: true
    running: true
    onTriggered: enableControls = !enableControls
  }

  TwoAxesJoyStick {
    id: twoAxesJoyStick
    anchors.centerIn: parent
    width: 250
    height: width
    enabled: toggleTimer.enableControls
  }

  SingleAxisJoyStick {
    id: singleAxisJoyStick
    anchors.left: twoAxesJoyStick.right
    anchors.verticalCenter: twoAxesJoyStick.verticalCenter
    anchors.margins: Sizes.doubleMargin
    height: 250
    enabled: toggleTimer.enableControls
  }
}
