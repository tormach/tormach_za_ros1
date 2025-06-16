import QtQuick
import QtQuick.Window
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.hal

UnscaledTestBase {
  id: root

  HalIoGroup {
    id: halIoGroup
    containerItem: root
  }

  Column {
    Repeater {
      id: inRepeater
      model: ROS.getParam("io/digital_in_topics", [])

      Led {
        id: halLed
        value: halPin.value

        HalPin {
          id: halPin
          direction: Hal.In
          type: Hal.Bit
          topic: inRepeater.model[index]
          enabled: true
        }

        Component.onCompleted: halIoGroup.update()
      }
    }
  }

  Column {
    anchors.right: parent.right
    Repeater {
      id: outRepeater
      model: ROS.getParam("io/digital_out_topics", [])

      PathPilotButtonWithLed {
        id: outButton
        width: 150
        anchors.right: parent.right
        text: "Digital Out %1".arg(index)
        checkable: true

        Binding {
          target: outButton
          property: "checked"
          value: outPin.value
        }
        Binding {
          target: outPin
          property: "value"
          value: outButton.checked
        }

        HalPin {
          id: outPin
          direction: Hal.Out
          type: Hal.Bit
          topic: outRepeater.model[index]
        }
      }
    }
  }
}
