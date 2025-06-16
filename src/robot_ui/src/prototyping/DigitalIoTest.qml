import QtQuick
import QtQuick.Controls
import pathpilot.controls
import pathpilot.robot.program

UnscaledTestBase {
  id: root

  DigitalIOs {
    id: ios
    Component.onCompleted: ios.update()
  }

  Column {
    Repeater {
      id: repeater
      model: ios.digitalInputs

      PathPilotLabel {
        text: ios.digitalInputs[index].number + ":   " + ios.digitalInputs[index].name
      }
    }

    PathPilotButton {
      text: "Rename"
      onClicked: ios.digitalInputs[0].name = "bachus"
    }

    Repeater {
      id: repeater2
      model: ios.digitalOutputs

      PathPilotLabel {
        text: ios.digitalOutputs[index].number + ":   " + ios.digitalOutputs[index].name
      }
    }
  }
}
