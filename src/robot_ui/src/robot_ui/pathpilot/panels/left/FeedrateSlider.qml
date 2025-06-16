import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.hal

PathPilotSlider {
  id: root
  signal updated
  from: 0.0
  to: 1.0
  stepSize: 0.01

  function update(value) {
    root.value = value;
    root.updated();
  }

  QtObject {
    id: d
    function update() {
      {
        Config.user.feedrate = root.value;
        root.updated();
      }
    }
  }

  onValueChanged: {
    updateTimer.restart();
  }

  onPressedChanged: {
    if (!pressed && updateTimer.running) {
      updateTimer.stop();
      d.update();
    }
  }

  Binding {
    target: root
    property: "value"
    value: Config.user.feedrate
  }

  Timer {
    id: updateTimer
    interval: 500
    onTriggered: d.update()
  }
}
