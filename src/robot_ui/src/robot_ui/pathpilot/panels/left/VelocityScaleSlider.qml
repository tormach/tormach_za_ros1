import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.hal

PathPilotSlider {
  id: root

  // This slider *sets* the user-configured max_vel, but *indicates*
  // the current global max_vel.  Moving the slider (by clicking)
  // updates the Config.user.maximumVelocity param.  When either
  // Config.user.maximumVelocity or Config.machine.maxVelocityLimit is
  // updated, the slider position is updated to the minimum of the
  // two; a visual indicator changes when the slider value is less
  // than the user-set value.
  signal updated
  from: 0.0
  to: 1.0
  stepSize: 0.01

  property double machineMaxVelocity: Config.machine.maxVelocityLimit
  property double userMaxVelocity: Config.user.maximumVelocity

  function update(value) {
    root.value = value;
    d.update();
  }

  QtObject {
    id: d
    function update() {
      // The machine maxvel may limit velocity more than the user
      // setting; show the most restrictive limit in slider position
      root.value = Math.min(root.userMaxVelocity, root.machineMaxVelocity);
      if (root.value < root.userMaxVelocity) {
        // Indicate the machine limit is retricting velocity
        root.labelColor = Colors.red1;
      } else {
        root.labelColor = Colors.blue2;
      }
      root.updated();
    }
  }

  onPressedChanged: {
    if (!pressed) {
      Config.user.maximumVelocity = root.value;
    }
  }

  onMachineMaxVelocityChanged: {
    d.update();
  }

  onUserMaxVelocityChanged: {
    d.update();
  }
}
