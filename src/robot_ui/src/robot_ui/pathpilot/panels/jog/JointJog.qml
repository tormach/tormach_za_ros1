import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.jog
import pathpilot.robot
import pathpilot.handlers

GridLayout {
  id: root
  property double velocity: Config.data.jog.jointVelocity * Config.user.jograte
  property JointState jointState: Handlers.state.jointState
  rows: 3
  flow: GridLayout.TopToBottom

  QtObject {
    id: d
    readonly property QtObject incrementalJog: Handlers.jog.incremental
    readonly property QtObject continuousJog: Handlers.jog.continuous
  }

  Repeater {
    model: root.jointState.joints.length

    RowLayout {
      id: row
      spacing: Sizes.singleSpacing
      readonly property double value: (slider.decrementPressed * -1.0 + slider.incrementPressed) * root.velocity
      property bool activeJoint: index + 1 == Config.user.jog.joint

      PathPilotLabel {
        Layout.preferredWidth: 20
        text: qsTr("J%1").arg(index + 1)
        color: row.activeJoint ? Colors.cyan1 : Colors.white1
      }

      JointJogSlider {
        id: slider
        from: root.jointState.joints[index].minimum
        to: root.jointState.joints[index].maximum
        value: root.jointState.joints[index].position
        incrementActiveExternal: keyboardJogInput.incrementPressed && row.activeJoint
        decrementActiveExternal: keyboardJogInput.decrementPressed && row.activeJoint

        onIncrementPressedChanged: {
          if (incrementPressed) {
            if (Config.user.jog.continuous) {
              d.incrementalJog.joints.continuous(index, 1);
            } else {
              d.incrementalJog.joints.step(index, d.incrementalJog.angularStepSize);
            }
          } else {
            d.incrementalJog.stop();
          }
        }

        onDecrementPressedChanged: {
          if (decrementPressed) {
            if (Config.user.jog.continuous) {
              d.incrementalJog.joints.continuous(index, -1);
            } else {
              d.incrementalJog.joints.step(index, -d.incrementalJog.angularStepSize);
            }
          } else {
            d.incrementalJog.stop();
          }
        }
      }

      Binding {
        target: Handlers.jog.jogMarkers
        property: "activeJoints." + (index + 1)
        value: slider.decrementHovered ? -1 : (slider.incrementHovered ? 1 : 0)
      }
    }
  }

  JointJogKeyboardInput {
    id: keyboardJogInput
    globalShortcuts: GlobalShortcuts
    enabled: parent.visible

    onJointSelected: function (index) {
      Config.user.jog.joint = index;
    }
  }

  Connections {
    target: d.continuousJog.joints
    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onActiveChanged(active) {
      Handlers.app.lockPanel(active);
    }
  }
}
