import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.handlers

Item {
  id: root
  property var jointNames: Config.data.jointNames
  property var jointPositions: d.jointState.ready ? d.jointState.jointPositions : d.defaultJointPosition

  QtObject {
    id: d
    readonly property JointState jointState: Handlers.state.jointState
    readonly property var defaultJointPosition: {
      "j1": 1.0,
      "j2": 0.0,
      "j3": 0.0,
      "j4": 0.0,
      "j5": 0.0,
      "j6": 0.0
    }
    readonly property int joints: root.jointNames.length
  }

  ColumnLayout {
    id: container
    anchors.fill: parent

    Repeater {
      model: d.joints
      JointDro {
        required property int index
        Layout.fillWidth: true
        Layout.fillHeight: true
        jointName: root.jointNames[index]
        jointPosition: root.jointPositions ? Units.fromRos(root.jointPositions[root.jointNames[index].toLowerCase()], Config.user.angularUnit) : 0
        decimals: Config.data.dro.decimals[Config.user.angularUnit]
      }
    }
  }
}
