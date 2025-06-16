import QtQuick
import QtQuick.Layouts
import pathpilot.core
import pathpilot.controls
import pathpilot.robot
import pathpilot.robot.jog
import pathpilot.robot.preview
import pathpilot.handlers

RowLayout {
  id: root

  property InteractiveMove interactiveMove: Handlers.jog.interactiveMove
  property var targetPose
  property var targetJoints
  property int targetType

  signal moveCompleted
  signal moveAborted

  onVisibleChanged: {
    if (!root.visible) {
      root.moveAborted();
    }
    Handlers.app.lockPanel(root.visible);
  }

  onEnabledChanged: {
    // panel can be disabled by parent when the robot goes into an error state
    if (root.visible && !root.enabled) {
      root.moveAborted();
    }
  }

  function setTargetPose(pose) {
    interactiveMove.stop();
    interactiveMove.setAbsolutePoseTarget(["x", "y", "z", "a", "b", "c"], pose);
  }

  function setTargetJoints(joints) {
    interactiveMove.stop();
    interactiveMove.setAbsoluteJointsTarget(["joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6"], joints);
  }

  function start() {
    if (interactiveMove.targetIsCurrent) {
      root.moveCompleted();
    } else {
      d.targetReached = false;
    }
  }

  QtObject {
    id: d
    property bool targetReached: true
    property bool failed: false
  }

  RvizPreviewController {
    Layout.fillWidth: true
    Layout.fillHeight: true
    mode: PreviewMode.View
  }

  ColumnLayout {
    Layout.preferredWidth: 200
    Layout.fillWidth: false

    PathPilotButton {
      Layout.fillHeight: true
      Layout.fillWidth: true
      text: d.targetReached ? qsTr("Complete") : qsTr("Hold\nto\nMove")
      horizontalAlignment: Text.AlignHCenter
      blink: interactiveMove.active
      highlighted: true

      onPressed: interactiveMove.start()
      onReleased: {
        interactiveMove.stop();
        if (d.targetReached)
          if (d.failed) {
            root.moveAborted();
          } else {
            root.moveCompleted();
          }
      }
    }

    PathPilotButton {
      id: cancelButton
      Layout.fillWidth: true
      visible: !d.targetReached
      text: qsTr("Cancel")
      onClicked: root.moveAborted()
    }
  }

  Connections {
    target: interactiveMove
    // ignoreUnknownSignals: true // might need to reactivate with Qt6
    function onCompletedChanged() {
      d.targetReached = interactiveMove.completed;
      if (interactiveMove.completed) {
        d.failed = false;
      }
    }
    function onFailedChanged() {
      d.targetReached = interactiveMove.failed;
      if (interactiveMove.failed) {
        d.failed = true;
      }
    }
  }
}
