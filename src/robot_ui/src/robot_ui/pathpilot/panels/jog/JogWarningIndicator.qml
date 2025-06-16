import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.jog
import pathpilot.robot.hal

RowLayout {
  id: root

  readonly property QtObject _d: QtObject {
    id: d
    readonly property bool hasCollisionHalt: (jogStatus.guiStatus === JogControlStatus.HaltForCollisionStatus) || (jogStatus.joyStatus === JogControlStatus.HaltForCollisionStatus)
    readonly property bool hasCollisionDecel: (jogStatus.guiStatus === JogControlStatus.DecelerateForCollisionStatus) || (jogStatus.joyStatus === JogControlStatus.DecelerateForCollisionStatus)
    readonly property bool hasLimit: (jogStatus.guiStatus === JogControlStatus.JointBoundStatus) || (jogStatus.joyStatus === JogControlStatus.JointBoundStatus)
    readonly property bool hasSingularityHalt: (jogStatus.guiStatus === JogControlStatus.HaltForSingularityStatus) || (jogStatus.joyStatus === JogControlStatus.HaltForSingularityStatus)
    readonly property bool hasSingularityDecel: (jogStatus.guiStatus === JogControlStatus.DecelerateForSingularityStatus) || (jogStatus.joyStatus === JogControlStatus.DecelerateForSingularityStatus)
  }

  HalPin {
    id: probeStatusHalPin
    type: Hal.Bit
    direction: Hal.In
    topic: "hal_io/probe_in"
  }

  PathPilotLabel {
    font.pixelSize: Fonts.jogPanel.size1
    text: qsTr("Probe")
  }

  Led {
    id: probe_led
    implicitHeight: 25
    implicitWidth: 25
    activeColor: probeStatusHalPin.synced ? "orange" : Colors.yellow1
    value: probeStatusHalPin.value || !probeStatusHalPin.synced
  }

  PathPilotLabel {
    font.pixelSize: Fonts.jogPanel.size1
    text: qsTr("Limit")
  }

  Led {
    implicitHeight: 25
    implicitWidth: 25
    activeColor: "orange"
    value: d.hasLimit
  }

  PathPilotLabel {
    font.pixelSize: Fonts.jogPanel.size1
    text: qsTr("Collision")
  }

  Led {
    implicitHeight: 25
    implicitWidth: 25
    activeColor: d.hasCollisionHalt ? "orange" : "yellow"
    value: d.hasCollisionHalt || d.hasCollisionDecel
  }

  PathPilotLabel {
    font.pixelSize: Fonts.jogPanel.size1
    text: qsTr("Singularity")
  }

  Led {
    implicitHeight: 25
    implicitWidth: 25
    activeColor: d.hasSingularityHalt ? "orange" : "yellow"
    value: d.hasSingularityHalt || d.hasSingularityDecel
  }

  JogControlStatus {
    id: jogStatus
  }
}
