import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import pathpilot.controls
import pathpilot.development
import pathpilot.robot
import pathpilot.robot.jog
import pathpilot.handlers

Item {

  // --||--
  id: root

  //default property alias buttonData: manualJog.buttonData
  //property alias controlData: manualJog.controlData

  signal moveCancelled
  // called when started in target pose mode and user cancelled movement
  signal moveCompleted
  enabled: Handlers.state.driveStart.inEffect

  /**
    Sets a target pose and puts the panel into target pose mode.
  */
  function setTargetPose(pose) {
    d.requireMoveToPose = true;
    stack.currentIndex = 1;
    moveToWaypoint.setTargetPose(pose);
    moveToWaypoint.start();
  }

  function setTargetJoints(joints) {
    d.requireMoveToPose = true;
    stack.currentIndex = 1;
    moveToWaypoint.setTargetJoints(joints);
    moveToWaypoint.start();
  }

  QtObject {
    id: d
    property bool requireMoveToPose: false
  }

  StackLayout {
    id: stack
    anchors.fill: parent
    currentIndex: 0

    ManualJogPanel {
      id: manualJog
    }

    MoveToWaypointPanel {
      id: moveToWaypoint

      onMoveCompleted: {
        if (d.requireMoveToPose) {
          d.requireMoveToPose = false;
          root.moveCompleted();
        }
        stack.currentIndex = 0;
      }

      onMoveAborted: {
        if (d.requireMoveToPose) {
          d.requireMoveToPose = false;
          root.moveCancelled();
        }
        stack.currentIndex = 0;
      }
    }
  }
}
