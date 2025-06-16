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
  live: true

  function update(value) {
    root.value = value;
    d.update();
  }

  QtObject {
    id: d
    function update() {
      Config.user.uniformVelocityScale = root.value;
      root.updated();
    }
  }

  onValueChanged: {
    d.update();
  }

  Binding {
    target: root
    property: "value"
    value: Config.user.uniformVelocityScale
  }
}
