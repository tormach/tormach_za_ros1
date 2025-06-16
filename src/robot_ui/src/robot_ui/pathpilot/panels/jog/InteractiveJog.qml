import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import pathpilot.core
import pathpilot.controls
import pathpilot.robot.jog
import pathpilot.handlers

ColumnLayout {
  id: root

  onVisibleChanged: {
    if (visible) {
      root.visible = true;
      d.previousPose = d.interactiveMarker.pose.copy(root);
      d.setMarkerPoseToCurrent();
      d.updateDrosFromMarker();
    }
  }

  readonly property QtObject _d: QtObject {
    id: d
    readonly property InteractiveMarker interactiveMarker: Handlers.jog.interactiveMarker
    readonly property InteractiveMove interactiveMove: Handlers.jog.interactiveMove
    property var previousPose
    property bool isUpdating: false
    readonly property var axisNames: Config.data.axisNames
    readonly property var jointNames: Config.data.jointNames
    property var axisPositions: [0, 0, 0, 0, 0, 0]
    property var jointPositions: [0, 0, 0, 0, 0, 0]

    function setMarkerPose(pose: Pose) {
      d.interactiveMarker.pose.orientation = pose.orientation;
      d.interactiveMarker.pose.position = pose.position;
      d.interactiveMarker.publish();
    }

    function setMarkerPoseToCurrent() {
      var pose = Handlers.state.cartesianState.pose;
      d.setMarkerPose(pose);
    }

    function setMarkerOrientation(a: double, b: double, c: double) {
      var pose = d.interactiveMarker.pose.copy(d);
      pose.axisPositions["a"] = a;
      pose.axisPositions["b"] = b;
      pose.axisPositions["c"] = c;
      d.setMarkerPose(pose);
    }

    function resetMarkerPose() {
      d.setMarkerPose(d.previousPose);
    }

    function updateDrosFromMarker() {
      if (!d.isUpdating) {
        d.axisPositions = d.interactiveMarker.pose.toEulerAngles();
      }
    }

    function setAxisValue(index: int, value: double) {
      var values = d.axisPositions.slice();
      values[index] = value;
      var pose = d.interactiveMarker.pose.copy(d);
      for (var i = 0; i < d.axisNames.length; ++i) {
        pose.axisPositions[d.axisNames[i].toLowerCase()] = values[i];
      }
      d.isUpdating = true;
      d.setMarkerPose(pose);
      d.isUpdating = false;
      d.axisPositions = values;
    }
  }

  Connections {
    target: d.interactiveMarker.pose
    enabled: root.visible
    function onPositionChanged() {
      Qt.callLater(d.updateDrosFromMarker);
    }
    function onOrientationChanged() {
      Qt.callLater(d.updateDrosFromMarker);
    }
  }

  MarkerOperations {
    id: markerOperations
    Layout.fillWidth: true
    Layout.fillHeight: false
    onResetMarkerPose: d.resetMarkerPose()
    onSetMarkerPoseToCurrent: d.setMarkerPoseToCurrent()
    onSetMarkerOrientation: function (a, b, c) {
      d.setMarkerOrientation(a, b, c);
    }
  }

  MarkerDros {
    id: markerDros
    Layout.fillWidth: true
    Layout.fillHeight: true
    axisNames: d.axisNames
    jointNames: d.jointNames
    axisPositions: d.axisPositions
    jointPositions: d.jointPositions

    onUpdateAxisValue: function (index, value) {
      d.setAxisValue(index, value);
    }
  }

  RowLayout {
    HorizontalFiller {
    }

    PathPilotLabel {
      text: qsTr("Pose Reachable")
    }

    Led {
      activeColor: "green"
      offColor: "orange"
      value: d.interactiveMove.isReachable
    }
  }
}
