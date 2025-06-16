import QtQuick
import pathpilot.core
import pathpilot.robot
import pathpilot.robot.jog
import pathpilot.handlers

QtObject {
  id: root
  property StateHandler stateHandler
  readonly property bool jogActive: root.interactiveMove.active

  readonly property InteractiveMove interactiveMove: InteractiveMove {
    function moveToPose(pose, frameId) {
      frameId = (frameId === undefined ? "" : frameId);
      interactiveMove.setAbsolutePoseTarget(["x", "y", "z", "a", "b", "c"], pose, frameId);
      interactiveMove.start();
    }

    function moveToJoints(joints) {
      interactiveMove.setAbsoluteJointsTarget(["joint_1", "joint_2", "joint_3", "joint_4", "joint_5", "joint_6"], joints);
      interactiveMove.start();
    }

    function checkPoseReachable(pose, frameId) {
      frameId = (frameId === undefined ? "" : frameId);
      return interactiveMove.checkAbsolutePoseTargetReachable(["x", "y", "z", "a", "b", "c"], pose, frameId);
    }
  }

  readonly property InteractiveMarker interactiveMarker: InteractiveMarker {
    fixedFrame: Config.data.preview.fixedFrame
    markerName: "EE:goal_" + Config.data.preview.toolFrame
    frames: stateHandler.userFrames

    readonly property Connections _connections: Connections {
      target: interactiveMarker.pose

      function checkPoseReachable() {
        interactiveMove.checkPoseReachable(interactiveMarker.pose.toEulerAngles());
      }

      function onPositionChanged() {
        Qt.callLater(checkPoseReachable);
      }
      function onOrientationChanged() {
        Qt.callLater(checkPoseReachable);
      }
    }

    readonly property Timer _timer: Timer {
      id: checkPoseReachableDelayTimer
      interval: 10
      repeat: false
      onTriggered: {
        interactiveMove.checkPoseReachable(interactiveMarker.pose.toEulerAngles());
      }
    }
  }

  readonly property JogMarkers jogMarkers: JogMarkers {
    markerFrame: root.stateHandler.userFrames.activeFrameFrame
    markerPose: root.stateHandler.cartesianState.pose
    useToolFrame: Config.user.jog.toolFrame
  }

  readonly property QtObject incremental: QtObject {

    readonly property var linearSteps: Config.data.jog.increments[Config.user.linearUnit]
    readonly property var angularSteps: Config.data.jog.increments[Config.user.angularUnit]
    readonly property int jogstepsize: (Config.user.jog.stepSize == -1) ? 0 : Config.user.jog.stepSize
    readonly property double linearStepSize: Units.toRos(Number(linearSteps[jogstepsize]), Config.user.linearUnit)
    readonly property double angularStepSize: Units.toRos(Number(angularSteps[jogstepsize]), Config.user.angularUnit)

    function stop() {
      interactiveMove.stop();
    }

    readonly property QtObject joints: QtObject {
      function step(index, value) {
        interactiveMove.setOffsetJointsTarget(["joint_" + (index + 1)], [value]);
        interactiveMove.start();
      }

      function continuous(index, value) {
        interactiveMove.setContinuousJointsTarget(["joint_" + (index + 1)], [value]);
        interactiveMove.start();
      }
    }

    readonly property QtObject cartesian: QtObject {
      function step(axis, value, frameId) {
        frameId = (frameId === undefined ? "" : frameId);
        interactiveMove.setOffsetPoseTarget([axis.toLowerCase()], [value], frameId);
        interactiveMove.start();
      }

      function continuous(axis, value, frameId) {
        frameId = (frameId === undefined ? "" : frameId);
        axis = axis.toLowerCase();
        value = Math.sign(value);
        if (["x", "y", "z"].includes(axis)) {
          value = Math.sign(value) * 5.0;
        } else {
          value = Math.sign(value) * Math.PI;
        }
        interactiveMove.setContinuousPoseTarget([axis], [value], frameId);
        interactiveMove.start();
      }
    }
  }

  readonly property QtObject continuous: QtObject {

    readonly property JointJogControl joints: JointJogControl {
      enabled: true
      autorepeatInterval: 250
      baseLink: Config.data.robotArmBaseLink
      jointNamePrefix: "joint_"
    }

    readonly property CartesianJogControl cartesian: CartesianJogControl {
      enabled: true
      autorepeatInterval: 250
      frameId: Config.user.jog.toolFrame ? Config.data.preview.toolFrame : ""
    }
  }
}
