import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.handlers
import pathpilot.robot.jog

GridLayout {
  id: root
  columns: 4

  GripperJogControl {
    id: gripperJogControl
  }

  RowLayout {
    PathPilotLabel {
      text: qsTr("Gripper")
    }
  }

  PathPilotButton {
    text: qsTr("Open")
    onClicked: {
      gripperJogControl.gotoPosition(100, 100);
    }
  }

  PathPilotButton {
    text: qsTr("Soft Close")
    onClicked: {
      gripperJogControl.gotoPosition(0, 20);
    }
  }

  PathPilotLabel {
    text: qsTr("Position: %1%").arg(gripperJogControl.currentPosition)
  }

  Item {
  }

  PathPilotButton {
    text: qsTr("Release")
    onClicked: {
      gripperJogControl.gotoPosition(100, 0);
    }
  }
  PathPilotButton {
    text: qsTr("Hard Close")
    onClicked: {
      gripperJogControl.gotoPosition(0, 100);
    }
  }

  RowLayout {
    PathPilotLabel {
      text: qsTr("Connected")
    }

    Led {
      id: gripperLed
      activeColor: "green"
      value: gripperJogControl.configured
    }

    PathPilotLabel {
      text: qsTr("Moving")
    }

    Led {
      id: gripperLed2
      activeColor: "orange"
      value: gripperJogControl.commandActive
    }
  }
}
