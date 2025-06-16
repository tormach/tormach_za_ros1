import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.preview
import pathpilot.panels.jog
import pathpilot.handlers

AddWaypointPanelBase {
  id: root

  property var target: [0, 0, 0, 0, 0, 0]
  property string frame: ""
  property string name: ""
  property bool poseMode: false
  property bool globalWaypointMode: false

  function show() {
    root.visible = true;
    Handlers.preview.activeWaypointName = name;
    if (poseMode) {
      Handlers.state.userFrames.activeFrame = frame;
      jogPanel.setTargetPose(target);
    } else {
      jogPanel.setTargetJoints(target);
    }
  }

  function hide() {
    root.visible = false;
  }

  QtObject {
    id: d
    readonly property int decimals: Config.data.dro.decimals[Config.user.linearUnit]

    function formatArray(input, decimals) {
      var output = [];
      for (var i = 0; i < input.length; ++i) {
        output.push(Number(input[i].toFixed(decimals)));
      }
      return output;
    }
  }

  JogPanelControl {
    id: jogPanel
    Layout.fillWidth: true
    Layout.fillHeight: true

    onMoveCancelled: {
      Handlers.preview.activeWaypointName = "";
      root.hide();
    }

    onMoveCompleted: {
      Handlers.preview.activeWaypointName = "";
      root.hide();
    }

    PathPilotButton {
      Layout.fillWidth: true
      text: qsTr("Cancel")
      onClicked: root.hide()
    }
  }
}
