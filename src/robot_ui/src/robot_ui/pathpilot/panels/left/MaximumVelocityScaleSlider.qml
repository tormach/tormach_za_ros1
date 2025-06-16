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
  live: true  // Enable live updates

  property double machineMaxVelocity: Config.machine.maxVelocityLimits.safetyInput
  property double userMaxVelocity: Config.user.maximumVelocityScale
  property double originalUserValue: userMaxVelocity

  function update(value) {
    const targetValue = Math.min(value, machineMaxVelocity);
    root.value = targetValue;
    d.lastValue = targetValue;
    originalUserValue = value;
    d.update();
  }

  onValueChanged: {
    const targetValue = Math.min(value, machineMaxVelocity);
    if (machineMaxVelocity < 1.0) {
      // Indicate the machine limit is retricting velocity
      root.labelColor = Colors.red1;
    } else {
      root.labelColor = Colors.blue2;
    }
    if (value !== targetValue) {
      root.value = targetValue;
    }
    d.lastValue = targetValue;
    originalUserValue = value;
    updateTimer.restart();
  }

  Timer {
    id: updateTimer
    interval: 50  // 20Hz refresh rate (1000ms / 20 = 50ms)
    repeat: false
    onTriggered: {
      Config.user.maximumVelocityScale = root.value;
    }
  }

  QtObject {
    id: d
    property double lastValue: 0.0

    function update() {
      if (root.machineMaxVelocity >= root.originalUserValue) {
        root.value = root.originalUserValue;
      } else {
        root.value = root.machineMaxVelocity;
      }
      lastValue = root.value;
      root.updated();
    }
  }

  onMachineMaxVelocityChanged: {
    d.update();
  }

  onUserMaxVelocityChanged: {
    if (!pressed) {
      originalUserValue = userMaxVelocity;
      d.update();
    }
  }

  Component.onCompleted: {
    originalUserValue = userMaxVelocity;
    d.update();
  }
}
